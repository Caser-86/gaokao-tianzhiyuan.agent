'use server';

import { revalidatePath } from 'next/cache';

import {
  updateFeaturedMajor,
  updateFeaturedSchool,
  updateMajorRotationRule,
  updateSchoolRotationRule,
} from '../../../lib/admin-featured-content-api';
import {
  type AdminRankingReference,
  updateMajorRankingReferences,
  updateSchoolRankingReferences,
} from '../../../lib/admin-ranking-reference-api';
import {
  approveReviewQueueItem,
  rejectReviewQueueItem,
} from '../../../lib/admin-review-api';

const parseQueueId = (rawValue: FormDataEntryValue | null): number => {
  const value = typeof rawValue === 'string' ? Number.parseInt(rawValue, 10) : Number.NaN;
  if (Number.isNaN(value)) {
    throw new Error('queue id is required');
  }
  return value;
};

const parseRequiredSlug = (rawValue: FormDataEntryValue | null): string => {
  const slug = String(rawValue ?? '').trim();
  if (!slug) {
    throw new Error('slug is required');
  }
  return slug;
};

const parsePositiveNumber = (rawValue: FormDataEntryValue | null, fieldName: string): number => {
  const value = Number.parseInt(String(rawValue ?? ''), 10);
  if (Number.isNaN(value) || value < 1) {
    throw new Error(`${fieldName} must be positive`);
  }
  return value;
};

const parseOrderedSlugs = (rawValue: FormDataEntryValue | null): string[] =>
  String(rawValue ?? '')
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);

const parseRankingReferenceRows = (formData: FormData): AdminRankingReference[] => {
  const rowCount = parsePositiveNumber(formData.get('rowCount'), 'rowCount');
  const rows: AdminRankingReference[] = [];

  for (let index = 0; index < rowCount; index += 1) {
    const source = String(formData.get(`source_${index}`) ?? '').trim();
    const yearRaw = String(formData.get(`year_${index}`) ?? '').trim();
    const label = String(formData.get(`label_${index}`) ?? '').trim();
    const scope = String(formData.get(`scope_${index}`) ?? '').trim();
    const note = String(formData.get(`note_${index}`) ?? '').trim();
    const url = String(formData.get(`url_${index}`) ?? '').trim();

    if (!source && !yearRaw && !label && !scope && !note && !url) {
      continue;
    }

    const year = Number.parseInt(yearRaw, 10);
    if (!source || !label || Number.isNaN(year) || year < 1) {
      throw new Error('ranking reference row is invalid');
    }

    rows.push({
      source,
      year,
      label,
      scope,
      note,
      url,
    });
  }

  return rows;
};

export async function approveReviewQueueAction(formData: FormData): Promise<void> {
  try {
    const queueId = parseQueueId(formData.get('queueId'));
    const reviewedBy = String(formData.get('reviewedBy') ?? 'web-admin');

    await approveReviewQueueItem(queueId, reviewedBy);
    revalidatePath('/admin');
  } catch {
    return;
  }
}

export async function rejectReviewQueueAction(formData: FormData): Promise<void> {
  try {
    const queueId = parseQueueId(formData.get('queueId'));
    const reviewedBy = String(formData.get('reviewedBy') ?? 'web-admin');
    const reviewNote = String(formData.get('reviewNote') ?? '').trim();

    await rejectReviewQueueItem(queueId, reviewedBy, reviewNote || undefined);
    revalidatePath('/admin');
  } catch {
    return;
  }
}

export async function updateFeaturedSchoolAction(formData: FormData): Promise<void> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const heroImageUrl = String(formData.get('heroImageUrl') ?? '').trim();
    const isFeatured = formData.get('isFeatured') === 'on';

    await updateFeaturedSchool(slug, isFeatured, heroImageUrl);
    revalidatePath('/admin');
    revalidatePath('/');
  } catch {
    return;
  }
}

export async function updateFeaturedMajorAction(formData: FormData): Promise<void> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const isFeatured = formData.get('isFeatured') === 'on';

    await updateFeaturedMajor(slug, isFeatured);
    revalidatePath('/admin');
    revalidatePath('/');
  } catch {
    return;
  }
}

export async function updateSchoolRotationAction(formData: FormData): Promise<void> {
  try {
    await updateSchoolRotationRule({
      enabled: formData.get('enabled') === 'on',
      frequencyDays: parsePositiveNumber(formData.get('frequencyDays'), 'frequencyDays'),
      windowSize: parsePositiveNumber(formData.get('windowSize'), 'windowSize'),
      orderedSlugs: parseOrderedSlugs(formData.get('orderedSlugs')),
    });
    revalidatePath('/admin');
    revalidatePath('/');
  } catch {
    return;
  }
}

export async function updateMajorRotationAction(formData: FormData): Promise<void> {
  try {
    await updateMajorRotationRule({
      enabled: formData.get('enabled') === 'on',
      frequencyDays: parsePositiveNumber(formData.get('frequencyDays'), 'frequencyDays'),
      windowSize: parsePositiveNumber(formData.get('windowSize'), 'windowSize'),
      orderedSlugs: parseOrderedSlugs(formData.get('orderedSlugs')),
    });
    revalidatePath('/admin');
    revalidatePath('/');
  } catch {
    return;
  }
}

export async function updateSchoolRankingReferencesAction(formData: FormData): Promise<void> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const rankingReferences = parseRankingReferenceRows(formData);

    await updateSchoolRankingReferences(slug, rankingReferences);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/schools/${slug}`);
  } catch {
    return;
  }
}

export async function updateMajorRankingReferencesAction(formData: FormData): Promise<void> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const rankingReferences = parseRankingReferenceRows(formData);

    await updateMajorRankingReferences(slug, rankingReferences);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/majors/${slug}`);
  } catch {
    return;
  }
}
