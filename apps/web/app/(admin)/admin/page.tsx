import DashboardShell from '../../../components/admin/dashboard-shell';
import { listReviewQueue } from '../../../lib/admin-review-api';

import {
  approveReviewQueueAction,
  rejectReviewQueueAction,
} from './actions';

export default async function AdminPage() {
  try {
    const queueItems = await listReviewQueue();

    return (
      <DashboardShell
        title="内容运营后台"
        queueItems={queueItems}
        approveAction={approveReviewQueueAction}
        rejectAction={rejectReviewQueueAction}
      />
    );
  } catch {
    return (
      <DashboardShell
        title="内容运营后台"
        queueItems={[]}
        queueError="审核队列加载失败，请稍后重试"
        approveAction={approveReviewQueueAction}
        rejectAction={rejectReviewQueueAction}
      />
    );
  }
}
