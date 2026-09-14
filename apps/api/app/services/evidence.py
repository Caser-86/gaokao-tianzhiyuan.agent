"""Build small, provenance-aware evidence packages from the catalog database."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from sqlmodel import Session, select

from ..db import get_engine
from ..models.catalog import (
    Major,
    MajorRankingReference,
    School,
    SchoolRankingReference,
)
from .data_provenance import get_data_provenance
from .url_safety import UnsafeExternalUrlError, validate_external_url

EntityType = Literal["school", "major"]

DEFAULT_MAX_ITEMS = 20
DEFAULT_MAX_CHARS = 12_000
MAX_ALLOWED_ITEMS = 100
MAX_ALLOWED_CHARS = 50_000


class UnknownEvidenceEntityError(LookupError):
    """Raised when a requested school or major is not in the catalog."""


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """A bounded, model-ready fact with enough provenance to audit it."""

    id: str
    source_url: str | None
    source_name: str
    year: int | None
    province: str | None
    text: str
    data_status: str


def serialize_evidence_items(items: Iterable[EvidenceItem]) -> list[dict[str, Any]]:
    """Convert trusted evidence records to a JSON-safe internal payload."""

    return [
        {
            "id": item.id,
            "source_url": item.source_url,
            "source_name": item.source_name,
            "year": item.year,
            "province": item.province,
            "text": item.text,
            "data_status": item.data_status,
        }
        for item in items
    ]


def _optional_http_url(value: object) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if not isinstance(value, str):
        return None
    try:
        return validate_external_url(value)
    except UnsafeExternalUrlError:
        return None


def _normalise_limit(value: int, *, maximum: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    if value > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return value


def _normalise_year(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("year must be a positive integer")
    return value


def _section_items(sections: object) -> Iterable[tuple[int, int, str, str]]:
    if not isinstance(sections, list):
        return
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        title = str(section.get("title", "")).strip()
        raw_items = section.get("items", [])
        if not isinstance(raw_items, list):
            continue
        for item_index, item in enumerate(raw_items):
            if isinstance(item, str) and item.strip():
                yield section_index, item_index, title, item.strip()


def _entity_matches_keyword(entity: School | Major, keyword: str | None) -> bool:
    if not keyword:
        return True
    if isinstance(entity, School):
        fields: list[str] = [
            entity.slug,
            entity.name,
            entity.region,
            entity.city,
            entity.summary,
            *list(entity.tags or []),
        ]
    else:
        fields = [
            entity.slug,
            entity.name,
            entity.discipline,
            entity.summary,
            *list(entity.recommended_regions or []),
        ]
    fields.extend(text for _, _, title, text in _section_items(entity.sections))
    return keyword.casefold() in " ".join(fields).casefold()


def _provenance_is_stale(
    provenance: dict[str, Any], *, as_of: date | None, max_age_days: int | None
) -> bool:
    if max_age_days is None:
        return False
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or max_age_days < 0:
        raise ValueError("max_age_days must be a non-negative integer")
    updated_at = provenance.get("updated_at")
    try:
        updated_date = date.fromisoformat(str(updated_at))
    except ValueError:
        return True
    reference_date = as_of or date.today()
    age_days = max(0, (reference_date - updated_date).days)
    return age_days > max_age_days


def _base_item(
    *,
    item_id: str,
    text: str,
    provenance: dict[str, Any],
    source_url: str | None = None,
    source_name: str | None = None,
    year: int | None = None,
    province: str | None = None,
) -> EvidenceItem | None:
    clean_text = text.strip()
    clean_source_name = (source_name or str(provenance.get("source_name", ""))).strip()
    if not clean_text or not clean_source_name:
        return None
    status = str(provenance.get("status", "demo"))
    if status not in {"demo", "secondary", "official"}:
        status = "demo"
    return EvidenceItem(
        id=item_id,
        source_url=source_url,
        source_name=clean_source_name,
        year=year,
        province=province,
        text=clean_text,
        data_status=status,
    )


def _content_items(
    entity: School | Major, *, entity_type: EntityType, provenance: dict[str, Any]
) -> Iterable[EvidenceItem]:
    province = entity.region if isinstance(entity, School) else None
    summary = _base_item(
        item_id=f"{entity_type}:{entity.slug}:summary",
        text=f"{entity.name}：{entity.summary}",
        provenance=provenance,
        source_url=_optional_http_url(provenance.get("source_url")),
        year=provenance.get("applicable_year"),
        province=province,
    )
    if summary is not None:
        yield summary

    for section_index, item_index, title, text in _section_items(entity.sections):
        section_label = f"{title}：" if title else ""
        item = _base_item(
            item_id=f"{entity_type}:{entity.slug}:section:{section_index}:{item_index}",
            text=f"{entity.name}｜{section_label}{text}",
            provenance=provenance,
            source_url=_optional_http_url(provenance.get("source_url")),
            year=provenance.get("applicable_year"),
            province=province,
        )
        if item is not None:
            yield item


def _ranking_items(
    entity: School | Major,
    references: Iterable[SchoolRankingReference | MajorRankingReference],
    *,
    entity_type: EntityType,
    provenance: dict[str, Any],
    year: int | None,
) -> Iterable[EvidenceItem]:
    province = entity.region if isinstance(entity, School) else None
    for reference in references:
        if year is not None and reference.year != year:
            continue
        source_name = reference.source.strip()
        if not source_name:
            continue
        raw_url = reference.url.strip()
        source_url = _optional_http_url(raw_url)
        if raw_url and source_url is None:
            # An invalid URL cannot be presented as a citable source.
            continue
        note = f"；{reference.note.strip()}" if reference.note.strip() else ""
        item = _base_item(
            item_id=f"{entity_type}:{entity.slug}:ranking:{reference.id}",
            text=f"{entity.name}：{reference.label.strip()}{note}",
            provenance=provenance,
            source_url=source_url,
            source_name=source_name,
            year=reference.year,
            province=province,
        )
        if item is not None:
            yield item


def _load_entities(
    session: Session, *, entity_type: EntityType | None, entity_slug: str | None
) -> list[tuple[EntityType, School | Major]]:
    if entity_type == "school":
        schools = list(session.exec(select(School).order_by(School.id)).all())
        entities: list[tuple[EntityType, School | Major]] = [("school", item) for item in schools]
    elif entity_type == "major":
        majors = list(session.exec(select(Major).order_by(Major.id)).all())
        entities = [("major", item) for item in majors]
    elif entity_type is None:
        schools = list(session.exec(select(School).order_by(School.id)).all())
        majors = list(session.exec(select(Major).order_by(Major.id)).all())
        entities = [("school", item) for item in schools] + [("major", item) for item in majors]
    else:
        raise ValueError("entity_type must be 'school' or 'major'")

    if entity_slug is None:
        return entities
    normalized_selector = entity_slug.strip()
    selected = [
        (kind, entity)
        for kind, entity in entities
        if entity.slug == normalized_selector or entity.name == normalized_selector
    ]
    if not selected:
        label = entity_type or "entity"
        raise UnknownEvidenceEntityError(f"unknown {label}: {entity_slug}")
    return selected


def build_evidence_package(
    *,
    entity_type: EntityType | None = None,
    entity_slug: str | None = None,
    province: str | None = None,
    year: int | None = None,
    keyword: str | None = None,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_chars: int = DEFAULT_MAX_CHARS,
    as_of: date | None = None,
    max_age_days: int | None = None,
    session_factory: Callable[[], Session] | None = None,
) -> list[EvidenceItem]:
    """Return complete, bounded evidence items selected with SQL-backed filters.

    Content without a known applicable year is included only when ``year`` is
    omitted. A year-specific request therefore never silently falls back to an
    older record. Items larger than the remaining character budget are skipped
    rather than truncated, so a partial sentence cannot be mistaken for a fact.
    """

    max_items = _normalise_limit(max_items, maximum=MAX_ALLOWED_ITEMS, name="max_items")
    max_chars = _normalise_limit(max_chars, maximum=MAX_ALLOWED_CHARS, name="max_chars")
    year = _normalise_year(year)
    normalized_province = province.strip() if isinstance(province, str) else province
    normalized_keyword = keyword.strip() if isinstance(keyword, str) else keyword
    provenance = get_data_provenance()
    if _provenance_is_stale(provenance, as_of=as_of, max_age_days=max_age_days):
        return []

    factory = session_factory or (lambda: Session(get_engine()))
    with factory() as session:
        entities = _load_entities(session, entity_type=entity_type, entity_slug=entity_slug)
        output: list[EvidenceItem] = []
        used_chars = 0
        for kind, entity in entities:
            if not _entity_matches_keyword(entity, normalized_keyword):
                continue
            if isinstance(entity, School):
                if normalized_province and entity.region != normalized_province:
                    continue
                references = session.exec(
                    select(SchoolRankingReference)
                    .where(SchoolRankingReference.school_id == entity.id)
                    .order_by(SchoolRankingReference.id)
                ).all()
            else:
                if normalized_province and normalized_province not in list(
                    entity.recommended_regions or []
                ):
                    continue
                references = session.exec(
                    select(MajorRankingReference)
                    .where(MajorRankingReference.major_id == entity.id)
                    .order_by(MajorRankingReference.id)
                ).all()

            candidates: Iterable[EvidenceItem]
            if year is None:
                candidates = _content_items(entity, entity_type=kind, provenance=provenance)
            else:
                candidates = ()
            for candidate in candidates:
                if len(output) >= max_items:
                    return output
                if used_chars + len(candidate.text) > max_chars:
                    continue
                output.append(candidate)
                used_chars += len(candidate.text)

            for candidate in _ranking_items(
                entity,
                references,
                entity_type=kind,
                provenance=provenance,
                year=year,
            ):
                if len(output) >= max_items:
                    return output
                if used_chars + len(candidate.text) > max_chars:
                    continue
                output.append(candidate)
                used_chars += len(candidate.text)

        return output


def build_evidence_package_for_message(
    message: str,
    *,
    province: str | None = None,
    year: int | None = None,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_chars: int = DEFAULT_MAX_CHARS,
    as_of: date | None = None,
    max_age_days: int | None = None,
    session_factory: Callable[[], Session] | None = None,
) -> list[EvidenceItem]:
    """Select evidence only for catalog entities explicitly named by a message.

    Natural-language retrieval is intentionally conservative here: an entity
    must be present by its catalog name or slug before its SQL-backed evidence
    can enter the model context. This keeps a no-match question evidence-free
    instead of filling the prompt with unrelated catalog rows.
    """

    normalized_message = message.strip()
    if not normalized_message:
        return []

    max_items = _normalise_limit(max_items, maximum=MAX_ALLOWED_ITEMS, name="max_items")
    max_chars = _normalise_limit(max_chars, maximum=MAX_ALLOWED_CHARS, name="max_chars")
    factory = session_factory or (lambda: Session(get_engine()))
    with factory() as session:
        matches = [
            (kind, entity.slug)
            for kind, entity in _load_entities(session, entity_type=None, entity_slug=None)
            if entity.name in normalized_message or entity.slug in normalized_message
        ]

    output: list[EvidenceItem] = []
    used_chars = 0
    for entity_type, entity_slug in matches:
        if len(output) >= max_items or used_chars >= max_chars:
            break
        package = build_evidence_package(
            entity_type=entity_type,
            entity_slug=entity_slug,
            province=province,
            year=year,
            max_items=max_items - len(output),
            max_chars=max_chars - used_chars,
            as_of=as_of,
            max_age_days=max_age_days,
            session_factory=factory,
        )
        for item in package:
            if item.id in {existing.id for existing in output}:
                continue
            if len(output) >= max_items or used_chars + len(item.text) > max_chars:
                break
            output.append(item)
            used_chars += len(item.text)
    return output
