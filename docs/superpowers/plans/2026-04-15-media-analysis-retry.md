# Media Analysis Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an admin-triggered retry flow for media-analysis records so operators can re-run failed or suspicious records without editing the database manually.

**Architecture:** The admin API will expose a retry endpoint that loads a stored media-analysis event, reconstructs a provider request from its retained `context`, runs the existing media-analysis provider again, and persists a new retry event instead of mutating historical rows. The admin page will surface a per-record retry action and refresh back to `/admin` so operators can inspect the newly created record in the existing recent-events list.

**Tech Stack:** FastAPI, SQLModel/SQLite, existing media-analysis provider abstraction, Next.js server actions, Vitest, Pytest

---

### Task 1: Add failing backend tests for retrying media analysis records

**Files:**
- Modify: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing test**

```python
def test_media_analysis_retry_endpoint_creates_new_retry_record(admin_client) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_admin_api.py -k retry_media_analysis -q`
Expected: FAIL because the admin retry endpoint does not exist yet.

- [ ] **Step 3: Add validation coverage**

```python
def test_media_analysis_retry_endpoint_rejects_records_without_retryable_context(admin_client) -> None:
    ...
```

- [ ] **Step 4: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_admin_api.py -k retry_media_analysis -q`
Expected: FAIL with 404 or missing endpoint behavior.

### Task 2: Implement minimal backend retry endpoint

**Files:**
- Modify: `apps/api/app/routers/admin.py`
- Modify: `apps/api/app/services/media_analysis_events.py`
- Modify: `apps/api/app/services/media_analysis.py`
- Modify: `apps/api/app/config.py` only if existing helpers must be reused

- [ ] **Step 1: Add a service/helper that fetches one media-analysis event by id**

```python
def get_media_analysis_event(session: Session, event_id: int) -> MediaAnalysisEvent:
    ...
```

- [ ] **Step 2: Add a retry helper that reconstructs a request from stored context**

```python
def retry_media_analysis_event(...):
    ...
```

- [ ] **Step 3: Add the admin endpoint**

```python
@router.post("/media-analysis-events/{event_id}/retry", ...)
def retry_media_analysis_event_endpoint(...):
    ...
```

- [ ] **Step 4: Run the targeted backend tests**

Run: `python -m pytest apps/api/tests/test_admin_api.py -k retry_media_analysis -q`
Expected: PASS

### Task 3: Add failing admin-page and dashboard tests for the retry action

**Files:**
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Modify: `apps/web/tests/admin-page.test.tsx`
- Create or modify: `apps/web/lib/admin-media-analysis-api.ts`

- [ ] **Step 1: Add a failing dashboard test for rendering the retry button**

```ts
test('renders retry action for media analysis events', () => {
  ...
});
```

- [ ] **Step 2: Add a failing admin-page test for wiring the retry action**

```ts
test('passes retry action into the admin shell', async () => {
  ...
});
```

- [ ] **Step 3: Run the targeted web tests**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx tests/admin-page.test.tsx`
Expected: FAIL because retry wiring is not implemented yet.

### Task 4: Implement admin retry action and UI

**Files:**
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Modify: `apps/web/lib/admin-media-analysis-api.ts`

- [ ] **Step 1: Add a web client for the retry endpoint**

```ts
export async function retryMediaAnalysisEvent(eventId: number): Promise<void> {
  ...
}
```

- [ ] **Step 2: Add a server action that posts the retry request and redirects back to `/admin`**

```ts
export async function retryMediaAnalysisEventAction(formData: FormData): Promise<void> {
  ...
}
```

- [ ] **Step 3: Pass the action into `DashboardShell`**

```tsx
<DashboardShell retryMediaAnalysisEventAction={retryMediaAnalysisEventAction} />
```

- [ ] **Step 4: Render a per-record retry button in the media-analysis card**

```tsx
<form action={retryMediaAnalysisEventAction}>
  <input type="hidden" name="eventId" value={String(event.id)} />
  <button type="submit">重试分析</button>
</form>
```

- [ ] **Step 5: Run the targeted web tests**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx tests/admin-page.test.tsx`
Expected: PASS

### Task 5: Verify the feature end-to-end

**Files:**
- Modify if needed: `apps/api/README.md`
- Modify if needed: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Document the new retry endpoint and operator flow**

```md
- `POST /api/admin/media-analysis-events/{event_id}/retry`
```

- [ ] **Step 2: Run the focused suites**

Run: `python -m pytest apps/api/tests/test_admin_api.py -k media_analysis -q`
Expected: PASS

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-media-analysis-api.test.ts tests/admin-dashboard.test.tsx tests/admin-page.test.tsx`
Expected: PASS

- [ ] **Step 3: Run the full project verifier**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`
Expected: `Project verification finished successfully.`
