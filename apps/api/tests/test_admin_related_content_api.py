import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import catalog as catalog_service


@pytest.fixture
def related_content_catalog_file(tmp_path, monkeypatch):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            {
                "search_entry": {
                    "title": "测试入口",
                    "description": "测试描述",
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
                        "related_majors": ["clinical-medicine"],
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
                        "related_schools": ["southeast-university"],
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


def test_related_content_endpoint_returns_school_and_major_entries(
    related_content_catalog_file,
):
    with TestClient(app) as client:
        response = client.get(
            "/api/admin/related-content",
            headers={"x-admin-token": settings.admin_token},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schools"] == [
        {
            "slug": "southeast-university",
            "name": "东南大学",
            "related_majors": ["clinical-medicine"],
        }
    ]
    assert payload["majors"] == [
        {
            "slug": "clinical-medicine",
            "name": "临床医学",
            "related_schools": ["southeast-university"],
        }
    ]


def test_update_school_related_content(related_content_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/related-content/schools/southeast-university",
            headers={"x-admin-token": settings.admin_token},
            json={"related_majors": ["clinical-medicine"]},
        )

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "东南大学",
        "related_majors": ["clinical-medicine"],
    }

    stored_payload = json.loads(related_content_catalog_file.read_text(encoding="utf-8"))
    assert stored_payload["schools"][0]["related_majors"] == ["clinical-medicine"]


def test_update_major_related_content_rejects_invalid_related_slug(
    related_content_catalog_file,
):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/related-content/majors/clinical-medicine",
            headers={"x-admin-token": settings.admin_token},
            json={"related_schools": ["missing-school"]},
        )

    assert response.status_code == 422
