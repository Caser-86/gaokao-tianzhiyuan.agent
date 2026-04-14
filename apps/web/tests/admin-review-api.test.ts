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
  listFeaturedContent,
  updateFeaturedMajor,
  updateFeaturedSchool,
} from '../lib/admin-featured-content-api';
import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
  updateFeaturedMajorAction,
  updateFeaturedSchoolAction,
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

test('listFeaturedContent sends authenticated request and maps admin config', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      schools: [
        {
          slug: 'southeast-university',
          name: '东南大学',
          is_featured: true,
          hero_image_url: 'https://cdn.example.com/southeast.jpg',
        },
      ],
      majors: [
        {
          slug: 'clinical-medicine',
          name: '临床医学',
          is_featured: true,
        },
      ],
    }),
  });

  const payload = await listFeaturedContent();

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content',
    expect.objectContaining({
      headers: expect.objectContaining({
        'x-admin-token': 'secret-token',
      }),
      cache: 'no-store',
    }),
  );
  expect(payload.schools[0]).toEqual({
    slug: 'southeast-university',
    name: '东南大学',
    isFeatured: true,
    heroImageUrl: 'https://cdn.example.com/southeast.jpg',
  });
  expect(payload.majors[0]).toEqual({
    slug: 'clinical-medicine',
    name: '临床医学',
    isFeatured: true,
  });
});

test('updateFeaturedSchool posts feature state and image url', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      slug: 'southeast-university',
      name: '东南大学',
      is_featured: true,
      hero_image_url: 'https://cdn.example.com/southeast.jpg',
    }),
  });

  await updateFeaturedSchool('southeast-university', true, 'https://cdn.example.com/southeast.jpg');

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/schools/southeast-university',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
        'x-admin-token': 'secret-token',
      }),
      body: JSON.stringify({
        is_featured: true,
        hero_image_url: 'https://cdn.example.com/southeast.jpg',
      }),
    }),
  );
});

test('updateFeaturedMajor posts feature state', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      slug: 'clinical-medicine',
      name: '临床医学',
      is_featured: false,
    }),
  });

  await updateFeaturedMajor('clinical-medicine', false);

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/majors/clinical-medicine',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
        'x-admin-token': 'secret-token',
      }),
      body: JSON.stringify({
        is_featured: false,
      }),
    }),
  );
});

test('updateFeaturedSchoolAction revalidates admin and home pages after success', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      slug: 'southeast-university',
      name: '东南大学',
      is_featured: true,
      hero_image_url: 'https://cdn.example.com/southeast.jpg',
    }),
  });

  const formData = new FormData();
  formData.set('slug', 'southeast-university');
  formData.set('isFeatured', 'on');
  formData.set('heroImageUrl', 'https://cdn.example.com/southeast.jpg');

  await updateFeaturedSchoolAction(formData);

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/schools/southeast-university',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        is_featured: true,
        hero_image_url: 'https://cdn.example.com/southeast.jpg',
      }),
    }),
  );
  expect(revalidatePath).toHaveBeenCalledWith('/admin');
  expect(revalidatePath).toHaveBeenCalledWith('/');
});

test('updateFeaturedMajorAction revalidates admin and home pages after success', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      slug: 'clinical-medicine',
      name: '临床医学',
      is_featured: false,
    }),
  });

  const formData = new FormData();
  formData.set('slug', 'clinical-medicine');

  await updateFeaturedMajorAction(formData);

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/majors/clinical-medicine',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        is_featured: false,
      }),
    }),
  );
  expect(revalidatePath).toHaveBeenCalledWith('/admin');
  expect(revalidatePath).toHaveBeenCalledWith('/');
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
