# Web Admin Review Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a server-rendered admin dashboard in the web app that lists pending review items and supports approve and reject actions against the admin API.

**Architecture:** Keep the admin dashboard server-rendered with a small server-only API client and lightweight server actions. Expand `DashboardShell` into a presentational component for queue, empty, and error states first, then add API client and action helpers, then wire the `/admin` page to fetch data and refresh after review actions.

**Tech Stack:** Next.js App Router, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Expand DashboardShell To Render Review Queue States

**Files:**
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Test: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Write the failing test**

Replace `apps/web/tests/admin-dashboard.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react';

import DashboardShell, {
  type AdminReviewItem,
} from '../components/admin/dashboard-shell';

const queueItems: AdminReviewItem[] = [
  {
    id: 11,
    entity_type: 'school',
    entity_id: 101,
    candidate_version: 2,
    diff_summary: ['summary', 'strengths'],
    priority: 'normal',
    review_status: 'pending_review',
    reviewed_by: null,
    reviewed_at: null,
    review_note: null,
    created_at: '2026-04-13T09:00:00Z',
  },
];

test('renders admin dashboard heading and review queue items', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={queueItems}
      approveAction={async () => {}}
      rejectAction={async () => {}}
    />,
  );

  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('待审核内容')).toBeInTheDocument();
  expect(screen.getByText('school #101')).toBeInTheDocument();
  expect(screen.getByText('summary, strengths')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '通过' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '驳回' })).toBeInTheDocument();
});

test('renders empty state when there are no pending items', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      approveAction={async () => {}}
      rejectAction={async () => {}}
    />,
  );

  expect(screen.getByText('当前没有待审核内容')).toBeInTheDocument();
});

test('renders error state when queue loading fails', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      queueError="审核队列加载失败，请稍后重试"
      approveAction={async () => {}}
      rejectAction={async () => {}}
    />,
  );

  expect(screen.getByText('审核队列加载失败，请稍后重试')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`

Expected: `FAIL` because `DashboardShell` does not yet accept queue props, render queue rows, or show empty and error states.

- [ ] **Step 3: Write minimal implementation**

Update `apps/web/components/admin/dashboard-shell.tsx` to:

```tsx
export type AdminReviewItem = {
  id: number;
  entity_type: string;
  entity_id: number;
  candidate_version: number | null;
  diff_summary: string[];
  priority: string;
  review_status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  created_at: string;
};

type DashboardShellProps = {
  title: string;
  queueItems: AdminReviewItem[];
  queueError?: string;
  approveAction: (formData: FormData) => Promise<void>;
  rejectAction: (formData: FormData) => Promise<void>;
};

const cards = ['待审核内容', '最近发布', '抓取状态'];

export default function DashboardShell({
  title,
  queueItems,
  queueError,
  approveAction,
  rejectAction,
}: DashboardShellProps) {
  return (
    <main>
      <h1>{title}</h1>
      <section>
        {cards.map((card) => (
          <article key={card}>
            <h2>{card}</h2>
          </article>
        ))}
      </section>

      <section aria-labelledby="review-queue-heading">
        <h2 id="review-queue-heading">待审核队列</h2>

        {queueError ? <p>{queueError}</p> : null}

        {!queueError && queueItems.length === 0 ? <p>当前没有待审核内容</p> : null}

        {!queueError && queueItems.length > 0 ? (
          <div>
            {queueItems.map((item) => (
              <article key={item.id}>
                <h3>{`${item.entity_type} #${item.entity_id}`}</h3>
                <p>{item.diff_summary.join(', ')}</p>
                <p>{`优先级: ${item.priority}`}</p>
                <p>{`候选版本: ${item.candidate_version ?? '未提供'}`}</p>
                <p>{`创建时间: ${item.created_at}`}</p>

                <form action={approveAction}>
                  <input type="hidden" name="queueId" value={item.id} />
                  <input type="hidden" name="reviewedBy" value="web-admin" />
                  <button type="submit">通过</button>
                </form>

                <form action={rejectAction}>
                  <input type="hidden" name="queueId" value={item.id} />
                  <input type="hidden" name="reviewedBy" value="web-admin" />
                  <input type="text" name="reviewNote" aria-label={`驳回备注 ${item.id}`} />
                  <button type="submit">驳回</button>
                </form>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx`

Expected: `PASS` with 3 passing tests.

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-dashboard.test.tsx
git commit -m "feat(web): render admin review queue states"
```

### Task 2: Add Server-Only Admin Review API Client And Review Actions

**Files:**
- Create: `apps/web/lib/admin-review-api.ts`
- Create: `apps/web/app/(admin)/admin/actions.ts`
- Create: `apps/web/tests/admin-review-api.test.ts`
- Test: `apps/web/tests/admin-review-api.test.ts`

- [ ] **Step 1: Write the failing test**

Create `apps/web/tests/admin-review-api.test.ts` with:

