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
    reviewed_by: Optional[str] = Field(default=None, nullable=True)
    reviewed_at: Optional[datetime] = Field(default=None, nullable=True)
    review_note: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class MediaAnalysisEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str = Field(default="wechat", nullable=False, index=True)
    source: str = Field(default="wechat_official_account", nullable=False, index=True)
    user_id: str = Field(..., nullable=False, index=True)
    message_id: str = Field(default="", nullable=False, index=True)
    media_id: str = Field(default="", nullable=False, index=True)
    media_type: str = Field(default="image", nullable=False, index=True)
    provider: str = Field(default="pending", nullable=False)
    status: str = Field(default="pending", nullable=False, index=True)
    summary: str = Field(default="", nullable=False)
    rendered_reply: str = Field(default="", nullable=False)
    extracted_fields: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    context: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    auto_routed_to_chat: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
