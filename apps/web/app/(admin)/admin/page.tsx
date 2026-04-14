import DashboardShell, {
  type AdminReviewItem,
} from '../../../components/admin/dashboard-shell';
import {
  type AdminContentSummaryEntity,
  listContentSummaries,
} from '../../../lib/admin-content-summary-api';
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
  updateMajorSummaryAction,
  updateMajorRankingReferencesAction,
  updateMajorRotationAction,
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
}: {
  previewDate?: string;
  showMissingImageSchoolsOnly?: boolean;
  showScheduledMissingImageSchoolsOnly?: boolean;
  showMissingSchoolRankingsOnly?: boolean;
  showMissingMajorRankingsOnly?: boolean;
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
  const rankingSchoolFilterState =
    resolvedSearchParams?.missing_school_rankings !== undefined
      ? showMissingSchoolRankingsOnly
      : undefined;
  const rankingMajorFilterState =
    resolvedSearchParams?.missing_major_rankings !== undefined
      ? showMissingMajorRankingsOnly
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
        })
      : undefined;
  const previousPreviewDateHref = previousPreviewDate
    ? buildAdminHref({
        previewDate: previousPreviewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
      })
    : undefined;
  const nextPreviewDateHref = nextPreviewDate
    ? buildAdminHref({
        previewDate: nextPreviewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
      })
    : undefined;
  const showMissingImageSchoolsOnlyHref =
    !showMissingImageSchoolsOnly && !showScheduledMissingImageSchoolsOnly
      ? buildAdminHref({
          previewDate,
          showMissingImageSchoolsOnly: true,
          showMissingSchoolRankingsOnly: rankingSchoolFilterState,
          showMissingMajorRankingsOnly: rankingMajorFilterState,
        })
      : showScheduledMissingImageSchoolsOnly
        ? buildAdminHref({
            previewDate,
            showMissingImageSchoolsOnly: true,
            showMissingSchoolRankingsOnly: rankingSchoolFilterState,
            showMissingMajorRankingsOnly: rankingMajorFilterState,
          })
        : undefined;
  const showScheduledMissingImageSchoolsOnlyHref = !showScheduledMissingImageSchoolsOnly
    ? buildAdminHref({
        previewDate,
        showScheduledMissingImageSchoolsOnly: true,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
      })
    : undefined;
  const showMissingSchoolRankingsOnlyHref = !showMissingSchoolRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: true,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
      })
    : undefined;
  const showAllSchoolRankingReferencesHref = showMissingSchoolRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: false,
        showMissingMajorRankingsOnly: rankingMajorFilterState,
      })
    : undefined;
  const showMissingMajorRankingsOnlyHref = !showMissingMajorRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: true,
      })
    : undefined;
  const showAllMajorRankingReferencesHref = showMissingMajorRankingsOnly
    ? buildAdminHref({
        previewDate,
        showMissingImageSchoolsOnly,
        showScheduledMissingImageSchoolsOnly,
        showMissingSchoolRankingsOnly: rankingSchoolFilterState,
        showMissingMajorRankingsOnly: false,
      })
    : undefined;
  const showAllFeaturedSchoolsHref =
    showMissingImageSchoolsOnly || showScheduledMissingImageSchoolsOnly
      ? buildAdminHref({
          previewDate,
          showMissingSchoolRankingsOnly: rankingSchoolFilterState,
          showMissingMajorRankingsOnly: rankingMajorFilterState,
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
      rankingReferenceError={rankingReferenceError}
      contentSummaryError={contentSummaryError}
      queueError={queueError}
      featuredContentError={featuredContentError}
      approveAction={approveReviewQueueAction}
      rejectAction={rejectReviewQueueAction}
      updateFeaturedSchoolAction={updateFeaturedSchoolAction}
      updateFeaturedMajorAction={updateFeaturedMajorAction}
      updateSchoolSummaryAction={updateSchoolSummaryAction}
      updateMajorSummaryAction={updateMajorSummaryAction}
      updateSchoolRankingReferencesAction={updateSchoolRankingReferencesAction}
      updateMajorRankingReferencesAction={updateMajorRankingReferencesAction}
      updateSchoolRotationAction={updateSchoolRotationAction}
      updateMajorRotationAction={updateMajorRotationAction}
    />
  );
}
