import json
import logging
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat as chat_router_module
from app.services.llm import LLMMessage, OpenAICompatibleProvider, ProviderRequestError
from app.services.request_budget import (
    ModelConcurrencyLimitError,
    RequestBudget,
    RequestTimeoutError,
)


class StubResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "request failed",
                request=httpx.Request("POST", "https://relay.example/v1/chat/completions"),
                response=httpx.Response(self.status_code, json=self._payload),
            )

    def json(self) -> object:
        return self._payload


def test_request_budget_rejects_concurrent_work_without_running_callback() -> None:
    budget = RequestBudget(max_concurrent=1, rate_limit_requests=10, daily_request_budget=10)
    started = threading.Event()
    release = threading.Event()

    def slow_callback() -> str:
        started.set()
        release.wait(timeout=2)
        return "ok"

    worker_result: list[str] = []
    worker = threading.Thread(
        target=lambda: worker_result.append(
            budget.execute(
                slow_callback,
                client_ip="127.0.0.1",
                subject="user-1",
                timeout_seconds=2,
            )
        )
    )
    worker.start()
    assert started.wait(timeout=1)

    with pytest.raises(ModelConcurrencyLimitError):
        budget.execute(
            lambda: "must not run",
            client_ip="127.0.0.1",
            subject="user-2",
            timeout_seconds=1,
        )

    release.set()
    worker.join(timeout=2)
    assert worker_result == ["ok"]


def test_request_budget_times_out_without_waiting_for_callback() -> None:
    budget = RequestBudget(max_concurrent=1, rate_limit_requests=10, daily_request_budget=10)
    release = threading.Event()

    with pytest.raises(RequestTimeoutError):
        budget.execute(
            lambda: release.wait(timeout=2),
            client_ip="127.0.0.1",
            subject="user-1",
            timeout_seconds=0.01,
        )

    release.set()
    time.sleep(0.02)


def test_message_limit_rejects_before_conversation_service_is_called(monkeypatch) -> None:
    called = False

    class SpyService:
        def handle_message(self, **kwargs):
            nonlocal called
            called = True
            return {"ok": True}

    monkeypatch.setattr(chat_router_module, "conversation_service", SpyService())
    monkeypatch.setattr(
        chat_router_module,
        "request_budget",
        RequestBudget(max_concurrent=4, rate_limit_requests=10, daily_request_budget=10),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/messages",
            json={
                "channel": "web",
                "user_id": "user-long-message",
                "message": "x" * 4001,
            },
        )

    assert response.status_code == 422
    assert called is False


