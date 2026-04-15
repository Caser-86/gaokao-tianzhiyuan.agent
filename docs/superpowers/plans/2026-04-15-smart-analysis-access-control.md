# Smart Analysis Access Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global smart-analysis mode plus user-entitlement gating so provider-backed chat analysis can be fully off, premium-only, or fully on without changing the public chat API contract.

**Architecture:** Extend runtime settings with a validated `smart_analysis_mode`, add `smart_analysis` to the platform entitlement vocabulary, and centralize eligibility evaluation in the chat service layer. Keep business-policy fallback separate from technical provider fallback by passing an explicit smart-analysis decision into `ZhangXueFengSkill` and surfacing distinct `debug.notes`.

**Tech Stack:** FastAPI, Pydantic Settings, Python dataclasses/protocols, pytest, FastAPI `TestClient`

---

## File Map

- Modify: `apps/api/app/config.py`
  - Add and validate `smart_analysis_mode`
- Modify: `apps/api/tests/test_config.py`
  - Add mode validation tests
- Modify: `apps/api/app/services/platform.py`
  - Add the `smart_analysis` entitlement to a premium product bundle
- Modify: `apps/api/tests/test_platform_api.py`
  - Verify `smart_analysis` appears in product and entitlement responses
- Modify: `apps/api/app/services/skills.py`
  - Allow `ZhangXueFengSkill` to receive a smart-analysis permission decision and distinguish policy fallback from provider fallback
- Modify: `apps/api/app/services/chat.py`
  - Add smart-analysis eligibility evaluation based on global mode and `metadata.entitlements`
- Modify: `apps/api/tests/test_chat_services.py`
  - Add service-level gating tests for `off`, `gated`, and `on`
- Modify: `apps/api/tests/test_chat_api.py`
  - Add API-level assertions for policy fallback debug notes
- Modify: `apps/api/README.md`
  - Document `GAOKAO_AGENT_SMART_ANALYSIS_MODE` and `metadata.entitlements`

### Task 1: Add smart-analysis mode config and platform entitlement support

**Files:**
- Modify: `apps/api/app/config.py`
- Modify: `apps/api/tests/test_config.py`
- Modify: `apps/api/app/services/platform.py`
- Modify: `apps/api/tests/test_platform_api.py`

- [ ] **Step 1: Write the failing config and platform tests**

Update `apps/api/tests/test_config.py` to add:

```python
def test_smart_analysis_mode_accepts_supported_values() -> None:
    assert Settings(smart_analysis_mode="off").smart_analysis_mode == "off"
    assert Settings(smart_analysis_mode="gated").smart_analysis_mode == "gated"
    assert Settings(smart_analysis_mode="on").smart_analysis_mode == "on"


def test_smart_analysis_mode_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(smart_analysis_mode="partial")
    assert "smart_analysis_mode must be one of: off, gated, on" in str(exc_info.value)
```

Update `apps/api/tests/test_platform_api.py` to change the expected premium bundle:

```python
{
    "slug": "deep-dive-pack",
    "name": "深度报告包",
    "description": "适合需要学校、专业、地域和就业深度分析的家庭。",
    "entitlements": [
        "school_deep_dive_access",
        "major_deep_dive_access",
        "region_compare_access",
        "smart_analysis",
    ],
}
```

and the entitlement evaluation expectation:

```python
assert response.json() == {
    "product_slugs": ["deep-dive-pack", "insight-weekly"],
    "entitlements": [
        "major_basic_access",
        "major_deep_dive_access",
        "region_compare_access",
        "risk_alert_access",
        "school_basic_access",
        "school_deep_dive_access",
        "smart_analysis",
    ],
}
```

- [ ] **Step 2: Run the focused tests to verify failure**

Run:

```powershell
python -m pytest tests/test_config.py tests/test_platform_api.py -v
```

Expected: FAIL because `smart_analysis_mode` is not validated yet and `smart_analysis` is not in the product catalog.

- [ ] **Step 3: Implement the config validation and platform entitlement**

Modify `apps/api/app/config.py` to:

```python
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GAOKAO_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "gaokao-agent-api"
    api_prefix: str = "/api"
    environment: str = "development"
    admin_token: str = DEFAULT_ADMIN_TOKEN
    database_url: str = "sqlite:///./gaokao-agent.db"
    llm_provider: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 30
    zhangxuefeng_skill_path: str = ""
    smart_analysis_mode: str = "off"

    @field_validator("smart_analysis_mode")
    @classmethod
    def validate_smart_analysis_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"off", "gated", "on"}:
            raise ValueError("smart_analysis_mode must be one of: off, gated, on")
        return normalized
```

