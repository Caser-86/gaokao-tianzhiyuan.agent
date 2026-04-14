# Chat Skill Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-pass API chat gateway with a reusable skill registry, a rule-based `zhangxuefeng` placeholder skill, a unified message API, and a JSON-only WeChat adapter path.

**Architecture:** Keep the first implementation API-only and stateless. Add a dedicated chat router that delegates to a `ConversationService`, which in turn uses an in-memory `SkillRegistry` and the first built-in `zhangxuefeng` skill handler. Keep channel adaptation outside the core routing path by translating WeChat-shaped payloads into the same internal request contract used by the unified message endpoint.

**Tech Stack:** FastAPI, Pydantic, Python dataclasses/protocols, pytest, FastAPI `TestClient`

---

## File Map

- Create: `apps/api/app/routers/chat.py`
  - Chat request/response models and `/api/chat/*` routes
- Create: `apps/api/app/services/skills.py`
  - Shared chat request/result dataclasses, `SkillRegistry`, `SkillHandler` protocol, and `ZhangXueFengSkill`
- Create: `apps/api/app/services/chat.py`
  - `ConversationService`, fallback generation, and default registry builder
- Modify: `apps/api/app/main.py`
  - Register the new chat router
- Modify: `apps/api/app/services/__init__.py`
  - Export the new chat service modules in the services namespace
- Create: `apps/api/tests/test_chat_services.py`
  - Unit tests for the registry and `zhangxuefeng` skill behavior
- Create: `apps/api/tests/test_chat_api.py`
  - Router tests for message routing, direct invocation, fallback behavior, skill listing, health, and WeChat normalization

### Task 1: Add the skill registry and `zhangxuefeng` placeholder skill

**Files:**
- Create: `apps/api/app/services/skills.py`
- Create: `apps/api/tests/test_chat_services.py`

- [ ] **Step 1: Write the failing skill service tests**

Create `apps/api/tests/test_chat_services.py` with:

```python
from dataclasses import dataclass

from app.services.skills import (
    ChatRequestContext,
    SkillMatchResult,
    SkillMetadata,
    SkillRegistry,
    SkillInvocationResult,
    ZhangXueFengSkill,
)


@dataclass(frozen=True)
class DisabledSkill:
    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="disabled-skill",
            name="Disabled Skill",
            version="v1",
            description="Disabled test skill",
            enabled=False,
            supports_channels=("wechat",),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        return SkillMatchResult(matched=True, confidence=1.0, reason="always matched")

    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult:
        return SkillInvocationResult(
            intent="fallback",
            summary="disabled",
            entities={},
            suggestions=[],
            follow_up_questions=[],
            actions=[],
        )


def test_skill_registry_lists_enabled_skills_for_supported_channel() -> None:
    registry = SkillRegistry([ZhangXueFengSkill(), DisabledSkill()])

    listed = registry.list_skills()
    enabled_for_wechat = registry.enabled_for_channel("wechat")
    enabled_for_web = registry.enabled_for_channel("web")

    assert [item.skill_id for item in listed] == ["zhangxuefeng", "disabled-skill"]
    assert [item.describe().skill_id for item in enabled_for_wechat] == ["zhangxuefeng"]
    assert [item.describe().skill_id for item in enabled_for_web] == ["zhangxuefeng"]


def test_zhangxuefeng_skill_matches_and_returns_structured_school_recommendation() -> None:
    skill = ZhangXueFengSkill()
    request = ChatRequestContext(
        channel="wechat",
        user_id="wx-openid-1",
        message="帮我看看江苏适合冲哪些985",
    )

    match = skill.match(request)
    result = skill.invoke(request)

    assert match.matched is True
    assert match.confidence >= 0.6
    assert "985" in match.reason
    assert result.intent == "school_recommendation"
    assert result.summary == "用户在咨询江苏地区 985 冲刺建议"
    assert result.entities == {
        "province": "江苏",
        "school_tags": ["985"],
        "score": None,
    }
    assert result.suggestions == [
        {
            "type": "school",
            "title": "东南大学",
            "slug": "southeast-university",
            "reason": "属于 985，工科实力强，适合作为冲刺项",
            "confidence": 0.81,
        }
    ]
    assert result.actions == [
        {
            "type": "open_school",
            "label": "查看学校详情",
            "target": "/schools/southeast-university",
        }
    ]


def test_zhangxuefeng_skill_returns_low_confidence_for_irrelevant_message() -> None:
    skill = ZhangXueFengSkill()
    request = ChatRequestContext(
        channel="wechat",
        user_id="wx-openid-2",
        message="今天天气怎么样",
    )

    match = skill.match(request)

    assert match == SkillMatchResult(
        matched=False,
        confidence=0.0,
        reason="no gaokao keyword matched",
    )
```

