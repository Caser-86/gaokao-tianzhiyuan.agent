from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models.chat import ChatMessage, ChatSession
from app.models.ingestion import MediaAnalysisEvent
from app.services.auth import create_session_token


def test_delete_my_data_requires_an_existing_session() -> None:
    response = TestClient(app).delete("/api/privacy/me")

    assert response.status_code == 401


def test_delete_my_data_removes_only_the_authenticated_users_records(engine) -> None:
    with Session(engine) as session:
        owned = ChatSession(session_id="privacy-owned", user_id="privacy-user", channel="web")
        other = ChatSession(session_id="privacy-other", user_id="other-user", channel="web")
        session.add(owned)
        session.add(other)
        session.flush()
        session.add(
            ChatMessage(
                session_id=owned.id,
                request_id="privacy-request",
                role="user",
                content_type="text",
                content="private message",
            )
        )
        session.add(MediaAnalysisEvent(user_id="privacy-user", message_id="privacy-media"))
        session.add(MediaAnalysisEvent(user_id="other-user", message_id="other-media"))
        session.commit()

    token = create_session_token("privacy-user")
    response = TestClient(app).delete(
        "/api/privacy/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "deleted": {
            "chat_sessions": 1,
            "chat_messages": 1,
            "media_analysis_events": 1,
        }
    }

    with Session(engine) as session:
        assert [item.user_id for item in session.exec(select(ChatSession)).all()] == ["other-user"]
        assert [item.user_id for item in session.exec(select(MediaAnalysisEvent)).all()] == [
            "other-user"
        ]
