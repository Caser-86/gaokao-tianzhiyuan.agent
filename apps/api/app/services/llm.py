from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Literal, Protocol

import httpx


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    def __init__(self, message: str, *, reason: str = "request_failed") -> None:
        super().__init__(message)
        self.reason = reason


class ProviderResponseFormatError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


class LLMProvider(Protocol):
    def complete_text(self, *, messages: list[LLMMessage]) -> str: ...


def _chat_completions_url(base_url: str) -> str:
    normalized_base_url = base_url.rstrip("/")
    if normalized_base_url.endswith(("/v1", "/v3")):
        return f"{normalized_base_url}/chat/completions"
    return f"{normalized_base_url}/v1/chat/completions"


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
        max_output_tokens: int = 0,
        max_retries: int = 1,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url or not api_key or not model:
            raise ProviderConfigurationError("missing openai-compatible provider config")
        self.base_url = normalized_base_url
        self.api_key = api_key
        self.model = model
        self.requested_model = model
        self.returned_model: str | None = None
        self.usage: dict[str, object] | None = None
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.max_retries = min(max(0, max_retries), 1)

    def complete_text(self, *, messages: list[LLMMessage]) -> str:
        self.returned_model = None
        self.usage = None
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        if self.max_output_tokens > 0:
            payload["max_tokens"] = self.max_output_tokens
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        deadline = monotonic() + self.timeout_seconds
        response = None
        for attempt in range(self.max_retries + 1):
            remaining_seconds = deadline - monotonic()
            if remaining_seconds <= 0:
                raise ProviderRequestError(
                    "openai-compatible provider request timed out",
                    reason="timeout",
                )
            try:
                with httpx.Client(timeout=remaining_seconds) as client:
                    response = client.post(
                        _chat_completions_url(self.base_url),
                        headers=headers,
                        json=payload,
                    )
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    continue

                reason = "request_failed"
                if status_code >= 500:
                    reason = "server_error"
                try:
                    error_payload = exc.response.json()
                    error_code = (
                        error_payload.get("code", "") if isinstance(error_payload, dict) else ""
                    )
                except (AttributeError, ValueError):
                    error_code = ""

                if isinstance(error_code, str) and error_code.upper() == "INSUFFICIENT_BALANCE":
                    reason = "insufficient_balance"

                raise ProviderRequestError(
                    "openai-compatible provider request failed",
                    reason=reason,
                ) from exc
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries and monotonic() < deadline:
                    continue
                raise ProviderRequestError(
                    "openai-compatible provider request timed out",
                    reason="timeout",
                ) from exc
            except httpx.HTTPError as exc:
                raise ProviderRequestError(
                    "openai-compatible provider request failed",
                    reason="request_failed",
                ) from exc

        if response is None:  # pragma: no cover - defensive guard for future retry changes
            raise ProviderRequestError("openai-compatible provider request failed")

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise ProviderResponseFormatError("provider returned invalid JSON envelope") from exc

        if not isinstance(response_payload, dict):
            raise ProviderResponseFormatError("provider response envelope must be an object")

        returned_model = response_payload.get("model")
        self.returned_model = (
            returned_model.strip()
            if isinstance(returned_model, str) and returned_model.strip()
            else None
        )
        usage = response_payload.get("usage")
        self.usage = dict(usage) if isinstance(usage, dict) else None

        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderResponseFormatError("provider response choices must be a non-empty list")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ProviderResponseFormatError("provider response choice must be an object")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ProviderResponseFormatError("provider response message must be an object")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseFormatError("provider returned no message content")
        return content
