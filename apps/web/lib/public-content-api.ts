import 'server-only';

export type PageSection = {
  type: string;
  title: string;
  items: string[];
};

export type RankingReference = {
  source: string;
  year: number;
  label: string;
  scope?: string;
  note?: string;
  url?: string;
};

export type DataProvenance = {
  status: 'demo' | 'secondary' | 'official';
  sourceName: string;
  sourceUrl: string | null;
  updatedAt: string;
  applicableYear: number | null;
  region: string;
  official: boolean;
  disclaimer: string;
};

type DataProvenancePayload = {
  status: DataProvenance['status'];
  source_name: string;
  source_url: string | null;
  updated_at: string;
  applicable_year: number | null;
  region: string;
  official: boolean;
  disclaimer: string;
};

export type SearchEntryData = {
  title: string;
  description: string;
  quickPrompts: string[];
  dataProvenance?: DataProvenance;
};

export type SchoolSummary = {
  slug: string;
  name: string;
  region: string;
  city: string;
  tags: string[];
  summary: string;
  heroImageUrl?: string;
  hasRankingReferences?: boolean;
};

export type MajorSummary = {
  slug: string;
  name: string;
  discipline: string;
  recommendedRegions: string[];
  summary: string;
  hasRankingReferences?: boolean;
};

export type SchoolDetail = SchoolSummary & {
  sections: PageSection[];
  relatedMajors: string[];
  rankingReferences: RankingReference[];
  dataProvenance?: DataProvenance;
};

export type MajorDetail = MajorSummary & {
  sections: PageSection[];
  relatedSchools: string[];
  rankingReferences: RankingReference[];
  dataProvenance?: DataProvenance;
};

export class PublicApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message || `Request failed with status ${status}`);
    this.name = 'PublicApiError';
    this.status = status;
  }
}

const getPublicApiUrl = (): string => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';

const mapDataProvenance = (
  payload: DataProvenancePayload | undefined,
): DataProvenance | undefined => {
  if (!payload) {
    return undefined;
  }

  return {
    status: payload.status,
    sourceName: payload.source_name,
    sourceUrl: payload.source_url,
    updatedAt: payload.updated_at,
    applicableYear: payload.applicable_year,
    region: payload.region,
    official: payload.official,
    disclaimer: payload.disclaimer,
  };
};

async function fetchPublicJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getPublicApiUrl()}${path}`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new PublicApiError(
      response.status,
      (await response.text()) || `Request failed with status ${response.status}`,
    );
  }

  return (await response.json()) as T;
}

export async function getSearchEntry(): Promise<SearchEntryData> {
  const payload = await fetchPublicJson<{
    title: string;
    description: string;
    quick_prompts: string[];
    data_provenance?: DataProvenancePayload;
  }>('/api/public/search-entry');

  return {
    title: payload.title,
    description: payload.description,
    quickPrompts: payload.quick_prompts,
    dataProvenance: mapDataProvenance(payload.data_provenance),
  };
}

export async function listSchools(): Promise<{
  items: SchoolSummary[];
  total: number;
  dataProvenance?: DataProvenance;
}> {
  const payload = await fetchPublicJson<{
    items: Array<{
      slug: string;
      name: string;
      region: string;
      city: string;
      tags: string[];
      summary: string;
      hero_image_url?: string | null;
      has_ranking_references?: boolean;
    }>;
    total: number;
    data_provenance?: DataProvenancePayload;
  }>('/api/public/schools');

  return {
    items: payload.items.map((item) => ({
      slug: item.slug,
      name: item.name,
      region: item.region,
      city: item.city,
      tags: item.tags,
      summary: item.summary,
      heroImageUrl: item.hero_image_url ?? '',
      hasRankingReferences: item.has_ranking_references ?? false,
    })),
    total: payload.total,
    dataProvenance: mapDataProvenance(payload.data_provenance),
  };
}

export async function listMajors(): Promise<{
  items: MajorSummary[];
  total: number;
  dataProvenance?: DataProvenance;
}> {
  const payload = await fetchPublicJson<{
    items: Array<{
      slug: string;
      name: string;
      discipline: string;
      recommended_regions: string[];
      summary: string;
      has_ranking_references?: boolean;
    }>;
    total: number;
    data_provenance?: DataProvenancePayload;
  }>('/api/public/majors');

  return {
    items: payload.items.map((item) => ({
      slug: item.slug,
      name: item.name,
      discipline: item.discipline,
      recommendedRegions: item.recommended_regions,
      summary: item.summary,
      hasRankingReferences: item.has_ranking_references ?? false,
    })),
    total: payload.total,
    dataProvenance: mapDataProvenance(payload.data_provenance),
  };
}

export async function getSchoolBySlug(slug: string): Promise<SchoolDetail> {
  const payload = await fetchPublicJson<{
    slug: string;
    name: string;
    region: string;
    city: string;
    tags: string[];
    summary: string;
    sections: PageSection[];
    related_majors: string[];
    ranking_references?: RankingReference[];
    data_provenance?: DataProvenancePayload;
  }>(`/api/public/schools/${slug}`);

  return {
    slug: payload.slug,
    name: payload.name,
    region: payload.region,
    city: payload.city,
    tags: payload.tags,
    summary: payload.summary,
    sections: payload.sections,
    relatedMajors: payload.related_majors,
    rankingReferences: payload.ranking_references ?? [],
    dataProvenance: mapDataProvenance(payload.data_provenance),
  };
}

export async function getMajorBySlug(slug: string): Promise<MajorDetail> {
  const payload = await fetchPublicJson<{
    slug: string;
    name: string;
    discipline: string;
    recommended_regions: string[];
    summary: string;
    sections: PageSection[];
    related_schools: string[];
    ranking_references?: RankingReference[];
    data_provenance?: DataProvenancePayload;
  }>(`/api/public/majors/${slug}`);

  return {
    slug: payload.slug,
    name: payload.name,
    discipline: payload.discipline,
    recommendedRegions: payload.recommended_regions,
    summary: payload.summary,
    sections: payload.sections,
    relatedSchools: payload.related_schools,
    rankingReferences: payload.ranking_references ?? [],
    dataProvenance: mapDataProvenance(payload.data_provenance),
  };
}
