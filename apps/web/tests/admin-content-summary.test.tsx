import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const {
  listReviewQueueMock,
  listFeaturedContentMock,
  listRankingReferencesMock,
  listContentSummariesMock,
  listContentSectionsMock,
  listRelatedContentMock,
} = vi.hoisted(() => ({
  listReviewQueueMock: vi.fn(),
  listFeaturedContentMock: vi.fn(),
  listRankingReferencesMock: vi.fn(),
  listContentSummariesMock: vi.fn(),
  listContentSectionsMock: vi.fn(),
  listRelatedContentMock: vi.fn(),
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

vi.mock('../lib/admin-related-content-api', () => ({
  listRelatedContent: listRelatedContentMock,
}));

vi.mock('../app/(admin)/admin/actions', () => ({
  approveReviewQueueAction: async () => undefined,
  rejectReviewQueueAction: async () => undefined,
  updateFeaturedSchoolAction: async () => undefined,
  updateFeaturedMajorAction: async () => undefined,
  updateSchoolRankingReferencesAction: async () => undefined,
  updateMajorRankingReferencesAction: async () => undefined,
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
  updateSchoolSummaryAction: async () => undefined,
  updateMajorSummaryAction: async () => undefined,
  updateSchoolSectionsAction: async () => undefined,
  updateMajorSectionsAction: async () => undefined,
  updateSchoolRelatedContentAction: async () => undefined,
  updateMajorRelatedContentAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';
import DashboardShell from '../components/admin/dashboard-shell';

beforeEach(() => {
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
  listRankingReferencesMock.mockReset();
  listContentSummariesMock.mockReset();
  listContentSectionsMock.mockReset();
  listRelatedContentMock.mockReset();
  listContentSectionsMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listRelatedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
});

test('renders school and major summary editors in admin', async () => {
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
    schools: [
      {
        slug: 'southeast-university',
        name: 'Southeast University',
        summary: 'school summary',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: 'Clinical Medicine',
        summary: 'major summary',
      },
    ],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校摘要编辑' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业摘要编辑' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('school summary')).toBeInTheDocument();
  expect(screen.getByDisplayValue('major summary')).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: '保存摘要' })).toHaveLength(2);
});

test('surfaces missing summary coverage and prioritizes scheduled gaps', () => {
  const { container } = render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: 'Southeast University',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
          isFeatured: true,
        },
      ]}
      schoolRotation={{
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      }}
      majorRotation={{
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      }}
      featuredSchoolPreview={[
        {
          slug: 'southeast-university',
          name: 'Southeast University',
        },
      ]}
      featuredMajorPreview={[
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
        },
      ]}
      nextFeaturedSchoolPreview={[
        {
          slug: 'wuhan-university',
          name: 'Wuhan University',
        },
      ]}
      nextFeaturedMajorPreview={[
        {
          slug: 'software-engineering',
          name: 'Software Engineering',
        },
      ]}
      featuredSchedule={[]}
      summarySchools={[
        {
          slug: 'zhejiang-university',
          name: 'Zhejiang University',
          summary: 'filled summary',
        },
        {
          slug: 'wuhan-university',
          name: 'Wuhan University',
          summary: '',
        },
        {
          slug: 'southeast-university',
          name: 'Southeast University',
          summary: '',
        },
      ]}
      summaryMajors={[
        {
          slug: 'finance',
          name: 'Finance',
          summary: 'filled summary',
        },
        {
          slug: 'software-engineering',
          name: 'Software Engineering',
          summary: '',
        },
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
          summary: '',
        },
      ]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolSummaryAction={async () => undefined}
      updateMajorSummaryAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const schoolSection = container.querySelector('[data-testid="school-summary-section"]');
  const majorSection = container.querySelector('[data-testid="major-summary-section"]');
  const missingSchoolSection = container.querySelector('[data-testid="missing-school-summary-section"]');
  const missingMajorSection = container.querySelector('[data-testid="missing-major-summary-section"]');

  expect(
    Array.from(schoolSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['Southeast University', 'Wuhan University', 'Zhejiang University']);
  expect(
    Array.from(majorSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['Clinical Medicine', 'Software Engineering', 'Finance']);
  expect(
    Array.from(
      missingSchoolSection?.querySelectorAll('a[href^="#school-summary-"]') ?? [],
      (link) => link.getAttribute('href'),
    ),
  ).toEqual(['#school-summary-southeast-university', '#school-summary-wuhan-university']);
  expect(
    Array.from(
      missingMajorSection?.querySelectorAll('a[href^="#major-summary-"]') ?? [],
      (link) => link.getAttribute('href'),
    ),
  ).toEqual(['#major-summary-clinical-medicine', '#major-summary-software-engineering']);
});

