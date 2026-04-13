# Platform Entitlements Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an anonymous homepage entitlement preview that lets users select platform products and see the merged capabilities returned by `/api/platform/entitlements/evaluate`.

**Architecture:** Keep homepage product loading on the server, and extend the existing client-side `PlatformHomepageShelf` to own selection state, entitlement evaluation, and local empty/loading/error/success rendering. Add a small `platform-entitlements` helper that mirrors the existing platform API and event helper patterns, and continue passing an explicit `apiBaseUrl` from the server page into client components.

**Tech Stack:** Next.js 15.4.0 app router, React 19.1.0, Vitest, Testing Library, existing FastAPI platform endpoints

---

### Task 1: Add The Platform Entitlements API Helper

**Files:**
- Create: `apps/web/lib/platform-entitlements.ts`
- Create: `apps/web/tests/platform-entitlements.test.ts`

- [ ] **Step 1: Write the failing helper test**

```ts
// apps/web/tests/platform-entitlements.test.ts
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { evaluatePlatformEntitlements } from '../lib/platform-entitlements';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  delete process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL;
});

test('evaluatePlatformEntitlements posts selected products to the entitlement API', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      product_slugs: ['insight-weekly', 'deep-dive-pack'],
      entitlements: ['major_basic_access', 'school_basic_access'],
    }),
  });

  const payload = await evaluatePlatformEntitlements(
    ['insight-weekly', 'deep-dive-pack'],
    'https://api.gaokao.test',
  );

  expect(fetchMock).toHaveBeenCalledWith(
    'https://api.gaokao.test/api/platform/entitlements/evaluate',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_slugs: ['insight-weekly', 'deep-dive-pack'],
      }),
    },
  );
  expect(payload.entitlements).toEqual(['major_basic_access', 'school_basic_access']);
});
```

- [ ] **Step 2: Run the helper test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-entitlements.test.ts`

Expected: FAIL because `../lib/platform-entitlements` does not exist yet.

- [ ] **Step 3: Write the minimal helper implementation**

```ts
// apps/web/lib/platform-entitlements.ts
export type PlatformEntitlementsPayload = {
  product_slugs: string[];
  entitlements: string[];
};

const getPlatformApiUrl = (apiBaseUrl?: string): string =>
  apiBaseUrl ??
  process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL ??
  process.env.GAOKAO_AGENT_API_URL ??
  'http://127.0.0.1:8000';

