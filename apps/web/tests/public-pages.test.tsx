import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const {
  MockPublicApiError,
  getSearchEntryMock,
  listSchoolsMock,
  listMajorsMock,
  listPlatformProductsMock,
  getSchoolBySlugMock,
  getMajorBySlugMock,
  evaluatePlatformEntitlementsMock,
  notFoundMock,
  refreshMock,
} = vi.hoisted(() => ({
  MockPublicApiError: class MockPublicApiError extends Error {
    status: number;

    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
  getSearchEntryMock: vi.fn(),
  listSchoolsMock: vi.fn(),
  listMajorsMock: vi.fn(),
  listPlatformProductsMock: vi.fn(),
  getSchoolBySlugMock: vi.fn(),
  getMajorBySlugMock: vi.fn(),
  evaluatePlatformEntitlementsMock: vi.fn(),
  notFoundMock: vi.fn(() => {
    throw new Error('NEXT_NOT_FOUND');
  }),
  refreshMock: vi.fn(),
}));

vi.mock('../lib/public-content-api', () => ({
  PublicApiError: MockPublicApiError,
  getSearchEntry: getSearchEntryMock,
  listSchools: listSchoolsMock,
  listMajors: listMajorsMock,
  getSchoolBySlug: getSchoolBySlugMock,
  getMajorBySlug: getMajorBySlugMock,
}));

vi.mock('../lib/platform-api', () => ({
  listPlatformProducts: listPlatformProductsMock,
}));

vi.mock('../lib/platform-entitlements', () => ({
  evaluatePlatformEntitlements: evaluatePlatformEntitlementsMock,
}));

vi.mock('next/navigation', () => ({
  notFound: notFoundMock,
  useRouter: () => ({
    refresh: refreshMock,
  }),
}));

import HomePage from '../app/page';
import MajorPage from '../app/majors/[slug]/page';
import SchoolPage from '../app/schools/[slug]/page';

const HOME_TITLE = '\u9ad8\u8003\u5fd7\u613f\u52a9\u624b';
const HOME_DESCRIPTION =
  '\u5e2e\u52a9\u8003\u751f\u548c\u5bb6\u957f\u5feb\u901f\u770b\u5b66\u6821\u3001\u4e13\u4e1a\u3001\u5730\u533a\u4e0e\u5c31\u4e1a\u3002';
const SCHOOL_SECTION_TITLE = '\u5b66\u6821\u901f\u67e5';
const MAJOR_SECTION_TITLE = '\u4e13\u4e1a\u901f\u67e5';
const PLATFORM_SECTION_TITLE = '\u7cbe\u9009\u670d\u52a1';
const PROMPT_TEXT = '\u9009\u62e9\u4ea7\u54c1\u540e\u67e5\u770b\u80fd\u529b\u5305\u3002';
const PLATFORM_UNAVAILABLE_TITLE = '\u5e73\u53f0\u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528';
const RANKING_SECTION_TITLE = '\u53c2\u8003\u699c\u5355';
const RANKING_HINT_TEXT = '\u4e0d\u540c\u699c\u5355\u53e3\u5f84\u4e0d\u540c\uff0c\u7ed3\u679c\u4ec5\u4f9b\u53c2\u8003\u3002';
const RANKING_BADGE_TEXT = '\u542b\u53c2\u8003\u699c\u5355';
const PUBLIC_ERROR_TEXT =
  '\u516c\u5f00\u5185\u5bb9\u52a0\u8f7d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002';

beforeEach(() => {
  getSearchEntryMock.mockReset();
  listSchoolsMock.mockReset();
  listMajorsMock.mockReset();
  listPlatformProductsMock.mockReset();
  getSchoolBySlugMock.mockReset();
  getMajorBySlugMock.mockReset();
  evaluatePlatformEntitlementsMock.mockReset();
  evaluatePlatformEntitlementsMock.mockResolvedValue({
    product_slugs: ['insight-weekly'],
    entitlements: ['school_basic_access'],
  });
  notFoundMock.mockClear();
  refreshMock.mockReset();
});

test('home page renders API-backed search, catalog, and product data', async () => {
  getSearchEntryMock.mockResolvedValue({
    title: HOME_TITLE,
    description: HOME_DESCRIPTION,
    quickPrompts: ['\u67e5\u5b66\u6821', '\u67e5\u4e13\u4e1a'],
  });
  listSchoolsMock.mockResolvedValue({
    items: [
      {
        slug: 'southeast-university',
        name: '\u4e1c\u5357\u5927\u5b66',
        region: '\u6c5f\u82cf',
        city: '\u5357\u4eac',
        tags: ['985'],
        summary: '\u5de5\u79d1\u89c1\u957f\u3002',
        heroImageUrl: 'https://cdn.example.com/southeast.jpg',
        hasRankingReferences: true,
      },
      {
        slug: 'plain-school',
        name: '\u666e\u901a\u5b66\u6821',
        region: '\u5c71\u4e1c',
        city: '\u6d4e\u5357',
        tags: ['\u53cc\u975e'],
        summary: '\u65e0\u989d\u5916\u699c\u5355\u793a\u4f8b\u3002',
        hasRankingReferences: false,
      },
    ],
    total: 2,
  });
  listMajorsMock.mockResolvedValue({
    items: [
      {
        slug: 'clinical-medicine',
        name: '\u4e34\u5e8a\u533b\u5b66',
        discipline: '\u533b\u5b66',
        recommendedRegions: ['\u6c5f\u82cf', '\u6d59\u6c5f'],
        summary: '\u57f9\u517b\u5468\u671f\u957f\u3002',
        hasRankingReferences: true,
      },
      {
        slug: 'plain-major',
        name: '\u666e\u901a\u4e13\u4e1a',
        discipline: '\u5de5\u5b66',
        recommendedRegions: ['\u6cb3\u5317'],
        summary: '\u65e0\u989d\u5916\u699c\u5355\u793a\u4f8b\u3002',
        hasRankingReferences: false,
      },
    ],
    total: 2,
  });
  listPlatformProductsMock.mockResolvedValue({
    items: [
      {
        slug: 'insight-weekly',
        name: '\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605',
        description:
          '\u6301\u7eed\u8ddf\u8e2a\u5b66\u6821\u3001\u4e13\u4e1a\u548c\u98ce\u9669\u53d8\u5316\u3002',
        entitlements: ['school_basic_access', 'risk_alert_access'],
      },
    ],
  });

  render(await HomePage());

  expect(screen.getByRole('heading', { name: HOME_TITLE })).toBeInTheDocument();
  expect(screen.getByText('\u4e1c\u5357\u5927\u5b66')).toBeInTheDocument();
  expect(screen.getByText('\u4e34\u5e8a\u533b\u5b66')).toBeInTheDocument();
  expect(screen.getByRole('img', { name: '\u4e1c\u5357\u5927\u5b66' })).toHaveAttribute(
    'src',
    'https://cdn.example.com/southeast.jpg',
  );
  expect(screen.getByText('\u6682\u672a\u914d\u7f6e\u5b66\u6821\u56fe\u7247')).toBeInTheDocument();
  expect(screen.queryByRole('img', { name: '\u666e\u901a\u5b66\u6821' })).not.toBeInTheDocument();
  expect(screen.getAllByText(RANKING_BADGE_TEXT)).toHaveLength(2);
  expect(screen.getByRole('heading', { name: PLATFORM_SECTION_TITLE })).toBeInTheDocument();
  expect(
    screen.getByRole('button', {
      name: '\u52a0\u5165\u80fd\u529b\u9884\u89c8\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605',
    }),
  ).toBeInTheDocument();
  expect(screen.getByText(PROMPT_TEXT)).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: SCHOOL_SECTION_TITLE }).closest('article')).toHaveAttribute(
    'id',
    'school-catalog',
  );
});

