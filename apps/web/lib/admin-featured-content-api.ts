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

export type AdminFeaturedPreviewItem = {
  slug: string;
  name: string;
};

export type AdminFeaturedPreviewDay = {
  date: string;
  weekday: string;
  schools: AdminFeaturedPreviewItem[];
  majors: AdminFeaturedPreviewItem[];
};

export type AdminRotationRule = {
  enabled: boolean;
  frequencyDays: number;
  windowSize: number;
  orderedSlugs: string[];
};

export type AdminFeaturedContent = {
  schools: AdminFeaturedSchool[];
  majors: AdminFeaturedMajor[];
  rotation: {
    schools: AdminRotationRule;
    majors: AdminRotationRule;
  };
  preview: {
    today: {
      schools: AdminFeaturedPreviewItem[];
      majors: AdminFeaturedPreviewItem[];
    };
    next: {
      schools: AdminFeaturedPreviewItem[];
      majors: AdminFeaturedPreviewItem[];
    };
    schedule: AdminFeaturedPreviewDay[];
    selectedDate: AdminFeaturedPreviewDay | null;
    selectedDateError: string | null;
  };
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

const mapRotationRule = (item?: {
  enabled: boolean;
  frequency_days: number;
  window_size: number;
  ordered_slugs: string[];
}): AdminRotationRule => ({
  enabled: item?.enabled ?? false,
  frequencyDays: item?.frequency_days ?? 1,
  windowSize: item?.window_size ?? 1,
  orderedSlugs: item?.ordered_slugs ?? [],
});

const mapPreviewItems = (
  items?: Array<{
    slug: string;
    name: string;
  }>,
): AdminFeaturedPreviewItem[] => items ?? [];

const mapPreviewDay = (day?: {
  date: string;
  weekday: string;
  schools?: Array<{
    slug: string;
    name: string;
  }>;
  majors?: Array<{
    slug: string;
    name: string;
  }>;
}): AdminFeaturedPreviewDay | null => {
  if (!day) {
    return null;
  }

  return {
    date: day.date,
    weekday: day.weekday,
    schools: mapPreviewItems(day.schools),
    majors: mapPreviewItems(day.majors),
  };
};

export async function listFeaturedContent(previewDate?: string): Promise<AdminFeaturedContent> {
  const url = new URL(`${getApiUrl()}/api/admin/featured-content`);
  if (previewDate) {
    url.searchParams.set('preview_date', previewDate);
  }

  const response = await fetch(url.toString(), {
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
    rotation?: {
      schools?: {
        enabled: boolean;
        frequency_days: number;
        window_size: number;
        ordered_slugs: string[];
      };
      majors?: {
        enabled: boolean;
        frequency_days: number;
        window_size: number;
        ordered_slugs: string[];
      };
    };
    preview?: {
      today?: {
        schools?: Array<{
          slug: string;
          name: string;
        }>;
        majors?: Array<{
          slug: string;
          name: string;
        }>;
      };
      next?: {
        schools?: Array<{
          slug: string;
          name: string;
        }>;
        majors?: Array<{
          slug: string;
          name: string;
        }>;
      };
      schedule?: Array<{
        date: string;
        weekday: string;
        schools?: Array<{
          slug: string;
          name: string;
        }>;
        majors?: Array<{
          slug: string;
          name: string;
        }>;
      }>;
      selected_date?: {
        date: string;
        weekday: string;
        schools?: Array<{
          slug: string;
          name: string;
        }>;
        majors?: Array<{
          slug: string;
          name: string;
        }>;
      } | null;
      selected_date_error?: string | null;
    };
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
    rotation: {
      schools: mapRotationRule(payload.rotation?.schools),
      majors: mapRotationRule(payload.rotation?.majors),
    },
    preview: {
      today: {
        schools: mapPreviewItems(payload.preview?.today?.schools),
        majors: mapPreviewItems(payload.preview?.today?.majors),
      },
      next: {
        schools: mapPreviewItems(payload.preview?.next?.schools),
        majors: mapPreviewItems(payload.preview?.next?.majors),
      },
      schedule:
        payload.preview?.schedule?.map((day) => ({
          date: day.date,
          weekday: day.weekday,
          schools: mapPreviewItems(day.schools),
          majors: mapPreviewItems(day.majors),
        })) ?? [],
      selectedDate: mapPreviewDay(payload.preview?.selected_date ?? undefined),
      selectedDateError: payload.preview?.selected_date_error ?? null,
    },
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

export async function updateSchoolRotationRule(
  rule: AdminRotationRule,
): Promise<AdminRotationRule> {
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content/rotation/schools`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      enabled: rule.enabled,
      frequency_days: rule.frequencyDays,
      window_size: rule.windowSize,
      ordered_slugs: rule.orderedSlugs,
    }),
  });

  return mapRotationRule(
    await parseResponse<{
      enabled: boolean;
      frequency_days: number;
      window_size: number;
      ordered_slugs: string[];
    }>(response),
  );
}

export async function updateMajorRotationRule(
  rule: AdminRotationRule,
): Promise<AdminRotationRule> {
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content/rotation/majors`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      enabled: rule.enabled,
      frequency_days: rule.frequencyDays,
      window_size: rule.windowSize,
      ordered_slugs: rule.orderedSlugs,
    }),
  });

  return mapRotationRule(
    await parseResponse<{
      enabled: boolean;
      frequency_days: number;
      window_size: number;
      ordered_slugs: string[];
    }>(response),
  );
}
