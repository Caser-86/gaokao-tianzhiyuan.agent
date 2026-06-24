import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import featured_content as featured_content_service

client = TestClient(app)

CATALOG_PATH = Path(__file__).resolve().parents[3] / "data" / "catalog.json"


def _load_catalog_data() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _featured_payload() -> dict:
    return {
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
    }


@pytest.fixture
def catalog_seed(seed_catalog):
    """从 data/catalog.json 注入完整 catalog 数据。"""
    seed_catalog(_load_catalog_data())


@pytest.fixture
def featured_seed(seed_featured):
    """注入默认 featured 数据。"""
    seed_featured(_featured_payload())


@pytest.fixture
def featured_with_rotation(seed_featured):
    """注入带轮播规则的 featured 数据。"""
    payload = _featured_payload()
    payload["rotation"]["schools"] = {
        "enabled": True,
        "frequency_days": 1,
        "window_size": 1,
        "ordered_slugs": [
            "west-china-medical-center",
            "southeast-university",
        ],
    }
    seed_featured(payload)


def test_list_schools_returns_current_rotation_window(
    catalog_seed, featured_with_rotation, monkeypatch
) -> None:
    monkeypatch.setattr(featured_content_service, "ROTATION_ANCHOR_DATE", date.today())

    response = client.get("/api/public/schools")

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["items"]] == ["west-china-medical-center"]


def test_list_schools_only_returns_featured_items(catalog_seed, featured_seed) -> None:
    response = client.get("/api/public/schools")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "slug": "southeast-university",
                "name": "东南大学",
                "region": "江苏",
                "city": "南京",
                "tags": ["985", "双一流", "工科强校"],
                "summary": "建筑、电子、工科实力强，适合理工基础扎实且想留在长三角发展的考生。",
                "hero_image_url": "https://cdn.example.com/southeast.jpg",
                "has_ranking_references": True,
            },
            {
                "slug": "west-china-medical-center",
                "name": "华西医学中心",
                "region": "四川",
                "city": "成都",
                "tags": ["医学强校", "西部龙头", "附属医院强"],
                "summary": "临床医学培养实力强，适合想走医学长线发展、能接受高强度培养的考生。",
                "hero_image_url": "",
                "has_ranking_references": True,
            },
        ],
        "total": 2,
    }


def test_list_schools_filters_by_region(catalog_seed, featured_seed) -> None:
    response = client.get("/api/public/schools", params={"region": "江苏"})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "slug": "southeast-university",
                "name": "东南大学",
                "region": "江苏",
                "city": "南京",
                "tags": ["985", "双一流", "工科强校"],
                "summary": "建筑、电子、工科实力强，适合理工基础扎实且想留在长三角发展的考生。",
                "hero_image_url": "https://cdn.example.com/southeast.jpg",
                "has_ranking_references": True,
            }
        ],
        "total": 1,
    }


def test_school_detail_returns_modular_sections(catalog_seed) -> None:
    response = client.get("/api/public/schools/southeast-university")

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "东南大学",
        "region": "江苏",
        "city": "南京",
        "tags": ["985", "双一流", "工科强校"],
        "summary": "建筑、电子、工科实力强，适合理工基础扎实且想留在长三角发展的考生。",
        "sections": [
            {
                "type": "highlights",
                "title": "学校亮点",
                "items": [
                    "建筑、土木、电子科学与技术长期强势。",
                    "南京区位好，实习与升学资源密集。",
                    "整体学风偏硬核，适合自驱型学生。",
                ],
            },
            {
                "type": "major_recommendations",
                "title": "推荐专业",
                "items": [
                    "建筑学：行业认可度高，但学习强度大。",
                    "电子科学与技术：适配芯片与硬科技就业方向。",
                    "计算机类：保研和就业都比较稳。",
                ],
            },
            {
                "type": "pitfalls",
                "title": "报考坑点",
                "items": [
                    "热门专业分流竞争强，不能只看学校名气。",
                    "部分专业培养节奏紧，读书压力不小。",
                    "建筑类需要长期投入，不适合只图学校牌子报考。",
                ],
            },
        ],
        "website": "",
        "related_majors": [
            "architecture",
            "microelectronics",
            "computer-science",
            "clinical-medicine",
        ],
        "ranking_references": [
            {
                "source": "软科中国大学排名",
                "year": 2025,
                "label": "全国第 15 名",
                "scope": "综合类高校",
                "note": "用于综合实力参考，不等同于具体专业优势。",
                "url": "https://example.com/rankings/southeast-university",
            }
        ],
    }


