import { render, screen } from '@testing-library/react';

import DashboardShell, {
  type AdminReviewItem,
} from '../components/admin/dashboard-shell';

const queueItems: AdminReviewItem[] = [
  {
    id: 11,
    entity_type: 'school',
    entity_id: 101,
    candidate_version: 2,
    diff_summary: ['summary', 'strengths'],
    priority: 'normal',
    review_status: 'pending_review',
    reviewed_by: null,
    reviewed_at: null,
    review_note: null,
    created_at: '2026-04-13T09:00:00Z',
  },
];

test('renders admin dashboard heading and review queue items', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={queueItems}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: '东南大学',
          isFeatured: true,
          heroImageUrl: 'https://cdn.example.com/southeast.jpg',
        },
      ]}
      featuredMajors={[
        {
          slug: 'clinical-medicine',
          name: '临床医学',
          isFeatured: true,
        },
      ]}
      approveAction={async () => {}}
      rejectAction={async () => {}}
      updateFeaturedSchoolAction={async () => {}}
      updateFeaturedMajorAction={async () => {}}
    />,
  );

  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('待审核内容')).toBeInTheDocument();
  expect(screen.getByText('school #101')).toBeInTheDocument();
  expect(screen.getByText('summary, strengths')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByText('东南大学')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业展示配置' })).toBeInTheDocument();
  expect(screen.getByText('临床医学')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '通过' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '驳回' })).toBeInTheDocument();
});

test('renders empty state when there are no pending items', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[]}
      featuredMajors={[]}
      approveAction={async () => {}}
      rejectAction={async () => {}}
      updateFeaturedSchoolAction={async () => {}}
      updateFeaturedMajorAction={async () => {}}
    />,
  );

  expect(screen.getByText('当前没有待审核内容')).toBeInTheDocument();
});

test('renders error state when queue loading fails', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[]}
      featuredMajors={[]}
      queueError="审核队列加载失败，请稍后重试"
      approveAction={async () => {}}
      rejectAction={async () => {}}
      updateFeaturedSchoolAction={async () => {}}
      updateFeaturedMajorAction={async () => {}}
    />,
  );

  expect(screen.getByText('审核队列加载失败，请稍后重试')).toBeInTheDocument();
});
