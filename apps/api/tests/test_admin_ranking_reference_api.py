import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import catalog as catalog_service


@pytest.fixture
def ranking_catalog_file(tmp_path, monkeypatch):
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
                        "summary": "测试学校",
                        "sections": [],
                        "related_majors": [],
                        "ranking_references": [
                            {
                                "source": "软科中国大学排名",
                                "year": 2025,
                                "label": "全国第 15 名",
                                "scope": "综合类高校",
                                "note": "用于综合实力参考",
                                "url": "https://example.com/rankings/southeast-university",
                            }
                        ],
                    }
                ],
                "majors": [
                    {
                        "slug": "clinical-medicine",
                        "name": "临床医学",
                        "discipline": "医学",
                        "recommended_regions": ["江苏"],
                        "summary": "测试专业",
                        "sections": [],
                        "related_schools": [],
                        "ranking_references": [
                            {
                                "source": "教育部学科评估",
                                "year": 2023,
                                "label": "A-",
                                "scope": "一级学科",
                                "note": "用于学科实力参考",
                                "url": "https://example.com/rankings/clinical-medicine",
                            }
                        ],
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


def test_ranking_reference_endpoint_returns_school_and_major_entries(
    ranking_catalog_file,
):
    with TestClient(app) as client:
        response = client.get(
            "/api/admin/ranking-references",
            headers={"x-admin-token": settings.admin_token},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schools"] == [
        {
            "slug": "southeast-university",
            "name": "东南大学",
            "ranking_references": [
                {
                    "source": "软科中国大学排名",
                    "year": 2025,
                    "label": "全国第 15 名",
                    "scope": "综合类高校",
                    "note": "用于综合实力参考",
                    "url": "https://example.com/rankings/southeast-university",
                }
            ],
        }
    ]
    assert payload["majors"] == [
        {
            "slug": "clinical-medicine",
            "name": "临床医学",
            "ranking_references": [
                {
                    "source": "教育部学科评估",
                    "year": 2023,
                    "label": "A-",
                    "scope": "一级学科",
                    "note": "用于学科实力参考",
                    "url": "https://example.com/rankings/clinical-medicine",
                }
            ],
        }
    ]


def test_update_school_ranking_references(ranking_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/ranking-references/schools/southeast-university",
            headers={"x-admin-token": settings.admin_token},
            json={
                "ranking_references": [
                    {
                        "source": "软科中国大学排名",
                        "year": 2026,
                        "label": "全国第 12 名",
                        "scope": "综合类高校",
                        "note": "更新后的榜单备注",
                        "url": "https://example.com/new-ranking",
                    }
                ]
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "东南大学",
        "ranking_references": [
            {
                "source": "软科中国大学排名",
                "year": 2026,
                "label": "全国第 12 名",
                "scope": "综合类高校",
                "note": "更新后的榜单备注",
                "url": "https://example.com/new-ranking",
            }
        ],
    }

    stored_payload = json.loads(ranking_catalog_file.read_text(encoding="utf-8"))
    assert stored_payload["schools"][0]["ranking_references"][0]["year"] == 2026


def test_update_major_ranking_references_rejects_invalid_year(ranking_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/ranking-references/majors/clinical-medicine",
            headers={"x-admin-token": settings.admin_token},
            json={
                "ranking_references": [
                    {
                        "source": "教育部学科评估",
                        "year": 0,
                        "label": "A-",
                        "scope": "一级学科",
                        "note": "",
                        "url": "",
                    }
                ]
            },
        )

    assert response.status_code == 422
