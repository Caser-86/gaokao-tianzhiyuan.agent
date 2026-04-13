import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { trackPlatformEvent } from '../lib/platform-events';

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

test('trackPlatformEvent uses an explicit API base URL when provided', async () => {
  fetchMock.mockResolvedValueOnce({ ok: true });

  await trackPlatformEvent(
    {
      eventName: 'quick_prompt_clicked',
      step: 'homepage_masthead',
      metadata: { prompt: '查学校' },
    },
    'https://api.gaokao.test',
  );

  expect(fetchMock).toHaveBeenCalledWith('https://api.gaokao.test/api/platform/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_name: 'quick_prompt_clicked',
      step: 'homepage_masthead',
      metadata: { prompt: '查学校' },
    }),
  });
});
