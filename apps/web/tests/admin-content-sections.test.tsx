import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const {
  listReviewQueueMock,
  listFeaturedContentMock,
  listRankingReferencesMock,
  listContentSummariesMock,
  listContentSectionsMock,
} = vi.hoisted(() => ({
  listReviewQueueMock: vi.fn(),
  listFeaturedContentMock: vi.fn(),
  listRankingReferencesMock: vi.fn(),
  listContentSummariesMock: vi.fn(),
  listContentSectionsMock: vi.fn(),
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

vi.mock('../lib/admin-content-summary-api', () => ({
  listContentSummaries: listContentSummariesMock,
}));

vi.mock('../lib/admin-content-sections-api', () => ({
  listContentSections: listContentSectionsMock,
}));

vi.mock('../app/(admin)/admin/actions', () => ({
  approveReviewQueueAction: async () => undefined,
  rejectReviewQueueAction: async () => undefined,
  updateFeaturedSchoolAction: async () => undefined,
  updateFeaturedMajorAction: async () => undefined,
  updateSchoolSummaryAction: async () => undefined,
  updateMajorSummaryAction: async () => undefined,
  updateSchoolSectionsAction: async () => undefined,
  updateMajorSectionsAction: async () => undefined,
  updateSchoolRankingReferencesAction: async () => undefined,
  updateMajorRankingReferencesAction: async () => undefined,
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';

beforeEach(() => {
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
  listRankingReferencesMock.mockReset();
  listContentSummariesMock.mockReset();
  listContentSectionsMock.mockReset();
});

test('renders school and major content section editors in admin', async () => {
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
    schools: [],
    majors: [],
  });
  listContentSummariesMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listContentSectionsMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        sections: [
          {
            type: 'highlights',
            title: '学校亮点',
            items: ['资源密集'],
          },
        ],
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        sections: [
          {
            type: 'fit_for',
            title: '适合人群',
            items: ['接受长周期培养'],
          },
        ],
      },
    ],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校正文编辑' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业正文编辑' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('学校亮点')).toBeInTheDocument();
  expect(screen.getByDisplayValue('highlights')).toBeInTheDocument();
  expect(screen.getByDisplayValue('资源密集')).toBeInTheDocument();
  expect(screen.getByDisplayValue('适合人群')).toBeInTheDocument();
  expect(screen.getByDisplayValue('fit_for')).toBeInTheDocument();
  expect(screen.getByDisplayValue('接受长周期培养')).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: '保存正文' })).toHaveLength(2);
});
