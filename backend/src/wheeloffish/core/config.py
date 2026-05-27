import zoneinfo
from functools import lru_cache
from typing import Literal

import structlog
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
    WOF_SESSION_DAYS: int | None = None
    WOF_ENABLED_PROVIDERS: str = "plex,jellyfin"
    WOF_PLEX_PRODUCT_NAME: str = "Wheel of Fish TV"
    WOF_OAUTH_CALLBACK_BASE: str = "http://localhost:8000"
    WOF_CATALOG_SYNC_CHUNK_SIZE: int = 500
    WOF_CATALOG_PAGE_DEFAULT: int = 50
    WOF_SCOPED_LIBRARY_IDS: str = ""
    WOF_ARTWORK_CACHE_DIR: str = "/data/artwork"
    WOF_ARTWORK_CACHE_TTL_DAYS: int = 30
    SPA_DIST_DIR: str = "/app/static/spa"
    WOF_INSTALL_TIMEZONE: str = "UTC"
    WOF_REBUILD_CRON: str = "04:00"

    def install_tz(self) -> zoneinfo.ZoneInfo:
        """Return ZoneInfo for WOF_INSTALL_TIMEZONE; falls back to UTC on unknown IANA name."""
        try:
            return zoneinfo.ZoneInfo(self.WOF_INSTALL_TIMEZONE)
        except zoneinfo.ZoneInfoNotFoundError:
            structlog.get_logger("wheeloffish.config").warning(
                "unknown_install_timezone",
                configured=self.WOF_INSTALL_TIMEZONE,
                fallback="UTC",
            )
            return zoneinfo.ZoneInfo("UTC")

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
