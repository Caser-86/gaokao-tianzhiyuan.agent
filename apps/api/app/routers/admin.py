from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import SQLModel, Session, select

from ..config import settings
from ..db import get_session
from ..models.ingestion import ReviewQueue

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ReviewQueueItemResponse(SQLModel):
    id: int
    entity_type: str
    entity_id: int
    candidate_version: int | None = None
    diff_summary: list[str]
    priority: str
    review_status: str
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    created_at: datetime


class ReviewQueueListResponse(SQLModel):
    items: list[ReviewQueueItemResponse]


class ReviewDecisionRequest(SQLModel):
    reviewed_by: str
    review_note: str | None = None


def serialize_review_queue_item(item: ReviewQueue) -> ReviewQueueItemResponse:
    created_at = item.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return ReviewQueueItemResponse(
        id=item.id,
        entity_type=item.entity_type,
        entity_id=item.entity_id,
        candidate_version=item.candidate_version,
        diff_summary=item.diff_summary,
        priority=item.priority,
        review_status=item.review_status,
        reviewed_by=item.reviewed_by,
        reviewed_at=item.reviewed_at,
        review_note=item.review_note,
        created_at=created_at,
    )


def get_review_queue_item(session: Session, queue_id: int) -> ReviewQueue:
    queue_item = session.get(ReviewQueue, queue_id)
    if queue_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="review queue item not found",
        )
    return queue_item


def finalize_review_queue_item(
    queue_item: ReviewQueue,
    decision: str,
    payload: ReviewDecisionRequest,
) -> ReviewQueue:
    if queue_item.review_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="review queue item is already finalized",
        )

    queue_item.review_status = decision
    queue_item.reviewed_by = payload.reviewed_by
    queue_item.reviewed_at = datetime.now(timezone.utc)
    queue_item.review_note = payload.review_note
    return queue_item


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin authentication required",
        )


@router.get("/review-queue", response_model=ReviewQueueListResponse)
def list_review_queue(
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ReviewQueueListResponse:
    stmt = (
        select(ReviewQueue)
        .where(ReviewQueue.review_status == "pending_review")
        .order_by(ReviewQueue.created_at)
    )
    items = session.exec(stmt).all()
    return ReviewQueueListResponse(
        items=[serialize_review_queue_item(item) for item in items]
    )


@router.post("/review-queue/{queue_id}/approve", response_model=ReviewQueueItemResponse)
def approve_review_queue_item(
    queue_id: int,
    payload: ReviewDecisionRequest,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ReviewQueueItemResponse:
    queue_item = get_review_queue_item(session, queue_id)
    queue_item = finalize_review_queue_item(queue_item, "approved", payload)
    session.add(queue_item)
    session.commit()
    session.refresh(queue_item)
    return serialize_review_queue_item(queue_item)


@router.post("/review-queue/{queue_id}/reject", response_model=ReviewQueueItemResponse)
def reject_review_queue_item(
    queue_id: int,
    payload: ReviewDecisionRequest,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ReviewQueueItemResponse:
    queue_item = get_review_queue_item(session, queue_id)
    queue_item = finalize_review_queue_item(queue_item, "rejected", payload)
    session.add(queue_item)
    session.commit()
    session.refresh(queue_item)
    return serialize_review_queue_item(queue_item)
