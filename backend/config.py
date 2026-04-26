from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DASHSCOPE_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-plus"

    BUSINESS_DB_PATH: str = "database/business.db"
    APP_DB_PATH: str = "database/app.db"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    @property
    def business_db_url(self) -> str:
        path = (BASE_DIR / self.BUSINESS_DB_PATH).resolve()
        return f"sqlite:///{path}"

    @property
    def app_db_url(self) -> str:
        path = (BASE_DIR / self.APP_DB_PATH).resolve()
        return f"sqlite:///{path}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
