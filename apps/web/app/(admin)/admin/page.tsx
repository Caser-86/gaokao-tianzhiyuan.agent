import DashboardShell from '../../../components/admin/dashboard-shell';
import type { AdminReviewItem } from '../../../components/admin/dashboard-shell';
import {
  type AdminFeaturedMajor,
  type AdminFeaturedSchool,
  listFeaturedContent,
} from '../../../lib/admin-featured-content-api';
import { listReviewQueue } from '../../../lib/admin-review-api';

import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
  updateFeaturedMajorAction,
  updateFeaturedSchoolAction,
} from './actions';

export default async function AdminPage() {
  let queueItems: AdminReviewItem[] = [];
  let queueError: string | undefined;
  let featuredSchools: AdminFeaturedSchool[] = [];
  let featuredMajors: AdminFeaturedMajor[] = [];
  let featuredContentError: string | undefined;

  try {
    queueItems = await listReviewQueue();
  } catch {
    queueError = '审核队列加载失败，请稍后重试';
  }

  try {
    const featuredContent = await listFeaturedContent();
    featuredSchools = featuredContent.schools;
    featuredMajors = featuredContent.majors;
  } catch {
    featuredContentError = '展示配置加载失败，请稍后重试';
  }

  return (
    <DashboardShell
      title="内容运营后台"
      queueItems={queueItems}
      featuredSchools={featuredSchools}
      featuredMajors={featuredMajors}
      queueError={queueError}
      featuredContentError={featuredContentError}
      approveAction={approveReviewQueueAction}
      rejectAction={rejectReviewQueueAction}
      updateFeaturedSchoolAction={updateFeaturedSchoolAction}
      updateFeaturedMajorAction={updateFeaturedMajorAction}
    />
  );
}
