"""通过 HTTP 客户端测试 /chat/stream 的 SSE 输出。"""
import asyncio
import json
import sys

import httpx


BASE = "http://127.0.0.1:8000"


async def main(question: str) -> None:
    async with httpx.AsyncClient(timeout=180.0) as cli:
        # 创建会话
        r = await cli.post(f"{BASE}/sessions", json={"title": "SSE 测试"})
        r.raise_for_status()
        sid = r.json()["id"]
        print(f"[create] session_id = {sid}")

        # 发起 SSE 请求
        print(f"\n[stream] 问题: {question}\n")
        async with cli.stream(
            "POST",
            f"{BASE}/chat/stream",
            json={"session_id": sid, "message": question},
            headers={"Accept": "text/event-stream"},
        ) as resp:
            buf = ""
            async for chunk in resp.aiter_text():
                buf += chunk
                while "\n\n" in buf:
                    frame, buf = buf.split("\n\n", 1)
                    if not frame.strip():
                        continue
                    event = "message"
                    data = ""
                    for line in frame.splitlines():
                        if line.startswith("event:"):
                            event = line[6:].strip()
                        elif line.startswith("data:"):
                            data = (data + line[5:].lstrip()) if data else line[5:].lstrip()
                    handle(event, data)

        # 验证消息已落库
        r = await cli.get(f"{BASE}/sessions/{sid}/messages")
        msgs = r.json()
        print(f"\n[persisted] 共 {len(msgs)} 条消息:")
        for m in msgs:
            print(f"  - [{m['role']}] {m['content'][:60]}...  sql={'✓' if m['sql'] else '·'}  chart={'✓' if m['chart'] else '·'}")


def handle(event: str, data: str) -> None:
    try:
        obj = json.loads(data) if data else {}
    except Exception:
        obj = {"raw": data}

    if event == "thinking":
        c = obj.get("content", "")
        sys.stdout.write(f"\r[thinking 累计 {len(c)} 字]")
        sys.stdout.flush()
    elif event == "sql":
        print(f"\n[sql]\n{obj.get('sql','')}")
    elif event == "answer":
        c = obj.get("content", "")
        sys.stdout.write(f"\r[answer 累计 {len(c)} 字] {c[-40:]}")
        sys.stdout.flush()
    elif event == "chart":
        print(f"\n\n[chart] type={obj.get('chartType')} title={obj.get('title','')}")
        print(f"        xAxis: {obj.get('xAxis')}")
        for s in obj.get("series", []):
            print(f"        series '{s.get('name')}': {s.get('data')}")
    elif event == "error":
        print(f"\n[ERROR] {obj.get('message','')}")
    elif event == "done":
        print(f"\n[done]")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "各品类的销售额对比"
    asyncio.run(main(q))
