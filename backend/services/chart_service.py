"""
图表数据规范化
==============

* ``infer_chart_from_rows`` — 当 LLM 没返回图表 JSON 时，根据 SQL 结果行的形状自动推断
* ``normalize_chart``       — 把 LLM 给出的 chart dict 规范成前端可直接用的 ECharts 格式
* ``parse_chart_json``      — 从 LLM 文本中提取 ```json ... ``` 块或纯 JSON

输出始终是这种结构（与前端 mock/data.js 中 `ChartJSON` 一致）：

    {
      "chartType": "bar | line | pie | scatter",
      "title":     str?,
      "xAxis":     [str|num] (pie/scatter 时可省),
      "series":    [{ "name": str, "data": [...] }]
    }
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterable, Optional


VALID_TYPES = {"bar", "line", "pie", "scatter"}


# ---------------------------------------------------------------
# 1. 从 LLM 自由文本中提取 JSON
# ---------------------------------------------------------------
_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def parse_chart_json(text: str) -> Optional[dict[str, Any]]:
    """
    在 LLM 返回的文本里找出图表 JSON：
      1. 先匹配 ```json ... ``` 围栏
      2. 再退化到第一个看起来像顶层对象的 {...} 段
    解析失败时返回 None。
    """
    if not text:
        return None

    # ① fenced block
    m = _FENCE_RE.search(text)
    candidate: Optional[str] = m.group(1) if m else None

    # ② fallback: first {...}
    if candidate is None:
        start = text.find("{")
        end   = text.rfind("}")
        if start != -1 and end > start:
            candidate = text[start:end + 1]

    if candidate is None:
        return None
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


# ---------------------------------------------------------------
# 2. 规范化
# ---------------------------------------------------------------
def _coerce_chart_type(t: Any) -> str:
    if isinstance(t, str) and t.lower() in VALID_TYPES:
        return t.lower()
    return "bar"


def _coerce_series(raw: Any) -> list[dict[str, Any]]:
    """series 接受多种形态，统一为 [{name, data}]。"""
    if raw is None:
        return []
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        out: list[dict[str, Any]] = []
        for s in raw:
            name = s.get("name") or s.get("label") or "系列"
            data = s.get("data") if isinstance(s.get("data"), list) else []
            out.append({"name": str(name), "data": data})
        return out
    if isinstance(raw, list):
        return [{"name": "系列1", "data": list(raw)}]
    return []


def normalize_chart(chart: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """把可能不规整的 chart dict 改写成前端期望的形态；空值返回 None。"""
    if not isinstance(chart, dict):
        return None

    chart_type = _coerce_chart_type(chart.get("chartType") or chart.get("type"))
    title      = chart.get("title")
    x_axis_raw = chart.get("xAxis") or chart.get("x")
    series     = _coerce_series(chart.get("series"))

    if not series:
        return None

    # xAxis 必须是 list — 字符串/None 都视为缺失，由调用方 fallback
    x_axis: Optional[list[Any]] = x_axis_raw if isinstance(x_axis_raw, list) else None

    out: dict[str, Any] = {"chartType": chart_type, "series": series}
    if title:
        out["title"] = str(title)

    if chart_type in {"bar", "line"}:
        if x_axis is None:
            data_len = len(series[0].get("data") or [])
            x_axis = [str(i + 1) for i in range(data_len)]
        out["xAxis"] = x_axis
    elif chart_type == "scatter":
        if x_axis is not None:
            out["xAxis"] = x_axis

    return out


# ---------------------------------------------------------------
# 3. 兜底推断 — 没有 chart JSON 时根据 SQL 结果行形状自动构造
# ---------------------------------------------------------------
def infer_chart_from_rows(
    rows: Iterable[dict[str, Any]],
    columns: list[str],
    *,
    title: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    根据返回的列结构猜一个合理的图表：

    * 2 列且第二列数值     → bar
    * 3 列且第一列时间样   → line
    * 列数为 2 且类目较多  → bar
    * 否则                  → bar (用第一列做 x，剩余列做多 series)
    """
    rows = list(rows)
    if not rows or not columns or len(columns) < 2:
        return None

    # 时间字段判断 — 列名包含 date/time/year/month
    first_col = columns[0]
    looks_temporal = any(t in first_col.lower() for t in ("date", "time", "year", "month", "day"))

    x_data = [r[first_col] for r in rows]

    if len(columns) == 2:
        y_col = columns[1]
        y_data = [r[y_col] for r in rows]
        chart_type = "line" if looks_temporal else "bar"
        return {
            "chartType": chart_type,
            "title": title,
            "xAxis": [str(v) for v in x_data],
            "series": [{"name": y_col, "data": y_data}],
        }

    # 多列 → 多个 series，共享 x 轴
    series = []
    for col in columns[1:]:
        series.append({"name": col, "data": [r[col] for r in rows]})

    return {
        "chartType": "line" if looks_temporal else "bar",
        "title": title,
        "xAxis": [str(v) for v in x_data],
        "series": series,
    }
