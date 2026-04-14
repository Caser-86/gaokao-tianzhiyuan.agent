from dataclasses import dataclass

from app.services.skills import (
    ChatRequestContext,
    SkillInvocationResult,
    SkillMatchResult,
    SkillMetadata,
    SkillRegistry,
    ZhangXueFengSkill,
)


@dataclass(frozen=True)
class DisabledSkill:
    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="disabled-skill",
            name="Disabled Skill",
            version="v1",
            description="Disabled test skill",
            enabled=False,
            supports_channels=("wechat",),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        return SkillMatchResult(matched=True, confidence=1.0, reason="always matched")

    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult:
        return SkillInvocationResult(
            intent="fallback",
            summary="disabled",
            entities={},
            suggestions=[],
            follow_up_questions=[],
            actions=[],
        )


def test_skill_registry_lists_enabled_skills_for_supported_channel() -> None:
    registry = SkillRegistry([ZhangXueFengSkill(), DisabledSkill()])

    listed = registry.list_skills()
    enabled_for_wechat = registry.enabled_for_channel("wechat")
    enabled_for_web = registry.enabled_for_channel("web")

    assert [item.skill_id for item in listed] == ["zhangxuefeng", "disabled-skill"]
    assert [item.describe().skill_id for item in enabled_for_wechat] == ["zhangxuefeng"]
    assert [item.describe().skill_id for item in enabled_for_web] == ["zhangxuefeng"]


def test_zhangxuefeng_skill_matches_and_returns_structured_school_recommendation() -> None:
    skill = ZhangXueFengSkill()
    request = ChatRequestContext(
        channel="wechat",
        user_id="wx-openid-1",
        message="帮我看看江苏适合冲哪些985",
    )

    match = skill.match(request)
    result = skill.invoke(request)

    assert match.matched is True
    assert match.confidence >= 0.6
    assert "985" in match.reason
    assert result.intent == "school_recommendation"
    assert result.summary == "用户在咨询江苏地区 985 冲刺建议"
    assert result.entities == {
        "province": "江苏",
        "school_tags": ["985"],
        "score": None,
    }
    assert result.suggestions == [
        {
            "type": "school",
            "title": "东南大学",
            "slug": "southeast-university",
            "reason": "属于 985，工科实力强，适合作为冲刺项",
            "confidence": 0.81,
        }
    ]
    assert result.actions == [
        {
            "type": "open_school",
            "label": "查看学校详情",
            "target": "/schools/southeast-university",
        }
    ]


def test_zhangxuefeng_skill_returns_low_confidence_for_irrelevant_message() -> None:
    skill = ZhangXueFengSkill()
    request = ChatRequestContext(
        channel="wechat",
        user_id="wx-openid-2",
        message="今天天气怎么样",
    )

    match = skill.match(request)

    assert match == SkillMatchResult(
        matched=False,
        confidence=0.0,
        reason="no gaokao keyword matched",
    )
