export type AdminFeaturedSchool = {
  slug: string;
  name: string;
  isFeatured: boolean;
  heroImageUrl: string;
};

export type AdminFeaturedMajor = {
  slug: string;
  name: string;
  isFeatured: boolean;
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

export async function listFeaturedContent(): Promise<{
  schools: AdminFeaturedSchool[];
  majors: AdminFeaturedMajor[];
}> {
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{
    schools: Array<{
      slug: string;
      name: string;
      is_featured: boolean;
      hero_image_url?: string | null;
    }>;
    majors: Array<{
      slug: string;
      name: string;
      is_featured: boolean;
    }>;
  }>(response);

  return {
    schools: payload.schools.map((item) => ({
      slug: item.slug,
      name: item.name,
      isFeatured: item.is_featured,
      heroImageUrl: item.hero_image_url ?? '',
    })),
    majors: payload.majors.map((item) => ({
      slug: item.slug,
      name: item.name,
      isFeatured: item.is_featured,
    })),
  };
}

export async function updateFeaturedSchool(
  slug: string,
  isFeatured: boolean,
  heroImageUrl: string,
): Promise<AdminFeaturedSchool> {
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content/schools/${slug}`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      is_featured: isFeatured,
      hero_image_url: heroImageUrl,
    }),
  });
  const payload = await parseResponse<{
    slug: string;
    name: string;
    is_featured: boolean;
    hero_image_url?: string | null;
  }>(response);

  return {
    slug: payload.slug,
    name: payload.name,
    isFeatured: payload.is_featured,
    heroImageUrl: payload.hero_image_url ?? '',
  };
}

export async function updateFeaturedMajor(
  slug: string,
  isFeatured: boolean,
): Promise<AdminFeaturedMajor> {
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content/majors/${slug}`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      is_featured: isFeatured,
    }),
  });
  const payload = await parseResponse<{
    slug: string;
    name: string;
    is_featured: boolean;
  }>(response);

  return {
    slug: payload.slug,
    name: payload.name,
    isFeatured: payload.is_featured,
  };
}
