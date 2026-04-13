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

test('rejectReviewQueueAction resolves without returning a value when the API fails', async () => {
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

  expect(result).toBeUndefined();
});
