from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str = Field(nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class UserEntitlement(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "entitlement",
            name="uq_user_entitlements_user_id_entitlement",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(nullable=False, index=True)
    entitlement: str = Field(nullable=False, index=True)
    is_enabled: bool = Field(default=True, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
