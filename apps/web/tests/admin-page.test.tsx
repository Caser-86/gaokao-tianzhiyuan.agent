import { render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

const {
  listReviewQueueMock,
  listMediaAnalysisEventsMock,
  listFeaturedContentMock,
  suggestFeaturedSchoolImageMock,
  listRankingReferencesMock,
  listContentSummariesMock,
  listContentSectionsMock,
  listRelatedContentMock,
  listSmartAnalysisSettingsMock,
  getSmartAnalysisUserMock,
} = vi.hoisted(() => ({
  listReviewQueueMock: vi.fn(),
  listMediaAnalysisEventsMock: vi.fn(),
  listFeaturedContentMock: vi.fn(),
  suggestFeaturedSchoolImageMock: vi.fn(),
  listRankingReferencesMock: vi.fn(),
  listContentSummariesMock: vi.fn(),
  listContentSectionsMock: vi.fn(),
  listRelatedContentMock: vi.fn(),
  listSmartAnalysisSettingsMock: vi.fn(),
  getSmartAnalysisUserMock: vi.fn(),
}));

vi.mock('../lib/admin-review-api', () => ({
  listReviewQueue: listReviewQueueMock,
}));

vi.mock('../lib/admin-media-analysis-api', () => ({
  listMediaAnalysisEvents: listMediaAnalysisEventsMock,
}));

vi.mock('../lib/admin-featured-content-api', () => ({
  listFeaturedContent: listFeaturedContentMock,
  suggestFeaturedSchoolImage: suggestFeaturedSchoolImageMock,
}));

vi.mock('../lib/admin-ranking-reference-api', () => ({
  listRankingReferences: listRankingReferencesMock,
}));

vi.mock('../lib/admin-content-summary-api', () => ({
  listContentSummaries: listContentSummariesMock,
}));

vi.mock('../lib/admin-content-sections-api', () => ({
  listContentSections: listContentSectionsMock,
}));

vi.mock('../lib/admin-related-content-api', () => ({
  listRelatedContent: listRelatedContentMock,
}));

vi.mock('../lib/admin-smart-analysis-api', () => ({
  getSmartAnalysisSettings: listSmartAnalysisSettingsMock,
  getSmartAnalysisUser: getSmartAnalysisUserMock,
}));

vi.mock('../app/(admin)/admin/actions', () => ({
  approveReviewQueueAction: async () => undefined,
  rejectReviewQueueAction: async () => undefined,
  retryMediaAnalysisEventAction: async () => undefined,
  updateFeaturedSchoolAction: async () => undefined,
  suggestSchoolImageAction: async () => undefined,
  updateFeaturedMajorAction: async () => undefined,
  updateSchoolSummaryAction: async () => undefined,
  updateMajorSummaryAction: async () => undefined,
  updateSchoolSectionsAction: async () => undefined,
  updateMajorSectionsAction: async () => undefined,
  updateSchoolRelatedContentAction: async () => undefined,
  updateMajorRelatedContentAction: async () => undefined,
  updateSchoolRankingReferencesAction: async () => undefined,
  updateMajorRankingReferencesAction: async () => undefined,
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
  updateSmartAnalysisModeAction: async () => undefined,
  updateSmartAnalysisUserAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-04-14T12:00:00Z'));
  listReviewQueueMock.mockReset();
  listMediaAnalysisEventsMock.mockReset();
  listFeaturedContentMock.mockReset();
  suggestFeaturedSchoolImageMock.mockReset();
  listRankingReferencesMock.mockReset();
  listContentSummariesMock.mockReset();
  listContentSectionsMock.mockReset();
  listRelatedContentMock.mockReset();
  listSmartAnalysisSettingsMock.mockReset();
  getSmartAnalysisUserMock.mockReset();
  listRankingReferencesMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listContentSummariesMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listContentSectionsMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listRelatedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
  });
  listSmartAnalysisSettingsMock.mockResolvedValue({
    mode: 'off',
  });
  listMediaAnalysisEventsMock.mockResolvedValue([]);
  getSmartAnalysisUserMock.mockResolvedValue({
    userId: '',
    entitlements: [],
  });
  suggestFeaturedSchoolImageMock.mockResolvedValue({
    slug: 'southeast-university',
    name: '东南大学',
    status: 'found',
    sourceUrl: 'https://www.seu.edu.cn/',
    suggestedImageUrl: 'https://www.seu.edu.cn/assets/hero.jpg',
    message: null,
  });
});

