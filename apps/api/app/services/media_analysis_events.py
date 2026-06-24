from __future__ import annotations

from sqlmodel import Session, select

from ..models.ingestion import MediaAnalysisEvent


def create_media_analysis_event(
    session: Session,
    *,
    channel: str,
    source: str,
    user_id: str,
    message_id: str,
    media_id: str,
    media_type: str,
    provider: str,
    status: str,
    summary: str,
    rendered_reply: str,
    extracted_fields: dict,
    context: dict,
    auto_routed_to_chat: bool,
) -> MediaAnalysisEvent:
    event = MediaAnalysisEvent(
        channel=channel,
        source=source,
        user_id=user_id,
        message_id=message_id,
        media_id=media_id,
        media_type=media_type,
        provider=provider,
        status=status,
        summary=summary,
        rendered_reply=rendered_reply,
        extracted_fields=extracted_fields,
        context=context,
        auto_routed_to_chat=auto_routed_to_chat,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def list_media_analysis_events(
    session: Session,
    *,
    limit: int,
    status: str | None = None,
    user_id: str | None = None,
    auto_routed_to_chat: bool | None = None,
) -> list[MediaAnalysisEvent]:
    stmt = select(MediaAnalysisEvent)

    if status:
        stmt = stmt.where(MediaAnalysisEvent.status == status)
    if user_id:
        stmt = stmt.where(MediaAnalysisEvent.user_id == user_id)
    if auto_routed_to_chat is not None:
        stmt = stmt.where(MediaAnalysisEvent.auto_routed_to_chat == auto_routed_to_chat)

    stmt = stmt.order_by(
        MediaAnalysisEvent.created_at.desc(),
        MediaAnalysisEvent.id.desc(),
    ).limit(limit)
    return list(session.exec(stmt).all())
