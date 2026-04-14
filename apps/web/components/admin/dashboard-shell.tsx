import type {
  AdminContentSummaryEntity,
} from '../../lib/admin-content-summary-api';
import type {
  AdminContentSection,
  AdminContentSectionsEntity,
} from '../../lib/admin-content-sections-api';
import type {
  AdminFeaturedMajor,
  AdminFeaturedPreviewDay,
  AdminFeaturedPreviewItem,
  AdminFeaturedSchool,
  AdminRotationRule,
} from '../../lib/admin-featured-content-api';
import type { AdminRankingReferenceEntity } from '../../lib/admin-ranking-reference-api';

export type AdminReviewItem = {
  id: number;
  entity_type: string;
  entity_id: number;
  candidate_version: number | null;
  diff_summary: string[];
  priority: string;
  review_status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  created_at: string;
};

type DashboardShellProps = {
  title: string;
  queueItems: AdminReviewItem[];
  featuredSchools: AdminFeaturedSchool[];
  featuredMajors: AdminFeaturedMajor[];
  schoolRotation: AdminRotationRule;
  majorRotation: AdminRotationRule;
  featuredSchoolPreview: AdminFeaturedPreviewItem[];
  featuredMajorPreview: AdminFeaturedPreviewItem[];
  nextFeaturedSchoolPreview: AdminFeaturedPreviewItem[];
  nextFeaturedMajorPreview: AdminFeaturedPreviewItem[];
  featuredSchedule: AdminFeaturedPreviewDay[];
  summarySchools?: AdminContentSummaryEntity[];
  summaryMajors?: AdminContentSummaryEntity[];
  sectionSchools?: AdminContentSectionsEntity[];
  sectionMajors?: AdminContentSectionsEntity[];
  rankingReferenceSchools?: AdminRankingReferenceEntity[];
  rankingReferenceMajors?: AdminRankingReferenceEntity[];
  highlightedScheduleDate?: string;
  selectedPreviewDateValue: string;
  selectedDatePreview: AdminFeaturedPreviewDay | null;
  selectedDateError?: string;
  todayPreviewDateHref?: string;
  previousPreviewDateHref?: string;
  nextPreviewDateHref?: string;
  showMissingImageSchoolsOnly?: boolean;
  showMissingImageSchoolsOnlyHref?: string;
  showScheduledMissingImageSchoolsOnly?: boolean;
  showScheduledMissingImageSchoolsOnlyHref?: string;
  showAllFeaturedSchoolsHref?: string;
  showMissingSchoolRankingsOnly?: boolean;
  showMissingSchoolRankingsOnlyHref?: string;
  showAllSchoolRankingReferencesHref?: string;
  showMissingMajorRankingsOnly?: boolean;
  showMissingMajorRankingsOnlyHref?: string;
  showAllMajorRankingReferencesHref?: string;
  rankingReferenceError?: string;
  contentSummaryError?: string;
  contentSectionError?: string;
  queueError?: string;
  featuredContentError?: string;
  approveAction: (formData: FormData) => Promise<void>;
  rejectAction: (formData: FormData) => Promise<void>;
  updateFeaturedSchoolAction: (formData: FormData) => Promise<void>;
  updateFeaturedMajorAction: (formData: FormData) => Promise<void>;
  updateSchoolSummaryAction?: (formData: FormData) => Promise<void>;
  updateMajorSummaryAction?: (formData: FormData) => Promise<void>;
  updateSchoolSectionsAction?: (formData: FormData) => Promise<void>;
  updateMajorSectionsAction?: (formData: FormData) => Promise<void>;
  updateSchoolRankingReferencesAction?: (formData: FormData) => Promise<void>;
  updateMajorRankingReferencesAction?: (formData: FormData) => Promise<void>;
  updateSchoolRotationAction: (formData: FormData) => Promise<void>;
  updateMajorRotationAction: (formData: FormData) => Promise<void>;
};

const cards = ['待审核内容', '最近发布', '抓取状态'];
const noopAction = async (): Promise<void> => undefined;

