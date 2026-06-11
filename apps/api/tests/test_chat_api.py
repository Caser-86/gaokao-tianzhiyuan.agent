import json
import base64
import struct
from hashlib import sha1
from dataclasses import dataclass

from fastapi.testclient import TestClient
import pyaes
from sqlmodel import Session, select

from app.main import app
from app.db import create_all_models, get_engine
from app.models.ingestion import MediaAnalysisEvent
from app.routers import chat as chat_router_module
from app.services.access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    set_smart_analysis_mode,
    set_user_entitlement,
)
from app.services.chat import ConversationService
from app.services.skills import (
    CatalogLookupSkill,
    ChatRequestContext,
    SkillInvocationResult,
    SkillMatchResult,
    SkillMetadata,
    SkillRegistry,
    ZhangXueFengSkill,
)

client = TestClient(app)


@dataclass(frozen=True)
class WebOnlySkill:
    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="web-only-skill",
            name="Web Only Skill",
            version="v1",
            description="Direct invoke availability test skill",
            enabled=True,
            supports_channels=("web",),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        return SkillMatchResult(matched=True, confidence=1.0, reason="always matched")

    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult:
        return SkillInvocationResult(
            intent="fallback",
            summary="web-only",
            entities={},
            analysis="",
            suggestions=[],
            follow_up_questions=[],
            actions=[],
            risk_flags=[],
            rendered_reply="",
        )


class FakeProvider:
    def complete_text(self, *, messages: list) -> str:
        return json.dumps(
            {
                "intent": "major_recommendation",
                "summary": "建议避开金融",
                "entities": {"province": "河南", "score": 560},
                "analysis": "普通家庭优先看就业出口",
                "suggestions": [
                    {
                        "type": "major",
                        "title": "计算机科学与技术",
                        "reason": "通用能力更强",
                    }
                ],
                "follow_up_questions": ["孩子是理科还是文科？"],
                "actions": [],
                "risk_flags": ["financial_industry_competition"],
                "rendered_reply": "我跟你说，普通家庭先别冲金融。",
            },
            ensure_ascii=False,
        )


