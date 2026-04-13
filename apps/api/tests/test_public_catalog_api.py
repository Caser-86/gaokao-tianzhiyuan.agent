from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_schools_filters_by_region() -> None:
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
            }
        ],
        "total": 1,
    }


def test_school_detail_returns_modular_sections() -> None:
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


def test_list_majors_returns_catalog_cards() -> None:
    response = client.get("/api/public/majors")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 4
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
    }
    assert payload["items"][-1]["slug"] == "microelectronics"
