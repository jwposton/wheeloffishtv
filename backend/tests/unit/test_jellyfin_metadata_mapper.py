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


def test_map_series_maps_metadata_and_thumb() -> None:
    item = _jellyfin_item(
        Overview="A great show.",
        Genres=["Drama", "Sci-Fi"],
        OfficialRating="TV-14",
        Studios=[{"Name": "ACME Studios", "Id": "studio-1"}],
    )

    series = map_series("conn-1", "lib-1", item)

    assert series.provider_metadata is not None
    assert series.provider_metadata["Type"] == "Series"
    assert series.provider_metadata["summary"] == "A great show."
    assert series.provider_metadata["genres"] == ["Drama", "Sci-Fi"]
    assert series.provider_metadata["contentRating"] == "TV-14"
    assert series.provider_metadata["studio"] == "ACME Studios"
    assert series.thumb_url == "/Items/abc/Images/Primary?tag=tag1"


def test_map_series_genres_from_dict_list() -> None:
    item = _jellyfin_item(
        Genres=[{"Name": "Comedy"}, {"Name": "Action"}],
        ImageTags={},
    )
    series = map_series("conn-1", "lib-1", item)
    assert series.provider_metadata["genres"] == ["Comedy", "Action"]
    assert series.thumb_url is None


def test_map_series_stubs_when_fields_absent() -> None:
    item = _jellyfin_item(ImageTags={})

    series = map_series("conn-1", "lib-1", item)

    assert series.provider_metadata["summary"] is None
    assert series.provider_metadata["genres"] == []
    assert series.provider_metadata["contentRating"] is None
    assert series.provider_metadata["studio"] is None
    assert series.thumb_url is None