test('home page renders an explicit error state on public API failure', async () => {
  getSearchEntryMock.mockImplementation(() => {
    throw new Error('boom');
  });

  render(await HomePage());

  expect(screen.getByText(PUBLIC_ERROR_TEXT)).toBeInTheDocument();
});

test('home page accepts openid query params for platform entitlement lookup', async () => {
  getSearchEntryMock.mockResolvedValue({
    title: HOME_TITLE,
    description: HOME_DESCRIPTION,
    quickPrompts: ['\u67e5\u5b66\u6821', '\u67e5\u4e13\u4e1a'],
  });
  listSchoolsMock.mockResolvedValue({
    items: [
      {
        slug: 'southeast-university',
        name: '\u4e1c\u5357\u5927\u5b66',
        region: '\u6c5f\u82cf',
        city: '\u5357\u4eac',
        tags: ['985'],
        summary: '\u5de5\u79d1\u89c1\u957f\u3002',
      },
    ],
    total: 1,
  });
  listMajorsMock.mockResolvedValue({
    items: [
      {
        slug: 'clinical-medicine',
        name: '\u4e34\u5e8a\u533b\u5b66',
        discipline: '\u533b\u5b66',
        recommendedRegions: ['\u6c5f\u82cf'],
        summary: '\u57f9\u517b\u5468\u671f\u957f\u3002',
      },
    ],
    total: 1,
  });
  listPlatformProductsMock.mockResolvedValue({
    items: [
      {
        slug: 'insight-weekly',
        name: '\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605',
        description:
          '\u6301\u7eed\u8ddf\u8e2a\u5b66\u6821\u3001\u4e13\u4e1a\u548c\u98ce\u9669\u53d8\u5316\u3002',
        entitlements: ['school_basic_access'],
      },
    ],
  });

  render(
    await HomePage({
      searchParams: Promise.resolve({
        openid: 'wx-openid-homepage',
      }),
    }),
  );

  fireEvent.click(
    screen.getByRole('button', {
      name: '\u52a0\u5165\u80fd\u529b\u9884\u89c8\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605',
    }),
  );

  await waitFor(() => {
    expect(evaluatePlatformEntitlementsMock).toHaveBeenCalledWith(
      ['insight-weekly'],
      'http://127.0.0.1:8000',
      'wx-openid-homepage',
    );
  });
});

