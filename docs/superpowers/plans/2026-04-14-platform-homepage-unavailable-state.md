# Platform Homepage Unavailable State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a clear homepage degraded-state panel when platform products fail to load, with a next-step action and a retry-later action.

**Architecture:** Move platform failure handling out of the “empty products” path in the homepage server component and into an explicit branch that renders a dedicated unavailable panel. Keep the unavailable UI in its own small component so homepage data loading stays readable and the degraded state remains local to the platform section.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Add failing tests for the homepage unavailable panel

**Files:**
- Create: `apps/web/tests/platform-unavailable-panel.test.tsx`
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import PlatformUnavailablePanel from '../components/public/platform-unavailable-panel';

test('renders platform unavailable actions', () => {
  render(<PlatformUnavailablePanel />);

  expect(screen.getByRole('heading', { name: '平台服务暂时不可用' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '先去查学校' })).toHaveAttribute('href', '#school-catalog');
  expect(screen.getByRole('link', { name: '稍后再试' })).toHaveAttribute('href', '/');
});
```

And update the homepage failure test:

```tsx
test('home page renders a platform unavailable panel when platform products fail', async () => {
  getSearchEntryMock.mockResolvedValue(...);
  listSchoolsMock.mockResolvedValue(...);
  listMajorsMock.mockResolvedValue(...);
  listPlatformProductsMock.mockRejectedValue(new Error('platform down'));

  render(await HomePage());

  expect(screen.getByRole('heading', { name: '平台服务暂时不可用' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '先去查学校' })).toHaveAttribute('href', '#school-catalog');
  expect(screen.getByRole('link', { name: '稍后再试' })).toHaveAttribute('href', '/');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-unavailable-panel.test.tsx tests/public-pages.test.tsx`
Expected: FAIL because `PlatformUnavailablePanel` does not exist and the homepage still converts platform failures into `{ items: [] }`

- [ ] **Step 3: Write minimal implementation**

```tsx
// apps/web/components/public/platform-unavailable-panel.tsx
import Link from 'next/link';

export default function PlatformUnavailablePanel() {
  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <div className="label">平台服务</div>
      <h2 className="panel-title">平台服务暂时不可用</h2>
      <p>产品方案和能力预览暂时无法加载，你可以先继续查看学校、专业和地区信息。</p>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
        <Link href="#school-catalog" className="chip">先去查学校</Link>
        <Link href="/" className="chip">稍后再试</Link>
      </div>
    </section>
  );
}
```

And update homepage data branching:

```tsx
let productPayload: { items: PlatformProduct[] } | null = null;

try {
  productPayload = await listPlatformProducts();
} catch {
  productPayload = null;
}

{productPayload ? (
  <PlatformHomepageShelf apiBaseUrl={apiBaseUrl} products={productPayload.items} />
) : (
  <PlatformUnavailablePanel />
)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-unavailable-panel.test.tsx tests/public-pages.test.tsx`
Expected: PASS with the new unavailable-panel behavior covered

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/public/platform-unavailable-panel.tsx apps/web/tests/platform-unavailable-panel.test.tsx apps/web/app/page.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): add platform homepage unavailable state"
```

### Task 2: Preserve homepage navigation target

**Files:**
- Modify: `apps/web/app/page.tsx`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
expect(screen.getByRole('heading', { name: '学校速查' }).closest('article')).toHaveAttribute('id', 'school-catalog');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`
Expected: FAIL because the school section does not yet expose the anchor target

- [ ] **Step 3: Write minimal implementation**

```tsx
<article id="school-catalog" className="panel">
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/app/page.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): anchor platform unavailable panel actions"
```

### Task 3: Full Web verification

**Files:**
- Test: `apps/web/tests/platform-unavailable-panel.test.tsx`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Run focused verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-unavailable-panel.test.tsx tests/public-pages.test.tsx`
Expected: PASS

- [ ] **Step 2: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`
Expected: PASS with all Web tests green

- [ ] **Step 3: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`
Expected: PASS with a successful Next.js production build

- [ ] **Step 4: Review git status**

Run: `git status --short`
Expected: clean working tree or only the intended unavailable-state changes before the final report

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-platform-homepage-unavailable-state.md
git commit -m "docs: add platform homepage unavailable state plan"
```
