"""
POST /chat/stream — SSE 流式问答
=================================

接收 { session_id, message }，把 sql_agent.run_chat_flow 产出的事件
转成 SSE 推给前端：

    event: thinking
    data:  {"content": "..."}

    event: sql
    data:  {"sql": "..."}

    event: chart
    data:  {chartType, ...}

    event: answer
    data:  {"content": "..."}        # 增量

    event: error
    data:  {"message": "..."}

    event: done
    data:  {}

执行结束后，最终的 thinking / sql / chart / 完整 answer 会作为一条 assistant 消息
持久化到 app.db。
"""

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from database import session_store as ss
from database.connection import get_app_session
from models.message import ChatRequest
from services import memory_service
from services.sql_agent import run_chat_flow


logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def _to_sse(event: str, payload) -> dict:
    """sse-starlette 接受 dict 形式的 SSE event。"""
    return {"event": event, "data": json.dumps(payload, ensure_ascii=False)}


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    # 1) 校验会话存在 + 持久化用户消息 + 加载历史
    with get_app_session() as db:
        s = ss.get_session(db, body.session_id)
        if not s:
            raise HTTPException(status_code=404, detail="会话不存在")
        memory_service.persist_user_message(db, body.session_id, body.message)
        history = memory_service.load_history(db, body.session_id)

    # 2) 在生成器里跑 agent flow，并把最终结果落库
    async def gen() -> AsyncIterator[dict]:
        final_thinking = ""
        final_sql = ""
        final_chart = None
        final_answer = ""
        had_error = False

        try:
            async for evt in run_chat_flow(body.message, history):
                t = evt["type"]
                d = evt.get("data")

                if t == "thinking":
                    final_thinking = d
                    yield _to_sse("thinking", {"content": d})
                elif t == "sql":
                    final_sql = d
                    yield _to_sse("sql", {"sql": d})
                elif t == "chart":
                    final_chart = d
                    yield _to_sse("chart", d)
                elif t == "answer":
                    final_answer = d
                    yield _to_sse("answer", {"content": d})
                elif t == "error":
                    had_error = True
                    yield _to_sse("error", {"message": d})
                elif t == "done":
                    summary = d if isinstance(d, dict) else {}
                    final_answer  = summary.get("final_answer",  final_answer)
                    final_sql     = summary.get("final_sql",     final_sql)
                    final_chart   = summary.get("final_chart",   final_chart)
                    final_thinking = summary.get("thinking",     final_thinking)
        except Exception as e:                                   # noqa: BLE001
            logger.exception("chat stream failed")
            had_error = True
            yield _to_sse("error", {"message": f"内部错误：{e}"})

        # 持久化（即便出错，也保存当前可见内容供前端历史回看）
        try:
            with get_app_session() as db2:
                memory_service.persist_assistant_message(
                    db2,
                    body.session_id,
                    content=final_answer or ("（生成失败）" if had_error else ""),
                    thinking=final_thinking or None,
                    sql=final_sql or None,
                    chart=final_chart,
                )
        except Exception:                                        # noqa: BLE001
            logger.exception("persist assistant message failed")

        yield _to_sse("done", {})

    return EventSourceResponse(gen(), ping=15)
