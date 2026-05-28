import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from wheeloffish.core.config import get_settings
from wheeloffish.core.version_check import reset_release_cache
from wheeloffish.main import app


@pytest.fixture(autouse=True)
def clear_release_cache() -> None:
    reset_release_cache()
    yield
    reset_release_cache()


@pytest.fixture
async def meta_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_PROVIDER", "plex")
    monkeypatch.setenv("WOF_OAUTH_CALLBACK_BASE", "http://localhost:8000")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_providers_returns_single_provider(meta_client: AsyncClient) -> None:
    response = await meta_client.get("/api/v1/meta/providers")
    assert response.status_code == 200
    assert response.json() == {
        "provider": "plex",
        "oauth_callback_base": "http://localhost:8000",
    }


@pytest.mark.asyncio
@respx.mock
async def test_version_reports_update_when_github_is_newer(meta_client: AsyncClient) -> None:
    respx.get("https://api.github.com/repos/jwposton/wheeloffishtv/releases/latest").mock(
        return_value=Response(
            200,
            json={
                "tag_name": "v9.9.9",
                "html_url": "https://github.com/jwposton/wheeloffishtv/releases/tag/v9.9.9",
            },
        ),
    )

    response = await meta_client.get("/api/v1/meta/version")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.0.0"
    assert body["latest_version"] == "9.9.9"
    assert body["update_available"] is True
    assert body["release_url"] == "https://github.com/jwposton/wheeloffishtv/releases/tag/v9.9.9"


@pytest.mark.asyncio
@respx.mock
async def test_version_hides_release_url_when_current(meta_client: AsyncClient) -> None:
    respx.get("https://api.github.com/repos/jwposton/wheeloffishtv/releases/latest").mock(
        return_value=Response(
            200,
            json={
                "tag_name": "v0.1.8",
                "html_url": "https://github.com/jwposton/wheeloffishtv/releases/tag/v0.1.8",
            },
        ),
    )

    response = await meta_client.get("/api/v1/meta/version")
    assert response.status_code == 200
    body = response.json()
    assert body["update_available"] is False
    assert body["release_url"] is None
