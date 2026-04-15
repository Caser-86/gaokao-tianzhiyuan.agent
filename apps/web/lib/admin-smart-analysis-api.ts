export type AdminSmartAnalysisMode = 'off' | 'gated' | 'on';

export type AdminSmartAnalysisSettings = {
  mode: AdminSmartAnalysisMode;
};

export type AdminSmartAnalysisEntitlement = {
  name: string;
  enabled: boolean;
};

export type AdminSmartAnalysisUser = {
  userId: string;
  entitlements: AdminSmartAnalysisEntitlement[];
};

const getApiUrl = () => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';
const getAdminToken = () => process.env.GAOKAO_AGENT_ADMIN_TOKEN ?? 'dev-admin-token';

const buildHeaders = (contentType?: string) => {
  const headers: Record<string, string> = {
    'x-admin-token': getAdminToken(),
  };

  if (contentType) {
    headers['Content-Type'] = contentType;
  }

  return headers;
};

const parseResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
};

export async function getSmartAnalysisSettings(): Promise<AdminSmartAnalysisSettings> {
  const response = await fetch(`${getApiUrl()}/api/admin/smart-analysis/settings`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  return parseResponse<AdminSmartAnalysisSettings>(response);
}

export async function updateSmartAnalysisSettings(
  mode: AdminSmartAnalysisMode,
): Promise<AdminSmartAnalysisSettings> {
  const response = await fetch(`${getApiUrl()}/api/admin/smart-analysis/settings`, {
    method: 'PUT',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({ mode }),
  });
  return parseResponse<AdminSmartAnalysisSettings>(response);
}

export async function getSmartAnalysisUser(userId: string): Promise<AdminSmartAnalysisUser> {
  const response = await fetch(
    `${getApiUrl()}/api/admin/smart-analysis/users/${encodeURIComponent(userId)}`,
    {
      headers: buildHeaders(),
      cache: 'no-store',
    },
  );
  const payload = await parseResponse<{
    user_id: string;
    entitlements: AdminSmartAnalysisEntitlement[];
  }>(response);

  return {
    userId: payload.user_id,
    entitlements: payload.entitlements,
  };
}

export async function updateSmartAnalysisUser(
  userId: string,
  enabled: boolean,
): Promise<AdminSmartAnalysisUser> {
  const response = await fetch(
    `${getApiUrl()}/api/admin/smart-analysis/users/${encodeURIComponent(userId)}`,
    {
      method: 'PUT',
      headers: buildHeaders('application/json'),
      body: JSON.stringify({ smart_analysis_enabled: enabled }),
    },
  );
  const payload = await parseResponse<{
    user_id: string;
    entitlements: AdminSmartAnalysisEntitlement[];
  }>(response);

  return {
    userId: payload.user_id,
    entitlements: payload.entitlements,
  };
}
