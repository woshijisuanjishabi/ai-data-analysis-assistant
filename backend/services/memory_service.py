"""
按 sessionId 隔离的会话记忆
==========================

* ``load_history(session_id, limit=N)`` — 从 app.db 读最近 N 条消息，转成 LangChain
  ``BaseMessage`` 列表，可直接拼到对话提示里。
* ``persist_user_message`` / ``persist_assistant_message`` — 将一次对话两端写库。

记忆做了两点取舍：
* **只取最近 N 条** (默认 8)：避免上下文无限增长导致 token 爆掉
* **assistant 只放 content + sql**：把 thinking 和 chart 这种结构化字段排除在 prompt 外，
  避免 LLM 误把它们当成新一轮的输出格式参考
"""

from typing import Any, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.orm import Session

from database import session_store as ss


HISTORY_DEFAULT = 8


def load_history(db: Session, session_id: str, limit: int = HISTORY_DEFAULT) -> list[BaseMessage]:
    """读取最近若干轮对话作为 prompt 上下文。"""
    msgs = ss.list_messages(db, session_id)
    if not msgs:
        return []

    tail = msgs[-limit:]
    out: list[BaseMessage] = []
    for m in tail:
        if m.role == "user":
            out.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            content = m.content or ""
            if m.sql:
                content += f"\n\n[已执行 SQL]\n{m.sql}"
            out.append(AIMessage(content=content))
    return out


def persist_user_message(db: Session, session_id: str, text: str) -> str:
    m = ss.append_message(db, session_id=session_id, role="user", content=text)
    return m.id


def persist_assistant_message(
    db: Session,
    session_id: str,
    *,
    content: str,
    thinking: Optional[str] = None,
    sql: Optional[str] = None,
    chart: Optional[dict[str, Any]] = None,
) -> str:
    m = ss.append_message(
        db,
        session_id=session_id,
        role="assistant",
        content=content,
        thinking=thinking,
        sql=sql,
        chart=chart,
    )
    return m.id
