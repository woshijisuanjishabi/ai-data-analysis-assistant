"""
端到端回归 (Phase 4-6)
======================

模拟一个完整的用户旅程：
  ① 启动 → GET /sessions（应为空）
  ② 新建会话 A
  ③ 在 A 内问 3 个问题（验证 message_count 同步增长）
  ④ 新建会话 B
  ⑤ 在 B 内问 1 个问题
  ⑥ 切回 A → GET /sessions/A/messages 应能拿到完整历史（含 sql/chart）
  ⑦ 重命名 A
  ⑧ 删除 B
  ⑨ 最终 GET /sessions 应只剩 A

目的：模拟"刷新浏览器"的状态保留场景（关键在 GET /sessions 与 GET /sessions/{id}/messages
能复原所有 user/assistant 消息及结构化字段）。
"""
import asyncio
import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"


async def stream_chat(cli, sid, msg):
    async with cli.stream("POST", f"{BASE}/chat/stream",
                          json={"session_id": sid, "message": msg},
                          headers={"Accept": "text/event-stream"}) as resp:
        resp.raise_for_status()
        async for chunk in resp.aiter_text():
            pass  # 消费完整个流即可


def step(s):
    print(f"\n--- {s} ---")


async def main():
    async with httpx.AsyncClient(timeout=300.0) as cli:
        # 清理
        for s in (await cli.get(f"{BASE}/sessions")).json():
            await cli.delete(f"{BASE}/sessions/{s['id']}")

        step("① 初始 GET /sessions")
        sessions = (await cli.get(f"{BASE}/sessions")).json()
        print(f"   sessions: {len(sessions)} 条")
        assert sessions == [], "初始应为空"

        step("② 新建会话 A")
        a = (await cli.post(f"{BASE}/sessions", json={"title": "会话 A"})).json()
        sid_a = a["id"]
        print(f"   {sid_a}  msg_count={a['message_count']}")

        step("③ A 内问 3 个问题")
        for q in ["销售部有几个员工", "客户分布在哪些区域", "电子产品最贵的 3 款"]:
            print(f"     问: {q}")
            await stream_chat(cli, sid_a, q)
        a2 = next(s for s in (await cli.get(f"{BASE}/sessions")).json() if s["id"] == sid_a)
        print(f"   现在 message_count = {a2['message_count']}")
        assert a2["message_count"] == 6, f"期待 6，实际 {a2['message_count']}"

        step("④ 新建会话 B")
        b = (await cli.post(f"{BASE}/sessions", json={"title": "会话 B"})).json()
        sid_b = b["id"]
        print(f"   {sid_b}")

        step("⑤ B 内问 1 个问题")
        await stream_chat(cli, sid_b, "各部门的员工人数")

        step("⑥ 切回 A：GET /sessions/A/messages 复原历史")
        a_msgs = (await cli.get(f"{BASE}/sessions/{sid_a}/messages")).json()
        print(f"   A 历史: {len(a_msgs)} 条")
        roles = [m["role"] for m in a_msgs]
        print(f"   role 序列: {roles}")
        assert roles == ["user", "assistant"] * 3, f"role 序列异常: {roles}"

        # 检查 assistant 消息的结构化字段是否完整保留
        for i, m in enumerate(a_msgs):
            if m["role"] == "assistant":
                has_sql   = "✓" if m["sql"] else "✗"
                has_chart = "✓" if m["chart"] else "✗"
                has_think = "✓" if m["thinking"] else "✗"
                preview   = (m["content"] or "")[:50]
                print(f"     [{i}] sql{has_sql} chart{has_chart} thinking{has_think}  {preview}...")
                assert m["sql"], "assistant 消息应有 sql"
                assert m["chart"], "assistant 消息应有 chart"

        step("⑦ 重命名 A")
        renamed = (await cli.patch(f"{BASE}/sessions/{sid_a}", json={"title": "重要分析"})).json()
        print(f"   title: {renamed['title']}")

        step("⑧ 删除 B")
        r = await cli.delete(f"{BASE}/sessions/{sid_b}")
        assert r.status_code == 204
        print(f"   204")

        step("⑨ 最终 GET /sessions")
        final = (await cli.get(f"{BASE}/sessions")).json()
        print(f"   sessions: {[(s['title'], s['message_count']) for s in final]}")
        assert len(final) == 1
        assert final[0]["id"] == sid_a
        assert final[0]["title"] == "重要分析"

        # 清理 A
        await cli.delete(f"{BASE}/sessions/{sid_a}")

        print("\n[Regression passed]")


if __name__ == "__main__":
    asyncio.run(main())
