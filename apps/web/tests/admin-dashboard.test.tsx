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
  const missingImageRegion = screen.getByRole('region', { name: '待补图片学校（1）' });
  const scheduleRegion = screen.getByRole('region', { name: '未来 7 天轮换预览' });
  const highlightedScheduleDay = within(scheduleRegion)
    .getByRole('heading', { name: '2026-04-15' })
    .closest('article');

  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('待审核内容')).toBeInTheDocument();
  expect(screen.getByText('school #101')).toBeInTheDocument();
  expect(screen.getByText('summary, strengths')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByText('已配置图片 1 所，待补图片 1 所')).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: '东南大学' })).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: '华西医学中心' })).toBeInTheDocument();
  expect(
    within(featuredSchoolsRegion)
      .getAllByRole('checkbox')
      .map((checkbox) => checkbox.parentElement?.textContent?.trim()),
  ).toEqual(['华西医学中心', '东南大学']);
  expect(
    screen.getByRole('img', { name: 'featured-school-image-southeast-university' }),
  ).toHaveAttribute('src', 'https://cdn.example.com/southeast.jpg');
  expect(screen.getByRole('link', { name: '查看原图' })).toHaveAttribute(
    'href',
    'https://cdn.example.com/southeast.jpg',
  );
  expect(screen.getByRole('button', { name: '清空图片' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '待补图片学校（1）' })).toBeInTheDocument();
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
  expect(screen.getByText('已配置图片 0 所，待补图片 0 所')).toBeInTheDocument();
  expect(screen.getByText('当前没有可展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有可展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有待补图片学校')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '待补图片学校（0）' })).toBeInTheDocument();
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

