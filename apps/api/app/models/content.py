from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel


class VersionStatus(StrEnum):
    draft = "draft"
    published = "published"
    archived = "archived"


class SchoolContentVersion(SQLModel, table=True):
    """学校内容版本表，用于发布流程管理。

    注意：School 主表已迁移到 app.models.catalog.School，
    本表通过 school_id 外键引用 school.id。
    """

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "version",
            name="uq_school_content_versions_school_id_version",
        ),
        Index(
            "uq_school_content_versions_one_published_per_school",
            "school_id",
            unique=True,
            sqlite_where=text("status = 'published'"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    school_id: int = Field(foreign_key="school.id", nullable=False, index=True)
    version: int = Field(..., nullable=False)
    summary: str = Field(..., nullable=False)
    status: VersionStatus = Field(default=VersionStatus.draft, nullable=False, index=True)
    published_at: datetime | None = Field(default=None, nullable=True)
    published_by: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
