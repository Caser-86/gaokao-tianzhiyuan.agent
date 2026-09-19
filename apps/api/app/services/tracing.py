from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

TraceSink = Callable[[dict[str, Any]], None]

_logger = logging.getLogger("app.agent_trace")


def log_agent_trace(event: dict[str, Any]) -> None:
    """Write a structured trace without making tracing a request dependency."""
    _logger.info("agent_trace %s", json.dumps(event, ensure_ascii=False, sort_keys=True))


def _session_ref(session_id: str | None) -> str | None:
    if not session_id:
        return None
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]


def _safe_text(value: Any, *, max_length: int = 160) -> str:
    """Keep trace metadata bounded and free of line breaks."""
    return " ".join(str(value).split())[:max_length]


def _unique_reasons(reasons: list[str]) -> tuple[str, ...]:
    unique: list[str] = []
    for reason in reasons:
        normalized = _safe_text(reason)
        if normalized and normalized not in unique:
            unique.append(normalized)
    return tuple(unique)


def _safe_usage(usage: dict[str, Any] | None) -> dict[str, int | float] | None:
    """Keep only bounded numeric token counters supplied by a Provider."""
    if not isinstance(usage, dict):
        return None
    allowed_keys = {
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "input_tokens",
        "output_tokens",
        "prompt_cache_hit_tokens",
        "prompt_cache_miss_tokens",
    }
    safe: dict[str, int | float] = {}
    for key in allowed_keys:
        value = usage.get(key)
        if isinstance(value, int | float) and not isinstance(value, bool) and value >= 0:
            safe[key] = value
    return safe or None


@dataclass(frozen=True)
class AgentTrace:
    schema_version: str
    request_id: str
    channel: str
    session_ref: str | None
    message_length: int
    candidates: tuple[dict[str, Any], ...]
    selected_skill: dict[str, Any] | None
    provider: str
    requested_model: str | None
    returned_model: str | None
    model_called: bool
    duration_ms: float
    used_fallback: bool
    fallback_reasons: tuple[str, ...]
    usage: dict[str, int | float] | None

    def as_dict(self) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "channel": self.channel,
            "session_ref": self.session_ref,
            "message_length": self.message_length,
            "candidates": [dict(candidate) for candidate in self.candidates],
            "selected_skill": dict(self.selected_skill) if self.selected_skill else None,
            "provider": self.provider,
            "model_called": self.model_called,
            "duration_ms": self.duration_ms,
            "used_fallback": self.used_fallback,
            "fallback_reasons": list(self.fallback_reasons),
            "usage": self.usage,
        }
        if self.requested_model:
            result["requested_model"] = self.requested_model
        if self.returned_model:
            result["returned_model"] = self.returned_model
        return result


class AgentTraceRecorder:
    """Collect explainability metadata for one request and emit it once."""

    def __init__(
        self,
        *,
        request_id: str,
        channel: str,
        session_id: str | None,
        message_length: int,
        sink: TraceSink | None = None,
    ) -> None:
        self._request_id = request_id
        self._channel = _safe_text(channel, max_length=40)
        self._session_ref = _session_ref(session_id)
        self._message_length = max(0, int(message_length))
        self._sink = sink or log_agent_trace
        self._started_at = time.perf_counter()
        self._candidates: list[dict[str, Any]] = []
        self._selected_skill: dict[str, Any] | None = None
        self._outcome: dict[str, Any] | None = None
        self._emitted = False

    def add_candidate(
        self,
        *,
        skill_id: str,
        version: str,
        prompt_hash: str | None = None,
        effective_prompt_hash: str | None = None,
        matched: bool,
        confidence: float,
        reason: str,
    ) -> None:
        candidate = {
            "skill_id": _safe_text(skill_id, max_length=80),
            "version": _safe_text(version, max_length=40),
            "matched": bool(matched),
            "confidence": float(confidence),
            "reason": _safe_text(reason),
        }
        if prompt_hash:
            candidate["prompt_hash"] = _safe_text(prompt_hash, max_length=64)
        if effective_prompt_hash:
            candidate["effective_prompt_hash"] = _safe_text(
                effective_prompt_hash,
                max_length=64,
            )
        self._candidates.append(candidate)

    def select_skill(
        self,
        matched_skill: dict[str, Any],
        *,
        prompt_hash: str | None = None,
        effective_prompt_hash: str | None = None,
    ) -> None:
        self._selected_skill = {
            "skill_id": _safe_text(matched_skill.get("skill_id", ""), max_length=80),
            "version": _safe_text(matched_skill.get("version", ""), max_length=40),
            "confidence": float(matched_skill.get("confidence", 0.0)),
            "reason": _safe_text(matched_skill.get("reason", "")),
        }
        if prompt_hash:
            self._selected_skill["prompt_hash"] = _safe_text(prompt_hash, max_length=64)
        if effective_prompt_hash:
            self._selected_skill["effective_prompt_hash"] = _safe_text(
                effective_prompt_hash,
                max_length=64,
            )

    def set_outcome(
        self,
        *,
        provider: str,
        model_called: bool,
        requested_model: str | None = None,
        returned_model: str | None = None,
        usage: dict[str, Any] | None = None,
        used_fallback: bool,
        fallback_reasons: list[str],
    ) -> None:
        self._outcome = {
            "provider": provider,
            "model_called": model_called,
            "requested_model": requested_model,
            "returned_model": returned_model,
            "usage": usage,
            "used_fallback": used_fallback,
            "fallback_reasons": list(fallback_reasons),
        }

    def mark_failure(self, reason: str) -> None:
        if self._outcome is None:
            self.set_outcome(
                provider="none",
                model_called=False,
                used_fallback=True,
                fallback_reasons=[reason],
            )
            return
        self._outcome["used_fallback"] = True
        reasons = list(self._outcome["fallback_reasons"])
        if reason not in reasons:
            reasons.append(reason)
        self._outcome["fallback_reasons"] = reasons

    def emit(self) -> None:
        if self._emitted:
            return
        self._emitted = True
        outcome = self._outcome or {
            "provider": "none",
            "model_called": False,
            "requested_model": None,
            "returned_model": None,
            "usage": None,
            "used_fallback": True,
            "fallback_reasons": ["trace_without_outcome"],
        }
        event = AgentTrace(
            schema_version="agent-trace.v1",
            request_id=self._request_id,
            channel=self._channel,
            session_ref=self._session_ref,
            message_length=self._message_length,
            candidates=tuple(dict(candidate) for candidate in self._candidates),
            selected_skill=(dict(self._selected_skill) if self._selected_skill else None),
            provider=_safe_text(outcome["provider"], max_length=80),
            requested_model=(
                _safe_text(outcome["requested_model"], max_length=120)
                if outcome["requested_model"]
                else None
            ),
            returned_model=(
                _safe_text(outcome["returned_model"], max_length=120)
                if outcome["returned_model"]
                else None
            ),
            model_called=bool(outcome["model_called"]),
            duration_ms=round(max(0.0, (time.perf_counter() - self._started_at) * 1000), 2),
            used_fallback=bool(outcome["used_fallback"]),
            fallback_reasons=_unique_reasons(outcome["fallback_reasons"]),
            usage=_safe_usage(outcome["usage"]),
        ).as_dict()
        try:
            self._sink(event)
        except Exception:  # pragma: no cover - protects the request path from observability errors
            _logger.exception("agent trace sink failed")
