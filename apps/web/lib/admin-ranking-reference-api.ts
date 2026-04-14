export type AdminRankingReference = {
  source: string;
  year: number;
  label: string;
  scope: string;
  note: string;
  url: string;
};

export type AdminRankingReferenceEntity = {
  slug: string;
  name: string;
  rankingReferences: AdminRankingReference[];
};

export type AdminRankingReferenceList = {
  schools: AdminRankingReferenceEntity[];
  majors: AdminRankingReferenceEntity[];
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

const mapRankingReference = (item: {
  source: string;
  year: number;
  label: string;
  scope?: string | null;
  note?: string | null;
  url?: string | null;
}): AdminRankingReference => ({
  source: item.source,
  year: item.year,
  label: item.label,
  scope: item.scope ?? '',
  note: item.note ?? '',
  url: item.url ?? '',
});

const mapRankingReferenceEntity = (item: {
  slug: string;
  name: string;
  ranking_references?: Array<{
    source: string;
    year: number;
    label: string;
    scope?: string | null;
    note?: string | null;
    url?: string | null;
  }>;
}): AdminRankingReferenceEntity => ({
  slug: item.slug,
  name: item.name,
  rankingReferences: (item.ranking_references ?? []).map(mapRankingReference),
});

export async function listRankingReferences(): Promise<AdminRankingReferenceList> {
  const response = await fetch(`${getApiUrl()}/api/admin/ranking-references`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{
    schools: Array<{
      slug: string;
      name: string;
      ranking_references?: Array<{
        source: string;
        year: number;
        label: string;
        scope?: string | null;
        note?: string | null;
        url?: string | null;
      }>;
    }>;
    majors: Array<{
      slug: string;
      name: string;
      ranking_references?: Array<{
        source: string;
        year: number;
        label: string;
        scope?: string | null;
        note?: string | null;
        url?: string | null;
      }>;
    }>;
  }>(response);

  return {
    schools: payload.schools.map(mapRankingReferenceEntity),
    majors: payload.majors.map(mapRankingReferenceEntity),
  };
}

async function updateRankingReferenceEntity(
  entityType: 'schools' | 'majors',
  slug: string,
  rankingReferences: AdminRankingReference[],
): Promise<AdminRankingReferenceEntity> {
  const response = await fetch(`${getApiUrl()}/api/admin/ranking-references/${entityType}/${slug}`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      ranking_references: rankingReferences.map((item) => ({
        source: item.source,
        year: item.year,
        label: item.label,
        scope: item.scope,
        note: item.note,
        url: item.url,
      })),
    }),
  });

  return mapRankingReferenceEntity(
    await parseResponse<{
      slug: string;
      name: string;
      ranking_references?: Array<{
        source: string;
        year: number;
        label: string;
        scope?: string | null;
        note?: string | null;
        url?: string | null;
      }>;
    }>(response),
  );
}

export async function updateSchoolRankingReferences(
  slug: string,
  rankingReferences: AdminRankingReference[],
): Promise<AdminRankingReferenceEntity> {
  return updateRankingReferenceEntity('schools', slug, rankingReferences);
}

export async function updateMajorRankingReferences(
  slug: string,
  rankingReferences: AdminRankingReference[],
): Promise<AdminRankingReferenceEntity> {
  return updateRankingReferenceEntity('majors', slug, rankingReferences);
}
