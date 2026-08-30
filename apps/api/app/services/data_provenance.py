from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_DATA_PROVENANCE: dict[str, object] = {
    "status": "demo",
    "source_name": "项目手工编写演示数据",
    "source_url": None,
    "updated_at": "2026-08-30",
    "applicable_year": None,
    "region": "多地区示例",
    "official": False,
    "disclaimer": "仅用于功能演示，不构成招生、排名或志愿决策依据。",
}

DATA_PROVENANCE_PATH = Path(__file__).resolve().parents[4] / "data" / "catalog.json"
PROVENANCE_STATUSES = {"demo", "secondary", "official"}


def _is_http_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_valid_provenance(value: object) -> bool:
    if not isinstance(value, dict):
        return False

    status = value.get("status")
    if status not in PROVENANCE_STATUSES:
        return False

    for field in ("source_name", "region", "disclaimer"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            return False

    updated_at = value.get("updated_at")
    if not isinstance(updated_at, str):
        return False
    try:
        date.fromisoformat(updated_at)
    except ValueError:
        return False

    if not isinstance(value.get("official"), bool):
        return False
    if status == "demo" and value["official"] is not False:
        return False

    source_url = value.get("source_url")
    if source_url is not None and not _is_http_url(source_url):
        return False

    applicable_year = value.get("applicable_year")
    if applicable_year is not None and (
        isinstance(applicable_year, bool) or not isinstance(applicable_year, int)
    ):
        return False

    return not (status != "demo" and (source_url is None or applicable_year is None))


def _load_data_provenance() -> dict[str, object]:
    try:
        payload = json.loads(DATA_PROVENANCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_DATA_PROVENANCE)

    provenance = payload.get("data_provenance") if isinstance(payload, dict) else None
    if not _is_valid_provenance(provenance):
        return dict(DEFAULT_DATA_PROVENANCE)

    return {
        "status": provenance["status"],
        "source_name": provenance["source_name"],
        "source_url": provenance["source_url"],
        "updated_at": provenance["updated_at"],
        "applicable_year": provenance["applicable_year"],
        "region": provenance["region"],
        "official": provenance["official"],
        "disclaimer": provenance["disclaimer"],
    }


def get_data_provenance() -> dict[str, Any]:
    """返回公开数据的来源边界，并为每次调用提供独立字典。"""
    return dict(_load_data_provenance())
