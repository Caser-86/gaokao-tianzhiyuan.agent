'use server';

import { revalidatePath } from 'next/cache';

import {
  suggestFeaturedSchoolImage,
  updateFeaturedMajor,
  updateFeaturedSchool,
  updateMajorRotationRule,
  updateSchoolRotationRule,
} from '../../../lib/admin-featured-content-api';
import {
  updateMajorSummary,
  updateSchoolSummary,
} from '../../../lib/admin-content-summary-api';
import {
  type AdminContentSection,
  updateMajorSections,
  updateSchoolSections,
} from '../../../lib/admin-content-sections-api';
import {
  updateMajorRelatedContent,
  updateSchoolRelatedContent,
} from '../../../lib/admin-related-content-api';
import {
  type AdminRankingReference,
  updateMajorRankingReferences,
  updateSchoolRankingReferences,
} from '../../../lib/admin-ranking-reference-api';
import {
  approveReviewQueueItem,
  rejectReviewQueueItem,
} from '../../../lib/admin-review-api';
import {
  type AdminSmartAnalysisMode,
  updateSmartAnalysisSettings,
  updateSmartAnalysisUser,
} from '../../../lib/admin-smart-analysis-api';
import { retryMediaAnalysisEvent } from '../../../lib/admin-media-analysis-api';

export type AdminActionResult =
  | { ok: true; message: string }
  | { ok: false; message: string };

const ADMIN_ERROR_MESSAGE_LIMIT = 280;

const extractErrorMessage = (error: unknown): string => {
  const rawMessage = error instanceof Error ? error.message : String(error ?? '');
  const trimmedMessage = rawMessage.trim();

  if (trimmedMessage) {
    try {
      const payload: unknown = JSON.parse(trimmedMessage);
      if (payload && typeof payload === 'object' && 'detail' in payload) {
        const detail = payload.detail;
        if (typeof detail === 'string' && detail.trim()) {
          return detail.trim().slice(0, ADMIN_ERROR_MESSAGE_LIMIT);
        }
        if (Array.isArray(detail)) {
          const messages = detail
            .map((item) => {
              if (typeof item === 'string') {
                return item.trim();
              }
              if (item && typeof item === 'object' && 'msg' in item) {
                return typeof item.msg === 'string' ? item.msg.trim() : '';
              }
              return '';
            })
            .filter(Boolean);
          if (messages.length > 0) {
            return messages.join('；').slice(0, ADMIN_ERROR_MESSAGE_LIMIT);
          }
        }
      }
    } catch {
      // Non-JSON backend messages are still shown below after truncation.
    }
  }

  return (
    trimmedMessage.slice(0, ADMIN_ERROR_MESSAGE_LIMIT) || '管理操作失败，请稍后重试'
  );
};

const actionSuccess = (message: string): AdminActionResult => ({ ok: true, message });

const actionFailure = (error: unknown): AdminActionResult => ({
  ok: false,
  message: extractErrorMessage(error),
});

const parseQueueId = (rawValue: FormDataEntryValue | null): number => {
  const value = typeof rawValue === 'string' ? Number.parseInt(rawValue, 10) : Number.NaN;
  if (Number.isNaN(value)) {
    throw new Error('queue id is required');
  }
  return value;
};

const parseEventId = (rawValue: FormDataEntryValue | null): number => {
  const value = typeof rawValue === 'string' ? Number.parseInt(rawValue, 10) : Number.NaN;
  if (Number.isNaN(value)) {
    throw new Error('event id is required');
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

const parseRequiredSummary = (rawValue: FormDataEntryValue | null): string => {
  const summary = String(rawValue ?? '').trim();
  if (!summary) {
    throw new Error('summary is required');
  }
  return summary;
};

const parseSmartAnalysisMode = (rawValue: FormDataEntryValue | null): AdminSmartAnalysisMode => {
  const mode = String(rawValue ?? '').trim();
  if (mode === 'off' || mode === 'gated' || mode === 'on') {
    return mode;
  }
  throw new Error('smart analysis mode is invalid');
};

const parseRequiredUserId = (rawValue: FormDataEntryValue | null): string => {
  const userId = String(rawValue ?? '').trim();
  if (!userId) {
    throw new Error('userId is required');
  }
  return userId;
};

const parseBooleanFlag = (rawValue: FormDataEntryValue | null, fieldName: string): boolean => {
  const value = String(rawValue ?? '').trim().toLowerCase();
  if (value === 'true') {
    return true;
  }
  if (value === 'false') {
    return false;
  }
  throw new Error(`${fieldName} must be true or false`);
};

const parseSlugLines = (rawValue: FormDataEntryValue | null): string[] =>
  String(rawValue ?? '')
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);

const parseContentSectionRows = (formData: FormData): AdminContentSection[] => {
  const rowCount = parsePositiveNumber(formData.get('rowCount'), 'rowCount');
  const sections: AdminContentSection[] = [];

  for (let index = 0; index < rowCount; index += 1) {
    const type = String(formData.get(`section_type_${index}`) ?? '').trim();
    const title = String(formData.get(`section_title_${index}`) ?? '').trim();
    const items = String(formData.get(`section_items_${index}`) ?? '')
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);

    if (!type && !title && items.length === 0) {
      continue;
    }

    if (!type || !title || items.length === 0) {
      throw new Error('content section row is invalid');
    }

    sections.push({ type, title, items });
  }

  return sections;
};

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

