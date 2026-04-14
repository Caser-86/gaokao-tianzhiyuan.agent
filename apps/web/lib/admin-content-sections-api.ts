export type AdminContentSection = {
  type: string;
  title: string;
  items: string[];
};

export type AdminContentSectionsEntity = {
  slug: string;
  name: string;
  sections: AdminContentSection[];
};

export type AdminContentSectionsList = {
  schools: AdminContentSectionsEntity[];
  majors: AdminContentSectionsEntity[];
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

const mapSection = (item: {
  type: string;
  title: string;
  items: string[];
}): AdminContentSection => ({
  type: item.type,
  title: item.title,
  items: item.items ?? [],
});

const mapEntity = (item: {
  slug: string;
  name: string;
  sections?: Array<{
    type: string;
    title: string;
    items: string[];
  }>;
}): AdminContentSectionsEntity => ({
  slug: item.slug,
  name: item.name,
  sections: (item.sections ?? []).map(mapSection),
});

export async function listContentSections(): Promise<AdminContentSectionsList> {
  const response = await fetch(`${getApiUrl()}/api/admin/content-sections`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{
    schools: Array<{
      slug: string;
      name: string;
      sections?: Array<{
        type: string;
        title: string;
        items: string[];
      }>;
    }>;
    majors: Array<{
      slug: string;
      name: string;
      sections?: Array<{
        type: string;
        title: string;
        items: string[];
      }>;
    }>;
  }>(response);

  return {
    schools: payload.schools.map(mapEntity),
    majors: payload.majors.map(mapEntity),
  };
}

async function updateContentSections(
  entityType: 'schools' | 'majors',
  slug: string,
  sections: AdminContentSection[],
): Promise<AdminContentSectionsEntity> {
  const response = await fetch(`${getApiUrl()}/api/admin/content-sections/${entityType}/${slug}`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      sections: sections.map((section) => ({
        type: section.type,
        title: section.title,
        items: section.items,
      })),
    }),
  });

  return mapEntity(
    await parseResponse<{
      slug: string;
      name: string;
      sections?: Array<{
        type: string;
        title: string;
        items: string[];
      }>;
    }>(response),
  );
}

export async function updateSchoolSections(
  slug: string,
  sections: AdminContentSection[],
): Promise<AdminContentSectionsEntity> {
  return updateContentSections('schools', slug, sections);
}

export async function updateMajorSections(
  slug: string,
  sections: AdminContentSection[],
): Promise<AdminContentSectionsEntity> {
  return updateContentSections('majors', slug, sections);
}
