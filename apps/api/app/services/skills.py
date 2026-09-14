from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import ValidationError
from sqlmodel import Session

from ..schemas.skill_output import SkillOutput
from .catalog import load_catalog
from .evidence import DEFAULT_MAX_CHARS, DEFAULT_MAX_ITEMS, EvidenceItem
from .llm import (
    LLMMessage,
    LLMProvider,
    ProviderRequestError,
    ProviderResponseFormatError,
)
from .prompt_assets import PromptSnapshot, load_prompt_snapshot

GAOKAO_KEYWORDS = ("学校", "专业", "志愿", "985", "211", "双一流", "冲", "稳", "保", "对比")
PROVINCES = ("北京", "上海", "江苏", "浙江", "广东", "四川", "湖北", "河南")
SCHOOL_TAGS = ("985", "211", "双一流")
SCHOOL_CONSULTATION_MARKERS = ("大学", "学院", "学校")
SCHOOL_CONSULTATION_QUESTIONS = (
    "怎么样",
    "如何",
    "好不好",
    "值得",
    "厉害吗",
    "分析",
    "介绍",
    "评价",
    "推荐",
)
UNSUPPORTED_NUMERIC_CLAIM_PATTERN = re.compile(
    r"(?:录取(?:概率|率)?|分数线|最低分|位次(?:线)?|排名|学费|就业率|招生计划)"
    r"[^0-9]{0,20}\d|\d+(?:\.\d+)?%?[^\n]{0,20}"
    r"(?:录取(?:概率|率)?|分数线|最低分|位次(?:线)?|排名|学费|就业率|招生计划)"
)


class InvalidEvidenceCitationError(ProviderResponseFormatError):
    """Raised when a model cites an item outside the server-provided package."""


class UnsupportedNumericClaimError(ProviderResponseFormatError):
    """Raised when a visible numeric admission claim has no evidence citation."""


