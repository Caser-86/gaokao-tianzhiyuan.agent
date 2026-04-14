import { render, screen, within } from '@testing-library/react';
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
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';

beforeEach(() => {
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
});

test('renders queue items, selected-date preview, next preview, and schedule returned by the admin api client', async () => {
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
        name: '内容学校',
        isFeatured: true,
        heroImageUrl: 'https://cdn.example.com/southeast.jpg',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '内容专业',
        isFeatured: true,
      },
    ],
    rotation: {
      schools: {
        enabled: true,
        frequencyDays: 1,
        windowSize: 2,
        orderedSlugs: ['southeast-university', 'west-china-medical-center'],
      },
      majors: {
        enabled: false,
        frequencyDays: 3,
        windowSize: 4,
        orderedSlugs: ['clinical-medicine'],
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
      selectedDate: {
        date: '2026-04-20',
        weekday: '周一',
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
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-20',
      }),
    }),
  );

  expect(listFeaturedContentMock).toHaveBeenCalledWith('2026-04-20');
  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('school #901')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByText('内容学校')).toBeInTheDocument();
  expect(screen.getByDisplayValue('https://cdn.example.com/southeast.jpg')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业展示配置' })).toBeInTheDocument();
  expect(screen.getByText('内容专业')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('学校轮换顺序')).toHaveValue(
    'southeast-university\nwest-china-medical-center',
  );
  expect(screen.getByRole('heading', { name: '专业轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('专业轮换顺序')).toHaveValue('clinical-medicine');
  expect(screen.getByRole('heading', { name: '今日展示学校' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '今日展示专业' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '下一轮展示学校' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '下一轮展示专业' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '指定日期预览' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('2026-04-20')).toBeInTheDocument();

  const selectedSchoolPreview = screen.getByRole('region', { name: '该日展示学校' });
  const selectedMajorPreview = screen.getByRole('region', { name: '该日展示专业' });

  expect(within(selectedSchoolPreview).getByText('东南大学')).toBeInTheDocument();
  expect(within(selectedSchoolPreview).getByText('southeast-university')).toBeInTheDocument();
  expect(within(selectedMajorPreview).getByText('临床医学')).toBeInTheDocument();
  expect(within(selectedMajorPreview).getByText('clinical-medicine')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '未来 7 天轮换预览' })).toBeInTheDocument();
  expect(screen.getByText('2026-04-14')).toBeInTheDocument();
  expect(screen.getByText('周二')).toBeInTheDocument();
  expect(screen.getByText('2026-04-15')).toBeInTheDocument();
  expect(screen.getByText('周三')).toBeInTheDocument();
});

test('renders selected-date validation error when preview_date is invalid', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
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
      selectedDate: null,
      selectedDateError: '预览日期格式无效',
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-99-99',
      }),
    }),
  );

  expect(listFeaturedContentMock).toHaveBeenCalledWith('2026-99-99');
  expect(screen.getByText('预览日期格式无效')).toBeInTheDocument();
});

test('renders queue error when loading fails', async () => {
  listReviewQueueMock.mockRejectedValue(new Error('boom'));
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
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
      selectedDate: null,
      selectedDateError: null,
    },
  });

  render(await AdminPage({}));

  expect(screen.getByText('审核队列加载失败，请稍后重试')).toBeInTheDocument();
});

test('renders empty preview states when today, next, and selected-date preview are empty', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
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
      selectedDate: {
        date: '2026-04-20',
        weekday: '周一',
        schools: [],
        majors: [],
      },
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-20',
      }),
    }),
  );

  expect(screen.getByText('当前没有可展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有可展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有未来轮换预览')).toBeInTheDocument();
  expect(screen.getByText('该日没有展示学校')).toBeInTheDocument();
  expect(screen.getByText('该日没有展示专业')).toBeInTheDocument();
});
