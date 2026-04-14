from __future__ import annotations

from typing import Any
from uuid import uuid4

from .skills import ChatRequestContext, SkillRegistry, ZhangXueFengSkill

ROUTING_THRESHOLD = 0.6


class ChatSkillNotFoundError(LookupError):
    pass


class ChatSkillUnavailableError(RuntimeError):
    pass


def build_default_registry() -> SkillRegistry:
    return SkillRegistry([ZhangXueFengSkill()])


class ConversationService:
    def __init__(self, registry: SkillRegistry | None = None, threshold: float = ROUTING_THRESHOLD) -> None:
        self.registry = registry or build_default_registry()
        self.threshold = threshold

    def list_skills(self) -> list[dict[str, Any]]:
        return [
            {
                "skill_id": metadata.skill_id,
                "name": metadata.name,
                "version": metadata.version,
                "enabled": metadata.enabled,
                "supports_channels": list(metadata.supports_channels),
                "description": metadata.description,
            }
            for metadata in self.registry.list_skills()
        ]

    def handle_message(
        self,
        *,
        channel: str,
        user_id: str,
        message: str,
        session_id: str | None = None,
        skill_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = ChatRequestContext(
            channel=channel,
            user_id=user_id,
            message=message.strip(),
            session_id=session_id,
            metadata=metadata or {},
        )

        if skill_id:
            return self._invoke_direct(skill_id=skill_id, request=request)
        return self._invoke_best_match(request)

    def _invoke_direct(self, *, skill_id: str, request: ChatRequestContext) -> dict[str, Any]:
        skill = self.registry.get(skill_id)
        if skill is None:
            raise ChatSkillNotFoundError(skill_id)

        metadata = skill.describe()
        if not metadata.enabled or request.channel not in metadata.supports_channels:
            raise ChatSkillUnavailableError(skill_id)

        return self._build_response(
            request=request,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": 1.0,
                "reason": "direct skill invocation",
            },
            content=skill.invoke(request).as_content(),
            used_fallback=False,
        )

    def _invoke_best_match(self, request: ChatRequestContext) -> dict[str, Any]:
        best_skill = None
        best_match = None

        for skill in self.registry.enabled_for_channel(request.channel):
            current_match = skill.match(request)
            if not current_match.matched:
                continue
            if best_match is None or current_match.confidence > best_match.confidence:
                best_skill = skill
                best_match = current_match

        if best_skill is None or best_match is None or best_match.confidence < self.threshold:
            return self._build_fallback_response(request)

        metadata = best_skill.describe()
        return self._build_response(
            request=request,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": best_match.confidence,
                "reason": best_match.reason,
            },
            content=best_skill.invoke(request).as_content(),
            used_fallback=False,
        )

    def _build_response(
        self,
        *,
        request: ChatRequestContext,
        matched_skill: dict[str, Any],
        content: dict[str, Any],
        used_fallback: bool,
    ) -> dict[str, Any]:
        return {
            "request_id": f"chat_{uuid4().hex[:8]}",
            "channel": request.channel,
            "user_id": request.user_id,
            "matched_skill": matched_skill,
            "output": {
                "type": "structured_json",
                "content": content,
            },
            "debug": {
                "used_fallback": used_fallback,
                "notes": [],
            },
        }

    def _build_fallback_response(self, request: ChatRequestContext) -> dict[str, Any]:
        return self._build_response(
            request=request,
            matched_skill={
                "skill_id": "fallback",
                "version": "v1",
                "confidence": 0.0,
                "reason": "no enabled skill exceeded routing threshold",
            },
            content={
                "intent": "fallback",
                "summary": "当前没有命中明确技能",
                "entities": {},
                "suggestions": [],
                "follow_up_questions": ["你想查学校、专业，还是志愿填报建议？"],
                "actions": [],
            },
            used_fallback=True,
        )
