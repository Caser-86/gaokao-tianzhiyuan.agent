import DashboardShell, {
  type AdminReviewItem,
} from '../../../components/admin/dashboard-shell';
import {
  type AdminContentSummaryEntity,
  listContentSummaries,
} from '../../../lib/admin-content-summary-api';
import {
  type AdminContentSectionsEntity,
  listContentSections,
} from '../../../lib/admin-content-sections-api';
import {
  type AdminRelatedMajorEntity,
  type AdminRelatedSchoolEntity,
  listRelatedContent,
} from '../../../lib/admin-related-content-api';
import {
  type AdminFeaturedMajor,
  type AdminFeaturedPreviewDay,
  type AdminFeaturedPreviewItem,
  type AdminFeaturedSchool,
  type AdminRotationRule,
  listFeaturedContent,
} from '../../../lib/admin-featured-content-api';
import {
  type AdminRankingReferenceEntity,
  listRankingReferences,
} from '../../../lib/admin-ranking-reference-api';
import { listReviewQueue } from '../../../lib/admin-review-api';
import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
  updateFeaturedMajorAction,
  updateFeaturedSchoolAction,
  updateMajorSectionsAction,
  updateMajorRelatedContentAction,
  updateMajorSummaryAction,
  updateMajorRankingReferencesAction,
  updateMajorRotationAction,
  updateSchoolRelatedContentAction,
  updateSchoolSectionsAction,
  updateSchoolSummaryAction,
  updateSchoolRankingReferencesAction,
  updateSchoolRotationAction,
} from './actions';

const defaultRotationRule = (): AdminRotationRule => ({
  enabled: false,
  frequencyDays: 1,
  windowSize: 1,
  orderedSlugs: [],
});

type AdminPageProps = {
  searchParams?: Promise<{
    preview_date?: string;
    missing_school_images?: string;
    scheduled_missing_school_images?: string;
    missing_school_rankings?: string;
    missing_major_rankings?: string;
    missing_school_related?: string;
    missing_major_related?: string;
    scheduled_missing_school_related?: string;
    scheduled_missing_major_related?: string;
    missing_school_summaries?: string;
    missing_major_summaries?: string;
    scheduled_missing_school_summaries?: string;
    scheduled_missing_major_summaries?: string;
    missing_school_sections?: string;
    missing_major_sections?: string;
    scheduled_missing_school_sections?: string;
    scheduled_missing_major_sections?: string;
  }>;
};

const shiftIsoDate = (value: string, offsetDays: number): string | null => {
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  parsed.setUTCDate(parsed.getUTCDate() + offsetDays);
  return parsed.toISOString().slice(0, 10);
};

const todayIsoDate = (): string => new Date().toISOString().slice(0, 10);

