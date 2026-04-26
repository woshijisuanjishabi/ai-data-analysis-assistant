"""把 /chat/stream 的原始 SSE 帧打印出来，做接口规范取证。"""
import asyncio
import sys

import httpx

BASE = "http://127.0.0.1:8000"


async def main(question: str) -> None:
    async with httpx.AsyncClient(timeout=180.0) as cli:
        sid = (await cli.post(f"{BASE}/sessions", json={"title": "SSE frame dump"})).json()["id"]
        print(f"# session_id = {sid}\n")

        async with cli.stream(
            "POST",
            f"{BASE}/chat/stream",
            json={"session_id": sid, "message": question},
            headers={"Accept": "text/event-stream"},
        ) as resp:
            print(f"# HTTP {resp.status_code}, headers={dict(resp.headers)}\n")
            buf = ""
            event_summary: dict[str, int] = {}
            samples: dict[str, str] = {}
            chunks_seen = 0
            async for chunk in resp.aiter_text():
                chunks_seen += 1
                buf += chunk
                # 兼容 \r\n\r\n 和 \n\n
                buf = buf.replace("\r\n", "\n")
                while "\n\n" in buf:
                    frame, buf = buf.split("\n\n", 1)
                    frame = frame.strip()
                    if not frame or frame.startswith(":"):
                        continue
                    event = "message"
                    data_lines: list[str] = []
                    for line in frame.splitlines():
                        if line.startswith("event:"):
                            event = line[6:].strip()
                        elif line.startswith("data:"):
                            data_lines.append(line[5:].lstrip())
                    data = "\n".join(data_lines)
                    event_summary[event] = event_summary.get(event, 0) + 1
                    if event not in samples:
                        samples[event] = data

            print(f"# total chunks_seen={chunks_seen}, leftover_buf_len={len(buf)}\n")
            print("# 事件统计:")
            for k, v in event_summary.items():
                print(f"  {k}: {v}")
            print("\n# 各事件首帧 data 样例:")
            for k, v in samples.items():
                print(f"  [{k}] {v[:200]}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "客户区域分布"))
