from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from ..config import settings
from ..db import get_engine
from sqlmodel import Session
from .access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    get_user_entitlements,
)
from .llm import OpenAICompatibleProvider, ProviderConfigurationError
from .skills import ChatRequestContext, SkillRegistry, ZhangXueFengSkill

ROUTING_THRESHOLD = 0.6


class ChatSkillNotFoundError(LookupError):
    pass


class ChatSkillUnavailableError(RuntimeError):
    pass


def resolve_smart_analysis_decision(
    metadata: dict[str, Any] | None,
    *,
    default_mode: str,
) -> tuple[bool, str | None]:
    metadata = metadata or {}
    mode = str(metadata.get("smart_analysis_mode", default_mode)).strip().lower()
    entitlements = metadata.get("entitlements", [])
    if not isinstance(entitlements, list):
        entitlements = []

    if mode == "off":
        return False, "smart_analysis_disabled_globally"
    if mode == "gated" and SMART_ANALYSIS_ENTITLEMENT not in entitlements:
        return False, "smart_analysis_entitlement_required"
    return True, None


def build_default_registry() -> SkillRegistry:
    provider = None
    if settings.llm_provider == "openai_compatible":
        try:
            provider = OpenAICompatibleProvider(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_model,
                timeout_seconds=settings.llm_timeout_seconds,
            )
        except ProviderConfigurationError:
            provider = None

    return SkillRegistry(
        [
            ZhangXueFengSkill(
                provider=provider,
                skill_prompt_path=settings.zhangxuefeng_skill_path,
            )
        ]
    )


class ConversationService:
    def __init__(
        self,
        registry: SkillRegistry | None = None,
        threshold: float = ROUTING_THRESHOLD,
        session_factory: Callable[[], Session] | None = None,
    ) -> None:
        self.registry = registry or build_default_registry()
        self.threshold = threshold
        self.session_factory = session_factory or (lambda: Session(get_engine()))

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
        incoming_metadata = metadata or {}
        with self.session_factory() as session:
            persisted_mode = get_effective_smart_analysis_mode(
                session,
                default_mode=settings.smart_analysis_mode,
            )
            persisted_entitlements = get_user_entitlements(session, user_id)

        metadata_entitlements = (
            incoming_metadata.get("entitlements", [])
            if isinstance(incoming_metadata.get("entitlements"), list)
            else []
        )
        merged_metadata = {
            **incoming_metadata,
            "entitlements": sorted({*persisted_entitlements, *metadata_entitlements}),
        }
        smart_analysis_allowed, smart_analysis_reason = resolve_smart_analysis_decision(
            merged_metadata,
            default_mode=persisted_mode,
        )
        request = ChatRequestContext(
            channel=channel,
            user_id=user_id,
            message=message.strip(),
            session_id=session_id,
            metadata={
                **merged_metadata,
                "smart_analysis_allowed": smart_analysis_allowed,
                "smart_analysis_reason": smart_analysis_reason,
            },
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

        result = skill.invoke(request)
        return self._build_response(
            request=request,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": 1.0,
                "reason": "direct skill invocation",
            },
            content=result.as_content(),
            used_fallback=bool(result.debug_notes),
            debug_notes=result.debug_notes,
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
            return self._build_global_fallback_response(request)

        metadata = best_skill.describe()
        result = best_skill.invoke(request)
        return self._build_response(
            request=request,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": best_match.confidence,
                "reason": best_match.reason,
            },
            content=result.as_content(),
            used_fallback=bool(result.debug_notes),
            debug_notes=result.debug_notes,
        )

    def _build_response(
        self,
        *,
        request: ChatRequestContext,
        matched_skill: dict[str, Any],
        content: dict[str, Any],
        used_fallback: bool,
        debug_notes: list[str],
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
                "notes": debug_notes,
            },
        }

    def _build_global_fallback_response(self, request: ChatRequestContext) -> dict[str, Any]:
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
                "analysis": "当前使用全局回退，请补充学校、专业或志愿填报需求。",
                "suggestions": [],
                "follow_up_questions": ["你想查学校、专业，还是志愿填报建议？"],
                "actions": [],
                "risk_flags": [],
                "rendered_reply": "你想查学校、专业，还是志愿填报建议？",
            },
            used_fallback=True,
            debug_notes=[],
        )
