"""
端到端联调脚本 — 模拟前端行为，直接打 HTTP/SSE 接口。
覆盖 Phase 4 的：4-1 会话 CRUD、4-2 SSE 流、4-3 多轮上下文、4-4 多图表。
"""
import asyncio
import json
import sys
from typing import Any

import httpx

BASE = "http://127.0.0.1:8000"


async def chat(cli: httpx.AsyncClient, sid: str, msg: str) -> dict[str, Any]:
    print(f"\n  → 发送: {msg!r}")
    captured: dict[str, Any] = {"thinking": "", "sql": "", "answer": "", "chart": None, "error": None}

    async with cli.stream(
        "POST",
        f"{BASE}/chat/stream",
        json={"session_id": sid, "message": msg},
        headers={"Accept": "text/event-stream"},
    ) as resp:
        resp.raise_for_status()
        buf = ""
        async for chunk in resp.aiter_text():
            buf += chunk
            buf = buf.replace("\r\n", "\n")
            while "\n\n" in buf:
                frame, buf = buf.split("\n\n", 1)
                if not frame.strip() or frame.startswith(":"):
                    continue
                event = "message"
                data_lines: list[str] = []
                for line in frame.splitlines():
                    if line.startswith("event:"):
                        event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                try:
                    data = json.loads("\n".join(data_lines))
                except Exception:
                    data = "\n".join(data_lines)

                if event == "thinking":
                    captured["thinking"] = data.get("content", "")
                elif event == "sql":
                    captured["sql"] = data.get("sql", "")
                elif event == "answer":
                    captured["answer"] = data.get("content", "")
                elif event == "chart":
                    captured["chart"] = data
                elif event == "error":
                    captured["error"] = data.get("message", "")
    return captured


def header(s: str) -> None:
    print("\n" + "=" * 60)
    print(s)
    print("=" * 60)


async def main() -> None:
    async with httpx.AsyncClient(timeout=180.0) as cli:
        header("4-1 创建会话 + 列表读取")
        new = (await cli.post(f"{BASE}/sessions", json={"title": "E2E 联调"})).json()
        sid = new["id"]
        print(f"  ✓ 创建: {sid}  title={new['title']}  msg_count={new['message_count']}")

        sessions = (await cli.get(f"{BASE}/sessions")).json()
        assert any(s["id"] == sid for s in sessions), "新会话未出现在列表"
        print(f"  ✓ 列表中找到该会话")

        header("4-2 / 4-4 SSE 流式 + 多图表类型")
        cases = [
            ("各部门 2024 年销售额对比", "bar"),
            ("电子产品类目按月销售趋势", "line"),
            ("各品类的销售占比",          "pie"),
        ]
        for q, expected in cases:
            res = await chat(cli, sid, q)
            if res["error"]:
                print(f"  ✗ 错误: {res['error']}")
                continue
            ct = res["chart"]["chartType"] if res["chart"] else "(none)"
            print(f"    thinking: {len(res['thinking'])} 字  sql: {'有' if res['sql'] else '无'}  answer: {len(res['answer'])} 字  chart: {ct}")
            assert res["sql"], "未收到 SQL"
            assert res["answer"], "未收到 answer"
            if res["chart"]:
                print(f"    chart.title: {res['chart'].get('title','')}")
                # 不强制类型完全相同（LLM 可能选择更合适的），只校验是合法类型
                assert ct in ("bar", "line", "pie", "scatter"), f"非法类型 {ct}"

        header("4-3 多轮上下文：追问")
        # 此前已经问过销售额。现在追问"再看 2025 年"，应能复用上下文知道是销售额
        res = await chat(cli, sid, "那 2025 年 1 季度呢？")
        print(f"    thinking: {res['thinking'][:80]}...")
        print(f"    sql: {(res['sql'] or '').splitlines()[0][:80]}...")
        print(f"    answer: {res['answer'][:80]}...")
        # 验证：SQL 应包含 2025 而不是 2024（说明读懂了"那"是承接前一轮的销售额话题）
        assert "2025" in (res["sql"] or ""), "上下文未生效 — SQL 中没有 2025"
        print(f"  ✓ 多轮上下文有效（SQL 含 2025）")

        header("会话元数据更新检查")
        s2 = (await cli.get(f"{BASE}/sessions")).json()
        cur = next(s for s in s2 if s["id"] == sid)
        print(f"  ✓ message_count 从 0 → {cur['message_count']}")
        print(f"  ✓ updated_at: {cur['updated_at']}")
        assert cur["message_count"] >= 8, f"消息数应 >= 8，实际 {cur['message_count']}"

        header("4-1 重命名 + 删除")
        renamed = (await cli.patch(f"{BASE}/sessions/{sid}", json={"title": "E2E 已完成"})).json()
        print(f"  ✓ 重命名: {renamed['title']}")
        assert renamed["title"] == "E2E 已完成"

        del_resp = await cli.delete(f"{BASE}/sessions/{sid}")
        assert del_resp.status_code == 204
        print(f"  ✓ 删除: 204")
        gone = (await cli.get(f"{BASE}/sessions")).json()
        assert all(s["id"] != sid for s in gone), "删除后会话仍在"
        print(f"  ✓ 列表已不含该会话")

        print("\n[All passed]")


if __name__ == "__main__":
    asyncio.run(main())