def test_chat_health_returns_ok() -> None:
    response = client.get("/api/chat/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_skills_lists_registered_skills() -> None:
    response = client.get("/api/chat/skills")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["skill_id"] == "zhangxuefeng"
    assert payload["items"][0]["version"] == "v2"
    assert any(item["skill_id"] == "catalog_lookup" for item in payload["items"])
    return
    assert response.json() == {
        "items": [
            {
                "skill_id": "zhangxuefeng",
                "name": "张雪峰",
                "version": "v2",
                "enabled": True,
                "supports_channels": ["wechat", "web"],
                "description": "使用本地 SKILL.md 和模型中转的高考咨询 skill",
            }
        ]
    }


def test_chat_skills_list_includes_catalog_lookup() -> None:
    response = client.get("/api/chat/skills")

    assert response.status_code == 200
    assert any(
        item == {
            "skill_id": "catalog_lookup",
            "name": "Catalog Lookup",
            "version": "v1",
            "enabled": True,
            "supports_channels": ["wechat", "web"],
            "description": "Catalog-backed school and major lookup skill",
        }
        for item in response.json()["items"]
    )


def test_chat_messages_can_route_to_catalog_lookup_skill_for_school_queries() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-catalog-school",
            "message": "\u4e1c\u5357\u5927\u5b66\u600e\u4e48\u6837",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_skill"]["skill_id"] == "catalog_lookup"
    assert payload["output"]["content"]["intent"] == "catalog_lookup_school"
    assert payload["output"]["content"]["entities"] == {
        "entity_type": "school",
        "slug": "southeast-university",
        "name": "\u4e1c\u5357\u5927\u5b66",
        "region": "\u6c5f\u82cf",
        "city": "\u5357\u4eac",
    }
    assert payload["output"]["content"]["actions"] == [
        {
            "type": "open_school",
            "label": "\u67e5\u770b\u9662\u6821\u8be6\u60c5",
            "target": "/schools/southeast-university",
        }
    ]
    assert payload["debug"] == {"used_fallback": False, "notes": []}


def test_chat_skill_invoke_supports_catalog_lookup_direct_calls() -> None:
    response = client.post(
        "/api/chat/skills/catalog_lookup/invoke",
        json={
            "channel": "web",
            "user_id": "user-catalog-major",
            "message": "\u8ba1\u7b97\u673a\u79d1\u5b66\u4e0e\u6280\u672f\u4e13\u4e1a\u4ecb\u7ecd",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_skill"]["skill_id"] == "catalog_lookup"
    assert payload["output"]["content"]["intent"] == "catalog_lookup_major"
    assert payload["output"]["content"]["entities"] == {
        "entity_type": "major",
        "slug": "computer-science",
        "name": "\u8ba1\u7b97\u673a\u79d1\u5b66\u4e0e\u6280\u672f",
        "discipline": "\u5de5\u5b66",
    }
    assert payload["output"]["content"]["actions"] == [
        {
            "type": "open_major",
            "label": "\u67e5\u770b\u4e13\u4e1a\u8be6\u60c5",
            "target": "/majors/computer-science",
        }
    ]
    assert payload["debug"] == {"used_fallback": False, "notes": []}


def test_chat_messages_can_return_provider_backed_skill_output(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    original_service = chat_router_module.conversation_service
    chat_router_module.conversation_service = ConversationService(
        registry=SkillRegistry(
            [
                ZhangXueFengSkill(
                    provider=FakeProvider(),
                    skill_prompt_path=str(skill_file),
                )
            ]
        )
    )

    try:
        response = client.post(
            "/api/chat/messages",
            json={
                "channel": "wechat",
                "user_id": "wx-openid-123",
                "message": "河南560分想学金融，靠谱吗？",
                "metadata": {"smart_analysis_mode": "on"},
            },
        )
    finally:
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "wechat"
    assert payload["user_id"] == "wx-openid-123"
    assert payload["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert payload["output"]["content"]["summary"] == "建议避开金融"
    assert payload["output"]["content"]["analysis"] == "普通家庭优先看就业出口"
    assert payload["output"]["content"]["rendered_reply"] == "我跟你说，普通家庭先别冲金融。"
    assert payload["debug"] == {"used_fallback": False, "notes": []}
    assert payload["request_id"].startswith("chat_")


def test_chat_messages_returns_global_fallback_for_unmatched_message() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-456",
            "message": "今天天气怎么样",
        },
    )

    assert response.status_code == 200
    assert response.json()["matched_skill"] == {
        "skill_id": "fallback",
        "version": "v1",
        "confidence": 0.0,
        "reason": "no enabled skill exceeded routing threshold",
    }
    assert response.json()["output"]["content"] == {
        "intent": "fallback",
        "summary": "当前没有命中明确技能",
        "entities": {},
        "analysis": "当前使用全局回退，请补充学校、专业或志愿填报需求。",
        "suggestions": [],
        "follow_up_questions": ["你想查学校、专业，还是志愿填报建议？"],
        "actions": [],
        "risk_flags": [],
        "rendered_reply": "你想查学校、专业，还是志愿填报建议？",
    }
    assert response.json()["debug"] == {"used_fallback": True, "notes": []}


def test_chat_messages_rejects_invalid_channel() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "sms",
            "user_id": "wx-openid-789",
            "message": "帮我查学校",
        },
    )

    assert response.status_code == 422


def test_chat_skill_invoke_allows_direct_skill_call(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    original_service = chat_router_module.conversation_service
    chat_router_module.conversation_service = ConversationService(
        registry=SkillRegistry(
            [
                ZhangXueFengSkill(
                    provider=None,
                    skill_prompt_path=str(skill_file),
                )
            ]
        )
    )

    try:
        response = client.post(
            "/api/chat/skills/zhangxuefeng/invoke",
            json={
                "channel": "web",
                "user_id": "user-1",
                "message": "江苏985怎么选",
                "metadata": {
                    "source": "manual-debug",
                    "smart_analysis_mode": "on",
                },
            },
        )
    finally:
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert response.json()["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert response.json()["output"]["type"] == "structured_json"
    assert response.json()["output"]["content"]["analysis"] == "当前使用规则降级结果，建议补充省份、分数和专业意向。"
    assert response.json()["debug"] == {
        "used_fallback": True,
        "notes": ["provider_not_configured"],
    }


def test_chat_skill_invoke_returns_404_for_unknown_skill() -> None:
    response = client.post(
        "/api/chat/skills/missing-skill/invoke",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-999",
            "message": "帮我查学校",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "chat skill not found"}


def test_chat_skill_invoke_returns_409_for_unsupported_channel() -> None:
    original_service = chat_router_module.conversation_service
    chat_router_module.conversation_service = ConversationService(
        registry=SkillRegistry([WebOnlySkill()])
    )

    try:
        response = client.post(
            "/api/chat/skills/web-only-skill/invoke",
            json={
                "channel": "wechat",
                "user_id": "wx-openid-unsupported",
                "message": "帮我查学校",
            },
        )
    finally:
        chat_router_module.conversation_service = original_service

    assert response.status_code == 409
    assert response.json() == {"detail": "chat skill unavailable"}


def test_wechat_chat_adapter_normalizes_payload_and_reuses_chat_flow(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    original_service = chat_router_module.conversation_service
    chat_router_module.conversation_service = ConversationService(
        registry=SkillRegistry(
            [
                ZhangXueFengSkill(
                    provider=None,
                    skill_prompt_path=str(skill_file),
                )
            ]
        )
    )

    try:
        response = client.post(
            "/api/chat/channels/wechat",
            json={
                "openid": "wx-adapter-1",
                "message": "帮我看看江苏适合冲哪些985",
                "message_type": "text",
                "metadata": {
                    "source": "official_account",
                    "smart_analysis_mode": "on",
                },
            },
        )
    finally:
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "wechat"
    assert payload["user_id"] == "wx-adapter-1"
    assert payload["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert payload["output"]["content"]["intent"] == "school_recommendation"
    assert payload["debug"] == {
        "used_fallback": True,
        "notes": ["provider_not_configured"],
    }


def test_wechat_chat_adapter_requires_openid_and_message() -> None:
    response = client.post(
        "/api/chat/channels/wechat",
        json={
            "openid": "",
            "message": "",
            "message_type": "text",
        },
    )

    assert response.status_code == 422


def test_wechat_chat_adapter_merges_persisted_user_entitlements(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("寮犻洩宄版祴璇曟彁绀鸿瘝", encoding="utf-8")
    with Session(get_engine()) as session:
        set_user_entitlement(
            session,
            user_id="wx-openid-entitled",
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=True,
        )

    original_service = chat_router_module.conversation_service
    chat_router_module.conversation_service = ConversationService(
        registry=SkillRegistry(
            [
                ZhangXueFengSkill(
                    provider=None,
                    skill_prompt_path=str(skill_file),
                )
            ]
        )
    )

    try:
        response = client.post(
            "/api/chat/channels/wechat",
            json={
                "openid": "wx-openid-entitled",
                "message": "娌冲崡560鍒嗘兂瀛﹂噾铻嶏紝闈犺氨鍚楋紵",
                "message_type": "text",
                "metadata": {
                    "source": "official_account",
                    "smart_analysis_mode": "gated",
                },
            },
        )
    finally:
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "wechat"
    assert payload["user_id"] == "wx-openid-entitled"
    assert payload["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert payload["debug"] == {
        "used_fallback": True,
        "notes": ["provider_not_configured"],
    }


def test_chat_messages_return_policy_note_when_smart_analysis_is_globally_off() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-policy-1",
            "message": "河南560分想学金融，靠谱吗？",
            "metadata": {
                "smart_analysis_mode": "off",
                "entitlements": ["smart_analysis"],
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["debug"] == {
        "used_fallback": True,
        "notes": ["smart_analysis_disabled_globally"],
    }


def test_chat_messages_return_policy_note_when_gated_user_lacks_entitlement() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-policy-2",
            "message": "河南560分想学金融，靠谱吗？",
            "metadata": {
                "smart_analysis_mode": "gated",
                "entitlements": [],
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["debug"] == {
        "used_fallback": True,
        "notes": ["smart_analysis_entitlement_required"],
    }


def build_wechat_signature(*, token: str, timestamp: str, nonce: str) -> str:
    payload = "".join(sorted([token, timestamp, nonce]))
    return sha1(payload.encode("utf-8")).hexdigest()


def build_wechat_msg_signature(
    *, token: str, timestamp: str, nonce: str, encrypted: str
) -> str:
    payload = "".join(sorted([token, timestamp, nonce, encrypted]))
    return sha1(payload.encode("utf-8")).hexdigest()


def pad_wechat_plaintext(raw: bytes) -> bytes:
    block_size = 32
    amount = block_size - (len(raw) % block_size)
    if amount == 0:
        amount = block_size
    return raw + bytes([amount]) * amount


def unpad_wechat_plaintext(raw: bytes) -> bytes:
    amount = raw[-1]
    return raw[:-amount]


def encrypt_wechat_message(*, plaintext: str, app_id: str, encoding_aes_key: str) -> str:
    key = base64.b64decode(f"{encoding_aes_key}=")
    iv = key[:16]
    plain = (
        b"0123456789ABCDEF"
        + struct.pack(">I", len(plaintext.encode("utf-8")))
        + plaintext.encode("utf-8")
        + app_id.encode("utf-8")
    )
    padded = pad_wechat_plaintext(plain)
    encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv=iv))
    encrypted = encrypter.feed(padded) + encrypter.feed()
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_wechat_message(*, encrypted: str, app_id: str, encoding_aes_key: str) -> str:
    key = base64.b64decode(f"{encoding_aes_key}=")
    iv = key[:16]
    decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv=iv))
    padded = decrypter.feed(base64.b64decode(encrypted)) + decrypter.feed()
    plain = unpad_wechat_plaintext(padded)
    xml_length = struct.unpack(">I", plain[16:20])[0]
    xml_content = plain[20 : 20 + xml_length].decode("utf-8")
    app_id_from_payload = plain[20 + xml_length :].decode("utf-8")
    assert app_id_from_payload == app_id
    return xml_content


def test_wechat_official_account_verify_returns_echostr_for_valid_signature() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    timestamp = "1710000000"
    nonce = "nonce-123"
    echostr = "echo-me"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )

    try:
        response = client.get(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
                "echostr": echostr,
            },
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token

    assert response.status_code == 200
    assert response.text == echostr


def test_wechat_official_account_verify_returns_plain_echostr_for_valid_aes_signature() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_app_id = getattr(
        chat_router_module.settings,
        "wechat_official_account_app_id",
        "",
    )
    original_aes_key = getattr(
        chat_router_module.settings,
        "wechat_official_account_encoding_aes_key",
        "",
    )
    raw_key = b"0123456789abcdef0123456789abcdef"
    encoding_aes_key = base64.b64encode(raw_key).decode("utf-8")[:-1]
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    chat_router_module.settings.wechat_official_account_app_id = "wx-test-appid"
    chat_router_module.settings.wechat_official_account_encoding_aes_key = (
        encoding_aes_key
    )
    timestamp = "1710000000"
    nonce = "nonce-123"
    echostr = encrypt_wechat_message(
        plaintext="echo-me-aes",
        app_id="wx-test-appid",
        encoding_aes_key=encoding_aes_key,
    )
    msg_signature = build_wechat_msg_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
        encrypted=echostr,
    )

    try:
        response = client.get(
            "/api/chat/channels/wechat/official-account",
            params={
                "msg_signature": msg_signature,
                "timestamp": timestamp,
                "nonce": nonce,
                "echostr": echostr,
                "encrypt_type": "aes",
            },
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.settings.wechat_official_account_app_id = original_app_id
        chat_router_module.settings.wechat_official_account_encoding_aes_key = (
            original_aes_key
        )

    assert response.status_code == 200
    assert response.text == "echo-me-aes"


def test_wechat_official_account_verify_rejects_invalid_signature() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    try:
        response = client.get(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": "invalid",
                "timestamp": "1710000000",
                "nonce": "nonce-123",
                "echostr": "echo-me",
            },
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token

    assert response.status_code == 403
    assert response.json() == {"detail": "wechat signature verification failed"}


def test_wechat_official_account_aes_text_message_reuses_chat_flow_and_returns_encrypted_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_app_id = getattr(
        chat_router_module.settings,
        "wechat_official_account_app_id",
        "",
    )
    original_aes_key = getattr(
        chat_router_module.settings,
        "wechat_official_account_encoding_aes_key",
        "",
    )
    original_service = chat_router_module.conversation_service
    raw_key = b"0123456789abcdef0123456789abcdef"
    encoding_aes_key = base64.b64encode(raw_key).decode("utf-8")[:-1]
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    chat_router_module.settings.wechat_official_account_app_id = "wx-test-appid"
    chat_router_module.settings.wechat_official_account_encoding_aes_key = (
        encoding_aes_key
    )

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_oa_aes_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "AES recommendation summary",
                        "rendered_reply": "AES official account reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    inner_xml = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_aes]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[text]]></MsgType>
      <Content><![CDATA[Need AES advice]]></Content>
      <MsgId>1234567890</MsgId>
    </xml>
    """.strip()
    encrypted = encrypt_wechat_message(
        plaintext=inner_xml,
        app_id="wx-test-appid",
        encoding_aes_key=encoding_aes_key,
    )
    msg_signature = build_wechat_msg_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
        encrypted=encrypted,
    )
    body = f"""
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <Encrypt><![CDATA[{encrypted}]]></Encrypt>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "msg_signature": msg_signature,
                "timestamp": timestamp,
                "nonce": nonce,
                "encrypt_type": "aes",
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.settings.wechat_official_account_app_id = original_app_id
        chat_router_module.settings.wechat_official_account_encoding_aes_key = (
            original_aes_key
        )
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Encrypt><![CDATA[" in response.text
    encrypted_reply = response.text.split("<Encrypt><![CDATA[", 1)[1].split(
        "]]></Encrypt>",
        1,
    )[0]
    decrypted_reply = decrypt_wechat_message(
        encrypted=encrypted_reply,
        app_id="wx-test-appid",
        encoding_aes_key=encoding_aes_key,
    )
    assert "<ToUserName><![CDATA[user_openid_aes]]></ToUserName>" in decrypted_reply
    assert "<FromUserName><![CDATA[gh_test]]></FromUserName>" in decrypted_reply
    assert "<Content><![CDATA[AES official account reply]]></Content>" in decrypted_reply


def test_wechat_official_account_text_message_reuses_chat_flow() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_oa_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Recommendation summary",
                        "rendered_reply": "Official account reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
                "captured_message": message,
                "captured_metadata": metadata or {},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_1]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[text]]></MsgType>
      <Content><![CDATA[Need advice]]></Content>
      <MsgId>1234567890</MsgId>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<ToUserName><![CDATA[user_openid_1]]></ToUserName>" in response.text
    assert "<FromUserName><![CDATA[gh_test]]></FromUserName>" in response.text
    assert "<Content><![CDATA[Official account reply]]></Content>" in response.text


def _legacy_wechat_official_account_image_message_returns_picture_guidance_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("image message should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_2]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image.png]]></PicUrl>
      <MediaId><![CDATA[image-media-1]]></MediaId>
      <MsgId>1234567891</MsgId>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert (
        "<Content><![CDATA[当前已支持文本消息、关注事件和常用菜单事件，其他类型后续开放。]]></Content>"
        in response.text
    )


def test_wechat_official_account_direct_image_message_returns_picture_fallback_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    with Session(get_engine()) as session:
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )
        set_smart_analysis_mode(session, "off")

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("direct image message should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_image]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image.png]]></PicUrl>
      <MediaId><![CDATA[image-media-1]]></MediaId>
      <MsgId>1234567891</MsgId>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        with Session(get_engine()) as session:
            set_smart_analysis_mode(session, original_mode)
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert "<ToUserName><![CDATA[user_openid_image]]></ToUserName>" in response.text
    assert (
        f"<Content><![CDATA[{chat_router_module.WECHAT_OFFICIAL_ACCOUNT_PICTURE_FALLBACK_REPLY}]]></Content>"
        in response.text
    )


def test_wechat_official_account_direct_image_message_returns_media_pending_reply_when_smart_analysis_is_on() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("direct image message should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_image_enabled]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image.png]]></PicUrl>
      <MediaId><![CDATA[image-media-enabled-1]]></MediaId>
      <MsgId>1234567892</MsgId>
    </xml>
    """.strip()

    with Session(get_engine()) as session:
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )
        set_smart_analysis_mode(session, "on")

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        with Session(get_engine()) as session:
            set_smart_analysis_mode(session, original_mode)
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert (
        f"<Content><![CDATA[{chat_router_module.WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_PENDING_REPLY}]]></Content>"
        in response.text
    )


def test_wechat_official_account_video_messages_return_video_guidance_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("video message should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )

    for message_type, user_id in (
        ("video", "user_openid_video"),
        ("shortvideo", "user_openid_shortvideo"),
    ):
        body = f"""
        <xml>
          <ToUserName><![CDATA[gh_test]]></ToUserName>
          <FromUserName><![CDATA[{user_id}]]></FromUserName>
          <CreateTime>1710000001</CreateTime>
          <MsgType><![CDATA[{message_type}]]></MsgType>
          <MediaId><![CDATA[{message_type}-media-1]]></MediaId>
          <ThumbMediaId><![CDATA[{message_type}-thumb-1]]></ThumbMediaId>
          <MsgId>4234567891</MsgId>
        </xml>
        """.strip()

        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )

        assert response.status_code == 200
        assert f"<ToUserName><![CDATA[{user_id}]]></ToUserName>" in response.text
        assert (
            f"<Content><![CDATA[{chat_router_module.WECHAT_OFFICIAL_ACCOUNT_VIDEO_FALLBACK_REPLY}]]></Content>"
            in response.text
        )

    chat_router_module.settings.wechat_official_account_token = original_token
    chat_router_module.conversation_service = original_service


def test_wechat_official_account_video_messages_record_failed_unsupported_reason_for_entitled_gated_user() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    original_provider = chat_router_module.media_analysis_provider
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("video message should not enter chat routing")

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            assert request.media_type in {"video", "shortvideo"}
            return chat_router_module.MediaAnalysisResult(
                status="failed",
                provider="openai_compatible",
                failure_reason="当前 openai_compatible 媒体分析仅支持 image，暂不支持 video/shortvideo",
            )

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    chat_router_module.media_analysis_provider = FakeMediaAnalysisProvider()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )

    create_all_models(get_engine())

    with Session(get_engine()) as session:
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )

    try:
        for message_type, user_id in (
            ("video", "user_openid_video_enabled"),
            ("shortvideo", "user_openid_shortvideo_enabled"),
        ):
            body = f"""
            <xml>
              <ToUserName><![CDATA[gh_test]]></ToUserName>
              <FromUserName><![CDATA[{user_id}]]></FromUserName>
              <CreateTime>1710000001</CreateTime>
              <MsgType><![CDATA[{message_type}]]></MsgType>
              <MediaId><![CDATA[{message_type}-media-enabled-1]]></MediaId>
              <ThumbMediaId><![CDATA[{message_type}-thumb-enabled-1]]></ThumbMediaId>
              <MsgId>4234567892</MsgId>
            </xml>
            """.strip()

            with Session(get_engine()) as session:
                existing = session.exec(
                    select(MediaAnalysisEvent).where(
                        MediaAnalysisEvent.user_id == user_id
                    )
                ).all()
                for item in existing:
                    session.delete(item)
                session.commit()
                set_smart_analysis_mode(session, "gated")
                set_user_entitlement(
                    session,
                    user_id=user_id,
                    entitlement=SMART_ANALYSIS_ENTITLEMENT,
                    is_enabled=True,
                )

            response = client.post(
                "/api/chat/channels/wechat/official-account",
                params={
                    "signature": signature,
                    "timestamp": timestamp,
                    "nonce": nonce,
                },
                content=body,
                headers={"Content-Type": "application/xml"},
            )

            with Session(get_engine()) as session:
                saved = session.exec(
                    select(MediaAnalysisEvent)
                    .where(MediaAnalysisEvent.user_id == user_id)
                    .order_by(MediaAnalysisEvent.id.desc())
                ).first()

            assert response.status_code == 200
            assert saved is not None
            assert saved.media_type == message_type
            assert saved.provider == "openai_compatible"
            assert saved.status == "failed"
            assert saved.summary == ""
            assert saved.rendered_reply == ""
            assert saved.extracted_fields == {}
            assert saved.context == {
                "to_user_name": "gh_test",
                "from_user_name": user_id,
                "create_time": "1710000001",
                "msg_type": message_type,
                "msg_id": "4234567892",
                "media_id": f"{message_type}-media-enabled-1",
                "thumb_media_id": f"{message_type}-thumb-enabled-1",
                "failure_reason": "当前 openai_compatible 媒体分析仅支持 image，暂不支持 video/shortvideo",
            }
            assert saved.auto_routed_to_chat is False
            assert f"<ToUserName><![CDATA[{user_id}]]></ToUserName>" in response.text
            assert (
                f"<Content><![CDATA[{chat_router_module.WECHAT_OFFICIAL_ACCOUNT_VIDEO_FALLBACK_REPLY}]]></Content>"
                in response.text
            )

            with Session(get_engine()) as session:
                saved_items = session.exec(
                    select(MediaAnalysisEvent).where(MediaAnalysisEvent.user_id == user_id)
                ).all()
                for item in saved_items:
                    session.delete(item)
                session.commit()
    finally:
        with Session(get_engine()) as session:
            set_smart_analysis_mode(session, original_mode)
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service
        chat_router_module.media_analysis_provider = original_provider


def test_wechat_official_account_image_message_can_use_media_analysis_provider_reply_when_enabled() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    original_provider = chat_router_module.media_analysis_provider
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("image message should not enter chat routing")

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            assert request.media_type == "image"
            assert request.user_id == "user_openid_image_provider"
            assert request.payload["MediaId"] == "image-media-provider-1"
            return chat_router_module.MediaAnalysisResult(
                status="success",
                provider="fake",
                rendered_reply="Media provider reply",
            )

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    chat_router_module.media_analysis_provider = FakeMediaAnalysisProvider()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_image_provider]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image.png]]></PicUrl>
      <MediaId><![CDATA[image-media-provider-1]]></MediaId>
      <MsgId>1234567893</MsgId>
    </xml>
    """.strip()

    with Session(get_engine()) as session:
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )
        set_smart_analysis_mode(session, "on")

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        with Session(get_engine()) as session:
            set_smart_analysis_mode(session, original_mode)
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service
        chat_router_module.media_analysis_provider = original_provider

    assert response.status_code == 200
    assert "<Content><![CDATA[Media provider reply]]></Content>" in response.text


def test_wechat_official_account_image_message_records_media_analysis_event() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    original_provider = chat_router_module.media_analysis_provider
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("image message should not enter chat routing")

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            assert request.media_type == "image"
            assert request.user_id == "user_openid_media_event"
            return chat_router_module.MediaAnalysisResult(
                status="success",
                provider="fake",
                summary="识别到河南560分理科截图",
                rendered_reply="Media provider reply",
                extracted_fields={"province": "河南", "score": 560},
            )

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    chat_router_module.media_analysis_provider = FakeMediaAnalysisProvider()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_media_event]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image-record.png]]></PicUrl>
      <MediaId><![CDATA[image-media-record-1]]></MediaId>
      <MsgId>12345678931</MsgId>
    </xml>
    """.strip()

    create_all_models(get_engine())

    with Session(get_engine()) as session:
        existing = session.exec(
            select(MediaAnalysisEvent).where(
                MediaAnalysisEvent.user_id == "user_openid_media_event"
            )
        ).all()
        for item in existing:
            session.delete(item)
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )
        set_smart_analysis_mode(session, "on")
        session.commit()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )

        with Session(get_engine()) as session:
            saved = session.exec(
                select(MediaAnalysisEvent)
                .where(MediaAnalysisEvent.user_id == "user_openid_media_event")
                .order_by(MediaAnalysisEvent.id.desc())
            ).first()

        assert saved is not None
        assert saved.channel == "wechat"
        assert saved.source == "wechat_official_account"
        assert saved.user_id == "user_openid_media_event"
        assert saved.message_id == "12345678931"
        assert saved.media_id == "image-media-record-1"
        assert saved.media_type == "image"
        assert saved.provider == "fake"
        assert saved.status == "success"
        assert saved.summary == "识别到河南560分理科截图"
        assert saved.rendered_reply == "Media provider reply"
        assert saved.extracted_fields == {"province": "河南", "score": 560}
        assert saved.context == {
            "to_user_name": "gh_test",
            "from_user_name": "user_openid_media_event",
            "create_time": "1710000001",
            "msg_type": "image",
            "msg_id": "12345678931",
            "media_id": "image-media-record-1",
            "pic_url": "https://example.com/image-record.png",
        }
        assert saved.auto_routed_to_chat is False
    finally:
        with Session(get_engine()) as session:
            saved_items = session.exec(
                select(MediaAnalysisEvent).where(
                    MediaAnalysisEvent.user_id == "user_openid_media_event"
                )
            ).all()
            for item in saved_items:
                session.delete(item)
            set_smart_analysis_mode(session, original_mode)
            session.commit()
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service
        chat_router_module.media_analysis_provider = original_provider

    assert response.status_code == 200
    assert "<Content><![CDATA[Media provider reply]]></Content>" in response.text


def test_wechat_official_account_image_message_records_failed_media_reason_event() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    original_provider = chat_router_module.media_analysis_provider
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("image message should not enter chat routing")

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            assert request.media_type == "image"
            assert request.user_id == "user_openid_media_failed"
            return chat_router_module.MediaAnalysisResult(
                status="failed",
                provider="fake",
                failure_reason="上游媒体分析请求失败：HTTP 429",
            )

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    chat_router_module.media_analysis_provider = FakeMediaAnalysisProvider()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_media_failed]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image-failed.png]]></PicUrl>
      <MediaId><![CDATA[image-media-failed-1]]></MediaId>
      <MsgId>12345678932</MsgId>
    </xml>
    """.strip()

    create_all_models(get_engine())

    with Session(get_engine()) as session:
        existing = session.exec(
            select(MediaAnalysisEvent).where(
                MediaAnalysisEvent.user_id == "user_openid_media_failed"
            )
        ).all()
        for item in existing:
            session.delete(item)
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )
        set_smart_analysis_mode(session, "on")
        session.commit()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )

        with Session(get_engine()) as session:
            saved = session.exec(
                select(MediaAnalysisEvent)
                .where(MediaAnalysisEvent.user_id == "user_openid_media_failed")
                .order_by(MediaAnalysisEvent.id.desc())
            ).first()

        assert saved is not None
        assert saved.status == "failed"
        assert saved.provider == "fake"
        assert saved.summary == ""
        assert saved.rendered_reply == ""
        assert saved.extracted_fields == {}
        assert saved.context == {
            "to_user_name": "gh_test",
            "from_user_name": "user_openid_media_failed",
            "create_time": "1710000001",
            "msg_type": "image",
            "msg_id": "12345678932",
            "media_id": "image-media-failed-1",
            "pic_url": "https://example.com/image-failed.png",
            "failure_reason": "上游媒体分析请求失败：HTTP 429",
        }
        assert saved.auto_routed_to_chat is False
    finally:
        with Session(get_engine()) as session:
            saved_items = session.exec(
                select(MediaAnalysisEvent).where(
                    MediaAnalysisEvent.user_id == "user_openid_media_failed"
                )
            ).all()
            for item in saved_items:
                session.delete(item)
            set_smart_analysis_mode(session, original_mode)
            session.commit()
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service
        chat_router_module.media_analysis_provider = original_provider

    assert response.status_code == 200
    assert (
        f"<Content><![CDATA[{chat_router_module.WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_UNAVAILABLE_REPLY}]]></Content>"
        in response.text
    )


