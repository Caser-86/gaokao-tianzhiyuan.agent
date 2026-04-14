import json
from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.services import featured_content as featured_content_service

client = TestClient(app)


def _write_featured_content(path) -> None:
    path.write_text(
        json.dumps(
            {
                "schools": [
                    {
                        "slug": "southeast-university",
                        "is_featured": True,
                        "hero_image_url": "https://cdn.example.com/southeast.jpg",
                    },
                    {
                        "slug": "west-china-medical-center",
                        "is_featured": True,
                        "hero_image_url": "",
                    },
                ],
                "majors": [
                    {
                        "slug": "clinical-medicine",
                        "is_featured": True,
                    },
                    {
                        "slug": "computer-science",
                        "is_featured": True,
                    },
                ],
                "rotation": {
                    "schools": {
                        "enabled": False,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [],
                    },
                    "majors": {
                        "enabled": False,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_list_schools_returns_current_rotation_window(tmp_path, monkeypatch) -> None:
    featured_content_path = tmp_path / "featured-content.json"
    featured_content_path.write_text(
        json.dumps(
            {
                "schools": [
                    {
                        "slug": "southeast-university",
                        "is_featured": True,
                        "hero_image_url": "",
                    },
                    {
                        "slug": "west-china-medical-center",
                        "is_featured": True,
                        "hero_image_url": "",
                    },
                ],
                "majors": [
                    {
                        "slug": "clinical-medicine",
                        "is_featured": True,
                    },
                    {
                        "slug": "computer-science",
                        "is_featured": True,
                    },
                ],
                "rotation": {
                    "schools": {
                        "enabled": True,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [
                            "west-china-medical-center",
                            "southeast-university",
                        ],
                    },
                    "majors": {
                        "enabled": False,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", featured_content_path)
    monkeypatch.setattr(featured_content_service, "ROTATION_ANCHOR_DATE", date.today())

    response = client.get("/api/public/schools")

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["items"]] == ["west-china-medical-center"]


def test_list_schools_only_returns_featured_items(tmp_path, monkeypatch) -> None:
    featured_content_path = tmp_path / "featured-content.json"
    _write_featured_content(featured_content_path)
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", featured_content_path)

    response = client.get("/api/public/schools")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "slug": "southeast-university",
                "name": "\u4e1c\u5357\u5927\u5b66",
                "region": "\u6c5f\u82cf",
                "city": "\u5357\u4eac",
                "tags": ["985", "\u53cc\u4e00\u6d41", "\u5de5\u79d1\u5f3a\u6821"],
                "summary": "\u5efa\u7b51\u3001\u7535\u5b50\u3001\u5de5\u79d1\u5b9e\u529b\u5f3a\uff0c\u9002\u5408\u7406\u5de5\u57fa\u7840\u624e\u5b9e\u4e14\u60f3\u7559\u5728\u957f\u4e09\u89d2\u53d1\u5c55\u7684\u8003\u751f\u3002",
                "hero_image_url": "https://cdn.example.com/southeast.jpg",
                "has_ranking_references": True,
            },
            {
                "slug": "west-china-medical-center",
                "name": "\u534e\u897f\u533b\u5b66\u4e2d\u5fc3",
                "region": "\u56db\u5ddd",
                "city": "\u6210\u90fd",
                "tags": ["\u533b\u5b66\u5f3a\u6821", "\u897f\u90e8\u9f99\u5934", "\u9644\u5c5e\u533b\u9662\u5f3a"],
                "summary": "\u4e34\u5e8a\u533b\u5b66\u57f9\u517b\u5b9e\u529b\u5f3a\uff0c\u9002\u5408\u60f3\u8d70\u533b\u5b66\u957f\u7ebf\u53d1\u5c55\u3001\u80fd\u63a5\u53d7\u9ad8\u5f3a\u5ea6\u57f9\u517b\u7684\u8003\u751f\u3002",
                "hero_image_url": "",
                "has_ranking_references": True,
            },
        ],
        "total": 2,
    }


def test_list_schools_filters_by_region(tmp_path, monkeypatch) -> None:
    featured_content_path = tmp_path / "featured-content.json"
    _write_featured_content(featured_content_path)
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", featured_content_path)

    response = client.get("/api/public/schools", params={"region": "\u6c5f\u82cf"})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "slug": "southeast-university",
                "name": "\u4e1c\u5357\u5927\u5b66",
                "region": "\u6c5f\u82cf",
                "city": "\u5357\u4eac",
                "tags": ["985", "\u53cc\u4e00\u6d41", "\u5de5\u79d1\u5f3a\u6821"],
                "summary": "\u5efa\u7b51\u3001\u7535\u5b50\u3001\u5de5\u79d1\u5b9e\u529b\u5f3a\uff0c\u9002\u5408\u7406\u5de5\u57fa\u7840\u624e\u5b9e\u4e14\u60f3\u7559\u5728\u957f\u4e09\u89d2\u53d1\u5c55\u7684\u8003\u751f\u3002",
                "hero_image_url": "https://cdn.example.com/southeast.jpg",
                "has_ranking_references": True,
            }
        ],
        "total": 1,
    }


def test_school_detail_returns_modular_sections() -> None:
    response = client.get("/api/public/schools/southeast-university")

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "\u4e1c\u5357\u5927\u5b66",
        "region": "\u6c5f\u82cf",
        "city": "\u5357\u4eac",
        "tags": ["985", "\u53cc\u4e00\u6d41", "\u5de5\u79d1\u5f3a\u6821"],
        "summary": "\u5efa\u7b51\u3001\u7535\u5b50\u3001\u5de5\u79d1\u5b9e\u529b\u5f3a\uff0c\u9002\u5408\u7406\u5de5\u57fa\u7840\u624e\u5b9e\u4e14\u60f3\u7559\u5728\u957f\u4e09\u89d2\u53d1\u5c55\u7684\u8003\u751f\u3002",
        "sections": [
            {
                "type": "highlights",
                "title": "\u5b66\u6821\u4eae\u70b9",
                "items": [
                    "\u5efa\u7b51\u3001\u571f\u6728\u3001\u7535\u5b50\u79d1\u5b66\u4e0e\u6280\u672f\u957f\u671f\u5f3a\u52bf\u3002",
                    "\u5357\u4eac\u533a\u4f4d\u597d\uff0c\u5b9e\u4e60\u4e0e\u5347\u5b66\u8d44\u6e90\u5bc6\u96c6\u3002",
                    "\u6574\u4f53\u5b66\u98ce\u504f\u786c\u6838\uff0c\u9002\u5408\u81ea\u9a71\u578b\u5b66\u751f\u3002",
                ],
            },
            {
                "type": "major_recommendations",
                "title": "\u63a8\u8350\u4e13\u4e1a",
                "items": [
                    "\u5efa\u7b51\u5b66\uff1a\u884c\u4e1a\u8ba4\u53ef\u5ea6\u9ad8\uff0c\u4f46\u5b66\u4e60\u5f3a\u5ea6\u5927\u3002",
                    "\u7535\u5b50\u79d1\u5b66\u4e0e\u6280\u672f\uff1a\u9002\u914d\u82af\u7247\u4e0e\u786c\u79d1\u6280\u5c31\u4e1a\u65b9\u5411\u3002",
                    "\u8ba1\u7b97\u673a\u7c7b\uff1a\u4fdd\u7814\u548c\u5c31\u4e1a\u90fd\u6bd4\u8f83\u7a33\u3002",
                ],
            },
            {
                "type": "pitfalls",
                "title": "\u62a5\u8003\u5751\u70b9",
                "items": [
                    "\u70ed\u95e8\u4e13\u4e1a\u5206\u6d41\u7ade\u4e89\u5f3a\uff0c\u4e0d\u80fd\u53ea\u770b\u5b66\u6821\u540d\u6c14\u3002",
                    "\u90e8\u5206\u4e13\u4e1a\u57f9\u517b\u8282\u594f\u7d27\uff0c\u8bfb\u4e66\u538b\u529b\u4e0d\u5c0f\u3002",
                    "\u5efa\u7b51\u7c7b\u9700\u8981\u957f\u671f\u6295\u5165\uff0c\u4e0d\u9002\u5408\u53ea\u56fe\u5b66\u6821\u724c\u5b50\u62a5\u8003\u3002",
                ],
            },
        ],
        "related_majors": ["architecture", "microelectronics", "computer-science"],
        "ranking_references": [
            {
                "source": "\u8f6f\u79d1\u4e2d\u56fd\u5927\u5b66\u6392\u540d",
                "year": 2025,
                "label": "\u5168\u56fd\u7b2c 15 \u540d",
                "scope": "\u7efc\u5408\u7c7b\u9ad8\u6821",
                "note": "\u7528\u4e8e\u7efc\u5408\u5b9e\u529b\u53c2\u8003\uff0c\u4e0d\u7b49\u540c\u4e8e\u5177\u4f53\u4e13\u4e1a\u4f18\u52bf\u3002",
                "url": "https://example.com/rankings/southeast-university",
            }
        ],
    }


def test_major_detail_returns_career_and_risk_sections() -> None:
    response = client.get("/api/public/majors/clinical-medicine")

    assert response.status_code == 200
    assert response.json() == {
        "slug": "clinical-medicine",
        "name": "\u4e34\u5e8a\u533b\u5b66",
        "discipline": "\u533b\u5b66",
        "recommended_regions": ["\u6c5f\u82cf", "\u6d59\u6c5f", "\u56db\u5ddd"],
        "summary": "\u57f9\u517b\u5468\u671f\u957f\u3001\u5b66\u4e60\u538b\u529b\u9ad8\uff0c\u4f46\u804c\u4e1a\u58c1\u5792\u5f3a\uff0c\u9002\u5408\u6297\u538b\u5f3a\u4e14\u613f\u610f\u957f\u671f\u6295\u5165\u7684\u8003\u751f\u3002",
        "sections": [
            {
                "type": "fit_for",
                "title": "\u9002\u5408\u4eba\u7fa4",
                "items": [
                    "\u80fd\u63a5\u53d7\u957f\u57f9\u517b\u5468\u671f\u548c\u6301\u7eed\u8003\u8bd5\u538b\u529b\u3002",
                    "\u5bf9\u4e34\u5e8a\u4e00\u7ebf\u5de5\u4f5c\u6709\u771f\u5b9e\u5174\u8da3\uff0c\u4e0d\u53ea\u770b\u7a33\u5b9a\u6027\u3002",
                    "\u5bb6\u5ead\u80fd\u63a5\u53d7\u524d\u671f\u6295\u5165\u5927\u3001\u56de\u62a5\u6765\u5f97\u6162\u3002",
                ],
            },
            {
                "type": "career_paths",
                "title": "\u5c31\u4e1a\u53bb\u5411",
                "items": [
                    "\u4e09\u7532\u533b\u9662\u4e34\u5e8a\u5c97",
                    "\u89c4\u57f9\u540e\u7ee7\u7eed\u4e13\u57f9\u6216\u8bfb\u7814\u6df1\u9020",
                    "\u533b\u5b66\u79d1\u7814\u4e0e\u533b\u9662\u7ba1\u7406\u65b9\u5411",
                ],
            },
            {
                "type": "pitfalls",
                "title": "\u5751\u70b9\u63d0\u9192",
                "items": [
                    "\u672c\u79d1\u6bd5\u4e1a\u76f4\u63a5\u9ad8\u8d28\u91cf\u5c31\u4e1a\u5e76\u4e0d\u8f7b\u677e\uff0c\u8bfb\u7814\u8bfb\u535a\u5f88\u5e38\u89c1\u3002",
                    "\u503c\u73ed\u548c\u89c4\u57f9\u5f3a\u5ea6\u9ad8\uff0c\u4e0d\u80fd\u53ea\u770b\u793e\u4f1a\u5370\u8c61\u3002",
                    "\u533b\u5b66\u53e3\u7891\u3001\u9644\u5c5e\u533b\u9662\u5b9e\u529b\u3001\u57ce\u5e02\u8d44\u6e90\u5dee\u5f02\u5f88\u5927\u3002",
                ],
            },
        ],
        "related_schools": ["southeast-university", "west-china-medical-center"],
        "ranking_references": [
            {
                "source": "\u6559\u80b2\u90e8\u5b66\u79d1\u8bc4\u4f30",
                "year": 2023,
                "label": "\u4e34\u5e8a\u533b\u5b66 A-",
                "scope": "\u4e00\u7ea7\u5b66\u79d1",
                "note": "\u9002\u5408\u4f5c\u4e3a\u533b\u5b66\u5b66\u79d1\u5b9e\u529b\u53c2\u8003\u3002",
                "url": "https://example.com/rankings/clinical-medicine",
            }
        ],
    }


def test_school_detail_returns_ranking_references_for_west_china() -> None:
    response = client.get("/api/public/schools/west-china-medical-center")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "\u8f6f\u79d1\u4e2d\u56fd\u533b\u5b66\u9662\u6821\u6392\u540d",
            "year": 2025,
            "label": "\u5168\u56fd\u524d 10",
            "scope": "\u533b\u5b66\u9662\u6821",
            "note": "\u9002\u5408\u4f5c\u4e3a\u4e34\u5e8a\u533b\u5b66\u57f9\u517b\u5e73\u53f0\u7684\u6a2a\u5411\u53c2\u8003\u3002",
            "url": "https://example.com/rankings/west-china-medical-center",
        }
    ]


