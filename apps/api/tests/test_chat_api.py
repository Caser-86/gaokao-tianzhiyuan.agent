import json
from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat as chat_router_module
from app.services.chat import ConversationService
from app.services.skills import (
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
