import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Coding Assistant Agent"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/coding_assistant"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    REDIS_URL: str = "redis://:redis123@localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_CALLBACK_URL: str = "http://localhost:8000/api/v1/auth/callback"
    GITHUB_APP_ID: str = ""
    GITHUB_PRIVATE_KEY_PATH: str = "./secrets/github_private_key.pem"
    GITHUB_SCOPES: str = "repo,read:org,user:email"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    WS_URL: str = "ws://localhost:8000"

    MAX_ITERATIONS: int = 5
    TEST_TIMEOUT: int = 600
    SANDBOX_TIMEOUT: int = 900

    REPO_CACHE_DIR: str = "./repo_cache"
    LOGS_DIR: str = "./logs"

    ENABLE_AUTO_APPROVAL: bool = False
    ENABLE_RAG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
