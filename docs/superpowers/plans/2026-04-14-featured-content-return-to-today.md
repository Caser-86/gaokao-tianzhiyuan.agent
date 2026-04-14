# Featured Content Return-To-Today Shortcut Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `回到今天` shortcut to the admin selected-date preview when the current selected date is valid and not already today.

**Architecture:** Keep the feature web-only and server-rendered. The admin page computes today's ISO date and conditionally derives a `todayPreviewDateHref`, while the dashboard shell only renders the shortcut link when that href is present.

**Tech Stack:** Next.js App Router, TypeScript, Vitest, Testing Library

---

### Task 1: Cover the return-to-today shortcut in the admin page and shell tests

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Write the failing assertions**

```tsx
expect(screen.getByRole('link', { name: '回到今天' })).toHaveAttribute(
  'href',
  '/admin?preview_date=2026-04-14',
);
```

And for hidden states:

```tsx
expect(screen.queryByRole('link', { name: '回到今天' })).not.toBeInTheDocument();
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: FAIL because the shell does not render a `回到今天` shortcut yet

- [ ] **Step 3: Commit the red tests**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "test(web): cover return-to-today shortcut"
```

### Task 2: Implement the return-to-today shortcut

**Files:**
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Add a helper to derive today's ISO date**

```ts
const todayIsoDate = (): string => new Date().toISOString().slice(0, 10);
```

- [ ] **Step 2: Derive an optional return-to-today href**

```ts
const currentToday = todayIsoDate();
const todayPreviewDateHref =
  previewDate && shiftIsoDate(previewDate, 0) && previewDate !== currentToday
    ? `/admin?preview_date=${currentToday}`
    : undefined;
```

- [ ] **Step 3: Pass the today shortcut into the shell**

```tsx
<DashboardShell
  ...
  todayPreviewDateHref={todayPreviewDateHref}
/>
```

- [ ] **Step 4: Render the shortcut only when present**

```tsx
{todayPreviewDateHref ? <a href={todayPreviewDateHref}>回到今天</a> : null}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add "apps/web/app/(admin)/admin/page.tsx" apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "feat(web): add return-to-today shortcut"
```

### Task 3: Run verification

**Files:**
- Verify only

- [ ] **Step 1: Run the full web test suite**

Run: `node .\node_modules\vitest\vitest.mjs run`

Expected: PASS

- [ ] **Step 2: Run the web build**

Run: `node .\node_modules\next\dist\bin\next build`

Expected: PASS

- [ ] **Step 3: Confirm a clean working tree**

Run: `git status --short`

Expected: no output