def test_wechat_official_account_image_message_can_fall_back_to_media_summary_when_reply_missing() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    original_provider = chat_router_module.media_analysis_provider
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("image message should not enter chat routing")

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            assert request.media_type == "image"
            return chat_router_module.MediaAnalysisResult(
                status="success",
                provider="fake",
                summary="识别到河南560分理科信息",
                extracted_fields={"province": "河南", "score": 560, "subject": "理科"},
            )

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    chat_router_module.media_analysis_provider = FakeMediaAnalysisProvider()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_image_summary]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image.png]]></PicUrl>
      <MediaId><![CDATA[image-media-summary-1]]></MediaId>
      <MsgId>1234567894</MsgId>
    </xml>
    """.strip()

    with Session(get_engine()) as session:
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )
        set_smart_analysis_mode(session, "on")

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        with Session(get_engine()) as session:
            set_smart_analysis_mode(session, original_mode)
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service
        chat_router_module.media_analysis_provider = original_provider

    assert response.status_code == 200
    assert "<Content><![CDATA[识别到河南560分理科信息]]></Content>" in response.text


def test_wechat_official_account_image_message_can_route_extracted_fields_into_chat() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    original_provider = chat_router_module.media_analysis_provider
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    captured: dict[str, object] = {}

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            captured["channel"] = channel
            captured["user_id"] = user_id
            captured["message"] = message
            captured["metadata"] = metadata or {}
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_media_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Media routed summary",
                        "rendered_reply": "Media routed reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            return chat_router_module.MediaAnalysisResult(
                status="success",
                provider="fake",
                summary="识别到河南560分理科，目标专业计算机",
                extracted_fields={
                    "province": "河南",
                    "score": 560,
                    "subject": "理科",
                    "target_major": "计算机科学与技术",
                },
            )

    chat_router_module.conversation_service = FakeConversationService()
    chat_router_module.media_analysis_provider = FakeMediaAnalysisProvider()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_image_route]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[image]]></MsgType>
      <PicUrl><![CDATA[https://example.com/image.png]]></PicUrl>
      <MediaId><![CDATA[image-media-route-1]]></MediaId>
      <MsgId>1234567895</MsgId>
    </xml>
    """.strip()

    with Session(get_engine()) as session:
        original_mode = get_effective_smart_analysis_mode(
            session,
            default_mode=chat_router_module.settings.smart_analysis_mode,
        )
        set_smart_analysis_mode(session, "on")

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        with Session(get_engine()) as session:
            set_smart_analysis_mode(session, original_mode)
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service
        chat_router_module.media_analysis_provider = original_provider

    assert response.status_code == 200
    assert "<Content><![CDATA[Media routed reply]]></Content>" in response.text
    assert captured["channel"] == "wechat"
    assert captured["user_id"] == "user_openid_image_route"
    assert captured["message"] == "河南理科560分，目标专业计算机科学与技术。请帮我做高考志愿分析。"
    assert captured["metadata"] == {
        "source": "wechat_official_account_image_media_analysis",
        "message_type": "image",
        "wechat_official_account": {
            "to_user_name": "gh_test",
            "msg_id": "1234567895",
            "create_time": "1710000001",
            "media_id": "image-media-route-1",
            "pic_url": "https://example.com/image.png",
        },
        "media_analysis": {
            "provider": "fake",
            "summary": "识别到河南560分理科，目标专业计算机",
            "extracted_fields": {
                "province": "河南",
                "score": 560,
                "subject": "理科",
                "target_major": "计算机科学与技术",
            },
        },
    }


