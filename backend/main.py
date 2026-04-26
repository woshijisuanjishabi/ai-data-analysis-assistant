import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.connection import init_app_db
from routers import chat as chat_router
from routers import schema as schema_router
from routers import session as session_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


app = FastAPI(
    title="智能数据分析系统",
    description="基于 Qwen3 + LangChain SQL Agent 的自然语言数据分析服务",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_app_db()


# ----- 路由 -----
app.include_router(session_router.router)
app.include_router(schema_router.router)
app.include_router(chat_router.router)


@app.get("/")
def root():
    return {
        "name": "智能数据分析系统",
        "version": "0.2.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
