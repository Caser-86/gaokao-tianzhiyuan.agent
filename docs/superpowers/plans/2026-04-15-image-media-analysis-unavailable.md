# Image Media Analysis Unavailable Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split intentional pending media-analysis behavior from explicit image-provider unavailability and failed image-analysis replies.

**Architecture:** Keep the existing success path intact. A declared-but-incomplete `openai_compatible` provider will now return a failed result with a readable reason, and the image router will use a dedicated unavailable reply for failed results while preserving the existing pending reply for truly unconfigured providers.

**Tech Stack:** FastAPI, Python, pytest

---

### Task 1: Add failing tests for provider-unavailable image behavior

**Files:**
- Modify: `apps/api/tests/test_chat_services.py`
- Modify: `apps/api/tests/test_chat_api.py`

- [ ] **Step 1: Add a failing service test for incomplete openai-compatible config**

```python
provider = build_media_analysis_provider(
    provider="openai_compatible",
    base_url="",
    api_key="secret-key",
    model="gpt-4o-mini",
)

result = provider.analyze(
    request=MediaAnalysisRequest(
        media_type="image",
        user_id="wx-openid-image",
        payload={"PicUrl": "https://example.com/image.png"},
    )
)

assert result.status == "failed"
assert result.failure_reason == (
    "当前 openai_compatible 媒体分析配置不完整，请检查 BASE_URL / API_KEY / MODEL"
)
```

- [ ] **Step 2: Change the failed-image API test to the new reply**

```python
assert (
    f"<Content><![CDATA[{chat_router_module.WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_UNAVAILABLE_REPLY}]]></Content>"
    in response.text
)
```

- [ ] **Step 3: Run focused tests to verify they fail**

Run: `python -m pytest apps/api/tests/test_chat_services.py -k "openai_compatible and config" -q`
Expected: FAIL because incomplete config still collapses to pending.

Run: `python -m pytest apps/api/tests/test_chat_api.py -k "image_message_records_failed_media_reason_event" -q`
Expected: FAIL because failed image replies still use the pending-integration text.

- [ ] **Step 4: Commit**

```bash
git add apps/api/tests/test_chat_services.py apps/api/tests/test_chat_api.py
git commit -m "test: cover image media analysis unavailable path"
```

### Task 2: Implement explicit unavailable-provider and failed-image reply behavior

**Files:**
- Modify: `apps/api/app/services/media_analysis.py`
- Modify: `apps/api/app/routers/chat.py`

- [ ] **Step 1: Add an unavailable media-analysis provider**

```python
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
```

- [ ] **Step 2: Use it for incomplete openai-compatible config**

```python
if normalized_provider == "openai_compatible":
    if not base_url.strip() or not api_key.strip() or not model.strip():
        return UnavailableMediaAnalysisProvider(
            provider_name="openai_compatible",
            failure_reason="当前 openai_compatible 媒体分析配置不完整，请检查 BASE_URL / API_KEY / MODEL",
        )
```

- [ ] **Step 3: Add the new failed-image reply constant and route failed results to it**

```python
WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_UNAVAILABLE_REPLY = (
    "已收到你上传的图片，但当前图片解析暂时不可用。请继续补充文字描述、分数、省份或专业方向，我先继续帮你分析。"
)

if result.status == "failed":
    return WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_UNAVAILABLE_REPLY
return WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_PENDING_REPLY
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m pytest apps/api/tests/test_chat_services.py -k "openai_compatible and config" -q`
Expected: PASS

Run: `python -m pytest apps/api/tests/test_chat_api.py -k "direct_image_message_returns_media_pending_reply_when_smart_analysis_is_on or image_message_records_failed_media_reason_event" -q`
Expected: PASS, showing pending and failed paths are now distinct.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/media_analysis.py apps/api/app/routers/chat.py
git commit -m "feat: distinguish image media analysis unavailable from pending"
```

### Task 3: Update docs and run full verification

**Files:**
- Modify: `apps/api/README.md`
- Modify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Update operator docs**

```md
- Blank media-analysis providers still use the pending path, but declared-yet-incomplete `openai_compatible` image analysis now records an explicit failed reason and returns an image-analysis-unavailable reply.
```

- [ ] **Step 2: Run focused verification**

Run: `python -m pytest apps/api/tests/test_chat_services.py -q`
Expected: PASS

Run: `python -m pytest apps/api/tests/test_chat_api.py -q`
Expected: PASS

- [ ] **Step 3: Run full project verification**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`
Expected: PASS with only the existing known non-blocking warnings.

- [ ] **Step 4: Commit**

```bash
git add apps/api/README.md docs/operations/local-handover-runbook.md
git commit -m "docs: note image media analysis unavailable behavior"
```
