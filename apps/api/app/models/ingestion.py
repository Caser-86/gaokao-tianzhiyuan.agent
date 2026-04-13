from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ReviewQueue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(..., nullable=False)
    entity_id: int = Field(..., nullable=False, index=True)
    diff_summary: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    has_changes: bool = Field(..., nullable=False)
    status: str = Field(..., nullable=False)
