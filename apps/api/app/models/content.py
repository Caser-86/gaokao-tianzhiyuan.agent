from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

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
    id: Optional[int] = Field(default=None, primary_key=True)
    school_id: int = Field(foreign_key="school.id", nullable=False, index=True)
    summary: str = Field(..., nullable=False)
    status: VersionStatus = Field(
        default=VersionStatus.draft, nullable=False, index=True
    )
    published_at: Optional[datetime] = Field(default=None, nullable=True)
    published_by: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
