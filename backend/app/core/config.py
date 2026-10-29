import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "DevAlert"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="devalert-insecure-secret-key-change-in-production-1234567890", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database: Supports SQLite (for easy zero-config local tests) or PostgreSQL
    DATABASE_URL: str = Field(
        default="sqlite:///./devalert.db",
        env="DATABASE_URL"
    )

    # Redis & Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CELERY_BROKER_URL: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    CELERY_ALWAYS_EAGER: bool = Field(default=False, env="CELERY_ALWAYS_EAGER")

    # Email settings
    EMAIL_MODE: str = Field(default="console", env="EMAIL_MODE")  # console, smtp, file, mock
    EMAIL_FILE_PATH: str = Field(default="./data/emails", env="EMAIL_FILE_PATH")
    SMTP_HOST: str = Field(default="localhost", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=1025, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(default="notifications@devalert.local", env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field(default="DevAlert Monitoring", env="SMTP_FROM_NAME")
    SMTP_USE_TLS: bool = Field(default=False, env="SMTP_USE_TLS")
    SMTP_USE_SSL: bool = Field(default=False, env="SMTP_USE_SSL")

    # Frontend URL for link generation in alerts
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # AI Error Analysis
    AI_ANALYSIS_ENABLED: bool = Field(default=False, env="AI_ANALYSIS_ENABLED")
    AI_API_KEY: Optional[str] = Field(default=None, env="AI_API_KEY")
    AI_PROVIDER: str = Field(default="gemini", env="AI_PROVIDER")  # gemini, openai, mock

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=120, env="RATE_LIMIT_PER_MINUTE")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()

if not settings.CELERY_BROKER_URL:
    settings.CELERY_BROKER_URL = settings.REDIS_URL
if not settings.CELERY_RESULT_BACKEND:
    settings.CELERY_RESULT_BACKEND = settings.REDIS_URL

