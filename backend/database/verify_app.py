"""验证 app.db ORM + 业务库只读保护。"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import text

from database.connection import init_app_db, get_app_session, get_business_session
from database import session_store as ss


def main() -> None:
    init_app_db()
    print("[1] app.db 初始化完成")

    # 创建一个会话和两条消息
    with get_app_session() as db:
        s1 = ss.create_session(db, title="测试会话1")
        print(f"[2] 创建会话: {s1.id} / {s1.title}")

        ss.append_message(db, session_id=s1.id, role="user", content="你好")
        ss.append_message(
            db,
            session_id=s1.id,
            role="assistant",
            content="你好！",
            sql="SELECT 1",
            thinking="先打个招呼",
            chart={
                "chartType": "bar",
                "title": "demo",
                "xAxis": ["a", "b"],
                "series": [{"name": "x", "data": [1, 2]}],
            },
        )

    with get_app_session() as db:
        sessions = ss.list_sessions(db)
        print(f"[3] 当前会话数: {len(sessions)}")
        for s in sessions:
            d = ss.session_to_dict(s, db)
            print(f"    - {d['id']}  title={d['title']}  msgs={d['message_count']}")

        msgs = ss.list_messages(db, s1.id)
        print(f"[4] 会话 {s1.id} 消息: {len(msgs)} 条")
        for m in msgs:
            chart_flag = "yes" if m.chart else "no"
            print(f"    - [{m.role}] {m.content[:30]}  sql={'yes' if m.sql else 'no'}  chart={chart_flag}")

    # 业务库只读测试
    with get_business_session() as db:
        rows = db.execute(text("SELECT name FROM departments")).fetchall()
        print(f"[5] business.db 部门: {[r[0] for r in rows]}")

        try:
            db.execute(text(
                "INSERT INTO departments(id, name, manager_name, created_at) "
                "VALUES (99, 'X', 'X', '2026-01-01')"
            ))
            print("[6] !!! 写入未被拦截 — 不安全")
        except Exception as e:
            print(f"[6] [OK] 业务库写入被正确拦截 ({type(e).__name__})")

    # 清理
    with get_app_session() as db:
        for s in ss.list_sessions(db):
            ss.delete_session(db, s.id)
        print("[7] 已清理所有测试会话")


if __name__ == "__main__":
    main()
