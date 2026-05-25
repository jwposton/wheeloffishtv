from wheeloffish.core.media_artwork import public_artwork_url


def test_public_artwork_url_rewrites_plex_relative_path() -> None:
    url = public_artwork_url("conn-1", "/library/metadata/1001/thumb/abc")
    assert url == "/api/v1/connections/conn-1/artwork?path=/library/metadata/1001/thumb/abc"


def test_public_artwork_url_passes_through_absolute_url() -> None:
    absolute = "https://plex.example.com/library/metadata/1/thumb/2"
    assert public_artwork_url("conn-1", absolute) == absolute


def test_public_artwork_url_none_for_missing() -> None:
    assert public_artwork_url("conn-1", None) is None
