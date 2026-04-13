# Platform Unavailable Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the homepage platform unavailable panel’s retry action refresh the current route instead of navigating to `/`.

**Architecture:** Convert the unavailable panel into a lightweight client component that uses `useRouter()` from Next navigation for the retry action while preserving the existing school anchor link. Keep homepage render branching unchanged and cover the behavior in the panel test by mocking `router.refresh()`.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Add failing retry-action test coverage

**Files:**
- Modify: `apps/web/tests/platform-unavailable-panel.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';

const refreshMock = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    refresh: refreshMock,
  }),
}));

test('triggers router refresh when retry is clicked', () => {
  render(<PlatformUnavailablePanel />);

  fireEvent.click(screen.getByRole('button', { name: '稍后再试' }));

  expect(refreshMock).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-unavailable-panel.test.tsx`
Expected: FAIL because the retry action still renders as a link to `/`

- [ ] **Step 3: Write minimal implementation**

```tsx
'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function PlatformUnavailablePanel() {
  const router = useRouter();

  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <div className="label">平台服务</div>
      <h2 className="panel-title">平台服务暂时不可用</h2>
      <p>产品方案和能力预览暂时无法加载，你可以先继续查看学校、专业和地区信息。</p>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
        <Link href="#school-catalog" className="chip">
          先去查学校
        </Link>
        <button type="button" className="chip" onClick={() => router.refresh()}>
          稍后再试
        </button>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-unavailable-panel.test.tsx`
Expected: PASS with the anchor assertion and refresh-action assertion both green

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/public/platform-unavailable-panel.tsx apps/web/tests/platform-unavailable-panel.test.tsx
git commit -m "feat(web): refresh platform unavailable panel"
```

### Task 2: Run full Web verification

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
Expected: clean working tree or only the intended unavailable-refresh changes before the final report

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-platform-unavailable-refresh.md
git commit -m "docs: add platform unavailable refresh plan"
```
