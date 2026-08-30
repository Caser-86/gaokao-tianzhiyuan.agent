from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from ..config import settings
from ..models.chat import ChatMessage, ChatSession
from ..models.ingestion import MediaAnalysisEvent, WeChatMessageReceipt
from .chat_sessions import ChatSessionStore


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _now(value: datetime | None) -> datetime:
    return _utc(value or datetime.now(UTC))


def purge_expired_media_analysis_events(
    session: Session,
    *,
    now: datetime | None = None,
    retention_days: int | None = None,
    commit: bool = True,
) -> int:
    current_time = _now(now)
    resolved_retention_days = (
        settings.media_analysis_retention_days if retention_days is None else retention_days
    )
    cutoff = current_time - timedelta(days=resolved_retention_days)
    expired = [
        item
        for item in session.exec(select(MediaAnalysisEvent)).all()
        if _utc(item.created_at) < cutoff
    ]
    for item in expired:
        session.delete(item)
    if commit and expired:
        session.commit()
    return len(expired)


def purge_expired_data(
    session: Session,
    *,
    now: datetime | None = None,
    chat_session_retention_days: int | None = None,
    media_analysis_retention_days: int | None = None,
    wechat_receipt_retention_seconds: int | None = None,
) -> dict[str, int]:
    """Delete expired SQLite records in one transaction.

    This is intentionally explicit and small so it can run at API startup in
    deployments without a scheduler. Request paths still perform local cleanup
    for the high-volume session, media, and receipt tables.
    """

    current_time = _now(now)
    session_cutoff = current_time - timedelta(
        days=(
            settings.chat_session_retention_days
            if chat_session_retention_days is None
            else chat_session_retention_days
        )
    )
    receipt_cutoff = current_time - timedelta(
        seconds=(
            settings.wechat_signature_ttl_seconds
            if wechat_receipt_retention_seconds is None
            else wechat_receipt_retention_seconds
        )
    )

    deleted = {
        "chat_sessions": 0,
        "chat_messages": 0,
        "media_analysis_events": 0,
        "wechat_message_receipts": 0,
    }

    expired_sessions = [
        item
        for item in session.exec(select(ChatSession)).all()
        if _utc(item.expires_at) <= current_time or _utc(item.created_at) < session_cutoff
    ]
    for item in expired_sessions:
        deleted["chat_messages"] += len(
            session.exec(select(ChatMessage).where(ChatMessage.session_id == item.id)).all()
        )
        ChatSessionStore._delete_session_row(session, item)
    deleted["chat_sessions"] = len(expired_sessions)

    expired_media = [
        item
        for item in session.exec(select(MediaAnalysisEvent)).all()
        if _utc(item.created_at)
        < current_time
        - timedelta(
            days=(
                settings.media_analysis_retention_days
                if media_analysis_retention_days is None
                else media_analysis_retention_days
            )
        )
    ]
    for item in expired_media:
        session.delete(item)
    deleted["media_analysis_events"] = len(expired_media)

    expired_receipts = [
        item
        for item in session.exec(select(WeChatMessageReceipt)).all()
        if _utc(item.received_at) < receipt_cutoff
    ]
    for item in expired_receipts:
        session.delete(item)
    deleted["wechat_message_receipts"] = len(expired_receipts)

    if any(deleted.values()):
        session.commit()
    return deleted


def delete_user_data(session: Session, *, user_id: str) -> dict[str, int]:
    """Delete data owned by one authenticated subject; make it idempotent."""

    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id must not be empty")

    sessions = list(
        session.exec(select(ChatSession).where(ChatSession.user_id == normalized_user_id)).all()
    )
    deleted = {
        "chat_sessions": len(sessions),
        "chat_messages": 0,
        "media_analysis_events": 0,
    }
    for stored in sessions:
        deleted["chat_messages"] += len(
            session.exec(select(ChatMessage).where(ChatMessage.session_id == stored.id)).all()
        )
        ChatSessionStore._delete_session_row(session, stored)

    media_events = list(
        session.exec(
            select(MediaAnalysisEvent).where(MediaAnalysisEvent.user_id == normalized_user_id)
        ).all()
    )
    for item in media_events:
        session.delete(item)
    deleted["media_analysis_events"] = len(media_events)
    session.commit()
    return deleted
