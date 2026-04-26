"""
SQLAlchemy 连接工厂
==================

提供两套独立连接：

* business_engine / business_session  — 业务数据 (business.db)，**只读**
  - 在 SQL 层增加 ``PRAGMA query_only = ON`` 防止 LLM 生成的 SQL 破坏数据
* app_engine / app_session            — 会话与消息 (app.db)，读写

模块在导入时即创建 engine（SQLAlchemy 内部连接池），
之后通过 ``with get_business_session()`` / ``with get_app_session()`` 拿到 Session。
"""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings, BASE_DIR


# ---------- 路径 ----------
BUSINESS_DB_PATH: Path = (BASE_DIR / settings.BUSINESS_DB_PATH).resolve()
APP_DB_PATH: Path      = (BASE_DIR / settings.APP_DB_PATH).resolve()
APP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ---------- ORM 基类 (供 session_store 使用) ----------
Base = declarative_base()


# ---------- business.db：只读 ----------
business_engine: Engine = create_engine(
    f"sqlite:///{BUSINESS_DB_PATH}",
    future=True,
    connect_args={"check_same_thread": False},
)


@event.listens_for(business_engine, "connect")
def _set_business_readonly(dbapi_conn, _conn_record):
    """每次新连接被建立时强制为只读。"""
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA query_only = ON")
    cur.execute("PRAGMA foreign_keys = ON")
    cur.close()


BusinessSession = sessionmaker(
    bind=business_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


# ---------- app.db：读写 ----------
app_engine: Engine = create_engine(
    f"sqlite:///{APP_DB_PATH}",
    future=True,
    connect_args={"check_same_thread": False},
)


@event.listens_for(app_engine, "connect")
def _set_app_pragmas(dbapi_conn, _conn_record):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("PRAGMA journal_mode = WAL")
    cur.close()


AppSession = sessionmaker(
    bind=app_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


# ---------- Context manager 接口 ----------
@contextmanager
def get_business_session():
    """业务数据库 Session（只读，自动 close）。"""
    sess = BusinessSession()
    try:
        yield sess
    finally:
        sess.close()


@contextmanager
def get_app_session():
    """应用数据库 Session（读写，异常自动 rollback，正常 commit）。"""
    sess = AppSession()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()


# ---------- FastAPI 依赖 ----------
def get_business_db():
    sess = BusinessSession()
    try:
        yield sess
    finally:
        sess.close()


def get_app_db():
    sess = AppSession()
    try:
        yield sess
    finally:
        sess.close()


def init_app_db() -> None:
    """创建 app.db 中的所有表（幂等）。"""
    # 触发 ORM 类导入，注册到 metadata
    from . import session_store  # noqa: F401
    Base.metadata.create_all(app_engine)
