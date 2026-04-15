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
});

afterEach(() => {
  vi.useRealTimers();
});

test('renders school and major related content editors in admin', async () => {
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
    schools: [],
    majors: [],
  });
  listRelatedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '涓滃崡澶у',
        relatedMajors: ['clinical-medicine', 'architecture'],
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '涓村簥鍖诲',
        relatedSchools: ['southeast-university'],
      },
    ],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校相关推荐' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业相关推荐' })).toBeInTheDocument();
  const relatedSlugInputs = screen.getAllByRole('textbox', { name: '关联 slug' });
  expect(relatedSlugInputs[0]).toHaveValue('clinical-medicine\narchitecture');
  expect(relatedSlugInputs[1]).toHaveValue('southeast-university');
  expect(screen.getAllByRole('button', { name: '保存相关推荐' })).toHaveLength(2);
});

test('surfaces missing related-content coverage and prioritizes scheduled gaps', () => {
  const { container } = render(
    <DashboardShell
      title="鍐呭杩愯惀鍚庡彴"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: '涓滃崡澶у',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[
        {
          slug: 'clinical-medicine',
          name: '涓村簥鍖诲',
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
          name: '涓滃崡澶у',
        },
      ]}
      featuredMajorPreview={[
        {
          slug: 'clinical-medicine',
          name: '涓村簥鍖诲',
        },
      ]}
      nextFeaturedSchoolPreview={[
        {
          slug: 'wuhan-university',
          name: '姝︽眽澶у',
        },
      ]}
      nextFeaturedMajorPreview={[
        {
          slug: 'software-engineering',
          name: '杞欢宸ョ▼',
        },
      ]}
      featuredSchedule={[]}
      relatedSchools={[
        {
          slug: 'zhejiang-university',
          name: '娴欐睙澶у',
          relatedMajors: ['finance'],
        },
        {
          slug: 'wuhan-university',
          name: '姝︽眽澶у',
          relatedMajors: [],
        },
        {
          slug: 'southeast-university',
          name: '涓滃崡澶у',
          relatedMajors: [],
        },
      ]}
      relatedMajors={[
        {
          slug: 'finance',
          name: '閲戣瀺瀛?',
          relatedSchools: ['zhejiang-university'],
        },
        {
          slug: 'software-engineering',
          name: '杞欢宸ョ▼',
          relatedSchools: [],
        },
        {
          slug: 'clinical-medicine',
          name: '涓村簥鍖诲',
          relatedSchools: [],
        },
      ]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRelatedContentAction={async () => undefined}
      updateMajorRelatedContentAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const schoolSection = container.querySelector('[data-testid="school-related-content-section"]');
  const majorSection = container.querySelector('[data-testid="major-related-content-section"]');
  const missingSchoolSection = container.querySelector('[data-testid="missing-school-related-content-section"]');
  const missingMajorSection = container.querySelector('[data-testid="missing-major-related-content-section"]');

  expect(schoolSection).not.toBeNull();
  expect(majorSection).not.toBeNull();
  expect(missingSchoolSection).not.toBeNull();
  expect(missingMajorSection).not.toBeNull();

  const schoolHeadings = Array.from(
    schoolSection?.querySelectorAll('h3') ?? [],
    (heading) => heading.textContent,
  );
  const majorHeadings = Array.from(
    majorSection?.querySelectorAll('h3') ?? [],
    (heading) => heading.textContent,
  );

  expect(schoolHeadings).toEqual(['涓滃崡澶у', '姝︽眽澶у', '娴欐睙澶у']);
  expect(majorHeadings).toEqual(['涓村簥鍖诲', '杞欢宸ョ▼', '閲戣瀺瀛?']);

  const missingSchoolLinks = Array.from(
    missingSchoolSection?.querySelectorAll('a[href^="#school-related-content-"]') ?? [],
    (link) => link.getAttribute('href'),
  );
  const missingMajorLinks = Array.from(
    missingMajorSection?.querySelectorAll('a[href^="#major-related-content-"]') ?? [],
    (link) => link.getAttribute('href'),
  );
  const previewLinks = Array.from(
    missingSchoolSection?.querySelectorAll('a[href="#featured-school-preview-heading"], a[href="#next-featured-school-preview-heading"]') ?? [],
    (link) => link.getAttribute('href'),
  );
  const majorPreviewLinks = Array.from(
    missingMajorSection?.querySelectorAll('a[href="#featured-major-preview-heading"], a[href="#next-featured-major-preview-heading"]') ?? [],
    (link) => link.getAttribute('href'),
  );

  expect(missingSchoolLinks).toEqual([
    '#school-related-content-southeast-university',
    '#school-related-content-wuhan-university',
  ]);
  expect(missingMajorLinks).toEqual([
    '#major-related-content-clinical-medicine',
    '#major-related-content-software-engineering',
  ]);
  expect(previewLinks).toEqual([
    '#featured-school-preview-heading',
    '#next-featured-school-preview-heading',
  ]);
  expect(majorPreviewLinks).toEqual([
    '#featured-major-preview-heading',
    '#next-featured-major-preview-heading',
  ]);
});

test('filters related-content editors down to missing entries only and preserves date shortcuts', async () => {
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
      schedule: [
        {
          date: '2026-04-17',
          weekday: '鍛ㄤ簲',
          schools: [],
          majors: [],
        },
      ],
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
    schools: [],
    majors: [],
  });
  listRelatedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'zhejiang-university',
        name: '娴欐睙澶у',
        relatedMajors: ['finance'],
      },
      {
        slug: 'southeast-university',
        name: '涓滃崡澶у',
        relatedMajors: [],
      },
    ],
    majors: [
      {
        slug: 'finance',
        name: '閲戣瀺瀛?',
        relatedSchools: ['zhejiang-university'],
      },
      {
        slug: 'clinical-medicine',
        name: '涓村簥鍖诲',
        relatedSchools: [],
      },
    ],
  });

  const { container } = render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-18',
        missing_school_related: '1',
        missing_major_related: '1',
      } as never),
    }),
  );

  const schoolSection = container.querySelector('[data-testid="school-related-content-section"]');
  const majorSection = container.querySelector('[data-testid="major-related-content-section"]');
  const allHrefs = Array.from(container.querySelectorAll('a'), (link) => link.getAttribute('href') ?? '');

  expect(
    Array.from(schoolSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['涓滃崡澶у']);
  expect(
    Array.from(majorSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['涓村簥鍖诲']);

  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-18') &&
        href.includes('missing_school_related=0') &&
        href.includes('missing_major_related=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-18') &&
        href.includes('missing_school_related=1') &&
        href.includes('missing_major_related=0'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-17') &&
        href.includes('missing_school_related=1') &&
        href.includes('missing_major_related=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-14') &&
        href.includes('missing_school_related=1') &&
        href.includes('missing_major_related=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-19') &&
        href.includes('missing_school_related=1') &&
        href.includes('missing_major_related=1'),
    ),
  ).toBe(true);
});

