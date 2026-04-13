export type PlatformEntitlementsPayload = {
  product_slugs: string[];
  entitlements: string[];
};

const getPlatformApiUrl = (apiBaseUrl?: string): string =>
  apiBaseUrl ??
  process.env.NEXT_PUBLIC_GAOKAO_AGENT_API_URL ??
  process.env.GAOKAO_AGENT_API_URL ??
  'http://127.0.0.1:8000';

export async function evaluatePlatformEntitlements(
  productSlugs: string[],
  apiBaseUrl?: string,
): Promise<PlatformEntitlementsPayload> {
  const response = await fetch(
    `${getPlatformApiUrl(apiBaseUrl)}/api/platform/entitlements/evaluate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_slugs: productSlugs,
      }),
    },
  );

  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as PlatformEntitlementsPayload;
}