test('home page renders a platform unavailable panel when platform products fail', async () => {
  getSearchEntryMock.mockResolvedValue({
    title: HOME_TITLE,
    description: HOME_DESCRIPTION,
    quickPrompts: ['\u67e5\u5b66\u6821', '\u67e5\u4e13\u4e1a'],
  });
  listSchoolsMock.mockResolvedValue({
    items: [
      {
        slug: 'southeast-university',
        name: '\u4e1c\u5357\u5927\u5b66',
        region: '\u6c5f\u82cf',
        city: '\u5357\u4eac',
        tags: ['985'],
        summary: '\u5de5\u79d1\u89c1\u957f\u3002',
      },
    ],
    total: 1,
  });
  listMajorsMock.mockResolvedValue({
    items: [
      {
        slug: 'clinical-medicine',
        name: '\u4e34\u5e8a\u533b\u5b66',
        discipline: '\u533b\u5b66',
        recommendedRegions: ['\u6c5f\u82cf', '\u6d59\u6c5f'],
        summary: '\u57f9\u517b\u5468\u671f\u957f\u3002',
      },
    ],
    total: 1,
  });
  listPlatformProductsMock.mockRejectedValue(new Error('platform down'));

  render(await HomePage());

  expect(screen.getByRole('heading', { name: PLATFORM_UNAVAILABLE_TITLE })).toBeInTheDocument();
  expect(
    screen.getByRole('link', { name: '\u5148\u53bb\u67e5\u5b66\u6821' }),
  ).toHaveAttribute('href', '#school-catalog');
  expect(
    screen.getByRole('button', { name: '\u7a0d\u540e\u518d\u8bd5' }),
  ).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: SCHOOL_SECTION_TITLE })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: MAJOR_SECTION_TITLE })).toBeInTheDocument();
});

test('school page renders API-backed detail data', async () => {
  getSchoolBySlugMock.mockResolvedValue({
    slug: 'southeast-university',
    name: '\u4e1c\u5357\u5927\u5b66',
    region: '\u6c5f\u82cf',
    city: '\u5357\u4eac',
    tags: ['985'],
    summary: '\u5de5\u79d1\u89c1\u957f\u3002',
    sections: [
      {
        type: 'highlights',
        title: '\u5b66\u6821\u4eae\u70b9',
        items: ['\u5efa\u7b51\u5f3a'],
      },
    ],
    relatedMajors: ['architecture'],
    rankingReferences: [
      {
        source: '\u8f6f\u79d1\u4e2d\u56fd\u5927\u5b66\u6392\u540d',
        year: 2025,
        label: '\u5168\u56fd\u7b2c 15 \u540d',
        scope: '\u7efc\u5408\u7c7b\u9ad8\u6821',
        note: '\u7528\u4e8e\u7efc\u5408\u5b9e\u529b\u53c2\u8003\uff0c\u4e0d\u7b49\u540c\u4e8e\u5177\u4f53\u4e13\u4e1a\u4f18\u52bf\u3002',
        url: 'https://example.com/rankings/southeast-university',
      },
    ],
  });

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(screen.getByRole('heading', { name: '\u4e1c\u5357\u5927\u5b66' })).toBeInTheDocument();
  expect(screen.getByText('\u5b66\u6821\u4eae\u70b9')).toBeInTheDocument();
  expect(
    screen.getByRole('link', { name: '\u67e5\u770b\u53c2\u8003\u699c\u5355' }),
  ).toHaveAttribute('href', '#ranking-references');
  expect(screen.getByRole('heading', { name: RANKING_SECTION_TITLE })).toBeInTheDocument();
  expect(screen.getByText(RANKING_HINT_TEXT)).toBeInTheDocument();
  expect(screen.getByText('\u8f6f\u79d1\u4e2d\u56fd\u5927\u5b66\u6392\u540d 2025')).toBeInTheDocument();
  expect(
    screen.getByRole('link', { name: '\u67e5\u770b\u6765\u6e90\u539f\u6587' }),
  ).toHaveAttribute('href', 'https://example.com/rankings/southeast-university');
});

