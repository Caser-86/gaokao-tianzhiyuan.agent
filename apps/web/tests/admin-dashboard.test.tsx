import { render, screen, within } from '@testing-library/react';

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

const schoolRotation = {
  enabled: true,
  frequencyDays: 1,
  windowSize: 2,
  orderedSlugs: ['southeast-university', 'west-china-medical-center'],
};

const majorRotation = {
  enabled: false,
  frequencyDays: 3,
  windowSize: 1,
  orderedSlugs: ['clinical-medicine'],
};

const schoolPreview = [
  {
    slug: 'southeast-university',
    name: '东南大学',
  },
];

const majorPreview = [
  {
    slug: 'clinical-medicine',
    name: '临床医学',
  },
];

const nextSchoolPreview = [
  {
    slug: 'west-china-medical-center',
    name: '华西医学中心',
  },
];

const nextMajorPreview = [
  {
    slug: 'computer-science',
    name: '计算机科学与技术',
  },
];

const selectedDatePreview = {
  date: '2026-04-20',
  weekday: '周一',
  schools: schoolPreview,
  majors: majorPreview,
};

const sevenDaySchedule = [
  {
    date: '2026-04-14',
    weekday: '周二',
    schools: schoolPreview,
    majors: majorPreview,
  },
  {
    date: '2026-04-15',
    weekday: '周三',
    schools: nextSchoolPreview,
    majors: nextMajorPreview,
  },
];

test('renders admin dashboard heading, selected-date preview, next preview, and review queue items', () => {
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
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={schoolPreview}
      featuredMajorPreview={majorPreview}
      nextFeaturedSchoolPreview={nextSchoolPreview}
      nextFeaturedMajorPreview={nextMajorPreview}
      featuredSchedule={sevenDaySchedule}
      selectedPreviewDateValue="2026-04-20"
      selectedDatePreview={selectedDatePreview}
      selectedDateError={undefined}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('待审核内容')).toBeInTheDocument();
  expect(screen.getByText('school #101')).toBeInTheDocument();
  expect(screen.getByText('summary, strengths')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: '东南大学' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业展示配置' })).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: '临床医学' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('学校轮换顺序')).toHaveValue(
    'southeast-university\nwest-china-medical-center',
  );
  expect(screen.getByRole('heading', { name: '专业轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('专业轮换顺序')).toHaveValue('clinical-medicine');

  const schoolPreviewRegion = screen.getByRole('region', { name: '今日展示学校' });
  const majorPreviewRegion = screen.getByRole('region', { name: '今日展示专业' });
  const nextSchoolPreviewRegion = screen.getByRole('region', { name: '下一轮展示学校' });
  const nextMajorPreviewRegion = screen.getByRole('region', { name: '下一轮展示专业' });
  const selectedSchoolPreviewRegion = screen.getByRole('region', { name: '该日展示学校' });
  const selectedMajorPreviewRegion = screen.getByRole('region', { name: '该日展示专业' });

  expect(within(schoolPreviewRegion).getByText('东南大学')).toBeInTheDocument();
  expect(within(schoolPreviewRegion).getByText('southeast-university')).toBeInTheDocument();
  expect(within(majorPreviewRegion).getByText('临床医学')).toBeInTheDocument();
  expect(within(majorPreviewRegion).getByText('clinical-medicine')).toBeInTheDocument();
  expect(within(nextSchoolPreviewRegion).getByText('华西医学中心')).toBeInTheDocument();
  expect(within(nextSchoolPreviewRegion).getByText('west-china-medical-center')).toBeInTheDocument();
  expect(within(nextMajorPreviewRegion).getByText('计算机科学与技术')).toBeInTheDocument();
  expect(within(nextMajorPreviewRegion).getByText('computer-science')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '指定日期预览' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('2026-04-20')).toBeInTheDocument();
  expect(within(selectedSchoolPreviewRegion).getByText('东南大学')).toBeInTheDocument();
  expect(within(selectedSchoolPreviewRegion).getByText('southeast-university')).toBeInTheDocument();
  expect(within(selectedMajorPreviewRegion).getByText('临床医学')).toBeInTheDocument();
  expect(within(selectedMajorPreviewRegion).getByText('clinical-medicine')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '未来 7 天轮换预览' })).toBeInTheDocument();
  expect(screen.getByText('2026-04-14')).toBeInTheDocument();
  expect(screen.getByText('周二')).toBeInTheDocument();
  expect(screen.getByText('2026-04-15')).toBeInTheDocument();
  expect(screen.getByText('周三')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '通过' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '驳回' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '查看该日轮换' })).toBeInTheDocument();
});

test('renders helper text when no selected preview date is provided', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      selectedDateError={undefined}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByText('选择一个日期查看当天轮换结果')).toBeInTheDocument();
});

test('renders selected-date validation error and empty state when needed', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue="2026-99-99"
      selectedDatePreview={null}
      selectedDateError="预览日期格式无效"
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByText('当前没有待审核内容')).toBeInTheDocument();
  expect(screen.getByText('当前没有可展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有可展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有未来轮换预览')).toBeInTheDocument();
  expect(screen.getByText('预览日期格式无效')).toBeInTheDocument();
});

test('renders error state when queue loading fails', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      selectedDateError={undefined}
      queueError="审核队列加载失败，请稍后重试"
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByText('审核队列加载失败，请稍后重试')).toBeInTheDocument();
});
