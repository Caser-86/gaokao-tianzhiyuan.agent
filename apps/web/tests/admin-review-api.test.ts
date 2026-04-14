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
  updateMajorRotationRule,
  updateSchoolRotationRule,
} from '../lib/admin-featured-content-api';
import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
  updateFeaturedMajorAction,
  updateFeaturedSchoolAction,
  updateMajorRotationAction,
  updateSchoolRotationAction,
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

test('listFeaturedContent sends authenticated request, supports preview_date, and maps admin config', async () => {
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
      rotation: {
        schools: {
          enabled: true,
          frequency_days: 1,
          window_size: 2,
          ordered_slugs: ['southeast-university', 'west-china-medical-center'],
        },
        majors: {
          enabled: false,
          frequency_days: 3,
          window_size: 4,
          ordered_slugs: ['clinical-medicine'],
        },
      },
      preview: {
        today: {
          schools: [
            {
              slug: 'southeast-university',
              name: '东南大学',
            },
          ],
          majors: [
            {
              slug: 'clinical-medicine',
              name: '临床医学',
            },
          ],
        },
        next: {
          schools: [
            {
              slug: 'west-china-medical-center',
              name: '华西医学中心',
            },
          ],
          majors: [
            {
              slug: 'computer-science',
              name: '计算机科学与技术',
            },
          ],
        },
        schedule: [
          {
            date: '2026-04-14',
            weekday: '周二',
            schools: [
              {
                slug: 'southeast-university',
                name: '东南大学',
              },
            ],
            majors: [
              {
                slug: 'clinical-medicine',
                name: '临床医学',
              },
            ],
          },
          {
            date: '2026-04-15',
            weekday: '周三',
            schools: [
              {
                slug: 'west-china-medical-center',
                name: '华西医学中心',
              },
            ],
            majors: [
              {
                slug: 'computer-science',
                name: '计算机科学与技术',
              },
            ],
          },
        ],
        selected_date: {
          date: '2026-04-15',
          weekday: '周三',
          schools: [
            {
              slug: 'west-china-medical-center',
              name: '华西医学中心',
            },
          ],
          majors: [
            {
              slug: 'computer-science',
              name: '计算机科学与技术',
            },
          ],
        },
        selected_date_error: null,
      },
    }),
  });

  const payload = await listFeaturedContent('2026-04-15');

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content?preview_date=2026-04-15',
    expect.objectContaining({
      headers: expect.objectContaining({
        'x-admin-token': 'secret-token',
      }),
      cache: 'no-store',
    }),
  );
  expect(payload.preview.selectedDate).toEqual({
    date: '2026-04-15',
    weekday: '周三',
    schools: [
      {
        slug: 'west-china-medical-center',
        name: '华西医学中心',
      },
    ],
    majors: [
      {
        slug: 'computer-science',
        name: '计算机科学与技术',
      },
    ],
  });
  expect(payload.preview.selectedDateError).toBeNull();
});

test('listFeaturedContent maps local selected-date validation errors', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      schools: [],
      majors: [],
      rotation: {
        schools: {
          enabled: false,
          frequency_days: 1,
          window_size: 1,
          ordered_slugs: [],
        },
        majors: {
          enabled: false,
          frequency_days: 1,
          window_size: 1,
          ordered_slugs: [],
        },
      },
      preview: {
        today: {
          schools: [],
          majors: [],
        },
        next: {
          schools: [],
          majors: [],
        },
        schedule: [],
        selected_date: null,
        selected_date_error: '预览日期格式无效',
      },
    }),
  });

  const payload = await listFeaturedContent('2026-99-99');

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content?preview_date=2026-99-99',
    expect.any(Object),
  );
  expect(payload.preview.selectedDate).toBeNull();
  expect(payload.preview.selectedDateError).toBe('预览日期格式无效');
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

test('updateSchoolRotationRule posts rotation state', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      enabled: true,
      frequency_days: 2,
      window_size: 3,
      ordered_slugs: ['west-china-medical-center', 'southeast-university'],
    }),
  });

  await updateSchoolRotationRule({
    enabled: true,
    frequencyDays: 2,
    windowSize: 3,
    orderedSlugs: ['west-china-medical-center', 'southeast-university'],
  });

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/rotation/schools',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
        'x-admin-token': 'secret-token',
      }),
      body: JSON.stringify({
        enabled: true,
        frequency_days: 2,
        window_size: 3,
        ordered_slugs: ['west-china-medical-center', 'southeast-university'],
      }),
    }),
  );
});

test('updateMajorRotationRule posts rotation state', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      enabled: false,
      frequency_days: 4,
      window_size: 2,
      ordered_slugs: ['clinical-medicine'],
    }),
  });

  await updateMajorRotationRule({
    enabled: false,
    frequencyDays: 4,
    windowSize: 2,
    orderedSlugs: ['clinical-medicine'],
  });

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/rotation/majors',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
        'x-admin-token': 'secret-token',
      }),
      body: JSON.stringify({
        enabled: false,
        frequency_days: 4,
        window_size: 2,
        ordered_slugs: ['clinical-medicine'],
      }),
    }),
  );
});

test('updateFeaturedSchoolAction revalidates the admin page after success', async () => {
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

  expect(revalidatePath).toHaveBeenCalledWith('/admin');
});

test('updateFeaturedMajorAction revalidates the admin page after success', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      slug: 'clinical-medicine',
      name: '临床医学',
      is_featured: true,
    }),
  });

  const formData = new FormData();
  formData.set('slug', 'clinical-medicine');
  formData.set('isFeatured', 'on');

  await updateFeaturedMajorAction(formData);

  expect(revalidatePath).toHaveBeenCalledWith('/admin');
});

test('updateSchoolRotationAction revalidates the admin page after success', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      enabled: true,
      frequency_days: 2,
      window_size: 3,
      ordered_slugs: ['west-china-medical-center', 'southeast-university'],
    }),
  });

  const formData = new FormData();
  formData.set('enabled', 'on');
  formData.set('frequencyDays', '2');
  formData.set('windowSize', '3');
  formData.set('orderedSlugs', 'west-china-medical-center\nsoutheast-university');

  await updateSchoolRotationAction(formData);

  expect(revalidatePath).toHaveBeenCalledWith('/admin');
});

test('updateMajorRotationAction revalidates the admin page after success', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      enabled: false,
      frequency_days: 4,
      window_size: 2,
      ordered_slugs: ['clinical-medicine'],
    }),
  });

  const formData = new FormData();
  formData.set('frequencyDays', '4');
  formData.set('windowSize', '2');
  formData.set('orderedSlugs', 'clinical-medicine');

  await updateMajorRotationAction(formData);

  expect(revalidatePath).toHaveBeenCalledWith('/admin');
});
