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
            suggestions=[],
            follow_up_questions=[],
            actions=[],
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
                "version": "v1",
                "enabled": True,
                "supports_channels": ["wechat", "web"],
                "description": "高考志愿、学校专业咨询的首期占位 skill",
            }
        ]
    }


def test_chat_messages_auto_matches_zhangxuefeng() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-123",
            "message": "帮我看看江苏适合冲哪些985",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "wechat"
    assert payload["user_id"] == "wx-openid-123"
    assert payload["matched_skill"] == {
        "skill_id": "zhangxuefeng",
        "version": "v1",
        "confidence": 0.92,
        "reason": "matched keyword: 985 / 冲",
    }
    assert payload["output"] == {
        "type": "structured_json",
        "content": {
            "intent": "school_recommendation",
            "summary": "用户在咨询江苏地区 985 冲刺建议",
            "entities": {
                "province": "江苏",
                "school_tags": ["985"],
                "score": None,
            },
            "suggestions": [
                {
                    "type": "school",
                    "title": "东南大学",
                    "slug": "southeast-university",
                    "reason": "属于 985，工科实力强，适合作为冲刺项",
                    "confidence": 0.81,
                }
            ],
            "follow_up_questions": [],
            "actions": [
                {
                    "type": "open_school",
                    "label": "查看学校详情",
                    "target": "/schools/southeast-university",
                }
            ],
        },
    }
    assert payload["debug"] == {"used_fallback": False, "notes": []}
    assert payload["request_id"].startswith("chat_")


def test_chat_messages_returns_fallback_for_unmatched_message() -> None:
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
        "suggestions": [],
        "follow_up_questions": ["你想查学校、专业，还是志愿填报建议？"],
        "actions": [],
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


def test_chat_skill_invoke_allows_direct_skill_call() -> None:
    response = client.post(
        "/api/chat/skills/zhangxuefeng/invoke",
        json={
            "channel": "web",
            "user_id": "user-1",
            "message": "江苏985怎么选",
            "metadata": {"source": "manual-debug"},
        },
    )

    assert response.status_code == 200
    assert response.json()["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert response.json()["output"]["type"] == "structured_json"
    assert response.json()["debug"] == {"used_fallback": False, "notes": []}


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


def test_chat_skill_invoke_returns_409_for_unsupported_channel(monkeypatch) -> None:
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
