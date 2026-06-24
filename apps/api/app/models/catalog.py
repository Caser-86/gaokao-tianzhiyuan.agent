from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class School(SQLModel, table=True):
    """学校主表，替代 catalog.json 中的 schools 数组。"""

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(..., nullable=False, unique=True, index=True)
    name: str = Field(..., nullable=False)
    region: str = Field(..., nullable=False, index=True)
    city: str = Field(..., nullable=False)
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    summary: str = Field(default="", nullable=False)
    sections: list[dict] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    website: str = Field(default="", nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class Major(SQLModel, table=True):
    """专业主表，替代 catalog.json 中的 majors 数组。"""

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(..., nullable=False, unique=True, index=True)
    name: str = Field(..., nullable=False)
    discipline: str = Field(..., nullable=False, index=True)
    recommended_regions: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    summary: str = Field(default="", nullable=False)
    sections: list[dict] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class SchoolRankingReference(SQLModel, table=True):
    """学校榜单参考，1:N 关系，替代 catalog.json 中内嵌的 ranking_references。"""

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "source",
            "year",
            name="uq_school_ranking_references_school_source_year",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    school_id: int = Field(foreign_key="school.id", nullable=False, index=True)
    source: str = Field(..., nullable=False)
    year: int = Field(..., nullable=False)
    label: str = Field(..., nullable=False)
    scope: str = Field(default="", nullable=False)
    note: str = Field(default="", nullable=False)
    url: str = Field(default="", nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class MajorRankingReference(SQLModel, table=True):
    """专业榜单参考，1:N 关系，替代 catalog.json 中内嵌的 ranking_references。"""

    __table_args__ = (
        UniqueConstraint(
            "major_id",
            "source",
            "year",
            name="uq_major_ranking_references_major_source_year",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    major_id: int = Field(foreign_key="major.id", nullable=False, index=True)
    source: str = Field(..., nullable=False)
    year: int = Field(..., nullable=False)
    label: str = Field(..., nullable=False)
    scope: str = Field(default="", nullable=False)
    note: str = Field(default="", nullable=False)
    url: str = Field(default="", nullable=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class SchoolMajorRelation(SQLModel, table=True):
    """学校-专业多对多关联表，替代双向冗余的 related_majors/related_schools。"""

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "major_id",
            name="uq_school_major_relations_school_major",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    school_id: int = Field(foreign_key="school.id", nullable=False, index=True)
    major_id: int = Field(foreign_key="major.id", nullable=False, index=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class FeaturedSchool(SQLModel, table=True):
    """精选学校配置，替代 featured-content.json 中的 schools 数组。"""

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(..., nullable=False, unique=True, index=True)
    is_featured: bool = Field(default=False, nullable=False)
    hero_image_url: str = Field(default="", nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class FeaturedMajor(SQLModel, table=True):
    """精选专业配置，替代 featured-content.json 中的 majors 数组。"""

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(..., nullable=False, unique=True, index=True)
    is_featured: bool = Field(default=False, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class FeaturedRotationRule(SQLModel, table=True):
    """精选内容轮播规则，替代 featured-content.json 中的 rotation 对象。"""

    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            name="uq_featured_rotation_rules_entity_type",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    entity_type: str = Field(..., nullable=False, unique=True)
    enabled: bool = Field(default=False, nullable=False)
    frequency_days: int = Field(default=1, nullable=False)
    window_size: int = Field(default=1, nullable=False)
    ordered_slugs: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class SearchEntry(SQLModel, table=True):
    """搜索入口配置，替代 catalog.json 中的 search_entry 对象。"""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(default="高考志愿助手", nullable=False)
    description: str = Field(default="", nullable=False)
    quick_prompts: list[str] = Field(
        default_factory=lambda: ["查学校", "查专业", "看地域对比"],
        sa_column=Column(JSON, nullable=False),
    )
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
