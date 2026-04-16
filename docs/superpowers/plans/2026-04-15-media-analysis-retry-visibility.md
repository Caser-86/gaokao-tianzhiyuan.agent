# Media Analysis Retry Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make admin operators see retry relationships and latest retry status directly in the existing recent media-analysis cards.

**Architecture:** Keep the existing `/admin` media-analysis list and compute retry relationships in the dashboard component from already returned event data. Treat events with `context.retried_from_event_id` as retry records, derive the latest visible retry for each original record, and render lightweight status text on both original and retry cards without adding a new API shape.

**Tech Stack:** Next.js App Router, React server actions, Vitest, Testing Library, TypeScript

---

### Task 1: Lock the visibility behavior with failing dashboard tests

**Files:**
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Test: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
test('shows retry relationship details for original and retried media-analysis events', () => {
  const events: AdminMediaAnalysisEvent[] = [
    {
      id: 22,
      channel: 'wechat',
      source: 'admin_media_analysis_retry',
      userId: 'wx-openid-123',
      messageId: 'msg-123',
      mediaId: 'media-123',
      mediaType: 'image',
      provider: 'openai_compatible',
      status: 'pending',
      summary: 'retry summary',
      renderedReply: '',
      extractedFields: {},
      context: {
        retried_from_event_id: 21,
        pic_url: 'https://example.com/image-123.png',
      },
      autoRoutedToChat: false,
      createdAt: '2026-04-15T09:05:00Z',
    },
    {
      id: 21,
      channel: 'wechat',
      source: 'wechat_official_account_image_media_analysis',
      userId: 'wx-openid-123',
      messageId: 'msg-123',
      mediaId: 'media-123',
      mediaType: 'image',
      provider: 'openai_compatible',
      status: 'success',
      summary: 'original summary',
      renderedReply: '',
      extractedFields: {},
      context: {
        pic_url: 'https://example.com/image-123.png',
      },
      autoRoutedToChat: true,
      createdAt: '2026-04-15T09:00:00Z',
    },
  ];

  render(<DashboardShell ... mediaAnalysisEvents={events} ... />);

  expect(screen.getByText('原始记录 · 最新重试 #22 · pending')).toBeInTheDocument();
  expect(screen.getByText('手动重试记录 · 来源 #21')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: FAIL because the dashboard does not yet render retry relationship text.

- [ ] **Step 3: Write minimal implementation**

```tsx
const getRetriedFromEventId = (event: AdminMediaAnalysisEvent): number | null => {
  const value = event.context['retried_from_event_id'];
  return typeof value === 'number' ? value : null;
};

const latestRetryByOriginalId = new Map<number, AdminMediaAnalysisEvent>();
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-dashboard.test.tsx apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat: surface media retry visibility in admin dashboard"
```

### Task 2: Render compact retry status copy in the dashboard

**Files:**
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Test: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Write the failing refinement test**

```tsx
expect(screen.getByText('原始记录')).toBeInTheDocument();
expect(screen.getByText('手动重试记录')).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: FAIL until the labels are rendered near each event card.

- [ ] **Step 3: Write minimal implementation**

```tsx
const retryRelationshipLabel = isRetryRecord
  ? `手动重试记录 · 来源 #${retriedFromEventId}`
  : latestRetry
    ? `原始记录 · 最新重试 #${latestRetry.id} · ${latestRetry.status}`
    : '原始记录';
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "test: cover media retry relationship labels"
```

### Task 3: Verify and document the operator-facing change

**Files:**
- Modify: `docs/operations/local-handover-runbook.md`
- Test: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Update the runbook**

```md
- Recent media-analysis cards now show whether a row is the original record or a manual retry record, and when visible they also show the latest retry id/status for the original row.
```

- [ ] **Step 2: Run focused verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 3: Run full project verification**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`
Expected: `Project verification finished successfully.`

- [ ] **Step 4: Commit**

```bash
git add docs/operations/local-handover-runbook.md apps/web/tests/admin-dashboard.test.tsx apps/web/components/admin/dashboard-shell.tsx
git commit -m "docs: note admin media retry visibility"
```
