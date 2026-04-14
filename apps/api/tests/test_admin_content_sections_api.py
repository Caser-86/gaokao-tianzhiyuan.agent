import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import catalog as catalog_service

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    return {"x-admin-token": settings.admin_token}


@pytest.fixture
def sections_catalog_file(tmp_path, monkeypatch):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            {
                "search_entry": {
                    "title": "高考志愿助手",
                    "description": "测试入口",
                    "quick_prompts": ["查学校"],
                },
                "schools": [
                    {
                        "slug": "southeast-university",
                        "name": "东南大学",
                        "region": "江苏",
                        "city": "南京",
                        "tags": ["985"],
                        "summary": "测试学校摘要",
                        "sections": [
                            {
                                "type": "highlights",
                                "title": "学校亮点",
                                "items": ["原始学校亮点"],
                            }
                        ],
                        "related_majors": [],
                    }
                ],
                "majors": [
                    {
                        "slug": "clinical-medicine",
                        "name": "临床医学",
                        "discipline": "医学",
                        "recommended_regions": ["江苏"],
                        "summary": "测试专业摘要",
                        "sections": [
                            {
                                "type": "fit_for",
                                "title": "适合人群",
                                "items": ["原始专业正文"],
                            }
                        ],
                        "related_schools": [],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(catalog_service, "CATALOG_PATH", path)
    catalog_service.load_catalog.cache_clear()
    yield path
    catalog_service.load_catalog.cache_clear()


def test_content_sections_endpoint_returns_school_and_major_entries(sections_catalog_file) -> None:
    response = client.get("/api/admin/content-sections", headers=auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert any(item["slug"] == "southeast-university" for item in payload["schools"])
    assert any(item["slug"] == "clinical-medicine" for item in payload["majors"])


def test_update_school_sections(sections_catalog_file) -> None:
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

    stored_payload = json.loads(sections_catalog_file.read_text(encoding="utf-8"))
    assert stored_payload["schools"][0]["sections"][1]["title"] == "坑点提醒"


def test_update_major_sections_rejects_partially_filled_section(sections_catalog_file) -> None:
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
