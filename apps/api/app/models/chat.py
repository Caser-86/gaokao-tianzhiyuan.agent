from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class ChatSession(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("session_id", name="uq_chat_sessions_session_id"),)

    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(nullable=False, index=True)
    user_id: str = Field(nullable=False, index=True)
    channel: str = Field(default="web", nullable=False, index=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
    expires_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", nullable=False, index=True)
    request_id: str = Field(default="", nullable=False, index=True)
    role: str = Field(nullable=False, index=True)
    content_type: str = Field(default="text", nullable=False)
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)
