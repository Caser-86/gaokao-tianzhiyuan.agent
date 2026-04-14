# Featured Content Schedule Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show names and slugs in the admin seven-day featured-content schedule so operators can read the schedule without mentally decoding slugs.

**Architecture:** Reuse the existing `PreviewList` UI pattern inside the seven-day schedule. This keeps schedule behavior, highlighting, and navigation intact while aligning schedule copy with the other preview sections.

**Tech Stack:** Next.js app router, React server components, Vitest, Testing Library

---

### Task 1: Add the failing schedule copy tests

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Add assertions for names inside the seven-day schedule**

```tsx
expect(within(scheduleRegion).getByText('华西医学中心')).toBeInTheDocument();
expect(within(scheduleRegion).getByText('计算机科学与技术')).toBeInTheDocument();
```

- [ ] **Step 2: Run focused tests to verify failure**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`
Expected: FAIL because the schedule still renders slug-only list items.

- [ ] **Step 3: Commit**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "test(web): cover featured content schedule copy"
```

### Task 2: Reuse PreviewList in the schedule

**Files:**
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Replace the schedule school slug list**

```tsx
{day.schools.length === 0 ? <p>当天没有展示学校</p> : <PreviewList items={day.schools} />}
```

- [ ] **Step 2: Replace the schedule major slug list**

```tsx
{day.majors.length === 0 ? <p>当天没有展示专业</p> : <PreviewList items={day.majors} />}
```

- [ ] **Step 3: Run focused tests to verify pass**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat(web): align featured content schedule copy"
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
