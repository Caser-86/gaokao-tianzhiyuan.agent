# Platform Shelf Copy Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align homepage shelf tests with the same Chinese product naming and description semantics used by the real platform product data.

**Architecture:** Keep the cleanup entirely inside the shelf test file by replacing English placeholder fixtures with Chinese product copy that matches the API-layer semantics. Preserve the current behavior coverage and only adjust assertions that directly depend on product-facing copy.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Update shelf test fixtures to use realistic product copy

**Files:**
- Modify: `apps/web/tests/platform-homepage-shelf.test.tsx`
- Test: `apps/web/tests/platform-homepage-shelf.test.tsx`

- [ ] **Step 1: Write the failing test adjustment**

```ts
const homepageProducts = [
  {
    slug: 'insight-weekly',
    name: '志愿快报订阅',
    description: '适合持续接收学校、专业和风险变化提醒。',
    entitlements: ['school_basic_access'],
  },
  {
    slug: 'deep-dive-pack',
    name: '深度报告包',
    description: '适合需要学校、专业、地区和就业深度分析的家庭。',
    entitlements: ['school_deep_dive_access'],
  },
];
```

And update at least one existing CTA assertion to use the Chinese product name:

```ts
fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: FAIL because the CTA query still looks for the old English button label

- [ ] **Step 3: Write minimal implementation**

```ts
fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));
fireEvent.click(screen.getByRole('button', { name: '选择深度报告包' }));
```

Update the other button assertions in the same file to the new Chinese names while keeping all behavior checks unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: PASS with all shelf tests green

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/platform-homepage-shelf.test.tsx
git commit -m "test(web): align shelf copy fixtures"
```

### Task 2: Run full Web verification

**Files:**
- Test: `apps/web/tests/platform-homepage-shelf.test.tsx`

- [ ] **Step 1: Run focused shelf verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: PASS

- [ ] **Step 2: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`
Expected: PASS with all Web tests green

- [ ] **Step 3: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`
Expected: PASS with a successful Next.js production build

- [ ] **Step 4: Review git status**

Run: `git status --short`
Expected: clean working tree or only the intended shelf test copy changes before the final report

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-platform-shelf-copy-consistency.md
git commit -m "docs: add platform shelf copy consistency plan"
```