const buildAdminHref = ({
  previewDate,
  showMissingImageSchoolsOnly,
  showScheduledMissingImageSchoolsOnly,
  showMissingSchoolRankingsOnly,
  showMissingMajorRankingsOnly,
  showMissingSchoolRelatedOnly,
  showMissingMajorRelatedOnly,
  showScheduledMissingSchoolRelatedOnly,
  showScheduledMissingMajorRelatedOnly,
  showMissingSchoolSummariesOnly,
  showMissingMajorSummariesOnly,
  showScheduledMissingSchoolSummariesOnly,
  showScheduledMissingMajorSummariesOnly,
  showMissingSchoolSectionsOnly,
  showMissingMajorSectionsOnly,
  showScheduledMissingSchoolSectionsOnly,
  showScheduledMissingMajorSectionsOnly,
}: {
  previewDate?: string;
  showMissingImageSchoolsOnly?: boolean;
  showScheduledMissingImageSchoolsOnly?: boolean;
  showMissingSchoolRankingsOnly?: boolean;
  showMissingMajorRankingsOnly?: boolean;
  showMissingSchoolRelatedOnly?: boolean;
  showMissingMajorRelatedOnly?: boolean;
  showScheduledMissingSchoolRelatedOnly?: boolean;
  showScheduledMissingMajorRelatedOnly?: boolean;
  showMissingSchoolSummariesOnly?: boolean;
  showMissingMajorSummariesOnly?: boolean;
  showScheduledMissingSchoolSummariesOnly?: boolean;
  showScheduledMissingMajorSummariesOnly?: boolean;
  showMissingSchoolSectionsOnly?: boolean;
  showMissingMajorSectionsOnly?: boolean;
  showScheduledMissingSchoolSectionsOnly?: boolean;
  showScheduledMissingMajorSectionsOnly?: boolean;
}): string => {
  const searchParams = new URLSearchParams();

  if (previewDate) {
    searchParams.set('preview_date', previewDate);
  }

  if (showMissingImageSchoolsOnly) {
    searchParams.set('missing_school_images', '1');
  }

  if (showScheduledMissingImageSchoolsOnly) {
    searchParams.set('scheduled_missing_school_images', '1');
  }

  if (showMissingSchoolRankingsOnly !== undefined) {
    searchParams.set('missing_school_rankings', showMissingSchoolRankingsOnly ? '1' : '0');
  }

  if (showMissingMajorRankingsOnly !== undefined) {
    searchParams.set('missing_major_rankings', showMissingMajorRankingsOnly ? '1' : '0');
  }

  if (showMissingSchoolRelatedOnly !== undefined) {
    searchParams.set('missing_school_related', showMissingSchoolRelatedOnly ? '1' : '0');
  }

  if (showMissingMajorRelatedOnly !== undefined) {
    searchParams.set('missing_major_related', showMissingMajorRelatedOnly ? '1' : '0');
  }

  if (showScheduledMissingSchoolRelatedOnly !== undefined) {
    searchParams.set(
      'scheduled_missing_school_related',
      showScheduledMissingSchoolRelatedOnly ? '1' : '0',
    );
  }

  if (showScheduledMissingMajorRelatedOnly !== undefined) {
    searchParams.set(
      'scheduled_missing_major_related',
      showScheduledMissingMajorRelatedOnly ? '1' : '0',
    );
  }

  if (showMissingSchoolSummariesOnly !== undefined) {
    searchParams.set('missing_school_summaries', showMissingSchoolSummariesOnly ? '1' : '0');
  }

  if (showMissingMajorSummariesOnly !== undefined) {
    searchParams.set('missing_major_summaries', showMissingMajorSummariesOnly ? '1' : '0');
  }

  if (showScheduledMissingSchoolSummariesOnly !== undefined) {
    searchParams.set(
      'scheduled_missing_school_summaries',
      showScheduledMissingSchoolSummariesOnly ? '1' : '0',
    );
  }

  if (showScheduledMissingMajorSummariesOnly !== undefined) {
    searchParams.set(
      'scheduled_missing_major_summaries',
      showScheduledMissingMajorSummariesOnly ? '1' : '0',
    );
  }

  if (showMissingSchoolSectionsOnly !== undefined) {
    searchParams.set('missing_school_sections', showMissingSchoolSectionsOnly ? '1' : '0');
  }

  if (showMissingMajorSectionsOnly !== undefined) {
    searchParams.set('missing_major_sections', showMissingMajorSectionsOnly ? '1' : '0');
  }

  if (showScheduledMissingSchoolSectionsOnly !== undefined) {
    searchParams.set(
      'scheduled_missing_school_sections',
      showScheduledMissingSchoolSectionsOnly ? '1' : '0',
    );
  }

  if (showScheduledMissingMajorSectionsOnly !== undefined) {
    searchParams.set(
      'scheduled_missing_major_sections',
      showScheduledMissingMajorSectionsOnly ? '1' : '0',
    );
  }

  const queryString = searchParams.toString();
  return queryString ? `/admin?${queryString}` : '/admin';
};

