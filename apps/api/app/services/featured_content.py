from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

FEATURED_CONTENT_PATH = Path(__file__).resolve().parents[4] / "data" / "featured-content.json"
ROTATION_ANCHOR_DATE = date(2026, 4, 14)


def _default_rotation_rule() -> dict[str, Any]:
    return {
        "enabled": False,
        "frequency_days": 1,
        "window_size": 1,
        "ordered_slugs": [],
    }


def _normalize_rotation(payload: dict[str, Any]) -> dict[str, Any]:
    rotation = payload.setdefault("rotation", {})
    rotation.setdefault("schools", _default_rotation_rule())
    rotation.setdefault("majors", _default_rotation_rule())
    return rotation


def _read_featured_content() -> dict[str, Any]:
    if not FEATURED_CONTENT_PATH.exists():
        payload = {"schools": [], "majors": []}
        _normalize_rotation(payload)
        return payload

    payload = json.loads(FEATURED_CONTENT_PATH.read_text(encoding="utf-8"))
    payload.setdefault("schools", [])
    payload.setdefault("majors", [])
    _normalize_rotation(payload)
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


def _validate_rotation_rule(entity_key: str, ordered_slugs: list[str]) -> None:
    catalog_slugs = {item["slug"] for item in _catalog_entities(entity_key)}
    if len(ordered_slugs) != len(set(ordered_slugs)):
        raise ValueError("featured rotation contains duplicate slugs")

    for slug in ordered_slugs:
        if slug not in catalog_slugs:
            raise KeyError(slug)


def list_featured_content() -> dict[str, Any]:
    payload = _read_featured_content()
    school_config = {item["slug"]: item for item in payload["schools"]}
    major_config = {item["slug"]: item for item in payload["majors"]}
    rotation = _normalize_rotation(payload)

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

    return {"schools": schools, "majors": majors, "rotation": rotation}


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


def update_rotation_rule(
    rotation_key: str,
    *,
    enabled: bool,
    frequency_days: int,
    window_size: int,
    ordered_slugs: list[str],
) -> dict[str, Any]:
    if frequency_days < 1 or window_size < 1:
        raise ValueError("featured rotation values must be positive")

    entity_key = "schools" if rotation_key == "schools" else "majors"
    _validate_rotation_rule(entity_key, ordered_slugs)

    payload = _read_featured_content()
    rotation = _normalize_rotation(payload)
    rotation[rotation_key] = {
        "enabled": enabled,
        "frequency_days": frequency_days,
        "window_size": window_size,
        "ordered_slugs": ordered_slugs,
    }
    _write_featured_content(payload)
    return rotation[rotation_key]


def _current_rotation_window(
    entries: list[dict[str, Any]],
    rule: dict[str, Any],
    *,
    today: date | None = None,
) -> list[dict[str, Any]]:
    eligible = [item for item in entries if item.get("is_featured")]
    if not rule.get("enabled"):
        return eligible

    frequency_days = int(rule.get("frequency_days", 0) or 0)
    window_size = int(rule.get("window_size", 0) or 0)
    ordered_slugs = rule.get("ordered_slugs", [])

    if frequency_days < 1 or window_size < 1 or not ordered_slugs:
        return eligible

    eligible_by_slug = {item["slug"]: item for item in eligible}
    ordered = [eligible_by_slug[slug] for slug in ordered_slugs if slug in eligible_by_slug]
    if not ordered:
        return eligible

    today = today or date.today()
    rotation_step = ((today - ROTATION_ANCHOR_DATE).days // frequency_days) % len(ordered)
    window_size = min(window_size, len(ordered))
    return [ordered[(rotation_step + offset) % len(ordered)] for offset in range(window_size)]


def list_current_featured_schools() -> list[dict[str, Any]]:
    payload = list_featured_content()
    return _current_rotation_window(payload["schools"], payload["rotation"]["schools"])


def list_current_featured_majors() -> list[dict[str, Any]]:
    payload = list_featured_content()
    return _current_rotation_window(payload["majors"], payload["rotation"]["majors"])