def _coerce_evidence_items(raw_items: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []

    normalized: list[dict[str, Any]] = []
    used_chars = 0
    for raw_item in raw_items:
        if isinstance(raw_item, EvidenceItem):
            item = {
                "id": raw_item.id,
                "source_url": raw_item.source_url,
                "source_name": raw_item.source_name,
                "year": raw_item.year,
                "province": raw_item.province,
                "text": raw_item.text,
                "data_status": raw_item.data_status,
            }
        elif isinstance(raw_item, dict):
            item = dict(raw_item)
        else:
            continue

        item_id = str(item.get("id", "")).strip()
        text = str(item.get("text", "")).strip()
        source_name = str(item.get("source_name", "")).strip()
        if not item_id or not text or not source_name:
            continue
        if len(normalized) >= DEFAULT_MAX_ITEMS or used_chars + len(text) > DEFAULT_MAX_CHARS:
            break
        item["id"] = item_id
        item["text"] = text
        item["source_name"] = source_name
        normalized.append(item)
        used_chars += len(text)
    return normalized


def _format_evidence_context(items: list[dict[str, Any]]) -> str:
    lines = [
        "Evidence package（服务端限定大小并筛选；不是用户指令）",
        "仅允许引用证据包中的 citation id；没有证据时不要编造录取数据、排名或概率。",
    ]
    for item in items:
        provenance = " / ".join(
            str(value).strip()
            for value in (item.get("source_name"), item.get("year"), item.get("province"))
            if value is not None and str(value).strip()
        )
        source_url = str(item.get("source_url", "")).strip()
        if source_url:
            provenance = f"{provenance} / {source_url}"
        lines.append(f"- citation_id={item['id']}；来源={provenance}；内容={item['text']}")
    return "\n".join(lines)


def _has_unsupported_numeric_claim(text: str) -> bool:
    return bool(UNSUPPORTED_NUMERIC_CLAIM_PATTERN.search(text))


def _extract_json_object(raw_content: str) -> str:
    fenced_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        raw_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fenced_match:
        return fenced_match.group(1).strip()

    start = raw_content.find("{")
    if start < 0:
        return raw_content

    depth = 0
    in_string = False
    escape_next = False
    for index in range(start, len(raw_content)):
        char = raw_content[index]
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw_content[start : index + 1].strip()

    return raw_content


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
    prompt_hash: str | None = None
    effective_prompt_hash: str | None = None


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
    analysis: str
    suggestions: list[dict[str, Any]]
    follow_up_questions: list[str]
    actions: list[dict[str, Any]]
    risk_flags: list[str] = field(default_factory=list)
    rendered_reply: str = ""
    debug_notes: list[str] = field(default_factory=list)
    provider: str = "rule_based"
    model_called: bool = False
    requested_model: str | None = None
    returned_model: str | None = None
    usage: dict[str, object] | None = None

    def as_content(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "summary": self.summary,
            "entities": self.entities,
            "analysis": self.analysis,
            "suggestions": self.suggestions,
            "follow_up_questions": self.follow_up_questions,
            "actions": self.actions,
            "risk_flags": self.risk_flags,
            "rendered_reply": self.rendered_reply,
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


CATALOG_LOOKUP_HINTS = (
    "\u600e\u4e48\u6837",
    "\u4ecb\u7ecd",
    "\u8be6\u60c5",
    "\u4ec0\u4e48",
    "\u503c\u5f97",
    "\u9662\u6821",
    "\u4e13\u4e1a",
)


def _catalog_lookup_candidates(
    entity_key: str,
    *,
    session_factory: Callable[[], Session] | None = None,
) -> list[dict[str, Any]]:
    catalog = load_catalog(session_factory)
    entities = catalog.get(entity_key, [])
    return sorted(
        [item for item in entities if str(item.get("name", "")).strip()],
        key=lambda item: len(str(item["name"])),
        reverse=True,
    )


def _catalog_lookup_exact_message(message: str, name: str) -> bool:
    normalized_message = message.strip()
    normalized_name = name.strip()
    return bool(normalized_message and normalized_name and normalized_message == normalized_name)


def _catalog_lookup_has_hint(message: str) -> bool:
    return any(hint in message for hint in CATALOG_LOOKUP_HINTS)


def _resolve_catalog_lookup_entity(
    message: str,
    *,
    session_factory: Callable[[], Session] | None = None,
) -> tuple[str, dict[str, Any]] | None:
    for entity_key in ("majors", "schools"):
        for item in _catalog_lookup_candidates(entity_key, session_factory=session_factory):
            name = str(item.get("name", "")).strip()
            if not name or name not in message:
                continue
            if _catalog_lookup_exact_message(message, name) or _catalog_lookup_has_hint(message):
                entity_type = "major" if entity_key == "majors" else "school"
                return entity_type, item
    return None


def _build_catalog_lookup_related_suggestions(
    *,
    related_field: str,
    related_entity_key: str,
    suggestion_type: str,
    related_slugs: list[str],
    session_factory: Callable[[], Session] | None = None,
) -> list[dict[str, Any]]:
    catalog = load_catalog(session_factory)
    related_by_slug = {
        item["slug"]: item
        for item in catalog.get(related_entity_key, [])
        if str(item.get("slug", "")).strip()
    }
    suggestions: list[dict[str, Any]] = []
    for slug in related_slugs[:3]:
        item = related_by_slug.get(slug)
        if item is None:
            continue
        suggestions.append(
            {
                "type": suggestion_type,
                "title": str(item.get("name", "")).strip(),
                "slug": slug,
                related_field: slug,
            }
        )
    return suggestions


class CatalogLookupSkill:
    def __init__(self, *, session_factory: Callable[[], Session] | None = None) -> None:
        self.session_factory = session_factory

    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="catalog_lookup",
            name="Catalog Lookup",
            version="v1",
            description="Catalog-backed school and major lookup skill",
            enabled=True,
            supports_channels=("wechat", "web"),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        matched_entity = _resolve_catalog_lookup_entity(
            request.message,
            session_factory=self.session_factory,
        )
        if matched_entity is None:
            return SkillMatchResult(
                matched=False,
                confidence=0.0,
                reason="no catalog entity matched",
            )

        entity_type, item = matched_entity
        confidence = 0.88 if _catalog_lookup_has_hint(request.message) else 0.82
        return SkillMatchResult(
            matched=True,
            confidence=confidence,
            reason=f"matched {entity_type}: {item['slug']}",
        )

    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult:
        matched_entity = _resolve_catalog_lookup_entity(
            request.message,
            session_factory=self.session_factory,
        )
        if matched_entity is None:
            return SkillInvocationResult(
                intent="catalog_lookup_fallback",
                summary="\u672a\u547d\u4e2d\u9662\u6821\u6216\u4e13\u4e1a\u76ee\u5f55",
                entities={},
                analysis="\u8bf7\u76f4\u63a5\u53d1\u9001\u5b66\u6821\u540d\u6216\u4e13\u4e1a\u540d\uff0c\u6211\u53ef\u4ee5\u5148\u8fd4\u56de\u76ee\u5f55\u91cc\u7684\u57fa\u7840\u4fe1\u606f\u6458\u8981\u3002",
                suggestions=[],
                follow_up_questions=[
                    "\u4f60\u60f3\u67e5\u5b66\u6821\u8be6\u60c5\uff0c\u8fd8\u662f\u4e13\u4e1a\u4ecb\u7ecd\uff1f"
                ],
                actions=[],
                risk_flags=[],
                rendered_reply="\u8bf7\u76f4\u63a5\u53d1\u9001\u5b66\u6821\u540d\u6216\u4e13\u4e1a\u540d\uff0c\u6211\u53ef\u4ee5\u5148\u8fd4\u56de\u76ee\u5f55\u91cc\u7684\u57fa\u7840\u4fe1\u606f\u6458\u8981\u3002",
                debug_notes=["catalog_lookup_no_match"],
            )

        entity_type, item = matched_entity
        if entity_type == "school":
            return self._build_school_result(item)
        return self._build_major_result(item)

    def _build_school_result(self, item: dict[str, Any]) -> SkillInvocationResult:
        slug = str(item.get("slug", "")).strip()
        name = str(item.get("name", "")).strip()
        region = str(item.get("region", "")).strip()
        city = str(item.get("city", "")).strip()
        summary = str(item.get("summary", "")).strip()
        tags = [str(tag).strip() for tag in item.get("tags", []) if str(tag).strip()]
        suggestions = _build_catalog_lookup_related_suggestions(
            related_field="related_major_slug",
            related_entity_key="majors",
            suggestion_type="major",
            related_slugs=[
                str(related_slug).strip()
                for related_slug in item.get("related_majors", [])
                if str(related_slug).strip()
            ],
            session_factory=self.session_factory,
        )
        analysis_parts = []
        if region or city:
            analysis_parts.append(f"{region}{city}".strip())
        if tags:
            analysis_parts.append(" / ".join(tags))
        if summary:
            analysis_parts.append(summary)
        analysis = "；".join(part for part in analysis_parts if part)
        rendered_reply = f"{name}位于{region}{city}。{summary}".strip("。") + "。"

        return SkillInvocationResult(
            intent="catalog_lookup_school",
            summary=f"已命中院校：{name}",
            entities={
                "entity_type": "school",
                "slug": slug,
                "name": name,
                "region": region,
                "city": city,
            },
            analysis=analysis,
            suggestions=suggestions,
            follow_up_questions=(["想继续看这所学校相关专业的目录摘要吗？"] if suggestions else []),
            actions=[
                {
                    "type": "open_school",
                    "label": "查看院校详情",
                    "target": f"/schools/{slug}",
                }
            ],
            risk_flags=[],
            rendered_reply=rendered_reply,
        )

    def _build_major_result(self, item: dict[str, Any]) -> SkillInvocationResult:
        slug = str(item.get("slug", "")).strip()
        name = str(item.get("name", "")).strip()
        discipline = str(item.get("discipline", "")).strip()
        summary = str(item.get("summary", "")).strip()
        recommended_regions = [
            str(region).strip()
            for region in item.get("recommended_regions", [])
            if str(region).strip()
        ]
        suggestions = _build_catalog_lookup_related_suggestions(
            related_field="related_school_slug",
            related_entity_key="schools",
            suggestion_type="school",
            related_slugs=[
                str(related_slug).strip()
                for related_slug in item.get("related_schools", [])
                if str(related_slug).strip()
            ],
            session_factory=self.session_factory,
        )
        analysis_parts = []
        if discipline:
            analysis_parts.append(f"学科门类：{discipline}")
        if recommended_regions:
            analysis_parts.append(f"推荐区域：{' / '.join(recommended_regions)}")
        if summary:
            analysis_parts.append(summary)
        analysis = "；".join(part for part in analysis_parts if part)
        rendered_reply = f"{name}属于{discipline}。{summary}".strip("。") + "。"

        return SkillInvocationResult(
            intent="catalog_lookup_major",
            summary=f"已命中专业：{name}",
            entities={
                "entity_type": "major",
                "slug": slug,
                "name": name,
                "discipline": discipline,
            },
            analysis=analysis,
            suggestions=suggestions,
            follow_up_questions=(["想继续看这个专业可关联的院校吗？"] if suggestions else []),
            actions=[
                {
                    "type": "open_major",
                    "label": "查看专业详情",
                    "target": f"/majors/{slug}",
                }
            ],
            risk_flags=[],
            rendered_reply=rendered_reply,
        )


class ZhangXueFengSkill:
    def __init__(
        self,
        *,
        provider: LLMProvider | None = None,
        skill_prompt_path: str = "",
        prompt_snapshot: PromptSnapshot | None = None,
    ) -> None:
        self.provider = provider
        self.skill_prompt_path = skill_prompt_path
        self._prompt_snapshot = prompt_snapshot
        if self._prompt_snapshot is not None:
            self.skill_prompt_path = self._prompt_snapshot.path
        if self._prompt_snapshot is None and self.skill_prompt_path:
            try:
                self._prompt_snapshot = load_prompt_snapshot(self.skill_prompt_path)
            except (FileNotFoundError, OSError, UnicodeError):
                self._prompt_snapshot = None

    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="zhangxuefeng",
            name="张雪峰",
            version="v2",
            description="使用本地 SKILL.md 和模型中转的高考咨询 skill",
            enabled=True,
            supports_channels=("wechat", "web"),
            prompt_hash=(self._prompt_snapshot.asset_sha256 if self._prompt_snapshot else None),
            effective_prompt_hash=(
                self._prompt_snapshot.effective_sha256 if self._prompt_snapshot else None
            ),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        matched_keywords = [keyword for keyword in GAOKAO_KEYWORDS if keyword in request.message]
        if any(marker in request.message for marker in SCHOOL_CONSULTATION_MARKERS) and any(
            question in request.message for question in SCHOOL_CONSULTATION_QUESTIONS
        ):
            return SkillMatchResult(
                matched=True,
                confidence=0.75,
                reason="matched school pattern",
            )
        if not matched_keywords and re.search(r"\d{3}分", request.message):
            return SkillMatchResult(
                matched=True,
                confidence=0.7,
                reason="matched score pattern",
            )
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
        if request.metadata.get("smart_analysis_allowed") is False:
            reason = str(
                request.metadata.get(
                    "smart_analysis_reason",
                    "smart_analysis_disabled_globally",
                )
            )
            return self._rule_based_fallback(request, debug_note=reason)

        if self.provider and (self.skill_prompt_path or self._prompt_snapshot is not None):
            try:
                prompt_snapshot = self._get_prompt_snapshot()
                history_messages: list[LLMMessage] = []
                raw_history = request.metadata.get("conversation_history", [])
                if isinstance(raw_history, list):
                    for item in raw_history:
                        if not isinstance(item, dict):
                            continue
                        role = item.get("role")
                        content = item.get("content")
                        if role not in {"user", "assistant"}:
                            continue
                        if not isinstance(content, str) or not content.strip():
                            continue
                        history_messages.append(LLMMessage(role=role, content=content.strip()))
                evidence_items = _coerce_evidence_items(request.metadata.get("evidence_items", []))
                evidence_messages = (
                    [LLMMessage(role="system", content=_format_evidence_context(evidence_items))]
                    if evidence_items
                    else []
                )
                raw_content = self.provider.complete_text(
                    messages=[
                        LLMMessage(
                            role="system",
                            content=prompt_snapshot.system_text,
                        ),
                        *evidence_messages,
                        *history_messages,
                        LLMMessage(role="user", content=request.message),
                    ]
                )
                payload = self._parse_provider_payload(raw_content)
                payload = self._normalize_provider_payload(payload, request=request)
                validated_payload = SkillOutput.model_validate(payload)
                normalized_payload = validated_payload.model_dump()
                return SkillInvocationResult(
                    intent=normalized_payload["intent"],
                    summary=normalized_payload["summary"],
                    entities=normalized_payload["entities"],
                    analysis=normalized_payload["analysis"],
                    suggestions=normalized_payload["suggestions"],
                    follow_up_questions=normalized_payload["follow_up_questions"],
                    actions=normalized_payload["actions"],
                    risk_flags=normalized_payload["risk_flags"],
                    rendered_reply=normalized_payload["rendered_reply"],
                    provider="openai_compatible",
                    model_called=True,
                    requested_model=getattr(self.provider, "requested_model", None),
                    returned_model=getattr(self.provider, "returned_model", None),
                    usage=getattr(self.provider, "usage", None),
                )
            except (FileNotFoundError, OSError, UnicodeError):
                return self._rule_based_fallback(
                    request,
                    debug_note="skill_prompt_missing",
                    provider="openai_compatible" if self.provider else "rule_based",
                )
            except (json.JSONDecodeError, ValidationError):
                return self._rule_based_fallback(
                    request,
                    debug_note="provider_invalid_response",
                    provider="openai_compatible",
                    model_called=True,
                )
            except InvalidEvidenceCitationError:
                return self._rule_based_fallback(
                    request,
                    debug_note="provider_invalid_citation",
                    provider="openai_compatible",
                    model_called=True,
                )
            except UnsupportedNumericClaimError:
                return self._rule_based_fallback(
                    request,
                    debug_note="provider_unsupported_numeric_claim",
                    provider="openai_compatible",
                    model_called=True,
                )
            except KeyError:
                return self._rule_based_fallback(
                    request,
                    debug_note="provider_invalid_response",
                    provider="openai_compatible",
                    model_called=True,
                )
            except ProviderRequestError as exc:
                debug_note = (
                    "provider_insufficient_balance"
                    if exc.reason == "insufficient_balance"
                    else "provider_request_failed"
                )
                return self._rule_based_fallback(
                    request,
                    debug_note=debug_note,
                    provider="openai_compatible",
                    model_called=True,
                )
            except ProviderResponseFormatError:
                return self._rule_based_fallback(
                    request,
                    debug_note="provider_invalid_response",
                    provider="openai_compatible",
                    model_called=True,
                )

        if not self.skill_prompt_path:
            return self._rule_based_fallback(request, debug_note="skill_prompt_missing")
        return self._rule_based_fallback(request, debug_note="provider_not_configured")

    def _get_prompt_snapshot(self) -> PromptSnapshot:
        if self._prompt_snapshot is None:
            self._prompt_snapshot = load_prompt_snapshot(self.skill_prompt_path)
        return self._prompt_snapshot

    def _normalize_provider_payload(
        self,
        payload: dict[str, Any],
        *,
        request: ChatRequestContext,
    ) -> dict[str, Any]:
        fallback = self._rule_based_fallback(request, debug_note="provider_normalized_response")
        evidence_items = _coerce_evidence_items(request.metadata.get("evidence_items", []))
        evidence_ids = {item["id"] for item in evidence_items}
        raw_entities = payload.get("entities", fallback.entities)
        if isinstance(raw_entities, dict):
            entities = dict(raw_entities)
            raw_evidence_refs = entities.get("evidence_refs", [])
            if not isinstance(raw_evidence_refs, list) or not all(
                isinstance(item, str) and item.strip() for item in raw_evidence_refs
            ):
                raise InvalidEvidenceCitationError("evidence_refs must be a list of strings")
            if any(item not in evidence_ids for item in raw_evidence_refs):
                raise InvalidEvidenceCitationError("provider cited an unknown evidence item")
            if evidence_items:
                entities["evidence_refs"] = list(raw_evidence_refs)
                # Source metadata is attached by the server, never accepted
                # from the model, so a client can render an auditable citation.
                entities["evidence"] = evidence_items
            else:
                entities.pop("evidence", None)
        else:
            entities = raw_entities

        raw_suggestions = payload.get("suggestions", fallback.suggestions)
        if "suggestions" not in payload:
            suggestions = fallback.suggestions
        elif isinstance(raw_suggestions, list) and all(
            isinstance(item, dict) for item in raw_suggestions
        ):
            suggestions = raw_suggestions
        elif isinstance(raw_suggestions, list) and all(
            isinstance(item, str) for item in raw_suggestions
        ):
            suggestions = fallback.suggestions
        else:
            suggestions = raw_suggestions

        raw_follow_up_questions = payload.get("follow_up_questions")
        if raw_follow_up_questions is None:
            follow_up_questions = (
                raw_suggestions
                if isinstance(raw_suggestions, list)
                and all(isinstance(item, str) for item in raw_suggestions)
                else fallback.follow_up_questions
            )
        else:
            follow_up_questions = raw_follow_up_questions

        rendered_reply = (
            payload.get("rendered_reply") or payload.get("message") or fallback.rendered_reply
        )
        follow_up_text = "\n".join(
            str(item)
            for item in (follow_up_questions if isinstance(follow_up_questions, list) else [])
        )
        citation_refs = entities.get("evidence_refs", []) if isinstance(entities, dict) else []
        if (
            not citation_refs
            and isinstance(rendered_reply, str)
            and _has_unsupported_numeric_claim(f"{rendered_reply}\n{follow_up_text}")
        ):
            raise UnsupportedNumericClaimError(
                "provider returned a visible numeric admission claim without evidence"
            )

        return {
            "intent": payload.get("intent", fallback.intent),
            "summary": payload.get("summary", fallback.summary),
            "entities": entities,
            "analysis": payload.get("analysis") or payload.get("message") or fallback.analysis,
            "suggestions": suggestions,
            "follow_up_questions": follow_up_questions,
            "actions": payload.get("actions", fallback.actions),
            "risk_flags": payload.get("risk_flags", fallback.risk_flags),
            "rendered_reply": rendered_reply,
        }

    @staticmethod
    def _parse_provider_payload(raw_content: str) -> dict[str, Any]:
        payload = json.loads(_extract_json_object(raw_content))
        if not isinstance(payload, dict):
            raise ProviderResponseFormatError("provider returned non-object JSON")
        return payload

    def _rule_based_fallback(
        self,
        request: ChatRequestContext,
        *,
        debug_note: str,
        provider: str = "rule_based",
        model_called: bool = False,
    ) -> SkillInvocationResult:
        province = next((item for item in PROVINCES if item in request.message), None)
        school_tags = [tag for tag in SCHOOL_TAGS if tag in request.message]

        if "对比" in request.message:
            intent = "comparison"
            summary = "用户在咨询学校或专业对比"
        elif "专业" in request.message and "学校" not in request.message:
            intent = "major_recommendation"
            summary = "用户在咨询专业选择建议"
        elif (
            any(keyword in request.message for keyword in ("志愿", "稳", "保")) and not school_tags
        ):
            intent = "volunteer_strategy"
            summary = "用户在咨询志愿填报策略"
        else:
            intent = "school_recommendation"
            summary = (
                "用户在咨询江苏地区 985 冲刺建议"
                if province == "江苏" and "985" in school_tags
                else "用户在咨询学校推荐建议"
            )

        suggestions: list[dict[str, Any]] = []
        actions: list[dict[str, Any]] = []
        follow_up_questions: list[str] = []
        risk_flags: list[str] = []

        if intent == "school_recommendation" and province == "江苏" and "985" in school_tags:
            has_score_or_rank = bool(re.search(r"\d{3,4}\s*分", request.message)) or (
                "位次" in request.message and bool(re.search(r"\d+", request.message))
            )
            if has_score_or_rank:
                suggestions = [
                    {
                        "type": "school",
                        "title": "东南大学",
                        "slug": "southeast-university",
                        "reason": "属于 985，工科实力强，可作为待核验的比较对象",
                    }
                ]
                actions = [
                    {
                        "type": "open_school",
                        "label": "查看学校详情",
                        "target": "/schools/southeast-university",
                    }
                ]
            else:
                risk_flags = ["insufficient_candidate_context"]
                follow_up_questions = ["请补充高考分数或省内位次，以及目标专业方向。"]
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
            analysis="当前使用规则降级结果，建议补充省份、分数和专业意向。",
            suggestions=suggestions,
            follow_up_questions=follow_up_questions,
            actions=actions,
            risk_flags=risk_flags,
            rendered_reply=summary,
            debug_notes=[debug_note],
            provider=provider,
            model_called=model_called,
        )
