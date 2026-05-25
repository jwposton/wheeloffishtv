from wheeloffish.integrations.plex.mappers import map_series


def _plex_metadata(**overrides: object) -> dict:
    base = {
        "guid": "plex://show/abc123",
        "title": "Test Show",
        "year": 2021,
        "thumb": "/library/metadata/12/thumb",
        "ratingKey": "12",
    }
    base.update(overrides)
    return base


def test_map_series_with_metadata() -> None:
    metadata = _plex_metadata(
        summary="A spy show",
        Genre=[{"tag": "Action"}, {"tag": "Drama"}],
        contentRating="TV-MA",
        studio="HBO",
    )

    series = map_series("conn-1", "5", metadata)

    assert series.provider_metadata == {
        "ratingKey": "12",
        "summary": "A spy show",
        "genres": ["Action", "Drama"],
        "contentRating": "TV-MA",
        "studio": "HBO",
    }


def test_map_series_omits_missing_metadata_gracefully() -> None:
    metadata = _plex_metadata()

    series = map_series("conn-1", "5", metadata)

    assert series.provider_metadata is not None
    assert series.provider_metadata["ratingKey"] == "12"
    assert series.provider_metadata["summary"] is None
    assert series.provider_metadata["genres"] == []
    assert series.provider_metadata["contentRating"] is None
    assert series.provider_metadata["studio"] is None


def test_map_series_handles_malformed_genre_array() -> None:
    metadata = _plex_metadata(Genre=[{"foo": "bar"}, {}])

    series = map_series("conn-1", "5", metadata)

    assert series.provider_metadata is not None
    assert series.provider_metadata["genres"] == []


def test_map_series_preserves_existing_rating_key() -> None:
    metadata = _plex_metadata(
        summary="A spy show",
        Genre=[{"tag": "Action"}],
        contentRating="TV-MA",
        studio="HBO",
    )

    series = map_series("conn-1", "5", metadata)

    assert series.provider_metadata is not None
    assert series.provider_metadata["ratingKey"] == "12"
