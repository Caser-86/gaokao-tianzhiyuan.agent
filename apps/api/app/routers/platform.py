from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..db import get_session
from ..services.access_control import get_user_entitlements
from ..services.platform import evaluate_entitlements, list_products, normalize_event

router = APIRouter(prefix="/api/platform", tags=["platform"])


class EntitlementEvaluationRequest(BaseModel):
    product_slugs: list[str] = Field(default_factory=list)
    user_id: str | None = None


class EventTrackRequest(BaseModel):
    event_name: str
    step: str
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("/products")
def product_catalog() -> dict[str, list[dict[str, Any]]]:
    return list_products()


@router.post("/entitlements/evaluate")
def entitlement_evaluation(
    payload: EntitlementEvaluationRequest,
    session: Session = Depends(get_session),
) -> dict[str, list[str]]:
    persisted_entitlements = (
        get_user_entitlements(session, payload.user_id)
        if isinstance(payload.user_id, str)
        else []
    )
    return evaluate_entitlements(
        payload.product_slugs,
        persisted_entitlements=persisted_entitlements,
    )


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
def track_event(payload: EventTrackRequest) -> dict[str, object]:
    return {
        "accepted": True,
        "event": normalize_event(
            event_name=payload.event_name,
            step=payload.step,
            metadata=payload.metadata,
        ),
    }
