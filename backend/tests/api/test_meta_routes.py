import pytest
from httpx import ASGITransport, AsyncClient

from wheeloffish.core.config import get_settings
from wheeloffish.main import app


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
