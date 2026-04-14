from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .featured_content import (
    list_current_featured_majors,
    list_current_featured_schools,
)


CATALOG_PATH = Path(__file__).resolve().parents[4] / "data" / "catalog.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def get_search_entry() -> dict[str, Any]:
    return load_catalog()["search_entry"]


def list_schools(*, region: str | None = None, keyword: str | None = None) -> dict[str, Any]:
    schools = load_catalog()["schools"]
    featured_schools = {
        school["slug"]: school
        for school in list_current_featured_schools()
    }
    filtered = []

    for school in schools:
        config = featured_schools.get(school["slug"])
        if config is None:
            continue

        if region and school["region"] != region:
            continue

        if keyword:
            haystack = " ".join(
                [
                    school["name"],
                    school["city"],
                    school["region"],
                    school["summary"],
                    " ".join(school["tags"]),
                ]
            )
            if keyword.lower() not in haystack.lower():
                continue

        filtered.append(
            {
                "slug": school["slug"],
                "name": school["name"],
                "region": school["region"],
                "city": school["city"],
                "tags": school["tags"],
                "summary": school["summary"],
                "hero_image_url": config["hero_image_url"],
                "has_ranking_references": bool(school.get("ranking_references")),
            }
        )

    return {
        "items": filtered,
        "total": len(filtered),
    }


def list_majors() -> dict[str, Any]:
    majors = load_catalog()["majors"]
    featured_majors = {
        major["slug"]
        for major in list_current_featured_majors()
    }
    items = [
        {
            "slug": major["slug"],
            "name": major["name"],
            "discipline": major["discipline"],
            "recommended_regions": major["recommended_regions"],
            "summary": major["summary"],
            "has_ranking_references": bool(major.get("ranking_references")),
        }
        for major in majors
        if major["slug"] in featured_majors
    ]

    return {
        "items": items,
        "total": len(items),
    }


def get_school_detail(slug: str) -> dict[str, Any] | None:
    schools = load_catalog()["schools"]
    return next((school for school in schools if school["slug"] == slug), None)


def get_major_detail(slug: str) -> dict[str, Any] | None:
    majors = load_catalog()["majors"]
    return next((major for major in majors if major["slug"] == slug), None)


def list_admin_ranking_references() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {
                "slug": school["slug"],
                "name": school["name"],
                "ranking_references": school.get("ranking_references", []),
            }
            for school in catalog["schools"]
        ],
        "majors": [
            {
                "slug": major["slug"],
                "name": major["name"],
                "ranking_references": major.get("ranking_references", []),
            }
            for major in catalog["majors"]
        ],
    }


def list_admin_content_summaries() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {
                "slug": school["slug"],
                "name": school["name"],
                "summary": school["summary"],
            }
            for school in catalog["schools"]
        ],
        "majors": [
            {
                "slug": major["slug"],
                "name": major["name"],
                "summary": major["summary"],
            }
            for major in catalog["majors"]
        ],
    }


def list_admin_content_sections() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {
                "slug": school["slug"],
                "name": school["name"],
                "sections": school.get("sections", []),
            }
            for school in catalog["schools"]
        ],
        "majors": [
            {
                "slug": major["slug"],
                "name": major["name"],
                "sections": major.get("sections", []),
            }
            for major in catalog["majors"]
        ],
    }


def list_admin_related_content() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {
                "slug": school["slug"],
                "name": school["name"],
                "related_majors": school.get("related_majors", []),
            }
            for school in catalog["schools"]
        ],
        "majors": [
            {
                "slug": major["slug"],
                "name": major["name"],
                "related_schools": major.get("related_schools", []),
            }
            for major in catalog["majors"]
        ],
    }


def update_ranking_references(
    entity_key: str,
    slug: str,
    ranking_references: list[dict[str, Any]],
) -> dict[str, Any]:
    catalog = load_catalog()
    entries = catalog[entity_key]
    entity = next((item for item in entries if item["slug"] == slug), None)
    if entity is None:
        raise KeyError(slug)

    entity["ranking_references"] = ranking_references
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    load_catalog.cache_clear()

    return {
        "slug": entity["slug"],
        "name": entity["name"],
        "ranking_references": entity.get("ranking_references", []),
    }


def update_content_summary(
    entity_key: str,
    slug: str,
    summary: str,
) -> dict[str, Any]:
    normalized_summary = summary.strip()
    if not normalized_summary:
        raise ValueError("summary is required")

    catalog = load_catalog()
    entries = catalog[entity_key]
    entity = next((item for item in entries if item["slug"] == slug), None)
    if entity is None:
        raise KeyError(slug)

    entity["summary"] = normalized_summary
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    load_catalog.cache_clear()

    return {
        "slug": entity["slug"],
        "name": entity["name"],
        "summary": entity["summary"],
    }


def update_content_sections(
    entity_key: str,
    slug: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    catalog = load_catalog()
    entries = catalog[entity_key]
    entity = next((item for item in entries if item["slug"] == slug), None)
    if entity is None:
        raise KeyError(slug)

    entity["sections"] = sections
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    load_catalog.cache_clear()

    return {
        "slug": entity["slug"],
        "name": entity["name"],
        "sections": entity.get("sections", []),
    }


def update_related_content(
    entity_key: str,
    slug: str,
    related_field: str,
    related_slugs: list[str],
) -> dict[str, Any]:
    catalog = load_catalog()
    entries = catalog[entity_key]
    entity = next((item for item in entries if item["slug"] == slug), None)
    if entity is None:
        raise KeyError(slug)

    related_entity_key = "majors" if related_field == "related_majors" else "schools"
    valid_related_slugs = {
        item["slug"]
        for item in catalog[related_entity_key]
    }
    invalid_slugs = [
        related_slug for related_slug in related_slugs if related_slug not in valid_related_slugs
    ]
    if invalid_slugs:
        raise ValueError("related content slug is invalid")

    entity[related_field] = related_slugs
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    load_catalog.cache_clear()

    return {
        "slug": entity["slug"],
        "name": entity["name"],
        related_field: entity.get(related_field, []),
    }