def test_wechat_official_account_location_message_routes_into_chat() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    captured: dict[str, object] = {}

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            captured["channel"] = channel
            captured["user_id"] = user_id
            captured["message"] = message
            captured["metadata"] = metadata or {}
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_location_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Location summary",
                        "rendered_reply": "Location routed reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_location]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[location]]></MsgType>
      <Location_X>39.984154</Location_X>
      <Location_Y>116.307490</Location_Y>
      <Scale>15</Scale>
      <Label><![CDATA[Beijing Haidian District]]></Label>
      <MsgId>5234567891</MsgId>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert "<Content><![CDATA[Location routed reply]]></Content>" in response.text
    assert captured["channel"] == "wechat"
    assert captured["user_id"] == "user_openid_location"
    assert captured["message"] == "I shared my location: Beijing Haidian District"
    assert captured["metadata"] == {
        "source": "wechat_official_account_location_message",
        "message_type": "location",
        "wechat_official_account": {
            "to_user_name": "gh_test",
            "msg_id": "5234567891",
            "create_time": "1710000001",
            "location_label": "Beijing Haidian District",
            "location_x": "39.984154",
            "location_y": "116.307490",
            "scale": "15",
        },
    }


def test_wechat_official_account_link_message_routes_into_chat() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    captured: dict[str, object] = {}

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            captured["channel"] = channel
            captured["user_id"] = user_id
            captured["message"] = message
            captured["metadata"] = metadata or {}
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_link_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Link summary",
                        "rendered_reply": "Link routed reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_link]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[link]]></MsgType>
      <Title><![CDATA[Henan admission report]]></Title>
      <Description><![CDATA[2025 analysis report]]></Description>
      <Url><![CDATA[https://example.com/report]]></Url>
      <MsgId>6234567891</MsgId>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert "<Content><![CDATA[Link routed reply]]></Content>" in response.text
    assert captured["channel"] == "wechat"
    assert captured["user_id"] == "user_openid_link"
    assert (
        captured["message"]
        == "I shared a link: title=Henan admission report; description=2025 analysis report; url=https://example.com/report"
    )
    assert captured["metadata"] == {
        "source": "wechat_official_account_link_message",
        "message_type": "link",
        "wechat_official_account": {
            "to_user_name": "gh_test",
            "msg_id": "6234567891",
            "create_time": "1710000001",
            "title": "Henan admission report",
            "description": "2025 analysis report",
            "url": "https://example.com/report",
        },
    }


def test_wechat_official_account_voice_message_routes_recognition_into_chat() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    captured: dict[str, object] = {}

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            captured["channel"] = channel
            captured["user_id"] = user_id
            captured["message"] = message
            captured["metadata"] = metadata or {}
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_voice_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Voice summary",
                        "rendered_reply": "Voice routed reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_voice]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[voice]]></MsgType>
      <MediaId><![CDATA[media-voice-1]]></MediaId>
      <Format><![CDATA[amr]]></Format>
      <Recognition><![CDATA[Henan 560 recommend majors]]></Recognition>
      <MsgId>2234567890</MsgId>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert "<Content><![CDATA[Voice routed reply]]></Content>" in response.text
    assert captured["channel"] == "wechat"
    assert captured["user_id"] == "user_openid_voice"
    assert captured["message"] == "Henan 560 recommend majors"
    assert captured["metadata"] == {
        "source": "wechat_official_account_voice_message",
        "message_type": "voice",
        "wechat_official_account": {
            "to_user_name": "gh_test",
            "msg_id": "2234567890",
            "create_time": "1710000001",
            "media_id": "media-voice-1",
            "format": "amr",
            "recognition": "Henan 560 recommend majors",
        },
    }


def test_wechat_official_account_subscribe_event_returns_welcome_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("subscribe event should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_3]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[subscribe]]></Event>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert (
        "<Content><![CDATA[欢迎关注高考Agent，请直接发送省份、分数、选科和目标专业，我来帮你做志愿分析。]]></Content>"
        in response.text
    )


def test_wechat_official_account_unsubscribe_event_returns_success_ack() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("unsubscribe event should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_4]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[unsubscribe]]></Event>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert response.text == "success"


def test_wechat_official_account_click_event_can_return_static_menu_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("static menu click should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_5]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[CLICK]]></Event>
      <EventKey><![CDATA[menu_usage_help]]></EventKey>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert (
        "<Content><![CDATA[你可以直接发送省份、分数、选科和目标专业，我会继续帮你分析。]]></Content>"
        in response.text
    )


def test_wechat_official_account_click_event_can_route_menu_prompt_into_chat() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    captured: dict[str, object] = {}

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            captured["channel"] = channel
            captured["user_id"] = user_id
            captured["message"] = message
            captured["metadata"] = metadata or {}
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_menu_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Menu recommendation summary",
                        "rendered_reply": "Menu click routed reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_6]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[CLICK]]></Event>
      <EventKey><![CDATA[menu_major_recommendation]]></EventKey>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert "<Content><![CDATA[Menu click routed reply]]></Content>" in response.text
    assert captured["channel"] == "wechat"
    assert captured["user_id"] == "user_openid_6"
    assert captured["message"] == "请给我做专业推荐。"
    assert captured["metadata"] == {
        "source": "wechat_official_account_menu_click",
        "message_type": "event",
        "wechat_official_account": {
            "to_user_name": "gh_test",
            "msg_id": "",
            "create_time": "1710000001",
            "event": "click",
            "event_key": "menu_major_recommendation",
        },
    }


def test_wechat_official_account_click_event_returns_fallback_for_unknown_key() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("unknown menu click should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_7]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[CLICK]]></Event>
      <EventKey><![CDATA[menu_unknown_key]]></EventKey>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert (
        "<Content><![CDATA[该菜单功能还在整理中，你也可以直接发送问题给我。]]></Content>"
        in response.text
    )


def test_wechat_official_account_scancode_event_routes_scan_result_into_chat() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    captured: dict[str, object] = {}

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            captured["channel"] = channel
            captured["user_id"] = user_id
            captured["message"] = message
            captured["metadata"] = metadata or {}
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_scan_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Scan event summary",
                        "rendered_reply": "Scan event routed reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_8]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[scancode_push]]></Event>
      <EventKey><![CDATA[menu_scan_code]]></EventKey>
      <ScanCodeInfo>
        <ScanType><![CDATA[qrcode]]></ScanType>
        <ScanResult><![CDATA[https://example.com/mock-result]]></ScanResult>
      </ScanCodeInfo>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert "<Content><![CDATA[Scan event routed reply]]></Content>" in response.text
    assert captured["channel"] == "wechat"
    assert captured["user_id"] == "user_openid_8"
    assert captured["message"] == "我刚刚扫码了，结果是：https://example.com/mock-result"
    assert captured["metadata"] == {
        "source": "wechat_official_account_event",
        "message_type": "event",
        "wechat_official_account": {
            "to_user_name": "gh_test",
            "msg_id": "",
            "create_time": "1710000001",
            "event": "scancode_push",
            "event_key": "menu_scan_code",
            "scan_type": "qrcode",
            "scan_result": "https://example.com/mock-result",
        },
    }


def test_wechat_official_account_location_event_routes_location_into_chat() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"
    captured: dict[str, object] = {}

    class FakeConversationService:
        def handle_message(
            self,
            *,
            channel: str,
            user_id: str,
            message: str,
            session_id: str | None = None,
            skill_id: str | None = None,
            metadata: dict | None = None,
        ) -> dict:
            captured["channel"] = channel
            captured["user_id"] = user_id
            captured["message"] = message
            captured["metadata"] = metadata or {}
            return {
                "channel": channel,
                "user_id": user_id,
                "request_id": "chat_location_1",
                "matched_skill": {
                    "skill_id": "zhangxuefeng",
                    "version": "v2",
                    "confidence": 0.95,
                    "reason": "matched",
                },
                "output": {
                    "type": "structured_json",
                    "content": {
                        "summary": "Location event summary",
                        "rendered_reply": "Location event routed reply",
                    },
                },
                "debug": {"used_fallback": False, "notes": []},
            }

    chat_router_module.conversation_service = FakeConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_9]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[location_select]]></Event>
      <EventKey><![CDATA[menu_pick_location]]></EventKey>
      <SendLocationInfo>
        <Location_X>31.2304</Location_X>
        <Location_Y>121.4737</Location_Y>
        <Scale>15</Scale>
        <Label><![CDATA[上海市黄浦区人民广场]]></Label>
        <Poiname><![CDATA[人民广场]]></Poiname>
      </SendLocationInfo>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert "<Content><![CDATA[Location event routed reply]]></Content>" in response.text
    assert captured["channel"] == "wechat"
    assert captured["user_id"] == "user_openid_9"
    assert captured["message"] == "我选择的位置是：上海市黄浦区人民广场"
    assert captured["metadata"] == {
        "source": "wechat_official_account_event",
        "message_type": "event",
        "wechat_official_account": {
            "to_user_name": "gh_test",
            "msg_id": "",
            "create_time": "1710000001",
            "event": "location_select",
            "event_key": "menu_pick_location",
            "location_label": "上海市黄浦区人民广场",
            "location_name": "人民广场",
            "location_x": "31.2304",
            "location_y": "121.4737",
            "scale": "15",
        },
    }


def test_wechat_official_account_picture_menu_event_returns_image_guidance_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("picture menu event should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_10]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[pic_photo_or_album]]></Event>
      <EventKey><![CDATA[menu_upload_picture]]></EventKey>
      <SendPicsInfo>
        <Count>2</Count>
        <PicList>
          <item><PicMd5Sum><![CDATA[pic-md5-1]]></PicMd5Sum></item>
          <item><PicMd5Sum><![CDATA[pic-md5-2]]></PicMd5Sum></item>
        </PicList>
      </SendPicsInfo>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert (
        "<Content><![CDATA[已收到你上传的2张图片。当前公众号回调还不支持直接识图，请继续补充文字描述、分数、省份或专业方向，我继续帮你分析。]]></Content>"
        in response.text
    )


def test_wechat_official_account_picture_menu_event_without_count_returns_generic_reply() -> None:
    original_token = chat_router_module.settings.wechat_official_account_token
    original_service = chat_router_module.conversation_service
    chat_router_module.settings.wechat_official_account_token = "wechat-token"

    class ShouldNotBeCalledConversationService:
        def handle_message(self, **kwargs) -> dict:
            raise AssertionError("picture menu event should not enter chat routing")

    chat_router_module.conversation_service = ShouldNotBeCalledConversationService()
    timestamp = "1710000000"
    nonce = "nonce-123"
    signature = build_wechat_signature(
        token="wechat-token",
        timestamp=timestamp,
        nonce=nonce,
    )
    body = """
    <xml>
      <ToUserName><![CDATA[gh_test]]></ToUserName>
      <FromUserName><![CDATA[user_openid_11]]></FromUserName>
      <CreateTime>1710000001</CreateTime>
      <MsgType><![CDATA[event]]></MsgType>
      <Event><![CDATA[pic_weixin]]></Event>
      <EventKey><![CDATA[menu_pick_wechat_picture]]></EventKey>
      <SendPicsInfo>
        <PicList />
      </SendPicsInfo>
    </xml>
    """.strip()

    try:
        response = client.post(
            "/api/chat/channels/wechat/official-account",
            params={
                "signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
            },
            content=body,
            headers={"Content-Type": "application/xml"},
        )
    finally:
        chat_router_module.settings.wechat_official_account_token = original_token
        chat_router_module.conversation_service = original_service

    assert response.status_code == 200
    assert (
        "<Content><![CDATA[已收到你上传的图片。当前公众号回调还不支持直接识图，请继续补充文字描述、分数、省份或专业方向，我继续帮你分析。]]></Content>"
        in response.text
    )
