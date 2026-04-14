export type AdminContentSummaryEntity = {
  slug: string;
  name: string;
  summary: string;
};

export type AdminContentSummaryList = {
  schools: AdminContentSummaryEntity[];
  majors: AdminContentSummaryEntity[];
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

const mapEntity = (item: {
  slug: string;
  name: string;
  summary: string;
}): AdminContentSummaryEntity => ({
  slug: item.slug,
  name: item.name,
  summary: item.summary,
});

export async function listContentSummaries(): Promise<AdminContentSummaryList> {
  const response = await fetch(`${getApiUrl()}/api/admin/content-summaries`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{
    schools: Array<{
      slug: string;
      name: string;
      summary: string;
    }>;
    majors: Array<{
      slug: string;
      name: string;
      summary: string;
    }>;
  }>(response);

  return {
    schools: payload.schools.map(mapEntity),
    majors: payload.majors.map(mapEntity),
  };
}

async function updateContentSummary(
  entityType: 'schools' | 'majors',
  slug: string,
  summary: string,
): Promise<AdminContentSummaryEntity> {
  const response = await fetch(`${getApiUrl()}/api/admin/content-summaries/${entityType}/${slug}`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      summary,
    }),
  });

  return mapEntity(
    await parseResponse<{
      slug: string;
      name: string;
      summary: string;
    }>(response),
  );
}

export async function updateSchoolSummary(
  slug: string,
  summary: string,
): Promise<AdminContentSummaryEntity> {
  return updateContentSummary('schools', slug, summary);
}

export async function updateMajorSummary(
  slug: string,
  summary: string,
): Promise<AdminContentSummaryEntity> {
  return updateContentSummary('majors', slug, summary);
}
