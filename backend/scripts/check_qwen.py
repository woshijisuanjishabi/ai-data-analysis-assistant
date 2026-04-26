"""
Qwen3 (DashScope) 连通性验证脚本。

使用方式：
    python scripts/check_qwen.py                  # 发默认问题
    python scripts/check_qwen.py "你好，简单介绍自己"  # 自定义问题

校验项：
  1. 是否从 .env 成功读取到 DASHSCOPE_API_KEY
  2. 能否调用 ChatTongyi 完成一次非流式对话
  3. 能否完成一次流式对话（streaming=True）
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import settings


def check_api_key() -> bool:
    key = settings.DASHSCOPE_API_KEY
    if not key or key == "your_dashscope_api_key_here":
        print("[ERROR] DASHSCOPE_API_KEY 未设置。请编辑 backend/.env 填入真实的 API Key。")
        print("        申请地址：https://dashscope.console.aliyun.com/apiKey")
        return False
    masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "***"
    print(f"[OK] DASHSCOPE_API_KEY 已加载（{masked}），模型：{settings.QWEN_MODEL}")
    return True


def check_non_streaming(prompt: str) -> bool:
    print("\n--- 非流式调用测试 ---")
    try:
        from langchain_community.chat_models.tongyi import ChatTongyi
        from langchain_core.messages import HumanMessage
    except ImportError as e:
        print(f"[ERROR] 依赖缺失: {e}")
        return False

    llm = ChatTongyi(
        model=settings.QWEN_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
        streaming=False,
    )
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        text = getattr(resp, "content", str(resp))
        print(f"[OK] 模型回复：\n{text}")
        return True
    except Exception as e:
        print(f"[ERROR] 调用失败：{type(e).__name__}: {e}")
        return False


def check_streaming(prompt: str) -> bool:
    print("\n--- 流式调用测试 ---")
    try:
        from langchain_community.chat_models.tongyi import ChatTongyi
        from langchain_core.messages import HumanMessage
    except ImportError as e:
        print(f"[ERROR] 依赖缺失: {e}")
        return False

    llm = ChatTongyi(
        model=settings.QWEN_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
        streaming=True,
    )
    try:
        print("[OK] 流式输出：", end="", flush=True)
        chunks = 0
        for chunk in llm.stream([HumanMessage(content=prompt)]):
            piece = getattr(chunk, "content", "")
            if piece:
                print(piece, end="", flush=True)
                chunks += 1
        print(f"\n[OK] 流式完成，收到 {chunks} 个 chunk")
        return True
    except Exception as e:
        print(f"\n[ERROR] 流式调用失败：{type(e).__name__}: {e}")
        return False


def main() -> int:
    default_prompt = "你好，请用一句话介绍自己。"
    prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt
    print(f"测试问题：{prompt}")

    if not check_api_key():
        return 1

    ok1 = check_non_streaming(prompt)
    ok2 = check_streaming("用三句话解释什么是数据分析。")

    print("\n=== 总结 ===")
    print(f"  非流式: {'[OK]' if ok1 else '[FAIL]'}")
    print(f"  流式  : {'[OK]' if ok2 else '[FAIL]'}")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
