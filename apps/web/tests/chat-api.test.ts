import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { sendChatMessage } from '../lib/chat-api';

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

test('sendChatMessage posts the normalized web chat payload', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      request_id: 'chat_test',
      output: {
        type: 'structured_json',
        content: {
          summary: 'ok',
          analysis: 'fine',
          follow_up_questions: [],
          rendered_reply: 'reply',
        },
      },
    }),
  });

  await sendChatMessage(
    {
      userId: 'wx-openid-123',
      message: '帮我分析江苏985',
    },
    'https://api.gaokao.test',
  );

  expect(fetchMock).toHaveBeenCalledWith('https://api.gaokao.test/api/chat/skills/zhangxuefeng/invoke', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      channel: 'web',
      user_id: 'wx-openid-123',
      message: '帮我分析江苏985',
      metadata: {
        source: 'web_chat_page',
      },
    }),
  });
});
