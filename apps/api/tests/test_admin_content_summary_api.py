import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import catalog as catalog_service


@pytest.fixture
def summary_catalog_file(tmp_path, monkeypatch):
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
                        "sections": [],
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
                        "sections": [],
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


def test_content_summary_endpoint_returns_school_and_major_entries(summary_catalog_file):
    with TestClient(app) as client:
        response = client.get(
            "/api/admin/content-summaries",
            headers={"x-admin-token": settings.admin_token},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schools"] == [
        {
            "slug": "southeast-university",
            "name": "东南大学",
            "summary": "测试学校摘要",
        }
    ]
    assert payload["majors"] == [
        {
            "slug": "clinical-medicine",
            "name": "临床医学",
            "summary": "测试专业摘要",
        }
    ]


def test_update_school_summary(summary_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/content-summaries/schools/southeast-university",
            headers={"x-admin-token": settings.admin_token},
            json={"summary": "更新后的学校摘要"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "东南大学",
        "summary": "更新后的学校摘要",
    }

    stored_payload = json.loads(summary_catalog_file.read_text(encoding="utf-8"))
    assert stored_payload["schools"][0]["summary"] == "更新后的学校摘要"


def test_update_major_summary_rejects_blank_summary(summary_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/content-summaries/majors/clinical-medicine",
            headers={"x-admin-token": settings.admin_token},
            json={"summary": "   "},
        )

    assert response.status_code == 422
