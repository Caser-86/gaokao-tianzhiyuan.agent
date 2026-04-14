from __future__ import annotations

import json
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

FEATURED_CONTENT_PATH = Path(__file__).resolve().parents[4] / "data" / "featured-content.json"
ROTATION_ANCHOR_DATE = date(2026, 4, 14)
WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class _ImageCandidateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.og_image: str | None = None
        self.first_image: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta":
            property_name = (values.get("property") or values.get("name") or "").lower()
            content = (values.get("content") or "").strip()
            if property_name == "og:image" and content and self.og_image is None:
                self.og_image = content

        if tag == "img":
            src = (values.get("src") or "").strip()
            if src and self.first_image is None:
                self.first_image = src


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


def fetch_school_image_candidate(slug: str) -> dict[str, Any]:
    from .catalog import get_school_detail, get_school_website

    school = get_school_detail(slug)
    if school is None:
        raise KeyError(slug)

    website = get_school_website(slug)
    if not website:
        return {
            "slug": school["slug"],
            "name": school["name"],
            "status": "missing",
            "source_url": None,
            "suggested_image_url": None,
            "message": "学校未配置可抓取的官网地址",
        }

    request = Request(
        website,
        headers={"User-Agent": "gaokao-agent/1.0 (+featured-school-image-suggestion)"},
    )

    try:
        with urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return {
            "slug": school["slug"],
            "name": school["name"],
            "status": "failed",
            "source_url": website,
            "suggested_image_url": None,
            "message": "抓取失败，请稍后重试",
        }

    parser = _ImageCandidateParser()
    parser.feed(html)
    candidate = parser.og_image or parser.first_image

    if not candidate:
        return {
            "slug": school["slug"],
            "name": school["name"],
            "status": "missing",
            "source_url": website,
            "suggested_image_url": None,
            "message": "官网页面未找到可用图片",
        }

    return {
        "slug": school["slug"],
        "name": school["name"],
        "status": "found",
        "source_url": website,
        "suggested_image_url": urljoin(website, candidate),
        "message": None,
    }


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


def _preview_items(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "slug": item["slug"],
            "name": item["name"],
        }
        for item in entries
    ]


def _preview_entry_for_date(
    payload: dict[str, Any],
    target_date: date,
) -> dict[str, Any]:
    schools = _current_rotation_window(
        payload["schools"],
        payload["rotation"]["schools"],
        today=target_date,
    )
    majors = _current_rotation_window(
        payload["majors"],
        payload["rotation"]["majors"],
        today=target_date,
    )
    return {
        "date": target_date.isoformat(),
        "weekday": WEEKDAY_LABELS[target_date.weekday()],
        "schools": _preview_items(schools),
        "majors": _preview_items(majors),
    }


def _next_preview_items(
    entries: list[dict[str, Any]],
    rule: dict[str, Any],
    *,
    today: date,
) -> list[dict[str, str]]:
    if not rule.get("enabled") or not rule.get("ordered_slugs"):
        return _preview_items(_current_rotation_window(entries, rule, today=today))

    frequency_days = int(rule.get("frequency_days", 1) or 1)
    next_date = today + timedelta(days=max(frequency_days, 1))
    return _preview_items(_current_rotation_window(entries, rule, today=next_date))


def list_current_featured_schools() -> list[dict[str, Any]]:
    payload = list_featured_content()
    return _current_rotation_window(payload["schools"], payload["rotation"]["schools"])


def list_current_featured_majors() -> list[dict[str, Any]]:
    payload = list_featured_content()
    return _current_rotation_window(payload["majors"], payload["rotation"]["majors"])


def build_featured_content_preview(
    *,
    preview_date: date | None = None,
) -> dict[str, Any]:
    payload = list_featured_content()
    today = date.today()
    today_entry = _preview_entry_for_date(payload, today)
    next_preview = {
        "schools": _next_preview_items(
            payload["schools"],
            payload["rotation"]["schools"],
            today=today,
        ),
        "majors": _next_preview_items(
            payload["majors"],
            payload["rotation"]["majors"],
            today=today,
        ),
    }
    schedule = [
        _preview_entry_for_date(payload, today + timedelta(days=offset))
        for offset in range(7)
    ]
    selected_date_entry = (
        _preview_entry_for_date(payload, preview_date)
        if preview_date is not None
        else None
    )
    return {
        "today": {
            "schools": today_entry["schools"],
            "majors": today_entry["majors"],
        },
        "next": next_preview,
        "schedule": schedule,
        "selected_date": selected_date_entry,
        "selected_date_error": None,
    }