function PreviewList({
  items,
  imageAvailabilityBySlug,
}: {
  items: AdminFeaturedPreviewItem[];
  imageAvailabilityBySlug?: Record<string, boolean>;
}) {
  return (
    <ul>
      {items.map((item) => (
        <li key={item.slug}>
          {imageAvailabilityBySlug ? (
            <a href={`#featured-school-${item.slug}`}>{item.name}</a>
          ) : (
            <span>{item.name}</span>
          )}
          <span>{item.slug}</span>
          {imageAvailabilityBySlug ? (
            <span>{imageAvailabilityBySlug[item.slug] ? '已配置图片' : '未配置图片'}</span>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

function RankingReferenceForm({
  entity,
  entityLabel,
  action,
  submitLabel,
}: {
  entity: AdminRankingReferenceEntity;
  entityLabel: string;
  action: (formData: FormData) => Promise<void>;
  submitLabel: string;
}) {
  const rows = [
    ...entity.rankingReferences,
    {
      source: '',
      year: '',
      label: '',
      scope: '',
      note: '',
      url: '',
    },
  ];

  return (
    <form action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <input type="hidden" name="rowCount" value={rows.length} />
      <h3>{entity.name}</h3>
      <p>{entity.slug}</p>

      {rows.map((row, index) => (
        <fieldset key={`${entity.slug}-${index}`}>
          <legend>{`${entityLabel}榜单条目 ${index + 1}`}</legend>
          <label>
            来源
            <input name={`source_${index}`} defaultValue={row.source} />
          </label>
          <label>
            年份
            <input
              type="number"
              min={1}
              name={`year_${index}`}
              defaultValue={row.year === '' ? '' : row.year}
            />
          </label>
          <label>
            结果
            <input name={`label_${index}`} defaultValue={row.label} />
          </label>
          <label>
            范围
            <input name={`scope_${index}`} defaultValue={row.scope} />
          </label>
          <label>
            备注
            <input name={`note_${index}`} defaultValue={row.note} />
          </label>
          <label>
            来源链接
            <input name={`url_${index}`} defaultValue={row.url} />
          </label>
        </fieldset>
      ))}

      <button type="submit">{submitLabel}</button>
    </form>
  );
}

function ContentSummaryForm({
  entity,
  action,
}: {
  entity: AdminContentSummaryEntity;
  action: (formData: FormData) => Promise<void>;
}) {
  return (
    <form action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <h3>{entity.name}</h3>
      <p>{entity.slug}</p>
      <label>
        摘要
        <textarea name="summary" defaultValue={entity.summary} />
      </label>
      <button type="submit">保存摘要</button>
    </form>
  );
}

function ContentSectionsForm({
  entity,
  action,
}: {
  entity: AdminContentSectionsEntity;
  action: (formData: FormData) => Promise<void>;
}) {
  const rows: AdminContentSection[] = [
    ...entity.sections,
    {
      type: '',
      title: '',
      items: [],
    },
  ];

  return (
    <form action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <input type="hidden" name="rowCount" value={rows.length} />
      <h3>{entity.name}</h3>
      <p>{entity.slug}</p>
      {rows.map((row, index) => (
        <fieldset key={`${entity.slug}-section-${index}`}>
          <legend>{`正文模块 ${index + 1}`}</legend>
          <label>
            类型
            <input name={`section_type_${index}`} defaultValue={row.type} />
          </label>
          <label>
            标题
            <input name={`section_title_${index}`} defaultValue={row.title} />
          </label>
          <label>
            条目
            <textarea
              name={`section_items_${index}`}
              defaultValue={row.items.join('\n')}
            />
          </label>
        </fieldset>
      ))}
      <button type="submit">保存正文</button>
    </form>
  );
}

export default function DashboardShell({
  title,
  queueItems,
  featuredSchools,
  featuredMajors,
  schoolRotation,
  majorRotation,
  featuredSchoolPreview,
  featuredMajorPreview,
  nextFeaturedSchoolPreview,
  nextFeaturedMajorPreview,
  featuredSchedule,
  summarySchools = [],
  summaryMajors = [],
  sectionSchools = [],
  sectionMajors = [],
  rankingReferenceSchools = [],
  rankingReferenceMajors = [],
  highlightedScheduleDate,
  selectedPreviewDateValue,
  selectedDatePreview,
  selectedDateError,
  todayPreviewDateHref,
  previousPreviewDateHref,
  nextPreviewDateHref,
  showMissingImageSchoolsOnly = false,
  showMissingImageSchoolsOnlyHref,
  showScheduledMissingImageSchoolsOnly = false,
  showScheduledMissingImageSchoolsOnlyHref,
  showAllFeaturedSchoolsHref,
  showMissingSchoolRankingsOnly = false,
  showMissingSchoolRankingsOnlyHref,
  showAllSchoolRankingReferencesHref,
  showMissingMajorRankingsOnly = false,
  showMissingMajorRankingsOnlyHref,
  showAllMajorRankingReferencesHref,
  rankingReferenceError,
  contentSummaryError,
  contentSectionError,
  queueError,
  featuredContentError,
  approveAction,
  rejectAction,
  updateFeaturedSchoolAction,
  updateFeaturedMajorAction,
  updateSchoolSummaryAction = noopAction,
  updateMajorSummaryAction = noopAction,
  updateSchoolSectionsAction = noopAction,
  updateMajorSectionsAction = noopAction,
  updateSchoolRankingReferencesAction = noopAction,
  updateMajorRankingReferencesAction = noopAction,
  updateSchoolRotationAction,
  updateMajorRotationAction,
}: DashboardShellProps) {
  const showSelectedDateHelper =
    !selectedPreviewDateValue && !selectedDatePreview && !selectedDateError;
  const sortedFeaturedSchools = [...featuredSchools].sort((left, right) => {
    if (Boolean(left.heroImageUrl) === Boolean(right.heroImageUrl)) {
      return 0;
    }

    return left.heroImageUrl ? 1 : -1;
  });
  const schoolImageAvailabilityBySlug = Object.fromEntries(
    featuredSchools.map((school) => [school.slug, Boolean(school.heroImageUrl)]),
  );
  const todayPreviewSchoolSlugs = new Set(featuredSchoolPreview.map((school) => school.slug));
  const nextPreviewSchoolSlugs = new Set(nextFeaturedSchoolPreview.map((school) => school.slug));
  const scheduledMissingSchoolSlugs = new Set([
    ...featuredSchoolPreview.map((school) => school.slug),
    ...nextFeaturedSchoolPreview.map((school) => school.slug),
  ]);
  const schoolsMissingImages = sortedFeaturedSchools
    .filter((school) => !school.heroImageUrl)
    .map(({ slug, name }) => ({ slug, name }));
  const schoolsWithImagesCount = featuredSchools.length - schoolsMissingImages.length;
  const scheduledMissingImagesCount = schoolsMissingImages.filter((school) =>
    scheduledMissingSchoolSlugs.has(school.slug),
  ).length;
  const todayMissingImagesCount = schoolsMissingImages.filter((school) =>
    todayPreviewSchoolSlugs.has(school.slug),
  ).length;
  const nextMissingImagesCount = schoolsMissingImages.filter((school) =>
    nextPreviewSchoolSlugs.has(school.slug),
  ).length;
  const displayedFeaturedSchools = showScheduledMissingImageSchoolsOnly
    ? sortedFeaturedSchools.filter(
        (school) => !school.heroImageUrl && scheduledMissingSchoolSlugs.has(school.slug),
      )
    : showMissingImageSchoolsOnly
      ? sortedFeaturedSchools.filter((school) => !school.heroImageUrl)
      : sortedFeaturedSchools;
  const featuredSchoolSlugs = new Set(featuredSchools.map((school) => school.slug));
  const featuredMajorSlugs = new Set(featuredMajors.map((major) => major.slug));
  const sortRankingReferenceEntities = (entities: AdminRankingReferenceEntity[], featuredSlugs: Set<string>) =>
    [...entities].sort((left, right) => {
      const leftMissing = left.rankingReferences.length === 0 ? 0 : 1;
      const rightMissing = right.rankingReferences.length === 0 ? 0 : 1;
      if (leftMissing !== rightMissing) {
        return leftMissing - rightMissing;
      }

      const leftFeatured = featuredSlugs.has(left.slug) ? 0 : 1;
      const rightFeatured = featuredSlugs.has(right.slug) ? 0 : 1;
      if (leftFeatured !== rightFeatured) {
        return leftFeatured - rightFeatured;
      }

      return left.name.localeCompare(right.name, 'zh-CN');
    });
  const sortedRankingReferenceSchools = sortRankingReferenceEntities(
    rankingReferenceSchools,
    featuredSchoolSlugs,
  );
  const sortedRankingReferenceMajors = sortRankingReferenceEntities(
    rankingReferenceMajors,
    featuredMajorSlugs,
  );
  const missingSchoolRankingReferences = sortedRankingReferenceSchools.filter(
    (school) => school.rankingReferences.length === 0,
  );
  const missingMajorRankingReferences = sortedRankingReferenceMajors.filter(
    (major) => major.rankingReferences.length === 0,
  );
  const displayedSchoolRankingReferences = showMissingSchoolRankingsOnly
    ? missingSchoolRankingReferences
    : sortedRankingReferenceSchools;
  const displayedMajorRankingReferences = showMissingMajorRankingsOnly
    ? missingMajorRankingReferences
    : sortedRankingReferenceMajors;
  const configuredSchoolRankingReferenceCount =
    sortedRankingReferenceSchools.length - missingSchoolRankingReferences.length;
  const configuredMajorRankingReferenceCount =
    sortedRankingReferenceMajors.length - missingMajorRankingReferences.length;
  const todayMissingSchoolRankingCount = missingSchoolRankingReferences.filter((school) =>
    todayPreviewSchoolSlugs.has(school.slug),
  ).length;
  const nextMissingSchoolRankingCount = missingSchoolRankingReferences.filter((school) =>
    nextPreviewSchoolSlugs.has(school.slug),
  ).length;
  const todayPreviewMajorSlugs = new Set(featuredMajorPreview.map((major) => major.slug));
  const nextPreviewMajorSlugs = new Set(nextFeaturedMajorPreview.map((major) => major.slug));
  const todayMissingMajorRankingCount = missingMajorRankingReferences.filter((major) =>
    todayPreviewMajorSlugs.has(major.slug),
  ).length;
  const nextMissingMajorRankingCount = missingMajorRankingReferences.filter((major) =>
    nextPreviewMajorSlugs.has(major.slug),
  ).length;

  const schoolFilterLinks = (
    <p>
      {!showMissingImageSchoolsOnly &&
      !showScheduledMissingImageSchoolsOnly &&
      showMissingImageSchoolsOnlyHref ? (
        <a href={showMissingImageSchoolsOnlyHref}>{`仅看待补图片学校（${schoolsMissingImages.length}）`}</a>
      ) : null}
      {!showScheduledMissingImageSchoolsOnly && showScheduledMissingImageSchoolsOnlyHref ? (
        <>
          {!showMissingImageSchoolsOnly &&
          !showScheduledMissingImageSchoolsOnly &&
          showMissingImageSchoolsOnlyHref
            ? ' '
            : null}
          <a href={showScheduledMissingImageSchoolsOnlyHref}>{`仅看近期缺图学校（${scheduledMissingImagesCount}）`}</a>
        </>
      ) : null}
      {(showMissingImageSchoolsOnly || showScheduledMissingImageSchoolsOnly) &&
      showAllFeaturedSchoolsHref ? (
        <>
          {' '}
          <a href={showAllFeaturedSchoolsHref}>查看全部学校</a>
        </>
      ) : null}
      {showScheduledMissingImageSchoolsOnly && showMissingImageSchoolsOnlyHref ? (
        <>
          {' '}
          <a href={showMissingImageSchoolsOnlyHref}>{`仅看待补图片学校（${schoolsMissingImages.length}）`}</a>
        </>
      ) : null}
      {showMissingImageSchoolsOnly && showScheduledMissingImageSchoolsOnlyHref ? (
        <>
          {' '}
          <a href={showScheduledMissingImageSchoolsOnlyHref}>{`仅看近期缺图学校（${scheduledMissingImagesCount}）`}</a>
        </>
      ) : null}
    </p>
  );

  return (
    <main>
      <h1>{title}</h1>

      <section>
        {cards.map((card) => (
          <article key={card}>
            <h2>{card}</h2>
          </article>
        ))}
      </section>

      <section aria-labelledby="review-queue-heading">
        <h2 id="review-queue-heading">待审核队列</h2>

        {queueError ? <p>{queueError}</p> : null}

        {!queueError && queueItems.length === 0 ? <p>当前没有待审核内容</p> : null}

        {!queueError && queueItems.length > 0 ? (
          <div>
            {queueItems.map((item) => (
              <article key={item.id}>
                <h3>{`${item.entity_type} #${item.entity_id}`}</h3>
                <p>{item.diff_summary.join(', ')}</p>
                <p>{`优先级: ${item.priority}`}</p>
                <p>{`候选版本: ${item.candidate_version ?? '未提供'}`}</p>
                <p>{`创建时间: ${item.created_at}`}</p>

                <form action={approveAction}>
                  <input type="hidden" name="queueId" value={item.id} />
                  <input type="hidden" name="reviewedBy" value="web-admin" />
                  <button type="submit">通过</button>
                </form>

                <form action={rejectAction}>
                  <input type="hidden" name="queueId" value={item.id} />
                  <input type="hidden" name="reviewedBy" value="web-admin" />
                  <input type="text" name="reviewNote" aria-label={`驳回备注 ${item.id}`} />
                  <button type="submit">驳回</button>
                </form>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="featured-schools-heading">
        <h2 id="featured-schools-heading">学校展示配置</h2>
        <p>{`已配置图片 ${schoolsWithImagesCount} 所，待补图片 ${schoolsMissingImages.length} 所`}</p>
        {showMissingImageSchoolsOnlyHref ||
        showScheduledMissingImageSchoolsOnlyHref ||
        showAllFeaturedSchoolsHref
          ? schoolFilterLinks
          : null}

        {featuredContentError ? <p>{featuredContentError}</p> : null}

        {!featuredContentError ? (
          <div>
            {displayedFeaturedSchools.length === 0 ? (
              <p>
                {showScheduledMissingImageSchoolsOnly
                  ? '当前没有近期会展示且缺图的学校'
                  : '当前没有待补图片学校配置'}
              </p>
            ) : null}
            {displayedFeaturedSchools.map((school) => (
              <div key={school.slug} id={`featured-school-${school.slug}`}>
                <form action={updateFeaturedSchoolAction}>
                  <input type="hidden" name="slug" value={school.slug} />
                  <label>
                    <input type="checkbox" name="isFeatured" defaultChecked={school.isFeatured} />
                    {school.name}
                  </label>
                  <p>{school.slug}</p>
                  <input
                    type="text"
                    name="heroImageUrl"
                    defaultValue={school.heroImageUrl}
                    aria-label={`学校图片 ${school.slug}`}
                  />
                  {school.heroImageUrl ? (
                    <img
                      src={school.heroImageUrl}
                      alt={`${school.name} 当前展示图`}
                      aria-label={`featured-school-image-${school.slug}`}
                      width={160}
                      height={96}
                    />
                  ) : null}
                  {school.heroImageUrl ? (
                    <a
                      href={school.heroImageUrl}
                      target="_blank"
                      rel="noreferrer"
                      aria-label="查看原图"
                    >
                      查看原图
                    </a>
                  ) : null}
                  <button type="submit">保存</button>
                </form>

                {school.heroImageUrl ? (
                  <form action={updateFeaturedSchoolAction}>
                    <input type="hidden" name="slug" value={school.slug} />
                    <input type="hidden" name="isFeatured" value={school.isFeatured ? 'on' : ''} />
                    <input type="hidden" name="heroImageUrl" value="" />
                    <button type="submit">清空图片</button>
                  </form>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="missing-school-images-heading">
        <h2 id="missing-school-images-heading">{`待补图片学校（${schoolsMissingImages.length}）`}</h2>

        {featuredContentError ? null : schoolsMissingImages.length === 0 ? (
          <p>当前没有待补图片学校</p>
        ) : (
          <>
            <p>{`今日缺图 ${todayMissingImagesCount} 所，下一轮缺图 ${nextMissingImagesCount} 所`}</p>
            <ul>
              {schoolsMissingImages.map((school) => (
                <li key={school.slug}>
                  <a href={`#featured-school-${school.slug}`}>{school.name}</a>
                  <span>{school.slug}</span>
                  {todayPreviewSchoolSlugs.has(school.slug) ? (
                    <a href="#featured-school-preview-heading">今日展示</a>
                  ) : null}
                  {nextPreviewSchoolSlugs.has(school.slug) ? (
                    <a href="#next-featured-school-preview-heading">下一轮展示</a>
                  ) : null}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section aria-labelledby="featured-majors-heading">
        <h2 id="featured-majors-heading">专业展示配置</h2>

        {featuredContentError ? null : (
          <div>
            {featuredMajors.map((major) => (
              <form key={major.slug} action={updateFeaturedMajorAction}>
                <input type="hidden" name="slug" value={major.slug} />
                <label>
                  <input type="checkbox" name="isFeatured" defaultChecked={major.isFeatured} />
                  {major.name}
                </label>
                <p>{major.slug}</p>
                <button type="submit">保存</button>
              </form>
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="school-content-summary-heading">
        <h2 id="school-content-summary-heading">学校摘要编辑</h2>

        {contentSummaryError ? <p>{contentSummaryError}</p> : null}

        {!contentSummaryError ? (
          <div>
            {summarySchools.length === 0 ? <p>当前没有可编辑的学校摘要</p> : null}
            {summarySchools.map((school) => (
              <div key={school.slug}>
                <ContentSummaryForm entity={school} action={updateSchoolSummaryAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="major-content-summary-heading">
        <h2 id="major-content-summary-heading">专业摘要编辑</h2>

        {contentSummaryError ? <p>{contentSummaryError}</p> : null}

        {!contentSummaryError ? (
          <div>
            {summaryMajors.length === 0 ? <p>当前没有可编辑的专业摘要</p> : null}
            {summaryMajors.map((major) => (
              <div key={major.slug}>
                <ContentSummaryForm entity={major} action={updateMajorSummaryAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="school-content-sections-heading">
        <h2 id="school-content-sections-heading">学校正文编辑</h2>

        {contentSectionError ? <p>{contentSectionError}</p> : null}

        {!contentSectionError ? (
          <div>
            {sectionSchools.length === 0 ? <p>当前没有可编辑的学校正文</p> : null}
            {sectionSchools.map((school) => (
              <div key={school.slug}>
                <ContentSectionsForm entity={school} action={updateSchoolSectionsAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="major-content-sections-heading">
        <h2 id="major-content-sections-heading">专业正文编辑</h2>

        {contentSectionError ? <p>{contentSectionError}</p> : null}

        {!contentSectionError ? (
          <div>
            {sectionMajors.length === 0 ? <p>当前没有可编辑的专业正文</p> : null}
            {sectionMajors.map((major) => (
              <div key={major.slug}>
                <ContentSectionsForm entity={major} action={updateMajorSectionsAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="school-ranking-reference-heading">
        <h2 id="school-ranking-reference-heading">学校榜单引用</h2>

        {rankingReferenceError ? <p>{rankingReferenceError}</p> : null}

        {!rankingReferenceError ? (
          <div>
            <p>{`已配置学校榜单 ${configuredSchoolRankingReferenceCount} 所，待补学校榜单 ${missingSchoolRankingReferences.length} 所`}</p>
            {showMissingSchoolRankingsOnlyHref || showAllSchoolRankingReferencesHref ? (
              <p>
                {!showMissingSchoolRankingsOnly && showMissingSchoolRankingsOnlyHref ? (
                  <a href={showMissingSchoolRankingsOnlyHref}>{`仅看待补学校榜单（${missingSchoolRankingReferences.length}）`}</a>
                ) : null}
                {showMissingSchoolRankingsOnly && showAllSchoolRankingReferencesHref ? (
                  <a href={showAllSchoolRankingReferencesHref}>查看全部学校榜单</a>
                ) : null}
              </p>
            ) : null}
            {displayedSchoolRankingReferences.map((school) => (
              <div key={school.slug} id={`school-ranking-reference-${school.slug}`}>
                <RankingReferenceForm
                  entity={school}
                  entityLabel="学校"
                  action={updateSchoolRankingReferencesAction}
                  submitLabel="保存学校榜单"
                />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="missing-school-ranking-reference-heading">
        <h2 id="missing-school-ranking-reference-heading">{`待补学校榜单（${missingSchoolRankingReferences.length}）`}</h2>

        {rankingReferenceError ? null : missingSchoolRankingReferences.length === 0 ? (
          <p>当前没有待补学校榜单</p>
        ) : (
          <>
            <p>{`今日待补 ${todayMissingSchoolRankingCount} 所，下一轮待补 ${nextMissingSchoolRankingCount} 所`}</p>
            <ul>
              {missingSchoolRankingReferences.map((school) => (
                <li key={school.slug}>
                  <a href={`#school-ranking-reference-${school.slug}`}>{school.name}</a>
                  <span>{school.slug}</span>
                  {featuredSchoolSlugs.has(school.slug) ? <span>当前展示</span> : null}
                  {todayPreviewSchoolSlugs.has(school.slug) ? (
                    <a href="#featured-school-preview-heading">今日展示</a>
                  ) : null}
                  {nextPreviewSchoolSlugs.has(school.slug) ? (
                    <a href="#next-featured-school-preview-heading">下一轮展示</a>
                  ) : null}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section aria-labelledby="major-ranking-reference-heading">
        <h2 id="major-ranking-reference-heading">专业榜单引用</h2>

        {rankingReferenceError ? <p>{rankingReferenceError}</p> : null}

        {!rankingReferenceError ? (
          <div>
            <p>{`已配置专业榜单 ${configuredMajorRankingReferenceCount} 个，待补专业榜单 ${missingMajorRankingReferences.length} 个`}</p>
            {showMissingMajorRankingsOnlyHref || showAllMajorRankingReferencesHref ? (
              <p>
                {!showMissingMajorRankingsOnly && showMissingMajorRankingsOnlyHref ? (
                  <a href={showMissingMajorRankingsOnlyHref}>{`仅看待补专业榜单（${missingMajorRankingReferences.length}）`}</a>
                ) : null}
                {showMissingMajorRankingsOnly && showAllMajorRankingReferencesHref ? (
                  <a href={showAllMajorRankingReferencesHref}>查看全部专业榜单</a>
                ) : null}
              </p>
            ) : null}
            {displayedMajorRankingReferences.map((major) => (
              <div key={major.slug} id={`major-ranking-reference-${major.slug}`}>
                <RankingReferenceForm
                  entity={major}
                  entityLabel="专业"
                  action={updateMajorRankingReferencesAction}
                  submitLabel="保存专业榜单"
                />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-labelledby="missing-major-ranking-reference-heading">
        <h2 id="missing-major-ranking-reference-heading">{`待补专业榜单（${missingMajorRankingReferences.length}）`}</h2>

        {rankingReferenceError ? null : missingMajorRankingReferences.length === 0 ? (
          <p>当前没有待补专业榜单</p>
        ) : (
          <>
            <p>{`今日待补 ${todayMissingMajorRankingCount} 个，下一轮待补 ${nextMissingMajorRankingCount} 个`}</p>
            <ul>
              {missingMajorRankingReferences.map((major) => (
                <li key={major.slug}>
                  <a href={`#major-ranking-reference-${major.slug}`}>{major.name}</a>
                  <span>{major.slug}</span>
                  {featuredMajorSlugs.has(major.slug) ? <span>当前展示</span> : null}
                  {todayPreviewMajorSlugs.has(major.slug) ? (
                    <a href="#featured-major-preview-heading">今日展示</a>
                  ) : null}
                  {nextPreviewMajorSlugs.has(major.slug) ? (
                    <a href="#next-featured-major-preview-heading">下一轮展示</a>
                  ) : null}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section aria-labelledby="school-rotation-heading">
        <h2 id="school-rotation-heading">学校轮换规则</h2>

        {featuredContentError ? null : (
          <form action={updateSchoolRotationAction}>
            <label>
              <input type="checkbox" name="enabled" defaultChecked={schoolRotation.enabled} />
              启用自动轮换
            </label>
            <label>
              轮换频率（天）
              <input
                type="number"
                name="frequencyDays"
                min={1}
                defaultValue={schoolRotation.frequencyDays}
              />
            </label>
            <label>
              当前展示数量
              <input type="number" name="windowSize" min={1} defaultValue={schoolRotation.windowSize} />
            </label>
            <label>
              学校轮换顺序
              <textarea
                name="orderedSlugs"
                aria-label="学校轮换顺序"
                defaultValue={schoolRotation.orderedSlugs.join('\n')}
              />
            </label>
            <button type="submit">保存轮换规则</button>
          </form>
        )}
      </section>

      <section aria-labelledby="major-rotation-heading">
        <h2 id="major-rotation-heading">专业轮换规则</h2>

        {featuredContentError ? null : (
          <form action={updateMajorRotationAction}>
            <label>
              <input type="checkbox" name="enabled" defaultChecked={majorRotation.enabled} />
              启用自动轮换
            </label>
            <label>
              轮换频率（天）
              <input
                type="number"
                name="frequencyDays"
                min={1}
                defaultValue={majorRotation.frequencyDays}
              />
            </label>
            <label>
              当前展示数量
              <input type="number" name="windowSize" min={1} defaultValue={majorRotation.windowSize} />
            </label>
            <label>
              专业轮换顺序
              <textarea
                name="orderedSlugs"
                aria-label="专业轮换顺序"
                defaultValue={majorRotation.orderedSlugs.join('\n')}
              />
            </label>
            <button type="submit">保存轮换规则</button>
          </form>
        )}
      </section>

      <section aria-labelledby="featured-school-preview-heading">
        <h2 id="featured-school-preview-heading">今日展示学校</h2>

        {featuredContentError ? null : featuredSchoolPreview.length === 0 ? (
          <p>当前没有可展示学校</p>
        ) : (
          <PreviewList
            items={featuredSchoolPreview}
            imageAvailabilityBySlug={schoolImageAvailabilityBySlug}
          />
        )}
      </section>

      <section aria-labelledby="featured-major-preview-heading">
        <h2 id="featured-major-preview-heading">今日展示专业</h2>

        {featuredContentError ? null : featuredMajorPreview.length === 0 ? (
          <p>当前没有可展示专业</p>
        ) : (
          <PreviewList items={featuredMajorPreview} />
        )}
      </section>

      <section aria-labelledby="next-featured-school-preview-heading">
        <h2 id="next-featured-school-preview-heading">下一轮展示学校</h2>

        {featuredContentError ? null : nextFeaturedSchoolPreview.length === 0 ? (
          <p>当前没有下一轮展示学校</p>
        ) : (
          <PreviewList
            items={nextFeaturedSchoolPreview}
            imageAvailabilityBySlug={schoolImageAvailabilityBySlug}
          />
        )}
      </section>

      <section aria-labelledby="next-featured-major-preview-heading">
        <h2 id="next-featured-major-preview-heading">下一轮展示专业</h2>

        {featuredContentError ? null : nextFeaturedMajorPreview.length === 0 ? (
          <p>当前没有下一轮展示专业</p>
        ) : (
          <PreviewList items={nextFeaturedMajorPreview} />
        )}
      </section>

      <section aria-labelledby="selected-date-preview-heading">
        <h2 id="selected-date-preview-heading">指定日期预览</h2>

        <form action="/admin" method="GET">
          <label>
            预览日期
            <input type="date" name="preview_date" defaultValue={selectedPreviewDateValue} />
          </label>
          {showMissingImageSchoolsOnly ? (
            <input type="hidden" name="missing_school_images" value="1" />
          ) : null}
          {showScheduledMissingImageSchoolsOnly ? (
            <input type="hidden" name="scheduled_missing_school_images" value="1" />
          ) : null}
          <button type="submit">查看该日轮换</button>
        </form>

        {todayPreviewDateHref || previousPreviewDateHref || nextPreviewDateHref ? (
          <p>
            {previousPreviewDateHref ? <a href={previousPreviewDateHref}>查看前一天</a> : null}
            {previousPreviewDateHref && (todayPreviewDateHref || nextPreviewDateHref) ? ' ' : null}
            {todayPreviewDateHref ? <a href={todayPreviewDateHref}>回到今天</a> : null}
            {todayPreviewDateHref && nextPreviewDateHref ? ' ' : null}
            {nextPreviewDateHref ? <a href={nextPreviewDateHref}>查看后一天</a> : null}
          </p>
        ) : null}

        {showSelectedDateHelper ? <p>选择一个日期查看当天轮换结果</p> : null}
        {selectedDateError ? <p>{selectedDateError}</p> : null}

        {selectedDatePreview ? (
          <div>
            <p>{selectedDatePreview.date}</p>
            <p>{selectedDatePreview.weekday}</p>

            <section aria-labelledby="selected-date-school-preview-heading">
              <h3 id="selected-date-school-preview-heading">该日展示学校</h3>
              {selectedDatePreview.schools.length === 0 ? (
                <p>该日没有展示学校</p>
              ) : (
                <PreviewList
                  items={selectedDatePreview.schools}
                  imageAvailabilityBySlug={schoolImageAvailabilityBySlug}
                />
              )}
            </section>

            <section aria-labelledby="selected-date-major-preview-heading">
              <h3 id="selected-date-major-preview-heading">该日展示专业</h3>
              {selectedDatePreview.majors.length === 0 ? (
                <p>该日没有展示专业</p>
              ) : (
                <PreviewList items={selectedDatePreview.majors} />
              )}
            </section>
          </div>
        ) : null}
      </section>

      <section aria-labelledby="featured-schedule-heading">
        <h2 id="featured-schedule-heading">未来 7 天轮换预览</h2>

        {featuredContentError ? null : featuredSchedule.length === 0 ? (
          <p>当前没有未来轮换预览</p>
        ) : (
          <div>
            {featuredSchedule.map((day) => (
              <article key={day.date}>
                <h3>
                  {day.date === highlightedScheduleDate ? (
                    day.date
                  ) : (
                    <a
                      href={
                        showScheduledMissingImageSchoolsOnly
                          ? `/admin?preview_date=${day.date}&scheduled_missing_school_images=1`
                          : showMissingImageSchoolsOnly
                            ? `/admin?preview_date=${day.date}&missing_school_images=1`
                            : `/admin?preview_date=${day.date}`
                      }
                    >
                      {day.date}
                    </a>
                  )}
                </h3>
                <p>{day.weekday}</p>
                {day.date === highlightedScheduleDate ? <p>当前查看</p> : null}
                <p>学校</p>
                {day.schools.length === 0 ? (
                  <p>当天没有展示学校</p>
                ) : (
                  <PreviewList
                    items={day.schools}
                    imageAvailabilityBySlug={schoolImageAvailabilityBySlug}
                  />
                )}
                <p>专业</p>
                {day.majors.length === 0 ? (
                  <p>当天没有展示专业</p>
                ) : (
                  <PreviewList items={day.majors} />
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
