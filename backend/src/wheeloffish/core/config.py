from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    WOF_SECRET_KEY: str = Field(..., min_length=64, max_length=64)
    DATABASE_URL: str = "sqlite:////data/wheeloffish.db"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENVIRONMENT: str = "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