def test_rate_limit_rejects_without_calling_conversation_service(monkeypatch) -> None:
    calls = 0

    class SpyService:
        def handle_message(self, **kwargs):
            nonlocal calls
            calls += 1
            return {"ok": True}

    monkeypatch.setattr(chat_router_module, "conversation_service", SpyService())
    monkeypatch.setattr(
        chat_router_module,
        "request_budget",
        RequestBudget(
            max_concurrent=4,
            rate_limit_requests=1,
            rate_limit_window_seconds=60,
            daily_request_budget=10,
        ),
    )

    with TestClient(app) as client:
        first = client.post(
            "/api/chat/messages",
            json={"channel": "web", "user_id": "rate-user", "message": "hello"},
        )
        second = client.post(
            "/api/chat/messages",
            json={"channel": "web", "user_id": "rate-user", "message": "hello again"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "chat request rate limit exceeded"
    assert calls == 1


def test_daily_budget_is_global_across_anonymous_identities(monkeypatch) -> None:
    calls = 0

    class SpyService:
        def handle_message(self, **kwargs):
            nonlocal calls
            calls += 1
            return {"ok": True}

    monkeypatch.setattr(chat_router_module, "conversation_service", SpyService())
    monkeypatch.setattr(
        chat_router_module,
        "request_budget",
        RequestBudget(
            max_concurrent=4,
            rate_limit_requests=10,
            daily_request_budget=1,
        ),
    )

    with TestClient(app) as first_client:
        first = first_client.post(
            "/api/chat/messages",
            json={"channel": "web", "message": "anonymous one"},
        )
    with TestClient(app) as second_client:
        second = second_client.post(
            "/api/chat/messages",
            json={"channel": "web", "message": "anonymous two"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "daily chat request budget exhausted"
    assert calls == 1


def test_provider_retries_one_transient_server_error_and_preserves_usage(monkeypatch) -> None:
    responses = iter(
        [
            StubResponse({"error": "temporary"}, status_code=503),
            StubResponse(
                {
                    "model": "deepseek-v4-flash",
                    "usage": {"prompt_tokens": 11, "completion_tokens": 7},
                    "choices": [{"message": {"content": '{"summary":"ok"}'}}],
                }
            ),
        ]
    )

    def fake_post(self, url: str, *, headers: dict, json: dict) -> StubResponse:
        _ = (self, url, headers, json)
        return next(responses)

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    provider = OpenAICompatibleProvider(
        base_url="https://relay.example",
        api_key="secret-key",
        model="ark-code-latest",
        timeout_seconds=30,
        max_output_tokens=800,
    )

    assert provider.complete_text(messages=[LLMMessage(role="user", content="test")]) == (
        '{"summary":"ok"}'
    )
    assert provider.usage == {"prompt_tokens": 11, "completion_tokens": 7}


def test_provider_does_not_retry_non_transient_client_error(monkeypatch) -> None:
    calls = 0

    def fake_post(self, url: str, *, headers: dict, json: dict) -> StubResponse:
        nonlocal calls
        calls += 1
        return StubResponse({"error": "bad request"}, status_code=400)

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    provider = OpenAICompatibleProvider(
        base_url="https://relay.example",
        api_key="secret-key",
        model="ark-code-latest",
        timeout_seconds=30,
    )

    with pytest.raises(ProviderRequestError):
        provider.complete_text(messages=[LLMMessage(role="user", content="test")])

    assert calls == 1


def test_trace_contains_null_usage_when_provider_does_not_report_usage(tmp_path) -> None:
    from sqlmodel import Session, SQLModel, create_engine

    from app.services.access_control import set_smart_analysis_mode
    from app.services.chat import ConversationService
    from app.services.skills import SkillRegistry, ZhangXueFengSkill

    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("测试提示词", encoding="utf-8")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        set_smart_analysis_mode(session, "on")

    class Provider:
        requested_model = "ark-code-latest"
        returned_model = None
        usage = None

        def complete_text(self, *, messages: list) -> str:
            _ = messages
            return json.dumps(
                {
                    "intent": "fallback",
                    "summary": "ok",
                    "entities": {},
                    "analysis": "ok",
                    "suggestions": [],
                    "follow_up_questions": [],
                    "actions": [],
                    "risk_flags": [],
                    "rendered_reply": "ok",
                }
            )

    traces: list[dict] = []
    service = ConversationService(
        registry=SkillRegistry(
            [ZhangXueFengSkill(provider=Provider(), skill_prompt_path=str(skill_file))]
        ),
        session_factory=lambda: Session(engine),
        trace_sink=traces.append,
    )

    service.handle_message(
        channel="web",
        user_id="trace-user",
        message="河南560分想学专业",
        metadata={"smart_analysis_mode": "on"},
    )

    assert traces[0]["usage"] is None


def test_trace_is_emitted_after_persistence_and_marks_persistence_failure() -> None:
    from sqlalchemy.pool import StaticPool
    from sqlmodel import Session, SQLModel, create_engine

    from app.services.chat import ConversationService
    from app.services.skills import CatalogLookupSkill, SkillRegistry

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    trace_events: list[dict] = []
    persisted = False
    service = ConversationService(
        registry=SkillRegistry([CatalogLookupSkill()]),
        session_factory=lambda: Session(engine),
        trace_sink=trace_events.append,
    )
    original_save = service.session_store.save_exchange

    def save_and_mark(**kwargs):
        nonlocal persisted
        persisted = True
        return original_save(**kwargs)

    service.session_store.save_exchange = save_and_mark
    service.handle_message(channel="web", user_id="trace-save-user", message="今天天气怎么样")

    assert persisted is True
    assert len(trace_events) == 1

    failed_events: list[dict] = []
    failed_service = ConversationService(
        registry=SkillRegistry([CatalogLookupSkill()]),
        session_factory=lambda: Session(engine),
        trace_sink=failed_events.append,
    )

    def fail_save(**kwargs):
        _ = kwargs
        raise RuntimeError("database unavailable")

    failed_service.session_store.save_exchange = fail_save
    with pytest.raises(RuntimeError):
        failed_service.handle_message(
            channel="web",
            user_id="trace-failure-user",
            message="今天天气怎么样",
        )

    assert len(failed_events) == 1
    assert "request_error:RuntimeError" in failed_events[0]["fallback_reasons"]


def test_application_configures_agent_trace_logging() -> None:
    from app.main import configure_logging

    trace_logger = logging.getLogger("app.agent_trace")
    previous_level = trace_logger.level
    try:
        trace_logger.setLevel(logging.WARNING)
        configure_logging()
        assert trace_logger.level == logging.INFO
    finally:
        trace_logger.setLevel(previous_level)
