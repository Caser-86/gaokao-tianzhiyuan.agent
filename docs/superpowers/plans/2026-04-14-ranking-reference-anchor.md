# Ranking Reference Anchor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight `查看参考榜单` anchor entry to school and major detail pages so users can jump directly to the existing ranking-reference section.

**Architecture:** Reuse the existing detail-page `link-row` for the new entry and expose a stable `id="ranking-references"` from `RankingReferenceList`. Keep the behavior entirely server-rendered and conditional on `rankingReferences.length > 0`.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Add failing detail-page coverage for the ranking-reference anchor

**Files:**
- Modify: `apps/web/tests/public-pages.test.tsx`
- Modify: `apps/web/app/schools/[slug]/page.tsx`
- Modify: `apps/web/app/majors/[slug]/page.tsx`
- Modify: `apps/web/components/public/ranking-reference-list.tsx`

- [ ] **Step 1: Write the failing test**

Extend the existing detail-page tests so they expect an anchor entry when ranking references exist and omit it when they do not.

```tsx
expect(
  screen.getByRole('link', { name: '\u67e5\u770b\u53c2\u8003\u699c\u5355' }),
).toHaveAttribute('href', '#ranking-references');

expect(
  screen.queryByRole('link', { name: '\u67e5\u770b\u53c2\u8003\u699c\u5355' }),
).not.toBeInTheDocument();
```

Add the positive assertion to the seeded school and major detail tests, and the negative assertion to the school detail test with an empty `rankingReferences` array.

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: FAIL because the detail pages do not yet render the anchor entry.

- [ ] **Step 3: Write minimal implementation**

Update the detail pages to render the anchor only when ranking references exist, and give the ranking-reference section a stable id.

```tsx
{school.rankingReferences.length > 0 ? (
  <Link href="#ranking-references" className="cta secondary">
    {'\u67e5\u770b\u53c2\u8003\u699c\u5355'}
  </Link>
) : null}
```

```tsx
<section id="ranking-references" className="panel" style={{ marginTop: 28 }}>
```

Apply the same conditional link pattern to the major detail page.

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS with detail pages exposing the anchor only when ranking references are present.

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/public-pages.test.tsx apps/web/app/schools/[slug]/page.tsx apps/web/app/majors/[slug]/page.tsx apps/web/components/public/ranking-reference-list.tsx
git commit -m "feat(web): add ranking reference anchor links"
```

### Task 2: Run final Web verification

**Files:**
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Run focused page verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS

- [ ] **Step 2: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`

Expected: PASS with all `apps/web` tests green

- [ ] **Step 3: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`

Expected: PASS with a successful Next.js production build. The known Windows SWC policy warning is acceptable if the build completes successfully via the wasm fallback.

- [ ] **Step 4: Review git status**

Run: `git status --short`

Expected: clean working tree after the intended commit, or only the plan/spec files before their own commits