test('filters summary editors down to scheduled gaps only and preserves date shortcuts', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: 'Southeast University',
        isFeatured: true,
        heroImageUrl: '',
      },
      {
        slug: 'wuhan-university',
        name: 'Wuhan University',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: 'Clinical Medicine',
        isFeatured: true,
      },
      {
        slug: 'software-engineering',
        name: 'Software Engineering',
        isFeatured: true,
      },
    ],
    rotation: {
      schools: {
        enabled: true,
        frequencyDays: 1,
        windowSize: 2,
        orderedSlugs: ['southeast-university', 'wuhan-university'],
      },
      majors: {
        enabled: true,
        frequencyDays: 1,
        windowSize: 2,
        orderedSlugs: ['clinical-medicine', 'software-engineering'],
      },
    },
    preview: {
      today: {
        schools: [{ slug: 'southeast-university', name: 'Southeast University' }],
        majors: [{ slug: 'clinical-medicine', name: 'Clinical Medicine' }],
      },
      next: {
        schools: [{ slug: 'wuhan-university', name: 'Wuhan University' }],
        majors: [{ slug: 'software-engineering', name: 'Software Engineering' }],
      },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });
  listRankingReferencesMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listContentSectionsMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listRelatedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listContentSummariesMock.mockResolvedValue({
    schools: [
      {
        slug: 'zhejiang-university',
        name: 'Zhejiang University',
        summary: '',
      },
      {
        slug: 'wuhan-university',
        name: 'Wuhan University',
        summary: '',
      },
      {
        slug: 'southeast-university',
        name: 'Southeast University',
        summary: '',
      },
    ],
    majors: [
      {
        slug: 'finance',
        name: 'Finance',
        summary: '',
      },
      {
        slug: 'software-engineering',
        name: 'Software Engineering',
        summary: '',
      },
      {
        slug: 'clinical-medicine',
        name: 'Clinical Medicine',
        summary: '',
      },
    ],
  });

  const { container } = render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-18',
        scheduled_missing_school_summaries: '1',
        scheduled_missing_major_summaries: '1',
      } as never),
    }),
  );

  const schoolSection = container.querySelector('[data-testid="school-summary-section"]');
  const majorSection = container.querySelector('[data-testid="major-summary-section"]');
  const allHrefs = Array.from(container.querySelectorAll('a'), (link) => link.getAttribute('href') ?? '');

  expect(
    Array.from(schoolSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['Southeast University', 'Wuhan University']);
  expect(
    Array.from(majorSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['Clinical Medicine', 'Software Engineering']);

  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-18') &&
        href.includes('scheduled_missing_school_summaries=0') &&
        href.includes('scheduled_missing_major_summaries=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-18') &&
        href.includes('scheduled_missing_school_summaries=1') &&
        href.includes('scheduled_missing_major_summaries=0'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-17') &&
        href.includes('scheduled_missing_school_summaries=1') &&
        href.includes('scheduled_missing_major_summaries=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-14') &&
        href.includes('scheduled_missing_school_summaries=1') &&
        href.includes('scheduled_missing_major_summaries=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-19') &&
        href.includes('scheduled_missing_school_summaries=1') &&
        href.includes('scheduled_missing_major_summaries=1'),
    ),
  ).toBe(true);
});
