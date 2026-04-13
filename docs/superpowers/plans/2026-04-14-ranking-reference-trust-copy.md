# Ranking Reference Trust Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the ranking-reference module clearer and more trustworthy by adding a light reference hint and more explicit source-link copy.

**Architecture:** Keep the current `ranking_references` data flow unchanged and refine only the shared ranking-reference presentation component. Update page-level tests so school and major detail pages verify the new hint and source-link wording while still omitting the module when no ranking references exist.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Add failing page tests for trust-oriented ranking copy

**Files:**
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing test**

Add assertions to the existing detail-page tests so they expect the section hint and the new source-link wording.

```tsx
const RANKING_HINT_TEXT = '\u4e0d\u540c\u699c\u5355\u53e3\u5f84\u4e0d\u540c\uff0c\u7ed3\u679c\u4ec5\u4f9b\u53c2\u8003\u3002';

test('school page renders ranking references when present', async () => {
  // existing school mock setup...

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(screen.getByRole('heading', { name: '\u53c2\u8003\u699c\u5355' })).toBeInTheDocument();
  expect(screen.getByText(RANKING_HINT_TEXT)).toBeInTheDocument();
  expect(
    screen.getByRole('link', { name: '\u67e5\u770b\u6765\u6e90\u539f\u6587' }),
  ).toHaveAttribute('href', 'https://example.com/rankings/southeast-university');
});

test('school page omits ranking references when none are available', async () => {
  // existing no-reference mock setup...

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(screen.queryByRole('heading', { name: '\u53c2\u8003\u699c\u5355' })).not.toBeInTheDocument();
  expect(screen.queryByText(RANKING_HINT_TEXT)).not.toBeInTheDocument();
});
```

Also update the major-page ranking test to check for the same hint and `查看来源原文`.

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: FAIL because the current ranking-reference component does not render the trust hint and still uses `查看来源`.

- [ ] **Step 3: Write minimal implementation**

No production code in this task. Stop after the test is red.

- [ ] **Step 4: Run test to verify it still fails for the expected reason**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: FAIL with missing hint text and/or missing `查看来源原文`.

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/public-pages.test.tsx
git commit -m "test(web): cover ranking reference trust copy"
```

### Task 2: Implement trust-oriented ranking reference copy

**Files:**
- Modify: `apps/web/components/public/ranking-reference-list.tsx`

- [ ] **Step 1: Write the failing test**

Use the already-red `tests/public-pages.test.tsx` expectations from Task 1 as the active failing test. Do not add a second test file unless the page test proves insufficient.

```tsx
expect(screen.getByText('\u4e0d\u540c\u699c\u5355\u53e3\u5f84\u4e0d\u540c\uff0c\u7ed3\u679c\u4ec5\u4f9b\u53c2\u8003\u3002')).toBeInTheDocument();
expect(screen.getByRole('link', { name: '\u67e5\u770b\u6765\u6e90\u539f\u6587' })).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: FAIL because the ranking-reference list has not been updated yet.

- [ ] **Step 3: Write minimal implementation**

Update `apps/web/components/public/ranking-reference-list.tsx` to render the section hint and the new link wording.

```tsx
export default function RankingReferenceList({ references }: RankingReferenceListProps) {
  if (references.length === 0) {
    return null;
  }

  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <h2 className="panel-title">{'\u53c2\u8003\u699c\u5355'}</h2>
      <p>{'\u4e0d\u540c\u699c\u5355\u53e3\u5f84\u4e0d\u540c\uff0c\u7ed3\u679c\u4ec5\u4f9b\u53c2\u8003\u3002'}</p>
      <div className="section-grid">
        {references.map((reference) => (
          <article
            key={`${reference.source}-${reference.year}-${reference.label}`}
            className="section-card"
          >
            <p>{`${reference.source} ${reference.year}`}</p>
            <strong>{reference.label}</strong>
            {reference.scope ? <p>{reference.scope}</p> : null}
            {reference.note ? <p>{reference.note}</p> : null}
            {reference.url ? (
              <a href={reference.url} target="_blank" rel="noreferrer">
                {'\u67e5\u770b\u6765\u6e90\u539f\u6587'}
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS with the section hint and updated source-link wording visible on both detail pages when ranking references exist.

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/public/ranking-reference-list.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): refine ranking reference trust copy"
```

### Task 3: Run full Web verification

**Files:**
- Test: `apps/web/tests/public-pages.test.tsx`
- Test: `apps/web/components/public/ranking-reference-list.tsx`

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

Expected: clean working tree after the intended commits, or only the plan file before its own commit

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-ranking-reference-trust-copy.md
git commit -m "docs: add ranking reference trust copy plan"
```
