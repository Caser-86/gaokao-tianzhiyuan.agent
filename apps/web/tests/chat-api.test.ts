import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import {
  deleteChatSession,
  getChatSessionMessages,
  sendChatMessage,
} from '../lib/chat-api';

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
    credentials: 'include',
    body: JSON.stringify({
      channel: 'web',
      message: '帮我分析江苏985',
      metadata: {
        source: 'web_chat_page',
      },
    }),
  });
});

test('loads and deletes user-scoped chat session history', async () => {
  fetchMock
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: 'session-1',
        channel: 'web',
        created_at: '2026-08-25T00:00:00Z',
        updated_at: '2026-08-25T00:00:00Z',
        expires_at: '2026-09-24T00:00:00Z',
        items: [],
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: 'session-1', deleted: true }),
    });

  await getChatSessionMessages('session-1', 'https://api.gaokao.test');
  expect(fetchMock).toHaveBeenNthCalledWith(
    1,
    'https://api.gaokao.test/api/chat/sessions/session-1/messages',
    { credentials: 'include' },
  );

  await deleteChatSession('session-1', 'https://api.gaokao.test');
  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    'https://api.gaokao.test/api/chat/sessions/session-1',
    { method: 'DELETE', credentials: 'include' },
  );
});
