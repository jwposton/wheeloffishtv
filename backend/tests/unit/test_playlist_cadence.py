"""Tests for cadence evaluation in install timezone (D-02/D-03/D-04)."""
from __future__ import annotations

import zoneinfo
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from wheeloffish.core.playlist.cadence import is_due, now_in_tz, parse_cron_time


def _playlist(cadence: str, day_of_week: int | None = None) -> MagicMock:
    p = MagicMock()
    p.refresh_cadence = cadence
    p.refresh_day_of_week = day_of_week
    return p


NY_TZ = zoneinfo.ZoneInfo("America/New_York")
UTC_TZ = zoneinfo.ZoneInfo("UTC")


class TestIsDueDaily:
    def test_daily_is_always_due(self):
        playlist = _playlist("daily")
        now = datetime(2026, 5, 25, 4, 0, tzinfo=NY_TZ)
        assert is_due(playlist, now) is True

    def test_daily_any_time_is_due(self):
        playlist = _playlist("daily")
        now = datetime(2026, 5, 25, 23, 59, tzinfo=NY_TZ)
        assert is_due(playlist, now) is True


class TestIsDueWeekly:
    def test_weekly_due_on_matching_weekday(self):
        # Monday = 0; 2026-05-25 is a Monday
        playlist = _playlist("weekly", day_of_week=0)
        now = datetime(2026, 5, 25, 4, 0, tzinfo=NY_TZ)
        assert is_due(playlist, now) is True

    def test_weekly_not_due_on_non_matching_weekday(self):
        # Monday = 0; 2026-05-26 is a Tuesday (weekday=1)
        playlist = _playlist("weekly", day_of_week=0)
        now = datetime(2026, 5, 26, 4, 0, tzinfo=NY_TZ)
        assert is_due(playlist, now) is False

    def test_weekly_null_dow_not_due(self):
        playlist = _playlist("weekly", day_of_week=None)
        now = datetime(2026, 5, 25, 4, 0, tzinfo=NY_TZ)
        assert is_due(playlist, now) is False

    def test_weekly_dow_uses_local_weekday(self):
        """America/New_York Saturday 1am local (= Friday UTC) must use local Saturday (weekday=5)."""
        # 2026-05-23 is a Saturday; at 01:00 NY time that is 06:00 UTC (still Sat local)
        saturday_ny = datetime(2026, 5, 23, 1, 0, tzinfo=NY_TZ)
        # Confirm this is indeed Saturday (weekday 5) locally
        assert saturday_ny.weekday() == 5

        # Playlist due on Saturday (5)
        playlist_sat = _playlist("weekly", day_of_week=5)
        assert is_due(playlist_sat, saturday_ny) is True

        # Playlist due on Friday (4) must NOT fire
        playlist_fri = _playlist("weekly", day_of_week=4)
        assert is_due(playlist_fri, saturday_ny) is False


class TestParseCronTime:
    def test_parse_valid_cron(self):
        assert parse_cron_time("04:00") == (4, 0)

    def test_parse_midnight(self):
        assert parse_cron_time("00:00") == (0, 0)

    def test_parse_arbitrary_time(self):
        assert parse_cron_time("23:59") == (23, 59)

    def test_parse_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_cron_time("invalid")

    def test_parse_missing_colon_raises(self):
        with pytest.raises(ValueError):
            parse_cron_time("0400")

    def test_parse_non_numeric_raises(self):
        with pytest.raises(ValueError):
            parse_cron_time("ab:cd")


class TestNowInTz:
    def test_now_in_tz_returns_aware_datetime(self):
        result = now_in_tz(UTC_TZ)
        assert result.tzinfo is not None

    def test_now_in_tz_uses_provided_zone(self):
        result = now_in_tz(NY_TZ)
        assert result.utcoffset() == datetime.now(NY_TZ).utcoffset()
