from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

GAOKAO_KEYWORDS = ("学校", "专业", "志愿", "985", "211", "双一流", "冲", "稳", "保", "对比")
PROVINCES = ("北京", "上海", "江苏", "浙江", "广东", "四川", "湖北")
SCHOOL_TAGS = ("985", "211", "双一流")


@dataclass(frozen=True)
class ChatRequestContext:
    channel: str
    user_id: str
    message: str
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillMetadata:
    skill_id: str
    name: str
    version: str
    description: str
    enabled: bool = True
    supports_channels: tuple[str, ...] = ("wechat", "web")


@dataclass(frozen=True)
class SkillMatchResult:
    matched: bool
    confidence: float
    reason: str


@dataclass(frozen=True)
class SkillInvocationResult:
    intent: str
    summary: str
    entities: dict[str, Any]
    suggestions: list[dict[str, Any]]
    follow_up_questions: list[str]
    actions: list[dict[str, Any]]

    def as_content(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "summary": self.summary,
            "entities": self.entities,
            "suggestions": self.suggestions,
            "follow_up_questions": self.follow_up_questions,
            "actions": self.actions,
        }


class SkillHandler(Protocol):
    def describe(self) -> SkillMetadata: ...

    def match(self, request: ChatRequestContext) -> SkillMatchResult: ...

    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult: ...


class SkillRegistry:
    def __init__(self, skills: list[SkillHandler] | None = None) -> None:
        self._skills: dict[str, SkillHandler] = {}
        for skill in skills or []:
            self.register(skill)

    def register(self, skill: SkillHandler) -> None:
        self._skills[skill.describe().skill_id] = skill

    def list_skills(self) -> list[SkillMetadata]:
        return [skill.describe() for skill in self._skills.values()]

    def get(self, skill_id: str) -> SkillHandler | None:
        return self._skills.get(skill_id)

    def enabled_for_channel(self, channel: str) -> list[SkillHandler]:
        enabled: list[SkillHandler] = []
        for skill in self._skills.values():
            metadata = skill.describe()
            if metadata.enabled and channel in metadata.supports_channels:
                enabled.append(skill)
        return enabled


class ZhangXueFengSkill:
    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="zhangxuefeng",
            name="张雪峰",
            version="v1",
            description="高考志愿、学校专业咨询的首期占位 skill",
            enabled=True,
            supports_channels=("wechat", "web"),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        matched_keywords = [keyword for keyword in GAOKAO_KEYWORDS if keyword in request.message]
        if not matched_keywords:
            return SkillMatchResult(
                matched=False,
                confidence=0.0,
                reason="no gaokao keyword matched",
            )
        return SkillMatchResult(
            matched=True,
            confidence=0.92 if "985" in matched_keywords else 0.75,
            reason=f"matched keyword: {' / '.join(matched_keywords)}",
        )

    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult:
        province = next((item for item in PROVINCES if item in request.message), None)
        school_tags = [tag for tag in SCHOOL_TAGS if tag in request.message]

        if "对比" in request.message:
            intent = "comparison"
            summary = "用户在咨询学校或专业对比"
        elif "专业" in request.message and "学校" not in request.message:
            intent = "major_recommendation"
            summary = "用户在咨询专业选择建议"
        elif any(keyword in request.message for keyword in ("志愿", "稳", "保")) and not school_tags:
            intent = "volunteer_strategy"
            summary = "用户在咨询志愿填报策略"
        else:
            intent = "school_recommendation"
            if province == "江苏" and "985" in school_tags:
                summary = "用户在咨询江苏地区 985 冲刺建议"
            else:
                summary = "用户在咨询学校推荐建议"

        suggestions: list[dict[str, Any]] = []
        actions: list[dict[str, Any]] = []
        follow_up_questions: list[str] = []

        if intent == "school_recommendation" and province == "江苏" and "985" in school_tags:
            suggestions = [
                {
                    "type": "school",
                    "title": "东南大学",
                    "slug": "southeast-university",
                    "reason": "属于 985，工科实力强，适合作为冲刺项",
                    "confidence": 0.81,
                }
            ]
            actions = [
                {
                    "type": "open_school",
                    "label": "查看学校详情",
                    "target": "/schools/southeast-university",
                }
            ]
        elif province is None:
            follow_up_questions = ["你所在省份、分数和目标专业方向是什么？"]

        return SkillInvocationResult(
            intent=intent,
            summary=summary,
            entities={
                "province": province,
                "school_tags": school_tags,
                "score": None,
            },
            suggestions=suggestions,
            follow_up_questions=follow_up_questions,
            actions=actions,
        )
