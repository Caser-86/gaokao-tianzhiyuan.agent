export type ChatMessageRequest = {
  userId?: string;
  message: string;
};

export type ChatMessageResponse = {
  request_id: string;
  output: {
    type: 'structured_json';
    content: {
      summary?: string;
      analysis?: string;
      follow_up_questions?: string[];
      rendered_reply?: string;
    };
  };
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
  const response = await fetch(`${getChatApiUrl(apiBaseUrl)}/api/chat/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      channel: 'web',
      user_id: payload.userId ?? 'web-anonymous',
      message: payload.message,
      metadata: {
        source: 'web_chat_page',
      },
    }),
  });

  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as ChatMessageResponse;
}
