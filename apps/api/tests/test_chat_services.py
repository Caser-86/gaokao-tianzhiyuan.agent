from dataclasses import dataclass

from app.services.llm import ProviderRequestError
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
            analysis="",
            suggestions=[],
            follow_up_questions=[],
            actions=[],
            risk_flags=[],
            rendered_reply="",
        )


class FakeProvider:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages: list = []

    def complete_text(self, *, messages: list) -> str:
        self.messages = messages
        return self.content


class ExplodingProvider:
    def complete_text(self, *, messages: list) -> str:
        raise ProviderRequestError("relay unavailable")


def test_skill_registry_lists_enabled_skills_for_supported_channel(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    registry = SkillRegistry(
        [
            ZhangXueFengSkill(skill_prompt_path=str(skill_file)),
            DisabledSkill(),
        ]
    )

    listed = registry.list_skills()
    enabled_for_wechat = registry.enabled_for_channel("wechat")
    enabled_for_web = registry.enabled_for_channel("web")

    assert [item.skill_id for item in listed] == ["zhangxuefeng", "disabled-skill"]
    assert [item.describe().skill_id for item in enabled_for_wechat] == ["zhangxuefeng"]
    assert [item.describe().skill_id for item in enabled_for_web] == ["zhangxuefeng"]


def test_zhangxuefeng_skill_uses_provider_and_normalizes_json(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    provider = FakeProvider(
        '{"intent":"major_recommendation","summary":"建议避开金融","analysis":"普通家庭先看就业中位数","suggestions":[{"type":"major","title":"计算机科学与技术","reason":"可迁移能力更强"}],"follow_up_questions":["河南理科还是文科？"],"actions":[],"risk_flags":["financial_industry_competition"],"rendered_reply":"我跟你说，普通家庭别先冲金融。"}'
    )
    skill = ZhangXueFengSkill(
        provider=provider,
        skill_prompt_path=str(skill_file),
    )

    request = ChatRequestContext(
        channel="wechat",
        user_id="wx-openid-1",
        message="河南560分想学金融，靠谱吗？",
    )

    result = skill.invoke(request)

    assert result.intent == "major_recommendation"
    assert result.summary == "建议避开金融"
    assert result.analysis == "普通家庭先看就业中位数"
    assert result.risk_flags == ["financial_industry_competition"]
    assert result.rendered_reply == "我跟你说，普通家庭别先冲金融。"
    assert provider.messages[0].role == "system"
    assert "张雪峰测试提示词" in provider.messages[0].content
    assert "Return valid JSON only" in provider.messages[0].content


def test_zhangxuefeng_skill_falls_back_to_rule_based_response_on_provider_failure(
    tmp_path,
) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    skill = ZhangXueFengSkill(
        provider=ExplodingProvider(),
        skill_prompt_path=str(skill_file),
    )

    result = skill.invoke(
        ChatRequestContext(
            channel="wechat",
            user_id="wx-openid-1",
            message="帮我看看江苏适合冲哪些985",
        )
    )

    assert result.intent == "school_recommendation"
    assert result.summary == "用户在咨询江苏地区 985 冲刺建议"
    assert result.debug_notes == ["skill_provider_unavailable"]


def test_zhangxuefeng_skill_returns_low_confidence_for_irrelevant_message(
    tmp_path,
) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    skill = ZhangXueFengSkill(skill_prompt_path=str(skill_file))

    match = skill.match(
        ChatRequestContext(
            channel="wechat",
            user_id="wx-openid-2",
            message="今天天气怎么样",
        )
    )

    assert match == SkillMatchResult(
        matched=False,
        confidence=0.0,
        reason="no gaokao keyword matched",
    )