test('filters related-content editors down to scheduled gaps only and preserves date shortcuts', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '涓滃崡澶у',
        isFeatured: true,
        heroImageUrl: '',
      },
      {
        slug: 'wuhan-university',
        name: '姝︽眽澶у',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '涓村簥鍖诲',
        isFeatured: true,
      },
      {
        slug: 'software-engineering',
        name: '杞欢宸ョ▼',
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
        schools: [{ slug: 'southeast-university', name: '涓滃崡澶у' }],
        majors: [{ slug: 'clinical-medicine', name: '涓村簥鍖诲' }],
      },
      next: {
        schools: [{ slug: 'wuhan-university', name: '姝︽眽澶у' }],
        majors: [{ slug: 'software-engineering', name: '杞欢宸ョ▼' }],
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
    schools: [],
    majors: [],
  });
  listRelatedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'zhejiang-university',
        name: '娴欐睙澶у',
        relatedMajors: [],
      },
      {
        slug: 'wuhan-university',
        name: '姝︽眽澶у',
        relatedMajors: [],
      },
      {
        slug: 'southeast-university',
        name: '涓滃崡澶у',
        relatedMajors: [],
      },
    ],
    majors: [
      {
        slug: 'finance',
        name: '閲戣瀺瀛?',
        relatedSchools: [],
      },
      {
        slug: 'software-engineering',
        name: '杞欢宸ョ▼',
        relatedSchools: [],
      },
      {
        slug: 'clinical-medicine',
        name: '涓村簥鍖诲',
        relatedSchools: [],
      },
    ],
  });

  const { container } = render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-18',
        scheduled_missing_school_related: '1',
        scheduled_missing_major_related: '1',
      } as never),
    }),
  );

  const schoolSection = container.querySelector('[data-testid="school-related-content-section"]');
  const majorSection = container.querySelector('[data-testid="major-related-content-section"]');
  const allHrefs = Array.from(container.querySelectorAll('a'), (link) => link.getAttribute('href') ?? '');

  expect(
    Array.from(schoolSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['涓滃崡澶у', '姝︽眽澶у']);
  expect(
    Array.from(majorSection?.querySelectorAll('h3') ?? [], (heading) => heading.textContent),
  ).toEqual(['涓村簥鍖诲', '杞欢宸ョ▼']);

  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-18') &&
        href.includes('scheduled_missing_school_related=0') &&
        href.includes('scheduled_missing_major_related=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-18') &&
        href.includes('scheduled_missing_school_related=1') &&
        href.includes('scheduled_missing_major_related=0'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-17') &&
        href.includes('scheduled_missing_school_related=1') &&
        href.includes('scheduled_missing_major_related=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-14') &&
        href.includes('scheduled_missing_school_related=1') &&
        href.includes('scheduled_missing_major_related=1'),
    ),
  ).toBe(true);
  expect(
    allHrefs.some(
      (href) =>
        href.includes('preview_date=2026-04-19') &&
        href.includes('scheduled_missing_school_related=1') &&
        href.includes('scheduled_missing_major_related=1'),
    ),
  ).toBe(true);
});
