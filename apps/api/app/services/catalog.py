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
