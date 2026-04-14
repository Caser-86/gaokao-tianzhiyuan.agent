# Featured Content Schedule Highlight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Highlight the relevant day inside the admin seven-day featured-content schedule so operators can line up selected-date preview with the schedule at a glance.

**Architecture:** Keep the change entirely in the Web admin layer. The server page computes one `highlightedScheduleDate` string and passes it into `DashboardShell`, which renders a lightweight `当前查看` marker on the matching schedule entry.

**Tech Stack:** Next.js app router, React server components, Vitest, Testing Library

---

### Task 1: Add the failing highlight tests

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Write the failing page tests**

```tsx
expect(screen.getByText('当前查看')).toBeInTheDocument();
expect(
  within(screen.getByText('2026-04-15').closest('article') as HTMLElement).getByText('当前查看'),
).toBeInTheDocument();
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`
Expected: FAIL because `当前查看` is not rendered yet.

- [ ] **Step 3: Add no-date and invalid-date expectations**

```tsx
expect(screen.getAllByText('当前查看')).toHaveLength(1);
expect(screen.queryByText('当前查看')).not.toBeInTheDocument();
```

- [ ] **Step 4: Re-run focused tests**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`
Expected: still FAIL on missing highlight marker.

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "test(web): cover featured content schedule highlight"
```

### Task 2: Implement highlighted schedule date

**Files:**
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Add minimal page logic**

```tsx
const highlightedScheduleDate =
  normalizedPreviewDate ?? (!previewDate ? todayPreviewDate : undefined);
```

- [ ] **Step 2: Pass the prop into `DashboardShell`**

```tsx
      highlightedScheduleDate={highlightedScheduleDate}
```

- [ ] **Step 3: Render the marker in the schedule**

```tsx
{day.date === highlightedScheduleDate ? <p>当前查看</p> : null}
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat(web): highlight featured content schedule day"
```

### Task 3: Verify the full Web surface

**Files:**
- Verify: `apps/web/tests/*.test.ts*`
- Verify: `apps/web/app/(admin)/admin/page.tsx`
- Verify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Run the full Web test suite**

Run: `node .\node_modules\vitest\vitest.mjs run`
Expected: PASS with all test files green.

- [ ] **Step 2: Run the production build**

Run: `node .\node_modules\next\dist\bin\next build`
Expected: PASS. The existing SWC policy warning may still appear, but build must complete successfully.

- [ ] **Step 3: Check git status**

Run: `git status --short`
Expected: only intended tracked changes or a clean tree after commit.

- [ ] **Step 4: Commit any remaining verification-related updates**

```bash
git add apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "fix(web): finalize featured content schedule highlight"
```
