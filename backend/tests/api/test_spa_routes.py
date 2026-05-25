from importlib import reload

import pytest
from httpx import ASGITransport, AsyncClient

from wheeloffish.core.config import get_settings


@pytest.fixture
async def spa_client(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """App client with SPA mounted from a temporary dist directory."""
    spa_dir = tmp_path / "spa"
    spa_dir.mkdir()
    (spa_dir / "index.html").write_text(
        "<!doctype html><html><head><title>Wheel of Fish TV</title></head>"
        "<body><div id='root'>Wheel of Fish TV</div></body></html>",
        encoding="utf-8",
    )

    monkeypatch.setenv("SPA_DIST_DIR", str(spa_dir))
    get_settings.cache_clear()

    import wheeloffish.main as main_module

    reload(main_module)

    async with AsyncClient(
        transport=ASGITransport(app=main_module.app),
        base_url="http://test",
    ) as client:
        yield client

    get_settings.cache_clear()
    reload(main_module)


@pytest.mark.asyncio
async def test_index_serves_spa_html(spa_client: AsyncClient) -> None:
    response = await spa_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Wheel of Fish TV" in response.text


@pytest.mark.asyncio
async def test_browse_fallback_serves_index_html(spa_client: AsyncClient) -> None:
    response = await spa_client.get("/browse")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Wheel of Fish TV" in response.text
