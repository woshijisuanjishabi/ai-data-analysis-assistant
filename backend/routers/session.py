"""
/sessions  CRUD + 历史消息查询
==============================

* GET    /sessions                    — 列出所有会话
* POST   /sessions                    — 新建会话
* PATCH  /sessions/{sid}              — 重命名
* DELETE /sessions/{sid}              — 删除
* GET    /sessions/{sid}/messages     — 历史消息
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import session_store as ss
from database.connection import get_app_db
from models.message import MessageOut
from models.session import SessionCreate, SessionOut, SessionUpdate


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
def list_all(db: Session = Depends(get_app_db)):
    return [ss.session_to_dict(s, db) for s in ss.list_sessions(db)]


@router.post("", response_model=SessionOut, status_code=201)
def create(body: SessionCreate, db: Session = Depends(get_app_db)):
    s = ss.create_session(db, title=body.title)
    db.commit()
    return ss.session_to_dict(s, db)


@router.patch("/{sid}", response_model=SessionOut)
def rename(sid: str, body: SessionUpdate, db: Session = Depends(get_app_db)):
    s = ss.rename_session(db, sid, body.title)
    if not s:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.commit()
    return ss.session_to_dict(s, db)


@router.delete("/{sid}", status_code=204)
def delete(sid: str, db: Session = Depends(get_app_db)):
    ok = ss.delete_session(db, sid)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.commit()
    return None


@router.get("/{sid}/messages", response_model=list[MessageOut])
def list_msgs(sid: str, db: Session = Depends(get_app_db)):
    s = ss.get_session(db, sid)
    if not s:
        raise HTTPException(status_code=404, detail="会话不存在")
    return [ss.message_to_dict(m) for m in ss.list_messages(db, sid)]
