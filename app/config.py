"""
app/config.py
─────────────
Centralized configuration using pydantic-settings.
All values loaded from .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache
import json


class Settings(BaseSettings):
    # ── Anthropic ──────────────────────────────────────
    # ANTHROPIC_API_KEY: str = Field(..., env="ANTHROPIC_API_KEY")
    # CLAUDE_MODEL: str = "claude-sonnet-4-6"
    # CLAUDE_MAX_TOKENS: int = 1500


    # ── Gemini ─────────────────────────────────────────
    GEMINI_API_KEY: str = Field("", env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field("gemini-1.5-flash", env="GEMINI_MODEL")
    CLAUDE_MAX_TOKENS: int = 1500  # keep this, unused but referenced

    # ── GitHub ─────────────────────────────────────────
    GITHUB_TOKEN: str = Field("", env="GITHUB_TOKEN")
    GITHUB_USERNAME: str = Field("", env="GITHUB_USERNAME")

    # ── Redis ──────────────────────────────────────────
    REDIS_URL: str = Field("redis://localhost:6379", env="REDIS_URL")

    # ── Security ───────────────────────────────────────
    SECRET_KEY: str = Field("dev-secret-key-change-in-prod", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── AWS ────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = Field("", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field("", env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "venkatgpt-data"

    # ── CORS ───────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── App ────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    # ── File Paths ─────────────────────────────────────
    PORTFOLIO_JSON_PATH: str = "data/portfolio.json"
    RESUME_PDF_PATH: str = "data/resume.pdf"
    INDEXES_DIR: str = "indexes"
    PROMPTS_DIR: str = "prompts"

    # ── Resume URLs ────────────────────────────────────
    RESUME_DOWNLOAD_URL: str = Field("", env="RESUME_DOWNLOAD_URL")
    RESUME_VIEW_URL: str = Field("", env="RESUME_VIEW_URL")

    # ── RAG Settings ───────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # fast, good quality
    EMBEDDING_DIMENSION: int = 384
    TOP_K_RETRIEVAL: int = 8
    SIMILARITY_THRESHOLD: float = 0.1
    MAX_CONTEXT_TOKENS: int = 3000

    # ── Rate Limiting ──────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 20
    RATE_LIMIT_WINDOW: int = 60  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