```ts
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
}));

import { revalidatePath } from 'next/cache';

import {
  approveReviewQueueItem,
  listReviewQueue,
  rejectReviewQueueItem,
} from '../lib/admin-review-api';
import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
} from '../app/(admin)/admin/actions';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  process.env.GAOKAO_AGENT_API_URL = 'http://api.example.com';
  process.env.GAOKAO_AGENT_ADMIN_TOKEN = 'secret-token';
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete process.env.GAOKAO_AGENT_API_URL;
  delete process.env.GAOKAO_AGENT_ADMIN_TOKEN;
});

test('listReviewQueue sends authenticated request and returns items', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      items: [
        {
          id: 21,
          entity_type: 'school',
          entity_id: 201,
          candidate_version: 5,
          diff_summary: ['summary'],
          priority: 'normal',
          review_status: 'pending_review',
          reviewed_by: null,
          reviewed_at: null,
          review_note: null,
          created_at: '2026-04-13T09:00:00Z',
        },
      ],
    }),
  });

  const items = await listReviewQueue();

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/review-queue',
    expect.objectContaining({
      headers: expect.objectContaining({
        'x-admin-token': 'secret-token',
      }),
      cache: 'no-store',
    }),
  );
  expect(items).toHaveLength(1);
  expect(items[0]?.id).toBe(21);
});

test('approveReviewQueueItem posts reviewer identity', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      id: 21,
      entity_type: 'school',
      entity_id: 201,
      candidate_version: 5,
      diff_summary: ['summary'],
      priority: 'normal',
      review_status: 'approved',
      reviewed_by: 'web-admin',
      reviewed_at: '2026-04-13T09:05:00Z',
      review_note: null,
      created_at: '2026-04-13T09:00:00Z',
    }),
  });

  await approveReviewQueueItem(21, 'web-admin');

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/review-queue/21/approve',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
        'x-admin-token': 'secret-token',
      }),
      body: JSON.stringify({ reviewed_by: 'web-admin' }),
    }),
  );
});

test('rejectReviewQueueItem posts optional review note', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      id: 22,
      entity_type: 'major',
      entity_id: 301,
      candidate_version: 6,
      diff_summary: ['risks'],
      priority: 'high',
      review_status: 'rejected',
      reviewed_by: 'web-admin',
      reviewed_at: '2026-04-13T09:06:00Z',
      review_note: 'source stale',
      created_at: '2026-04-13T09:01:00Z',
    }),
  });

  await rejectReviewQueueItem(22, 'web-admin', 'source stale');

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/review-queue/22/reject',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        reviewed_by: 'web-admin',
        review_note: 'source stale',
      }),
    }),
  );
});

test('approveReviewQueueAction revalidates the admin page after success', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      id: 23,
      entity_type: 'school',
      entity_id: 401,
      candidate_version: 7,
      diff_summary: ['summary'],
      priority: 'normal',
      review_status: 'approved',
      reviewed_by: 'web-admin',
      reviewed_at: '2026-04-13T09:07:00Z',
      review_note: null,
      created_at: '2026-04-13T09:02:00Z',
    }),
  });

  const formData = new FormData();
  formData.set('queueId', '23');
  formData.set('reviewedBy', 'web-admin');

  await approveReviewQueueAction(formData);

  expect(revalidatePath).toHaveBeenCalledWith('/admin');
});

test('rejectReviewQueueAction returns an error message when the API fails', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: false,
    status: 500,
    text: async () => 'server error',
  });

  const formData = new FormData();
  formData.set('queueId', '24');
  formData.set('reviewedBy', 'web-admin');
  formData.set('reviewNote', 'needs manual review');

  const result = await rejectReviewQueueAction(formData);

  expect(result).toBe('审核操作失败，请稍后重试');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts`

Expected: `FAIL` because the API client module and review action module do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `apps/web/lib/admin-review-api.ts` with:

```ts
import 'server-only';

import type { AdminReviewItem } from '../components/admin/dashboard-shell';

const API_URL = process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';
const ADMIN_TOKEN = process.env.GAOKAO_AGENT_ADMIN_TOKEN ?? 'dev-admin-token';

const buildHeaders = (contentType?: string) => {
  const headers: Record<string, string> = {
    'x-admin-token': ADMIN_TOKEN,
  };

  if (contentType) {
    headers['Content-Type'] = contentType;
  }

  return headers;
};

const parseResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
};

export async function listReviewQueue(): Promise<AdminReviewItem[]> {
  const response = await fetch(`${API_URL}/api/admin/review-queue`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{ items: AdminReviewItem[] }>(response);
  return payload.items;
}

export async function approveReviewQueueItem(
  queueId: number,
  reviewedBy: string,
): Promise<AdminReviewItem> {
  const response = await fetch(`${API_URL}/api/admin/review-queue/${queueId}/approve`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({ reviewed_by: reviewedBy }),
  });
  return parseResponse<AdminReviewItem>(response);
}

export async function rejectReviewQueueItem(
  queueId: number,
  reviewedBy: string,
  reviewNote?: string,
): Promise<AdminReviewItem> {
  const response = await fetch(`${API_URL}/api/admin/review-queue/${queueId}/reject`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      reviewed_by: reviewedBy,
      review_note: reviewNote || undefined,
    }),
  });
  return parseResponse<AdminReviewItem>(response);
}
```

