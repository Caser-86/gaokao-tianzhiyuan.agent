from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_messages_preflight_allows_local_web_origin() -> None:
    response = client.options(
        "/api/chat/messages",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
    assert "POST" in response.headers["access-control-allow-methods"]