test('renders content gap overview shortcuts for high-priority missing content', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: 'Southeast University',
          isFeatured: true,
          heroImageUrl: '',
        },
        {
          slug: 'wuhan-university',
          name: 'Wuhan University',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
          isFeatured: true,
        },
        {
          slug: 'software-engineering',
          name: 'Software Engineering',
          isFeatured: true,
        },
      ]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[
        {
          slug: 'southeast-university',
          name: 'Southeast University',
        },
      ]}
      featuredMajorPreview={[
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
        },
      ]}
      nextFeaturedSchoolPreview={[
        {
          slug: 'wuhan-university',
          name: 'Wuhan University',
        },
      ]}
      nextFeaturedMajorPreview={[
        {
          slug: 'software-engineering',
          name: 'Software Engineering',
        },
      ]}
      featuredSchedule={[]}
      showScheduledMissingImageSchoolsOnlyHref="/admin?scheduled_missing_school_images=1"
      showScheduledMissingSchoolRankingsOnlyHref="/admin?scheduled_missing_school_rankings=1"
      showScheduledMissingMajorRankingsOnlyHref="/admin?scheduled_missing_major_rankings=1"
      showScheduledMissingSchoolSummariesOnlyHref="/admin?scheduled_missing_school_summaries=1"
      showScheduledMissingMajorSummariesOnlyHref="/admin?scheduled_missing_major_summaries=1"
      showScheduledMissingSchoolSectionsOnlyHref="/admin?scheduled_missing_school_sections=1"
      showScheduledMissingMajorSectionsOnlyHref="/admin?scheduled_missing_major_sections=1"
      showScheduledMissingSchoolRelatedOnlyHref="/admin?scheduled_missing_school_related=1"
      showScheduledMissingMajorRelatedOnlyHref="/admin?scheduled_missing_major_related=1"
      summarySchools={[
        { slug: 'southeast-university', name: 'Southeast University', summary: '' },
      ]}
      summaryMajors={[
        { slug: 'clinical-medicine', name: 'Clinical Medicine', summary: '' },
      ]}
      sectionSchools={[
        { slug: 'wuhan-university', name: 'Wuhan University', sections: [] },
      ]}
      sectionMajors={[
        { slug: 'software-engineering', name: 'Software Engineering', sections: [] },
      ]}
      relatedSchools={[
        { slug: 'southeast-university', name: 'Southeast University', relatedMajors: [] },
      ]}
      relatedMajors={[
        { slug: 'clinical-medicine', name: 'Clinical Medicine', relatedSchools: [] },
      ]}
      rankingReferenceSchools={[
        { slug: 'wuhan-university', name: 'Wuhan University', rankingReferences: [] },
      ]}
      rankingReferenceMajors={[
        { slug: 'software-engineering', name: 'Software Engineering', rankingReferences: [] },
      ]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const overviewRegion = screen.getByRole('region', { name: '内容缺口总览' });

  expect(
    within(overviewRegion).getByText('今日待补 5 项，下一轮待补 5 项，总待补 10 项'),
  ).toBeInTheDocument();
  const overviewLinks = within(overviewRegion).getAllByRole('link');

  expect(overviewLinks.map((link) => link.textContent)).toEqual([
    '今日优先 · 学校图片：今日 1，下一轮 1，待补 2',
    '今日优先 · 学校摘要：今日 1，下一轮 0，待补 1',
    '今日优先 · 专业摘要：今日 1，下一轮 0，待补 1',
    '今日优先 · 学校相关推荐：今日 1，下一轮 0，待补 1',
    '今日优先 · 专业相关推荐：今日 1，下一轮 0，待补 1',
    '下一轮关注 · 学校榜单：今日 0，下一轮 1，待补 1',
    '下一轮关注 · 专业榜单：今日 0，下一轮 1，待补 1',
    '下一轮关注 · 学校正文：今日 0，下一轮 1，待补 1',
    '下一轮关注 · 专业正文：今日 0，下一轮 1，待补 1',
  ]);
  expect(overviewLinks[0]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_school_images=1#missing-school-images-heading',
  );
  expect(overviewLinks[1]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_school_summaries=1#missing-school-summary-heading',
  );
  expect(overviewLinks[2]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_major_summaries=1#missing-major-summary-heading',
  );
  expect(overviewLinks[3]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_school_related=1#missing-school-related-content-heading',
  );
  expect(overviewLinks[4]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_major_related=1#missing-major-related-content-heading',
  );
  expect(overviewLinks[5]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_school_rankings=1#missing-school-ranking-reference-heading',
  );
  expect(overviewLinks[6]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_major_rankings=1#missing-major-ranking-reference-heading',
  );
  expect(overviewLinks[7]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_school_sections=1#missing-school-sections-heading',
  );
  expect(overviewLinks[8]).toHaveAttribute(
    'href',
    '/admin?scheduled_missing_major_sections=1#missing-major-sections-heading',
  );
});

