"""
边缘场景测试 (Phase 4-5)
========================

用例：
* 空结果集     — 查一个表里不存在的范围（2030 年的销售）
* 非数据问题   — 问"你好" / "你是谁"
* 数据库无关   — 问"今天天气"

验证：每个场景都不应让流挂起或崩溃；至少要能 done。
"""
import asyncio
import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"


async def chat_capture(cli: httpx.AsyncClient, sid: str, msg: str) -> dict:
    out = {"thinking": "", "sql_count": 0, "sql_last": "", "answer": "", "chart": None, "error": None, "done": False, "events": []}
    async with cli.stream("POST", f"{BASE}/chat/stream",
                          json={"session_id": sid, "message": msg},
                          headers={"Accept": "text/event-stream"}) as resp:
        resp.raise_for_status()
        buf = ""
        async for chunk in resp.aiter_text():
            buf += chunk
            buf = buf.replace("\r\n", "\n")
            while "\n\n" in buf:
                frame, buf = buf.split("\n\n", 1)
                if not frame.strip() or frame.startswith(":"):
                    continue
                event = "message"; data_lines = []
                for line in frame.splitlines():
                    if line.startswith("event:"): event = line[6:].strip()
                    elif line.startswith("data:"): data_lines.append(line[5:].lstrip())
                try: data = json.loads("\n".join(data_lines))
                except Exception: data = "\n".join(data_lines)
                out["events"].append(event)
                if event == "thinking": out["thinking"] = data.get("content", "")
                elif event == "sql":
                    out["sql_count"] += 1
                    out["sql_last"]   = data.get("sql", "")
                elif event == "answer": out["answer"] = data.get("content", "")
                elif event == "chart": out["chart"] = data
                elif event == "error": out["error"] = data.get("message", "")
                elif event == "done": out["done"] = True
    return out


async def main() -> None:
    async with httpx.AsyncClient(timeout=180.0) as cli:
        sid = (await cli.post(f"{BASE}/sessions", json={"title": "edge"})).json()["id"]
        print(f"# session_id = {sid}\n")

        cases = [
            ("空结果",     "查一下 2030 年 1 月的销售订单"),
            ("非数据问题", "你好，你是谁？"),
            ("数据库外",   "今天上海天气怎么样？"),
            ("模糊问题",   "随便看点什么"),
        ]
        for label, q in cases:
            print(f"== {label} == 问: {q}")
            try:
                r = await chat_capture(cli, sid, q)
                events = " → ".join(r["events"])
                print(f"   事件序列: {events}")
                print(f"   thinking:{len(r['thinking'])}字  sql:{r['sql_count']}次  answer:{len(r['answer'])}字  chart:{('有' if r['chart'] else '无')}  done:{r['done']}  error:{r['error']}")
                print(f"   answer片段: {r['answer'][:80]}...")
                if r["sql_count"] > 1:
                    print(f"   ★ SQL 重试触发 (3-10) — 共发了 {r['sql_count']} 次 sql 事件")
                assert r["done"], "未收到 done 事件"
            except Exception as e:
                print(f"   ✗ 抛错: {type(e).__name__}: {e}")
            print()

        # 清理
        await cli.delete(f"{BASE}/sessions/{sid}")
        print("[Edge cases all completed]")


if __name__ == "__main__":
    asyncio.run(main())
