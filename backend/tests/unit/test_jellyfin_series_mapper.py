from wheeloffish.integrations.jellyfin.mappers import map_series


def test_map_series_library_added_at_from_date_created() -> None:
    item = {
        "Id": "11111111-2222-4333-8444-555555555555",
        "Name": "Show",
        "DateCreated": "2024-06-01T12:00:00.000Z",
    }
    series = map_series("conn-1", "lib-1", item)
    assert series.library_added_at == 1_717_243_200


def test_map_series_library_added_at_none_without_date() -> None:
    item = {"Id": "11111111-2222-4333-8444-555555555555", "Name": "Show"}
    series = map_series("conn-1", "lib-1", item)
    assert series.library_added_at is None
