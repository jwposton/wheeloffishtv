from wheeloffish.integrations.jellyfin.mappers import map_series


def _jellyfin_item(**overrides: object) -> dict:
    base = {
        "Id": "abc",
        "Name": "Test Show",
        "ProductionYear": 2021,
        "ImageTags": {"Primary": "tag1"},
        "Type": "Series",
    }
    base.update(overrides)
    return base


def test_map_series_stubs_metadata_keys() -> None:
    item = _jellyfin_item()

    series = map_series("conn-1", "lib-1", item)

    assert series.provider_metadata is not None
    assert series.provider_metadata["Type"] == "Series"
    assert series.provider_metadata["summary"] is None
    assert series.provider_metadata["genres"] == []
    assert series.provider_metadata["contentRating"] is None
    assert series.provider_metadata["studio"] is None