test('renders selected-date gap overview when a preview date is selected', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: 'Southeast University',
          isFeatured: true,
          heroImageUrl: '',
        },
        {
          slug: 'wuhan-university',
          name: 'Wuhan University',
          isFeatured: true,
          heroImageUrl: 'https://cdn.example.com/wuhan.jpg',
        },
      ]}
      featuredMajors={[
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
          isFeatured: true,
        },
        {
          slug: 'software-engineering',
          name: 'Software Engineering',
          isFeatured: true,
        },
      ]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={schoolPreview}
      featuredMajorPreview={majorPreview}
      nextFeaturedSchoolPreview={nextSchoolPreview}
      nextFeaturedMajorPreview={nextMajorPreview}
      featuredSchedule={[]}
      selectedPreviewDateValue="2026-04-15"
      selectedDatePreview={{
        date: '2026-04-15',
        weekday: '周三',
        schools: [{ slug: 'southeast-university', name: 'Southeast University' }],
        majors: [{ slug: 'software-engineering', name: 'Software Engineering' }],
      }}
      summarySchools={[
        { slug: 'southeast-university', name: 'Southeast University', summary: '' },
      ]}
      summaryMajors={[
        { slug: 'software-engineering', name: 'Software Engineering', summary: '' },
      ]}
      sectionSchools={[
        { slug: 'southeast-university', name: 'Southeast University', sections: [] },
      ]}
      sectionMajors={[
        { slug: 'software-engineering', name: 'Software Engineering', sections: [] },
      ]}
      relatedSchools={[
        { slug: 'southeast-university', name: 'Southeast University', relatedMajors: [] },
      ]}
      relatedMajors={[
        { slug: 'software-engineering', name: 'Software Engineering', relatedSchools: [] },
      ]}
      rankingReferenceSchools={[
        { slug: 'southeast-university', name: 'Southeast University', rankingReferences: [] },
      ]}
      rankingReferenceMajors={[
        { slug: 'software-engineering', name: 'Software Engineering', rankingReferences: [] },
      ]}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const selectedGapRegion = screen.getByRole('region', { name: '该日缺口优先' });

  expect(
    within(selectedGapRegion).getByText('该日待补 9 项，下一轮待补 0 项，总待补 9 项'),
  ).toBeInTheDocument();
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 学校图片：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-school-images-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 学校榜单：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-school-ranking-reference-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 专业榜单：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-major-ranking-reference-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 学校摘要：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-school-summary-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 专业摘要：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-major-summary-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 学校正文：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-school-sections-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 专业正文：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-major-sections-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 学校相关推荐：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-school-related-content-heading');
  expect(
    within(selectedGapRegion).getByRole('link', { name: '该日优先 · 专业相关推荐：该日 1，下一轮 0，待补 1' }),
  ).toHaveAttribute('href', '#missing-major-related-content-heading');
});

test('renders content gap totals for each scheduled preview day', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: 'Southeast University',
          isFeatured: true,
          heroImageUrl: '',
        },
        {
          slug: 'wuhan-university',
          name: 'Wuhan University',
          isFeatured: true,
          heroImageUrl: 'https://cdn.example.com/wuhan.jpg',
        },
      ]}
      featuredMajors={[
        {
          slug: 'clinical-medicine',
          name: 'Clinical Medicine',
          isFeatured: true,
        },
        {
          slug: 'software-engineering',
          name: 'Software Engineering',
          isFeatured: true,
        },
      ]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={schoolPreview}
      featuredMajorPreview={majorPreview}
      nextFeaturedSchoolPreview={nextSchoolPreview}
      nextFeaturedMajorPreview={nextMajorPreview}
      featuredSchedule={[
        {
          date: '2026-04-14',
          weekday: '周二',
          schools: [{ slug: 'southeast-university', name: 'Southeast University' }],
          majors: [{ slug: 'clinical-medicine', name: 'Clinical Medicine' }],
        },
        {
          date: '2026-04-15',
          weekday: '周三',
          schools: [{ slug: 'wuhan-university', name: 'Wuhan University' }],
          majors: [{ slug: 'software-engineering', name: 'Software Engineering' }],
        },
      ]}
      summaryMajors={[{ slug: 'clinical-medicine', name: 'Clinical Medicine', summary: '' }]}
      sectionMajors={[{ slug: 'software-engineering', name: 'Software Engineering', sections: [] }]}
      rankingReferenceSchools={[{ slug: 'wuhan-university', name: 'Wuhan University', rankingReferences: [] }]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  const scheduleRegion = screen.getByRole('region', { name: '未来 7 天轮换预览' });
  const firstDayArticle = within(scheduleRegion)
    .getByRole('heading', { name: '2026-04-14' })
    .closest('article');
  const secondDayArticle = within(scheduleRegion)
    .getByRole('heading', { name: '2026-04-15' })
    .closest('article');

  expect(firstDayArticle).not.toBeNull();
  expect(secondDayArticle).not.toBeNull();
  expect(within(firstDayArticle as HTMLElement).getByText('该日待补 2 项')).toBeInTheDocument();
  expect(within(secondDayArticle as HTMLElement).getByText('该日待补 2 项')).toBeInTheDocument();
});
