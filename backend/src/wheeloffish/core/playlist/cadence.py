"""Cadence evaluation: determines whether a playlist is due for rebuild in install timezone."""
from __future__ import annotations

import zoneinfo
from datetime import datetime

import structlog

logger = structlog.get_logger("wheeloffish.cadence")


def is_due(playlist_orm, now_local: datetime) -> bool:
    """Return True if playlist_orm is due for rebuild at now_local (timezone-aware, install TZ).

    Rules (D-02/D-03):
    - daily: always due when the nightly job fires
    - weekly: due only when now_local.weekday() matches refresh_day_of_week (Mon=0)
    - weekly with null refresh_day_of_week: not due (logs warning)
    """
    cadence = playlist_orm.refresh_cadence
    if cadence == "daily":
        return True
    if cadence == "weekly":
        dow = playlist_orm.refresh_day_of_week
        if dow is None:
            logger.warning(
                "weekly_playlist_missing_dow",
                playlist_id=getattr(playlist_orm, "id", None),
            )
            return False
        return now_local.weekday() == dow
    return False


def parse_cron_time(cron_str: str) -> tuple[int, int]:
    """Parse "HH:MM" string and return (hour, minute) ints. Raises ValueError on bad format."""
    try:
        parts = cron_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Expected HH:MM format, got: {cron_str!r}")
        hour = int(parts[0])
        minute = int(parts[1])
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Invalid cron time {cron_str!r}: {exc}") from exc
    return (hour, minute)


def now_in_tz(tz: zoneinfo.ZoneInfo) -> datetime:
    """Return current datetime localised to tz (timezone-aware)."""
    return datetime.now(tz)
