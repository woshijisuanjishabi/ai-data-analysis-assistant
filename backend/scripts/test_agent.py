"""端到端测试 SQL Agent。"""
import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.sql_agent import run_chat_flow


async def run(question: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"问题：{question}")
    print("=" * 70)

    async for evt in run_chat_flow(question, history=[]):
        t = evt["type"]
        if t == "thinking":
            # 只打 thinking 第一次和最后一次（避免日志爆炸）
            content = evt["data"]
            print(f"\n[thinking] (累计 {len(content)} 字)")
            print("  " + content[-200:].replace("\n", "\n  "))
        elif t == "sql":
            print(f"\n[sql]\n{evt['data']}")
        elif t == "answer":
            # 只打最终长度，避免日志爆炸
            print(f"\r[answer 累计 {len(evt['data'])} 字] {evt['data'][:60]}...", end="", flush=True)
        elif t == "chart":
            c = evt["data"]
            print(f"\n\n[chart] type={c['chartType']}  title={c.get('title','')}")
            print(f"   xAxis: {c.get('xAxis', '(none)')}")
            for s in c.get("series", []):
                print(f"   series '{s['name']}': {s['data']}")
        elif t == "error":
            print(f"\n[ERROR] {evt['data']}")
        elif t == "done":
            print(f"\n[done] 最终回答字数: {len(evt.get('data', {}).get('final_answer', ''))}")


async def main() -> None:
    questions = sys.argv[1:] or [
        "各部门 2024 年的销售总额",
        "电子产品中销量 TOP5 的产品",
    ]
    for q in questions:
        await run(q)


if __name__ == "__main__":
    asyncio.run(main())
