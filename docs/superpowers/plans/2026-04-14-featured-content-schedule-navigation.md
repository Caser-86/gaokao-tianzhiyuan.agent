# Featured Content Schedule Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let operators click a day in the admin seven-day featured-content schedule to jump directly into that day's selected-date preview.

**Architecture:** Keep the change in the Web admin layer. `DashboardShell` will render schedule day headings as links when they are not the highlighted day and keep highlighted days as plain text with the existing `当前查看` marker.

**Tech Stack:** Next.js app router, React server components, Vitest, Testing Library

---

### Task 1: Add the failing schedule navigation tests

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Add link assertions for non-highlighted schedule days**

```tsx
expect(screen.getByRole('link', { name: '2026-04-14' })).toHaveAttribute(
  'href',
  '/admin?preview_date=2026-04-14',
);
```

- [ ] **Step 2: Add assertions that highlighted days are not links**

```tsx
expect(screen.queryByRole('link', { name: '2026-04-15' })).not.toBeInTheDocument();
```

- [ ] **Step 3: Run focused tests to verify failure**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`
Expected: FAIL because schedule headings are still plain text.

- [ ] **Step 4: Commit**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "test(web): cover featured content schedule navigation"
```

### Task 2: Implement schedule navigation

**Files:**
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Render non-highlighted day titles as links**

```tsx
{day.date === highlightedScheduleDate ? <h3>{day.date}</h3> : <h3><a href={`/admin?preview_date=${day.date}`}>{day.date}</a></h3>}
```

- [ ] **Step 2: Keep the highlighted marker behavior unchanged**

```tsx
{day.date === highlightedScheduleDate ? <p>当前查看</p> : null}
```

- [ ] **Step 3: Run focused tests to verify pass**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat(web): add featured content schedule navigation"
```

### Task 3: Verify the full Web surface

**Files:**
- Verify: `apps/web/tests/*.test.ts*`
- Verify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Run the full Web test suite**

Run: `node .\node_modules\vitest\vitest.mjs run`
Expected: PASS with all test files green.

- [ ] **Step 2: Run the production build**

Run: `node .\node_modules\next\dist\bin\next build`
Expected: PASS. Existing SWC policy warnings may remain, but build must finish successfully.

- [ ] **Step 3: Check git status**

Run: `git status --short`
Expected: only intended changes or a clean tree after commit.
