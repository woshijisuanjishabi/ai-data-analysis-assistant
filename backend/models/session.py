"""会话相关 Pydantic 模型（HTTP I/O）。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)


class SessionUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
