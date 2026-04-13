import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const {
  MockPublicApiError,
  getSearchEntryMock,
  listSchoolsMock,
  listMajorsMock,
  getSchoolBySlugMock,
  getMajorBySlugMock,
  notFoundMock,
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
  getSchoolBySlugMock: vi.fn(),
  getMajorBySlugMock: vi.fn(),
  notFoundMock: vi.fn(() => {
    throw new Error('NEXT_NOT_FOUND');
  }),
}));

vi.mock('../lib/public-content-api', () => ({
  PublicApiError: MockPublicApiError,
  getSearchEntry: getSearchEntryMock,
  listSchools: listSchoolsMock,
  listMajors: listMajorsMock,
  getSchoolBySlug: getSchoolBySlugMock,
  getMajorBySlug: getMajorBySlugMock,
}));

vi.mock('next/navigation', () => ({
  notFound: notFoundMock,
}));

import HomePage from '../app/page';
import MajorPage from '../app/majors/[slug]/page';
import SchoolPage from '../app/schools/[slug]/page';

beforeEach(() => {
  getSearchEntryMock.mockReset();
  listSchoolsMock.mockReset();
  listMajorsMock.mockReset();
  getSchoolBySlugMock.mockReset();
  getMajorBySlugMock.mockReset();
  notFoundMock.mockClear();
});

test('home page renders API-backed search and catalog data', async () => {
  getSearchEntryMock.mockResolvedValue({
    title: '高考志愿助手',
    description: '帮助考生和家长快速看学校、专业、地域与就业。',
    quickPrompts: ['查学校', '查专业'],
  });
  listSchoolsMock.mockResolvedValue({
    items: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        region: '江苏',
        city: '南京',
        tags: ['985'],
        summary: '工科见长。',
      },
    ],
    total: 1,
  });
  listMajorsMock.mockResolvedValue({
    items: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        discipline: '医学',
        recommendedRegions: ['江苏', '浙江'],
        summary: '培养周期长。',
      },
    ],
    total: 1,
  });

  render(await HomePage());

  expect(screen.getByRole('heading', { name: '高考志愿助手' })).toBeInTheDocument();
  expect(screen.getByText('东南大学')).toBeInTheDocument();
  expect(screen.getByText('临床医学')).toBeInTheDocument();
});

test('home page renders an explicit error state on public API failure', async () => {
  getSearchEntryMock.mockRejectedValue(new Error('boom'));

  render(await HomePage());

  expect(screen.getByText('公开内容加载失败，请稍后重试。')).toBeInTheDocument();
});

test('school page renders API-backed detail data', async () => {
  getSchoolBySlugMock.mockResolvedValue({
    slug: 'southeast-university',
    name: '东南大学',
    region: '江苏',
    city: '南京',
    tags: ['985'],
    summary: '工科见长。',
    sections: [{ type: 'highlights', title: '学校亮点', items: ['建筑强'] }],
    relatedMajors: ['architecture'],
  });

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(screen.getByRole('heading', { name: '东南大学' })).toBeInTheDocument();
  expect(screen.getByText('学校亮点')).toBeInTheDocument();
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

  expect(screen.getByText('公开内容加载失败，请稍后重试。')).toBeInTheDocument();
});
