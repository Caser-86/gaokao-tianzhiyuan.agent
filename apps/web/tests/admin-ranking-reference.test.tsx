import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const {
  listReviewQueueMock,
  listFeaturedContentMock,
  listRankingReferencesMock,
} = vi.hoisted(() => ({
  listReviewQueueMock: vi.fn(),
  listFeaturedContentMock: vi.fn(),
  listRankingReferencesMock: vi.fn(),
}));

vi.mock('../lib/admin-review-api', () => ({
  listReviewQueue: listReviewQueueMock,
}));

vi.mock('../lib/admin-featured-content-api', () => ({
  listFeaturedContent: listFeaturedContentMock,
}));

vi.mock('../lib/admin-ranking-reference-api', () => ({
  listRankingReferences: listRankingReferencesMock,
}));

vi.mock('../app/(admin)/admin/actions', () => ({
  approveReviewQueueAction: async () => undefined,
  rejectReviewQueueAction: async () => undefined,
  updateFeaturedSchoolAction: async () => undefined,
  updateFeaturedMajorAction: async () => undefined,
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
  updateSchoolRankingReferencesAction: async () => undefined,
  updateMajorRankingReferencesAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';

beforeEach(() => {
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
  listRankingReferencesMock.mockReset();
});

test('renders school and major ranking reference admin sections', async () => {
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
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });
  listRankingReferencesMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        rankingReferences: [
          {
            source: '软科中国大学排名',
            year: 2025,
            label: '全国第 15 名',
            scope: '综合类高校',
            note: '用于综合实力参考',
            url: 'https://example.com/rankings/southeast-university',
          },
        ],
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        rankingReferences: [
          {
            source: '教育部学科评估',
            year: 2023,
            label: 'A-',
            scope: '一级学科',
            note: '用于学科实力参考',
            url: 'https://example.com/rankings/clinical-medicine',
          },
        ],
      },
    ],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校榜单引用' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业榜单引用' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('软科中国大学排名')).toBeInTheDocument();
  expect(screen.getByDisplayValue('全国第 15 名')).toBeInTheDocument();
  expect(screen.getByDisplayValue('教育部学科评估')).toBeInTheDocument();
  expect(screen.getByDisplayValue('A-')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '保存学校榜单' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '保存专业榜单' })).toBeInTheDocument();
});
