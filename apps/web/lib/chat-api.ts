export type ChatMessageRequest = {
  /** Legacy fixture hint; the API resolves the real subject from its session cookie. */
  userId?: string;
  message: string;
  sessionId?: string;
};

export type ChatMessageResponse = {
  request_id: string;
  session_id?: string;
  output: {
    type: 'structured_json';
    content: {
      actions?: Array<{
        type?: string;
        label: string;
        target?: string;
      }>;
      risk_flags?: string[];
      summary?: string;
      analysis?: string;
      follow_up_questions?: string[];
      rendered_reply?: string;
      suggestions?: Array<{
        type?: string;
        title: string;
        slug?: string;
        reason?: string;
        confidence?: number;
      }>;
    };
  };
};

export type ChatSessionMessage = {
  id: number;
  request_id: string;
  role: 'user' | 'assistant';
  content_type: string;
  content: string;
  payload?: Record<string, unknown> | null;
  created_at: string;
};

export type ChatSessionHistoryResponse = {
  session_id: string;
  channel: string;
  created_at: string;
  updated_at: string;
  expires_at: string;
  items: ChatSessionMessage[];
};

const getChatApiUrl = (apiBaseUrl?: string): string =>
  apiBaseUrl ??
  process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL ??
  process.env.GAOKAO_AGENT_API_URL ??
  'http://127.0.0.1:8000';

export async function sendChatMessage(
  payload: ChatMessageRequest,
  apiBaseUrl?: string,
): Promise<ChatMessageResponse> {
  const body: Record<string, unknown> = {
    channel: 'web',
    message: payload.message,
    metadata: {
      source: 'web_chat_page',
    },
  };
  if (payload.sessionId) {
    body.session_id = payload.sessionId;
  }

  const response = await fetch(`${getChatApiUrl(apiBaseUrl)}/api/chat/skills/zhangxuefeng/invoke`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as ChatMessageResponse;
}

export async function getChatSessionMessages(
  sessionId: string,
  apiBaseUrl?: string,
): Promise<ChatSessionHistoryResponse> {
  const response = await fetch(
    `${getChatApiUrl(apiBaseUrl)}/api/chat/sessions/${encodeURIComponent(sessionId)}/messages`,
    { credentials: 'include' },
  );
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }
  return (await response.json()) as ChatSessionHistoryResponse;
}

export async function deleteChatSession(
  sessionId: string,
  apiBaseUrl?: string,
): Promise<{ session_id: string; deleted: boolean }> {
  const response = await fetch(
    `${getChatApiUrl(apiBaseUrl)}/api/chat/sessions/${encodeURIComponent(sessionId)}`,
    { method: 'DELETE', credentials: 'include' },
  );
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }
  return (await response.json()) as { session_id: string; deleted: boolean };
}
