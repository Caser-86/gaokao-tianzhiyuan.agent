import { render, screen, within } from '@testing-library/react';
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
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
  updateSchoolRankingReferencesAction: async () => undefined,
  updateMajorRankingReferencesAction: async () => undefined,
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

test('surfaces missing ranking-reference coverage and prioritizes missing featured entities', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: '东南大学',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[
        {
          slug: 'clinical-medicine',
          name: '临床医学',
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
          name: '东南大学',
        },
      ]}
      featuredMajorPreview={[
        {
          slug: 'clinical-medicine',
          name: '临床医学',
        },
      ]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      rankingReferenceSchools={[
        {
          slug: 'zhejiang-university',
          name: '浙江大学',
          rankingReferences: [
            {
              source: '软科中国大学排名',
              year: 2025,
              label: '全国第 3 名',
              scope: '',
              note: '',
              url: '',
            },
          ],
        },
        {
          slug: 'southeast-university',
          name: '东南大学',
          rankingReferences: [],
        },
      ]}
      rankingReferenceMajors={[
        {
          slug: 'finance',
          name: '金融学',
          rankingReferences: [
            {
              source: '校友会中国专业排名',
              year: 2025,
              label: 'A',
              scope: '',
              note: '',
              url: '',
            },
          ],
        },
        {
          slug: 'clinical-medicine',
          name: '临床医学',
          rankingReferences: [],
        },
      ]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRankingReferencesAction={async () => undefined}
      updateMajorRankingReferencesAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByText('已配置学校榜单 1 所，待补学校榜单 1 所')).toBeInTheDocument();
  expect(screen.getByText('已配置专业榜单 1 个，待补专业榜单 1 个')).toBeInTheDocument();

  const missingSchoolRegion = screen.getByRole('region', { name: '待补学校榜单（1）' });
  const missingMajorRegion = screen.getByRole('region', { name: '待补专业榜单（1）' });
  const schoolRankingRegion = screen.getByRole('region', { name: '学校榜单引用' });
  const majorRankingRegion = screen.getByRole('region', { name: '专业榜单引用' });

  expect(within(missingSchoolRegion).getByRole('link', { name: '东南大学' })).toHaveAttribute(
    'href',
    '#school-ranking-reference-southeast-university',
  );
  expect(within(missingSchoolRegion).getByText('今日待补 1 所，下一轮待补 0 所')).toBeInTheDocument();
  expect(within(missingSchoolRegion).getByText('当前展示')).toBeInTheDocument();
  expect(within(missingSchoolRegion).getByRole('link', { name: '今日展示' })).toHaveAttribute(
    'href',
    '#featured-school-preview-heading',
  );
  expect(within(missingMajorRegion).getByRole('link', { name: '临床医学' })).toHaveAttribute(
    'href',
    '#major-ranking-reference-clinical-medicine',
  );
  expect(within(missingMajorRegion).getByText('今日待补 1 个，下一轮待补 0 个')).toBeInTheDocument();
  expect(within(missingMajorRegion).getByText('当前展示')).toBeInTheDocument();
  expect(within(missingMajorRegion).getByRole('link', { name: '今日展示' })).toHaveAttribute(
    'href',
    '#featured-major-preview-heading',
  );

  expect(
    within(schoolRankingRegion)
      .getAllByRole('heading', { level: 3 })
      .map((heading) => heading.textContent),
  ).toEqual(['东南大学', '浙江大学']);
  expect(
    within(majorRankingRegion)
      .getAllByRole('heading', { level: 3 })
      .map((heading) => heading.textContent),
  ).toEqual(['临床医学', '金融学']);
});