Create `apps/web/app/(admin)/admin/actions.ts` with:

```ts
'use server';

import { revalidatePath } from 'next/cache';

import {
  approveReviewQueueItem,
  rejectReviewQueueItem,
} from '../../../lib/admin-review-api';

const parseQueueId = (rawValue: FormDataEntryValue | null): number => {
  const value = typeof rawValue === 'string' ? Number.parseInt(rawValue, 10) : Number.NaN;
  if (Number.isNaN(value)) {
    throw new Error('queue id is required');
  }
  return value;
};

export async function approveReviewQueueAction(formData: FormData): Promise<string | undefined> {
  try {
    const queueId = parseQueueId(formData.get('queueId'));
    const reviewedBy = String(formData.get('reviewedBy') ?? 'web-admin');

    await approveReviewQueueItem(queueId, reviewedBy);
    revalidatePath('/admin');
    return undefined;
  } catch {
    return '审核操作失败，请稍后重试';
  }
}

export async function rejectReviewQueueAction(formData: FormData): Promise<string | undefined> {
  try {
    const queueId = parseQueueId(formData.get('queueId'));
    const reviewedBy = String(formData.get('reviewedBy') ?? 'web-admin');
    const reviewNote = String(formData.get('reviewNote') ?? '').trim();

    await rejectReviewQueueItem(queueId, reviewedBy, reviewNote || undefined);
    revalidatePath('/admin');
    return undefined;
  } catch {
    return '审核操作失败，请稍后重试';
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts`

Expected: `PASS` with 5 passing tests.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/admin-review-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/tests/admin-review-api.test.ts
git commit -m "feat(web): add admin review api client and actions"
```

### Task 3: Wire The Admin Page To The API And Verify Rendered Dashboard

**Files:**
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Create: `apps/web/tests/admin-page.test.tsx`
- Test: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `apps/web/tests/admin-page.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const listReviewQueueMock = vi.fn();

vi.mock('../lib/admin-review-api', () => ({
  listReviewQueue: listReviewQueueMock,
}));

vi.mock('../app/(admin)/admin/actions', () => ({
  approveReviewQueueAction: async () => undefined,
  rejectReviewQueueAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';

beforeEach(() => {
  listReviewQueueMock.mockReset();
});

test('renders queue items returned by the admin api client', async () => {
  listReviewQueueMock.mockResolvedValue([
    {
      id: 31,
      entity_type: 'school',
      entity_id: 901,
      candidate_version: 3,
      diff_summary: ['summary'],
      priority: 'normal',
      review_status: 'pending_review',
      reviewed_by: null,
      reviewed_at: null,
      review_note: null,
      created_at: '2026-04-13T09:10:00Z',
    },
  ]);

  render(await AdminPage());

  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('school #901')).toBeInTheDocument();
});

test('renders queue error when loading fails', async () => {
  listReviewQueueMock.mockRejectedValue(new Error('boom'));

  render(await AdminPage());

  expect(screen.getByText('审核队列加载失败，请稍后重试')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-page.test.tsx`

Expected: `FAIL` because the admin page does not yet fetch queue items or pass error and action props into `DashboardShell`.

- [ ] **Step 3: Write minimal implementation**

Update `apps/web/app/(admin)/admin/page.tsx` to:

```tsx
import DashboardShell from '../../../components/admin/dashboard-shell';
import { listReviewQueue } from '../../../lib/admin-review-api';

import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
} from './actions';

export default async function AdminPage() {
  try {
    const queueItems = await listReviewQueue();

    return (
      <DashboardShell
        title="内容运营后台"
        queueItems={queueItems}
        approveAction={approveReviewQueueAction}
        rejectAction={rejectReviewQueueAction}
      />
    );
  } catch {
    return (
      <DashboardShell
        title="内容运营后台"
        queueItems={[]}
        queueError="审核队列加载失败，请稍后重试"
        approveAction={approveReviewQueueAction}
        rejectAction={rejectReviewQueueAction}
      />
    );
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-dashboard.test.tsx tests/admin-review-api.test.ts tests/admin-page.test.tsx`

Expected: `PASS` with 10 passing tests.

- [ ] **Step 5: Commit**

```bash
git add apps/web/app/(admin)/admin/page.tsx apps/web/tests/admin-page.test.tsx
git commit -m "feat(web): wire admin page to review api"
```
