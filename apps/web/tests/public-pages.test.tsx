import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const {
  MockPublicApiError,
  getSearchEntryMock,
  listSchoolsMock,
  listMajorsMock,
  listPlatformProductsMock,
  getSchoolBySlugMock,
  getMajorBySlugMock,
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
const PUBLIC_ERROR_TEXT =
  '\u516c\u5f00\u5185\u5bb9\u52a0\u8f7d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002';

beforeEach(() => {
  getSearchEntryMock.mockReset();
  listSchoolsMock.mockReset();
  listMajorsMock.mockReset();
  listPlatformProductsMock.mockReset();
  getSchoolBySlugMock.mockReset();
  getMajorBySlugMock.mockReset();
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
  expect(screen.getByRole('heading', { name: PLATFORM_SECTION_TITLE })).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: '\u9009\u62e9\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605' }),
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
  });

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(screen.getByRole('heading', { name: '\u4e1c\u5357\u5927\u5b66' })).toBeInTheDocument();
  expect(screen.getByText('\u5b66\u6821\u4eae\u70b9')).toBeInTheDocument();
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