- [ ] **Step 2: Run the skill tests to verify failure**

Run:

```powershell
python -m pytest tests/test_chat_services.py -v
```

Expected: FAIL because `app.services.skills` and the skill/registry types do not exist yet.

- [ ] **Step 3: Write the minimal registry and skill implementation**

Create `apps/api/app/services/skills.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


GAOKAO_KEYWORDS = ("学校", "专业", "志愿", "985", "211", "双一流", "冲", "稳", "保", "对比")
PROVINCES = ("北京", "上海", "江苏", "浙江", "广东", "四川", "湖北")
SCHOOL_TAGS = ("985", "211", "双一流")


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
    suggestions: list[dict[str, Any]]
    follow_up_questions: list[str]
    actions: list[dict[str, Any]]

    def as_content(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "summary": self.summary,
            "entities": self.entities,
            "suggestions": self.suggestions,
            "follow_up_questions": self.follow_up_questions,
            "actions": self.actions,
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


class ZhangXueFengSkill:
    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="zhangxuefeng",
            name="张雪峰",
            version="v1",
            description="高考志愿、学校专业咨询的首期占位 skill",
            enabled=True,
            supports_channels=("wechat", "web"),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        matched_keywords = [keyword for keyword in GAOKAO_KEYWORDS if keyword in request.message]
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
        province = next((item for item in PROVINCES if item in request.message), None)
        school_tags = [tag for tag in SCHOOL_TAGS if tag in request.message]

        if "对比" in request.message:
            intent = "comparison"
            summary = "用户在咨询学校或专业对比"
        elif "专业" in request.message and "学校" not in request.message:
            intent = "major_recommendation"
            summary = "用户在咨询专业选择建议"
        elif any(keyword in request.message for keyword in ("志愿", "稳", "保")) and not school_tags:
            intent = "volunteer_strategy"
            summary = "用户在咨询志愿填报策略"
        else:
            intent = "school_recommendation"
            if province == "江苏" and "985" in school_tags:
                summary = "用户在咨询江苏地区 985 冲刺建议"
            else:
                summary = "用户在咨询学校推荐建议"

        suggestions: list[dict[str, Any]] = []
        actions: list[dict[str, Any]] = []
        follow_up_questions: list[str] = []

        if intent == "school_recommendation" and province == "江苏" and "985" in school_tags:
            suggestions = [
                {
                    "type": "school",
                    "title": "东南大学",
                    "slug": "southeast-university",
                    "reason": "属于 985，工科实力强，适合作为冲刺项",
                    "confidence": 0.81,
                }
            ]
            actions = [
                {
                    "type": "open_school",
                    "label": "查看学校详情",
                    "target": "/schools/southeast-university",
                }
            ]
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
            suggestions=suggestions,
            follow_up_questions=follow_up_questions,
            actions=actions,
        )
```

- [ ] **Step 4: Run the skill tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_chat_services.py -v
```

Expected: PASS with the registry filtering and `zhangxuefeng` matching tests green.

- [ ] **Step 5: Commit the skill registry changes**

```powershell
git add apps/api/app/services/skills.py apps/api/tests/test_chat_services.py
git commit -m "feat(api): add chat skill registry"
```

### Task 2: Add the unified chat gateway routes and conversation service

**Files:**
- Create: `apps/api/app/services/chat.py`
- Create: `apps/api/app/routers/chat.py`
- Create: `apps/api/tests/test_chat_api.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/services/__init__.py`

- [ ] **Step 1: Write the failing chat API tests**

Create `apps/api/tests/test_chat_api.py` with:

```python
from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat as chat_router_module
from app.services.chat import ConversationService
from app.services.skills import (
    ChatRequestContext,
    SkillInvocationResult,
    SkillMatchResult,
    SkillMetadata,
    SkillRegistry,
)

