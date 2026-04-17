from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DSGVO Copilot API"
    env: str = "development"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "dsgvo_docs"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+asyncpg://dsgvo:dsgvo@localhost:5432/dsgvo"
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