afterEach(() => {
  vi.useRealTimers();
});

test('renders smart analysis admin controls from admin api clients', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });
  listSmartAnalysisSettingsMock.mockResolvedValue({ mode: 'gated' });
  getSmartAnalysisUserMock.mockResolvedValue({
    userId: 'wx-openid-123',
    entitlements: [{ name: 'smart_analysis', enabled: true }],
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        smart_analysis_user_id: 'wx-openid-123',
      }),
    }),
  );

  expect(screen.getByRole('heading', { name: '智能分析权限运营' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('gated')).toBeInTheDocument();
  expect(screen.getByLabelText('用户 ID')).toHaveValue('wx-openid-123');
  expect(screen.getByText('当前已开通智能分析')).toBeInTheDocument();
});

test('builds a failed-only media analysis shortcut while preserving active admin filters', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });
  listMediaAnalysisEventsMock.mockResolvedValue([
    {
      id: 1,
      channel: 'wechat',
      source: 'wechat_official_account',
      userId: 'wx-openid-123',
      messageId: 'msg-1',
      mediaId: 'media-1',
      mediaType: 'image',
      provider: 'openai_compatible',
      status: 'success',
      summary: '识别到河南560分',
      renderedReply: '图片已进入分析',
      extractedFields: {},
      context: {
        pic_url: 'https://example.com/retry-image.png',
      },
      retryable: true,
      retryBlockReason: null,
      autoRoutedToChat: true,
      createdAt: '2026-04-15T09:00:00Z',
    },
    {
      id: 2,
      channel: 'wechat',
      source: 'admin_media_analysis_retry',
      userId: 'wx-openid-123',
      messageId: 'msg-2',
      mediaId: 'media-2',
      mediaType: 'image',
      provider: 'openai_compatible',
      status: 'failed',
      summary: '管理员手动重试失败，等待排查',
      renderedReply: '',
      extractedFields: {},
      context: {
        pic_url: 'https://example.com/retry-failed-image.png',
        failure_reason: '上游媒体分析请求失败：HTTP 429',
      },
      retryable: true,
      retryBlockReason: null,
      autoRoutedToChat: true,
      createdAt: '2026-04-15T09:05:00Z',
    },
    {
      id: 3,
      channel: 'wechat',
      source: 'wechat_official_account_video_media_analysis',
      userId: 'wx-openid-123',
      messageId: 'msg-3',
      mediaId: 'media-3',
      mediaType: 'video',
      provider: 'openai_compatible',
      status: 'failed',
      summary: 'video unsupported',
      renderedReply: '',
      extractedFields: {},
      context: {
        failure_reason: 'video unsupported',
      },
      retryable: false,
      retryBlockReason:
        '\u975e\u56fe\u7247\u5a92\u4f53\u8bb0\u5f55\u6682\u4e0d\u652f\u6301\u624b\u52a8\u91cd\u8bd5',
      autoRoutedToChat: false,
      createdAt: '2026-04-15T09:06:00Z',
    },
  ]);

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-15',
        scheduled_gap_days: '1',
        media_analysis_user_id: 'wx-openid-123',
        media_analysis_auto_routed: '1',
      }),
    }),
  );

  expect(listMediaAnalysisEventsMock).toHaveBeenCalledWith({
    limit: 10,
    status: undefined,
    userId: 'wx-openid-123',
    autoRoutedToChat: true,
  });
  expect(screen.getByLabelText('媒体用户 ID')).toHaveValue('wx-openid-123');
  expect(screen.getByLabelText('只看已自动进主分析')).toBeChecked();
  expect(screen.getByRole('link', { name: '只看失败记录（2）' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-15&scheduled_gap_days=1&media_analysis_status=failed&media_analysis_user_id=wx-openid-123&media_analysis_auto_routed=1',
  );
  expect(screen.getAllByRole('button', { name: '重试分析' })).toHaveLength(2);
  expect(
    screen.getByText('不可重试：非图片媒体记录暂不支持手动重试'),
  ).toBeInTheDocument();
});

