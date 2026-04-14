import DashboardShell, {
  type AdminReviewItem,
} from '../../../components/admin/dashboard-shell';
import {
  type AdminFeaturedMajor,
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

export default async function AdminPage() {
  let queueItems: AdminReviewItem[] = [];
  let queueError: string | undefined;
  let featuredSchools: AdminFeaturedSchool[] = [];
  let featuredMajors: AdminFeaturedMajor[] = [];
  let featuredSchoolPreview: AdminFeaturedPreviewItem[] = [];
  let featuredMajorPreview: AdminFeaturedPreviewItem[] = [];
  let featuredContentError: string | undefined;
  let schoolRotation = defaultRotationRule();
  let majorRotation = defaultRotationRule();

  try {
    queueItems = await listReviewQueue();
  } catch {
    queueError = '审核队列加载失败，请稍后重试';
  }

  try {
    const featuredContent = await listFeaturedContent();
    featuredSchools = featuredContent.schools;
    featuredMajors = featuredContent.majors;
    schoolRotation = featuredContent.rotation.schools;
    majorRotation = featuredContent.rotation.majors;
    featuredSchoolPreview = featuredContent.preview.schools;
    featuredMajorPreview = featuredContent.preview.majors;
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
