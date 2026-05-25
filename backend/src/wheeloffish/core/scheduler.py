"""APScheduler factory: nightly rebuild cron wired to install timezone (D-07, SCH-01)."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from wheeloffish.core.config import Settings
from wheeloffish.core.playlist.cadence import parse_cron_time

logger = structlog.get_logger("wheeloffish.scheduler")


def create_scheduler(settings: Settings, job_callable: Callable[..., Any]) -> AsyncIOScheduler:
    """Build and return a configured AsyncIOScheduler (not yet started).

    - Resolves install timezone from settings (falls back to UTC on bad zone, T-05-02-03)
    - Parses WOF_REBUILD_CRON HH:MM; raises ValueError on invalid format (T-05-02-02)
    - Adds job 'nightly_rebuilds' with max_instances=1 and coalesce=True (D-05/D-10)
    """
    tz = settings.install_tz()
    hour, minute = parse_cron_time(settings.WOF_REBUILD_CRON)

    scheduler = AsyncIOScheduler(timezone=tz)
    trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
    scheduler.add_job(
        job_callable,
        trigger=trigger,
        id="nightly_rebuilds",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=None,
    )
    logger.info(
        "scheduler_configured",
        cron=settings.WOF_REBUILD_CRON,
        timezone=str(tz),
    )
    return scheduler
