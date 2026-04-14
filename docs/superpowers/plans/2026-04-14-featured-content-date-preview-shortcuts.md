# Featured Content Date Preview Shortcuts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lightweight previous-day and next-day shortcuts to the admin featured-content selected-date preview.

**Architecture:** Keep the existing server-rendered `preview_date` flow and compute adjacent ISO dates in the web admin layer only. Render shortcut links in the dashboard shell when the current selected date is valid, and keep the API untouched.

**Tech Stack:** Next.js App Router, TypeScript, Vitest, Testing Library

---

### Task 1: Add selected-date shortcut coverage to the admin web tests

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Write the failing page and shell assertions**

```tsx
expect(screen.getByRole('link', { name: '查看前一天' })).toHaveAttribute(
  'href',
  '/admin?preview_date=2026-04-19',
);
expect(screen.getByRole('link', { name: '查看后一天' })).toHaveAttribute(
  'href',
  '/admin?preview_date=2026-04-21',
);
```

And for missing or invalid dates:

```tsx
expect(screen.queryByRole('link', { name: '查看前一天' })).not.toBeInTheDocument();
expect(screen.queryByRole('link', { name: '查看后一天' })).not.toBeInTheDocument();
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: FAIL because the dashboard shell does not render shortcut links yet

- [ ] **Step 3: Commit the red tests**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "test(web): cover date preview shortcuts"
```

### Task 2: Implement selected-date shortcut links in the admin page and shell

**Files:**
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Add minimal date-offset helper in the admin page**

```ts
const shiftIsoDate = (value: string, offsetDays: number): string | null => {
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  parsed.setUTCDate(parsed.getUTCDate() + offsetDays);
  return parsed.toISOString().slice(0, 10);
};
```

- [ ] **Step 2: Derive optional previous and next preview URLs**

```ts
const previousPreviewDate = previewDate ? shiftIsoDate(previewDate, -1) : null;
const nextPreviewDate = previewDate ? shiftIsoDate(previewDate, 1) : null;

const previousPreviewDateHref = previousPreviewDate
  ? `/admin?preview_date=${previousPreviewDate}`
  : undefined;
const nextPreviewDateHref = nextPreviewDate
  ? `/admin?preview_date=${nextPreviewDate}`
  : undefined;
```

- [ ] **Step 3: Pass the shortcut hrefs into the dashboard shell**

```tsx
<DashboardShell
  ...
  previousPreviewDateHref={previousPreviewDateHref}
  nextPreviewDateHref={nextPreviewDateHref}
/>
```

- [ ] **Step 4: Render the shortcut links only when present**

```tsx
{previousPreviewDateHref ? <a href={previousPreviewDateHref}>查看前一天</a> : null}
{nextPreviewDateHref ? <a href={nextPreviewDateHref}>查看后一天</a> : null}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add "apps/web/app/(admin)/admin/page.tsx" apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "feat(web): add date preview shortcuts"
```

### Task 3: Run verification

**Files:**
- Verify only

- [ ] **Step 1: Run full web test suite**

Run: `node .\node_modules\vitest\vitest.mjs run`

Expected: PASS

- [ ] **Step 2: Run the web build**

Run: `node .\node_modules\next\dist\bin\next build`

Expected: PASS

- [ ] **Step 3: Confirm clean working tree**

Run: `git status --short`

Expected: no output
