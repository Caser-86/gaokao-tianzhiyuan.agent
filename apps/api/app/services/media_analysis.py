from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal, Protocol

import httpx
from sqlmodel import Session

from .access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    get_user_entitlements,
)


@dataclass(frozen=True)
class MediaAnalysisAccessDecision:
    enabled: bool
    mode: str
    has_entitlement: bool


@dataclass(frozen=True)
class MediaAnalysisRequest:
    media_type: Literal["image", "video", "shortvideo"]
    user_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class MediaAnalysisResult:
    status: Literal["pending", "success", "failed"]
    provider: str
    summary: str | None = None
    extracted_fields: dict[str, Any] | None = None
    rendered_reply: str | None = None
    failure_reason: str | None = None


class MediaAnalysisProvider(Protocol):
    def analyze(self, *, request: MediaAnalysisRequest) -> MediaAnalysisResult: ...


class PendingMediaAnalysisProvider:
    def __init__(self, *, provider_name: str = "pending") -> None:
        self.provider_name = provider_name

    def analyze(self, *, request: MediaAnalysisRequest) -> MediaAnalysisResult:
        _ = request
        return MediaAnalysisResult(status="pending", provider=self.provider_name)


class UnavailableMediaAnalysisProvider:
    def __init__(self, *, provider_name: str, failure_reason: str) -> None:
        self.provider_name = provider_name
        self.failure_reason = failure_reason

    def analyze(self, *, request: MediaAnalysisRequest) -> MediaAnalysisResult:
        _ = request
        return MediaAnalysisResult(
            status="failed",
            provider=self.provider_name,
            failure_reason=self.failure_reason,
        )


class OpenAICompatibleMediaAnalysisProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def analyze(self, *, request: MediaAnalysisRequest) -> MediaAnalysisResult:
        if request.media_type != "image":
            return MediaAnalysisResult(
                status="failed",
                provider="openai_compatible",
                failure_reason=(
                    "当前 openai_compatible 媒体分析仅支持 image，暂不支持 video/shortvideo"
                ),
            )

        image_url = str(request.payload.get("PicUrl", "")).strip()
        if not image_url:
            return MediaAnalysisResult(status="pending", provider="openai_compatible")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise Chinese gaokao admissions assistant. "
                        "Read the uploaded image if it contains score sheets, chat "
                        "screenshots, school tables, or major lists. Return valid "
                        "JSON only with keys: summary, extracted_fields, rendered_reply. "
                        "Use Chinese. summary should be short. extracted_fields should "
                        "contain only clearly supported fields from the image."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "请阅读这张用户上传的图片。如果图片包含高考分数、位次、学校、专业、"
                                "录取信息或志愿表，请先简要总结你能确认的信息，再提示用户补充继续分析所需的关键字段。"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                },
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return MediaAnalysisResult(
                status="failed",
                provider="openai_compatible",
                failure_reason=(f"上游媒体分析请求失败：HTTP {exc.response.status_code}"),
            )
        except httpx.HTTPError as exc:
            return MediaAnalysisResult(
                status="failed",
                provider="openai_compatible",
                failure_reason=f"上游媒体分析请求失败：{exc.__class__.__name__}",
            )

        return self._parse_result(response.json())

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        content = payload.get("choices", [{}])[0].get("message", {}).get("content")
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "text":
                    continue
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())
            return "\n".join(text_parts).strip()

        return ""

    @classmethod
    def _parse_result(cls, payload: dict[str, Any]) -> MediaAnalysisResult:
        content = cls._extract_text(payload)
        if not content:
            return MediaAnalysisResult(
                status="failed",
                provider="openai_compatible",
                failure_reason="上游媒体分析返回为空",
            )

        try:
            structured = json.loads(content)
        except json.JSONDecodeError:
            return MediaAnalysisResult(
                status="success",
                provider="openai_compatible",
                rendered_reply=content,
            )

        if not isinstance(structured, dict):
            return MediaAnalysisResult(
                status="success",
                provider="openai_compatible",
                rendered_reply=content,
            )

        summary = structured.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            summary = None
        else:
            summary = summary.strip()

        rendered_reply = structured.get("rendered_reply")
        if not isinstance(rendered_reply, str) or not rendered_reply.strip():
            rendered_reply = None
        else:
            rendered_reply = rendered_reply.strip()

        extracted_fields = structured.get("extracted_fields")
        if not isinstance(extracted_fields, dict):
            extracted_fields = {}

        if not rendered_reply and not summary:
            return MediaAnalysisResult(
                status="failed",
                provider="openai_compatible",
                failure_reason="上游媒体分析返回缺少 summary/rendered_reply",
            )

        return MediaAnalysisResult(
            status="success",
            provider="openai_compatible",
            summary=summary,
            extracted_fields=extracted_fields,
            rendered_reply=rendered_reply,
        )


def resolve_media_analysis_access(
    session: Session,
    *,
    user_id: str,
    default_mode: str,
) -> MediaAnalysisAccessDecision:
    mode = get_effective_smart_analysis_mode(session, default_mode=default_mode)
    if mode == "off":
        return MediaAnalysisAccessDecision(
            enabled=False,
            mode=mode,
            has_entitlement=False,
        )

    if mode == "on":
        return MediaAnalysisAccessDecision(
            enabled=True,
            mode=mode,
            has_entitlement=True,
        )

    entitlements = set(get_user_entitlements(session, user_id))
    has_entitlement = SMART_ANALYSIS_ENTITLEMENT in entitlements
    return MediaAnalysisAccessDecision(
        enabled=has_entitlement,
        mode=mode,
        has_entitlement=has_entitlement,
    )


def build_media_analysis_provider(
    *,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int = 30,
) -> MediaAnalysisProvider:
    normalized_provider = provider.strip().lower()
    if not normalized_provider or normalized_provider in {"pending", "noop", "none"}:
        return PendingMediaAnalysisProvider()

    if normalized_provider == "openai_compatible":
        if not base_url.strip() or not api_key.strip() or not model.strip():
            return UnavailableMediaAnalysisProvider(
                provider_name="openai_compatible",
                failure_reason=(
                    "当前 openai_compatible 媒体分析配置不完整，请检查 BASE_URL / API_KEY / MODEL"
                ),
            )
        return OpenAICompatibleMediaAnalysisProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    raise ValueError(
        "media_analysis_provider must be one of: '', pending, noop, none, openai_compatible"
    )
