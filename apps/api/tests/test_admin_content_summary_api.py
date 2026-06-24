import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import settings
from app.main import app
from app.models.catalog import School


@pytest.fixture
def summary_catalog_file(seed_catalog):
    """注入 catalog 数据到测试数据库。"""
    seed_catalog(
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
        }
    )


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


def test_update_school_summary(summary_catalog_file, engine):
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

    with Session(engine) as session:
        stored = session.exec(select(School).where(School.slug == "southeast-university")).first()
        assert stored is not None
        assert stored.summary == "更新后的学校摘要"


def test_update_major_summary_rejects_blank_summary(summary_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/content-summaries/majors/clinical-medicine",
            headers={"x-admin-token": settings.admin_token},
            json={"summary": "   "},
        )

    assert response.status_code == 422
