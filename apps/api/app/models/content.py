from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    content_versions: Mapped[list["SchoolContentVersion"]] = relationship(
        "SchoolContentVersion",
        back_populates="school",
        cascade="all, delete-orphan",
        order_by="SchoolContentVersion.version",
    )


class SchoolContentVersion(Base):
    __tablename__ = "school_content_versions"
    __table_args__ = (
        UniqueConstraint("school_id", "version", name="uq_school_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    school: Mapped["School"] = relationship("School", back_populates="content_versions")
