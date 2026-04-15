import httpx
import pytest

from app.services.llm import (
    LLMMessage,
    OpenAICompatibleProvider,
    ProviderRequestError,
    ProviderResponseFormatError,
)


class StubResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "request failed",
                request=httpx.Request("POST", "https://relay.example/v1/chat/completions"),
                response=httpx.Response(self.status_code, json=self._payload),
            )

    def json(self) -> dict:
        return self._payload


def test_openai_compatible_provider_posts_expected_payload(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(self, url: str, *, headers: dict, json: dict) -> StubResponse:
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return StubResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"intent":"major_recommendation","summary":"ok"}'
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    provider = OpenAICompatibleProvider(
        base_url="https://relay.example",
        api_key="secret-key",
        model="gpt-4o-mini",
        timeout_seconds=30,
    )

    result = provider.complete_text(
        messages=[
            LLMMessage(role="system", content="Return JSON only."),
            LLMMessage(role="user", content="帮我分析河南560分金融"),
        ]
    )

    assert result == '{"intent":"major_recommendation","summary":"ok"}'
    assert captured["url"] == "https://relay.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer secret-key"
    assert captured["json"]["model"] == "gpt-4o-mini"
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert captured["json"]["messages"][1]["content"] == "帮我分析河南560分金融"


def test_openai_compatible_provider_raises_request_error_on_transport_failure(
    monkeypatch,
) -> None:
    def fake_post(self, url: str, *, headers: dict, json: dict) -> StubResponse:
        raise httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    provider = OpenAICompatibleProvider(
        base_url="https://relay.example",
        api_key="secret-key",
        model="gpt-4o-mini",
        timeout_seconds=30,
    )

    with pytest.raises(ProviderRequestError):
        provider.complete_text(messages=[LLMMessage(role="user", content="test")])


def test_openai_compatible_provider_marks_insufficient_balance_errors(
    monkeypatch,
) -> None:
    def fake_post(self, url: str, *, headers: dict, json: dict) -> StubResponse:
        return StubResponse(
            {"code": "INSUFFICIENT_BALANCE", "message": "Insufficient account balance"},
            status_code=403,
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    provider = OpenAICompatibleProvider(
        base_url="https://relay.example",
        api_key="secret-key",
        model="gpt-4o-mini",
        timeout_seconds=30,
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        provider.complete_text(messages=[LLMMessage(role="user", content="test")])

    assert exc_info.value.reason == "insufficient_balance"


def test_openai_compatible_provider_raises_format_error_for_missing_message_content(
    monkeypatch,
) -> None:
    def fake_post(self, url: str, *, headers: dict, json: dict) -> StubResponse:
        return StubResponse({"choices": [{"message": {}}]})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    provider = OpenAICompatibleProvider(
        base_url="https://relay.example",
        api_key="secret-key",
        model="gpt-4o-mini",
        timeout_seconds=30,
    )

    with pytest.raises(ProviderResponseFormatError):
        provider.complete_text(messages=[LLMMessage(role="user", content="test")])
