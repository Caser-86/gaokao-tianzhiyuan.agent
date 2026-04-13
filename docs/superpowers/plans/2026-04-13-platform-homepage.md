# Platform Homepage Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the public homepage to the existing platform product and event APIs without adding checkout or entitlement flows.

**Architecture:** Add a small platform API client in `apps/web/lib`, then extend the homepage to render a product shelf alongside the existing search, school, and major content. Isolate interaction tracking inside a dedicated client component so homepage data loading stays server-rendered and product/event failures remain locally contained.

**Tech Stack:** Next.js 15.4.0 app router, React 19.1.0, Vitest, Testing Library, existing FastAPI platform endpoints

---

### Task 1: Read Platform Product Data On The Homepage

**Files:**
- Create: `apps/web/lib/platform-api.ts`
- Create: `apps/web/tests/platform-api.test.ts`
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing platform client and homepage tests**

```ts
// apps/web/tests/platform-api.test.ts
import { beforeEach, expect, test, vi } from 'vitest';

import { listPlatformProducts } from '../lib/platform-api';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  process.env.GAOKAO_AGENT_API_URL = 'http://api.example.com';
});

test('listPlatformProducts reads platform products from the API', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      items: [
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
      ],
    }),
  });

  const payload = await listPlatformProducts();

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/platform/products',
    expect.objectContaining({ cache: 'no-store' }),
  );
  expect(payload.items[0]?.name).toBe('志愿快报订阅');
});
```

```ts
// apps/web/tests/public-pages.test.tsx
const { listPlatformProductsMock } = vi.hoisted(() => ({
  listPlatformProductsMock: vi.fn(),
}));

vi.mock('../lib/platform-api', () => ({
  listPlatformProducts: listPlatformProductsMock,
}));

beforeEach(() => {
  listPlatformProductsMock.mockReset();
});

test('home page renders platform products when the product catalog is available', async () => {
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

  expect(screen.getByRole('heading', { name: '精选服务' })).toBeInTheDocument();
  expect(screen.getByText('志愿快报订阅')).toBeInTheDocument();
  expect(screen.getByText('持续跟踪学校、专业和风险变化。')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-api.test.ts tests/public-pages.test.tsx` from `apps/web`

Expected: FAIL because `../lib/platform-api` does not exist and the homepage does not render the product shelf yet.

- [ ] **Step 3: Write the minimal implementation**

```ts
// apps/web/lib/platform-api.ts
import 'server-only';

export type PlatformProduct = {
  slug: string;
  name: string;
  description: string;
  entitlements: string[];
};

const getPlatformApiUrl = (): string =>
  process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';

export async function listPlatformProducts(): Promise<{ items: PlatformProduct[] }> {
  const response = await fetch(`${getPlatformApiUrl()}/api/platform/products`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as { items: PlatformProduct[] };
}
```

```ts
// apps/web/app/page.tsx
import { listPlatformProducts } from '../lib/platform-api';

const [searchEntry, schoolPayload, majorPayload, productPayload] = await Promise.all([
  getSearchEntry(),
  listSchools(),
  listMajors(),
  listPlatformProducts().catch(() => ({ items: [] })),
]);

<section className="panel" style={{ marginTop: 28 }}>
  <h2 className="panel-title">精选服务</h2>
  {productPayload.items.length === 0 ? (
    <p>平台服务暂时不可用，请稍后再试。</p>
  ) : (
    <div className="catalog-list">
      {productPayload.items.map((product) => (
        <article key={product.slug} className="catalog-card">
          <strong>{product.name}</strong>
          <p>{product.description}</p>
          <div className="meta">
            {product.entitlements.map((entitlement) => (
              <span key={entitlement}>{entitlement}</span>
            ))}
          </div>
        </article>
      ))}
    </div>
  )}
</section>
```

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-api.test.ts tests/public-pages.test.tsx` from `apps/web`

Expected: PASS with the platform client returning data and the homepage rendering the product shelf.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/platform-api.ts apps/web/tests/platform-api.test.ts apps/web/app/page.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): render platform products on homepage"
```

### Task 2: Track Homepage Platform Interactions

**Files:**
- Create: `apps/web/lib/platform-events.ts`
- Create: `apps/web/components/public/platform-homepage-shelf.tsx`
- Create: `apps/web/tests/platform-homepage-shelf.test.tsx`
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/components/public/search-entry.tsx`
- Modify: `apps/web/tests/public-content.test.tsx`
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing interaction tests**

```ts
// apps/web/tests/platform-homepage-shelf.test.tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { trackPlatformEventMock } = vi.hoisted(() => ({
  trackPlatformEventMock: vi.fn(),
}));

