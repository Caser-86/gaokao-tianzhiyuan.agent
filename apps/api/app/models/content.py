from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped
from sqlmodel import Field, SQLModel


class VersionStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class School(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., nullable=False)
    slug: str = Field(..., nullable=False, unique=True, index=True)


class SchoolContentVersion(SQLModel, table=True):
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

    id: Optional[int] = Field(default=None, primary_key=True)
    school_id: int = Field(foreign_key="school.id", nullable=False, index=True)
    version: int = Field(..., nullable=False)
    summary: str = Field(..., nullable=False)
    status: VersionStatus = Field(
        default=VersionStatus.draft, nullable=False, index=True
    )
    published_at: Optional[datetime] = Field(default=None, nullable=True)
    published_by: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
