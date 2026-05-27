from wheeloffish.core.media_artwork import (
    artwork_cache_path,
    normalize_jellyfin_artwork_path,
    normalize_plex_artwork_path,
    resolve_series_artwork_fetch_path,
    series_artwork_url,
    write_cached_artwork,
)


def test_series_artwork_url() -> None:
    series_id = "conn-1:plex:guid-abc"
    url = series_artwork_url("conn-1", series_id)
    assert url == "/api/v1/connections/conn-1/series/conn-1%3Aplex%3Aguid-abc/artwork"


def test_normalize_plex_artwork_path_relative() -> None:
    path = normalize_plex_artwork_path("/library/metadata/1001/thumb/abc")
    assert path == "/library/metadata/1001/thumb/abc"


def test_normalize_plex_artwork_path_absolute() -> None:
    absolute = "https://plex.example.com/library/metadata/1/thumb/2"
    assert normalize_plex_artwork_path(absolute) == "/library/metadata/1/thumb/2"


def test_normalize_plex_artwork_path_rejects_traversal() -> None:
    assert normalize_plex_artwork_path("/library/metadata/../identity") is None


def test_normalize_plex_artwork_path_none_for_missing() -> None:
    assert normalize_plex_artwork_path(None) is None


def test_normalize_jellyfin_artwork_path_full() -> None:
    path = normalize_jellyfin_artwork_path(
        "/Items/11111111-2222-4333-8444-555555555555/Images/Primary?tag=abc",
        "11111111-2222-4333-8444-555555555555",
    )
    assert path == "/Items/11111111-2222-4333-8444-555555555555/Images/Primary?tag=abc"


def test_normalize_jellyfin_artwork_path_legacy_tag_only() -> None:
    path = normalize_jellyfin_artwork_path("legacytag", "11111111-2222-4333-8444-555555555555")
    assert path == "/Items/11111111-2222-4333-8444-555555555555/Images/Primary?tag=legacytag"


def test_normalize_jellyfin_artwork_path_rejects_traversal() -> None:
    assert normalize_jellyfin_artwork_path("/Items/../x/Images/Primary", "nid") is None


def test_resolve_series_artwork_fetch_path_jellyfin() -> None:
    p = resolve_series_artwork_fetch_path(
        provider_type="jellyfin",
        thumb_url="/Items/nid/Images/Primary",
        native_id="nid",
    )
    assert p == "/Items/nid/Images/Primary"


def test_artwork_cache_path_is_per_user(tmp_path) -> None:
    cache_dir = str(tmp_path)
    series_id = "conn-1:plex:guid-abc"
    first = artwork_cache_path(cache_dir, "user-a", "conn-1", series_id)
    second = artwork_cache_path(cache_dir, "user-b", "conn-1", series_id)
    assert first != second
    assert first.parent.parent.name == "user-a"
    assert first.parent.name == "conn-1"


def test_write_and_read_cached_artwork_roundtrip(tmp_path) -> None:
    from wheeloffish.core.media_artwork import read_cached_artwork

    cache_path = artwork_cache_path(str(tmp_path), "user-1", "conn-1", "series-1")
    write_cached_artwork(cache_path, b"jpeg-bytes")
    cached = read_cached_artwork(cache_path)
    assert cached is not None
    assert cached[0] == b"jpeg-bytes"
