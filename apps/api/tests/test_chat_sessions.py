from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models.chat import ChatMessage, ChatSession
from app.services.chat import ConversationService
from app.services.chat_sessions import (
    ChatSessionNotFoundError,
    ChatSessionOwnershipError,
    ChatSessionStore,
)
from app.services.skills import SkillRegistry


def build_session_service(engine) -> ConversationService:
    return ConversationService(
        registry=SkillRegistry([]),
        session_factory=lambda: Session(engine),
    )


def test_conversation_service_persists_and_restores_session_messages(engine) -> None:
    service = build_session_service(engine)

    first = service.handle_message(
        channel="web",
        user_id="user-a",
        message="第一轮问题",
        session_id="session-a",
    )
    second = service.handle_message(
        channel="web",
        user_id="user-a",
        message="第二轮问题",
        session_id=first["session_id"],
    )

    assert first["session_id"] == "session-a"
    assert second["session_id"] == "session-a"
    history = service.get_session_messages(session_id="session-a", user_id="user-a")
    assert [item["role"] for item in history["items"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert history["items"][0]["content"] == "第一轮问题"
    assert history["items"][1]["content_type"] == "structured_json"
    assert history["items"][1]["payload"]["intent"] == "fallback"

    with Session(engine) as session:
        stored_session = session.exec(
            select(ChatSession).where(ChatSession.session_id == "session-a")
        ).one()
        stored_messages = session.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == stored_session.id)
            .order_by(ChatMessage.id)
        ).all()

    assert stored_session.user_id == "user-a"
    assert len(stored_messages) == 4
    assert json.loads(stored_messages[1].content)["intent"] == "fallback"


def test_chat_session_cannot_be_reused_or_read_by_another_user(engine) -> None:
    service = build_session_service(engine)
    service.handle_message(
        channel="web",
        user_id="user-a",
        message="私有问题",
        session_id="private-session",
    )

    with pytest.raises(ChatSessionOwnershipError):
        service.handle_message(
            channel="web",
            user_id="user-b",
            message="越权问题",
            session_id="private-session",
        )

    with pytest.raises(ChatSessionOwnershipError):
        service.get_session_messages(
            session_id="private-session",
            user_id="user-b",
        )

    with pytest.raises(ChatSessionNotFoundError):
        service.get_session_messages(
            session_id="does-not-exist",
            user_id="user-b",
        )


def test_chat_session_delete_removes_messages_and_is_user_scoped(engine) -> None:
    service = build_session_service(engine)
    service.handle_message(
        channel="web",
        user_id="user-delete",
        message="待删除问题",
        session_id="delete-session",
    )

    assert service.delete_session(session_id="delete-session", user_id="user-delete") is True
    with pytest.raises(ChatSessionNotFoundError):
        service.get_session_messages(
            session_id="delete-session",
            user_id="user-delete",
        )

    with Session(engine) as session:
        assert session.exec(select(ChatSession)).all() == []
        assert session.exec(select(ChatMessage)).all() == []


def test_chat_session_store_purges_expired_sessions_and_messages(engine) -> None:
    now = datetime.now(UTC)
    with Session(engine) as session:
        stored = ChatSession(
            session_id="expired-session",
            user_id="expired-user",
            channel="web",
            created_at=now - timedelta(days=31),
            updated_at=now - timedelta(days=31),
            expires_at=now - timedelta(days=1),
        )
        session.add(stored)
        session.flush()
        session.add(
            ChatMessage(
                session_id=stored.id,
                request_id="chat-expired",
                role="user",
                content_type="text",
                content="过期问题",
            )
        )
        session.commit()

    store = ChatSessionStore(lambda: Session(engine))
    assert store.purge_expired_sessions() == 1
    with Session(engine) as session:
        assert session.exec(select(ChatSession)).all() == []
        assert session.exec(select(ChatMessage)).all() == []


def test_chat_session_store_builds_recent_model_context_with_turn_and_char_limits(engine) -> None:
    store = ChatSessionStore(
        lambda: Session(engine),
        context_max_turns=6,
        context_max_chars=120,
    )
    for index in range(1, 8):
        store.save_exchange(
            session_id="context-session",
            user_id="context-user",
            channel="web",
            request_id=f"chat-context-{index}",
            user_message=f"问题 {index}",
            assistant_content={
                "rendered_reply": f"回答 {index}",
                "analysis": "不应该把原始结构化 JSON 直接传给模型",
            },
        )

    context = store.get_recent_model_messages(
        session_id="context-session",
        user_id="context-user",
    )

    assert [item["role"] for item in context] == ["user", "assistant"] * 6
    assert [item["content"] for item in context[::2]] == [
        "问题 2",
        "问题 3",
        "问题 4",
        "问题 5",
        "问题 6",
        "问题 7",
    ]
    assert [item["content"] for item in context[1::2]] == [
        "回答 2",
        "回答 3",
        "回答 4",
        "回答 5",
        "回答 6",
        "回答 7",
    ]
    assert sum(len(item["content"]) for item in context) <= 120


def test_chat_session_store_trims_old_turns_when_character_budget_is_reached(engine) -> None:
    store = ChatSessionStore(
        lambda: Session(engine),
        context_max_turns=6,
        context_max_chars=17,
    )
    for index in range(1, 5):
        store.save_exchange(
            session_id="small-context-session",
            user_id="small-context-user",
            channel="web",
            request_id=f"chat-small-context-{index}",
            user_message=f"问题 {index}",
            assistant_content={"rendered_reply": f"回答 {index}"},
        )

    context = store.get_recent_model_messages(
        session_id="small-context-session",
        user_id="small-context-user",
    )

    assert [item["content"] for item in context] == [
        "问题 3",
        "回答 3",
        "问题 4",
        "回答 4",
    ]
    assert sum(len(item["content"]) for item in context) <= 17


def test_chat_session_store_does_not_leak_context_across_users(engine) -> None:
    store = ChatSessionStore(lambda: Session(engine))
    store.save_exchange(
        session_id="private-context",
        user_id="owner",
        channel="web",
        request_id="chat-owner",
        user_message="私有问题",
        assistant_content={"rendered_reply": "私有回答"},
    )

    with pytest.raises(ChatSessionOwnershipError):
        store.get_recent_model_messages(
            session_id="private-context",
            user_id="other-user",
        )


def test_chat_session_http_history_and_delete_are_user_scoped(engine) -> None:
    original_service = __import__(
        "app.routers.chat",
        fromlist=["conversation_service"],
    ).conversation_service
    chat_router_module = __import__("app.routers.chat", fromlist=["conversation_service"])
    chat_router_module.conversation_service = build_session_service(engine)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/chat/messages",
            json={
                "channel": "web",
                "user_id": "http-user",
                "message": "HTTP 会话问题",
                "session_id": "http-session",
            },
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == "http-session"

        history = client.get(
            "/api/chat/sessions/http-session/messages",
            params={"user_id": "http-user"},
        )
        assert history.status_code == 200
        assert len(history.json()["items"]) == 2

        forbidden = client.get(
            "/api/chat/sessions/http-session/messages",
            params={"user_id": "another-user"},
        )
        assert forbidden.status_code == 404

        deleted = client.delete(
            "/api/chat/sessions/http-session",
            params={"user_id": "http-user"},
        )
        assert deleted.status_code == 200
        assert deleted.json() == {
            "session_id": "http-session",
            "deleted": True,
        }
    finally:
        chat_router_module.conversation_service = original_service
