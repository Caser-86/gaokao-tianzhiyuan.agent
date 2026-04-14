from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlmodel import SQLModel, Session, select

from ..config import settings
from ..db import get_session
from ..models.ingestion import ReviewQueue
from ..services.featured_content import (
    build_featured_content_preview,
    list_featured_content,
    update_featured_major,
    update_rotation_rule,
    update_featured_school,
)
from ..services.catalog import (
    list_admin_ranking_references,
    update_ranking_references,
)

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


class FeaturedSchoolConfigResponse(SQLModel):
    slug: str
    name: str
    is_featured: bool
    hero_image_url: str = ""


class FeaturedMajorConfigResponse(SQLModel):
    slug: str
    name: str
    is_featured: bool


class FeaturedSchoolConfigRequest(SQLModel):
    is_featured: bool
    hero_image_url: str | None = None


class FeaturedMajorConfigRequest(SQLModel):
    is_featured: bool


class FeaturedRotationRuleRequest(SQLModel):
    enabled: bool
    frequency_days: int
    window_size: int
    ordered_slugs: list[str]


class FeaturedRotationRuleResponse(SQLModel):
    enabled: bool
    frequency_days: int
    window_size: int
    ordered_slugs: list[str]


class FeaturedContentRotationResponse(SQLModel):
    schools: FeaturedRotationRuleResponse
    majors: FeaturedRotationRuleResponse


class FeaturedPreviewItemResponse(SQLModel):
    slug: str
    name: str


class FeaturedPreviewDayResponse(SQLModel):
    date: str
    weekday: str
    schools: list[FeaturedPreviewItemResponse]
    majors: list[FeaturedPreviewItemResponse]


class FeaturedTodayPreviewResponse(SQLModel):
    schools: list[FeaturedPreviewItemResponse]
    majors: list[FeaturedPreviewItemResponse]


class FeaturedContentPreviewResponse(SQLModel):
    today: FeaturedTodayPreviewResponse
    next: FeaturedTodayPreviewResponse
    schedule: list[FeaturedPreviewDayResponse]
    selected_date: FeaturedPreviewDayResponse | None = None
    selected_date_error: str | None = None


class FeaturedContentResponse(SQLModel):
    schools: list[FeaturedSchoolConfigResponse]
    majors: list[FeaturedMajorConfigResponse]
    rotation: FeaturedContentRotationResponse
    preview: FeaturedContentPreviewResponse


class RankingReferenceResponse(SQLModel):
    source: str
    year: int
    label: str
    scope: str = ""
    note: str = ""
    url: str = ""


class RankingReferenceEntityResponse(SQLModel):
    slug: str
    name: str
    ranking_references: list[RankingReferenceResponse]


class RankingReferenceListResponse(SQLModel):
    schools: list[RankingReferenceEntityResponse]
    majors: list[RankingReferenceEntityResponse]


class RankingReferenceRequest(SQLModel):
    source: str
    year: int
    label: str
    scope: str = ""
    note: str = ""
    url: str = ""


class RankingReferenceUpdateRequest(SQLModel):
    ranking_references: list[RankingReferenceRequest]


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


def normalize_ranking_references(
    ranking_references: list[RankingReferenceRequest],
) -> list[dict[str, str | int]]:
    normalized: list[dict[str, str | int]] = []

    for item in ranking_references:
        source = item.source.strip()
        label = item.label.strip()
        if not source or not label:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="ranking reference source and label are required",
            )
        if item.year < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="ranking reference year must be positive",
            )

        normalized.append(
            {
                "source": source,
                "year": item.year,
                "label": label,
                "scope": item.scope.strip(),
                "note": item.note.strip(),
                "url": item.url.strip(),
            }
        )

    return normalized


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


@router.get("/ranking-references", response_model=RankingReferenceListResponse)
def get_ranking_references(
    _authorized: None = Depends(require_admin),
) -> RankingReferenceListResponse:
    payload = list_admin_ranking_references()
    return RankingReferenceListResponse(
        schools=[RankingReferenceEntityResponse(**item) for item in payload["schools"]],
        majors=[RankingReferenceEntityResponse(**item) for item in payload["majors"]],
    )


