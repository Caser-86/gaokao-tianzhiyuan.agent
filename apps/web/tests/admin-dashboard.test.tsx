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
  date: '2026-04-15',
  weekday: '周三',
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

test('renders admin dashboard heading, missing-image shortcuts, and schedule highlight', () => {
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
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
          isFeatured: true,
          heroImageUrl: '',
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
      selectedPreviewDateValue="2026-04-15"
      selectedDatePreview={selectedDatePreview}
      selectedDateError={undefined}
      todayPreviewDateHref="/admin?preview_date=2026-04-14"
      previousPreviewDateHref="/admin?preview_date=2026-04-14"
      nextPreviewDateHref="/admin?preview_date=2026-04-16"
      highlightedScheduleDate="2026-04-15"
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const schoolPreviewRegion = screen.getByRole('region', { name: '今日展示学校' });
  const majorPreviewRegion = screen.getByRole('region', { name: '今日展示专业' });
  const nextSchoolPreviewRegion = screen.getByRole('region', { name: '下一轮展示学校' });
  const nextMajorPreviewRegion = screen.getByRole('region', { name: '下一轮展示专业' });
  const selectedSchoolPreviewRegion = screen.getByRole('region', { name: '该日展示学校' });
  const selectedMajorPreviewRegion = screen.getByRole('region', { name: '该日展示专业' });
  const featuredSchoolsRegion = screen.getByRole('region', { name: '学校展示配置' });
  const missingImageRegion = screen.getByRole('region', { name: '待补图片学校' });
  const scheduleRegion = screen.getByRole('region', { name: '未来 7 天轮换预览' });
  const highlightedScheduleDay = within(scheduleRegion)
    .getByRole('heading', { name: '2026-04-15' })
    .closest('article');

  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('待审核内容')).toBeInTheDocument();
  expect(screen.getByText('school #101')).toBeInTheDocument();
  expect(screen.getByText('summary, strengths')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: '东南大学' })).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: '华西医学中心' })).toBeInTheDocument();
  expect(
    screen.getByRole('img', { name: 'featured-school-image-southeast-university' }),
  ).toHaveAttribute('src', 'https://cdn.example.com/southeast.jpg');
  expect(screen.getByRole('link', { name: '查看原图' })).toHaveAttribute(
    'href',
    'https://cdn.example.com/southeast.jpg',
  );
  expect(screen.getByRole('button', { name: '清空图片' })).toBeInTheDocument();
  expect(within(featuredSchoolsRegion).getByText('west-china-medical-center')).toBeInTheDocument();
  expect(within(missingImageRegion).getByText('west-china-medical-center')).toBeInTheDocument();
  expect(within(missingImageRegion).getByRole('link', { name: '华西医学中心' })).toHaveAttribute(
    'href',
    '#featured-school-west-china-medical-center',
  );
  expect(screen.getByRole('heading', { name: '专业展示配置' })).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: '临床医学' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('学校轮换顺序')).toHaveValue(
    'southeast-university\nwest-china-medical-center',
  );
  expect(screen.getByRole('heading', { name: '专业轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('专业轮换顺序')).toHaveValue('clinical-medicine');
  expect(within(schoolPreviewRegion).getByText('东南大学')).toBeInTheDocument();
  expect(within(schoolPreviewRegion).getByText('southeast-university')).toBeInTheDocument();
  expect(within(schoolPreviewRegion).getByText('已配置图片')).toBeInTheDocument();
  expect(within(majorPreviewRegion).getByText('临床医学')).toBeInTheDocument();
  expect(within(majorPreviewRegion).getByText('clinical-medicine')).toBeInTheDocument();
  expect(within(nextSchoolPreviewRegion).getByText('华西医学中心')).toBeInTheDocument();
  expect(within(nextSchoolPreviewRegion).getByText('west-china-medical-center')).toBeInTheDocument();
  expect(within(nextSchoolPreviewRegion).getByText('未配置图片')).toBeInTheDocument();
  expect(within(nextMajorPreviewRegion).getByText('计算机科学与技术')).toBeInTheDocument();
  expect(within(nextMajorPreviewRegion).getByText('computer-science')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '指定日期预览' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('2026-04-15')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '查看前一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-14',
  );
  expect(screen.getByRole('link', { name: '回到今天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-14',
  );
  expect(screen.getByRole('link', { name: '查看后一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-16',
  );
  expect(within(selectedSchoolPreviewRegion).getByText('东南大学')).toBeInTheDocument();
  expect(within(selectedSchoolPreviewRegion).getByText('southeast-university')).toBeInTheDocument();
  expect(within(selectedSchoolPreviewRegion).getByText('已配置图片')).toBeInTheDocument();
  expect(within(selectedMajorPreviewRegion).getByText('临床医学')).toBeInTheDocument();
  expect(within(selectedMajorPreviewRegion).getByText('clinical-medicine')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '未来 7 天轮换预览' })).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('2026-04-14')).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('周二')).toBeInTheDocument();
  expect(within(scheduleRegion).getByRole('heading', { name: '2026-04-15' })).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('周三')).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('东南大学')).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('华西医学中心')).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('已配置图片')).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('未配置图片')).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('临床医学')).toBeInTheDocument();
  expect(within(scheduleRegion).getByText('计算机科学与技术')).toBeInTheDocument();
  expect(within(scheduleRegion).getByRole('link', { name: '2026-04-14' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-14',
  );
  expect(within(scheduleRegion).queryByRole('link', { name: '2026-04-15' })).not.toBeInTheDocument();
  expect(highlightedScheduleDay).not.toBeNull();
  expect(within(highlightedScheduleDay as HTMLElement).getByText('当前查看')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '通过' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '驳回' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '查看该日轮换' })).toBeInTheDocument();
});

test('renders helper text and highlights today when no selected preview date is provided', () => {
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
      featuredSchedule={sevenDaySchedule}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      selectedDateError={undefined}
      highlightedScheduleDate="2026-04-14"
      previousPreviewDateHref={undefined}
      todayPreviewDateHref={undefined}
      nextPreviewDateHref={undefined}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const renderedTodayScheduleDay = screen.getByText('2026-04-14').closest('article');

  expect(screen.getByText('选择一个日期查看当天轮换结果')).toBeInTheDocument();
  expect(renderedTodayScheduleDay).not.toBeNull();
  expect(screen.queryByRole('link', { name: '2026-04-14' })).not.toBeInTheDocument();
  expect(within(renderedTodayScheduleDay as HTMLElement).getByText('当前查看')).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '回到今天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看前一天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看后一天' })).not.toBeInTheDocument();
});

test('renders selected-date validation error and no schedule highlight when needed', () => {
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
      featuredSchedule={sevenDaySchedule}
      selectedPreviewDateValue="2026-99-99"
      selectedDatePreview={null}
      selectedDateError="预览日期格式无效"
      highlightedScheduleDate={undefined}
      previousPreviewDateHref={undefined}
      todayPreviewDateHref={undefined}
      nextPreviewDateHref={undefined}
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
  expect(screen.getByText('当前没有待补图片学校')).toBeInTheDocument();
  expect(screen.getByText('预览日期格式无效')).toBeInTheDocument();
  expect(screen.queryByText('当前查看')).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '回到今天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看前一天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看后一天' })).not.toBeInTheDocument();
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
      highlightedScheduleDate={undefined}
      previousPreviewDateHref={undefined}
      todayPreviewDateHref={undefined}
      nextPreviewDateHref={undefined}
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
  expect(screen.queryByText('当前查看')).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '回到今天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看前一天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看后一天' })).not.toBeInTheDocument();
});