test('school page omits ranking references when none are available', async () => {
  getSchoolBySlugMock.mockResolvedValue({
    slug: 'southeast-university',
    name: '\u4e1c\u5357\u5927\u5b66',
    region: '\u6c5f\u82cf',
    city: '\u5357\u4eac',
    tags: ['985'],
    summary: '\u5de5\u79d1\u89c1\u957f\u3002',
    sections: [],
    relatedMajors: ['architecture'],
    rankingReferences: [],
  });

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(
    screen.queryByRole('link', { name: '\u67e5\u770b\u53c2\u8003\u699c\u5355' }),
  ).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: RANKING_SECTION_TITLE })).not.toBeInTheDocument();
  expect(screen.queryByText(RANKING_HINT_TEXT)).not.toBeInTheDocument();
});

test('school page calls notFound on 404 detail responses', async () => {
  getSchoolBySlugMock.mockRejectedValue(new MockPublicApiError(404, 'school not found'));

  await expect(
    SchoolPage({ params: Promise.resolve({ slug: 'missing-school' }) }),
  ).rejects.toThrow('NEXT_NOT_FOUND');

  expect(notFoundMock).toHaveBeenCalled();
});

test('major page calls notFound on 404 detail responses', async () => {
  getMajorBySlugMock.mockRejectedValue(new MockPublicApiError(404, 'major not found'));

  await expect(
    MajorPage({ params: Promise.resolve({ slug: 'missing-major' }) }),
  ).rejects.toThrow('NEXT_NOT_FOUND');

  expect(notFoundMock).toHaveBeenCalled();
});

test('major page renders an explicit error state on non-404 failures', async () => {
  getMajorBySlugMock.mockRejectedValue(new MockPublicApiError(500, 'server error'));

  render(await MajorPage({ params: Promise.resolve({ slug: 'clinical-medicine' }) }));

  expect(screen.getByText(PUBLIC_ERROR_TEXT)).toBeInTheDocument();
});

test('major page renders ranking references when present', async () => {
  getMajorBySlugMock.mockResolvedValue({
    slug: 'clinical-medicine',
    name: '\u4e34\u5e8a\u533b\u5b66',
    discipline: '\u533b\u5b66',
    recommendedRegions: ['\u6c5f\u82cf', '\u56db\u5ddd'],
    summary: '\u57f9\u517b\u5468\u671f\u957f\u3002',
    sections: [],
    relatedSchools: ['southeast-university'],
    rankingReferences: [
      {
        source: '\u6559\u80b2\u90e8\u5b66\u79d1\u8bc4\u4f30',
        year: 2023,
        label: '\u4e34\u5e8a\u533b\u5b66 A-',
        scope: '\u4e00\u7ea7\u5b66\u79d1',
        note: '\u9002\u5408\u4f5c\u4e3a\u533b\u5b66\u5b66\u79d1\u5b9e\u529b\u53c2\u8003\u3002',
        url: 'https://example.com/rankings/clinical-medicine',
      },
    ],
  });

  render(await MajorPage({ params: Promise.resolve({ slug: 'clinical-medicine' }) }));

  expect(
    screen.getByRole('link', { name: '\u67e5\u770b\u53c2\u8003\u699c\u5355' }),
  ).toHaveAttribute('href', '#ranking-references');
  expect(screen.getByRole('heading', { name: RANKING_SECTION_TITLE })).toBeInTheDocument();
  expect(screen.getByText(RANKING_HINT_TEXT)).toBeInTheDocument();
  expect(screen.getByText('\u6559\u80b2\u90e8\u5b66\u79d1\u8bc4\u4f30 2023')).toBeInTheDocument();
  expect(screen.getByText('\u4e34\u5e8a\u533b\u5b66 A-')).toBeInTheDocument();
  expect(
    screen.getByRole('link', { name: '\u67e5\u770b\u6765\u6e90\u539f\u6587' }),
  ).toHaveAttribute('href', 'https://example.com/rankings/clinical-medicine');
});
