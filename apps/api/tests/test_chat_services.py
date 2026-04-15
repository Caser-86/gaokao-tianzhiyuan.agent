from dataclasses import dataclass

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.services.access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    set_smart_analysis_mode,
    set_user_entitlement,
)

from app.services.chat import ConversationService
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


class EmptyBalanceProvider:
    def complete_text(self, *, messages: list) -> str:
        raise ProviderRequestError(
            "insufficient account balance",
            reason="insufficient_balance",
        )


def build_chat_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


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
    assert result.debug_notes == ["provider_request_failed"]


def test_zhangxuefeng_skill_marks_insufficient_balance_fallback(
    tmp_path,
) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("寮犻洩宄版祴璇曟彁绀鸿瘝", encoding="utf-8")
    skill = ZhangXueFengSkill(
        provider=EmptyBalanceProvider(),
        skill_prompt_path=str(skill_file),
    )

    result = skill.invoke(
        ChatRequestContext(
            channel="wechat",
            user_id="wx-openid-1",
            message="甯垜鐪嬬湅姹熻嫃閫傚悎鍐插摢浜?85",
        )
    )

    assert result.debug_notes == ["provider_insufficient_balance"]


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


def test_zhangxuefeng_skill_returns_policy_fallback_when_smart_analysis_disabled(
    tmp_path,
) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    provider = FakeProvider('{"intent":"major_recommendation","summary":"不应被调用"}')
    skill = ZhangXueFengSkill(
        provider=provider,
        skill_prompt_path=str(skill_file),
    )

    result = skill.invoke(
        ChatRequestContext(
            channel="wechat",
            user_id="wx-openid-1",
            message="河南560分想学金融，靠谱吗？",
            metadata={
                "smart_analysis_allowed": False,
                "smart_analysis_reason": "smart_analysis_disabled_globally",
            },
        )
    )

    assert result.debug_notes == ["smart_analysis_disabled_globally"]
    assert result.summary != "不应被调用"


def test_conversation_service_requires_smart_analysis_entitlement_when_gated(
    tmp_path,
) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    service = ConversationService(
        registry=SkillRegistry(
            [
                ZhangXueFengSkill(
                    provider=FakeProvider('{"intent":"major_recommendation","summary":"ok"}'),
                    skill_prompt_path=str(skill_file),
                )
            ]
        )
    )

    result = service.handle_message(
        channel="wechat",
        user_id="wx-openid-1",
        message="河南560分想学金融，靠谱吗？",
        metadata={
            "smart_analysis_mode": "gated",
            "entitlements": [],
        },
    )

    assert result["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert result["debug"] == {
        "used_fallback": True,
        "notes": ["smart_analysis_entitlement_required"],
    }


def test_conversation_service_allows_smart_analysis_when_gated_and_entitled(
    tmp_path,
) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    service = ConversationService(
        registry=SkillRegistry(
            [
                ZhangXueFengSkill(
                    provider=FakeProvider(
                        '{"intent":"major_recommendation","summary":"建议避开金融","analysis":"真实智能分析","suggestions":[],"follow_up_questions":[],"actions":[],"risk_flags":[],"rendered_reply":"智能分析已开启"}'
                    ),
                    skill_prompt_path=str(skill_file),
                )
            ]
        )
    )

    result = service.handle_message(
        channel="wechat",
        user_id="wx-openid-1",
        message="河南560分想学金融，靠谱吗？",
        metadata={
            "smart_analysis_mode": "gated",
            "entitlements": ["smart_analysis"],
        },
    )

    assert result["output"]["content"]["analysis"] == "真实智能分析"
    assert result["debug"] == {"used_fallback": False, "notes": []}


def test_conversation_service_uses_db_entitlement_when_mode_is_gated(
    tmp_path,
) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("寮犻洩宄版祴璇曟彁绀鸿瘝", encoding="utf-8")
    engine = build_chat_engine()
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        set_smart_analysis_mode(session, "gated")
        set_user_entitlement(
            session,
            user_id="wx-openid-db-1",
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=True,
        )

    service = ConversationService(
        registry=SkillRegistry(
            [
                ZhangXueFengSkill(
                    provider=FakeProvider(
                        '{"intent":"major_recommendation","summary":"寤鸿閬垮紑閲戣瀺","analysis":"鏁版嵁搴撴潈鐩婂凡鐢熸晥","suggestions":[],"follow_up_questions":[],"actions":[],"risk_flags":[],"rendered_reply":"ok"}'
                    ),
                    skill_prompt_path=str(skill_file),
                )
            ]
        ),
        session_factory=lambda: Session(engine),
    )

    result = service.handle_message(
        channel="wechat",
        user_id="wx-openid-db-1",
        message="娌冲崡560鍒嗘兂瀛﹂噾铻嶏紝闈犺氨鍚楋紵",
    )

    assert result["output"]["content"]["analysis"] == "鏁版嵁搴撴潈鐩婂凡鐢熸晥"
    assert result["debug"] == {"used_fallback": False, "notes": []}
