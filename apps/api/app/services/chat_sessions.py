from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlmodel import Session, select

from ..models.chat import ChatMessage, ChatSession

CHAT_SESSION_RETENTION_DAYS = 30


class ChatSessionNotFoundError(LookupError):
    pass


class ChatSessionOwnershipError(LookupError):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


class ChatSessionStore:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        retention_days: int = CHAT_SESSION_RETENTION_DAYS,
    ) -> None:
        self.session_factory = session_factory
        if retention_days <= 0:
            raise ValueError("retention_days must be greater than zero")
        self.retention_days = retention_days

    def assert_access(self, *, session_id: str, user_id: str) -> None:
        with self.session_factory() as session:
            stored = self._find_session(session, session_id=session_id)
            if stored is None:
                return
            if self._is_expired(stored, now=utcnow()):
                self._delete_session_row(session, stored)
                session.commit()
                return
            self._assert_owner(stored, user_id=user_id)

    def save_exchange(
        self,
        *,
        session_id: str,
        user_id: str,
        channel: str,
        request_id: str,
        user_message: str,
        assistant_content: dict[str, Any],
    ) -> None:
        now = utcnow()
        with self.session_factory() as session:
            self._purge_expired(session, now=now)
            stored = self._find_session(session, session_id=session_id)
            if stored is None:
                stored = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    channel=channel,
                    created_at=now,
                    updated_at=now,
                    expires_at=now + timedelta(days=self.retention_days),
                )
                session.add(stored)
                session.flush()
            else:
                self._assert_owner(stored, user_id=user_id)
                stored.channel = channel
                stored.updated_at = now
                stored.expires_at = now + timedelta(days=self.retention_days)

            session.add(
                ChatMessage(
                    session_id=stored.id,
                    request_id=request_id,
                    role="user",
                    content_type="text",
                    content=user_message,
                    created_at=now,
                )
            )
            session.add(
                ChatMessage(
                    session_id=stored.id,
                    request_id=request_id,
                    role="assistant",
                    content_type="structured_json",
                    content=json.dumps(assistant_content, ensure_ascii=False, sort_keys=True),
                    created_at=now,
                )
            )
            session.commit()

    def get_messages(self, *, session_id: str, user_id: str) -> dict[str, Any]:
        now = utcnow()
        with self.session_factory() as session:
            stored = self._require_session(session, session_id=session_id, user_id=user_id)
            if self._is_expired(stored, now=now):
                self._delete_session_row(session, stored)
                session.commit()
                raise ChatSessionNotFoundError(session_id)

            messages = session.exec(
                select(ChatMessage)
                .where(ChatMessage.session_id == stored.id)
                .order_by(ChatMessage.id)
            ).all()
            return {
                "session_id": stored.session_id,
                "channel": stored.channel,
                "created_at": stored.created_at.isoformat(),
                "updated_at": stored.updated_at.isoformat(),
                "expires_at": stored.expires_at.isoformat(),
                "items": [self._serialize_message(item) for item in messages],
            }

    def delete_session(self, *, session_id: str, user_id: str) -> bool:
        with self.session_factory() as session:
            stored = self._require_session(session, session_id=session_id, user_id=user_id)
            self._delete_session_row(session, stored)
            session.commit()
            return True

    def purge_expired_sessions(self) -> int:
        with self.session_factory() as session:
            deleted = self._purge_expired(session, now=utcnow())
            session.commit()
            return deleted

    @staticmethod
    def _find_session(session: Session, *, session_id: str) -> ChatSession | None:
        return session.exec(select(ChatSession).where(ChatSession.session_id == session_id)).first()

    def _require_session(
        self,
        session: Session,
        *,
        session_id: str,
        user_id: str,
    ) -> ChatSession:
        stored = self._find_session(session, session_id=session_id)
        if stored is None:
            raise ChatSessionNotFoundError(session_id)
        self._assert_owner(stored, user_id=user_id)
        return stored

    @staticmethod
    def _assert_owner(stored: ChatSession, *, user_id: str) -> None:
        if stored.user_id != user_id:
            raise ChatSessionOwnershipError(stored.session_id)

    @staticmethod
    def _is_expired(stored: ChatSession, *, now: datetime) -> bool:
        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at <= now

    def _purge_expired(self, session: Session, *, now: datetime) -> int:
        expired = session.exec(select(ChatSession).where(ChatSession.expires_at <= now)).all()
        for stored in expired:
            self._delete_session_row(session, stored)
        return len(expired)

    @staticmethod
    def _delete_session_row(session: Session, stored: ChatSession) -> None:
        messages = session.exec(
            select(ChatMessage).where(ChatMessage.session_id == stored.id)
        ).all()
        for message in messages:
            session.delete(message)
        session.delete(stored)

    @staticmethod
    def _serialize_message(message: ChatMessage) -> dict[str, Any]:
        item: dict[str, Any] = {
            "id": message.id,
            "request_id": message.request_id,
            "role": message.role,
            "content_type": message.content_type,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }
        if message.content_type == "structured_json":
            try:
                item["payload"] = json.loads(message.content)
            except json.JSONDecodeError:
                item["payload"] = None
        return item