def test_major_detail_returns_career_and_risk_sections(catalog_seed) -> None:
    response = client.get("/api/public/majors/clinical-medicine")

    assert response.status_code == 200
    assert response.json() == {
        "slug": "clinical-medicine",
        "name": "临床医学",
        "discipline": "医学",
        "recommended_regions": ["江苏", "浙江", "四川"],
        "summary": "培养周期长、学习压力高，但职业壁垒强，适合抗压强且愿意长期投入的考生。",
        "sections": [
            {
                "type": "fit_for",
                "title": "适合人群",
                "items": [
                    "能接受长培养周期和持续考试压力。",
                    "对临床一线工作有真实兴趣，不只看稳定性。",
                    "家庭能接受前期投入大、回报来得慢。",
                ],
            },
            {
                "type": "career_paths",
                "title": "就业去向",
                "items": [
                    "三甲医院临床岗",
                    "规培后继续专培或读研深造",
                    "医学科研与医院管理方向",
                ],
            },
            {
                "type": "pitfalls",
                "title": "坑点提醒",
                "items": [
                    "本科毕业直接高质量就业并不轻松，读研读博很常见。",
                    "值班和规培强度高，不能只看社会印象。",
                    "医学口碑、附属医院实力、城市资源差异很大。",
                ],
            },
        ],
        "related_schools": ["west-china-medical-center", "southeast-university"],
        "ranking_references": [
            {
                "source": "教育部学科评估",
                "year": 2023,
                "label": "临床医学 A-",
                "scope": "一级学科",
                "note": "适合作为医学学科实力参考。",
                "url": "https://example.com/rankings/clinical-medicine",
            }
        ],
    }


def test_school_detail_returns_ranking_references_for_west_china(catalog_seed) -> None:
    response = client.get("/api/public/schools/west-china-medical-center")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "软科中国医学院校排名",
            "year": 2025,
            "label": "全国前 10",
            "scope": "医学院校",
            "note": "适合作为临床医学培养平台的横向参考。",
            "url": "https://example.com/rankings/west-china-medical-center",
        }
    ]


def test_major_detail_returns_ranking_references_for_computer_science(catalog_seed) -> None:
    response = client.get("/api/public/majors/computer-science")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "教育部学科评估",
            "year": 2023,
            "label": "计算机科学与技术 B+",
            "scope": "一级学科",
            "note": "适合作为院校计算机学科实力参考。",
            "url": "https://example.com/rankings/computer-science",
        }
    ]


def test_list_majors_returns_catalog_cards(catalog_seed, featured_seed) -> None:
    response = client.get("/api/public/majors")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 2
    assert payload["items"][0] == {
        "slug": "clinical-medicine",
        "name": "临床医学",
        "discipline": "医学",
        "recommended_regions": [
            "江苏",
            "浙江",
            "四川",
        ],
        "summary": "培养周期长、学习压力高，但职业壁垒强，适合抗压强且愿意长期投入的考生。",
        "has_ranking_references": True,
    }
    assert payload["items"][-1]["slug"] == "computer-science"
    assert payload["items"][-1]["has_ranking_references"] is True


def test_list_majors_falls_back_to_all_featured_items_when_rotation_disabled(
    catalog_seed, featured_seed
) -> None:
    response = client.get("/api/public/majors")

    assert response.status_code == 200
    assert {item["slug"] for item in response.json()["items"]} == {
        "clinical-medicine",
        "computer-science",
    }
