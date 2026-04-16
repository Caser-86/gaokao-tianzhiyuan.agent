import { render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import DashboardShell from '../components/admin/dashboard-shell';

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

const schoolRotation = {
  enabled: true,
  frequencyDays: 1,
  windowSize: 2,
  orderedSlugs: ['southeast-university', 'west-china-medical-center'],
};

const majorRotation = {
  enabled: false,
  frequencyDays: 3,
  windowSize: 1,
  orderedSlugs: ['clinical-medicine'],
};

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-04-14T12:00:00Z'));
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
  listRankingReferencesMock.mockReset();
  listContentSummariesMock.mockReset();
  listContentSectionsMock.mockReset();
  listRelatedContentMock.mockReset();
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
    schools: [],
    majors: [],
  });
});

afterEach(() => {
  vi.useRealTimers();
});

test('filters the featured school configuration down to missing-image schools only', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: '东南大学',
          isFeatured: true,
          heroImageUrl: 'https://cdn.example.com/southeast.jpg',
        },
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      showMissingImageSchoolsOnly
      showMissingImageSchoolsOnlyHref="/admin?missing_school_images=1"
      showAllFeaturedSchoolsHref="/admin"
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByRole('link', { name: '查看全部学校' })).toHaveAttribute('href', '/admin');
  expect(screen.queryByRole('link', { name: '仅看待补图片学校（1）' })).not.toBeInTheDocument();
  expect(document.getElementById('featured-school-west-china-medical-center')).not.toBeNull();
  expect(document.getElementById('featured-school-southeast-university')).toBeNull();
});

test('preserves the selected preview date when linking into the missing-image school filter', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '内容学校',
        isFeatured: true,
        heroImageUrl: 'https://cdn.example.com/southeast.jpg',
      },
      {
        slug: 'west-china-medical-center',
        name: '内容候补学校',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [],
    rotation: {
      schools: schoolRotation,
      majors: majorRotation,
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-15',
      }),
    }),
  );

  expect(listFeaturedContentMock).toHaveBeenCalledWith('2026-04-15');
  const filterLink = screen.getByRole('link', { name: '仅看待补图片学校（1）' });
  const filterUrl = new URL(filterLink.getAttribute('href') ?? '', 'https://example.com');

  expect(filterUrl.pathname).toBe('/admin');
  expect(filterUrl.searchParams.get('preview_date')).toBe('2026-04-15');
  expect(filterUrl.searchParams.get('missing_school_images')).toBe('1');
  expect(screen.queryByRole('link', { name: '查看全部学校' })).not.toBeInTheDocument();
});

test('keeps the missing-image filter active across date preview navigation', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'west-china-medical-center',
        name: '内容候补学校',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [],
    rotation: {
      schools: schoolRotation,
      majors: majorRotation,
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [
        {
          date: '2026-04-14',
          weekday: '周二',
          schools: [],
          majors: [],
        },
        {
          date: '2026-04-15',
          weekday: '周三',
          schools: [],
          majors: [],
        },
      ],
      selectedDate: null,
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-15',
        missing_school_images: '1',
      }),
    }),
  );

  const previousDayUrl = new URL(
    screen.getByRole('link', { name: '查看前一天' }).getAttribute('href') ?? '',
    'https://example.com',
  );
  const todayUrl = new URL(
    screen.getByRole('link', { name: '回到今天' }).getAttribute('href') ?? '',
    'https://example.com',
  );
  const scheduleDayUrl = new URL(
    screen.getByRole('link', { name: '2026-04-14' }).getAttribute('href') ?? '',
    'https://example.com',
  );

  expect(screen.getByDisplayValue('2026-04-15')).toBeInTheDocument();
  expect(
    document.querySelector('input[type="hidden"][name="missing_school_images"][value="1"]'),
  ).not.toBeNull();
  expect(previousDayUrl.searchParams.get('missing_school_images')).toBe('1');
  expect(todayUrl.searchParams.get('missing_school_images')).toBe('1');
  expect(scheduleDayUrl.searchParams.get('missing_school_images')).toBe('1');
});

test('links previewed schools back to their configuration rows', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
        },
      ]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(
    within(screen.getByRole('region', { name: '今日展示学校' })).getByRole('link', {
      name: '华西医学中心',
    }),
  ).toHaveAttribute('href', '#featured-school-west-china-medical-center');
});

test('links missing-image schedule badges back to today and next preview sections', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
        },
      ]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
        },
      ]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const missingImageRegion = screen.getByRole('region', { name: '待补图片学校（1）' });

  expect(within(missingImageRegion).getByText('今日缺图 1 所，下一轮缺图 1 所')).toBeInTheDocument();
  expect(within(missingImageRegion).getByRole('link', { name: '今日展示' })).toHaveAttribute(
    'href',
    '#featured-school-preview-heading',
  );
  expect(within(missingImageRegion).getByRole('link', { name: '下一轮展示' })).toHaveAttribute(
    'href',
    '#next-featured-school-preview-heading',
  );
});