vi.mock('../lib/platform-events', () => ({
  trackPlatformEvent: trackPlatformEventMock,
}));

import PlatformHomepageShelf from '../components/public/platform-homepage-shelf';

beforeEach(() => {
  trackPlatformEventMock.mockReset();
  trackPlatformEventMock.mockResolvedValue(undefined);
});

test('tracks product CTA clicks without blocking the button interaction', async () => {
  render(
    <PlatformHomepageShelf
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

  fireEvent.click(screen.getByRole('button', { name: '查看志愿快报订阅' }));

  await waitFor(() => {
    expect(trackPlatformEventMock).toHaveBeenCalledWith({
      eventName: 'product_cta_clicked',
      step: 'homepage_product_shelf',
      metadata: { productSlug: 'insight-weekly' },
    });
  });
});
```

```ts
// apps/web/tests/public-content.test.tsx
const { trackPlatformEventMock } = vi.hoisted(() => ({
  trackPlatformEventMock: vi.fn(),
}));

vi.mock('../lib/platform-events', () => ({
  trackPlatformEvent: trackPlatformEventMock,
}));

test('tracks quick prompt clicks on the homepage entry', async () => {
  trackPlatformEventMock.mockResolvedValue(undefined);

  render(
    <SearchEntry
      title="高考志愿助手"
      description="帮你看学校、专业、地域、就业和坑点。"
      quickPrompts={['查学校']}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: '查学校' }));

  await waitFor(() => {
    expect(trackPlatformEventMock).toHaveBeenCalledWith({
      eventName: 'quick_prompt_clicked',
      step: 'homepage_masthead',
      metadata: { prompt: '查学校' },
    });
  });
});
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx tests/public-content.test.tsx` from `apps/web`

Expected: FAIL because the tracking helper and client components do not exist yet, and `SearchEntry` still renders quick prompts as passive text.

- [ ] **Step 3: Write the minimal implementation**

```ts
// apps/web/lib/platform-events.ts
export type PlatformEventPayload = {
  eventName: string;
  step: string;
  metadata: Record<string, string>;
};

const getPlatformApiUrl = (): string =>
  process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL ??
  process.env.GAOKAO_AGENT_API_URL ??
  'http://127.0.0.1:8000';

export async function trackPlatformEvent(payload: PlatformEventPayload): Promise<void> {
  await fetch(`${getPlatformApiUrl()}/api/platform/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_name: payload.eventName,
      step: payload.step,
      metadata: payload.metadata,
    }),
  }).catch(() => undefined);
}
```

```tsx
// apps/web/components/public/platform-homepage-shelf.tsx
'use client';

import { trackPlatformEvent } from '../../lib/platform-events';
import type { PlatformProduct } from '../../lib/platform-api';

type PlatformHomepageShelfProps = {
  products: PlatformProduct[];
};

export default function PlatformHomepageShelf({ products }: PlatformHomepageShelfProps) {
  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <h2 className="panel-title">精选服务</h2>
      {products.length === 0 ? (
        <p>平台服务暂时不可用，请稍后再试。</p>
      ) : (
        <div className="catalog-list">
          {products.map((product) => (
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
                onClick={() => {
                  void trackPlatformEvent({
                    eventName: 'product_cta_clicked',
                    step: 'homepage_product_shelf',
                    metadata: { productSlug: product.slug },
                  });
                }}
              >
                {`查看${product.name}`}
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
```

```tsx
// apps/web/components/public/search-entry.tsx
'use client';

import { trackPlatformEvent } from '../../lib/platform-events';

{quickPrompts.map((prompt) => (
  <button
    key={prompt}
    type="button"
    className="chip"
    onClick={() => {
      void trackPlatformEvent({
        eventName: 'quick_prompt_clicked',
        step: 'homepage_masthead',
        metadata: { prompt },
      });
    }}
  >
    {prompt}
  </button>
))}
```

```tsx
// apps/web/app/page.tsx
import PlatformHomepageShelf from '../components/public/platform-homepage-shelf';

<PlatformHomepageShelf products={productPayload.items} />
```

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `node ./node_modules/vitest/vitest.mjs run tests/platform-homepage-shelf.test.tsx tests/public-content.test.tsx tests/public-pages.test.tsx` from `apps/web`

Expected: PASS with quick prompts rendered as clickable controls and product CTA clicks posting events through the mocked helper.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/platform-events.ts apps/web/components/public/platform-homepage-shelf.tsx apps/web/tests/platform-homepage-shelf.test.tsx apps/web/app/page.tsx apps/web/components/public/search-entry.tsx apps/web/tests/public-content.test.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): track homepage platform interactions"
```