def test_major_detail_returns_ranking_references_for_computer_science() -> None:
    response = client.get("/api/public/majors/computer-science")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "\u6559\u80b2\u90e8\u5b66\u79d1\u8bc4\u4f30",
            "year": 2023,
            "label": "\u8ba1\u7b97\u673a\u79d1\u5b66\u4e0e\u6280\u672f B+",
            "scope": "\u4e00\u7ea7\u5b66\u79d1",
            "note": "\u9002\u5408\u4f5c\u4e3a\u9662\u6821\u8ba1\u7b97\u673a\u5b66\u79d1\u5b9e\u529b\u53c2\u8003\u3002",
            "url": "https://example.com/rankings/computer-science",
        }
    ]


def test_list_majors_returns_catalog_cards(tmp_path, monkeypatch) -> None:
    featured_content_path = tmp_path / "featured-content.json"
    _write_featured_content(featured_content_path)
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", featured_content_path)

    response = client.get("/api/public/majors")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 2
    assert payload["items"][0] == {
        "slug": "clinical-medicine",
        "name": "\u4e34\u5e8a\u533b\u5b66",
        "discipline": "\u533b\u5b66",
        "recommended_regions": [
            "\u6c5f\u82cf",
            "\u6d59\u6c5f",
            "\u56db\u5ddd",
        ],
        "summary": "\u57f9\u517b\u5468\u671f\u957f\u3001\u5b66\u4e60\u538b\u529b\u9ad8\uff0c\u4f46\u804c\u4e1a\u58c1\u5792\u5f3a\uff0c\u9002\u5408\u6297\u538b\u5f3a\u4e14\u613f\u610f\u957f\u671f\u6295\u5165\u7684\u8003\u751f\u3002",
        "has_ranking_references": True,
    }
    assert payload["items"][-1]["slug"] == "computer-science"
    assert payload["items"][-1]["has_ranking_references"] is True


def test_list_majors_falls_back_to_all_featured_items_when_rotation_disabled(
    tmp_path,
    monkeypatch,
) -> None:
    featured_content_path = tmp_path / "featured-content.json"
    _write_featured_content(featured_content_path)
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", featured_content_path)

    response = client.get("/api/public/majors")

    assert response.status_code == 200
    assert {item["slug"] for item in response.json()["items"]} == {
        "clinical-medicine",
        "computer-science",
    }
