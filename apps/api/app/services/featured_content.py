from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FEATURED_CONTENT_PATH = Path(__file__).resolve().parents[4] / "data" / "featured-content.json"


def _read_featured_content() -> dict[str, Any]:
    if not FEATURED_CONTENT_PATH.exists():
        return {"schools": [], "majors": []}

    payload = json.loads(FEATURED_CONTENT_PATH.read_text(encoding="utf-8"))
    payload.setdefault("schools", [])
    payload.setdefault("majors", [])
    return payload


def _write_featured_content(payload: dict[str, Any]) -> None:
    FEATURED_CONTENT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _catalog_entities(entity_key: str) -> list[dict[str, Any]]:
    from .catalog import load_catalog

    return load_catalog()[entity_key]


def _catalog_entity_by_slug(entity_key: str, slug: str) -> dict[str, Any]:
    entity = next(
        (item for item in _catalog_entities(entity_key) if item["slug"] == slug),
        None,
    )
    if entity is None:
        raise KeyError(slug)
    return entity


def list_featured_content() -> dict[str, list[dict[str, Any]]]:
    payload = _read_featured_content()
    school_config = {item["slug"]: item for item in payload["schools"]}
    major_config = {item["slug"]: item for item in payload["majors"]}

    schools = [
        {
            "slug": school["slug"],
            "name": school["name"],
            "is_featured": bool(school_config.get(school["slug"], {}).get("is_featured", False)),
            "hero_image_url": school_config.get(school["slug"], {}).get("hero_image_url", ""),
        }
        for school in _catalog_entities("schools")
    ]
    majors = [
        {
            "slug": major["slug"],
            "name": major["name"],
            "is_featured": bool(major_config.get(major["slug"], {}).get("is_featured", False)),
        }
        for major in _catalog_entities("majors")
    ]

    return {"schools": schools, "majors": majors}


def update_featured_school(
    slug: str,
    *,
    is_featured: bool,
    hero_image_url: str | None,
) -> dict[str, Any]:
    school = _catalog_entity_by_slug("schools", slug)
    payload = _read_featured_content()
    entry = next((item for item in payload["schools"] if item["slug"] == slug), None)

    if entry is None:
        entry = {"slug": slug}
        payload["schools"].append(entry)

    entry["is_featured"] = is_featured
    entry["hero_image_url"] = (hero_image_url or "").strip()
    _write_featured_content(payload)

    return {
        "slug": slug,
        "name": school["name"],
        "is_featured": is_featured,
        "hero_image_url": entry["hero_image_url"],
    }


def update_featured_major(
    slug: str,
    *,
    is_featured: bool,
) -> dict[str, Any]:
    major = _catalog_entity_by_slug("majors", slug)
    payload = _read_featured_content()
    entry = next((item for item in payload["majors"] if item["slug"] == slug), None)

    if entry is None:
        entry = {"slug": slug}
        payload["majors"].append(entry)

    entry["is_featured"] = is_featured
    _write_featured_content(payload)

    return {
        "slug": slug,
        "name": major["name"],
        "is_featured": is_featured,
    }
