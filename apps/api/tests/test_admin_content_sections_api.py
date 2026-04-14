from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    return {"x-admin-token": settings.admin_token}


def test_content_sections_endpoint_returns_school_and_major_entries() -> None:
    response = client.get("/api/admin/content-sections", headers=auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert any(item["slug"] == "southeast-university" for item in payload["schools"])
    assert any(item["slug"] == "clinical-medicine" for item in payload["majors"])


def test_update_school_sections() -> None:
    response = client.post(
        "/api/admin/content-sections/schools/southeast-university",
        headers=auth_headers(),
        json={
            "sections": [
                {
                    "type": "highlights",
                    "title": "学校亮点",
                    "items": ["资源密集", "适合自驱型学生"],
                },
                {
                    "type": "pitfalls",
                    "title": "坑点提醒",
                    "items": ["课程强度高"],
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "southeast-university"
    assert len(payload["sections"]) == 2
    assert payload["sections"][1]["title"] == "坑点提醒"


def test_update_major_sections_rejects_partially_filled_section() -> None:
    response = client.post(
        "/api/admin/content-sections/majors/clinical-medicine",
        headers=auth_headers(),
        json={
            "sections": [
                {
                    "type": "fit_for",
                    "title": "",
                    "items": ["培养周期长"],
                }
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "content section row is invalid"
