# Media Analysis Failure Reason Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist readable media-analysis failure reasons and show them in the admin media-analysis cards.

**Architecture:** Extend the media-analysis result model with `failed` and `failure_reason`, persist that reason into event `context`, and render it in the existing admin dashboard cards. Keep user-facing WeChat fallback behavior unchanged so only operator visibility improves.

**Tech Stack:** Python, FastAPI, SQLModel, Next.js, React, Vitest, Pytest

---

### Task 1: Add failing backend tests for failed media-analysis reasons

**Files:**
- Modify: `apps/api/tests/test_chat_services.py`
- Modify: `apps/api/tests/test_chat_api.py`
- Modify: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_openai_compatible_media_analysis_provider_returns_failed_reason_on_http_error(...):
    assert result.status == "failed"
    assert result.failure_reason == "上游媒体分析请求失败：HTTP 429"


def test_wechat_official_account_image_message_persists_failed_media_reason(...):
    assert stored.status == "failed"
    assert stored.context["failure_reason"] == "上游媒体分析请求失败：HTTP 429"


def test_retry_media_analysis_endpoint_persists_failure_reason(...):
    assert payload["status"] == "failed"
    assert payload["context"]["failure_reason"] == "上游媒体分析请求失败：HTTP 429"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest apps/api/tests/test_chat_services.py -k media_analysis_failure_reason -q`
Expected: FAIL because `MediaAnalysisResult` does not yet expose `failed` or `failure_reason`.

Run: `python -m pytest apps/api/tests/test_chat_api.py -k failed_media_reason -q`
Expected: FAIL because failed reasons are not yet persisted into event context.

Run: `python -m pytest apps/api/tests/test_admin_api.py -k failure_reason -q`
Expected: FAIL because admin retry responses do not yet carry `failure_reason`.

- [ ] **Step 3: Write minimal backend implementation**

```python
@dataclass(frozen=True)
class MediaAnalysisResult:
    status: Literal["pending", "success", "failed"]
    provider: str
    summary: str | None = None
    extracted_fields: dict[str, Any] | None = None
    rendered_reply: str | None = None
    failure_reason: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest apps/api/tests/test_chat_services.py -k media_analysis_failure_reason -q`
Expected: PASS

Run: `python -m pytest apps/api/tests/test_chat_api.py -k failed_media_reason -q`
Expected: PASS

Run: `python -m pytest apps/api/tests/test_admin_api.py -k failure_reason -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/tests/test_chat_services.py apps/api/tests/test_chat_api.py apps/api/tests/test_admin_api.py apps/api/app/services/media_analysis.py apps/api/app/routers/chat.py apps/api/app/routers/admin.py
git commit -m "feat: persist media analysis failure reasons"
```

### Task 2: Add failing admin dashboard test for visible failure reasons

**Files:**
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
expect(screen.getByText('失败原因：上游媒体分析请求失败：HTTP 429')).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: FAIL because the dashboard does not yet render failure reasons.

- [ ] **Step 3: Write minimal implementation**

```tsx
const failureReason =
  typeof event.context['failure_reason'] === 'string' ? event.context['failure_reason'].trim() : '';

{failureReason ? <p>{`失败原因：${failureReason}`}</p> : null}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-dashboard.test.tsx apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat: show media analysis failure reasons in admin"
```

### Task 3: Update docs and run full verification

**Files:**
- Modify: `docs/operations/local-handover-runbook.md`
- Modify: `apps/api/README.md`

- [ ] **Step 1: Update docs**

```md
- Failed media-analysis records now persist a readable `context.failure_reason`, and `/admin` renders that reason directly in each media-analysis card.
```

- [ ] **Step 2: Run focused verification**

Run: `python -m pytest apps/api/tests/test_chat_services.py -k media_analysis_failure_reason -q`
Expected: PASS

Run: `python -m pytest apps/api/tests/test_chat_api.py -k failed_media_reason -q`
Expected: PASS

Run: `python -m pytest apps/api/tests/test_admin_api.py -k failure_reason -q`
Expected: PASS

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 3: Run full verification**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`
Expected: `Project verification finished successfully.`

- [ ] **Step 4: Commit**

```bash
git add docs/operations/local-handover-runbook.md apps/api/README.md
git commit -m "docs: note media analysis failure visibility"
```
