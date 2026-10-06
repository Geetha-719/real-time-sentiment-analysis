"""Application settings loaded from environment / backend/.env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+psycopg://sentiment:sentiment@localhost:5432/sentiment_db"
    postgres_admin_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    postgres_db: str = "sentiment_db"
    postgres_user: str = "sentiment"
    postgres_password: str = "sentiment"

    # JWT
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # App
    app_name: str = "Real-Time Sentiment Analysis System"
    environment: str = "development"
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    public_base_url: str = "http://localhost:5173"

    # Password reset
    password_reset_expire_minutes: int = 30

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = "no-reply@sentiment.local"

    # Live sources
    news_api_key: str = ""
    gnews_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "sentiment-dashboard/1.0"

    model_dir: str = "ml/models"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "dev", "local"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
