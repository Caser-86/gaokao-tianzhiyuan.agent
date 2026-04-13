import { afterEach, beforeEach, expect, test, vi } from 'vitest';

vi.mock('server-only', () => ({}));

import { listPlatformProducts } from '../lib/platform-api';

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

test('listPlatformProducts reads platform products from the API', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      items: [
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
      ],
    }),
  });

  const payload = await listPlatformProducts();

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/platform/products',
    expect.objectContaining({ cache: 'no-store' }),
  );
  expect(payload.items[0]?.name).toBe('志愿快报订阅');
});
