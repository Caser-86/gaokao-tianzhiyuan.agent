# Platform Success CTA Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the generic selection wording in homepage platform CTA buttons with preview-oriented copy that matches the actual interaction.

**Architecture:** Keep the platform homepage shelf behavior unchanged and only adjust the CTA label logic in the product cards. Update the shelf tests to query the new wording and verify that a selected product switches to the selected-preview label.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Add failing tests for preview-oriented CTA copy

**Files:**
- Modify: `apps/web/tests/platform-homepage-shelf.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
test('uses preview-oriented CTA copy for unselected and selected products', () => {
  renderShelf();

  const addButton = screen.getByRole('button', {
    name: '加入能力预览志愿快报订阅',
  });

  expect(addButton).toBeInTheDocument();

  fireEvent.click(addButton);

  expect(
    screen.getByRole('button', {
      name: '已加入能力预览志愿快报订阅',
    }),
  ).toBeInTheDocument();
});
```

Update the existing button queries in the same test file from the old `选择...` wording to the new `加入能力预览...` wording.

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: FAIL because the component still renders `选择...` / `取消选择...`

- [ ] **Step 3: Write minimal implementation**

```tsx
{isSelected
  ? `已加入能力预览${product.name}`
  : `加入能力预览${product.name}`}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: PASS with the updated CTA wording coverage green

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/public/platform-homepage-shelf.tsx apps/web/tests/platform-homepage-shelf.test.tsx
git commit -m "feat(web): refine platform success cta copy"
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
Expected: clean working tree or only the intended CTA-copy changes before the final report

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-platform-success-cta-copy.md
git commit -m "docs: add platform success cta copy plan"
```
