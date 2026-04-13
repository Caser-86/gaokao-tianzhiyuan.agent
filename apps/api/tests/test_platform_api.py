from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_product_catalog_returns_entitlement_bundles() -> None:
    response = client.get("/api/platform/products")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "slug": "insight-weekly",
                "name": "志愿快报订阅",
                "description": "适合持续接收学校、专业、地域变化提醒。",
                "entitlements": [
                    "school_basic_access",
                    "major_basic_access",
                    "risk_alert_access",
                ],
            },
            {
                "slug": "deep-dive-pack",
                "name": "深度报告包",
                "description": "适合需要学校、专业、地域和就业深度分析的家庭。",
                "entitlements": [
                    "school_deep_dive_access",
                    "major_deep_dive_access",
                    "region_compare_access",
                ],
            },
        ]
    }


def test_entitlement_evaluation_is_decoupled_from_products() -> None:
    response = client.post(
        "/api/platform/entitlements/evaluate",
        json={"product_slugs": ["deep-dive-pack", "insight-weekly"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "product_slugs": ["deep-dive-pack", "insight-weekly"],
        "entitlements": [
            "major_basic_access",
            "major_deep_dive_access",
            "region_compare_access",
            "risk_alert_access",
            "school_basic_access",
            "school_deep_dive_access",
        ],
    }


def test_track_event_accepts_funnel_metadata() -> None:
    response = client.post(
        "/api/platform/events",
        json={
            "event_name": "search_submitted",
            "step": "query_form",
            "metadata": {"query": "东南大学", "audience": "parent"},
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "event": {
            "event_name": "search_submitted",
            "step": "query_form",
            "metadata": {"query": "东南大学", "audience": "parent"},
        },
    }
