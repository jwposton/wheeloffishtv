"""Unit tests for Episode.last_viewed_at DTO field and provider mappers (D-06)."""

from datetime import UTC, datetime

from wheeloffish.domain.dto import Episode
from wheeloffish.integrations.jellyfin.mappers import map_episode as jellyfin_map_episode
from wheeloffish.integrations.plex.mappers import map_episode as plex_map_episode

CONNECTION_ID = "conn-1"


def _plex_metadata(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "guid": "com.plexapp.agents.thetvdb://1/1/1",
        "title": "S1E1",
        "parentIndex": 1,
        "index": 1,
        "duration": 3_600_000,
        "viewCount": 0,
        "viewOffset": 0,
    }
    base.update(overrides)
    return base


def _jellyfin_item(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "Id": "ep-1",
        "Name": "S1E1",
        "ParentIndexNumber": 1,
        "IndexNumber": 1,
        "RunTimeTicks": 36_000_000_000,
        "UserData": {"Played": False, "PlaybackPositionTicks": 0},
    }
    base.update(overrides)
    return base


def test_episode_dto_last_viewed_at_defaults_to_none() -> None:
    ep = Episode(
        id="x",
        title="t",
        season_index=1,
        episode_index=1,
        duration_ms=1000,
        percent_watched=0.0,
    )
    assert ep.last_viewed_at is None
    assert Episode.model_fields["last_viewed_at"].default is None


def test_episode_dto_round_trips_last_viewed_at() -> None:
    viewed_at = datetime(2026, 1, 1, tzinfo=UTC)
    ep = Episode(
        id="x",
        title="t",
        season_index=1,
        episode_index=1,
        duration_ms=1000,
        percent_watched=0.0,
        last_viewed_at=viewed_at,
    )
    assert ep.last_viewed_at == viewed_at
    assert ep.last_viewed_at is not None
    assert ep.last_viewed_at.tzinfo is not None


def test_episode_dto_locked_contract_unchanged() -> None:
    ep = Episode(
        id="ep-1",
        title="Pilot",
        season_index=1,
        episode_index=1,
        duration_ms=3_600_000,
        percent_watched=42.0,
        provider_marked_played=True,
        part_index=1,
        multipart_group_id="grp-1",
        is_special=False,
        special_for_season=None,
    )
    assert ep.id == "ep-1"
    assert ep.title == "Pilot"
    assert ep.season_index == 1
    assert ep.episode_index == 1
    assert ep.duration_ms == 3_600_000
    assert ep.percent_watched == 42.0
    assert ep.provider_marked_played is True
    assert ep.part_index == 1
    assert ep.multipart_group_id == "grp-1"


def test_plex_map_episode_includes_last_viewed_at() -> None:
    metadata = _plex_metadata(lastViewedAt=1_700_000_000)
    ep = plex_map_episode(CONNECTION_ID, metadata)
    expected = datetime.fromtimestamp(1_700_000_000, tz=UTC)
    assert ep.last_viewed_at == expected


def test_plex_map_episode_returns_none_when_lastViewedAt_missing() -> None:
    ep = plex_map_episode(CONNECTION_ID, _plex_metadata())
    assert ep.last_viewed_at is None


def test_plex_map_episode_returns_none_when_lastViewedAt_zero_d06() -> None:
    ep = plex_map_episode(CONNECTION_ID, _plex_metadata(lastViewedAt=0))
    assert ep.last_viewed_at is None


def test_plex_map_episode_returns_none_when_lastViewedAt_malformed() -> None:
    ep = plex_map_episode(CONNECTION_ID, _plex_metadata(lastViewedAt="not-a-timestamp"))
    assert ep.last_viewed_at is None


def test_jellyfin_map_episode_includes_last_viewed_at() -> None:
    item = _jellyfin_item(
        UserData={
            "Played": False,
            "PlaybackPositionTicks": 0,
            "LastPlayedDate": "2026-01-01T12:00:00.000Z",
        }
    )
    ep = jellyfin_map_episode(CONNECTION_ID, item)
    expected = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert ep.last_viewed_at == expected


def test_jellyfin_map_episode_returns_none_when_LastPlayedDate_missing() -> None:
    ep = jellyfin_map_episode(CONNECTION_ID, _jellyfin_item())
    assert ep.last_viewed_at is None


def test_jellyfin_map_episode_returns_none_when_LastPlayedDate_malformed() -> None:
    item = _jellyfin_item(
        UserData={
            "Played": False,
            "PlaybackPositionTicks": 0,
            "LastPlayedDate": "not-a-date",
        }
    )
    ep = jellyfin_map_episode(CONNECTION_ID, item)
    assert ep.last_viewed_at is None