client = TestClient(app)


@dataclass(frozen=True)
class WebOnlySkill:
    def describe(self) -> SkillMetadata:
        return SkillMetadata(
            skill_id="web-only-skill",
            name="Web Only Skill",
            version="v1",
            description="Direct invoke availability test skill",
            enabled=True,
            supports_channels=("web",),
        )

    def match(self, request: ChatRequestContext) -> SkillMatchResult:
        return SkillMatchResult(matched=True, confidence=1.0, reason="always matched")

    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult:
        return SkillInvocationResult(
            intent="fallback",
            summary="web-only",
            entities={},
            suggestions=[],
            follow_up_questions=[],
            actions=[],
        )


def test_chat_health_returns_ok() -> None:
    response = client.get("/api/chat/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_skills_lists_registered_skills() -> None:
    response = client.get("/api/chat/skills")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "skill_id": "zhangxuefeng",
                "name": "张雪峰",
                "version": "v1",
                "enabled": True,
                "supports_channels": ["wechat", "web"],
                "description": "高考志愿、学校专业咨询的首期占位 skill",
            }
        ]
    }


def test_chat_messages_auto_matches_zhangxuefeng() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-123",
            "message": "帮我看看江苏适合冲哪些985",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "wechat"
    assert payload["user_id"] == "wx-openid-123"
    assert payload["matched_skill"] == {
        "skill_id": "zhangxuefeng",
        "version": "v1",
        "confidence": 0.92,
        "reason": "matched keyword: 985 / 冲",
    }
    assert payload["output"] == {
        "type": "structured_json",
        "content": {
            "intent": "school_recommendation",
            "summary": "用户在咨询江苏地区 985 冲刺建议",
            "entities": {
                "province": "江苏",
                "school_tags": ["985"],
                "score": None,
            },
            "suggestions": [
                {
                    "type": "school",
                    "title": "东南大学",
                    "slug": "southeast-university",
                    "reason": "属于 985，工科实力强，适合作为冲刺项",
                    "confidence": 0.81,
                }
            ],
            "follow_up_questions": [],
            "actions": [
                {
                    "type": "open_school",
                    "label": "查看学校详情",
                    "target": "/schools/southeast-university",
                }
            ],
        },
    }
    assert payload["debug"] == {"used_fallback": False, "notes": []}
    assert payload["request_id"].startswith("chat_")


def test_chat_messages_returns_fallback_for_unmatched_message() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-456",
            "message": "今天天气怎么样",
        },
    )

    assert response.status_code == 200
    assert response.json()["matched_skill"] == {
        "skill_id": "fallback",
        "version": "v1",
        "confidence": 0.0,
        "reason": "no enabled skill exceeded routing threshold",
    }
    assert response.json()["output"]["content"] == {
        "intent": "fallback",
        "summary": "当前没有命中明确技能",
        "entities": {},
        "suggestions": [],
        "follow_up_questions": ["你想查学校、专业，还是志愿填报建议？"],
        "actions": [],
    }
    assert response.json()["debug"] == {"used_fallback": True, "notes": []}


def test_chat_messages_rejects_invalid_channel() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "sms",
            "user_id": "wx-openid-789",
            "message": "帮我查学校",
        },
    )

    assert response.status_code == 422


