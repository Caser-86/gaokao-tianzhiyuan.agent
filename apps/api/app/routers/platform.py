from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..db import get_session
from ..services.access_control import get_user_entitlements
from ..services.auth import (
    AuthenticationRequiredError,
    IdentityMismatchError,
    resolve_request_identity,
    set_session_cookie,
)
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
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> dict[str, list[str]]:
    try:
        identity, issued_token = resolve_request_identity(
            authorization=request.headers.get("authorization"),
            cookie_token=request.cookies.get("gaokao_session"),
            claimed_user_id=payload.user_id,
        )
    except AuthenticationRequiredError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except IdentityMismatchError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if issued_token:
        set_session_cookie(response, issued_token)

    persisted_entitlements = get_user_entitlements(session, identity.user_id)
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