export default async function AdminPage({ searchParams }: AdminPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const previewDate = resolvedSearchParams?.preview_date?.trim() || undefined;
  const showMissingImageSchoolsOnly =
    resolvedSearchParams?.missing_school_images?.trim() === '1';
  const showScheduledMissingImageSchoolsOnly =
    resolvedSearchParams?.scheduled_missing_school_images?.trim() === '1';
  const showMissingSchoolRankingsOnly =
    resolvedSearchParams?.missing_school_rankings?.trim() === '1';
  const showMissingMajorRankingsOnly =
    resolvedSearchParams?.missing_major_rankings?.trim() === '1';
  const showMissingSchoolRelatedOnly =
    resolvedSearchParams?.missing_school_related?.trim() === '1';
  const showMissingMajorRelatedOnly =
    resolvedSearchParams?.missing_major_related?.trim() === '1';
  const showScheduledMissingSchoolRelatedOnly =
    resolvedSearchParams?.scheduled_missing_school_related?.trim() === '1';
  const showScheduledMissingMajorRelatedOnly =
    resolvedSearchParams?.scheduled_missing_major_related?.trim() === '1';
  const showMissingSchoolSummariesOnly =
    resolvedSearchParams?.missing_school_summaries?.trim() === '1';
  const showMissingMajorSummariesOnly =
    resolvedSearchParams?.missing_major_summaries?.trim() === '1';
  const showScheduledMissingSchoolSummariesOnly =
    resolvedSearchParams?.scheduled_missing_school_summaries?.trim() === '1';
  const showScheduledMissingMajorSummariesOnly =
    resolvedSearchParams?.scheduled_missing_major_summaries?.trim() === '1';
  const showMissingSchoolSectionsOnly =
    resolvedSearchParams?.missing_school_sections?.trim() === '1';
  const showMissingMajorSectionsOnly =
    resolvedSearchParams?.missing_major_sections?.trim() === '1';
  const showScheduledMissingSchoolSectionsOnly =
    resolvedSearchParams?.scheduled_missing_school_sections?.trim() === '1';
  const showScheduledMissingMajorSectionsOnly =
    resolvedSearchParams?.scheduled_missing_major_sections?.trim() === '1';
  const rankingSchoolFilterState =
    resolvedSearchParams?.missing_school_rankings !== undefined
      ? showMissingSchoolRankingsOnly
      : undefined;
  const rankingMajorFilterState =
    resolvedSearchParams?.missing_major_rankings !== undefined
      ? showMissingMajorRankingsOnly
      : undefined;
  const relatedSchoolFilterState =
    resolvedSearchParams?.missing_school_related !== undefined
      ? showMissingSchoolRelatedOnly
      : undefined;
  const relatedMajorFilterState =
    resolvedSearchParams?.missing_major_related !== undefined
      ? showMissingMajorRelatedOnly
      : undefined;
  const scheduledRelatedSchoolFilterState =
    resolvedSearchParams?.scheduled_missing_school_related !== undefined
      ? showScheduledMissingSchoolRelatedOnly
      : undefined;
  const scheduledRelatedMajorFilterState =
    resolvedSearchParams?.scheduled_missing_major_related !== undefined
      ? showScheduledMissingMajorRelatedOnly
      : undefined;
  const summarySchoolFilterState =
    resolvedSearchParams?.missing_school_summaries !== undefined
      ? showMissingSchoolSummariesOnly
      : undefined;
  const summaryMajorFilterState =
    resolvedSearchParams?.missing_major_summaries !== undefined
      ? showMissingMajorSummariesOnly
      : undefined;
  const scheduledSummarySchoolFilterState =
    resolvedSearchParams?.scheduled_missing_school_summaries !== undefined
      ? showScheduledMissingSchoolSummariesOnly
      : undefined;
  const scheduledSummaryMajorFilterState =
    resolvedSearchParams?.scheduled_missing_major_summaries !== undefined
      ? showScheduledMissingMajorSummariesOnly
      : undefined;
  const sectionSchoolFilterState =
    resolvedSearchParams?.missing_school_sections !== undefined
      ? showMissingSchoolSectionsOnly
      : undefined;
  const sectionMajorFilterState =
    resolvedSearchParams?.missing_major_sections !== undefined
      ? showMissingMajorSectionsOnly
      : undefined;
  const scheduledSectionSchoolFilterState =
    resolvedSearchParams?.scheduled_missing_school_sections !== undefined
      ? showScheduledMissingSchoolSectionsOnly
      : undefined;
  const scheduledSectionMajorFilterState =
    resolvedSearchParams?.scheduled_missing_major_sections !== undefined
      ? showScheduledMissingMajorSectionsOnly
      : undefined;
  const normalizedPreviewDate = previewDate ? shiftIsoDate(previewDate, 0) : null;
  const todayPreviewDate = todayIsoDate();
  const highlightedScheduleDate =
    normalizedPreviewDate ?? (!previewDate ? todayPreviewDate : undefined);
  const previousPreviewDate = previewDate ? shiftIsoDate(previewDate, -1) : null;
  const nextPreviewDate = previewDate ? shiftIsoDate(previewDate, 1) : null;
  const todayPreviewDateHref =
    normalizedPreviewDate && normalizedPreviewDate !== todayPreviewDate
      ? buildAdminHref({
          previewDate: todayPreviewDate,
          showMissingImageSchoolsOnly,
          showScheduledMissingImageSchoolsOnly,
          showMissingSchoolRankingsOnly: rankingSchoolFilterState,
          showMissingMajorRankingsOnly: rankingMajorFilterState,
          showMissingSchoolRelatedOnly: relatedSchoolFilterState,
          showMissingMajorRelatedOnly: relatedMajorFilterState,
          showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
          showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
          showMissingSchoolSummariesOnly: summarySchoolFilterState,
          showMissingMajorSummariesOnly: summaryMajorFilterState,
          showScheduledMissingSchoolSummariesOnly: scheduledSummarySchoolFilterState,
          showScheduledMissingMajorSummariesOnly: scheduledSummaryMajorFilterState,
          showMissingSchoolSectionsOnly: sectionSchoolFilterState,
          showMissingMajorSectionsOnly: sectionMajorFilterState,
          showScheduledMissingSchoolSectionsOnly: scheduledSectionSchoolFilterState,
          showScheduledMissingMajorSectionsOnly: scheduledSectionMajorFilterState,
        })
      : undefined;
  const previousPreviewDateHref = previousPreviewDate
    ? buildAdminHref({
        previewDate: previousPreviewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
        showMissingSchoolSummariesOnly: summarySchoolFilterState,
        showMissingMajorSummariesOnly: summaryMajorFilterState,
        showScheduledMissingSchoolSummariesOnly: scheduledSummarySchoolFilterState,
        showScheduledMissingMajorSummariesOnly: scheduledSummaryMajorFilterState,
        showMissingSchoolSectionsOnly: sectionSchoolFilterState,
        showMissingMajorSectionsOnly: sectionMajorFilterState,
        showScheduledMissingSchoolSectionsOnly: scheduledSectionSchoolFilterState,
        showScheduledMissingMajorSectionsOnly: scheduledSectionMajorFilterState,
      })
    : undefined;
  const nextPreviewDateHref = nextPreviewDate
    ? buildAdminHref({
        previewDate: nextPreviewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
        showMissingSchoolSummariesOnly: summarySchoolFilterState,
        showMissingMajorSummariesOnly: summaryMajorFilterState,
        showScheduledMissingSchoolSummariesOnly: scheduledSummarySchoolFilterState,
        showScheduledMissingMajorSummariesOnly: scheduledSummaryMajorFilterState,
        showMissingSchoolSectionsOnly: sectionSchoolFilterState,
        showMissingMajorSectionsOnly: sectionMajorFilterState,
        showScheduledMissingSchoolSectionsOnly: scheduledSectionSchoolFilterState,
        showScheduledMissingMajorSectionsOnly: scheduledSectionMajorFilterState,
      })
    : undefined;
  const showMissingImageSchoolsOnlyHref =
    !showMissingImageSchoolsOnly && !showScheduledMissingImageSchoolsOnly
      ? buildAdminHref({
          previewDate,
          showMissingImageSchoolsOnly: true,
          showMissingSchoolRankingsOnly: rankingSchoolFilterState,
          showMissingMajorRankingsOnly: rankingMajorFilterState,
          showMissingSchoolRelatedOnly: relatedSchoolFilterState,
          showMissingMajorRelatedOnly: relatedMajorFilterState,
          showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
          showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
        })
      : showScheduledMissingImageSchoolsOnly
        ? buildAdminHref({
            previewDate,
            showMissingImageSchoolsOnly: true,
            showMissingSchoolRankingsOnly: rankingSchoolFilterState,
            showMissingMajorRankingsOnly: rankingMajorFilterState,
            showMissingSchoolRelatedOnly: relatedSchoolFilterState,
            showMissingMajorRelatedOnly: relatedMajorFilterState,
            showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
            showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
          })
        : undefined;
  const showScheduledMissingImageSchoolsOnlyHref = !showScheduledMissingImageSchoolsOnly
    ? buildAdminHref({
        previewDate,
        showScheduledMissingImageSchoolsOnly: true,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showMissingSchoolRankingsOnlyHref = !showMissingSchoolRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: true,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showAllSchoolRankingReferencesHref = showMissingSchoolRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: false,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showMissingMajorRankingsOnlyHref = !showMissingMajorRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: true,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showAllMajorRankingReferencesHref = showMissingMajorRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: false,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
      })
    : undefined;
  const showMissingSchoolRelatedOnlyHref = !showMissingSchoolRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: true,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showAllSchoolRelatedContentHref = showMissingSchoolRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: false,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showMissingMajorRelatedOnlyHref = !showMissingMajorRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: true,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showAllMajorRelatedContentHref = showMissingMajorRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: false,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showScheduledMissingSchoolRelatedOnlyHref = !showScheduledMissingSchoolRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: true,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showAllScheduledSchoolRelatedContentHref = showScheduledMissingSchoolRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: false,
        showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
      })
    : undefined;
  const showScheduledMissingMajorRelatedOnlyHref = !showScheduledMissingMajorRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: true,
      })
    : undefined;
  const showAllScheduledMajorRelatedContentHref = showScheduledMissingMajorRelatedOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
        showMissingSchoolRelatedOnly: relatedSchoolFilterState,
        showMissingMajorRelatedOnly: relatedMajorFilterState,
        showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
        showScheduledMissingMajorRelatedOnly: false,
      })
    : undefined;
  const showScheduledMissingSchoolSummariesOnlyHref = !showScheduledMissingSchoolSummariesOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSummariesOnly: summarySchoolFilterState,
        showMissingMajorSummariesOnly: summaryMajorFilterState,
        showScheduledMissingSchoolSummariesOnly: true,
        showScheduledMissingMajorSummariesOnly: scheduledSummaryMajorFilterState,
      })
    : undefined;
  const showAllScheduledSchoolSummariesHref = showScheduledMissingSchoolSummariesOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSummariesOnly: summarySchoolFilterState,
        showMissingMajorSummariesOnly: summaryMajorFilterState,
        showScheduledMissingSchoolSummariesOnly: false,
        showScheduledMissingMajorSummariesOnly: scheduledSummaryMajorFilterState,
      })
    : undefined;
  const showScheduledMissingMajorSummariesOnlyHref = !showScheduledMissingMajorSummariesOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSummariesOnly: summarySchoolFilterState,
        showMissingMajorSummariesOnly: summaryMajorFilterState,
        showScheduledMissingSchoolSummariesOnly: scheduledSummarySchoolFilterState,
        showScheduledMissingMajorSummariesOnly: true,
      })
    : undefined;
  const showAllScheduledMajorSummariesHref = showScheduledMissingMajorSummariesOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSummariesOnly: summarySchoolFilterState,
        showMissingMajorSummariesOnly: summaryMajorFilterState,
        showScheduledMissingSchoolSummariesOnly: scheduledSummarySchoolFilterState,
        showScheduledMissingMajorSummariesOnly: false,
      })
    : undefined;
  const showScheduledMissingSchoolSectionsOnlyHref = !showScheduledMissingSchoolSectionsOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSectionsOnly: sectionSchoolFilterState,
        showMissingMajorSectionsOnly: sectionMajorFilterState,
        showScheduledMissingSchoolSectionsOnly: true,
        showScheduledMissingMajorSectionsOnly: scheduledSectionMajorFilterState,
      })
    : undefined;
  const showAllScheduledSchoolSectionsHref = showScheduledMissingSchoolSectionsOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSectionsOnly: sectionSchoolFilterState,
        showMissingMajorSectionsOnly: sectionMajorFilterState,
        showScheduledMissingSchoolSectionsOnly: false,
        showScheduledMissingMajorSectionsOnly: scheduledSectionMajorFilterState,
      })
    : undefined;
  const showScheduledMissingMajorSectionsOnlyHref = !showScheduledMissingMajorSectionsOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSectionsOnly: sectionSchoolFilterState,
        showMissingMajorSectionsOnly: sectionMajorFilterState,
        showScheduledMissingSchoolSectionsOnly: scheduledSectionSchoolFilterState,
        showScheduledMissingMajorSectionsOnly: true,
      })
    : undefined;
  const showAllScheduledMajorSectionsHref = showScheduledMissingMajorSectionsOnly
    ? buildAdminHref({
        previewDate,
        showMissingSchoolSectionsOnly: sectionSchoolFilterState,
        showMissingMajorSectionsOnly: sectionMajorFilterState,
        showScheduledMissingSchoolSectionsOnly: scheduledSectionSchoolFilterState,
        showScheduledMissingMajorSectionsOnly: false,
      })
    : undefined;
  const showAllFeaturedSchoolsHref =
    showMissingImageSchoolsOnly || showScheduledMissingImageSchoolsOnly
      ? buildAdminHref({
          previewDate,
          showMissingSchoolRankingsOnly: rankingSchoolFilterState,
          showMissingMajorRankingsOnly: rankingMajorFilterState,
          showMissingSchoolRelatedOnly: relatedSchoolFilterState,
          showMissingMajorRelatedOnly: relatedMajorFilterState,
          showScheduledMissingSchoolRelatedOnly: scheduledRelatedSchoolFilterState,
          showScheduledMissingMajorRelatedOnly: scheduledRelatedMajorFilterState,
        })
      : undefined;

  let queueItems: AdminReviewItem[] = [];
  let queueError: string | undefined;
  let featuredSchools: AdminFeaturedSchool[] = [];
  let featuredMajors: AdminFeaturedMajor[] = [];
  let featuredSchoolPreview: AdminFeaturedPreviewItem[] = [];
  let featuredMajorPreview: AdminFeaturedPreviewItem[] = [];
  let nextFeaturedSchoolPreview: AdminFeaturedPreviewItem[] = [];
  let nextFeaturedMajorPreview: AdminFeaturedPreviewItem[] = [];
  let featuredSchedule: AdminFeaturedPreviewDay[] = [];
  let selectedDatePreview: AdminFeaturedPreviewDay | null = null;
  let selectedDateError: string | undefined;
  let featuredContentError: string | undefined;
  let rankingReferenceSchools: AdminRankingReferenceEntity[] = [];
  let rankingReferenceMajors: AdminRankingReferenceEntity[] = [];
  let rankingReferenceError: string | undefined;
  let summarySchools: AdminContentSummaryEntity[] = [];
  let summaryMajors: AdminContentSummaryEntity[] = [];
  let contentSummaryError: string | undefined;
  let sectionSchools: AdminContentSectionsEntity[] = [];
  let sectionMajors: AdminContentSectionsEntity[] = [];
  let contentSectionError: string | undefined;
  let relatedSchools: AdminRelatedSchoolEntity[] = [];
  let relatedMajors: AdminRelatedMajorEntity[] = [];
  let relatedContentError: string | undefined;
  let schoolRotation = defaultRotationRule();
  let majorRotation = defaultRotationRule();

  try {
    queueItems = await listReviewQueue();
  } catch {
    queueError = '审核队列加载失败，请稍后重试';
  }

  try {
    const featuredContent = await listFeaturedContent(previewDate);
    featuredSchools = featuredContent.schools;
    featuredMajors = featuredContent.majors;
    schoolRotation = featuredContent.rotation.schools;
    majorRotation = featuredContent.rotation.majors;
    featuredSchoolPreview = featuredContent.preview.today.schools;
    featuredMajorPreview = featuredContent.preview.today.majors;
    nextFeaturedSchoolPreview = featuredContent.preview.next.schools;
    nextFeaturedMajorPreview = featuredContent.preview.next.majors;
    featuredSchedule = featuredContent.preview.schedule;
    selectedDatePreview = featuredContent.preview.selectedDate;
    selectedDateError = featuredContent.preview.selectedDateError ?? undefined;
  } catch {
    featuredContentError = '展示配置加载失败，请稍后重试';
  }

  try {
    const rankingReferences = await listRankingReferences();
    rankingReferenceSchools = rankingReferences.schools;
    rankingReferenceMajors = rankingReferences.majors;
  } catch {
    rankingReferenceError = '榜单引用加载失败，请稍后重试';
  }

  try {
    const contentSummaries = await listContentSummaries();
    summarySchools = contentSummaries.schools;
    summaryMajors = contentSummaries.majors;
  } catch {
    contentSummaryError = '摘要内容加载失败，请稍后重试';
  }

  try {
    const contentSections = await listContentSections();
    sectionSchools = contentSections.schools;
    sectionMajors = contentSections.majors;
  } catch {
    contentSectionError = '正文内容加载失败，请稍后重试';
  }

  try {
    const relatedContent = await listRelatedContent();
    relatedSchools = relatedContent.schools;
    relatedMajors = relatedContent.majors;
  } catch {
    relatedContentError = '相关推荐加载失败，请稍后重试';
  }

  return (
    <DashboardShell
      title="内容运营后台"
      queueItems={queueItems}
      featuredSchools={featuredSchools}
      featuredMajors={featuredMajors}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={featuredSchoolPreview}
      featuredMajorPreview={featuredMajorPreview}
      nextFeaturedSchoolPreview={nextFeaturedSchoolPreview}
      nextFeaturedMajorPreview={nextFeaturedMajorPreview}
      featuredSchedule={featuredSchedule}
      rankingReferenceSchools={rankingReferenceSchools}
      rankingReferenceMajors={rankingReferenceMajors}
      summarySchools={summarySchools}
      summaryMajors={summaryMajors}
      showScheduledMissingSchoolSummariesOnly={showScheduledMissingSchoolSummariesOnly}
      showScheduledMissingSchoolSummariesOnlyHref={showScheduledMissingSchoolSummariesOnlyHref}
      showAllScheduledSchoolSummariesHref={showAllScheduledSchoolSummariesHref}
      showScheduledMissingMajorSummariesOnly={showScheduledMissingMajorSummariesOnly}
      showScheduledMissingMajorSummariesOnlyHref={showScheduledMissingMajorSummariesOnlyHref}
      showAllScheduledMajorSummariesHref={showAllScheduledMajorSummariesHref}
      sectionSchools={sectionSchools}
      sectionMajors={sectionMajors}
      showScheduledMissingSchoolSectionsOnly={showScheduledMissingSchoolSectionsOnly}
      showScheduledMissingSchoolSectionsOnlyHref={showScheduledMissingSchoolSectionsOnlyHref}
      showAllScheduledSchoolSectionsHref={showAllScheduledSchoolSectionsHref}
      showScheduledMissingMajorSectionsOnly={showScheduledMissingMajorSectionsOnly}
      showScheduledMissingMajorSectionsOnlyHref={showScheduledMissingMajorSectionsOnlyHref}
      showAllScheduledMajorSectionsHref={showAllScheduledMajorSectionsHref}
      relatedSchools={relatedSchools}
      relatedMajors={relatedMajors}
      highlightedScheduleDate={highlightedScheduleDate}
      selectedPreviewDateValue={previewDate ?? ''}
      selectedDatePreview={selectedDatePreview}
      selectedDateError={selectedDateError}
      todayPreviewDateHref={todayPreviewDateHref}
      previousPreviewDateHref={previousPreviewDateHref}
      nextPreviewDateHref={nextPreviewDateHref}
      showMissingImageSchoolsOnly={showMissingImageSchoolsOnly}
      showMissingImageSchoolsOnlyHref={showMissingImageSchoolsOnlyHref}
      showScheduledMissingImageSchoolsOnly={showScheduledMissingImageSchoolsOnly}
      showScheduledMissingImageSchoolsOnlyHref={showScheduledMissingImageSchoolsOnlyHref}
      showAllFeaturedSchoolsHref={showAllFeaturedSchoolsHref}
      showMissingSchoolRankingsOnly={showMissingSchoolRankingsOnly}
      showMissingSchoolRankingsOnlyHref={showMissingSchoolRankingsOnlyHref}
      showAllSchoolRankingReferencesHref={showAllSchoolRankingReferencesHref}
      showMissingMajorRankingsOnly={showMissingMajorRankingsOnly}
      showMissingMajorRankingsOnlyHref={showMissingMajorRankingsOnlyHref}
      showAllMajorRankingReferencesHref={showAllMajorRankingReferencesHref}
      showMissingSchoolRelatedOnly={showMissingSchoolRelatedOnly}
      showMissingSchoolRelatedOnlyHref={showMissingSchoolRelatedOnlyHref}
      showAllSchoolRelatedContentHref={showAllSchoolRelatedContentHref}
      showMissingMajorRelatedOnly={showMissingMajorRelatedOnly}
      showMissingMajorRelatedOnlyHref={showMissingMajorRelatedOnlyHref}
      showAllMajorRelatedContentHref={showAllMajorRelatedContentHref}
      showScheduledMissingSchoolRelatedOnly={showScheduledMissingSchoolRelatedOnly}
      showScheduledMissingSchoolRelatedOnlyHref={showScheduledMissingSchoolRelatedOnlyHref}
      showAllScheduledSchoolRelatedContentHref={showAllScheduledSchoolRelatedContentHref}
      showScheduledMissingMajorRelatedOnly={showScheduledMissingMajorRelatedOnly}
      showScheduledMissingMajorRelatedOnlyHref={showScheduledMissingMajorRelatedOnlyHref}
      showAllScheduledMajorRelatedContentHref={showAllScheduledMajorRelatedContentHref}
      rankingReferenceError={rankingReferenceError}
      contentSummaryError={contentSummaryError}
      contentSectionError={contentSectionError}
      relatedContentError={relatedContentError}
      queueError={queueError}
      featuredContentError={featuredContentError}
      approveAction={approveReviewQueueAction}
      rejectAction={rejectReviewQueueAction}
      updateFeaturedSchoolAction={updateFeaturedSchoolAction}
      updateFeaturedMajorAction={updateFeaturedMajorAction}
      updateSchoolSummaryAction={updateSchoolSummaryAction}
      updateMajorSummaryAction={updateMajorSummaryAction}
      updateSchoolSectionsAction={updateSchoolSectionsAction}
      updateMajorSectionsAction={updateMajorSectionsAction}
      updateSchoolRelatedContentAction={updateSchoolRelatedContentAction}
      updateMajorRelatedContentAction={updateMajorRelatedContentAction}
      updateSchoolRankingReferencesAction={updateSchoolRankingReferencesAction}
      updateMajorRankingReferencesAction={updateMajorRankingReferencesAction}
      updateSchoolRotationAction={updateSchoolRotationAction}
      updateMajorRotationAction={updateMajorRotationAction}
    />
  );
}