Modify `apps/api/app/services/platform.py` so `deep-dive-pack` includes `smart_analysis`:

```python
    {
        "slug": "deep-dive-pack",
        "name": "深度报告包",
        "description": "适合需要学校、专业、地域和就业深度分析的家庭。",
        "entitlements": [
            "school_deep_dive_access",
            "major_deep_dive_access",
            "region_compare_access",
            "smart_analysis",
        ],
    },
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_config.py tests/test_platform_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add apps/api/app/config.py apps/api/tests/test_config.py apps/api/app/services/platform.py apps/api/tests/test_platform_api.py
git commit -m "feat(api): add smart analysis access settings"
```

### Task 2: Add chat-time smart-analysis eligibility evaluation

**Files:**
- Modify: `apps/api/app/services/chat.py`
- Modify: `apps/api/app/services/skills.py`
- Modify: `apps/api/tests/test_chat_services.py`

- [ ] **Step 1: Write the failing chat service tests**

Update `apps/api/tests/test_chat_services.py` to add:

```python
def test_zhangxuefeng_skill_returns_policy_fallback_when_smart_analysis_disabled(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    provider = FakeProvider('{"intent":"major_recommendation","summary":"不应被调用"}')
    skill = ZhangXueFengSkill(
        provider=provider,
        skill_prompt_path=str(skill_file),
    )

    result = skill.invoke(
        ChatRequestContext(
            channel="wechat",
            user_id="wx-openid-1",
            message="河南560分想学金融，靠谱吗？",
            metadata={"smart_analysis_allowed": False, "smart_analysis_reason": "smart_analysis_disabled_globally"},
        )
    )

    assert result.debug_notes == ["smart_analysis_disabled_globally"]
    assert result.summary != "不应被调用"


def test_conversation_service_requires_smart_analysis_entitlement_when_gated(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    service = ConversationService(
        registry=SkillRegistry(
            [ZhangXueFengSkill(provider=FakeProvider('{"intent":"major_recommendation","summary":"ok"}'), skill_prompt_path=str(skill_file))]
        )
    )

    result = service.handle_message(
        channel="wechat",
        user_id="wx-openid-1",
        message="河南560分想学金融，靠谱吗？",
        metadata={
            "smart_analysis_mode": "gated",
            "entitlements": [],
        },
    )

    assert result["matched_skill"]["skill_id"] == "zhangxuefeng"
    assert result["debug"] == {
        "used_fallback": True,
        "notes": ["smart_analysis_entitlement_required"],
    }


def test_conversation_service_allows_smart_analysis_when_gated_and_entitled(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")
    service = ConversationService(
        registry=SkillRegistry(
            [ZhangXueFengSkill(provider=FakeProvider('{"intent":"major_recommendation","summary":"建议避开金融","analysis":"真实智能分析","suggestions":[],"follow_up_questions":[],"actions":[],"risk_flags":[],"rendered_reply":"智能分析已开启"}'), skill_prompt_path=str(skill_file))]
        )
    )

    result = service.handle_message(
        channel="wechat",
        user_id="wx-openid-1",
        message="河南560分想学金融，靠谱吗？",
        metadata={
            "smart_analysis_mode": "gated",
            "entitlements": ["smart_analysis"],
        },
    )

    assert result["output"]["content"]["analysis"] == "真实智能分析"
    assert result["debug"] == {"used_fallback": False, "notes": []}
```

- [ ] **Step 2: Run the chat service tests to verify failure**

Run:

```powershell
python -m pytest tests/test_chat_services.py -v
```

Expected: FAIL because `ConversationService` does not yet evaluate smart-analysis mode or entitlements, and `ZhangXueFengSkill` does not distinguish policy fallback reasons.

- [ ] **Step 3: Implement eligibility evaluation and policy fallback**

Modify `apps/api/app/services/chat.py` to add a focused evaluator:

```python
SMART_ANALYSIS_ENTITLEMENT = "smart_analysis"


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
```

Use it inside `handle_message()`:

```python
        smart_analysis_allowed, smart_analysis_reason = resolve_smart_analysis_decision(
            metadata,
            default_mode=settings.smart_analysis_mode,
        )
        request = ChatRequestContext(
            channel=channel,
            user_id=user_id,
            message=message.strip(),
            session_id=session_id,
            metadata={
                **(metadata or {}),
                "smart_analysis_allowed": smart_analysis_allowed,
                "smart_analysis_reason": smart_analysis_reason,
            },
        )
```

Modify `apps/api/app/services/skills.py` so `invoke()` checks policy before provider usage:

```python
    def invoke(self, request: ChatRequestContext) -> SkillInvocationResult:
        if request.metadata.get("smart_analysis_allowed") is False:
            reason = str(
                request.metadata.get(
                    "smart_analysis_reason",
                    "smart_analysis_disabled_globally",
                )
            )
            return self._rule_based_fallback(request, debug_note=reason)

        if self.provider and self.skill_prompt_path:
            ...
```

Also refine technical fallback notes so they can be distinguished later:

```python
            except (FileNotFoundError, OSError):
                return self._rule_based_fallback(request, debug_note="skill_prompt_missing")
            except json.JSONDecodeError:
                return self._rule_based_fallback(request, debug_note="provider_invalid_response")
            except KeyError:
                return self._rule_based_fallback(request, debug_note="provider_invalid_response")
            except ProviderRequestError:
                return self._rule_based_fallback(request, debug_note="provider_request_failed")
            except ProviderResponseFormatError:
                return self._rule_based_fallback(request, debug_note="provider_invalid_response")

        return self._rule_based_fallback(request, debug_note="provider_not_configured")
```

- [ ] **Step 4: Run the chat service tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_chat_services.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add apps/api/app/services/chat.py apps/api/app/services/skills.py apps/api/tests/test_chat_services.py
git commit -m "feat(api): gate smart analysis in chat service"
```

### Task 3: Surface policy fallback behavior through the API and docs

**Files:**
- Modify: `apps/api/tests/test_chat_api.py`
- Modify: `apps/api/README.md`

- [ ] **Step 1: Write the failing API and docs-facing tests**

Update `apps/api/tests/test_chat_api.py` to add:

```python
def test_chat_messages_return_policy_note_when_smart_analysis_is_globally_off() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-policy-1",
            "message": "河南560分想学金融，靠谱吗？",
            "metadata": {"smart_analysis_mode": "off", "entitlements": ["smart_analysis"]},
        },
    )

    assert response.status_code == 200
    assert response.json()["debug"] == {
        "used_fallback": True,
        "notes": ["smart_analysis_disabled_globally"],
    }


def test_chat_messages_return_policy_note_when_gated_user_lacks_entitlement() -> None:
    response = client.post(
        "/api/chat/messages",
        json={
            "channel": "wechat",
            "user_id": "wx-openid-policy-2",
            "message": "河南560分想学金融，靠谱吗？",
            "metadata": {"smart_analysis_mode": "gated", "entitlements": []},
        },
    )

    assert response.status_code == 200
    assert response.json()["debug"] == {
        "used_fallback": True,
        "notes": ["smart_analysis_entitlement_required"],
    }
```

- [ ] **Step 2: Run the API tests to verify failure**

Run:

```powershell
python -m pytest tests/test_chat_api.py -v
```

Expected: FAIL because policy fallback reasons are not yet surfaced through the public API.

- [ ] **Step 3: Update docs and verify the API contract**

Add to `apps/api/README.md`:

```md
## Smart analysis access control

The chat gateway supports three global modes through `GAOKAO_AGENT_SMART_ANALYSIS_MODE`:

- `off`: disable model-backed smart analysis for everyone
- `gated`: allow model-backed smart analysis only for callers with `smart_analysis`
- `on`: allow model-backed smart analysis for everyone

During the first implementation phase, callers may pass entitlements in request metadata:

```json
{
  "metadata": {
    "entitlements": ["smart_analysis"]
  }
}
```

When smart analysis is unavailable because of policy, the API keeps a normal fallback response and uses `debug.notes` to distinguish:

- `smart_analysis_disabled_globally`
- `smart_analysis_entitlement_required`
```

- [ ] **Step 4: Run the API tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_chat_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Run the full API test suite**

Run:

```powershell
python -m pytest -v
```

Expected: PASS for the entire `apps/api/tests` suite.

- [ ] **Step 6: Commit**

Run:

```bash
git add apps/api/tests/test_chat_api.py apps/api/README.md
git commit -m "docs(api): document smart analysis access control"
```

## Spec Coverage Check

- global modes `off`, `gated`, and `on`: covered in Tasks 1 and 2
- `smart_analysis` entitlement in the platform layer: covered in Task 1
- request-time entitlement source via `metadata.entitlements`: covered in Tasks 2 and 3
- separation between policy fallback and technical fallback: covered in Task 2
- public API visibility through `debug.notes`: covered in Task 3
- non-breaking request contract: preserved throughout Tasks 2 and 3

## Placeholder Scan

- No `TODO`, `TBD`, or deferred placeholders remain
- Each task includes exact file paths, code snippets, commands, and expected results
- Names are consistent across tasks: `smart_analysis_mode`, `smart_analysis`, `smart_analysis_disabled_globally`, and `smart_analysis_entitlement_required`

