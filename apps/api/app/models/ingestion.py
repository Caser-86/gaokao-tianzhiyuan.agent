from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ReviewQueue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(..., nullable=False)
    entity_id: int = Field(..., nullable=False, index=True)
    candidate_version: Optional[int] = Field(default=None, nullable=True)
    diff_summary: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    priority: str = Field(default="normal", nullable=False, index=False)
    review_status: str = Field(default="pending_review", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