test('preserves admin context when viewing failed-only media analysis records', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });
  listMediaAnalysisEventsMock.mockResolvedValue([
    {
      id: 2,
      channel: 'wechat',
      source: 'admin_media_analysis_retry',
      userId: 'wx-openid-123',
      messageId: 'msg-2',
      mediaId: 'media-2',
      mediaType: 'image',
      provider: 'openai_compatible',
      status: 'failed',
      summary: '管理员手动重试失败，等待排查',
      renderedReply: '',
      extractedFields: {},
      context: {
        pic_url: 'https://example.com/retry-failed-image.png',
        failure_reason: '上游媒体分析请求失败：HTTP 429',
      },
      autoRoutedToChat: true,
      createdAt: '2026-04-15T09:05:00Z',
    },
  ]);

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-15',
        scheduled_gap_days: '1',
        media_analysis_status: 'failed',
        media_analysis_user_id: 'wx-openid-123',
        media_analysis_auto_routed: '1',
      }),
    }),
  );

  expect(listMediaAnalysisEventsMock).toHaveBeenCalledWith({
    limit: 10,
    status: 'failed',
    userId: 'wx-openid-123',
    autoRoutedToChat: true,
  });
  expect(screen.getByDisplayValue('failed')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '查看全部媒体记录' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-15&scheduled_gap_days=1&media_analysis_user_id=wx-openid-123&media_analysis_auto_routed=1',
  );
});

test('renders queue items, date preview shortcuts, and schedule highlight returned by the admin api client', async () => {
  listReviewQueueMock.mockResolvedValue([
    {
      id: 31,
      entity_type: 'school',
      entity_id: 901,
      candidate_version: 3,
      diff_summary: ['summary'],
      priority: 'normal',
      review_status: 'pending_review',
      reviewed_by: null,
      reviewed_at: null,
      review_note: null,
      created_at: '2026-04-13T09:10:00Z',
    },
  ]);

  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '内容学校',
        isFeatured: true,
        heroImageUrl: 'https://cdn.example.com/southeast.jpg',
      },
      {
        slug: 'west-china-medical-center',
        name: '内容候补学校',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '内容专业',
        isFeatured: true,
      },
    ],
    rotation: {
      schools: {
        enabled: true,
        frequencyDays: 1,
        windowSize: 2,
        orderedSlugs: ['southeast-university', 'west-china-medical-center'],
      },
      majors: {
        enabled: false,
        frequencyDays: 3,
        windowSize: 4,
        orderedSlugs: ['clinical-medicine'],
      },
    },
    preview: {
      today: {
        schools: [
          {
            slug: 'southeast-university',
            name: '东南大学',
          },
        ],
        majors: [
          {
            slug: 'clinical-medicine',
            name: '临床医学',
          },
        ],
      },
      next: {
        schools: [
          {
            slug: 'west-china-medical-center',
            name: '华西医学中心',
          },
        ],
        majors: [
          {
            slug: 'computer-science',
            name: '计算机科学与技术',
          },
        ],
      },
      schedule: [
        {
          date: '2026-04-14',
          weekday: '周二',
          schools: [
            {
              slug: 'southeast-university',
              name: '东南大学',
            },
          ],
          majors: [
            {
              slug: 'clinical-medicine',
              name: '临床医学',
            },
          ],
        },
        {
          date: '2026-04-15',
          weekday: '周三',
          schools: [
            {
              slug: 'west-china-medical-center',
              name: '华西医学中心',
            },
          ],
          majors: [
            {
              slug: 'computer-science',
              name: '计算机科学与技术',
            },
          ],
        },
      ],
      selectedDate: {
        date: '2026-04-15',
        weekday: '周三',
        schools: [
          {
            slug: 'southeast-university',
            name: '东南大学',
          },
        ],
        majors: [
          {
            slug: 'clinical-medicine',
            name: '临床医学',
          },
        ],
      },
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-15',
      }),
    }),
  );

  expect(listFeaturedContentMock).toHaveBeenCalledWith('2026-04-15');
  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('school #901')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByText('已配置图片 1 所，待补图片 1 所')).toBeInTheDocument();

  const featuredSchoolsRegion = screen.getByRole('region', { name: '学校展示配置' });
  expect(screen.getByText('内容学校')).toBeInTheDocument();
  expect(within(featuredSchoolsRegion).getByText('内容候补学校')).toBeInTheDocument();
  expect(
    within(featuredSchoolsRegion)
      .getAllByRole('checkbox')
      .map((checkbox) => checkbox.parentElement?.textContent?.trim()),
  ).toEqual(['内容候补学校', '内容学校']);
  expect(screen.getByDisplayValue('https://cdn.example.com/southeast.jpg')).toBeInTheDocument();
  expect(
    screen.getByRole('img', { name: 'featured-school-image-southeast-university' }),
  ).toHaveAttribute('src', 'https://cdn.example.com/southeast.jpg');
  expect(screen.getByRole('link', { name: '查看原图' })).toHaveAttribute(
    'href',
    'https://cdn.example.com/southeast.jpg',
  );
  expect(screen.getByRole('button', { name: '清空图片' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '待补图片学校（1）' })).toBeInTheDocument();

  const missingImageRegion = screen.getByRole('region', { name: '待补图片学校（1）' });
  expect(within(missingImageRegion).getByText('内容候补学校')).toBeInTheDocument();
  expect(within(missingImageRegion).getByText('west-china-medical-center')).toBeInTheDocument();
  expect(within(missingImageRegion).getByRole('link', { name: '内容候补学校' })).toHaveAttribute(
    'href',
    '#featured-school-west-china-medical-center',
  );

  expect(screen.getByRole('heading', { name: '专业展示配置' })).toBeInTheDocument();
  expect(screen.getByText('内容专业')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '学校轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('学校轮换顺序')).toHaveValue(
    'southeast-university\nwest-china-medical-center',
  );
  expect(screen.getByRole('heading', { name: '专业轮换规则' })).toBeInTheDocument();
  expect(screen.getByLabelText('专业轮换顺序')).toHaveValue('clinical-medicine');
  expect(screen.getByRole('heading', { name: '今日展示学校' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '今日展示专业' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '下一轮展示学校' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '下一轮展示专业' })).toBeInTheDocument();
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

  const selectedSchoolPreview = screen.getByRole('region', { name: '该日展示学校' });
  const selectedMajorPreview = screen.getByRole('region', { name: '该日展示专业' });
  const scheduleRegion = screen.getByRole('region', { name: '未来 7 天轮换预览' });
  const selectedScheduleDay = within(scheduleRegion)
    .getByRole('heading', { name: '2026-04-15' })
    .closest('article');

  expect(within(selectedSchoolPreview).getByText('东南大学')).toBeInTheDocument();
  expect(within(selectedSchoolPreview).getByText('southeast-university')).toBeInTheDocument();
  expect(within(selectedSchoolPreview).getByText('已配置图片')).toBeInTheDocument();
  expect(within(selectedMajorPreview).getByText('临床医学')).toBeInTheDocument();
  expect(within(selectedMajorPreview).getByText('clinical-medicine')).toBeInTheDocument();
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
  expect(selectedScheduleDay).not.toBeNull();
  expect(within(selectedScheduleDay as HTMLElement).getByText('当前查看')).toBeInTheDocument();
});

