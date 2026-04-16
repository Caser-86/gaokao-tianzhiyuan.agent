import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

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
  updateSchoolSummaryAction: async () => undefined,
  updateMajorSummaryAction: async () => undefined,
  updateSchoolSectionsAction: async () => undefined,
  updateMajorSectionsAction: async () => undefined,
  updateSchoolRelatedContentAction: async () => undefined,
  updateMajorRelatedContentAction: async () => undefined,
  updateSchoolRankingReferencesAction: async () => undefined,
  updateMajorRankingReferencesAction: async () => undefined,
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
  updateSmartAnalysisModeAction: async () => undefined,
  updateSmartAnalysisUserAction: async () => undefined,
  retryMediaAnalysisEventAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';
import DashboardShell from '../components/admin/dashboard-shell';

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-04-14T12:00:00Z'));
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
  listRankingReferencesMock.mockReset();
  listContentSummariesMock.mockReset();
  listContentSectionsMock.mockReset();
  listRelatedContentMock.mockReset();
  listRelatedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
});

afterEach(() => {
  vi.useRealTimers();
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
        name: 'Southeast University',
        sections: [
          {
            type: 'highlights',
            title: 'Highlights',
            items: ['strong resources'],
          },
        ],
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: 'Clinical Medicine',
        sections: [
          {
            type: 'fit_for',
            title: 'Fit For',
            items: ['long-cycle training'],
          },
        ],
      },
    ],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校正文编辑' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业正文编辑' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('Highlights')).toBeInTheDocument();
  expect(screen.getByDisplayValue('highlights')).toBeInTheDocument();
  expect(screen.getByDisplayValue('strong resources')).toBeInTheDocument();
  expect(screen.getByDisplayValue('Fit For')).toBeInTheDocument();
  expect(screen.getByDisplayValue('fit_for')).toBeInTheDocument();
  expect(screen.getByDisplayValue('long-cycle training')).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: '保存正文' })).toHaveLength(2);
});

test('surfaces missing section coverage and prioritizes scheduled gaps', () => {
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
      sectionSchools={[
        {
          slug: 'zhejiang-university',
          name: 'Zhejiang University',
          sections: [
            {
              type: 'highlights',
              title: 'Highlights',
              items: ['filled item'],
            },
          ],
        },
        {
          slug: 'wuhan-university',
          name: 'Wuhan University',
          sections: [],
        },
        {
          slug: 'southeast-university',
          name: 'Southeast University',
          sections: [],
        },
      ]}
      sectionMajors={[
        {
          slug: 'finance',
          name: 'Finance',
          sections: [
            {
              type: 'fit_for',
              title: 'Fit For',
              items: ['filled item'],
            },
          ],
        },
        {
          slug: 'software-engineering',
          name: 'Software Engineering',
          sections: [],
        },
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
          sections: [],
        },
      ]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolSectionsAction={async () => undefined}
      updateMajorSectionsAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const schoolSection = container.querySelector('[data-testid="school-sections-section"]');
  const majorSection = container.querySelector('[data-testid="major-sections-section"]');
  const missingSchoolSection = container.querySelector(
    '[data-testid="missing-school-sections-section"]',
  );
  const missingMajorSection = container.querySelector(
    '[data-testid="missing-major-sections-section"]',
  );

  expect(
    Array.from(schoolSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['Southeast University', 'Wuhan University', 'Zhejiang University']);
  expect(
    Array.from(majorSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['Clinical Medicine', 'Software Engineering', 'Finance']);
  expect(
    Array.from(
      missingSchoolSection?.querySelectorAll('a[href^="#school-sections-"]') ?? [],
      (link) => link.getAttribute('href'),
    ),
  ).toEqual(['#school-sections-southeast-university', '#school-sections-wuhan-university']);
  expect(
    Array.from(
      missingMajorSection?.querySelectorAll('a[href^="#major-sections-"]') ?? [],
      (link) => link.getAttribute('href'),
    ),
  ).toEqual(['#major-sections-clinical-medicine', '#major-sections-software-engineering']);
});

test('filters section editors down to scheduled gaps only and preserves date shortcuts', async () => {
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
  listContentSummariesMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listContentSectionsMock.mockResolvedValue({
    schools: [
      {
        slug: 'zhejiang-university',
        name: 'Zhejiang University',
        sections: [],
      },
      {
        slug: 'wuhan-university',
        name: 'Wuhan University',
        sections: [],
      },
      {
        slug: 'southeast-university',
        name: 'Southeast University',
        sections: [],
      },
    ],
    majors: [
      {
        slug: 'finance',
        name: 'Finance',
        sections: [],
      },
      {
        slug: 'software-engineering',
        name: 'Software Engineering',
        sections: [],
      },
      {
        slug: 'clinical-medicine',
        name: 'Clinical Medicine',
        sections: [],
      },
    ],
  });

  const { container } = render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-18',
        scheduled_missing_school_sections: '1',
        scheduled_missing_major_sections: '1',
      } as never),
    }),
  );

  const schoolSection = container.querySelector('[data-testid="school-sections-section"]');
  const majorSection = container.querySelector('[data-testid="major-sections-section"]');
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
        href.includes('scheduled_missing_school_sections=0') &&
        href.includes('scheduled_missing_major_sections=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-18') &&
        href.includes('scheduled_missing_school_sections=1') &&
        href.includes('scheduled_missing_major_sections=0'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-17') &&
        href.includes('scheduled_missing_school_sections=1') &&
        href.includes('scheduled_missing_major_sections=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-14') &&
        href.includes('scheduled_missing_school_sections=1') &&
        href.includes('scheduled_missing_major_sections=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-19') &&
        href.includes('scheduled_missing_school_sections=1') &&
        href.includes('scheduled_missing_major_sections=1'),
    ),
  ).toBe(true);
});
