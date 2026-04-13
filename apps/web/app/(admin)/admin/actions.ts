'use server';

import { revalidatePath } from 'next/cache';

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
