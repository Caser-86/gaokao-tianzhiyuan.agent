from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlmodel import SQLModel, Session, select

from ..config import settings
from ..db import get_session
from ..models.ingestion import MediaAnalysisEvent, ReviewQueue
from ..services.access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    get_user_entitlements,
    set_smart_analysis_mode,
    set_user_entitlement,
)
from ..services import featured_content as featured_content_service
from ..services.media_analysis import (
    MediaAnalysisRequest,
    MediaAnalysisResult,
    build_media_analysis_provider,
)
from ..services.media_analysis_events import (
    create_media_analysis_event,
    list_media_analysis_events,
)
from ..services.featured_content import (
    build_featured_content_preview,
    list_featured_content,
    update_featured_major,
    update_rotation_rule,
    update_featured_school,
)
from ..services.catalog import (
    list_admin_content_sections,
    list_admin_related_content,
    list_admin_content_summaries,
    list_admin_ranking_references,
    update_content_sections,
    update_content_summary,
    update_related_content,
    update_ranking_references,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])
media_analysis_provider = build_media_analysis_provider(
    provider=settings.media_analysis_provider,
    base_url=settings.media_analysis_base_url,
    api_key=settings.media_analysis_api_key,
    model=settings.media_analysis_model,
    timeout_seconds=settings.media_analysis_timeout_seconds,
)


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


class MediaAnalysisEventResponse(SQLModel):
    id: int
    channel: str
    source: str
    user_id: str
    message_id: str
    media_id: str
    media_type: str
    provider: str
    status: str
    summary: str
    rendered_reply: str
    extracted_fields: dict
    context: dict
    retryable: bool
    retry_block_reason: str | None
    auto_routed_to_chat: bool
    created_at: datetime


class MediaAnalysisEventListResponse(SQLModel):
    items: list[MediaAnalysisEventResponse]


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


class FeaturedSchoolImageSuggestionResponse(SQLModel):
    slug: str
    name: str
    status: str
    source_url: str | None = None
    suggested_image_url: str | None = None
    message: str | None = None


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


class ContentSummaryEntityResponse(SQLModel):
    slug: str
    name: str
    summary: str


class ContentSummaryListResponse(SQLModel):
    schools: list[ContentSummaryEntityResponse]
    majors: list[ContentSummaryEntityResponse]


class ContentSummaryUpdateRequest(SQLModel):
    summary: str


class ContentSectionResponse(SQLModel):
    type: str
    title: str
    items: list[str]


class ContentSectionEntityResponse(SQLModel):
    slug: str
    name: str
    sections: list[ContentSectionResponse]


class ContentSectionListResponse(SQLModel):
    schools: list[ContentSectionEntityResponse]
    majors: list[ContentSectionEntityResponse]


class ContentSectionRequest(SQLModel):
    type: str
    title: str
    items: list[str]


class ContentSectionUpdateRequest(SQLModel):
    sections: list[ContentSectionRequest]


class RelatedSchoolEntityResponse(SQLModel):
    slug: str
    name: str
    related_majors: list[str]


class RelatedMajorEntityResponse(SQLModel):
    slug: str
    name: str
    related_schools: list[str]


class RelatedContentListResponse(SQLModel):
    schools: list[RelatedSchoolEntityResponse]
    majors: list[RelatedMajorEntityResponse]


class RelatedSchoolUpdateRequest(SQLModel):
    related_majors: list[str]


class RelatedMajorUpdateRequest(SQLModel):
    related_schools: list[str]


class SmartAnalysisSettingsResponse(SQLModel):
    mode: str


class SmartAnalysisSettingsRequest(SQLModel):
    mode: str


class UserEntitlementStatusResponse(SQLModel):
    name: str
    enabled: bool


class SmartAnalysisUserEntitlementsResponse(SQLModel):
    user_id: str
    entitlements: list[UserEntitlementStatusResponse]


class SmartAnalysisUserEntitlementsRequest(SQLModel):
    smart_analysis_enabled: bool


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


