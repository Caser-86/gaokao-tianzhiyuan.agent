import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import {
  listMediaAnalysisEvents,
  retryMediaAnalysisEvent,
} from '../lib/admin-media-analysis-api';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  process.env.GAOKAO_AGENT_API_URL = 'http://api.example.com';
  process.env.GAOKAO_AGENT_ADMIN_TOKEN = 'secret-token';
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete process.env.GAOKAO_AGENT_API_URL;
  delete process.env.GAOKAO_AGENT_ADMIN_TOKEN;
});

test('listMediaAnalysisEvents sends authenticated filtered request and maps payload', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      items: [
        {
          id: 21,
          channel: 'wechat',
          source: 'wechat_official_account_image_media_analysis',
          user_id: 'wx-openid-123',
          message_id: 'msg-123',
          media_id: 'media-123',
          media_type: 'image',
          provider: 'openai_compatible',
          status: 'success',
          summary: '识别到河南560分理科',
          rendered_reply: '图片已自动进入高考志愿分析',
          extracted_fields: { province: '河南', score: 560 },
          context: {
            msg_type: 'image',
            pic_url: 'https://example.com/image-123.png',
            create_time: '1710000001',
          },
          retryable: true,
          retry_block_reason: null,
          auto_routed_to_chat: true,
          created_at: '2026-04-15T09:00:00Z',
        },
      ],
    }),
  });

  const items = await listMediaAnalysisEvents({
    limit: 5,
    status: 'success',
    userId: 'wx-openid-123',
    autoRoutedToChat: true,
  });

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/media-analysis-events?limit=5&status=success&user_id=wx-openid-123&auto_routed_to_chat=1',
    expect.objectContaining({
      headers: expect.objectContaining({
        'x-admin-token': 'secret-token',
      }),
      cache: 'no-store',
    }),
  );
  expect(items[0]).toEqual({
    id: 21,
    channel: 'wechat',
    source: 'wechat_official_account_image_media_analysis',
    userId: 'wx-openid-123',
    messageId: 'msg-123',
    mediaId: 'media-123',
    mediaType: 'image',
    provider: 'openai_compatible',
    status: 'success',
    summary: '识别到河南560分理科',
    renderedReply: '图片已自动进入高考志愿分析',
    extractedFields: { province: '河南', score: 560 },
    context: {
      msg_type: 'image',
      pic_url: 'https://example.com/image-123.png',
      create_time: '1710000001',
    },
    retryable: true,
    retryBlockReason: null,
    autoRoutedToChat: true,
    createdAt: '2026-04-15T09:00:00Z',
  });
});

test('retryMediaAnalysisEvent sends authenticated retry request', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      id: 22,
    }),
  });

  await retryMediaAnalysisEvent(22);

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/media-analysis-events/22/retry',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'x-admin-token': 'secret-token',
      }),
      cache: 'no-store',
    }),
  );
});
