from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from ..db import get_session
from ..services.auth import (
    SESSION_COOKIE_NAME,
    AuthenticationRequiredError,
    resolve_request_identity,
)
from ..services.data_retention import delete_user_data

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.delete("/me")
def delete_my_data(
    request: Request,
    session: Session = Depends(get_session),
) -> dict[str, dict[str, int]]:
    if not request.headers.get("authorization") and not request.cookies.get(SESSION_COOKIE_NAME):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="server-issued session required",
        )

    try:
        identity, _ = resolve_request_identity(
            authorization=request.headers.get("authorization"),
            cookie_token=request.cookies.get(SESSION_COOKIE_NAME),
            claimed_user_id=None,
        )
    except AuthenticationRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return {"deleted": delete_user_data(session, user_id=identity.user_id)}
