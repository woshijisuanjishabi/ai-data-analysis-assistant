"""
Session / Message ORM + CRUD
============================

* sessions : 会话表 (id, title, created_at, updated_at)
* messages : 消息表 (id, session_id, role, content, thinking, sql, chart, created_at)

CRUD 函数都接受外部传入的 ``Session``（与 connection.py 的 context manager 配合），
保持事务边界由调用方控制。
"""

import json
import secrets
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text, func, select
)
from sqlalchemy.orm import Mapped, relationship, Session

from .connection import Base


# ---------- 工具 ----------
def _new_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6)}"


def _now() -> datetime:
    return datetime.utcnow()


# ---------- ORM ----------
class SessionORM(Base):
    __tablename__ = "sessions"

    id         = Column(String(40), primary_key=True)
    title      = Column(String(200), nullable=False, default="新会话")
    created_at = Column(DateTime, nullable=False, default=_now)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    messages = relationship(
        "MessageORM",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageORM.created_at.asc()",
    )


class MessageORM(Base):
    __tablename__ = "messages"

    id          = Column(String(40), primary_key=True)
    session_id  = Column(String(40), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role        = Column(String(16), nullable=False)         # user / assistant
    content     = Column(Text,        nullable=False, default="")
    thinking    = Column(Text,        nullable=True)
    sql         = Column(Text,        nullable=True)
    chart_json  = Column(Text,        nullable=True)          # 序列化后的 ChartJSON
    created_at  = Column(DateTime,    nullable=False, default=_now)

    session = relationship("SessionORM", back_populates="messages")

    # 便利属性 — 外部按字典访问
    @property
    def chart(self) -> Optional[dict[str, Any]]:
        if not self.chart_json:
            return None
        try:
            return json.loads(self.chart_json)
        except Exception:
            return None


# =========================================================
# Session CRUD
# =========================================================
def list_sessions(db: Session) -> list[SessionORM]:
    rows = db.execute(
        select(SessionORM).order_by(SessionORM.updated_at.desc())
    ).scalars().all()
    return list(rows)


def get_session(db: Session, sid: str) -> Optional[SessionORM]:
    return db.get(SessionORM, sid)


def create_session(db: Session, title: Optional[str] = None) -> SessionORM:
    s = SessionORM(id=_new_id("s"), title=title or "新会话")
    db.add(s)
    db.flush()
    return s


def rename_session(db: Session, sid: str, title: str) -> Optional[SessionORM]:
    s = db.get(SessionORM, sid)
    if not s:
        return None
    s.title = title
    s.updated_at = _now()
    db.flush()
    return s


def delete_session(db: Session, sid: str) -> bool:
    s = db.get(SessionORM, sid)
    if not s:
        return False
    db.delete(s)
    db.flush()
    return True


def session_to_dict(s: SessionORM, db: Session) -> dict[str, Any]:
    """把 ORM 转换为 API 输出（含 message_count）。"""
    msg_count = db.scalar(
        select(func.count(MessageORM.id)).where(MessageORM.session_id == s.id)
    )
    return {
        "id": s.id,
        "title": s.title,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
        "message_count": int(msg_count or 0),
    }


# =========================================================
# Message CRUD
# =========================================================
def list_messages(db: Session, sid: str) -> list[MessageORM]:
    rows = db.execute(
        select(MessageORM)
        .where(MessageORM.session_id == sid)
        .order_by(MessageORM.created_at.asc())
    ).scalars().all()
    return list(rows)


def append_message(
    db: Session,
    *,
    session_id: str,
    role: str,
    content: str,
    thinking: Optional[str] = None,
    sql: Optional[str] = None,
    chart: Optional[dict[str, Any]] = None,
) -> MessageORM:
    m = MessageORM(
        id=_new_id("m"),
        session_id=session_id,
        role=role,
        content=content,
        thinking=thinking,
        sql=sql,
        chart_json=json.dumps(chart, ensure_ascii=False) if chart else None,
    )
    db.add(m)

    # 同步刷新 session.updated_at
    s = db.get(SessionORM, session_id)
    if s:
        s.updated_at = _now()

    db.flush()
    return m


def message_to_dict(m: MessageORM) -> dict[str, Any]:
    return {
        "id": m.id,
        "session_id": m.session_id,
        "role": m.role,
        "content": m.content,
        "thinking": m.thinking,
        "sql": m.sql,
        "chart": m.chart,
        "created_at": m.created_at,
    }