test('passes school image suggestions into the admin shell', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        suggested_school_image_slug: 'southeast-university',
      }),
    }),
  );

  expect(suggestFeaturedSchoolImageMock).toHaveBeenCalledWith('southeast-university');
  expect(screen.getByAltText('东南大学候选图片')).toBeInTheDocument();
});

test('preserves suggested school image context across admin preview links', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: {
        date: '2026-04-20',
        weekday: '周一',
        schools: [],
        majors: [],
      },
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-20',
        suggested_school_image_slug: 'southeast-university',
        scheduled_gap_days: '1',
      }),
    }),
  );

  expect(screen.getByRole('link', { name: '查看前一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-19&scheduled_gap_days=1&suggested_school_image_slug=southeast-university',
  );
  expect(screen.getByRole('link', { name: '查看后一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-21&scheduled_gap_days=1&suggested_school_image_slug=southeast-university',
  );
  expect(screen.getByRole('link', { name: '查看全部日期' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-20&suggested_school_image_slug=southeast-university',
  );
  expect(screen.getByRole('link', { name: '清除候选图' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-20&scheduled_gap_days=1',
  );
});

test('renders selected-date validation error when preview_date is invalid', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: {
        schools: [],
        majors: [],
      },
      next: {
        schools: [],
        majors: [],
      },
      schedule: [
        {
          date: '2026-04-14',
          weekday: '周二',
          schools: [],
          majors: [],
        },
      ],
      selectedDate: null,
      selectedDateError: '预览日期格式无效',
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-99-99',
      }),
    }),
  );

  expect(listFeaturedContentMock).toHaveBeenCalledWith('2026-99-99');
  expect(screen.getByText('预览日期格式无效')).toBeInTheDocument();
  expect(screen.getByText('已配置图片 0 所，待补图片 0 所')).toBeInTheDocument();
  expect(screen.getByText('当前没有待补图片学校')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '待补图片学校（0）' })).toBeInTheDocument();
  expect(screen.queryByText('当前查看')).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '回到今天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看前一天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看后一天' })).not.toBeInTheDocument();
});

