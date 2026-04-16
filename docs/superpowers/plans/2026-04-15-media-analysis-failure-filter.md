# Media Analysis Failure Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a failure-focused summary and one-click failed-only filter to the admin media-analysis section.

**Architecture:** Keep the backend unchanged and extend the admin page plus dashboard shell only. The admin page will build failure-filter URLs from existing search params, and the dashboard will render a small summary plus status shortcuts from the loaded event list.

**Tech Stack:** Next.js, React, TypeScript, Vitest, Testing Library

---

### Task 1: Add failing tests for dashboard failure summary

**Files:**
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
expect(screen.getByText('当前列表共 2 条，失败 1 条，待处理 0 条')).toBeInTheDocument();
expect(screen.getByRole('link', { name: '只看失败记录（1）' })).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: FAIL because the dashboard does not render the summary or shortcut yet.

- [ ] **Step 3: Write minimal implementation**

```tsx
const failedMediaAnalysisCount = mediaAnalysisEvents.filter((event) => event.status === 'failed').length;
const pendingMediaAnalysisCount = mediaAnalysisEvents.filter((event) => event.status === 'pending').length;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-dashboard.test.tsx apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat: add media analysis failure summary"
```

### Task 2: Add failing tests for admin-page failed-only links

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
expect(screen.getByRole('link', { name: '只看失败记录（1）' })).toHaveAttribute(
  'href',
  '/admin?media_analysis_status=failed&media_analysis_user_id=wx-openid-123&media_analysis_auto_routed=1',
);
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-page.test.tsx`
Expected: FAIL because the page does not build failure shortcut links yet.

- [ ] **Step 3: Write minimal implementation**

```tsx
const showFailedMediaAnalysisOnlyHref = mediaAnalysisStatus !== 'failed'
  ? buildAdminHrefBase({ ..., mediaAnalysisStatus: 'failed' })
  : undefined;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-page.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat: add failed-only media analysis shortcut"
```

### Task 3: Run focused and full verification

**Files:**
- Modify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Update handover note**

```md
- `/admin` media-analysis now shows current-window failure counts and a failed-only shortcut for faster triage.
```

- [ ] **Step 2: Run focused tests**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx tests/admin-page.test.tsx`
Expected: PASS

- [ ] **Step 3: Run full verification**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`
Expected: PASS with existing known warnings only.

- [ ] **Step 4: Commit**

```bash
git add docs/operations/local-handover-runbook.md
git commit -m "docs: note media analysis failure filter shortcut"
```
