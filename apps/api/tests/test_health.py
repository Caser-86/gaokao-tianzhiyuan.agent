from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app

client = TestClient(app)


def test_healthcheck_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_probe_returns_configured_release_version() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "dev"}


def test_version_probe_surfaces_runtime_release_value(monkeypatch) -> None:
    monkeypatch.setattr(main_module.settings, "release_version", "release-test-2026-08-25")

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "release-test-2026-08-25"}
