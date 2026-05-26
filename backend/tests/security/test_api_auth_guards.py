"""Regression: non-public API routes reject unauthenticated requests."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable

import pytest
from fastapi.routing import APIRoute
from starlette.testclient import TestClient

from wheeloffish.core.config import Settings
from wheeloffish.main import create_app

TEST_SECRET_KEY = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)

os.environ.setdefault("WOF_SECRET_KEY", TEST_SECRET_KEY)


def _guard_app():
    """Route enumeration only — no DB access required."""
    return create_app(
        Settings(WOF_SECRET_KEY=TEST_SECRET_KEY, DATABASE_URL="sqlite:///:memory:")
    )

# Intentionally reachable without a session cookie (method, regex on FastAPI route.path).
PUBLIC_ROUTES: list[tuple[str, str]] = [
    ("GET", r"^/health$"),
    ("GET", r"^/api/v1/meta/providers$"),
    ("GET", r"^/api/v1/meta/version$"),
    ("POST", r"^/api/v1/auth/bootstrap-session$"),
    ("POST", r"^/api/v1/auth/logout$"),
    ("GET", r"^/api/v1/connections$"),
    ("POST", r"^/api/v1/connections$"),
    ("GET", r"^/api/v1/connections/plex/oauth/status/\{pin_id\}$"),
    ("GET", r"^/api/v1/connections/plex/oauth/callback$"),
]

PATH_PARAM_SAMPLES = {
    "connection_id": "00000000-0000-4000-8000-000000000001",
    "playlist_id": "00000000-0000-4000-8000-000000000002",
    "series_id": "00000000-0000-4000-8000-000000000001:plex:lib1:12345",
    "pin_id": "999001",
}


def _sample_path(route_path: str) -> str:
    path = route_path
    for key, value in PATH_PARAM_SAMPLES.items():
        path = path.replace(f"{{{key}}}", value)
    return path


def _is_public(method: str, path: str) -> bool:
    return any(method == pub_method and re.match(pattern, path) for pub_method, pattern in PUBLIC_ROUTES)


def _protected_routes(app) -> list[tuple[str, str]]:
    routes: list[tuple[str, str]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or []):
            if method in {"HEAD", "OPTIONS"}:
                continue
            if _is_public(method, route.path):
                continue
            routes.append((method, route.path))
    return routes


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "method" in metafunc.fixturenames and "route_path" in metafunc.fixturenames:
        cases = _protected_routes(_guard_app())
        metafunc.parametrize("method,route_path", cases, ids=[f"{m} {p}" for m, p in cases])


def test_unauthenticated_api_route_returns_401(
    guard_client: TestClient,
    method: str,
    route_path: str,
) -> None:
    url = _sample_path(route_path)
    if route_path.endswith("/callback"):
        response = guard_client.request(method, url, params={"pin_id": PATH_PARAM_SAMPLES["pin_id"]})
    else:
        response = guard_client.request(method, url)

    assert response.status_code == 401, (
        f"Expected 401 for unauthenticated {method} {url}, got {response.status_code}: {response.text[:200]}"
    )
    assert response.json()["detail"]["code"] == "unauthenticated"


def test_public_routes_do_not_require_session(guard_client: TestClient) -> None:
    assert guard_client.get("/api/v1/meta/providers").status_code == 200
    assert guard_client.get("/api/v1/meta/version").status_code == 200
    assert guard_client.post("/api/v1/auth/bootstrap-session").status_code == 200
    assert guard_client.post("/api/v1/connections").status_code == 403
