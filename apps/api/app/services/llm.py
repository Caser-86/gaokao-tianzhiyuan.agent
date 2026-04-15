from __future__ import annotations

from dataclasses import dataclass
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


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url or not api_key or not model:
            raise ProviderConfigurationError("missing openai-compatible provider config")
        self.base_url = normalized_base_url
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete_text(self, *, messages: list[LLMMessage]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
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
            reason = "request_failed"
            try:
                error_code = exc.response.json().get("code", "")
            except ValueError:
                error_code = ""

            if isinstance(error_code, str) and error_code.upper() == "INSUFFICIENT_BALANCE":
                reason = "insufficient_balance"

            raise ProviderRequestError(
                "openai-compatible provider request failed",
                reason=reason,
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderRequestError(
                "openai-compatible provider request failed",
                reason="request_failed",
            ) from exc

        content = response.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseFormatError("provider returned no message content")
        return content
