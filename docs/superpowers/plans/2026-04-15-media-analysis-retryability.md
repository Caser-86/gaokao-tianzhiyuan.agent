# Media Analysis Retryability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose retryability metadata for admin media-analysis records and align the UI with the backend retry contract.

**Architecture:** The backend becomes the single source of truth for retryability. Admin list responses expose `retryable` and `retry_block_reason`, the retry endpoint reuses the same rule helper, and the web dashboard only renders retry controls for retryable records.

**Tech Stack:** FastAPI, Next.js, TypeScript, pytest, Vitest

---

### Task 1: Add failing API and UI contract tests

**Files:**
- Modify: `apps/api/tests/test_admin_api.py`
- Modify: `apps/web/tests/admin-media-analysis-api.test.ts`
- Modify: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Add admin API list assertions for retryable vs blocked records**

- [ ] **Step 2: Add web API client assertions for `retryable` and `retry_block_reason` mapping**

- [ ] **Step 3: Add admin page assertions so only retryable records show the retry button**

- [ ] **Step 4: Run focused tests and verify RED**

Run:

```powershell
python -m pytest apps/api/tests/test_admin_api.py -k "media_analysis_events_endpoint" -q
pnpm --dir apps/web vitest run tests/admin-media-analysis-api.test.ts tests/admin-page.test.tsx
```

Expected:

- API list tests fail because the response lacks retryability metadata
- Web tests fail because the client/component cannot read or render retryability yet

### Task 2: Implement backend retryability metadata

**Files:**
- Modify: `apps/api/app/routers/admin.py`

- [ ] **Step 1: Add a retryability helper that returns `(retryable, retry_block_reason)`**

- [ ] **Step 2: Reuse the helper in list serialization and retry payload validation**

- [ ] **Step 3: Run focused API tests and verify GREEN**

Run:

```powershell
python -m pytest apps/api/tests/test_admin_api.py -k "media_analysis_events_endpoint or retry_media_analysis_endpoint" -q
```

Expected:

- PASS

### Task 3: Implement web mapping and dashboard behavior

**Files:**
- Modify: `apps/web/lib/admin-media-analysis-api.ts`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Map the new admin API fields**

- [ ] **Step 2: Show retry button only when retryable**

- [ ] **Step 3: Show `不可重试：...` when blocked**

- [ ] **Step 4: Run focused web tests and verify GREEN**

Run:

```powershell
pnpm --dir apps/web vitest run tests/admin-media-analysis-api.test.ts tests/admin-page.test.tsx
```

Expected:

- PASS

### Task 4: Update operator docs and run full verification

**Files:**
- Modify: `apps/api/README.md`
- Modify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Document retryability semantics for `/admin` media-analysis events**

- [ ] **Step 2: Run project verification**

Run:

```powershell
python -m pytest apps/api/tests/test_admin_api.py -q
pnpm --dir apps/web vitest run tests/admin-media-analysis-api.test.ts tests/admin-page.test.tsx
powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1
```

Expected:

- PASS with only existing known non-blocking warnings