test('filters school ranking references down to missing entries only and preserves preview date in filter links', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
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
        slug: 'zhejiang-university',
        name: '浙江大学',
        rankingReferences: [
          {
            source: '软科中国大学排名',
            year: 2025,
            label: '全国第 3 名',
            scope: '',
            note: '',
            url: '',
          },
        ],
      },
      {
        slug: 'southeast-university',
        name: '东南大学',
        rankingReferences: [],
      },
    ],
    majors: [],
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-18',
        missing_school_rankings: '1',
      } as never),
    }),
  );

  const schoolRankingRegion = screen.getByRole('region', { name: '学校榜单引用' });
  const viewAllLink = within(schoolRankingRegion).getByRole('link', { name: '查看全部学校榜单' });

  expect(
    within(schoolRankingRegion)
      .getAllByRole('heading', { level: 3 })
      .map((heading) => heading.textContent),
  ).toEqual(['东南大学']);
  expect(viewAllLink).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-18&missing_school_rankings=0',
  );
});

test('filters ranking references down to scheduled gaps only and preserves date shortcuts', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        isFeatured: true,
        heroImageUrl: '',
      },
      {
        slug: 'wuhan-university',
        name: '武汉大学',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        isFeatured: true,
      },
      {
        slug: 'software-engineering',
        name: '软件工程',
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
        schools: [{ slug: 'southeast-university', name: '东南大学' }],
        majors: [{ slug: 'clinical-medicine', name: '临床医学' }],
      },
      next: {
        schools: [{ slug: 'wuhan-university', name: '武汉大学' }],
        majors: [{ slug: 'software-engineering', name: '软件工程' }],
      },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });
  listRankingReferencesMock.mockResolvedValue({
    schools: [
      {
        slug: 'zhejiang-university',
        name: '浙江大学',
        rankingReferences: [],
      },
      {
        slug: 'wuhan-university',
        name: '武汉大学',
        rankingReferences: [],
      },
      {
        slug: 'southeast-university',
        name: '东南大学',
        rankingReferences: [],
      },
    ],
    majors: [
      {
        slug: 'finance',
        name: '金融学',
        rankingReferences: [],
      },
      {
        slug: 'software-engineering',
        name: '软件工程',
        rankingReferences: [],
      },
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        rankingReferences: [],
      },
    ],
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-18',
        scheduled_missing_school_rankings: '1',
        scheduled_missing_major_rankings: '1',
      } as never),
    }),
  );

  const schoolRankingRegion = screen.getByRole('region', { name: '学校榜单引用' });
  const majorRankingRegion = screen.getByRole('region', { name: '专业榜单引用' });

  expect(
    within(schoolRankingRegion)
      .getAllByRole('heading', { level: 3 })
      .map((heading) => heading.textContent),
  ).toEqual(['东南大学', '武汉大学']);
  expect(
    within(majorRankingRegion)
      .getAllByRole('heading', { level: 3 })
      .map((heading) => heading.textContent),
  ).toEqual(['临床医学', '软件工程']);

  expect(
    within(schoolRankingRegion).getByRole('link', { name: '查看全部近期待补学校榜单' }),
  ).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-18&scheduled_missing_school_rankings=0&scheduled_missing_major_rankings=1',
  );
  expect(
    within(majorRankingRegion).getByRole('link', { name: '查看全部近期待补专业榜单' }),
  ).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-18&scheduled_missing_school_rankings=1&scheduled_missing_major_rankings=0',
  );
  expect(screen.getByRole('link', { name: '查看前一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-17&scheduled_missing_school_rankings=1&scheduled_missing_major_rankings=1',
  );
  expect(screen.getByRole('link', { name: '回到今天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-14&scheduled_missing_school_rankings=1&scheduled_missing_major_rankings=1',
  );
  expect(screen.getByRole('link', { name: '查看后一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-19&scheduled_missing_school_rankings=1&scheduled_missing_major_rankings=1',
  );
});

test('preserves ranking-reference filters across date preview shortcuts', async () => {
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
          weekday: '周五',
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

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-18',
        missing_school_rankings: '1',
        missing_major_rankings: '1',
      }),
    }),
  );

  expect(screen.getByRole('link', { name: '查看前一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-17&missing_school_rankings=1&missing_major_rankings=1',
  );
  expect(screen.getByRole('link', { name: '回到今天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-14&missing_school_rankings=1&missing_major_rankings=1',
  );
  expect(screen.getByRole('link', { name: '查看后一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-19&missing_school_rankings=1&missing_major_rankings=1',
  );
});
