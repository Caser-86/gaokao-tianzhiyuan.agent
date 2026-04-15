from __future__ import annotations

from typing import Any


PRODUCTS = [
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
            "smart_analysis",
        ],
    },
]


def list_products() -> dict[str, list[dict[str, Any]]]:
    return {"items": PRODUCTS}


def evaluate_entitlements(
    product_slugs: list[str],
    *,
    persisted_entitlements: list[str] | None = None,
) -> dict[str, list[str]]:
    entitlement_set = {
        entitlement
        for product in PRODUCTS
        if product["slug"] in product_slugs
        for entitlement in product["entitlements"]
    }
    entitlement_set.update(persisted_entitlements or [])

    return {
        "product_slugs": product_slugs,
        "entitlements": sorted(entitlement_set),
    }


def normalize_event(event_name: str, step: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_name": event_name,
        "step": step,
        "metadata": metadata,
    }
