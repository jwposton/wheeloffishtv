from functools import lru_cache

from pydantic import Field, computed_field
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
    WOF_ENABLED_PROVIDERS: str = "plex,jellyfin"
    WOF_PLEX_PRODUCT_NAME: str = "Wheel of Fish TV"
    WOF_OAUTH_CALLBACK_BASE: str = "http://localhost:8000"
    WOF_CATALOG_SYNC_CHUNK_SIZE: int = 100
    WOF_CATALOG_PAGE_DEFAULT: int = 50

    @computed_field  # type: ignore[prop-decorator]
    @property
    def enabled_providers_set(self) -> set[str]:
        return {p.strip() for p in self.WOF_ENABLED_PROVIDERS.split(",") if p.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
