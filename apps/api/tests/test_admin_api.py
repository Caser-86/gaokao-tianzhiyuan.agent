from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_review_queue_endpoint_requires_admin_header() -> None:
    response = client.get("/api/admin/review-queue")
    assert response.status_code == 401
    assert response.json() == {"detail": "admin authentication required"}
