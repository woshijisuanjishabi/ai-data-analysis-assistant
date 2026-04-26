"""
SQL Agent — 把自然语言问题转换为 SQL，并产生结构化图表数据。
============================================================

工作流（一次问答）:

    1. plan_step    — LLM 拆解问题，输出 thinking + SQL（非流式，整段返回）
    2. execute_sql  — 在 business.db (只读) 执行 SQL；失败则带错误重调 LLM (3-10)
    3. summarize    — LLM 阅读结果行，**流式**产出用户向回复 + 可选 chart JSON

外部通过 ``run_chat_flow`` 异步生成器拿到一连串带类型的事件：

    {"type": "thinking", "data": "..."}
    {"type": "sql",      "data": "SELECT ..."}
    {"type": "chart",    "data": {chartType, ...}}
    {"type": "answer",   "data": "..."}        # 增量
    {"type": "error",    "data": "..."}
    {"type": "done"}

调用方（chat 路由）只负责把这些事件包装为 SSE。
"""

from __future__ import annotations

import asyncio
import re
from typing import Any, AsyncIterator, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from sqlalchemy import text

from database.connection import get_business_session
from services import chart_service, llm_service


# ============================================================
# 1. Schema 摘要
# ============================================================
def _summarize_schema() -> str:
    """从 business.db 抽取 CREATE TABLE 语句作为 LLM 上下文。"""
    with get_business_session() as db:
        rows = db.execute(
            text("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
        ).fetchall()
    parts: list[str] = []
    for name, sql in rows:
        if sql:
            parts.append(sql.strip().rstrip(";") + ";")
    return "\n\n".join(parts)


# ============================================================
# 2. Prompt 模板
# ============================================================
PLAN_SYSTEM = """你是一个企业数据分析助手，连接到 SQLite 数据库 business.db。
请基于用户问题，输出**思考过程**和**一条**可执行的 SELECT SQL。

【数据库 Schema】
{schema}

【输出格式 — 必须严格遵守】
<thinking>
用 1~3 句话说明你打算如何分析（用中文，不要超过 200 字）
</thinking>
<sql>
SELECT ... ;
</sql>

【硬性约束】
- 只允许 SELECT；禁止任何写操作
- SQLite 方言；日期处理用 strftime('%Y-%m', ...)
- 必要时 JOIN 多表；列名加上 AS 别名让结果可读
- 限制返回行数 ≤ 200
- 不要解释除以上格式之外的内容
"""

PLAN_RETRY_SYSTEM = """你之前生成的 SQL 在 SQLite 上执行失败：

【你之前的 SQL】
{prev_sql}

【数据库报错】
{error}

请基于 schema 重新生成正确的 SELECT 语句。仍然遵循同样的输出格式：
<thinking>...</thinking>
<sql>...</sql>

【数据库 Schema】
{schema}
"""

SUMMARIZE_SYSTEM = """你是数据分析师。下面给你用户的提问、刚刚执行的 SQL 以及结果。请：

1. 用中文写一段简洁、面向业务的回答（1~4 句话），告诉用户你看到了什么。
2. **如果数据适合可视化**（>= 2 行或多列），再追加一段图表 JSON（用 ```json ... ``` 围栏包住）。
3. 不需要再写 SQL。

【图表 JSON 严格规范】
- chartType: "bar" | "line" | "pie" | "scatter"
- title:     字符串
- xAxis:     **必须是数组**，元素是结果第一列的实际取值（不是列名！）
- series:    数组，每项是 {{ "name": 系列名, "data": [...] }}

【bar / line 示例】
```json
{{"chartType":"bar","title":"各部门销售额","xAxis":["销售部","技术部","市场部"],"series":[{{"name":"销售额","data":[1200,800,650]}}]}}
```

【pie 示例（省略 xAxis）】
```json
{{"chartType":"pie","title":"品类占比","series":[{{"name":"销售额","data":[{{"name":"电子产品","value":987}},{{"name":"办公家具","value":234}}]}}]}}
```

【scatter 示例】
```json
{{"chartType":"scatter","title":"客单 vs 数量","series":[{{"name":"订单","data":[[10,800],[20,1200]]}}]}}
```

如果只有 1 行结果，可以略过图表 JSON。

【用户问题】{question}

【SQL】
{sql}

【结果列】{columns}

【结果（最多 50 行）】
{rows_preview}
"""


# ============================================================
# 3. 解析 LLM 输出
# ============================================================
_THINKING_RE = re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE)
_SQL_RE      = re.compile(r"<sql>(.*?)</sql>",           re.DOTALL | re.IGNORECASE)
_FENCE_SQL   = re.compile(r"```(?:sql)?\s*(SELECT.*?)```", re.DOTALL | re.IGNORECASE)
_BARE_SELECT = re.compile(r"(SELECT[\s\S]+?;)",            re.IGNORECASE)


