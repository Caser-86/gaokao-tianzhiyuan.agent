from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_review_queue_endpoint_requires_admin_header() -> None:
    response = client.get("/api/admin/review-queue")
    assert response.status_code == 401
    assert response.json() == {"detail": "admin authentication required"}


def test_review_queue_endpoint_returns_empty_items_for_valid_admin_token() -> None:
    response = client.get(
        "/api/admin/review-queue",
        headers={"x-admin-token": "dev-admin-token"},
    )
    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_review_queue_endpoint_uses_configured_admin_token() -> None:
    previous_token = getattr(settings, "admin_token", "dev-admin-token")
    settings.admin_token = "task4-custom-token"
    try:
        response = client.get(
            "/api/admin/review-queue",
            headers={"x-admin-token": "task4-custom-token"},
        )
        assert response.status_code == 200
        assert response.json() == {"items": []}
    finally:
        settings.admin_token = previous_token
