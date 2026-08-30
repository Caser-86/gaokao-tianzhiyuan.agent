from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Response

from ..config import settings

SESSION_COOKIE_NAME = "gaokao_session"
SESSION_TOKEN_PREFIX = "v1"
SAFE_LEGACY_ID_ENVIRONMENTS = {"development", "test"}


class SessionTokenError(ValueError):
    pass


class AuthenticationRequiredError(PermissionError):
    pass


class IdentityMismatchError(PermissionError):
    pass


@dataclass(frozen=True)
class UserIdentity:
    user_id: str
    expires_at: datetime | None = None


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (ValueError, UnicodeError) as exc:
        raise SessionTokenError("invalid session token encoding") from exc


def _sign(payload: str) -> str:
    digest = hmac.new(
        settings.session_secret.encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _encode(digest)


def create_session_token(
    user_id: str,
    *,
    ttl_seconds: int | None = None,
    now: int | None = None,
) -> str:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id must not be empty")
    issued_at = int(time.time() if now is None else now)
    expires_at = issued_at + (ttl_seconds or settings.session_ttl_seconds)
    payload = _encode(
        json.dumps(
            {"sub": normalized_user_id, "iat": issued_at, "exp": expires_at},
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    )
    signing_input = f"{SESSION_TOKEN_PREFIX}.{payload}"
    return f"{signing_input}.{_sign(signing_input)}"


def parse_session_token(token: str, *, now: int | None = None) -> UserIdentity:
    parts = token.strip().split(".")
    if len(parts) != 3 or parts[0] != SESSION_TOKEN_PREFIX:
        raise SessionTokenError("invalid session token format")

    signing_input = f"{parts[0]}.{parts[1]}"
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(parts[2], expected_signature):
        raise SessionTokenError("invalid session token signature")

    try:
        payload = json.loads(_decode(parts[1]).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SessionTokenError("invalid session token payload") from exc
    if not isinstance(payload, dict):
        raise SessionTokenError("invalid session token payload")

    user_id = payload.get("sub")
    expires_at = payload.get("exp")
    issued_at = payload.get("iat")
    if not isinstance(user_id, str) or not user_id.strip():
        raise SessionTokenError("session token subject is missing")
    if not isinstance(expires_at, int) or not isinstance(issued_at, int):
        raise SessionTokenError("session token timestamps are invalid")
    current_time = int(time.time() if now is None else now)
    if expires_at <= current_time or issued_at > current_time + 60:
        raise SessionTokenError("session token is expired or not yet valid")

    return UserIdentity(
        user_id=user_id.strip(),
        expires_at=datetime.fromtimestamp(expires_at, tz=UTC),
    )


def issue_guest_identity(*, now: int | None = None) -> tuple[UserIdentity, str]:
    issued_at = int(time.time() if now is None else now)
    token = create_session_token(
        f"web_{secrets.token_urlsafe(12)}",
        now=issued_at,
    )
    return parse_session_token(token, now=issued_at), token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.environment.strip().lower() not in SAFE_LEGACY_ID_ENVIRONMENTS,
        samesite="lax",
        path="/",
    )


def resolve_request_identity(
    *,
    authorization: str | None,
    cookie_token: str | None,
    claimed_user_id: str | None,
) -> tuple[UserIdentity, str | None]:
    presented_token = None
    if authorization is not None:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() != "bearer" or not value.strip():
            raise AuthenticationRequiredError("Bearer session token required")
        presented_token = value.strip()
    elif cookie_token:
        presented_token = cookie_token.strip()

    normalized_claim = claimed_user_id.strip() if isinstance(claimed_user_id, str) else ""
    if presented_token:
        try:
            identity = parse_session_token(presented_token)
        except SessionTokenError as exc:
            raise AuthenticationRequiredError("invalid session token") from exc
        if normalized_claim and normalized_claim != identity.user_id:
            raise IdentityMismatchError("claimed user_id does not match session subject")
        return identity, None

    if normalized_claim:
        environment = settings.environment.strip().lower()
        if environment not in SAFE_LEGACY_ID_ENVIRONMENTS:
            raise AuthenticationRequiredError("server-issued session required")
        return UserIdentity(user_id=normalized_claim), None

    identity, token = issue_guest_identity()
    return identity, token
