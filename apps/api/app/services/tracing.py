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
    model_called: bool
    duration_ms: float
    used_fallback: bool
    fallback_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
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
        }


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
        self._emitted = False

    def add_candidate(
        self,
        *,
        skill_id: str,
        version: str,
        prompt_hash: str | None = None,
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
        self._candidates.append(candidate)

    def select_skill(
        self,
        matched_skill: dict[str, Any],
        *,
        prompt_hash: str | None = None,
    ) -> None:
        self._selected_skill = {
            "skill_id": _safe_text(matched_skill.get("skill_id", ""), max_length=80),
            "version": _safe_text(matched_skill.get("version", ""), max_length=40),
            "confidence": float(matched_skill.get("confidence", 0.0)),
            "reason": _safe_text(matched_skill.get("reason", "")),
        }
        if prompt_hash:
            self._selected_skill["prompt_hash"] = _safe_text(prompt_hash, max_length=64)

    def emit(
        self,
        *,
        provider: str,
        model_called: bool,
        used_fallback: bool,
        fallback_reasons: list[str],
    ) -> None:
        if self._emitted:
            return
        self._emitted = True
        event = AgentTrace(
            schema_version="agent-trace.v1",
            request_id=self._request_id,
            channel=self._channel,
            session_ref=self._session_ref,
            message_length=self._message_length,
            candidates=tuple(dict(candidate) for candidate in self._candidates),
            selected_skill=(dict(self._selected_skill) if self._selected_skill else None),
            provider=_safe_text(provider, max_length=80),
            model_called=bool(model_called),
            duration_ms=round(max(0.0, (time.perf_counter() - self._started_at) * 1000), 2),
            used_fallback=bool(used_fallback),
            fallback_reasons=_unique_reasons(fallback_reasons),
        ).as_dict()
        try:
            self._sink(event)
        except Exception:  # pragma: no cover - protects the request path from observability errors
            _logger.exception("agent trace sink failed")