def _extract_thinking(text_: str) -> str:
    m = _THINKING_RE.search(text_)
    if m:
        return m.group(1).strip()
    # 退化：取第一段非 SQL 文字
    return text_.split("<sql>")[0].strip()


def _extract_sql(text_: str) -> Optional[str]:
    for r in (_SQL_RE, _FENCE_SQL, _BARE_SELECT):
        m = r.search(text_)
        if m:
            sql = m.group(1).strip().rstrip(";").strip()
            return sql + ";"
    return None


# ============================================================
# 4. SQL 安全闸门
# ============================================================
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> None:
    """非法语句直接抛 ValueError。"""
    if not sql or not sql.strip():
        raise ValueError("LLM 没有返回可执行的 SQL")
    if _FORBIDDEN.search(sql):
        raise ValueError("SQL 含有非只读关键字，已拦截")
    # 必须以 SELECT 开头
    head = sql.strip().lstrip("(").lstrip().upper()
    if not head.startswith("SELECT") and not head.startswith("WITH"):
        raise ValueError("SQL 不是 SELECT 语句，已拦截")


# ============================================================
# 5. 执行 SQL
# ============================================================
def _execute_sql(sql: str, *, max_rows: int = 200) -> tuple[list[str], list[dict[str, Any]]]:
    """返回 (columns, rows_as_dicts)。失败抛原始异常。"""
    _validate_sql(sql)
    with get_business_session() as db:
        rs = db.execute(text(sql))
        cols = list(rs.keys())
        rows = []
        for i, row in enumerate(rs):
            if i >= max_rows:
                break
            rows.append({c: row[idx] for idx, c in enumerate(cols)})
    return cols, rows


# ============================================================
# 6. Plan 阶段（含 3-10 重试）
# ============================================================
MAX_RETRY = 2


def _plan_messages(history: list[BaseMessage], question: str, schema: str) -> list[BaseMessage]:
    msgs: list[BaseMessage] = [SystemMessage(content=PLAN_SYSTEM.format(schema=schema))]
    msgs.extend(history)
    msgs.append(HumanMessage(content=question))
    return msgs


def _retry_plan_messages(question: str, schema: str, prev_sql: str, error: str) -> list[BaseMessage]:
    return [
        SystemMessage(content=PLAN_RETRY_SYSTEM.format(
            schema=schema, prev_sql=prev_sql, error=error,
        )),
        HumanMessage(content=question),
    ]


def _plan_once(messages: list[BaseMessage]) -> tuple[str, str]:
    """调用 LLM 返回 (thinking, sql)。"""
    raw = llm_service.invoke(messages)
    thinking = _extract_thinking(raw)
    sql = _extract_sql(raw)
    if not sql:
        raise ValueError(f"LLM 输出未包含 SQL：\n{raw[:300]}")
    return thinking, sql


