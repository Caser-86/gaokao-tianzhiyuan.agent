"""测试全局配置：提供内存数据库隔离和数据注入辅助函数。"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app import db as db_module
from app.db import get_session
from app.main import app
from app.models.catalog import (
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


@pytest.fixture
def engine():
    """每个测试使用独立的内存 SQLite 数据库。"""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture(autouse=True)
def _override_engine(engine, monkeypatch):
    """让所有服务都使用测试数据库。"""
    monkeypatch.setattr(db_module, "get_engine", lambda *_args, **_kwargs: engine)
    # 同时覆盖 catalog/featured_content 服务模块中已导入的 get_engine 引用
    from app.services import catalog as catalog_service
    from app.services import featured_content as featured_content_service

    monkeypatch.setattr(catalog_service, "get_engine", lambda *_args, **_kwargs: engine)
    monkeypatch.setattr(featured_content_service, "get_engine", lambda *_args, **_kwargs: engine)

    # 覆盖 FastAPI 依赖
    def _override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    yield
    app.dependency_overrides.pop(get_session, None)


def seed_catalog_data(engine, catalog: dict[str, Any]) -> None:
    """将 catalog 字典结构的数据注入测试数据库。"""
    with Session(engine) as session:
        # 清空旧数据
        for model in (
            SchoolRankingReference,
            MajorRankingReference,
            SchoolMajorRelation,
            School,
            Major,
            SearchEntry,
        ):
            for row in session.exec(select(model)).all():
                session.delete(row)
        session.commit()

        # 写入 search entry
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

        # 写入学校
        school_id_map: dict[str, int] = {}
        for school_data in catalog.get("schools", []):
            school = School(
                slug=school_data["slug"],
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
            school_id_map[school.slug] = school.id

            for ref in school_data.get("ranking_references", []):
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

        # 写入专业
        major_id_map: dict[str, int] = {}
        for major_data in catalog.get("majors", []):
            major = Major(
                slug=major_data["slug"],
                name=major_data["name"],
                discipline=major_data["discipline"],
                recommended_regions=major_data.get("recommended_regions", []),
                summary=major_data.get("summary", ""),
                sections=major_data.get("sections", []),
            )
            session.add(major)
            session.flush()
            major_id_map[major.slug] = major.id

            for ref in major_data.get("ranking_references", []):
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

        # 写入学校-专业关联（合并 schools.related_majors 和 majors.related_schools）
        seen_relations: set[tuple[int, int]] = set()
        for school_data in catalog.get("schools", []):
            school_id = school_id_map.get(school_data["slug"])
            if school_id is None:
                continue
            for major_slug in school_data.get("related_majors", []):
                major_id = major_id_map.get(major_slug)
                if major_id is not None and (school_id, major_id) not in seen_relations:
                    seen_relations.add((school_id, major_id))
                    session.add(SchoolMajorRelation(school_id=school_id, major_id=major_id))
        for major_data in catalog.get("majors", []):
            major_id = major_id_map.get(major_data["slug"])
            if major_id is None:
                continue
            for school_slug in major_data.get("related_schools", []):
                school_id = school_id_map.get(school_slug)
                if school_id is not None and (school_id, major_id) not in seen_relations:
                    seen_relations.add((school_id, major_id))
                    session.add(SchoolMajorRelation(school_id=school_id, major_id=major_id))

        session.commit()


def seed_featured_data(engine, featured: dict[str, Any]) -> None:
    """将 featured-content 字典结构的数据注入测试数据库。"""
    with Session(engine) as session:
        # 清空旧数据
        for model in (FeaturedSchool, FeaturedMajor, FeaturedRotationRule):
            for row in session.exec(select(model)).all():
                session.delete(row)
        session.commit()

        for school_config in featured.get("schools", []):
            session.add(
                FeaturedSchool(
                    slug=school_config["slug"],
                    is_featured=school_config.get("is_featured", False),
                    hero_image_url=school_config.get("hero_image_url", ""),
                )
            )

        for major_config in featured.get("majors", []):
            session.add(
                FeaturedMajor(
                    slug=major_config["slug"],
                    is_featured=major_config.get("is_featured", False),
                )
            )

        rotation = featured.get("rotation", {})
        for entity_type in ("schools", "majors"):
            rule = rotation.get(entity_type, {})
            session.add(
                FeaturedRotationRule(
                    entity_type=entity_type,
                    enabled=rule.get("enabled", False),
                    frequency_days=rule.get("frequency_days", 1),
                    window_size=rule.get("window_size", 1),
                    ordered_slugs=rule.get("ordered_slugs", []),
                )
            )

        session.commit()


@pytest.fixture
def seed_catalog(engine):
    """提供注入 catalog 数据的辅助函数。"""

    def _seed(catalog: dict[str, Any]) -> None:
        seed_catalog_data(engine, catalog)

    return _seed


@pytest.fixture
def seed_featured(engine):
    """提供注入 featured 数据的辅助函数。"""

    def _seed(featured: dict[str, Any]) -> None:
        seed_featured_data(engine, featured)

    return _seed
