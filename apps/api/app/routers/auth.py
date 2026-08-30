from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Response
from pydantic import BaseModel

from ..services.auth import issue_guest_identity, set_session_cookie

router = APIRouter(prefix="/api/auth", tags=["auth"])


class GuestSessionResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user_id: str
    expires_at: datetime


@router.post("/session", response_model=GuestSessionResponse)
def create_guest_session(response: Response) -> GuestSessionResponse:
    identity, token = issue_guest_identity()
    set_session_cookie(response, token)
    return GuestSessionResponse(
        access_token=token,
        user_id=identity.user_id,
        expires_at=identity.expires_at,
    )
