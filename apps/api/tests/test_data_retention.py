from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.models.chat import ChatMessage, ChatSession
from app.models.ingestion import MediaAnalysisEvent, WeChatMessageReceipt
from app.services.data_retention import delete_user_data, purge_expired_data


def test_purge_expired_data_removes_expired_persisted_records(engine) -> None:
    now = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
    with Session(engine) as session:
        expired_session = ChatSession(
            session_id="expired-session",
            user_id="user-expired",
            channel="web",
            created_at=now - timedelta(days=31),
            updated_at=now - timedelta(days=31),
            expires_at=now - timedelta(seconds=1),
        )
        active_session = ChatSession(
            session_id="active-session",
            user_id="user-active",
            channel="web",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=29),
        )
        session.add(expired_session)
        session.add(active_session)
        session.flush()
        session.add(
            ChatMessage(
                session_id=expired_session.id,
                request_id="expired-request",
                role="user",
                content_type="text",
                content="过期消息",
                created_at=now - timedelta(days=31),
            )
        )
        session.add(
            MediaAnalysisEvent(
                user_id="user-expired",
                message_id="old-message",
                media_id="old-media",
                summary="old",
                created_at=now - timedelta(days=31),
            )
        )
        session.add(
            MediaAnalysisEvent(
                user_id="user-active",
                message_id="new-message",
                media_id="new-media",
                summary="new",
                created_at=now - timedelta(days=1),
            )
        )
        session.add(
            WeChatMessageReceipt(
                dedupe_key="msgid:old",
                message_id="old",
                received_at=now - timedelta(minutes=6),
            )
        )
        session.add(
            WeChatMessageReceipt(
                dedupe_key="msgid:new",
                message_id="new",
                received_at=now - timedelta(seconds=30),
            )
        )
        session.commit()

        result = purge_expired_data(
            session,
            now=now,
            chat_session_retention_days=30,
            media_analysis_retention_days=30,
            wechat_receipt_retention_seconds=300,
        )

        assert result == {
            "chat_sessions": 1,
            "chat_messages": 1,
            "media_analysis_events": 1,
            "wechat_message_receipts": 1,
        }

        assert session.exec(select(ChatSession)).all() == [active_session]
        assert len(session.exec(select(ChatMessage)).all()) == 0
        assert [item.message_id for item in session.exec(select(MediaAnalysisEvent)).all()] == [
            "new-message"
        ]
        assert [item.message_id for item in session.exec(select(WeChatMessageReceipt)).all()] == [
            "new"
        ]


def test_delete_user_data_is_scoped_and_removes_chat_and_media_records(engine) -> None:
    with Session(engine) as session:
        owned_session = ChatSession(session_id="owned", user_id="user-a", channel="web")
        other_session = ChatSession(session_id="other", user_id="user-b", channel="web")
        session.add(owned_session)
        session.add(other_session)
        session.flush()
        session.add(
            ChatMessage(
                session_id=owned_session.id,
                request_id="owned-request",
                role="user",
                content_type="text",
                content="应删除",
            )
        )
        session.add(
            ChatMessage(
                session_id=other_session.id,
                request_id="other-request",
                role="user",
                content_type="text",
                content="应保留",
            )
        )
        session.add(MediaAnalysisEvent(user_id="user-a", message_id="owned-media"))
        session.add(MediaAnalysisEvent(user_id="user-b", message_id="other-media"))
        session.commit()

        assert delete_user_data(session, user_id="user-a") == {
            "chat_sessions": 1,
            "chat_messages": 1,
            "media_analysis_events": 1,
        }
        assert [item.user_id for item in session.exec(select(ChatSession)).all()] == ["user-b"]
        assert [item.user_id for item in session.exec(select(MediaAnalysisEvent)).all()] == [
            "user-b"
        ]