# ============================================================
# 7. 主入口 — 异步生成事件流
# ============================================================
async def run_chat_flow(
    question: str,
    history: list[BaseMessage],
) -> AsyncIterator[dict[str, Any]]:
    """
    异步事件流。每个 event 为 {"type": str, "data": Any}。
    """
    schema = _summarize_schema()
    loop = asyncio.get_running_loop()

    # ---- 阶段 1：Plan ----
    try:
        thinking, sql = await loop.run_in_executor(
            None,
            _plan_once,
            _plan_messages(history, question, schema),
        )
    except Exception as e:
        yield {"type": "error", "data": f"规划失败: {e}"}
        yield {"type": "done"}
        return

    # 把 thinking 切成行 / 句子，做 "假" 流式
    pieces = re.split(r"(?<=[\n。；])", thinking)
    acc = ""
    for piece in pieces:
        if not piece:
            continue
        acc += piece
        yield {"type": "thinking", "data": acc}
        await asyncio.sleep(0.10)

    yield {"type": "sql", "data": sql}

    # ---- 阶段 2：执行 SQL（含 3-10 重试） ----
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    last_error: Optional[str] = None
    final_sql: str = sql

    for attempt in range(MAX_RETRY + 1):
        try:
            columns, rows = await loop.run_in_executor(None, _execute_sql, final_sql)
            last_error = None
            break
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            if attempt >= MAX_RETRY:
                break
            # 让前端看见自动修正的过程
            yield {
                "type": "thinking",
                "data": f"{acc}\n\n执行失败：{last_error}\n正在自动修正 SQL（第 {attempt + 1} 次）...",
            }
            try:
                _, new_sql = await loop.run_in_executor(
                    None,
                    _plan_once,
                    _retry_plan_messages(question, schema, final_sql, last_error),
                )
            except Exception as planning_err:
                last_error = f"修正失败: {planning_err}"
                break
            final_sql = new_sql
            yield {"type": "sql", "data": final_sql}

    if last_error:
        yield {"type": "error", "data": f"SQL 执行失败：{last_error}"}
        yield {"type": "done"}
        return

    # ---- 阶段 3：兜底先发一个图表（基于行形状） ----
    fallback_chart = chart_service.infer_chart_from_rows(rows, columns)
    if fallback_chart:
        # 不直接 emit，等 LLM 看完是否有更合适的图表 JSON
        pass

    # ---- 阶段 4：Summarize 流式输出 ----
    rows_preview = "\n".join(str(r) for r in rows[:50]) or "(空结果集)"
    summary_messages: list[BaseMessage] = [
        SystemMessage(content=SUMMARIZE_SYSTEM.format(
            question=question,
            sql=final_sql,
            columns=", ".join(columns) if columns else "(无)",
            rows_preview=rows_preview,
        )),
        HumanMessage(content="请按要求输出。"),
    ]

    # 在线程中迭代同步生成器，把结果搬到异步队列
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()

    def _produce() -> None:
        try:
            for piece in llm_service.stream(summary_messages):
                loop.call_soon_threadsafe(queue.put_nowait, piece)
        except Exception as e:                          # noqa: BLE001
            loop.call_soon_threadsafe(queue.put_nowait, ("__error__", str(e)))
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, sentinel)

    loop.run_in_executor(None, _produce)

    full_text = ""
    chart_emitted = False
    answer_acc = ""
    while True:
        item = await queue.get()
        if item is sentinel:
            break
        if isinstance(item, tuple) and item and item[0] == "__error__":
            yield {"type": "error", "data": f"总结阶段失败：{item[1]}"}
            break

        full_text += item

        # 截掉 ```...``` JSON 之后的部分作为用户向回答
        if "```" in full_text and not chart_emitted:
            answer_part, _, _ = full_text.partition("```")
            visible = answer_part.rstrip()
        else:
            visible = full_text

        if visible != answer_acc:
            answer_acc = visible
            yield {"type": "answer", "data": answer_acc}

    # 解析图表 JSON
    parsed = chart_service.parse_chart_json(full_text)
    chart = chart_service.normalize_chart(parsed) or fallback_chart
    if chart:
        yield {"type": "chart", "data": chart}
        chart_emitted = True

    # 整理最终 answer（移除 JSON 围栏部分）
    if "```" in full_text:
        answer_acc = full_text.partition("```")[0].rstrip()

    yield {"type": "done", "data": {
        "final_answer": answer_acc,
        "final_sql": final_sql,
        "final_chart": chart,
        "thinking": thinking,
    }}
