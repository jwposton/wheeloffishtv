"""Tests for scheduler factory and related utilities (D-07, D-05, D-10)."""
from __future__ import annotations

import zoneinfo
from unittest.mock import MagicMock

import pytest

from wheeloffish.core.scheduler import create_scheduler


def _settings(tz: str = "America/New_York", cron: str = "04:00") -> MagicMock:
    s = MagicMock()
    s.WOF_INSTALL_TIMEZONE = tz
    s.WOF_REBUILD_CRON = cron
    s.install_tz.return_value = zoneinfo.ZoneInfo(tz)
    return s


class TestCreateScheduler:
    def test_registers_nightly_rebuilds_job(self):
        """Scheduler must have a job with id 'nightly_rebuilds'."""
        settings = _settings()
        scheduler = create_scheduler(settings, job_callable=lambda: None)
        job = scheduler.get_job("nightly_rebuilds")
        assert job is not None

    def test_job_uses_install_timezone(self):
        """CronTrigger must use the install timezone, not hardcoded UTC."""
        settings = _settings(tz="America/New_York")
        scheduler = create_scheduler(settings, job_callable=lambda: None)
        job = scheduler.get_job("nightly_rebuilds")
        assert job is not None
        trigger_tz = str(job.trigger.timezone)
        assert trigger_tz == "America/New_York"

    def test_job_max_instances_one(self):
        """Job must have max_instances=1 to prevent pile-up (D-05)."""
        settings = _settings()
        scheduler = create_scheduler(settings, job_callable=lambda: None)
        job = scheduler.get_job("nightly_rebuilds")
        assert job.max_instances == 1

    def test_job_coalesce_true(self):
        """Job must coalesce missed fires (D-10)."""
        settings = _settings()
        scheduler = create_scheduler(settings, job_callable=lambda: None)
        job = scheduler.get_job("nightly_rebuilds")
        assert job.coalesce is True

    def test_scheduler_default_timezone_matches_install(self):
        """AsyncIOScheduler default timezone must match install timezone."""
        settings = _settings(tz="America/Chicago")
        settings.install_tz.return_value = zoneinfo.ZoneInfo("America/Chicago")
        scheduler = create_scheduler(settings, job_callable=lambda: None)
        assert str(scheduler.timezone) == "America/Chicago"


class TestParseCronTimeInvalidViaScheduler:
    def test_invalid_cron_raises_value_error(self):
        settings = _settings(cron="not-a-time")
        with pytest.raises(ValueError):
            create_scheduler(settings, job_callable=lambda: None)


class TestInvalidTimezoneConfig:
    def test_unknown_timezone_falls_back_to_utc(self):
        """install_tz() on bad zone falls back to UTC (T-05-02-03)."""
        from wheeloffish.core.config import Settings

        # Construct Settings directly with an invalid timezone
        s = Settings(
            WOF_SECRET_KEY="a" * 64,
            WOF_INSTALL_TIMEZONE="Not/A/Zone",
        )
        tz = s.install_tz()
        assert str(tz) == "UTC"
