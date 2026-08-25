"""Validate the repository's authoritative JSON demo data assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT / "data"


class DataAssetValidationError(ValueError):
    """Raised when a JSON data asset violates the repository contract."""


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataAssetValidationError(f"missing data asset: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataAssetValidationError(f"invalid JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise DataAssetValidationError(f"top-level JSON value must be an object: {path}")
    return payload


def _index_by_slug(items: Any, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        errors.append(f"{label} must be an array")
        return {}

    indexed: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        slug = item.get("slug")
        if not _is_non_empty_string(slug):
            errors.append(f"{label}[{index}].slug must be a non-empty string")
            continue
        if slug in indexed:
            errors.append(f"duplicate {label} slug: {slug}")
            continue
        indexed[slug] = item
    return indexed


def _validate_sections(items: Any, label: str, errors: list[str]) -> None:
    if items is None:
        return
    if not isinstance(items, list):
        errors.append(f"{label} must be an array")
        return
    for index, section in enumerate(items):
        if not isinstance(section, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        if not _is_non_empty_string(section.get("type")):
            errors.append(f"{label}[{index}].type must be a non-empty string")
        if not _is_non_empty_string(section.get("title")):
            errors.append(f"{label}[{index}].title must be a non-empty string")
        if not isinstance(section.get("items"), list) or not all(
            isinstance(item, str) and item.strip() for item in section["items"]
        ):
            errors.append(f"{label}[{index}].items must be an array of non-empty strings")


def _validate_relations(
    items: dict[str, dict[str, Any]],
    field: str,
    target_slugs: set[str],
    label: str,
    errors: list[str],
) -> None:
    for slug, item in items.items():
        relations = item.get(field, [])
        if not isinstance(relations, list) or not all(isinstance(value, str) for value in relations):
            errors.append(f"{label} {slug}.{field} must be an array of strings")
            continue
        for relation in relations:
            if relation not in target_slugs:
                errors.append(f"{label} {slug}.{field} references unknown slug: {relation}")


def _validate_ranking_references(
    items: dict[str, dict[str, Any]], label: str, errors: list[str]
) -> None:
    for slug, item in items.items():
        references = item.get("ranking_references", [])
        if not isinstance(references, list):
            errors.append(f"{label} {slug}.ranking_references must be an array")
            continue
        for index, reference in enumerate(references):
            reference_label = f"{label} {slug}.ranking_references[{index}]"
            if not isinstance(reference, dict):
                errors.append(f"{reference_label} must be an object")
                continue
            for field in ("source", "label", "scope", "url"):
                if not _is_non_empty_string(reference.get(field)):
                    errors.append(f"{reference_label}.{field} must be a non-empty string")
            if not isinstance(reference.get("year"), int) or isinstance(reference.get("year"), bool):
                errors.append(f"{reference_label}.year must be an integer")


def _validate_featured(
    featured: dict[str, Any],
    school_slugs: set[str],
    major_slugs: set[str],
    errors: list[str],
) -> None:
    for entity_type, known_slugs in (("schools", school_slugs), ("majors", major_slugs)):
        entries = featured.get(entity_type, [])
        if not isinstance(entries, list):
            errors.append(f"featured.{entity_type} must be an array")
            continue
        seen: set[str] = set()
        for index, item in enumerate(entries):
            if not isinstance(item, dict):
                errors.append(f"featured.{entity_type}[{index}] must be an object")
                continue
            slug = item.get("slug")
            if not _is_non_empty_string(slug):
                errors.append(f"featured.{entity_type}[{index}].slug must be a non-empty string")
                continue
            if slug in seen:
                errors.append(f"duplicate featured {entity_type} slug: {slug}")
            seen.add(slug)
            if slug not in known_slugs:
                errors.append(f"featured.{entity_type} references unknown slug: {slug}")
            if "is_featured" in item and not isinstance(item["is_featured"], bool):
                errors.append(f"featured.{entity_type}[{index}].is_featured must be boolean")

    rotation = featured.get("rotation", {})
    if not isinstance(rotation, dict):
        errors.append("featured.rotation must be an object")
        return

    for entity_type, known_slugs in (("schools", school_slugs), ("majors", major_slugs)):
        rule = rotation.get(entity_type, {})
        label = f"featured.rotation.{entity_type}"
        if not isinstance(rule, dict):
            errors.append(f"{label} must be an object")
            continue
        if "enabled" in rule and not isinstance(rule["enabled"], bool):
            errors.append(f"{label}.enabled must be boolean")
        for field in ("frequency_days", "window_size"):
            value = rule.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                errors.append(f"{label}.{field} must be a positive integer")
        ordered_slugs = rule.get("ordered_slugs", [])
        if not isinstance(ordered_slugs, list) or not all(
            isinstance(slug, str) for slug in ordered_slugs
        ):
            errors.append(f"{label}.ordered_slugs must be an array of strings")
            continue
        if len(ordered_slugs) != len(set(ordered_slugs)):
            errors.append(f"{label}.ordered_slugs must not contain duplicates")
        for slug in ordered_slugs:
            if slug not in known_slugs:
                errors.append(f"{label}.ordered_slugs references unknown slug: {slug}")


def validate_data(catalog: dict[str, Any], featured: dict[str, Any]) -> None:
    """Validate catalog and featured payloads, raising one actionable error."""
    errors: list[str] = []

    search_entry = catalog.get("search_entry")
    if not isinstance(search_entry, dict):
        errors.append("catalog.search_entry must be an object")
    else:
        for field in ("title", "description"):
            if not _is_non_empty_string(search_entry.get(field)):
                errors.append(f"catalog.search_entry.{field} must be a non-empty string")
        if not isinstance(search_entry.get("quick_prompts"), list) or not all(
            isinstance(prompt, str) and prompt.strip() for prompt in search_entry["quick_prompts"]
        ):
            errors.append("catalog.search_entry.quick_prompts must be an array of non-empty strings")

    schools = _index_by_slug(catalog.get("schools"), "catalog.schools", errors)
    majors = _index_by_slug(catalog.get("majors"), "catalog.majors", errors)

    for slug, school in schools.items():
        for field in ("name", "region", "city"):
            if not _is_non_empty_string(school.get(field)):
                errors.append(f"catalog.schools {slug}.{field} must be a non-empty string")
        _validate_sections(school.get("sections"), f"catalog.schools {slug}.sections", errors)

    for slug, major in majors.items():
        for field in ("name", "discipline"):
            if not _is_non_empty_string(major.get(field)):
                errors.append(f"catalog.majors {slug}.{field} must be a non-empty string")
        _validate_sections(major.get("sections"), f"catalog.majors {slug}.sections", errors)

    _validate_relations(schools, "related_majors", set(majors), "school", errors)
    _validate_relations(majors, "related_schools", set(schools), "major", errors)
    _validate_ranking_references(schools, "school", errors)
    _validate_ranking_references(majors, "major", errors)
    _validate_featured(featured, set(schools), set(majors), errors)

    if errors:
        raise DataAssetValidationError("\n".join(f"- {error}" for error in errors))


def validate_data_directory(data_dir: Path) -> tuple[int, int]:
    catalog = _load_json(data_dir / "catalog.json")
    featured = _load_json(data_dir / "featured-content.json")
    validate_data(catalog, featured)
    return len(catalog["schools"]), len(catalog["majors"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="directory containing catalog.json and featured-content.json",
    )
    parser.add_argument(
        "--fail-on-legacy-duplicate",
        action="store_true",
        help="fail when the local apps/data duplicate directory exists",
    )
    args = parser.parse_args()

    data_dir = args.data_dir.resolve()
    try:
        school_count, major_count = validate_data_directory(data_dir)
    except DataAssetValidationError as exc:
        print(f"Data asset validation failed for {data_dir}:\n{exc}")
        return 1

    legacy_duplicate = REPO_ROOT / "apps" / "data"
    if legacy_duplicate.exists():
        message = (
            "apps/data exists; data/ is the authoritative source and the duplicate "
            "directory is not validated."
        )
        if args.fail_on_legacy_duplicate:
            print(f"Data asset validation failed: {message}")
            return 1
        print(f"WARNING: {message}")
    print(f"Data assets valid: {school_count} schools, {major_count} majors from {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
