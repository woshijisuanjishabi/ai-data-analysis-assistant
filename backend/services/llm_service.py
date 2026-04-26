"""
LLM 服务 — 封装 ChatTongyi (Qwen3) 调用。

提供两种使用方式：

* ``get_llm()``        - 返回非流式 LLM 实例
* ``get_streaming_llm()`` - 返回 streaming=True 的 LLM 实例

以及便利方法：

* ``invoke(messages)``    - 非流式一次性调用
* ``stream(messages)``    - 同步流式生成器，逐 chunk 产出文本
"""

from typing import Iterator

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import BaseMessage, AIMessageChunk

from config import settings


def _build_llm(streaming: bool) -> ChatTongyi:
    if not settings.DASHSCOPE_API_KEY or settings.DASHSCOPE_API_KEY == "your_dashscope_api_key_here":
        raise RuntimeError(
            "DASHSCOPE_API_KEY 未设置。请在 backend/.env 中填入真实 Key。"
        )
    return ChatTongyi(
        model=settings.QWEN_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
        streaming=streaming,
    )


def get_llm() -> ChatTongyi:
    return _build_llm(streaming=False)


def get_streaming_llm() -> ChatTongyi:
    return _build_llm(streaming=True)


def invoke(messages: list[BaseMessage]) -> str:
    """非流式调用，返回完整文本。"""
    resp = get_llm().invoke(messages)
    return getattr(resp, "content", "") or ""


def stream(messages: list[BaseMessage]) -> Iterator[str]:
    """流式调用，逐 chunk yield 文本片段（不含空 chunk）。"""
    llm = get_streaming_llm()
    for chunk in llm.stream(messages):
        if isinstance(chunk, AIMessageChunk):
            piece = chunk.content
        else:
            piece = getattr(chunk, "content", "")
        if piece:
            yield piece
