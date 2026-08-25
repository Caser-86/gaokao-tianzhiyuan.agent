from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat as chat_router_module
from app.services.auth import (
    SessionTokenError,
    create_session_token,
    parse_session_token,
)

client = TestClient(app)


def test_production_rejects_claimed_user_without_server_session(monkeypatch) -> None:
    monkeypatch.setattr(chat_router_module.settings, "environment", "production")

    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "web",
            "user_id": "claimed-user-without-session",
            "message": "东南大学怎么样",
        },
    )

    assert response.status_code == 401


def test_production_rejects_user_id_mismatch_with_server_session(monkeypatch) -> None:
    monkeypatch.setattr(chat_router_module.settings, "environment", "production")
    token = create_session_token("server-issued-user")

    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "channel": "web",
            "user_id": "different-claimed-user",
            "message": "东南大学怎么样",
        },
    )

    assert response.status_code == 403


def test_guest_session_endpoint_issues_cookie_and_verifiable_token() -> None:
    response = client.post("/api/auth/session")

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "Bearer"
    assert payload["user_id"].startswith("web_")
    assert "gaokao_session=" in response.headers["set-cookie"]
    identity = parse_session_token(payload["access_token"])
    assert identity.user_id == payload["user_id"]


def test_production_accepts_server_session_and_uses_token_subject(monkeypatch) -> None:
    monkeypatch.setattr(chat_router_module.settings, "environment", "production")
    token = create_session_token("server-issued-chat-user")

    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "channel": "web",
            "message": "东南大学怎么样",
        },
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == "server-issued-chat-user"


def test_session_token_tampering_is_rejected() -> None:
    token = create_session_token("server-issued-user")
    tampered = f"{token[:-1]}{'a' if token[-1] != 'a' else 'b'}"

    try:
        parse_session_token(tampered)
    except SessionTokenError:
        return
    raise AssertionError("tampered session token was accepted")
