from functools import lru_cache
from typing import Literal

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
    WOF_PROVIDER: Literal["plex", "jellyfin"] = "plex"
    WOF_MEDIA_SERVER_URL: str = "http://localhost:32400"
    WOF_MEDIA_SERVER_DISPLAY_NAME: str = "Media Server"
    WOF_VERIFY_SSL: bool = True
    WOF_ADMIN_PROVIDER_USER_ID: str = ""
    WOF_ADMIN_USERNAME: str = ""
    WOF_SESSION_DAYS: int | None = None
    WOF_ENABLED_PROVIDERS: str = "plex,jellyfin"
    WOF_PLEX_PRODUCT_NAME: str = "Wheel of Fish TV"
    WOF_OAUTH_CALLBACK_BASE: str = "http://localhost:8000"
    WOF_CATALOG_SYNC_CHUNK_SIZE: int = 100
    WOF_CATALOG_PAGE_DEFAULT: int = 50
    WOF_SCOPED_LIBRARY_IDS: str = ""
    SPA_DIST_DIR: str = "/app/static/spa"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def enabled_providers_set(self) -> set[str]:
        legacy = {p.strip() for p in self.WOF_ENABLED_PROVIDERS.split(",") if p.strip()}
        if len(legacy) > 1:
            return legacy
        return {self.WOF_PROVIDER}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def session_max_age_seconds(self) -> int | None:
        if self.WOF_SESSION_DAYS is None:
            return None
        return self.WOF_SESSION_DAYS * 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()
