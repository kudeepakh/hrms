"""Centralized configuration using Pydantic BaseSettings.

All environment variables are loaded once and validated at startup.
Access via: `from app.config import settings`
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings — loaded from environment / .env file."""

    # ── App ──
    APP_NAME: str = "HRMS Agent API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # ── MongoDB ──
    MONGODB_URI: str = "mongodb://mongo:27017"
    MONGODB_DB_NAME: str = "hrms"

    # ── OpenAI ──
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── JWT ──
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OAuth SSO ──
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/sso/google/callback"

    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/auth/sso/microsoft/callback"

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/auth/sso/github/callback"

    # ── Cache ──
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default TTL

    # ── CORS ──
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for settings."""
    return Settings()


settings = get_settings()
