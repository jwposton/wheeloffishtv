from wheeloffish.core.provider_playlist_urls import (
    PLEX_WEB_APP_BASE,
    _plex_machine_identifier,
    provider_playlist_open_url,
)


def test_plex_open_url_uses_app_plex_tv_with_machine_id():
    url = provider_playlist_open_url(
        base_url="https://plex.example.com",
        provider_kind="plex",
        provider_playlist_id="27220",
        plex_machine_identifier="machine-abc",
    )
    assert (
        url
        == f"{PLEX_WEB_APP_BASE}#!/server/machine-abc/playlist?key=%2Fplaylists%2F27220"
    )


def test_plex_open_url_returns_none_without_machine_id(monkeypatch):
    monkeypatch.setattr(
        "wheeloffish.core.provider_playlist_urls._plex_machine_identifier",
        lambda *_args, **_kwargs: None,
    )
    url = provider_playlist_open_url(
        base_url="https://plex.example.com",
        provider_kind="plex",
        provider_playlist_id="27220",
    )
    assert url is None


def test_jellyfin_open_url_uses_server_web_app():
    url = provider_playlist_open_url(
        base_url="https://jellyfin.example.com",
        provider_kind="jellyfin",
        provider_playlist_id="playlist-guid",
    )
    assert url == "https://jellyfin.example.com/web/index.html#!/details?id=playlist-guid"


def test_open_url_returns_none_when_unlinked():
    assert (
        provider_playlist_open_url(
            base_url="https://plex.example.com",
            provider_kind="plex",
            provider_playlist_id="",
        )
        is None
    )


def test_plex_machine_identifier_cache(monkeypatch):
    _plex_machine_identifier.cache_clear()
    calls = {"count": 0}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"MediaContainer": {"machineIdentifier": "cached-machine"}}

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def get(self, url, headers):
            calls["count"] += 1
            assert url == "https://plex.example.com/identity"
            return FakeResponse()

    monkeypatch.setattr("wheeloffish.core.provider_playlist_urls.httpx.Client", FakeClient)

    assert _plex_machine_identifier("https://plex.example.com", True) == "cached-machine"
    assert _plex_machine_identifier("https://plex.example.com", True) == "cached-machine"
    assert calls["count"] == 1
