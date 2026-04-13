export type PlatformEventPayload = {
  eventName: string;
  step: string;
  metadata: Record<string, string>;
};

const getPlatformApiUrl = (): string =>
  process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL ??
  process.env.GAOKAO_AGENT_API_URL ??
  'http://127.0.0.1:8000';

export async function trackPlatformEvent(payload: PlatformEventPayload): Promise<void> {
  await fetch(`${getPlatformApiUrl()}/api/platform/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_name: payload.eventName,
      step: payload.step,
      metadata: payload.metadata,
    }),
  }).catch(() => undefined);
}