@router.post(
    "/ranking-references/schools/{slug}",
    response_model=RankingReferenceEntityResponse,
)
def update_school_ranking_references(
    slug: str,
    payload: RankingReferenceUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> RankingReferenceEntityResponse:
    try:
        updated = update_ranking_references(
            "schools",
            slug,
            normalize_ranking_references(payload.ranking_references),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ranking reference entity not found",
        ) from exc

    return RankingReferenceEntityResponse(**updated)


@router.post(
    "/ranking-references/majors/{slug}",
    response_model=RankingReferenceEntityResponse,
)
def update_major_ranking_references(
    slug: str,
    payload: RankingReferenceUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> RankingReferenceEntityResponse:
    try:
        updated = update_ranking_references(
            "majors",
            slug,
            normalize_ranking_references(payload.ranking_references),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ranking reference entity not found",
        ) from exc

    return RankingReferenceEntityResponse(**updated)


@router.get("/featured-content", response_model=FeaturedContentResponse)
def get_featured_content(
    preview_date: str | None = Query(default=None),
    _authorized: None = Depends(require_admin),
) -> FeaturedContentResponse:
    payload = list_featured_content()
    selected_preview_date: date | None = None
    selected_date_error: str | None = None

    if preview_date:
        try:
            selected_preview_date = date.fromisoformat(preview_date)
        except ValueError:
            selected_date_error = "预览日期格式无效"

    preview = build_featured_content_preview(preview_date=selected_preview_date)
    return FeaturedContentResponse(
        schools=[
            FeaturedSchoolConfigResponse(**school)
            for school in payload["schools"]
        ],
        majors=[
            FeaturedMajorConfigResponse(**major)
            for major in payload["majors"]
        ],
        rotation=FeaturedContentRotationResponse(
            schools=FeaturedRotationRuleResponse(**payload["rotation"]["schools"]),
            majors=FeaturedRotationRuleResponse(**payload["rotation"]["majors"]),
        ),
        preview=FeaturedContentPreviewResponse(
            today=FeaturedTodayPreviewResponse(
                schools=[
                    FeaturedPreviewItemResponse(**school)
                    for school in preview["today"]["schools"]
                ],
                majors=[
                    FeaturedPreviewItemResponse(**major)
                    for major in preview["today"]["majors"]
                ],
            ),
            next=FeaturedTodayPreviewResponse(
                schools=[
                    FeaturedPreviewItemResponse(**school)
                    for school in preview["next"]["schools"]
                ],
                majors=[
                    FeaturedPreviewItemResponse(**major)
                    for major in preview["next"]["majors"]
                ],
            ),
            schedule=[
                FeaturedPreviewDayResponse(
                    date=day["date"],
                    weekday=day["weekday"],
                    schools=[
                        FeaturedPreviewItemResponse(**school)
                        for school in day["schools"]
                    ],
                    majors=[
                        FeaturedPreviewItemResponse(**major)
                        for major in day["majors"]
                    ],
                )
                for day in preview["schedule"]
            ],
            selected_date=(
                FeaturedPreviewDayResponse(
                    date=preview["selected_date"]["date"],
                    weekday=preview["selected_date"]["weekday"],
                    schools=[
                        FeaturedPreviewItemResponse(**school)
                        for school in preview["selected_date"]["schools"]
                    ],
                    majors=[
                        FeaturedPreviewItemResponse(**major)
                        for major in preview["selected_date"]["majors"]
                    ],
                )
                if preview["selected_date"] is not None
                else None
            ),
            selected_date_error=selected_date_error,
        ),
    )


@router.post(
    "/featured-content/schools/{slug}",
    response_model=FeaturedSchoolConfigResponse,
)
def update_featured_school_config(
    slug: str,
    payload: FeaturedSchoolConfigRequest,
    _authorized: None = Depends(require_admin),
) -> FeaturedSchoolConfigResponse:
    try:
        updated = update_featured_school(
            slug,
            is_featured=payload.is_featured,
            hero_image_url=payload.hero_image_url,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="featured content entity not found",
        ) from exc

    return FeaturedSchoolConfigResponse(**updated)


@router.post(
    "/featured-content/majors/{slug}",
    response_model=FeaturedMajorConfigResponse,
)
def update_featured_major_config(
    slug: str,
    payload: FeaturedMajorConfigRequest,
    _authorized: None = Depends(require_admin),
) -> FeaturedMajorConfigResponse:
    try:
        updated = update_featured_major(
            slug,
            is_featured=payload.is_featured,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="featured content entity not found",
        ) from exc

    return FeaturedMajorConfigResponse(**updated)


@router.post(
    "/featured-content/rotation/schools",
    response_model=FeaturedRotationRuleResponse,
)
def update_school_rotation_rule(
    payload: FeaturedRotationRuleRequest,
    _authorized: None = Depends(require_admin),
) -> FeaturedRotationRuleResponse:
    try:
        updated = update_rotation_rule(
            "schools",
            enabled=payload.enabled,
            frequency_days=payload.frequency_days,
            window_size=payload.window_size,
            ordered_slugs=payload.ordered_slugs,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="featured rotation slug not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return FeaturedRotationRuleResponse(**updated)


@router.post(
    "/featured-content/rotation/majors",
    response_model=FeaturedRotationRuleResponse,
)
def update_major_rotation_rule(
    payload: FeaturedRotationRuleRequest,
    _authorized: None = Depends(require_admin),
) -> FeaturedRotationRuleResponse:
    try:
        updated = update_rotation_rule(
            "majors",
            enabled=payload.enabled,
            frequency_days=payload.frequency_days,
            window_size=payload.window_size,
            ordered_slugs=payload.ordered_slugs,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="featured rotation slug not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return FeaturedRotationRuleResponse(**updated)


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
