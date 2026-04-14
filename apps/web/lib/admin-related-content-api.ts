export type AdminRelatedSchoolEntity = {
  slug: string;
  name: string;
  relatedMajors: string[];
};

export type AdminRelatedMajorEntity = {
  slug: string;
  name: string;
  relatedSchools: string[];
};

export type AdminRelatedContentList = {
  schools: AdminRelatedSchoolEntity[];
  majors: AdminRelatedMajorEntity[];
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

const mapSchoolEntity = (item: {
  slug: string;
  name: string;
  related_majors?: string[];
}): AdminRelatedSchoolEntity => ({
  slug: item.slug,
  name: item.name,
  relatedMajors: item.related_majors ?? [],
});

const mapMajorEntity = (item: {
  slug: string;
  name: string;
  related_schools?: string[];
}): AdminRelatedMajorEntity => ({
  slug: item.slug,
  name: item.name,
  relatedSchools: item.related_schools ?? [],
});

export async function listRelatedContent(): Promise<AdminRelatedContentList> {
  const response = await fetch(`${getApiUrl()}/api/admin/related-content`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{
    schools: Array<{
      slug: string;
      name: string;
      related_majors?: string[];
    }>;
    majors: Array<{
      slug: string;
      name: string;
      related_schools?: string[];
    }>;
  }>(response);

  return {
    schools: payload.schools.map(mapSchoolEntity),
    majors: payload.majors.map(mapMajorEntity),
  };
}

async function updateRelatedContent(
  entityType: 'schools' | 'majors',
  slug: string,
  body: Record<string, string[]>,
): Promise<AdminRelatedSchoolEntity | AdminRelatedMajorEntity> {
  const response = await fetch(`${getApiUrl()}/api/admin/related-content/${entityType}/${slug}`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify(body),
  });

  const payload = await parseResponse<{
    slug: string;
    name: string;
    related_majors?: string[];
    related_schools?: string[];
  }>(response);

  return entityType === 'schools' ? mapSchoolEntity(payload) : mapMajorEntity(payload);
}

export async function updateSchoolRelatedContent(
  slug: string,
  relatedMajors: string[],
): Promise<AdminRelatedSchoolEntity> {
  return updateRelatedContent('schools', slug, {
    related_majors: relatedMajors,
  }) as Promise<AdminRelatedSchoolEntity>;
}

export async function updateMajorRelatedContent(
  slug: string,
  relatedSchools: string[],
): Promise<AdminRelatedMajorEntity> {
  return updateRelatedContent('majors', slug, {
    related_schools: relatedSchools,
  }) as Promise<AdminRelatedMajorEntity>;
}