export async function evaluatePlatformEntitlements(
  productSlugs: string[],
  apiBaseUrl?: string,
): Promise<PlatformEntitlementsPayload> {
  const response = await fetch(`${getPlatformApiUrl(apiBaseUrl)}/api/platform/entitlements/evaluate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      product_slugs: productSlugs,
    }),
  });

  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as PlatformEntitlementsPayload;
}
```

- [ ] **Step 4: Run the helper test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-entitlements.test.ts`

Expected: PASS with the helper posting to `/api/platform/entitlements/evaluate`.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/platform-entitlements.ts apps/web/tests/platform-entitlements.test.ts
git commit -m "feat(web): add platform entitlements helper"
```

### Task 2: Add Multi-Select Entitlement Preview To The Homepage Shelf

**Files:**
- Modify: `apps/web/components/public/platform-homepage-shelf.tsx`
- Modify: `apps/web/tests/platform-homepage-shelf.test.tsx`
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing shelf tests**

```ts
// apps/web/tests/platform-homepage-shelf.test.tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const {
  evaluatePlatformEntitlementsMock,
  trackPlatformEventMock,
} = vi.hoisted(() => ({
  evaluatePlatformEntitlementsMock: vi.fn(),
  trackPlatformEventMock: vi.fn(),
}));

vi.mock('../lib/platform-entitlements', () => ({
  evaluatePlatformEntitlements: evaluatePlatformEntitlementsMock,
}));

vi.mock('../lib/platform-events', () => ({
  trackPlatformEvent: trackPlatformEventMock,
}));

import PlatformHomepageShelf from '../components/public/platform-homepage-shelf';

beforeEach(() => {
  evaluatePlatformEntitlementsMock.mockReset();
  evaluatePlatformEntitlementsMock.mockResolvedValue({
    product_slugs: ['insight-weekly'],
    entitlements: ['school_basic_access'],
  });
  trackPlatformEventMock.mockReset();
  trackPlatformEventMock.mockResolvedValue(undefined);
});

test('shows an empty prompt before any products are selected', () => {
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

  expect(screen.getByText('选择产品后查看能力包。')).toBeInTheDocument();
});

test('selecting products renders merged entitlements from the API', async () => {
  evaluatePlatformEntitlementsMock.mockResolvedValueOnce({
    product_slugs: ['insight-weekly', 'deep-dive-pack'],
    entitlements: ['major_basic_access', 'school_deep_dive_access'],
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
        {
          slug: 'deep-dive-pack',
          name: '深度报告包',
          description: '适合需要学校、专业、地域和就业深度分析的家庭。',
          entitlements: ['school_deep_dive_access'],
        },
      ]}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));
  fireEvent.click(screen.getByRole('button', { name: '选择深度报告包' }));

  await waitFor(() => {
    expect(evaluatePlatformEntitlementsMock).toHaveBeenLastCalledWith(
      ['insight-weekly', 'deep-dive-pack'],
      'https://api.gaokao.test',
    );
  });

  expect(screen.getByText('major_basic_access')).toBeInTheDocument();
  expect(screen.getByText('school_deep_dive_access')).toBeInTheDocument();
});

test('shows a local error when entitlement evaluation fails', async () => {
  evaluatePlatformEntitlementsMock.mockRejectedValueOnce(new Error('boom'));

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

  await waitFor(() => {
    expect(screen.getByText('能力预览加载失败，请稍后再试。')).toBeInTheDocument();
  });
});
```

```ts
// apps/web/tests/public-pages.test.tsx
test('home page renders API-backed search, catalog, and product data', async () => {
  getSearchEntryMock.mockResolvedValue({
    title: '高考志愿助手',
    description: '帮助考生和家长快速看学校、专业、地域与就业。',
    quickPrompts: ['查学校', '查专业'],
  });
  listSchoolsMock.mockResolvedValue({
    items: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        region: '江苏',
        city: '南京',
        tags: ['985'],
        summary: '工科见长。',
      },
    ],
    total: 1,
  });
  listMajorsMock.mockResolvedValue({
    items: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        discipline: '医学',
        recommendedRegions: ['江苏', '浙江'],
        summary: '培养周期长。',
      },
    ],
    total: 1,
  });
  listPlatformProductsMock.mockResolvedValue({
    items: [
      {
        slug: 'insight-weekly',
        name: '志愿快报订阅',
        description: '持续跟踪学校、专业和风险变化。',
        entitlements: ['school_basic_access', 'risk_alert_access'],
      },
    ],
  });

  render(await HomePage());

  expect(screen.getByRole('heading', { name: '高考志愿助手' })).toBeInTheDocument();
  expect(screen.getByText('东南大学')).toBeInTheDocument();
  expect(screen.getByText('临床医学')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '精选服务' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '选择志愿快报订阅' })).toBeInTheDocument();
  expect(screen.getByText('选择产品后查看能力包。')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the shelf tests to verify they fail**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx tests/public-pages.test.tsx`

Expected: FAIL because the shelf does not yet support selection state, entitlement evaluation, or the preview states.

- [ ] **Step 3: Write the minimal entitlement preview implementation**

```tsx
// apps/web/components/public/platform-homepage-shelf.tsx
'use client';

import { useEffect, useState } from 'react';

import type { PlatformProduct } from '../../lib/platform-api';
import { evaluatePlatformEntitlements } from '../../lib/platform-entitlements';
import { trackPlatformEvent } from '../../lib/platform-events';

type PlatformHomepageShelfProps = {
  apiBaseUrl: string;
  products: PlatformProduct[];
};

type EntitlementState =
  | { status: 'idle'; entitlements: string[] }
  | { status: 'loading'; entitlements: string[] }
  | { status: 'success'; entitlements: string[] }
  | { status: 'error'; entitlements: string[] };

export default function PlatformHomepageShelf({
  apiBaseUrl,
  products,
}: PlatformHomepageShelfProps) {
  const [selectedProductSlugs, setSelectedProductSlugs] = useState<string[]>([]);
  const [entitlementState, setEntitlementState] = useState<EntitlementState>({
    status: 'idle',
    entitlements: [],
  });

  useEffect(() => {
    if (selectedProductSlugs.length === 0) {
      setEntitlementState({ status: 'idle', entitlements: [] });
      return;
    }

    let cancelled = false;
    setEntitlementState((current) => ({
      status: 'loading',
      entitlements: current.entitlements,
    }));

    void evaluatePlatformEntitlements(selectedProductSlugs, apiBaseUrl)
      .then((payload) => {
        if (cancelled) {
          return;
        }

        setEntitlementState({
          status: 'success',
          entitlements: payload.entitlements,
        });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        setEntitlementState({
          status: 'error',
          entitlements: [],
        });
      });

    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, selectedProductSlugs]);

  const toggleProduct = (productSlug: string) => {
    setSelectedProductSlugs((current) =>
      current.includes(productSlug)
        ? current.filter((slug) => slug !== productSlug)
        : [...current, productSlug],
    );
  };

  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <h2 className="panel-title">精选服务</h2>
      {products.length === 0 ? (
        <p>平台服务暂时不可用，请稍后再试。</p>
      ) : (
        <>
          <div className="catalog-list">
            {products.map((product) => {
              const isSelected = selectedProductSlugs.includes(product.slug);

              return (
                <article key={product.slug} className="catalog-card">
                  <strong>{product.name}</strong>
                  <p>{product.description}</p>
                  <div className="meta">
                    {product.entitlements.map((entitlement) => (
                      <span key={entitlement}>{entitlement}</span>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="chip"
                    aria-pressed={isSelected}
                    onClick={() => {
                      toggleProduct(product.slug);
                      void trackPlatformEvent(
                        {
                          eventName: 'product_cta_clicked',
                          step: 'homepage_product_shelf',
                          metadata: { productSlug: product.slug },
                        },
                        apiBaseUrl,
                      );
                    }}
                  >
                    {isSelected ? `取消选择${product.name}` : `选择${product.name}`}
                  </button>
                </article>
              );
            })}
          </div>

          <section className="panel" style={{ marginTop: 20 }}>
            <h3 className="panel-title">能力预览</h3>
            {selectedProductSlugs.length === 0 ? (
              <p>选择产品后查看能力包。</p>
            ) : entitlementState.status === 'loading' ? (
              <p>正在加载能力预览...</p>
            ) : entitlementState.status === 'error' ? (
              <p>能力预览加载失败，请稍后再试。</p>
            ) : (
              <ul className="feature-list">
                {entitlementState.entitlements.map((entitlement) => (
                  <li key={entitlement}>{entitlement}</li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  );
}
```

- [ ] **Step 4: Run the shelf tests to verify they pass**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx tests/public-pages.test.tsx`

Expected: PASS with product selection driving entitlement evaluation and the homepage preserving the new shelf entry state.

- [ ] **Step 5: Run the broader Web verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-entitlements.test.ts tests/platform-homepage-shelf.test.tsx tests/public-pages.test.tsx tests/public-content.test.tsx`

Expected: PASS with entitlement preview, homepage rendering, and existing quick-prompt tracking coverage all green.

- [ ] **Step 6: Commit**

```bash
git add apps/web/components/public/platform-homepage-shelf.tsx apps/web/tests/platform-homepage-shelf.test.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): preview platform entitlements on homepage"
```

### Task 3: Run Final Verification For The Homepage Entitlements Preview

**Files:**
- No code changes expected

- [ ] **Step 1: Run the full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`

Expected: PASS with all `apps/web` tests green.

- [ ] **Step 2: Run the production build**

Run: `node ./node_modules/next/dist/bin/next build`

Expected: PASS with the existing constrained-environment SWC warning still tolerated but the build finishing successfully.

- [ ] **Step 3: Commit only if verification required supporting updates**

```bash
git status --short
```

Expected: no output. If any verification-only cleanup is needed, commit it separately before finishing.
