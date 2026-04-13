import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { evaluatePlatformEntitlements } from '../lib/platform-entitlements';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  delete process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL;
});

test('evaluatePlatformEntitlements posts selected products to the entitlement API', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      product_slugs: ['insight-weekly', 'deep-dive-pack'],
      entitlements: ['major_basic_access', 'school_basic_access'],
    }),
  });

  const payload = await evaluatePlatformEntitlements(
    ['insight-weekly', 'deep-dive-pack'],
    'https://api.gaokao.test',
  );

  expect(fetchMock).toHaveBeenCalledWith(
    'https://api.gaokao.test/api/platform/entitlements/evaluate',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_slugs: ['insight-weekly', 'deep-dive-pack'],
      }),
    },
  );
  expect(payload.entitlements).toEqual(['major_basic_access', 'school_basic_access']);
});
