import 'server-only';

export type PlatformProduct = {
  slug: string;
  name: string;
  description: string;
  entitlements: string[];
};

const getPlatformApiUrl = (): string =>
  process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';

export async function listPlatformProducts(): Promise<{ items: PlatformProduct[] }> {
  const response = await fetch(`${getPlatformApiUrl()}/api/platform/products`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as { items: PlatformProduct[] };
}
