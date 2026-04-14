import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { listReviewQueueMock, listFeaturedContentMock } = vi.hoisted(() => ({
  listReviewQueueMock: vi.fn(),
  listFeaturedContentMock: vi.fn(),
}));

vi.mock('../lib/admin-review-api', () => ({
  listReviewQueue: listReviewQueueMock,
}));

vi.mock('../lib/admin-featured-content-api', () => ({
  listFeaturedContent: listFeaturedContentMock,
}));

vi.mock('../app/(admin)/admin/actions', () => ({
  approveReviewQueueAction: async () => undefined,
  rejectReviewQueueAction: async () => undefined,
  updateFeaturedSchoolAction: async () => undefined,
  updateFeaturedMajorAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';

beforeEach(() => {
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
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
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        isFeatured: true,
        heroImageUrl: 'https://cdn.example.com/southeast.jpg',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        isFeatured: true,
      },
    ],
  });

  render(await AdminPage());

  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('school #901')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByText('东南大学')).toBeInTheDocument();
  expect(screen.getByDisplayValue('https://cdn.example.com/southeast.jpg')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业展示配置' })).toBeInTheDocument();
  expect(screen.getByText('临床医学')).toBeInTheDocument();
});

test('renders queue error when loading fails', async () => {
  listReviewQueueMock.mockRejectedValue(new Error('boom'));
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
  });

  render(await AdminPage());

  expect(screen.getByText('审核队列加载失败，请稍后重试')).toBeInTheDocument();
});
