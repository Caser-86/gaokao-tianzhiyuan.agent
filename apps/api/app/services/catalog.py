from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlmodel import Session, select

from ..db import get_engine
from ..models.catalog import (
    Major,
    MajorRankingReference,
    School,
    SchoolMajorRelation,
    SchoolRankingReference,
    SearchEntry,
)
from .featured_content import (
    list_current_featured_majors,
    list_current_featured_schools,
)


def _serialize_school(
    school: School,
    *,
    ranking_references: list[SchoolRankingReference],
    related_major_slugs: list[str],
) -> dict[str, Any]:
    return {
        "slug": school.slug,
        "name": school.name,
        "region": school.region,
        "city": school.city,
        "tags": list(school.tags or []),
        "summary": school.summary,
        "sections": list(school.sections or []),
        "website": school.website,
        "related_majors": related_major_slugs,
        "ranking_references": [
            {
                "source": ref.source,
                "year": ref.year,
                "label": ref.label,
                "scope": ref.scope,
                "note": ref.note,
                "url": ref.url,
            }
            for ref in ranking_references
        ],
    }


def _serialize_major(
    major: Major,
    *,
    ranking_references: list[MajorRankingReference],
    related_school_slugs: list[str],
) -> dict[str, Any]:
    return {
        "slug": major.slug,
        "name": major.name,
        "discipline": major.discipline,
        "recommended_regions": list(major.recommended_regions or []),
        "summary": major.summary,
        "sections": list(major.sections or []),
        "related_schools": related_school_slugs,
        "ranking_references": [
            {
                "source": ref.source,
                "year": ref.year,
                "label": ref.label,
                "scope": ref.scope,
                "note": ref.note,
                "url": ref.url,
            }
            for ref in ranking_references
        ],
    }


def _build_catalog_dict(session: Session) -> dict[str, Any]:
    """从数据库构建与原 catalog.json 结构兼容的字典。"""
    search_entry = session.exec(select(SearchEntry)).first()
    if search_entry is None:
        search_entry_data = {
            "title": "高考志愿助手",
            "description": "",
            "quick_prompts": [],
        }
    else:
        search_entry_data = {
            "title": search_entry.title,
            "description": search_entry.description,
            "quick_prompts": list(search_entry.quick_prompts or []),
        }

    schools = session.exec(select(School)).all()
    majors = session.exec(select(Major)).all()

    school_ranking_refs: dict[int, list[SchoolRankingReference]] = {}
    for ref in session.exec(select(SchoolRankingReference)).all():
        school_ranking_refs.setdefault(ref.school_id, []).append(ref)

    major_ranking_refs: dict[int, list[MajorRankingReference]] = {}
    for ref in session.exec(select(MajorRankingReference)).all():
        major_ranking_refs.setdefault(ref.major_id, []).append(ref)

    school_major_relations = session.exec(select(SchoolMajorRelation)).all()
    school_to_majors: dict[int, list[int]] = {}
    major_to_schools: dict[int, list[int]] = {}
    for relation in school_major_relations:
        school_to_majors.setdefault(relation.school_id, []).append(relation.major_id)
        major_to_schools.setdefault(relation.major_id, []).append(relation.school_id)

    major_id_to_slug = {major.id: major.slug for major in majors}
    school_id_to_slug = {school.id: school.slug for school in schools}

    schools_data = []
    for school in schools:
        related_major_ids = school_to_majors.get(school.id, [])
        related_major_slugs = [
            major_id_to_slug[mid] for mid in related_major_ids if mid in major_id_to_slug
        ]
        schools_data.append(
            _serialize_school(
                school,
                ranking_references=school_ranking_refs.get(school.id, []),
                related_major_slugs=related_major_slugs,
            )
        )

    majors_data = []
    for major in majors:
        related_school_ids = major_to_schools.get(major.id, [])
        related_school_slugs = [
            school_id_to_slug[sid] for sid in related_school_ids if sid in school_id_to_slug
        ]
        majors_data.append(
            _serialize_major(
                major,
                ranking_references=major_ranking_refs.get(major.id, []),
                related_school_slugs=related_school_slugs,
            )
        )

    return {
        "search_entry": search_entry_data,
        "schools": schools_data,
        "majors": majors_data,
    }


def load_catalog(session_factory: Callable[[], Session] | None = None) -> dict[str, Any]:
    """加载目录数据，返回与原 catalog.json 结构兼容的字典。

    数据来源已从 JSON 文件迁移到数据库。
    """
    factory = session_factory or (lambda: Session(get_engine()))
    with factory() as session:
        return _build_catalog_dict(session)


def get_search_entry() -> dict[str, Any]:
    return load_catalog()["search_entry"]


def list_schools(*, region: str | None = None, keyword: str | None = None) -> dict[str, Any]:
    schools = load_catalog()["schools"]
    featured_schools = {school["slug"]: school for school in list_current_featured_schools()}
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
    featured_majors = {major["slug"] for major in list_current_featured_majors()}
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


