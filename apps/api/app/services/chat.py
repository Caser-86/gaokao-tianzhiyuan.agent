from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from sqlmodel import Session

from ..config import resolve_zhangxuefeng_skill_path, settings
from ..db import get_engine
from .access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    get_user_entitlements,
)
from .chat_sessions import ChatSessionStore
from .llm import OpenAICompatibleProvider, ProviderConfigurationError
from .skills import CatalogLookupSkill, ChatRequestContext, SkillRegistry, ZhangXueFengSkill
from .tracing import AgentTraceRecorder, TraceSink

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
                skill_prompt_path=resolve_zhangxuefeng_skill_path(settings.zhangxuefeng_skill_path),
            ),
            CatalogLookupSkill(),
        ]
    )


class ConversationService:
    def __init__(
        self,
        registry: SkillRegistry | None = None,
        threshold: float = ROUTING_THRESHOLD,
        session_factory: Callable[[], Session] | None = None,
        trace_sink: TraceSink | None = None,
    ) -> None:
        self.registry = registry or build_default_registry()
        self.threshold = threshold
        self.session_factory = session_factory or (lambda: Session(get_engine()))
        self.trace_sink = trace_sink
        self.session_store = ChatSessionStore(
            self.session_factory,
            retention_days=settings.chat_session_retention_days,
        )

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

    def get_session_messages(self, *, session_id: str, user_id: str) -> dict[str, Any]:
        return self.session_store.get_messages(
            session_id=session_id.strip(),
            user_id=user_id.strip(),
        )

    def delete_session(self, *, session_id: str, user_id: str) -> bool:
        return self.session_store.delete_session(
            session_id=session_id.strip(),
            user_id=user_id.strip(),
        )

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
        resolved_session_id = (session_id or "").strip() or f"session_{uuid4().hex[:12]}"
        request_id = f"chat_{uuid4().hex[:8]}"
        trace = AgentTraceRecorder(
            request_id=request_id,
            channel=channel,
            session_id=resolved_session_id,
            message_length=len(message.strip()),
            sink=self.trace_sink,
        )
        try:
            self.session_store.assert_access(
                session_id=resolved_session_id,
                user_id=user_id,
            )
            with self.session_factory() as session:
                persisted_mode = get_effective_smart_analysis_mode(
                    session,
                    default_mode=settings.smart_analysis_mode,
                )
                persisted_entitlements = get_user_entitlements(session, user_id)

            # Request metadata may describe the channel, but it is not an
            # authorization boundary. Policy keys are always overwritten by
            # values read from the server-side store.
            authoritative_metadata = {
                **incoming_metadata,
                "smart_analysis_mode": persisted_mode,
                "entitlements": persisted_entitlements,
            }
            smart_analysis_allowed, smart_analysis_reason = resolve_smart_analysis_decision(
                authoritative_metadata,
                default_mode=persisted_mode,
            )
            request = ChatRequestContext(
                channel=channel,
                user_id=user_id,
                message=message.strip(),
                session_id=resolved_session_id,
                metadata={
                    **authoritative_metadata,
                    "smart_analysis_allowed": smart_analysis_allowed,
                    "smart_analysis_reason": smart_analysis_reason,
                },
            )

            if skill_id:
                response = self._invoke_direct(
                    skill_id=skill_id,
                    request=request,
                    request_id=request_id,
                    trace=trace,
                )
            else:
                response = self._invoke_best_match(
                    request,
                    request_id=request_id,
                    trace=trace,
                )
            self.session_store.save_exchange(
                session_id=resolved_session_id,
                user_id=user_id,
                channel=channel,
                request_id=request_id,
                user_message=request.message,
                assistant_content=response["output"]["content"],
            )
            return response
        except Exception as exc:
            trace.emit(
                provider="none",
                model_called=False,
                used_fallback=True,
                fallback_reasons=[f"request_error:{type(exc).__name__}"],
            )
            raise

    def _invoke_direct(
        self,
        *,
        skill_id: str,
        request: ChatRequestContext,
        request_id: str,
        trace: AgentTraceRecorder,
    ) -> dict[str, Any]:
        skill = self.registry.get(skill_id)
        if skill is None:
            raise ChatSkillNotFoundError(skill_id)

        metadata = skill.describe()
        if not metadata.enabled or request.channel not in metadata.supports_channels:
            raise ChatSkillUnavailableError(skill_id)

        trace.add_candidate(
            skill_id=metadata.skill_id,
            version=metadata.version,
            prompt_hash=metadata.prompt_hash,
            matched=True,
            confidence=1.0,
            reason="direct skill invocation",
        )
        result = skill.invoke(request)
        return self._build_response(
            request=request,
            request_id=request_id,
            trace=trace,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": 1.0,
                "reason": "direct skill invocation",
            },
            content=result.as_content(),
            used_fallback=bool(result.debug_notes),
            debug_notes=result.debug_notes,
            provider=result.provider,
            model_called=result.model_called,
            prompt_hash=metadata.prompt_hash,
        )

    def _invoke_best_match(
        self,
        request: ChatRequestContext,
        *,
        request_id: str,
        trace: AgentTraceRecorder,
    ) -> dict[str, Any]:
        best_skill = None
        best_match = None

        for skill in self.registry.enabled_for_channel(request.channel):
            metadata = skill.describe()
            current_match = skill.match(request)
            trace.add_candidate(
                skill_id=metadata.skill_id,
                version=metadata.version,
                prompt_hash=metadata.prompt_hash,
                matched=current_match.matched,
                confidence=current_match.confidence,
                reason=current_match.reason,
            )
            if not current_match.matched:
                continue
            if best_match is None or current_match.confidence > best_match.confidence:
                best_skill = skill
                best_match = current_match

        if best_skill is None or best_match is None or best_match.confidence < self.threshold:
            return self._build_global_fallback_response(
                request,
                request_id=request_id,
                trace=trace,
            )

        metadata = best_skill.describe()
        result = best_skill.invoke(request)
        return self._build_response(
            request=request,
            request_id=request_id,
            trace=trace,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": best_match.confidence,
                "reason": best_match.reason,
            },
            content=result.as_content(),
            used_fallback=bool(result.debug_notes),
            debug_notes=result.debug_notes,
            provider=result.provider,
            model_called=result.model_called,
            prompt_hash=metadata.prompt_hash,
        )

    def _build_response(
        self,
        *,
        request: ChatRequestContext,
        request_id: str,
        trace: AgentTraceRecorder,
        matched_skill: dict[str, Any],
        content: dict[str, Any],
        used_fallback: bool,
        debug_notes: list[str],
        provider: str,
        model_called: bool,
        prompt_hash: str | None = None,
        trace_fallback_reasons: list[str] | None = None,
    ) -> dict[str, Any]:
        trace.select_skill(matched_skill, prompt_hash=prompt_hash)
        fallback_reasons = list(
            debug_notes if trace_fallback_reasons is None else trace_fallback_reasons
        )
        if used_fallback and not fallback_reasons:
            fallback_reasons.append("skill_fallback")
        trace.emit(
            provider=provider,
            model_called=model_called,
            used_fallback=used_fallback,
            fallback_reasons=fallback_reasons,
        )
        return {
            "request_id": request_id,
            "session_id": request.session_id,
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

    def _build_global_fallback_response(
        self,
        request: ChatRequestContext,
        *,
        request_id: str,
        trace: AgentTraceRecorder,
    ) -> dict[str, Any]:
        return self._build_response(
            request=request,
            request_id=request_id,
            trace=trace,
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
            provider="none",
            model_called=False,
            trace_fallback_reasons=["no_enabled_skill_above_threshold"],
        )
