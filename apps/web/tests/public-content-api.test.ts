import { afterEach, beforeEach, expect, test, vi } from 'vitest';

vi.mock('server-only', () => ({}));

import {
  PublicApiError,
  getMajorBySlug,
  getSearchEntry,
  getSchoolBySlug,
  listMajors,
  listSchools,
} from '../lib/public-content-api';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  process.env.GAOKAO_AGENT_API_URL = 'http://api.example.com';
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete process.env.GAOKAO_AGENT_API_URL;
});

test('getSearchEntry fetches public search metadata without caching', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      title: '高考志愿助手',
      description: '帮助考生和家长快速看学校、专业、地域与就业。',
      quick_prompts: ['查学校', '查专业'],
    }),
  });

  const entry = await getSearchEntry();

  expect(fetchMock).toHaveBeenCalledWith('http://api.example.com/api/public/search-entry', {
    cache: 'no-store',
  });
  expect(entry.quickPrompts).toEqual(['查学校', '查专业']);
});

test('listSchools returns public school cards', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
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
    }),
  });

  const payload = await listSchools();

  expect(payload.total).toBe(1);
  expect(payload.items[0]?.slug).toBe('southeast-university');
});

test('listMajors returns public major cards', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      items: [
        {
          slug: 'clinical-medicine',
          name: '临床医学',
          discipline: '医学',
          recommended_regions: ['江苏', '浙江'],
          summary: '培养周期长。',
        },
      ],
      total: 1,
    }),
  });

  const payload = await listMajors();

  expect(payload.total).toBe(1);
  expect(payload.items[0]?.recommendedRegions).toEqual(['江苏', '浙江']);
});

test('getSchoolBySlug throws a 404 PublicApiError for missing schools', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: false,
    status: 404,
    text: async () => 'school not found',
  });

  await expect(getSchoolBySlug('missing-school')).rejects.toEqual(
    expect.objectContaining<Partial<PublicApiError>>({
      status: 404,
      message: 'school not found',
    }),
  );
});

test('getMajorBySlug propagates non-404 failures with status', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: false,
    status: 500,
    text: async () => 'server error',
  });

  await expect(getMajorBySlug('clinical-medicine')).rejects.toEqual(
    expect.objectContaining<Partial<PublicApiError>>({
      status: 500,
      message: 'server error',
    }),
  );
});
