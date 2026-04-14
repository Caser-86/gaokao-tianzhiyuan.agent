'use server';

import { revalidatePath } from 'next/cache';

import {
  approveReviewQueueItem,
  rejectReviewQueueItem,
} from '../../../lib/admin-review-api';
import {
  updateFeaturedMajor,
  updateFeaturedSchool,
  updateMajorRotationRule,
  updateSchoolRotationRule,
} from '../../../lib/admin-featured-content-api';

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