test('renders queue error while still highlighting today when no preview date is selected', async () => {
  listReviewQueueMock.mockRejectedValue(new Error('boom'));
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: {
        schools: [],
        majors: [],
      },
      next: {
        schools: [],
        majors: [],
      },
      schedule: [
        {
          date: '2026-04-14',
          weekday: '周二',
          schools: [],
          majors: [],
        },
      ],
      selectedDate: null,
      selectedDateError: null,
    },
  });

  render(await AdminPage({}));

  const todayScheduleDay = screen.getByText('2026-04-14').closest('article');

  expect(screen.getByText('审核队列加载失败，请稍后重试')).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '2026-04-14' })).not.toBeInTheDocument();
  expect(todayScheduleDay).not.toBeNull();
  expect(within(todayScheduleDay as HTMLElement).getByText('当前查看')).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '回到今天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看前一天' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看后一天' })).not.toBeInTheDocument();
});

test('renders empty preview states when today, next, and selected-date preview are empty', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: {
        schools: [],
        majors: [],
      },
      next: {
        schools: [],
        majors: [],
      },
      schedule: [],
      selectedDate: {
        date: '2026-04-20',
        weekday: '周一',
        schools: [],
        majors: [],
      },
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-20',
      }),
    }),
  );

  expect(screen.getByText('当前没有可展示学校')).toBeInTheDocument();
  expect(screen.getByText('已配置图片 0 所，待补图片 0 所')).toBeInTheDocument();
  expect(screen.getByText('当前没有可展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有下一轮展示专业')).toBeInTheDocument();
  expect(screen.getByText('当前没有未来轮换预览')).toBeInTheDocument();
  expect(screen.getByText('当前没有待补图片学校')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '待补图片学校（0）' })).toBeInTheDocument();
  expect(screen.getByText('该日没有展示学校')).toBeInTheDocument();
  expect(screen.getByText('该日没有展示专业')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '查看前一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-19',
  );
  expect(screen.getByRole('link', { name: '回到今天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-14',
  );
  expect(screen.getByRole('link', { name: '查看后一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-21',
  );
});

test('preserves scheduled-gap-day filter in admin preview navigation', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: true,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: ['southeast-university'],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      today: {
        schools: [],
        majors: [],
      },
      next: {
        schools: [],
        majors: [],
      },
      schedule: [
        {
          date: '2026-04-14',
          weekday: '周二',
          schools: [],
          majors: [],
        },
        {
          date: '2026-04-15',
          weekday: '周三',
          schools: [
            {
              slug: 'southeast-university',
              name: '东南大学',
            },
          ],
          majors: [],
        },
      ],
      selectedDate: null,
      selectedDateError: null,
    },
  });
  listContentSummariesMock.mockResolvedValue({
    schools: [{ slug: 'southeast-university', name: '东南大学', summary: '' }],
    majors: [],
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-15',
        scheduled_gap_days: '1',
      }),
    }),
  );

  const scheduleRegion = screen.getByRole('region', { name: '未来 7 天轮换预览' });

  expect(screen.getByRole('link', { name: '查看全部日期' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-15',
  );
  expect(screen.getByRole('link', { name: '查看前一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-14&scheduled_gap_days=1',
  );
  expect(screen.getByRole('link', { name: '查看后一天' })).toHaveAttribute(
    'href',
    '/admin?preview_date=2026-04-16&scheduled_gap_days=1',
  );
  expect(within(scheduleRegion).queryByRole('link', { name: '2026-04-14' })).not.toBeInTheDocument();
  expect(within(scheduleRegion).queryByText('内容已齐备')).not.toBeInTheDocument();
});
