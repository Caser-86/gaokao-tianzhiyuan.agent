export type AdminMediaAnalysisEvent = {
  id: number;
  channel: string;
  source: string;
  userId: string;
  messageId: string;
  mediaId: string;
  mediaType: string;
  provider: string;
  status: string;
  summary: string;
  renderedReply: string;
  extractedFields: Record<string, unknown>;
  context: Record<string, unknown>;
  retryable: boolean;
  retryBlockReason: string | null;
  autoRoutedToChat: boolean;
  createdAt: string;
};

export type AdminMediaAnalysisEventFilters = {
  limit?: number;
  status?: string;
  userId?: string;
  autoRoutedToChat?: boolean;
};

const getApiUrl = () => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';
const getAdminToken = () => process.env.GAOKAO_AGENT_ADMIN_TOKEN ?? 'dev-admin-token';

const parseResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
};

export async function listMediaAnalysisEvents({
  limit = 10,
  status,
  userId,
  autoRoutedToChat,
}: AdminMediaAnalysisEventFilters = {}): Promise<AdminMediaAnalysisEvent[]> {
  const searchParams = new URLSearchParams({
    limit: String(limit),
  });
  if (status) {
    searchParams.set('status', status);
  }
  if (userId) {
    searchParams.set('user_id', userId);
  }
  if (autoRoutedToChat !== undefined) {
    searchParams.set('auto_routed_to_chat', autoRoutedToChat ? '1' : '0');
  }
  const response = await fetch(
    `${getApiUrl()}/api/admin/media-analysis-events?${searchParams.toString()}`,
    {
      headers: {
        'x-admin-token': getAdminToken(),
      },
      cache: 'no-store',
    },
  );
  const payload = await parseResponse<{
    items: Array<{
      id: number;
      channel: string;
      source: string;
      user_id: string;
      message_id: string;
      media_id: string;
      media_type: string;
      provider: string;
      status: string;
      summary: string;
      rendered_reply: string;
      extracted_fields: Record<string, unknown>;
      context: Record<string, unknown>;
      retryable: boolean;
      retry_block_reason: string | null;
      auto_routed_to_chat: boolean;
      created_at: string;
    }>;
  }>(response);

  return payload.items.map((item) => ({
    id: item.id,
    channel: item.channel,
    source: item.source,
    userId: item.user_id,
    messageId: item.message_id,
    mediaId: item.media_id,
    mediaType: item.media_type,
    provider: item.provider,
    status: item.status,
    summary: item.summary,
    renderedReply: item.rendered_reply,
    extractedFields: item.extracted_fields,
    context: item.context,
    retryable: item.retryable,
    retryBlockReason: item.retry_block_reason,
    autoRoutedToChat: item.auto_routed_to_chat,
    createdAt: item.created_at,
  }));
}

export async function retryMediaAnalysisEvent(eventId: number): Promise<void> {
  const response = await fetch(
    `${getApiUrl()}/api/admin/media-analysis-events/${eventId}/retry`,
    {
      method: 'POST',
      headers: {
        'x-admin-token': getAdminToken(),
      },
      cache: 'no-store',
    },
  );

  await parseResponse(response);
}
