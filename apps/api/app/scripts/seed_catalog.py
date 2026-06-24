"""从 catalog.json 和 featured-content.json 导入种子数据到数据库。

使用方式：
    python -m app.scripts.seed_catalog

脚本会：
1. 读取 data/catalog.json 和 data/featured-content.json
2. 将学校、专业、榜单参考、关联关系、精选内容、轮播规则写入数据库
3. 已存在的数据会被更新（基于 slug 或唯一约束）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from ..db import create_all_models, get_engine
from ..models.catalog import (
    FeaturedMajor,
    FeaturedRotationRule,
    FeaturedSchool,
    Major,
    MajorRankingReference,
    School,
    SchoolMajorRelation,
    SchoolRankingReference,
    SearchEntry,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
CATALOG_PATH = DATA_DIR / "catalog.json"
FEATURED_CONTENT_PATH = DATA_DIR / "featured-content.json"

DEFAULT_ROTATION_RULES = {
    "schools": {
        "enabled": False,
        "frequency_days": 1,
        "window_size": 1,
        "ordered_slugs": [],
    },
    "majors": {
        "enabled": False,
        "frequency_days": 1,
        "window_size": 1,
        "ordered_slugs": [],
    },
}


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_featured_content() -> dict[str, Any]:
    if not FEATURED_CONTENT_PATH.exists():
        return {"schools": [], "majors": [], "rotation": DEFAULT_ROTATION_RULES}
    payload = json.loads(FEATURED_CONTENT_PATH.read_text(encoding="utf-8"))
    payload.setdefault("schools", [])
    payload.setdefault("majors", [])
    payload.setdefault("rotation", DEFAULT_ROTATION_RULES)
    return payload


def upsert_search_entry(session: Session, catalog: dict[str, Any]) -> None:
    search_entry_data = catalog.get("search_entry", {})
    existing = session.exec(select(SearchEntry)).first()
    if existing is None:
        session.add(
            SearchEntry(
                title=search_entry_data.get("title", "高考志愿助手"),
                description=search_entry_data.get("description", ""),
                quick_prompts=search_entry_data.get("quick_prompts", []),
            )
        )
    else:
        existing.title = search_entry_data.get("title", existing.title)
        existing.description = search_entry_data.get("description", existing.description)
        existing.quick_prompts = search_entry_data.get("quick_prompts", existing.quick_prompts)
        session.add(existing)


def upsert_school(session: Session, school_data: dict[str, Any]) -> School:
    slug = school_data["slug"]
    existing = session.exec(select(School).where(School.slug == slug)).first()
    if existing is None:
        school = School(
            slug=slug,
            name=school_data["name"],
            region=school_data["region"],
            city=school_data["city"],
            tags=school_data.get("tags", []),
            summary=school_data.get("summary", ""),
            sections=school_data.get("sections", []),
            website=school_data.get("website", "")
            or school_data.get("official_website", "")
            or school_data.get("source_url", ""),
        )
        session.add(school)
        session.flush()
        return school

    existing.name = school_data["name"]
    existing.region = school_data["region"]
    existing.city = school_data["city"]
    existing.tags = school_data.get("tags", existing.tags)
    existing.summary = school_data.get("summary", existing.summary)
    existing.sections = school_data.get("sections", existing.sections)
    existing.website = (
        school_data.get("website", "")
        or school_data.get("official_website", "")
        or school_data.get("source_url", "")
        or existing.website
    )
    session.add(existing)
    session.flush()
    return existing


def upsert_major(session: Session, major_data: dict[str, Any]) -> Major:
    slug = major_data["slug"]
    existing = session.exec(select(Major).where(Major.slug == slug)).first()
    if existing is None:
        major = Major(
            slug=slug,
            name=major_data["name"],
            discipline=major_data["discipline"],
            recommended_regions=major_data.get("recommended_regions", []),
            summary=major_data.get("summary", ""),
            sections=major_data.get("sections", []),
        )
        session.add(major)
        session.flush()
        return major

    existing.name = major_data["name"]
    existing.discipline = major_data["discipline"]
    existing.recommended_regions = major_data.get(
        "recommended_regions", existing.recommended_regions
    )
    existing.summary = major_data.get("summary", existing.summary)
    existing.sections = major_data.get("sections", existing.sections)
    session.add(existing)
    session.flush()
    return existing


def sync_school_ranking_references(
    session: Session, school: School, references: list[dict[str, Any]]
) -> None:
    existing_refs = session.exec(
        select(SchoolRankingReference).where(SchoolRankingReference.school_id == school.id)
    ).all()
    for ref in existing_refs:
        session.delete(ref)

    for ref in references:
        session.add(
            SchoolRankingReference(
                school_id=school.id,
                source=ref["source"],
                year=ref["year"],
                label=ref["label"],
                scope=ref.get("scope", ""),
                note=ref.get("note", ""),
                url=ref.get("url", ""),
            )
        )


def sync_major_ranking_references(
    session: Session, major: Major, references: list[dict[str, Any]]
) -> None:
    existing_refs = session.exec(
        select(MajorRankingReference).where(MajorRankingReference.major_id == major.id)
    ).all()
    for ref in existing_refs:
        session.delete(ref)

    for ref in references:
        session.add(
            MajorRankingReference(
                major_id=major.id,
                source=ref["source"],
                year=ref["year"],
                label=ref["label"],
                scope=ref.get("scope", ""),
                note=ref.get("note", ""),
                url=ref.get("url", ""),
            )
        )


def sync_school_major_relations(
    session: Session,
    school: School,
    related_major_slugs: list[str],
    major_slug_to_id: dict[str, int],
) -> None:
    existing_relations = session.exec(
        select(SchoolMajorRelation).where(SchoolMajorRelation.school_id == school.id)
    ).all()
    for relation in existing_relations:
        session.delete(relation)

    for major_slug in related_major_slugs:
        major_id = major_slug_to_id.get(major_slug)
        if major_id is None:
            continue
        session.add(SchoolMajorRelation(school_id=school.id, major_id=major_id))


def upsert_featured_school(
    session: Session, slug: str, is_featured: bool, hero_image_url: str
) -> None:
    existing = session.exec(select(FeaturedSchool).where(FeaturedSchool.slug == slug)).first()
    if existing is None:
        session.add(
            FeaturedSchool(
                slug=slug,
                is_featured=is_featured,
                hero_image_url=hero_image_url,
            )
        )
    else:
        existing.is_featured = is_featured
        existing.hero_image_url = hero_image_url
        session.add(existing)


def upsert_featured_major(session: Session, slug: str, is_featured: bool) -> None:
    existing = session.exec(select(FeaturedMajor).where(FeaturedMajor.slug == slug)).first()
    if existing is None:
        session.add(FeaturedMajor(slug=slug, is_featured=is_featured))
    else:
        existing.is_featured = is_featured
        session.add(existing)


def upsert_rotation_rule(session: Session, entity_type: str, rule: dict[str, Any]) -> None:
    existing = session.exec(
        select(FeaturedRotationRule).where(FeaturedRotationRule.entity_type == entity_type)
    ).first()
    if existing is None:
        session.add(
            FeaturedRotationRule(
                entity_type=entity_type,
                enabled=rule.get("enabled", False),
                frequency_days=rule.get("frequency_days", 1),
                window_size=rule.get("window_size", 1),
                ordered_slugs=rule.get("ordered_slugs", []),
            )
        )
    else:
        existing.enabled = rule.get("enabled", existing.enabled)
        existing.frequency_days = rule.get("frequency_days", existing.frequency_days)
        existing.window_size = rule.get("window_size", existing.window_size)
        existing.ordered_slugs = rule.get("ordered_slugs", existing.ordered_slugs)
        session.add(existing)


def seed_catalog() -> None:
    """从 JSON 文件导入种子数据到数据库。"""
    catalog = load_catalog()
    featured = load_featured_content()

    create_all_models(get_engine())

    with Session(get_engine()) as session:
        upsert_search_entry(session, catalog)

        school_map: dict[str, School] = {}
        for school_data in catalog.get("schools", []):
            school = upsert_school(session, school_data)
            school_map[school.slug] = school
            sync_school_ranking_references(
                session, school, school_data.get("ranking_references", [])
            )

        major_map: dict[str, Major] = {}
        major_slug_to_id: dict[str, int] = {}
        for major_data in catalog.get("majors", []):
            major = upsert_major(session, major_data)
            major_map[major.slug] = major
            major_slug_to_id[major.slug] = major.id
            sync_major_ranking_references(session, major, major_data.get("ranking_references", []))

        for school_data in catalog.get("schools", []):
            school = school_map.get(school_data["slug"])
            if school is None:
                continue
            sync_school_major_relations(
                session,
                school,
                school_data.get("related_majors", []),
                major_slug_to_id,
            )

        # 合并 majors.related_schools 端的关联（避免重复）
        seen_relations: set[tuple[int, int]] = set()
        for relation in session.exec(select(SchoolMajorRelation)).all():
            seen_relations.add((relation.school_id, relation.major_id))
        school_slug_to_id = {s.slug: s.id for s in school_map.values()}
        for major_data in catalog.get("majors", []):
            major = major_map.get(major_data["slug"])
            if major is None:
                continue
            for school_slug in major_data.get("related_schools", []):
                school_id = school_slug_to_id.get(school_slug)
                if school_id is None:
                    continue
                if (school_id, major.id) not in seen_relations:
                    seen_relations.add((school_id, major.id))
                    session.add(SchoolMajorRelation(school_id=school_id, major_id=major.id))

        for school_config in featured.get("schools", []):
            upsert_featured_school(
                session,
                slug=school_config["slug"],
                is_featured=school_config.get("is_featured", False),
                hero_image_url=school_config.get("hero_image_url", ""),
            )

        for major_config in featured.get("majors", []):
            upsert_featured_major(
                session,
                slug=major_config["slug"],
                is_featured=major_config.get("is_featured", False),
            )

        rotation = featured.get("rotation", DEFAULT_ROTATION_RULES)
        upsert_rotation_rule(
            session, "schools", rotation.get("schools", DEFAULT_ROTATION_RULES["schools"])
        )
        upsert_rotation_rule(
            session, "majors", rotation.get("majors", DEFAULT_ROTATION_RULES["majors"])
        )

        session.commit()

    print(f"种子数据导入完成：{len(school_map)} 所学校，{len(major_map)} 个专业")


if __name__ == "__main__":
    seed_catalog()
