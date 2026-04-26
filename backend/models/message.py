"""消息相关 Pydantic 模型（HTTP I/O）。"""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChartJSON(BaseModel):
    """LLM 输出 / 前端渲染用的图表载体。"""
    chartType: Literal["bar", "line", "pie", "scatter"]
    title: Optional[str] = None
    xAxis: Optional[list[Any]] = None
    series: list[dict[str, Any]] = Field(default_factory=list)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    thinking: Optional[str] = None
    sql: Optional[str] = None
    chart: Optional[ChartJSON] = None
    created_at: datetime


class ChatRequest(BaseModel):
    """POST /chat/stream 入参。"""
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=4000)
