from fastapi.testclient import TestClient

from wheeloffish.main import app


def test_health_returns_ok(db_engine) -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "wheeloffish"
    assert body["checks"]["api"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert "schema_version" in body