def test_chat_skill_invoke_allows_direct_skill_call() -> None:
    response = client.post(
        "/api/chat/skills/zhangxuefeng/invoke",
        json={
            "channel": "web",
            "user_id": "user-1",
            "message": "江苏985怎么选",
            "metadata": {"source": "manual-debug"},
        },
    )

    assert response.status_code == 200
    assert response.json()["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert response.json()["output"]["type"] == "structured_json"
    assert response.json()["debug"] == {"used_fallback": False, "notes": []}


def test_chat_skill_invoke_returns_404_for_unknown_skill() -> None:
    response = client.post(
        "/api/chat/skills/missing-skill/invoke",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-999",
            "message": "帮我查学校",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "chat skill not found"}


def test_chat_skill_invoke_returns_409_for_unsupported_channel(monkeypatch) -> None:
    original_service = chat_router_module.conversation_service
    chat_router_module.conversation_service = ConversationService(
        registry=SkillRegistry([WebOnlySkill()])
    )

    try:
        response = client.post(
            "/api/chat/skills/web-only-skill/invoke",
            json={
                "channel": "wechat",
                "user_id": "wx-openid-unsupported",
                "message": "帮我查学校",
            },
        )
    finally:
        chat_router_module.conversation_service = original_service

    assert response.status_code == 409
    assert response.json() == {"detail": "chat skill unavailable"}
```

- [ ] **Step 2: Run the chat API tests to verify failure**

Run:

```powershell
python -m pytest tests/test_chat_api.py -v
```

Expected: FAIL because `/api/chat/*` routes and the conversation service do not exist yet.

- [ ] **Step 3: Write the minimal chat service and router implementation**

Create `apps/api/app/services/chat.py` with:

```python
from __future__ import annotations

from typing import Any
from uuid import uuid4

from .skills import ChatRequestContext, SkillRegistry, ZhangXueFengSkill


ROUTING_THRESHOLD = 0.6


class ChatSkillNotFoundError(LookupError):
    pass


class ChatSkillUnavailableError(RuntimeError):
    pass


def build_default_registry() -> SkillRegistry:
    return SkillRegistry([ZhangXueFengSkill()])


class ConversationService:
    def __init__(self, registry: SkillRegistry | None = None, threshold: float = ROUTING_THRESHOLD) -> None:
        self.registry = registry or build_default_registry()
        self.threshold = threshold

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
        request = ChatRequestContext(
            channel=channel,
            user_id=user_id,
            message=message.strip(),
            session_id=session_id,
            metadata=metadata or {},
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

        return self._build_success_response(
            request=request,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": 1.0,
                "reason": "direct skill invocation",
            },
            content=skill.invoke(request).as_content(),
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
            return self._build_fallback_response(request)

        metadata = best_skill.describe()
        return self._build_success_response(
            request=request,
            matched_skill={
                "skill_id": metadata.skill_id,
                "version": metadata.version,
                "confidence": best_match.confidence,
                "reason": best_match.reason,
            },
            content=best_skill.invoke(request).as_content(),
        )

    def _build_success_response(
        self,
        *,
        request: ChatRequestContext,
        matched_skill: dict[str, Any],
        content: dict[str, Any],
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
                "used_fallback": False,
                "notes": [],
            },
        }

    def _build_fallback_response(self, request: ChatRequestContext) -> dict[str, Any]:
        return {
            "request_id": f"chat_{uuid4().hex[:8]}",
            "channel": request.channel,
            "user_id": request.user_id,
            "matched_skill": {
                "skill_id": "fallback",
                "version": "v1",
                "confidence": 0.0,
                "reason": "no enabled skill exceeded routing threshold",
            },
            "output": {
                "type": "structured_json",
                "content": {
                    "intent": "fallback",
                    "summary": "当前没有命中明确技能",
                    "entities": {},
                    "suggestions": [],
                    "follow_up_questions": ["你想查学校、专业，还是志愿填报建议？"],
                    "actions": [],
                },
            },
            "debug": {
                "used_fallback": True,
                "notes": [],
            },
        }
```

Create `apps/api/app/routers/chat.py` with:

```python
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..services.chat import (
    ChatSkillNotFoundError,
    ChatSkillUnavailableError,
    ConversationService,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])
conversation_service = ConversationService()


class ChatMessageRequest(BaseModel):
    channel: Literal["wechat", "web"]
    user_id: str
    message: str
    session_id: str | None = None
    skill_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_id", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


class DirectSkillInvokeRequest(BaseModel):
    channel: Literal["wechat", "web"]
    user_id: str
    message: str
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_id", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


@router.get("/health")
def chat_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/skills")
def list_chat_skills() -> dict[str, list[dict[str, Any]]]:
    return {"items": conversation_service.list_skills()}


@router.post("/messages")
def create_chat_message(payload: ChatMessageRequest) -> dict[str, Any]:
    try:
        return conversation_service.handle_message(
            channel=payload.channel,
            user_id=payload.user_id,
            message=payload.message,
            session_id=payload.session_id,
            skill_id=payload.skill_id,
            metadata=payload.metadata,
        )
    except ChatSkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail="chat skill not found") from exc
    except ChatSkillUnavailableError as exc:
        raise HTTPException(status_code=409, detail="chat skill unavailable") from exc


@router.post("/skills/{skill_id}/invoke")
def invoke_chat_skill(skill_id: str, payload: DirectSkillInvokeRequest) -> dict[str, Any]:
    try:
        return conversation_service.handle_message(
            channel=payload.channel,
            user_id=payload.user_id,
            message=payload.message,
            session_id=payload.session_id,
            skill_id=skill_id,
            metadata=payload.metadata,
        )
    except ChatSkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail="chat skill not found") from exc
    except ChatSkillUnavailableError as exc:
        raise HTTPException(status_code=409, detail="chat skill unavailable") from exc
```

Modify `apps/api/app/main.py`:

```python
from .routers.chat import router as chat_router

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(admin_router)
app.include_router(platform_router)
app.include_router(public_router)
app.include_router(chat_router)
```

Modify `apps/api/app/services/__init__.py`:

```python
"""Application services namespace."""

from . import chat, featured_content, skills

__all__ = ["chat", "featured_content", "skills"]
```

- [ ] **Step 4: Run the chat API tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_chat_api.py -v
```

Expected: PASS with health, skills listing, unified message routing, fallback, direct invocation, unknown skill handling, and unavailable skill handling tests green.

- [ ] **Step 5: Commit the chat gateway core**

```powershell
git add apps/api/app/services/chat.py apps/api/app/routers/chat.py apps/api/app/main.py apps/api/app/services/__init__.py apps/api/tests/test_chat_api.py
git commit -m "feat(api): add chat gateway routes"
```

### Task 3: Add the WeChat adapter endpoint and run full API verification

**Files:**
- Modify: `apps/api/app/routers/chat.py`
- Modify: `apps/api/tests/test_chat_api.py`

- [ ] **Step 1: Add failing WeChat adapter tests**

Append these tests to `apps/api/tests/test_chat_api.py`:

```python
def test_wechat_chat_adapter_normalizes_payload_and_reuses_chat_flow() -> None:
    response = client.post(
        "/api/chat/channels/wechat",
        json={
            "openid": "wx-adapter-1",
            "message": "帮我看看江苏适合冲哪些985",
            "message_type": "text",
            "metadata": {"source": "official_account"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "wechat"
    assert payload["user_id"] == "wx-adapter-1"
    assert payload["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert payload["output"]["content"]["intent"] == "school_recommendation"


def test_wechat_chat_adapter_requires_openid_and_message() -> None:
    response = client.post(
        "/api/chat/channels/wechat",
        json={
            "openid": "",
            "message": "",
            "message_type": "text",
        },
    )

    assert response.status_code == 422
```

- [ ] **Step 2: Run the chat API tests to verify adapter failure**

Run:

```powershell
python -m pytest tests/test_chat_api.py -v
```

Expected: FAIL because `/api/chat/channels/wechat` does not exist yet.

- [ ] **Step 3: Add the minimal WeChat adapter implementation**

Modify `apps/api/app/routers/chat.py` to add:

```python
class WeChatChannelRequest(BaseModel):
    openid: str
    message: str
    message_type: str = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("openid", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


@router.post("/channels/wechat")
def create_wechat_chat_message(payload: WeChatChannelRequest) -> dict[str, Any]:
    try:
        return conversation_service.handle_message(
            channel="wechat",
            user_id=payload.openid,
            message=payload.message,
            metadata={
                **payload.metadata,
                "message_type": payload.message_type,
            },
        )
    except ChatSkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail="chat skill not found") from exc
    except ChatSkillUnavailableError as exc:
        raise HTTPException(status_code=409, detail="chat skill unavailable") from exc
```

- [ ] **Step 4: Run targeted and full API verification**

Run:

```powershell
python -m pytest tests/test_chat_api.py -v
python -m pytest -v
```

Expected:

- First command: PASS with the new WeChat adapter tests green
- Second command: PASS with the entire `apps/api/tests` suite green and no chat-related regressions

- [ ] **Step 5: Commit the WeChat adapter and verification state**

```powershell
git add apps/api/app/routers/chat.py apps/api/tests/test_chat_api.py
git commit -m "feat(api): add wechat chat adapter"
```