def serialize_media_analysis_event(
    item: MediaAnalysisEvent,
) -> MediaAnalysisEventResponse:
    created_at = item.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    retryable, retry_block_reason = get_media_analysis_retryability(item)

    return MediaAnalysisEventResponse(
        id=item.id,
        channel=item.channel,
        source=item.source,
        user_id=item.user_id,
        message_id=item.message_id,
        media_id=item.media_id,
        media_type=item.media_type,
        provider=item.provider,
        status=item.status,
        summary=item.summary,
        rendered_reply=item.rendered_reply,
        extracted_fields=item.extracted_fields,
        context=item.context,
        retryable=retryable,
        retry_block_reason=retry_block_reason,
        auto_routed_to_chat=item.auto_routed_to_chat,
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


def get_media_analysis_event(session: Session, event_id: int) -> MediaAnalysisEvent:
    event = session.get(MediaAnalysisEvent, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="media analysis event not found",
        )
    return event


def get_media_analysis_retryability(
    item: MediaAnalysisEvent,
) -> tuple[bool, str | None]:
    context = item.context or {}
    pic_url = str(context.get("pic_url", "")).strip()

    if item.media_type != "image":
        return False, "非图片媒体记录暂不支持手动重试"

    if not pic_url:
        return False, "图片记录缺少 pic_url，暂不支持手动重试"

    return True, None


def build_media_analysis_retry_payload(
    item: MediaAnalysisEvent,
) -> dict[str, str]:
    context = item.context or {}
    retryable, retry_block_reason = get_media_analysis_retryability(item)
    if not retryable:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=retry_block_reason or "media analysis retry is not available",
        )
    pic_url = str(context.get("pic_url", "")).strip()

    payload = {
        "ToUserName": str(context.get("to_user_name", "")).strip(),
        "FromUserName": str(context.get("from_user_name", "") or item.user_id).strip(),
        "CreateTime": str(context.get("create_time", "")).strip(),
        "MsgType": str(context.get("msg_type", "") or item.media_type).strip(),
        "MsgId": str(context.get("msg_id", "") or item.message_id).strip(),
        "MediaId": str(context.get("media_id", "") or item.media_id).strip(),
        "PicUrl": pic_url,
    }

    thumb_media_id = str(context.get("thumb_media_id", "")).strip()
    if thumb_media_id:
        payload["ThumbMediaId"] = thumb_media_id

    return payload


def retry_media_analysis_event(
    *,
    session: Session,
    item: MediaAnalysisEvent,
) -> MediaAnalysisEvent:
    payload = build_media_analysis_retry_payload(item)
    result: MediaAnalysisResult = media_analysis_provider.analyze(
        request=MediaAnalysisRequest(
            media_type=item.media_type,
            user_id=item.user_id,
            payload=payload,
        )
    )
    retry_context = {
        **(item.context or {}),
        "retried_from_event_id": item.id,
        "retry_trigger": "admin_manual",
    }
    if result.failure_reason:
        retry_context["failure_reason"] = result.failure_reason

    return create_media_analysis_event(
        session,
        channel=item.channel,
        source="admin_media_analysis_retry",
        user_id=item.user_id,
        message_id=item.message_id,
        media_id=item.media_id,
        media_type=item.media_type,
        provider=result.provider,
        status=result.status,
        summary=result.summary or "",
        rendered_reply=result.rendered_reply or "",
        extracted_fields=result.extracted_fields or {},
        context=retry_context,
        auto_routed_to_chat=False,
    )


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


def build_smart_analysis_user_response(
    *,
    user_id: str,
    entitlements: list[str],
) -> SmartAnalysisUserEntitlementsResponse:
    return SmartAnalysisUserEntitlementsResponse(
        user_id=user_id,
        entitlements=[
            UserEntitlementStatusResponse(name=name, enabled=True)
            for name in entitlements
        ],
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


def normalize_content_summary(summary: str) -> str:
    normalized = summary.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="summary is required",
        )
    return normalized