def get_school_website(slug: str) -> str | None:
    school = get_school_detail(slug)
    if school is None:
        raise KeyError(slug)

    for key in ("website", "official_website", "source_url"):
        value = school.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


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
    with Session(get_engine()) as session:
        if entity_key == "schools":
            entity = session.exec(select(School).where(School.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)
            # 删除旧榜单
            old_refs = session.exec(
                select(SchoolRankingReference).where(SchoolRankingReference.school_id == entity.id)
            ).all()
            for ref in old_refs:
                session.delete(ref)
            # 写入新榜单
            for ref in ranking_references:
                session.add(
                    SchoolRankingReference(
                        school_id=entity.id,
                        source=ref["source"],
                        year=ref["year"],
                        label=ref["label"],
                        scope=ref.get("scope", ""),
                        note=ref.get("note", ""),
                        url=ref.get("url", ""),
                    )
                )
            session.commit()
            name = entity.name
        else:
            entity = session.exec(select(Major).where(Major.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)
            old_refs = session.exec(
                select(MajorRankingReference).where(MajorRankingReference.major_id == entity.id)
            ).all()
            for ref in old_refs:
                session.delete(ref)
            for ref in ranking_references:
                session.add(
                    MajorRankingReference(
                        major_id=entity.id,
                        source=ref["source"],
                        year=ref["year"],
                        label=ref["label"],
                        scope=ref.get("scope", ""),
                        note=ref.get("note", ""),
                        url=ref.get("url", ""),
                    )
                )
            session.commit()
            name = entity.name

    return {
        "slug": slug,
        "name": name,
        "ranking_references": ranking_references,
    }


def update_content_summary(
    entity_key: str,
    slug: str,
    summary: str,
) -> dict[str, Any]:
    normalized_summary = summary.strip()
    if not normalized_summary:
        raise ValueError("summary is required")

    with Session(get_engine()) as session:
        if entity_key == "schools":
            entity = session.exec(select(School).where(School.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)
            entity.summary = normalized_summary
            session.add(entity)
            session.commit()
            name = entity.name
        else:
            entity = session.exec(select(Major).where(Major.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)
            entity.summary = normalized_summary
            session.add(entity)
            session.commit()
            name = entity.name

    return {
        "slug": slug,
        "name": name,
        "summary": normalized_summary,
    }


def update_content_sections(
    entity_key: str,
    slug: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    with Session(get_engine()) as session:
        if entity_key == "schools":
            entity = session.exec(select(School).where(School.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)
            entity.sections = sections
            session.add(entity)
            session.commit()
            name = entity.name
        else:
            entity = session.exec(select(Major).where(Major.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)
            entity.sections = sections
            session.add(entity)
            session.commit()
            name = entity.name

    return {
        "slug": slug,
        "name": name,
        "sections": sections,
    }


def update_related_content(
    entity_key: str,
    slug: str,
    related_field: str,
    related_slugs: list[str],
) -> dict[str, Any]:
    with Session(get_engine()) as session:
        if entity_key == "schools":
            entity = session.exec(select(School).where(School.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)

            related_entities = session.exec(select(Major)).all()
            valid_related_slugs = {m.slug for m in related_entities}
            invalid_slugs = [s for s in related_slugs if s not in valid_related_slugs]
            if invalid_slugs:
                raise ValueError("related content slug is invalid")

            # 删除旧关联
            old_relations = session.exec(
                select(SchoolMajorRelation).where(SchoolMajorRelation.school_id == entity.id)
            ).all()
            for relation in old_relations:
                session.delete(relation)
            session.flush()

            # 写入新关联
            major_slug_to_id = {m.slug: m.id for m in related_entities}
            for related_slug in related_slugs:
                major_id = major_slug_to_id.get(related_slug)
                if major_id is not None:
                    session.add(SchoolMajorRelation(school_id=entity.id, major_id=major_id))

            session.commit()
            name = entity.name
        else:
            entity = session.exec(select(Major).where(Major.slug == slug)).first()
            if entity is None:
                raise KeyError(slug)

            related_entities = session.exec(select(School)).all()
            valid_related_slugs = {s.slug for s in related_entities}
            invalid_slugs = [s for s in related_slugs if s not in valid_related_slugs]
            if invalid_slugs:
                raise ValueError("related content slug is invalid")

            # 删除旧关联
            old_relations = session.exec(
                select(SchoolMajorRelation).where(SchoolMajorRelation.major_id == entity.id)
            ).all()
            for relation in old_relations:
                session.delete(relation)
            session.flush()

            # 写入新关联
            school_slug_to_id = {s.slug: s.id for s in related_entities}
            for related_slug in related_slugs:
                school_id = school_slug_to_id.get(related_slug)
                if school_id is not None:
                    session.add(SchoolMajorRelation(school_id=school_id, major_id=entity.id))

            session.commit()
            name = entity.name

    return {
        "slug": slug,
        "name": name,
        related_field: related_slugs,
    }
