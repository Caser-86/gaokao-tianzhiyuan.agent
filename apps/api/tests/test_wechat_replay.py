from __future__ import annotations

from hashlib import sha1
from time import time

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import settings
from app.main import app
from app.models.ingestion import WeChatMessageReceipt

TOKEN = "wechat-token"
client = TestClient(app)


def _signature(timestamp: str, nonce: str) -> str:
    return sha1("".join(sorted([TOKEN, timestamp, nonce])).encode("utf-8")).hexdigest()


def _message_xml(*, msg_id: str, content: str = "东南大学怎么样") -> str:
    return f"""
    <xml>
      <ToUserName><![CDATA[gh-app]]></ToUserName>
      <FromUserName><![CDATA[wx-user-replay]]></FromUserName>
      <CreateTime>1710000000</CreateTime>
      <MsgType><![CDATA[text]]></MsgType>
      <Content><![CDATA[{content}]]></Content>
      <MsgId>{msg_id}</MsgId>
    </xml>
    """.strip()


def _post_message(*, timestamp: str, nonce: str, msg_id: str, content: str = "东南大学怎么样"):
    return client.post(
        "/api/chat/channels/wechat/official-account",
        params={
            "signature": _signature(timestamp, nonce),
            "timestamp": timestamp,
            "nonce": nonce,
        },
        content=_message_xml(msg_id=msg_id, content=content),
    )


def test_official_account_rejects_stale_timestamp(monkeypatch) -> None:
    monkeypatch.setattr(settings, "wechat_official_account_token", TOKEN)
    now = int(time())
    stale_timestamp = str(now - settings.wechat_signature_ttl_seconds - 1)

    response = _post_message(
        timestamp=stale_timestamp,
        nonce="stale-nonce",
        msg_id="stale-msg",
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "wechat timestamp outside allowed window"

    verification_response = client.get(
        "/api/chat/channels/wechat/official-account",
        params={
            "signature": _signature(stale_timestamp, "stale-get-nonce"),
            "timestamp": stale_timestamp,
            "nonce": "stale-get-nonce",
            "echostr": "echo",
        },
    )
    assert verification_response.status_code == 403


def test_official_account_rejects_oversized_body(monkeypatch) -> None:
    monkeypatch.setattr(settings, "wechat_official_account_token", TOKEN)
    timestamp = str(int(time()))
    nonce = "large-body-nonce"
    oversized_body = b"x" * (settings.wechat_max_body_bytes + 1)

    response = client.post(
        "/api/chat/channels/wechat/official-account",
        params={
            "signature": _signature(timestamp, nonce),
            "timestamp": timestamp,
            "nonce": nonce,
        },
        content=oversized_body,
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "wechat request body too large"


def test_duplicate_msg_id_is_acknowledged_without_second_processing(monkeypatch, engine) -> None:
    monkeypatch.setattr(settings, "wechat_official_account_token", TOKEN)
    timestamp = str(int(time()))
    first = _post_message(timestamp=timestamp, nonce="msgid-nonce-1", msg_id="same-msg-id")
    second = _post_message(timestamp=timestamp, nonce="msgid-nonce-2", msg_id="same-msg-id")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.text == "success"
    with Session(engine) as session:
        receipts = session.exec(select(WeChatMessageReceipt)).all()
    assert len(receipts) == 2


def test_duplicate_nonce_is_acknowledged_without_second_processing(monkeypatch, engine) -> None:
    monkeypatch.setattr(settings, "wechat_official_account_token", TOKEN)
    timestamp = str(int(time()))
    first = _post_message(timestamp=timestamp, nonce="same-nonce", msg_id="nonce-msg-1")
    second = _post_message(timestamp=timestamp, nonce="same-nonce", msg_id="nonce-msg-2")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.text == "success"
    with Session(engine) as session:
        receipts = session.exec(select(WeChatMessageReceipt)).all()
    assert len(receipts) == 2
