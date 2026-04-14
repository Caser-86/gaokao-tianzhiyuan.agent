import DashboardShell, {
  type AdminReviewItem,
} from '../../../components/admin/dashboard-shell';
import {
  type AdminFeaturedMajor,
  type AdminFeaturedPreviewDay,
  type AdminFeaturedPreviewItem,
  type AdminFeaturedSchool,
  type AdminRotationRule,
  listFeaturedContent,
} from '../../../lib/admin-featured-content-api';
import { listReviewQueue } from '../../../lib/admin-review-api';

import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
  updateFeaturedMajorAction,
  updateFeaturedSchoolAction,
  updateMajorRotationAction,
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

export default async function AdminPage({ searchParams }: AdminPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const previewDate = resolvedSearchParams?.preview_date?.trim() || undefined;
  const normalizedPreviewDate = previewDate ? shiftIsoDate(previewDate, 0) : null;
  const todayPreviewDate = todayIsoDate();
  const previousPreviewDate = previewDate ? shiftIsoDate(previewDate, -1) : null;
  const nextPreviewDate = previewDate ? shiftIsoDate(previewDate, 1) : null;
  const todayPreviewDateHref =
    normalizedPreviewDate && normalizedPreviewDate !== todayPreviewDate
      ? `/admin?preview_date=${todayPreviewDate}`
      : undefined;
  const previousPreviewDateHref = previousPreviewDate
    ? `/admin?preview_date=${previousPreviewDate}`
    : undefined;
  const nextPreviewDateHref = nextPreviewDate
    ? `/admin?preview_date=${nextPreviewDate}`
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
      selectedPreviewDateValue={previewDate ?? ''}
      selectedDatePreview={selectedDatePreview}
      selectedDateError={selectedDateError}
      todayPreviewDateHref={todayPreviewDateHref}
      previousPreviewDateHref={previousPreviewDateHref}
      nextPreviewDateHref={nextPreviewDateHref}
      queueError={queueError}
      featuredContentError={featuredContentError}
      approveAction={approveReviewQueueAction}
      rejectAction={rejectReviewQueueAction}
      updateFeaturedSchoolAction={updateFeaturedSchoolAction}
      updateFeaturedMajorAction={updateFeaturedMajorAction}
      updateSchoolRotationAction={updateSchoolRotationAction}
      updateMajorRotationAction={updateMajorRotationAction}
    />
  );
}