def normalize_content_sections(
    sections: list[ContentSectionRequest],
) -> list[dict[str, str | list[str]]]:
    normalized: list[dict[str, str | list[str]]] = []

    for section in sections:
        type_value = section.type.strip()
        title_value = section.title.strip()
        items = [item.strip() for item in section.items if item.strip()]

        if not type_value and not title_value and not items:
            continue

        if not type_value or not title_value or not items:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="content section row is invalid",
            )

        normalized.append(
            {
                "type": type_value,
                "title": title_value,
                "items": items,
            }
        )

    return normalized


def normalize_related_slugs(related_slugs: list[str]) -> list[str]:
    normalized = [slug.strip() for slug in related_slugs if slug.strip()]
    if any(not slug for slug in normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="related content slug is invalid",
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


@router.get(
    "/media-analysis-events",
    response_model=MediaAnalysisEventListResponse,
)
def get_media_analysis_events(
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    auto_routed_to_chat: bool | None = Query(default=None),
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> MediaAnalysisEventListResponse:
    items = list_media_analysis_events(
        session,
        limit=limit,
        status=status.strip() if status else None,
        user_id=user_id.strip() if user_id else None,
        auto_routed_to_chat=auto_routed_to_chat,
    )
    return MediaAnalysisEventListResponse(
        items=[serialize_media_analysis_event(item) for item in items]
    )


@router.post(
    "/media-analysis-events/{event_id}/retry",
    response_model=MediaAnalysisEventResponse,
)
def retry_media_analysis_event_endpoint(
    event_id: int,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> MediaAnalysisEventResponse:
    item = get_media_analysis_event(session, event_id)
    retried = retry_media_analysis_event(session=session, item=item)
    return serialize_media_analysis_event(retried)


@router.get("/smart-analysis/settings", response_model=SmartAnalysisSettingsResponse)
def get_smart_analysis_settings(
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SmartAnalysisSettingsResponse:
    return SmartAnalysisSettingsResponse(
        mode=get_effective_smart_analysis_mode(
            session,
            default_mode=settings.smart_analysis_mode,
        )
    )


@router.put("/smart-analysis/settings", response_model=SmartAnalysisSettingsResponse)
def update_smart_analysis_settings(
    payload: SmartAnalysisSettingsRequest,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SmartAnalysisSettingsResponse:
    try:
        mode = set_smart_analysis_mode(session, payload.mode)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return SmartAnalysisSettingsResponse(mode=mode)


@router.get(
    "/smart-analysis/users/{user_id}",
    response_model=SmartAnalysisUserEntitlementsResponse,
)
def get_smart_analysis_user_entitlements(
    user_id: str,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SmartAnalysisUserEntitlementsResponse:
    entitlements = get_user_entitlements(session, user_id)
    return build_smart_analysis_user_response(
        user_id=user_id,
        entitlements=entitlements,
    )


@router.put(
    "/smart-analysis/users/{user_id}",
    response_model=SmartAnalysisUserEntitlementsResponse,
)
def update_smart_analysis_user_entitlements(
    user_id: str,
    payload: SmartAnalysisUserEntitlementsRequest,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SmartAnalysisUserEntitlementsResponse:
    try:
        set_user_entitlement(
            session,
            user_id=user_id,
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=payload.smart_analysis_enabled,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    entitlements = get_user_entitlements(session, user_id)
    return build_smart_analysis_user_response(
        user_id=user_id,
        entitlements=entitlements,
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


@router.get("/content-summaries", response_model=ContentSummaryListResponse)
def get_content_summaries(
    _authorized: None = Depends(require_admin),
) -> ContentSummaryListResponse:
    payload = list_admin_content_summaries()
    return ContentSummaryListResponse(
        schools=[ContentSummaryEntityResponse(**item) for item in payload["schools"]],
        majors=[ContentSummaryEntityResponse(**item) for item in payload["majors"]],
    )


@router.get("/content-sections", response_model=ContentSectionListResponse)
def get_content_sections(
    _authorized: None = Depends(require_admin),
) -> ContentSectionListResponse:
    payload = list_admin_content_sections()
    return ContentSectionListResponse(
        schools=[ContentSectionEntityResponse(**item) for item in payload["schools"]],
        majors=[ContentSectionEntityResponse(**item) for item in payload["majors"]],
    )


@router.get("/related-content", response_model=RelatedContentListResponse)
def get_related_content(
    _authorized: None = Depends(require_admin),
) -> RelatedContentListResponse:
    payload = list_admin_related_content()
    return RelatedContentListResponse(
        schools=[RelatedSchoolEntityResponse(**item) for item in payload["schools"]],
        majors=[RelatedMajorEntityResponse(**item) for item in payload["majors"]],
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


@router.post(
    "/content-summaries/schools/{slug}",
    response_model=ContentSummaryEntityResponse,
)
def update_school_content_summary(
    slug: str,
    payload: ContentSummaryUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> ContentSummaryEntityResponse:
    try:
        updated = update_content_summary(
            "schools",
            slug,
            normalize_content_summary(payload.summary),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="content summary entity not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ContentSummaryEntityResponse(**updated)


@router.post(
    "/content-summaries/majors/{slug}",
    response_model=ContentSummaryEntityResponse,
)
def update_major_content_summary(
    slug: str,
    payload: ContentSummaryUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> ContentSummaryEntityResponse:
    try:
        updated = update_content_summary(
            "majors",
            slug,
            normalize_content_summary(payload.summary),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="content summary entity not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ContentSummaryEntityResponse(**updated)


@router.post(
    "/content-sections/schools/{slug}",
    response_model=ContentSectionEntityResponse,
)
def update_school_content_sections(
    slug: str,
    payload: ContentSectionUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> ContentSectionEntityResponse:
    try:
        updated = update_content_sections(
            "schools",
            slug,
            normalize_content_sections(payload.sections),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="content section entity not found",
        ) from exc

    return ContentSectionEntityResponse(**updated)


@router.post(
    "/content-sections/majors/{slug}",
    response_model=ContentSectionEntityResponse,
)
def update_major_content_sections(
    slug: str,
    payload: ContentSectionUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> ContentSectionEntityResponse:
    try:
        updated = update_content_sections(
            "majors",
            slug,
            normalize_content_sections(payload.sections),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="content section entity not found",
        ) from exc

    return ContentSectionEntityResponse(**updated)


@router.post(
    "/related-content/schools/{slug}",
    response_model=RelatedSchoolEntityResponse,
)
def update_school_related_content(
    slug: str,
    payload: RelatedSchoolUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> RelatedSchoolEntityResponse:
    try:
        updated = update_related_content(
            "schools",
            slug,
            "related_majors",
            normalize_related_slugs(payload.related_majors),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="related content entity not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return RelatedSchoolEntityResponse(**updated)


@router.post(
    "/related-content/majors/{slug}",
    response_model=RelatedMajorEntityResponse,
)
def update_major_related_content(
    slug: str,
    payload: RelatedMajorUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> RelatedMajorEntityResponse:
    try:
        updated = update_related_content(
            "majors",
            slug,
            "related_schools",
            normalize_related_slugs(payload.related_schools),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="related content entity not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return RelatedMajorEntityResponse(**updated)


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
    "/featured-content/schools/{slug}/suggest-image",
    response_model=FeaturedSchoolImageSuggestionResponse,
)
def suggest_featured_school_image(
    slug: str,
    _authorized: None = Depends(require_admin),
) -> FeaturedSchoolImageSuggestionResponse:
    try:
        suggestion = featured_content_service.fetch_school_image_candidate(slug)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="featured content entity not found",
        ) from exc

    return FeaturedSchoolImageSuggestionResponse(**suggestion)


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