export async function approveReviewQueueAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const queueId = parseQueueId(formData.get('queueId'));
    const reviewedBy = String(formData.get('reviewedBy') ?? 'web-admin');

    await approveReviewQueueItem(queueId, reviewedBy);
    revalidatePath('/admin');
    return actionSuccess('审核已通过');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function rejectReviewQueueAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const queueId = parseQueueId(formData.get('queueId'));
    const reviewedBy = String(formData.get('reviewedBy') ?? 'web-admin');
    const reviewNote = String(formData.get('reviewNote') ?? '').trim();

    await rejectReviewQueueItem(queueId, reviewedBy, reviewNote || undefined);
    revalidatePath('/admin');
    return actionSuccess('审核已驳回');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function retryMediaAnalysisEventAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const eventId = parseEventId(formData.get('eventId'));

    await retryMediaAnalysisEvent(eventId);
    revalidatePath('/admin');
    return actionSuccess('媒体分析已提交重试');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateFeaturedSchoolAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const heroImageUrl = String(formData.get('heroImageUrl') ?? '').trim();
    const isFeatured = formData.get('isFeatured') === 'on';

    await updateFeaturedSchool(slug, isFeatured, heroImageUrl);
    revalidatePath('/admin');
    revalidatePath('/');
    return actionSuccess('学校展示配置已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function suggestSchoolImageAction(formData: FormData) {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    return suggestFeaturedSchoolImage(slug);
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateFeaturedMajorAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const isFeatured = formData.get('isFeatured') === 'on';

    await updateFeaturedMajor(slug, isFeatured);
    revalidatePath('/admin');
    revalidatePath('/');
    return actionSuccess('专业展示配置已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateSmartAnalysisModeAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const mode = parseSmartAnalysisMode(formData.get('mode'));

    await updateSmartAnalysisSettings(mode);
    revalidatePath('/admin');
    return actionSuccess('智能分析全局模式已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateSmartAnalysisUserAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const userId = parseRequiredUserId(formData.get('userId'));
    const enabled = parseBooleanFlag(formData.get('enabled'), 'enabled');

    await updateSmartAnalysisUser(userId, enabled);
    revalidatePath('/admin');
    return actionSuccess('用户智能分析权益已更新');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateSchoolRotationAction(formData: FormData): Promise<AdminActionResult> {
  try {
    await updateSchoolRotationRule({
      enabled: formData.get('enabled') === 'on',
      frequencyDays: parsePositiveNumber(formData.get('frequencyDays'), 'frequencyDays'),
      windowSize: parsePositiveNumber(formData.get('windowSize'), 'windowSize'),
      orderedSlugs: parseOrderedSlugs(formData.get('orderedSlugs')),
    });
    revalidatePath('/admin');
    revalidatePath('/');
    return actionSuccess('学校轮换规则已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateMajorRotationAction(formData: FormData): Promise<AdminActionResult> {
  try {
    await updateMajorRotationRule({
      enabled: formData.get('enabled') === 'on',
      frequencyDays: parsePositiveNumber(formData.get('frequencyDays'), 'frequencyDays'),
      windowSize: parsePositiveNumber(formData.get('windowSize'), 'windowSize'),
      orderedSlugs: parseOrderedSlugs(formData.get('orderedSlugs')),
    });
    revalidatePath('/admin');
    revalidatePath('/');
    return actionSuccess('专业轮换规则已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateSchoolRankingReferencesAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const rankingReferences = parseRankingReferenceRows(formData);

    await updateSchoolRankingReferences(slug, rankingReferences);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/schools/${slug}`);
    return actionSuccess('学校榜单引用已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateMajorRankingReferencesAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const rankingReferences = parseRankingReferenceRows(formData);

    await updateMajorRankingReferences(slug, rankingReferences);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/majors/${slug}`);
    return actionSuccess('专业榜单引用已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateSchoolSummaryAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const summary = parseRequiredSummary(formData.get('summary'));

    await updateSchoolSummary(slug, summary);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/schools/${slug}`);
    return actionSuccess('学校摘要已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateMajorSummaryAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const summary = parseRequiredSummary(formData.get('summary'));

    await updateMajorSummary(slug, summary);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/majors/${slug}`);
    return actionSuccess('专业摘要已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateSchoolSectionsAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const sections = parseContentSectionRows(formData);

    await updateSchoolSections(slug, sections);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/schools/${slug}`);
    return actionSuccess('学校正文模块已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateMajorSectionsAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const sections = parseContentSectionRows(formData);

    await updateMajorSections(slug, sections);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/majors/${slug}`);
    return actionSuccess('专业正文模块已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateSchoolRelatedContentAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const relatedMajors = parseSlugLines(formData.get('relatedMajors'));

    await updateSchoolRelatedContent(slug, relatedMajors);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/schools/${slug}`);
    return actionSuccess('学校相关推荐已保存');
  } catch (error) {
    return actionFailure(error);
  }
}

export async function updateMajorRelatedContentAction(formData: FormData): Promise<AdminActionResult> {
  try {
    const slug = parseRequiredSlug(formData.get('slug'));
    const relatedSchools = parseSlugLines(formData.get('relatedSchools'));

    await updateMajorRelatedContent(slug, relatedSchools);
    revalidatePath('/admin');
    revalidatePath('/');
    revalidatePath(`/majors/${slug}`);
    return actionSuccess('专业相关推荐已保存');
  } catch (error) {
    return actionFailure(error);
  }
}
