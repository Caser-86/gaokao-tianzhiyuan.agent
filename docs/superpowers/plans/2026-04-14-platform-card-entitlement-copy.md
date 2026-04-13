# Platform Card Entitlement Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace known raw entitlement keys in homepage product card metadata with user-facing copy while preserving unknown-key visibility.

**Architecture:** Reuse the existing Web entitlement copy helper in the homepage shelf so product card metadata and entitlement preview both resolve through the same mapping path. Known card entitlements render compact titles, while unknown card entitlements keep their raw key for transparency.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Add failing shelf tests for card metadata copy

**Files:**
- Modify: `apps/web/tests/platform-homepage-shelf.test.tsx`
- Test: `apps/web/tests/platform-homepage-shelf.test.tsx`

- [ ] **Step 1: Write the failing test**

```ts
test('renders user-facing entitlement titles in product card metadata', () => {
  renderShelf();

  const firstCard = screen.getAllByRole('article')[0];

  expect(within(firstCard).getByText('院校基础信息查看')).toBeInTheDocument();
  expect(within(firstCard).queryByText('school_basic_access')).not.toBeInTheDocument();
});

test('keeps raw keys visible for unknown product entitlements', () => {
  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'future-pack',
          name: 'Future Pack',
          description: 'Upcoming capability bundle.',
          entitlements: ['future_capability'],
        },
      ]}
    />,
  );

  const onlyCard = screen.getAllByRole('article')[0];

  expect(within(onlyCard).getByText('future_capability')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: FAIL because product card metadata still renders raw entitlement keys for known values

- [ ] **Step 3: Write minimal implementation**

```ts
<div className="meta">
  {product.entitlements.map((entitlement) => {
    const entitlementCopy = getPlatformEntitlementCopy(entitlement);

    return (
      <span key={entitlement}>
        {isUnknownPlatformEntitlement(entitlement) ? entitlementCopy.rawKey : entitlementCopy.title}
      </span>
    );
  })}
</div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: PASS with the new product card metadata assertions green

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/public/platform-homepage-shelf.tsx apps/web/tests/platform-homepage-shelf.test.tsx
git commit -m "feat(web): align platform card entitlement copy"
```

### Task 2: Run full Web verification

**Files:**
- Test: `apps/web/tests/platform-homepage-shelf.test.tsx`

- [ ] **Step 1: Run focused shelf verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: PASS with all shelf tests green

- [ ] **Step 2: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`
Expected: PASS with all Web tests green

- [ ] **Step 3: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`
Expected: PASS with a successful Next.js production build

- [ ] **Step 4: Review git status**

Run: `git status --short`
Expected: clean working tree or only the intended card entitlement copy changes before the final report

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-platform-card-entitlement-copy.md
git commit -m "docs: add platform card entitlement copy plan"
```
