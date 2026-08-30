from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..config import settings
from ..models.ingestion import WeChatMessageReceipt


def _build_dedupe_keys(*, message_id: str, nonce: str) -> list[str]:
    keys: list[str] = []
    normalized_message_id = message_id.strip()
    normalized_nonce = nonce.strip()
    if normalized_message_id:
        keys.append(f"msgid:{normalized_message_id}")
    if normalized_nonce:
        keys.append(f"nonce:{normalized_nonce}")
    return keys


def claim_wechat_message(
    session: Session,
    *,
    message_id: str,
    nonce: str,
    received_at: datetime | None = None,
) -> bool:
    """Atomically claim MsgId/nonce keys; False means a verified duplicate."""
    keys = _build_dedupe_keys(message_id=message_id, nonce=nonce)
    if not keys:
        return True

    current_time = received_at or datetime.now(UTC)
    purge_expired_wechat_message_receipts(session, received_at=current_time)

    existing = session.exec(
        select(WeChatMessageReceipt).where(WeChatMessageReceipt.dedupe_key.in_(keys))
    ).first()
    if existing is not None:
        session.rollback()
        return False

    normalized_message_id = message_id.strip()
    normalized_nonce = nonce.strip()
    for key in keys:
        session.add(
            WeChatMessageReceipt(
                dedupe_key=key,
                message_id=normalized_message_id,
                nonce=normalized_nonce,
                received_at=current_time,
            )
        )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return False
    return True


def purge_expired_wechat_message_receipts(
    session: Session,
    *,
    received_at: datetime | None = None,
    retention_seconds: int | None = None,
) -> int:
    current_time = received_at or datetime.now(UTC)
    resolved_retention = (
        settings.wechat_signature_ttl_seconds if retention_seconds is None else retention_seconds
    )
    cutoff = current_time - timedelta(seconds=resolved_retention)
    result = session.exec(
        delete(WeChatMessageReceipt).where(WeChatMessageReceipt.received_at < cutoff)
    )
    return int(result.rowcount or 0)
