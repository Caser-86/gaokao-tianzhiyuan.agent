# Platform Entitlement Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw entitlement keys in the homepage entitlement preview with user-readable Chinese copy while preserving fallback behavior for unknown keys.

**Architecture:** Add a focused Web helper that maps raw entitlement keys to display copy, then update the homepage product shelf to render that copy instead of raw keys. Keep the FastAPI payload unchanged and verify the behavior through helper tests, shelf tests, the full Web test suite, and a production build.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Add entitlement copy helper coverage

**Files:**
- Create: `apps/web/lib/platform-entitlement-labels.ts`
- Create: `apps/web/tests/platform-entitlement-labels.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { expect, test } from 'vitest';

import { getPlatformEntitlementCopy } from '../lib/platform-entitlement-labels';

test('returns user-facing copy for a known entitlement key', () => {
  expect(getPlatformEntitlementCopy('school_basic_access')).toEqual({
    title: '院校基础信息查看',
    description: '查看院校的基础介绍、招生范围和核心数据。',
    rawKey: 'school_basic_access',
  });
});

test('returns fallback copy and preserves the raw key for unknown entitlements', () => {
  expect(getPlatformEntitlementCopy('future_capability')).toEqual({
    title: '更多平台能力',
    description: '该能力已开通，详细说明即将补充。',
    rawKey: 'future_capability',
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-entitlement-labels.test.ts`
Expected: FAIL with module-not-found or export-not-found for `../lib/platform-entitlement-labels`

- [ ] **Step 3: Write minimal implementation**

```ts
export type PlatformEntitlementCopy = {
  title: string;
  description: string;
  rawKey: string;
};

const ENTITLEMENT_COPY: Record<string, Omit<PlatformEntitlementCopy, 'rawKey'>> = {
  school_basic_access: {
    title: '院校基础信息查看',
    description: '查看院校的基础介绍、招生范围和核心数据。',
  },
  major_basic_access: {
    title: '专业基础信息查看',
    description: '查看专业的培养方向、选科要求和基础解读。',
  },
  risk_alert_access: {
    title: '风险提醒',
    description: '获得志愿填报中的波动提醒和风险提示。',
  },
  school_deep_dive_access: {
    title: '院校深度分析',
    description: '查看院校分数趋势、录取层次和深度解读。',
  },
  major_deep_dive_access: {
    title: '专业深度分析',
    description: '查看专业前景、课程结构和竞争情况分析。',
  },
  region_compare_access: {
    title: '地区对比分析',
    description: '对比不同地区的院校机会、录取难度和选择空间。',
  },
};

export function getPlatformEntitlementCopy(key: string): PlatformEntitlementCopy {
  const copy = ENTITLEMENT_COPY[key];

  if (copy) {
    return {
      ...copy,
      rawKey: key,
    };
  }

  return {
    title: '更多平台能力',
    description: '该能力已开通，详细说明即将补充。',
    rawKey: key,
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-entitlement-labels.test.ts`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/platform-entitlement-labels.ts apps/web/tests/platform-entitlement-labels.test.ts
git commit -m "feat(web): add platform entitlement copy labels"
```

### Task 2: Render entitlement preview with user-facing copy

**Files:**
- Modify: `apps/web/components/public/platform-homepage-shelf.tsx`
- Modify: `apps/web/tests/platform-homepage-shelf.test.tsx`
- Test: `apps/web/tests/platform-homepage-shelf.test.tsx`

- [ ] **Step 1: Write the failing test**

```ts
test('renders user-facing entitlement copy for known keys', async () => {
  evaluatePlatformEntitlementsMock.mockResolvedValueOnce({
    product_slugs: ['insight-weekly'],
    entitlements: ['school_basic_access'],
  });

  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
      ]}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));

  const previewSection = screen.getByRole('heading', { name: '能力预览' }).closest('section');

  await waitFor(() => {
    expect(
      within(previewSection as HTMLElement).getByText('院校基础信息查看'),
    ).toBeInTheDocument();
  });

  expect(
    within(previewSection as HTMLElement).getByText('查看院校的基础介绍、招生范围和核心数据。'),
  ).toBeInTheDocument();
});

test('renders fallback copy and keeps the raw key for unknown entitlements', async () => {
  evaluatePlatformEntitlementsMock.mockResolvedValueOnce({
    product_slugs: ['insight-weekly'],
    entitlements: ['future_capability'],
  });

  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
      ]}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));

  const previewSection = screen.getByRole('heading', { name: '能力预览' }).closest('section');

  await waitFor(() => {
    expect(
      within(previewSection as HTMLElement).getByText('更多平台能力'),
    ).toBeInTheDocument();
  });

  expect(
    within(previewSection as HTMLElement).getByText('该能力已开通，详细说明即将补充。'),
  ).toBeInTheDocument();
  expect(within(previewSection as HTMLElement).getByText('future_capability')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: FAIL because the shelf still renders raw entitlement keys instead of user-facing copy

- [ ] **Step 3: Write minimal implementation**

```ts
import { getPlatformEntitlementCopy } from '../../lib/platform-entitlement-labels';

// inside the success render branch
<ul className="feature-list">
  {entitlementState.entitlements.map((entitlement) => {
    const entitlementCopy = getPlatformEntitlementCopy(entitlement);

    return (
      <li key={entitlement}>
        <strong>{entitlementCopy.title}</strong>
        <p>{entitlementCopy.description}</p>
        {entitlementCopy.title === '更多平台能力' ? <small>{entitlementCopy.rawKey}</small> : null}
      </li>
    );
  })}
</ul>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx`
Expected: PASS with the updated entitlement preview assertions

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/public/platform-homepage-shelf.tsx apps/web/tests/platform-homepage-shelf.test.tsx
git commit -m "feat(web): render platform entitlement copy"
```

### Task 3: Full Web verification

**Files:**
- Test: `apps/web/tests/platform-entitlement-labels.test.ts`
- Test: `apps/web/tests/platform-homepage-shelf.test.tsx`

- [ ] **Step 1: Run focused entitlement verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-entitlement-labels.test.ts tests/platform-homepage-shelf.test.tsx`
Expected: PASS with the helper and shelf tests green

- [ ] **Step 2: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`
Expected: PASS with all Web tests green

- [ ] **Step 3: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`
Expected: PASS with a successful Next.js production build

- [ ] **Step 4: Review git status**

Run: `git status --short`
Expected: clean working tree or only the intended entitlement-copy changes before the final commit

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/platform-entitlement-labels.ts apps/web/components/public/platform-homepage-shelf.tsx apps/web/tests/platform-entitlement-labels.test.ts apps/web/tests/platform-homepage-shelf.test.tsx docs/superpowers/plans/2026-04-14-platform-entitlement-copy.md
git commit -m "docs: add platform entitlement copy plan"
```
