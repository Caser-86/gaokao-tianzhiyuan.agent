import type {
  AdminContentSummaryEntity,
} from '../../lib/admin-content-summary-api';
import type {
  AdminContentSection,
  AdminContentSectionsEntity,
} from '../../lib/admin-content-sections-api';
import type {
  AdminRelatedMajorEntity,
  AdminRelatedSchoolEntity,
} from '../../lib/admin-related-content-api';
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
  showScheduledMissingSchoolSummariesOnly?: boolean;
  showScheduledMissingSchoolSummariesOnlyHref?: string;
  showAllScheduledSchoolSummariesHref?: string;
  showScheduledMissingMajorSummariesOnly?: boolean;
  showScheduledMissingMajorSummariesOnlyHref?: string;
  showAllScheduledMajorSummariesHref?: string;
  sectionSchools?: AdminContentSectionsEntity[];
  sectionMajors?: AdminContentSectionsEntity[];
  showScheduledMissingSchoolSectionsOnly?: boolean;
  showScheduledMissingSchoolSectionsOnlyHref?: string;
  showAllScheduledSchoolSectionsHref?: string;
  showScheduledMissingMajorSectionsOnly?: boolean;
  showScheduledMissingMajorSectionsOnlyHref?: string;
  showAllScheduledMajorSectionsHref?: string;
  showScheduledGapDaysOnly?: boolean;
  showScheduledGapDaysOnlyHref?: string;
  showAllScheduledGapDaysHref?: string;
  relatedSchools?: AdminRelatedSchoolEntity[];
  relatedMajors?: AdminRelatedMajorEntity[];
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
  showScheduledMissingSchoolRankingsOnly?: boolean;
  showScheduledMissingSchoolRankingsOnlyHref?: string;
  showAllScheduledSchoolRankingReferencesHref?: string;
  showMissingMajorRankingsOnly?: boolean;
  showMissingMajorRankingsOnlyHref?: string;
  showAllMajorRankingReferencesHref?: string;
  showScheduledMissingMajorRankingsOnly?: boolean;
  showScheduledMissingMajorRankingsOnlyHref?: string;
  showAllScheduledMajorRankingReferencesHref?: string;
  showMissingSchoolRelatedOnly?: boolean;
  showMissingSchoolRelatedOnlyHref?: string;
  showAllSchoolRelatedContentHref?: string;
  showMissingMajorRelatedOnly?: boolean;
  showMissingMajorRelatedOnlyHref?: string;
  showAllMajorRelatedContentHref?: string;
  showScheduledMissingSchoolRelatedOnly?: boolean;
  showScheduledMissingSchoolRelatedOnlyHref?: string;
  showAllScheduledSchoolRelatedContentHref?: string;
  showScheduledMissingMajorRelatedOnly?: boolean;
  showScheduledMissingMajorRelatedOnlyHref?: string;
  showAllScheduledMajorRelatedContentHref?: string;
  rankingReferenceError?: string;
  contentSummaryError?: string;
  contentSectionError?: string;
  relatedContentError?: string;
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
  updateSchoolRelatedContentAction?: (formData: FormData) => Promise<void>;
  updateMajorRelatedContentAction?: (formData: FormData) => Promise<void>;
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

function RelatedContentForm({
  entity,
  fieldName,
  relatedSlugs,
  action,
}: {
  entity: { slug: string; name: string };
  fieldName: 'relatedMajors' | 'relatedSchools';
  relatedSlugs: string[];
  action: (formData: FormData) => Promise<void>;
}) {
  return (
    <form action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <h3>{entity.name}</h3>
      <p>{entity.slug}</p>
      <label>
        关联 slug
        <textarea name={fieldName} defaultValue={relatedSlugs.join('\n')} />
      </label>
      <button type="submit">保存相关推荐</button>
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
  showScheduledMissingSchoolSummariesOnly = false,
  showScheduledMissingSchoolSummariesOnlyHref,
  showAllScheduledSchoolSummariesHref,
  showScheduledMissingMajorSummariesOnly = false,
  showScheduledMissingMajorSummariesOnlyHref,
  showAllScheduledMajorSummariesHref,
  sectionSchools = [],
  sectionMajors = [],
  showScheduledMissingSchoolSectionsOnly = false,
  showScheduledMissingSchoolSectionsOnlyHref,
  showAllScheduledSchoolSectionsHref,
  showScheduledMissingMajorSectionsOnly = false,
  showScheduledMissingMajorSectionsOnlyHref,
  showAllScheduledMajorSectionsHref,
  showScheduledGapDaysOnly = false,
  showScheduledGapDaysOnlyHref,
  showAllScheduledGapDaysHref,
  relatedSchools = [],
  relatedMajors = [],
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
  showScheduledMissingSchoolRankingsOnly = false,
  showScheduledMissingSchoolRankingsOnlyHref,
  showAllScheduledSchoolRankingReferencesHref,
  showMissingMajorRankingsOnly = false,
  showMissingMajorRankingsOnlyHref,
  showAllMajorRankingReferencesHref,
  showScheduledMissingMajorRankingsOnly = false,
  showScheduledMissingMajorRankingsOnlyHref,
  showAllScheduledMajorRankingReferencesHref,
  showMissingSchoolRelatedOnly = false,
  showMissingSchoolRelatedOnlyHref,
  showAllSchoolRelatedContentHref,
  showMissingMajorRelatedOnly = false,
  showMissingMajorRelatedOnlyHref,
  showAllMajorRelatedContentHref,
  showScheduledMissingSchoolRelatedOnly = false,
  showScheduledMissingSchoolRelatedOnlyHref,
  showAllScheduledSchoolRelatedContentHref,
  showScheduledMissingMajorRelatedOnly = false,
  showScheduledMissingMajorRelatedOnlyHref,
  showAllScheduledMajorRelatedContentHref,
  rankingReferenceError,
  contentSummaryError,
  contentSectionError,
  relatedContentError,
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
  updateSchoolRelatedContentAction = noopAction,
  updateMajorRelatedContentAction = noopAction,
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
  const selectedDateSchoolSlugs = new Set(
    (selectedDatePreview?.schools ?? []).map((school) => school.slug),
  );
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
  const selectedDateMajorSlugs = new Set(
    (selectedDatePreview?.majors ?? []).map((major) => major.slug),
  );
  const todayMissingMajorRankingCount = missingMajorRankingReferences.filter((major) =>
    todayPreviewMajorSlugs.has(major.slug),
  ).length;
  const nextMissingMajorRankingCount = missingMajorRankingReferences.filter((major) =>
    nextPreviewMajorSlugs.has(major.slug),
  ).length;
  const scheduledMissingSchoolRankingSlugs = new Set([
    ...featuredSchoolPreview.map((school) => school.slug),
    ...nextFeaturedSchoolPreview.map((school) => school.slug),
  ]);
  const scheduledMissingMajorRankingSlugs = new Set([
    ...featuredMajorPreview.map((major) => major.slug),
    ...nextFeaturedMajorPreview.map((major) => major.slug),
  ]);
  const scheduledMissingSchoolRankingCount = missingSchoolRankingReferences.filter((school) =>
    scheduledMissingSchoolRankingSlugs.has(school.slug),
  ).length;
  const scheduledMissingMajorRankingCount = missingMajorRankingReferences.filter((major) =>
    scheduledMissingMajorRankingSlugs.has(major.slug),
  ).length;
  const displayedSchoolRankingReferences = showMissingSchoolRankingsOnly
    ? missingSchoolRankingReferences
    : showScheduledMissingSchoolRankingsOnly
      ? sortedRankingReferenceSchools.filter(
          (school) =>
            school.rankingReferences.length === 0 && scheduledMissingSchoolRankingSlugs.has(school.slug),
        )
      : sortedRankingReferenceSchools;
  const displayedMajorRankingReferences = showMissingMajorRankingsOnly
    ? missingMajorRankingReferences
    : showScheduledMissingMajorRankingsOnly
      ? sortedRankingReferenceMajors.filter(
          (major) =>
            major.rankingReferences.length === 0 && scheduledMissingMajorRankingSlugs.has(major.slug),
        )
      : sortedRankingReferenceMajors;
  const relatedCoveragePriority = (
    slug: string,
    featuredSlugs: Set<string>,
    todaySlugs: Set<string>,
    nextSlugs: Set<string>,
  ): number => {
    if (todaySlugs.has(slug)) {
      return 0;
    }

    if (nextSlugs.has(slug)) {
      return 1;
    }

    if (featuredSlugs.has(slug)) {
      return 2;
    }

    return 3;
  };
  const sortedRelatedSchools = [...relatedSchools].sort((left, right) => {
    const leftMissing = left.relatedMajors.length === 0 ? 0 : 1;
    const rightMissing = right.relatedMajors.length === 0 ? 0 : 1;
    if (leftMissing !== rightMissing) {
      return leftMissing - rightMissing;
    }

    const priorityDifference =
      relatedCoveragePriority(
        left.slug,
        featuredSchoolSlugs,
        todayPreviewSchoolSlugs,
        nextPreviewSchoolSlugs,
      ) -
      relatedCoveragePriority(
        right.slug,
        featuredSchoolSlugs,
        todayPreviewSchoolSlugs,
        nextPreviewSchoolSlugs,
      );
    if (priorityDifference !== 0) {
      return priorityDifference;
    }

    return left.name.localeCompare(right.name, 'zh-CN');
  });
  const sortedRelatedMajors = [...relatedMajors].sort((left, right) => {
    const leftMissing = left.relatedSchools.length === 0 ? 0 : 1;
    const rightMissing = right.relatedSchools.length === 0 ? 0 : 1;
    if (leftMissing !== rightMissing) {
      return leftMissing - rightMissing;
    }

    const priorityDifference =
      relatedCoveragePriority(
        left.slug,
        featuredMajorSlugs,
        todayPreviewMajorSlugs,
        nextPreviewMajorSlugs,
      ) -
      relatedCoveragePriority(
        right.slug,
        featuredMajorSlugs,
        todayPreviewMajorSlugs,
        nextPreviewMajorSlugs,
      );
    if (priorityDifference !== 0) {
      return priorityDifference;
    }

    return left.name.localeCompare(right.name, 'zh-CN');
  });
  const missingSchoolRelatedContent = sortedRelatedSchools.filter(
    (school) => school.relatedMajors.length === 0,
  );
  const missingMajorRelatedContent = sortedRelatedMajors.filter(
    (major) => major.relatedSchools.length === 0,
  );
  const configuredSchoolRelatedContentCount =
    sortedRelatedSchools.length - missingSchoolRelatedContent.length;
  const configuredMajorRelatedContentCount =
    sortedRelatedMajors.length - missingMajorRelatedContent.length;
  const todayMissingSchoolRelatedCount = missingSchoolRelatedContent.filter((school) =>
    todayPreviewSchoolSlugs.has(school.slug),
  ).length;
  const nextMissingSchoolRelatedCount = missingSchoolRelatedContent.filter((school) =>
    nextPreviewSchoolSlugs.has(school.slug),
  ).length;
  const todayMissingMajorRelatedCount = missingMajorRelatedContent.filter((major) =>
    todayPreviewMajorSlugs.has(major.slug),
  ).length;
  const nextMissingMajorRelatedCount = missingMajorRelatedContent.filter((major) =>
    nextPreviewMajorSlugs.has(major.slug),
  ).length;
  const scheduledMissingSchoolRelatedSlugs = new Set([
    ...featuredSchoolPreview.map((school) => school.slug),
    ...nextFeaturedSchoolPreview.map((school) => school.slug),
  ]);
  const scheduledMissingMajorRelatedSlugs = new Set([
    ...featuredMajorPreview.map((major) => major.slug),
    ...nextFeaturedMajorPreview.map((major) => major.slug),
  ]);
  const scheduledMissingSchoolRelatedCount = missingSchoolRelatedContent.filter((school) =>
    scheduledMissingSchoolRelatedSlugs.has(school.slug),
  ).length;
  const scheduledMissingMajorRelatedCount = missingMajorRelatedContent.filter((major) =>
    scheduledMissingMajorRelatedSlugs.has(major.slug),
  ).length;
  const displayedRelatedSchools = showMissingSchoolRelatedOnly
    ? missingSchoolRelatedContent
    : showScheduledMissingSchoolRelatedOnly
      ? sortedRelatedSchools.filter(
          (school) =>
            school.relatedMajors.length === 0 && scheduledMissingSchoolRelatedSlugs.has(school.slug),
        )
      : sortedRelatedSchools;
  const displayedRelatedMajors = showMissingMajorRelatedOnly
    ? missingMajorRelatedContent
    : showScheduledMissingMajorRelatedOnly
      ? sortedRelatedMajors.filter(
          (major) =>
            major.relatedSchools.length === 0 && scheduledMissingMajorRelatedSlugs.has(major.slug),
        )
      : sortedRelatedMajors;
  const sortedSummarySchools = [...summarySchools].sort((left, right) => {
    const leftMissing = left.summary.trim() === '' ? 0 : 1;
    const rightMissing = right.summary.trim() === '' ? 0 : 1;
    if (leftMissing !== rightMissing) {
      return leftMissing - rightMissing;
    }

    const priorityDifference =
      relatedCoveragePriority(
        left.slug,
        featuredSchoolSlugs,
        todayPreviewSchoolSlugs,
        nextPreviewSchoolSlugs,
      ) -
      relatedCoveragePriority(
        right.slug,
        featuredSchoolSlugs,
        todayPreviewSchoolSlugs,
        nextPreviewSchoolSlugs,
      );
    if (priorityDifference !== 0) {
      return priorityDifference;
    }

    return left.name.localeCompare(right.name, 'zh-CN');
  });
  const sortedSummaryMajors = [...summaryMajors].sort((left, right) => {
    const leftMissing = left.summary.trim() === '' ? 0 : 1;
    const rightMissing = right.summary.trim() === '' ? 0 : 1;
    if (leftMissing !== rightMissing) {
      return leftMissing - rightMissing;
    }

    const priorityDifference =
      relatedCoveragePriority(
        left.slug,
        featuredMajorSlugs,
        todayPreviewMajorSlugs,
        nextPreviewMajorSlugs,
      ) -
      relatedCoveragePriority(
        right.slug,
        featuredMajorSlugs,
        todayPreviewMajorSlugs,
        nextPreviewMajorSlugs,
      );
    if (priorityDifference !== 0) {
      return priorityDifference;
    }

    return left.name.localeCompare(right.name, 'zh-CN');
  });
  const missingSchoolSummaries = sortedSummarySchools.filter((school) => school.summary.trim() === '');
  const missingMajorSummaries = sortedSummaryMajors.filter((major) => major.summary.trim() === '');
  const scheduledMissingSchoolSummariesCount = missingSchoolSummaries.filter((school) =>
    scheduledMissingSchoolSlugs.has(school.slug),
  ).length;
  const scheduledMissingMajorSummariesCount = missingMajorSummaries.filter((major) =>
    scheduledMissingMajorRelatedSlugs.has(major.slug),
  ).length;
  const displayedSummarySchools = showScheduledMissingSchoolSummariesOnly
    ? sortedSummarySchools.filter(
        (school) => school.summary.trim() === '' && scheduledMissingSchoolSlugs.has(school.slug),
      )
    : sortedSummarySchools;
  const displayedSummaryMajors = showScheduledMissingMajorSummariesOnly
    ? sortedSummaryMajors.filter(
        (major) => major.summary.trim() === '' && scheduledMissingMajorRelatedSlugs.has(major.slug),
      )
    : sortedSummaryMajors;
  const sortedSectionSchools = [...sectionSchools].sort((left, right) => {
    const leftMissing = left.sections.length === 0 ? 0 : 1;
    const rightMissing = right.sections.length === 0 ? 0 : 1;
    if (leftMissing !== rightMissing) {
      return leftMissing - rightMissing;
    }

    const priorityDifference =
      relatedCoveragePriority(
        left.slug,
        featuredSchoolSlugs,
        todayPreviewSchoolSlugs,
        nextPreviewSchoolSlugs,
      ) -
      relatedCoveragePriority(
        right.slug,
        featuredSchoolSlugs,
        todayPreviewSchoolSlugs,
        nextPreviewSchoolSlugs,
      );
    if (priorityDifference !== 0) {
      return priorityDifference;
    }

    return left.name.localeCompare(right.name, 'zh-CN');
  });
  const sortedSectionMajors = [...sectionMajors].sort((left, right) => {
    const leftMissing = left.sections.length === 0 ? 0 : 1;
    const rightMissing = right.sections.length === 0 ? 0 : 1;
    if (leftMissing !== rightMissing) {
      return leftMissing - rightMissing;
    }

    const priorityDifference =
      relatedCoveragePriority(
        left.slug,
        featuredMajorSlugs,
        todayPreviewMajorSlugs,
        nextPreviewMajorSlugs,
      ) -
      relatedCoveragePriority(
        right.slug,
        featuredMajorSlugs,
        todayPreviewMajorSlugs,
        nextPreviewMajorSlugs,
      );
    if (priorityDifference !== 0) {
      return priorityDifference;
    }

    return left.name.localeCompare(right.name, 'zh-CN');
  });
  const missingSchoolSections = sortedSectionSchools.filter((school) => school.sections.length === 0);
  const missingMajorSections = sortedSectionMajors.filter((major) => major.sections.length === 0);
  const scheduledMissingSchoolSectionsCount = missingSchoolSections.filter((school) =>
    scheduledMissingSchoolSlugs.has(school.slug),
  ).length;
  const scheduledMissingMajorSectionsCount = missingMajorSections.filter((major) =>
    scheduledMissingMajorRelatedSlugs.has(major.slug),
  ).length;
  const displayedSectionSchools = showScheduledMissingSchoolSectionsOnly
    ? sortedSectionSchools.filter(
        (school) => school.sections.length === 0 && scheduledMissingSchoolSlugs.has(school.slug),
      )
    : sortedSectionSchools;
  const displayedSectionMajors = showScheduledMissingMajorSectionsOnly
    ? sortedSectionMajors.filter(
        (major) => major.sections.length === 0 && scheduledMissingMajorRelatedSlugs.has(major.slug),
      )
    : sortedSectionMajors;
  const appendAnchor = (href: string | undefined, anchorId: string): string =>
    href ? `${href}#${anchorId}` : `#${anchorId}`;
  const countMatchingSlugs = <T extends { slug: string }>(
    entities: T[],
    slugs: Set<string>,
  ): number => entities.filter((entity) => slugs.has(entity.slug)).length;
  const countPreviewContentGaps = (
    schoolSlugs: Set<string>,
    majorSlugs: Set<string>,
  ): number =>
    countMatchingSlugs(schoolsMissingImages, schoolSlugs) +
    countMatchingSlugs(missingSchoolRankingReferences, schoolSlugs) +
    countMatchingSlugs(missingMajorRankingReferences, majorSlugs) +
    countMatchingSlugs(missingSchoolSummaries, schoolSlugs) +
    countMatchingSlugs(missingMajorSummaries, majorSlugs) +
    countMatchingSlugs(missingSchoolSections, schoolSlugs) +
    countMatchingSlugs(missingMajorSections, majorSlugs) +
    countMatchingSlugs(missingSchoolRelatedContent, schoolSlugs) +
    countMatchingSlugs(missingMajorRelatedContent, majorSlugs);
  const contentGapOverviewItems = [
    {
      key: 'school-images',
      label: '学校图片',
      href: appendAnchor(showScheduledMissingImageSchoolsOnlyHref, 'missing-school-images-heading'),
      todayCount: todayMissingImagesCount,
      nextCount: nextMissingImagesCount,
      totalCount: schoolsMissingImages.length,
    },
    {
      key: 'school-rankings',
      label: '学校榜单',
      href: appendAnchor(
        showScheduledMissingSchoolRankingsOnlyHref,
        'missing-school-ranking-reference-heading',
      ),
      todayCount: todayMissingSchoolRankingCount,
      nextCount: nextMissingSchoolRankingCount,
      totalCount: missingSchoolRankingReferences.length,
    },
    {
      key: 'major-rankings',
      label: '专业榜单',
      href: appendAnchor(
        showScheduledMissingMajorRankingsOnlyHref,
        'missing-major-ranking-reference-heading',
      ),
      todayCount: todayMissingMajorRankingCount,
      nextCount: nextMissingMajorRankingCount,
      totalCount: missingMajorRankingReferences.length,
    },
    {
      key: 'school-summaries',
      label: '学校摘要',
      href: appendAnchor(
        showScheduledMissingSchoolSummariesOnlyHref,
        'missing-school-summary-heading',
      ),
      todayCount: missingSchoolSummaries.filter((school) => todayPreviewSchoolSlugs.has(school.slug)).length,
      nextCount: missingSchoolSummaries.filter((school) => nextPreviewSchoolSlugs.has(school.slug)).length,
      totalCount: missingSchoolSummaries.length,
    },
    {
      key: 'major-summaries',
      label: '专业摘要',
      href: appendAnchor(
        showScheduledMissingMajorSummariesOnlyHref,
        'missing-major-summary-heading',
      ),
      todayCount: missingMajorSummaries.filter((major) => todayPreviewMajorSlugs.has(major.slug)).length,
      nextCount: missingMajorSummaries.filter((major) => nextPreviewMajorSlugs.has(major.slug)).length,
      totalCount: missingMajorSummaries.length,
    },
    {
      key: 'school-sections',
      label: '学校正文',
      href: appendAnchor(
        showScheduledMissingSchoolSectionsOnlyHref,
        'missing-school-sections-heading',
      ),
      todayCount: missingSchoolSections.filter((school) => todayPreviewSchoolSlugs.has(school.slug)).length,
      nextCount: missingSchoolSections.filter((school) => nextPreviewSchoolSlugs.has(school.slug)).length,
      totalCount: missingSchoolSections.length,
    },
    {
      key: 'major-sections',
      label: '专业正文',
      href: appendAnchor(
        showScheduledMissingMajorSectionsOnlyHref,
        'missing-major-sections-heading',
      ),
      todayCount: missingMajorSections.filter((major) => todayPreviewMajorSlugs.has(major.slug)).length,
      nextCount: missingMajorSections.filter((major) => nextPreviewMajorSlugs.has(major.slug)).length,
      totalCount: missingMajorSections.length,
    },
    {
      key: 'school-related',
      label: '学校相关推荐',
      href: appendAnchor(
        showScheduledMissingSchoolRelatedOnlyHref,
        'missing-school-related-content-heading',
      ),
      todayCount: todayMissingSchoolRelatedCount,
      nextCount: nextMissingSchoolRelatedCount,
      totalCount: missingSchoolRelatedContent.length,
    },
    {
      key: 'major-related',
      label: '专业相关推荐',
      href: appendAnchor(
        showScheduledMissingMajorRelatedOnlyHref,
        'missing-major-related-content-heading',
      ),
      todayCount: todayMissingMajorRelatedCount,
      nextCount: nextMissingMajorRelatedCount,
      totalCount: missingMajorRelatedContent.length,
    },
  ]
    .filter((item) => item.totalCount > 0)
    .sort((left, right) => {
      if (left.todayCount !== right.todayCount) {
        return right.todayCount - left.todayCount;
      }

      if (left.nextCount !== right.nextCount) {
        return right.nextCount - left.nextCount;
      }

      if (left.totalCount !== right.totalCount) {
        return right.totalCount - left.totalCount;
      }

      return 0;
    });
  const contentGapOverviewTodayCount = contentGapOverviewItems.reduce(
    (sum, item) => sum + item.todayCount,
    0,
  );
  const contentGapOverviewNextCount = contentGapOverviewItems.reduce(
    (sum, item) => sum + item.nextCount,
    0,
  );
  const contentGapOverviewTotalCount = contentGapOverviewItems.reduce(
    (sum, item) => sum + item.totalCount,
    0,
  );
  const selectedDateGapOverviewItems = selectedDatePreview
    ? [
        {
          key: 'school-images',
          label: '学校图片',
          href: '#missing-school-images-heading',
          selectedDateCount: countMatchingSlugs(schoolsMissingImages, selectedDateSchoolSlugs),
          nextCount: countMatchingSlugs(schoolsMissingImages, nextPreviewSchoolSlugs),
          totalCount: schoolsMissingImages.length,
        },
        {
          key: 'school-rankings',
          label: '学校榜单',
          href: '#missing-school-ranking-reference-heading',
          selectedDateCount: countMatchingSlugs(
            missingSchoolRankingReferences,
            selectedDateSchoolSlugs,
          ),
          nextCount: countMatchingSlugs(missingSchoolRankingReferences, nextPreviewSchoolSlugs),
          totalCount: missingSchoolRankingReferences.length,
        },
        {
          key: 'major-rankings',
          label: '专业榜单',
          href: '#missing-major-ranking-reference-heading',
          selectedDateCount: countMatchingSlugs(missingMajorRankingReferences, selectedDateMajorSlugs),
          nextCount: countMatchingSlugs(missingMajorRankingReferences, nextPreviewMajorSlugs),
          totalCount: missingMajorRankingReferences.length,
        },
        {
          key: 'school-summaries',
          label: '学校摘要',
          href: '#missing-school-summary-heading',
          selectedDateCount: countMatchingSlugs(missingSchoolSummaries, selectedDateSchoolSlugs),
          nextCount: countMatchingSlugs(missingSchoolSummaries, nextPreviewSchoolSlugs),
          totalCount: missingSchoolSummaries.length,
        },
        {
          key: 'major-summaries',
          label: '专业摘要',
          href: '#missing-major-summary-heading',
          selectedDateCount: countMatchingSlugs(missingMajorSummaries, selectedDateMajorSlugs),
          nextCount: countMatchingSlugs(missingMajorSummaries, nextPreviewMajorSlugs),
          totalCount: missingMajorSummaries.length,
        },
        {
          key: 'school-sections',
          label: '学校正文',
          href: '#missing-school-sections-heading',
          selectedDateCount: countMatchingSlugs(missingSchoolSections, selectedDateSchoolSlugs),
          nextCount: countMatchingSlugs(missingSchoolSections, nextPreviewSchoolSlugs),
          totalCount: missingSchoolSections.length,
        },
        {
          key: 'major-sections',
          label: '专业正文',
          href: '#missing-major-sections-heading',
          selectedDateCount: countMatchingSlugs(missingMajorSections, selectedDateMajorSlugs),
          nextCount: countMatchingSlugs(missingMajorSections, nextPreviewMajorSlugs),
          totalCount: missingMajorSections.length,
        },
        {
          key: 'school-related',
          label: '学校相关推荐',
          href: '#missing-school-related-content-heading',
          selectedDateCount: countMatchingSlugs(missingSchoolRelatedContent, selectedDateSchoolSlugs),
          nextCount: countMatchingSlugs(missingSchoolRelatedContent, nextPreviewSchoolSlugs),
          totalCount: missingSchoolRelatedContent.length,
        },
        {
          key: 'major-related',
          label: '专业相关推荐',
          href: '#missing-major-related-content-heading',
          selectedDateCount: countMatchingSlugs(missingMajorRelatedContent, selectedDateMajorSlugs),
          nextCount: countMatchingSlugs(missingMajorRelatedContent, nextPreviewMajorSlugs),
          totalCount: missingMajorRelatedContent.length,
        },
      ]
        .filter((item) => item.selectedDateCount > 0 || item.nextCount > 0)
        .sort((left, right) => {
          if (left.selectedDateCount !== right.selectedDateCount) {
            return right.selectedDateCount - left.selectedDateCount;
          }

          if (left.nextCount !== right.nextCount) {
            return right.nextCount - left.nextCount;
          }

          if (left.totalCount !== right.totalCount) {
            return right.totalCount - left.totalCount;
          }

          return 0;
        })
    : [];
  const selectedDateGapOverviewSelectedCount = selectedDateGapOverviewItems.reduce(
    (sum, item) => sum + item.selectedDateCount,
    0,
  );
  const selectedDateGapOverviewNextCount = selectedDateGapOverviewItems.reduce(
    (sum, item) => sum + item.nextCount,
    0,
  );
  const selectedDateGapOverviewTotalCount = selectedDateGapOverviewItems.reduce(
    (sum, item) => sum + item.totalCount,
    0,
  );

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
  const buildPreviewDateHref = (previewDate: string): string => {
    const searchParams = new URLSearchParams({
      preview_date: previewDate,
    });

    if (showMissingImageSchoolsOnly) {
      searchParams.set('missing_school_images', '1');
    }

    if (showScheduledMissingImageSchoolsOnly) {
      searchParams.set('scheduled_missing_school_images', '1');
    }

    if (showMissingSchoolRankingsOnly) {
      searchParams.set('missing_school_rankings', '1');
    }

    if (showMissingMajorRankingsOnly) {
      searchParams.set('missing_major_rankings', '1');
    }

    if (showScheduledMissingSchoolRankingsOnly) {
      searchParams.set('scheduled_missing_school_rankings', '1');
    }

    if (showScheduledMissingMajorRankingsOnly) {
      searchParams.set('scheduled_missing_major_rankings', '1');
    }

    if (showMissingSchoolRelatedOnly) {
      searchParams.set('missing_school_related', '1');
    }

    if (showMissingMajorRelatedOnly) {
      searchParams.set('missing_major_related', '1');
    }

    if (showScheduledMissingSchoolRelatedOnly) {
      searchParams.set('scheduled_missing_school_related', '1');
    }

    if (showScheduledMissingMajorRelatedOnly) {
      searchParams.set('scheduled_missing_major_related', '1');
    }

    if (showScheduledMissingSchoolSummariesOnly) {
      searchParams.set('scheduled_missing_school_summaries', '1');
    }

    if (showScheduledMissingMajorSummariesOnly) {
      searchParams.set('scheduled_missing_major_summaries', '1');
    }

    if (showScheduledMissingSchoolSectionsOnly) {
      searchParams.set('scheduled_missing_school_sections', '1');
    }

    if (showScheduledMissingMajorSectionsOnly) {
      searchParams.set('scheduled_missing_major_sections', '1');
    }

    if (showScheduledGapDaysOnly) {
      searchParams.set('scheduled_gap_days', '1');
    }

    return `/admin?${searchParams.toString()}`;
  };
  const withSelectedPreviewDate = (href: string): string => {
    if (!selectedDatePreview) {
      return href;
    }

    if (href.startsWith('#')) {
      return `${buildPreviewDateHref(selectedDatePreview.date)}${href}`;
    }

    return href;
  };
  const withNearestScheduledGapDate = (itemKey: string, href: string): string => {
    if (!nearestScheduledGapDay) {
      return href;
    }

    const nearestSchoolSlugs = new Set(nearestScheduledGapDay.schools.map((school) => school.slug));
    const nearestMajorSlugs = new Set(nearestScheduledGapDay.majors.map((major) => major.slug));
    const deepLinkByKey: Record<string, string | undefined> = {
      'school-images': schoolsMissingImages.find((school) => nearestSchoolSlugs.has(school.slug))?.slug
        ? `#featured-school-${schoolsMissingImages.find((school) => nearestSchoolSlugs.has(school.slug))?.slug}`
        : undefined,
      'school-rankings': missingSchoolRankingReferences.find((school) =>
        nearestSchoolSlugs.has(school.slug),
      )?.slug
        ? `#school-ranking-reference-${missingSchoolRankingReferences.find((school) =>
            nearestSchoolSlugs.has(school.slug),
          )?.slug}`
        : undefined,
      'major-rankings': missingMajorRankingReferences.find((major) => nearestMajorSlugs.has(major.slug))
        ?.slug
        ? `#major-ranking-reference-${missingMajorRankingReferences.find((major) =>
            nearestMajorSlugs.has(major.slug),
          )?.slug}`
        : undefined,
      'school-summaries': missingSchoolSummaries.find((school) => nearestSchoolSlugs.has(school.slug))
        ?.slug
        ? `#school-summary-${missingSchoolSummaries.find((school) =>
            nearestSchoolSlugs.has(school.slug),
          )?.slug}`
        : undefined,
      'major-summaries': missingMajorSummaries.find((major) => nearestMajorSlugs.has(major.slug))
        ?.slug
        ? `#major-summary-${missingMajorSummaries.find((major) =>
            nearestMajorSlugs.has(major.slug),
          )?.slug}`
        : undefined,
      'school-sections': missingSchoolSections.find((school) => nearestSchoolSlugs.has(school.slug))
        ?.slug
        ? `#school-sections-${missingSchoolSections.find((school) =>
            nearestSchoolSlugs.has(school.slug),
          )?.slug}`
        : undefined,
      'major-sections': missingMajorSections.find((major) => nearestMajorSlugs.has(major.slug))
        ?.slug
        ? `#major-sections-${missingMajorSections.find((major) =>
            nearestMajorSlugs.has(major.slug),
          )?.slug}`
        : undefined,
      'school-related': missingSchoolRelatedContent.find((school) =>
        nearestSchoolSlugs.has(school.slug),
      )?.slug
        ? `#school-related-content-${missingSchoolRelatedContent.find((school) =>
            nearestSchoolSlugs.has(school.slug),
          )?.slug}`
        : undefined,
      'major-related': missingMajorRelatedContent.find((major) => nearestMajorSlugs.has(major.slug))
        ?.slug
        ? `#major-related-content-${missingMajorRelatedContent.find((major) =>
            nearestMajorSlugs.has(major.slug),
          )?.slug}`
        : undefined,
    };
    const targetHash = deepLinkByKey[itemKey] ?? '';

    if (href.startsWith('#')) {
      return `${buildPreviewDateHref(nearestScheduledGapDay.date)}${targetHash || href}`;
    }

    const [pathAndSearch] = href.split('#');
    const [pathname, search = ''] = pathAndSearch.split('?');
    const searchParams = new URLSearchParams(search);
    searchParams.set('preview_date', nearestScheduledGapDay.date);

    const query = searchParams.toString();

    return `${pathname}${query ? `?${query}` : ''}${targetHash}`;
  };
  const buildTopPriorityGapHref = (
    previewDate: string,
    schoolSlugs: Set<string>,
    majorSlugs: Set<string>,
  ): { href: string; label: string } | null => {
    const gapItems = [
      {
        label: '学校图片',
        href:
          schoolsMissingImages.find((school) => schoolSlugs.has(school.slug))?.slug
            ? `#featured-school-${schoolsMissingImages.find((school) => schoolSlugs.has(school.slug))?.slug}`
            : '#missing-school-images-heading',
        selectedDateCount: countMatchingSlugs(schoolsMissingImages, schoolSlugs),
        nextCount: countMatchingSlugs(schoolsMissingImages, nextPreviewSchoolSlugs),
        totalCount: schoolsMissingImages.length,
      },
      {
        label: '学校榜单',
        href:
          missingSchoolRankingReferences.find((school) => schoolSlugs.has(school.slug))?.slug
            ? `#school-ranking-reference-${missingSchoolRankingReferences.find((school) =>
                schoolSlugs.has(school.slug),
              )?.slug}`
            : '#missing-school-ranking-reference-heading',
        selectedDateCount: countMatchingSlugs(missingSchoolRankingReferences, schoolSlugs),
        nextCount: countMatchingSlugs(missingSchoolRankingReferences, nextPreviewSchoolSlugs),
        totalCount: missingSchoolRankingReferences.length,
      },
      {
        label: '专业榜单',
        href:
          missingMajorRankingReferences.find((major) => majorSlugs.has(major.slug))?.slug
            ? `#major-ranking-reference-${missingMajorRankingReferences.find((major) =>
                majorSlugs.has(major.slug),
              )?.slug}`
            : '#missing-major-ranking-reference-heading',
        selectedDateCount: countMatchingSlugs(missingMajorRankingReferences, majorSlugs),
        nextCount: countMatchingSlugs(missingMajorRankingReferences, nextPreviewMajorSlugs),
        totalCount: missingMajorRankingReferences.length,
      },
      {
        label: '学校摘要',
        href:
          missingSchoolSummaries.find((school) => schoolSlugs.has(school.slug))?.slug
            ? `#school-summary-${missingSchoolSummaries.find((school) => schoolSlugs.has(school.slug))?.slug}`
            : '#missing-school-summary-heading',
        selectedDateCount: countMatchingSlugs(missingSchoolSummaries, schoolSlugs),
        nextCount: countMatchingSlugs(missingSchoolSummaries, nextPreviewSchoolSlugs),
        totalCount: missingSchoolSummaries.length,
      },
      {
        label: '专业摘要',
        href:
          missingMajorSummaries.find((major) => majorSlugs.has(major.slug))?.slug
            ? `#major-summary-${missingMajorSummaries.find((major) => majorSlugs.has(major.slug))?.slug}`
            : '#missing-major-summary-heading',
        selectedDateCount: countMatchingSlugs(missingMajorSummaries, majorSlugs),
        nextCount: countMatchingSlugs(missingMajorSummaries, nextPreviewMajorSlugs),
        totalCount: missingMajorSummaries.length,
      },
      {
        label: '学校正文',
        href:
          missingSchoolSections.find((school) => schoolSlugs.has(school.slug))?.slug
            ? `#school-sections-${missingSchoolSections.find((school) => schoolSlugs.has(school.slug))?.slug}`
            : '#missing-school-sections-heading',
        selectedDateCount: countMatchingSlugs(missingSchoolSections, schoolSlugs),
        nextCount: countMatchingSlugs(missingSchoolSections, nextPreviewSchoolSlugs),
        totalCount: missingSchoolSections.length,
      },
      {
        label: '专业正文',
        href:
          missingMajorSections.find((major) => majorSlugs.has(major.slug))?.slug
            ? `#major-sections-${missingMajorSections.find((major) => majorSlugs.has(major.slug))?.slug}`
            : '#missing-major-sections-heading',
        selectedDateCount: countMatchingSlugs(missingMajorSections, majorSlugs),
        nextCount: countMatchingSlugs(missingMajorSections, nextPreviewMajorSlugs),
        totalCount: missingMajorSections.length,
      },
      {
        label: '学校相关推荐',
        href:
          missingSchoolRelatedContent.find((school) => schoolSlugs.has(school.slug))?.slug
            ? `#school-related-content-${missingSchoolRelatedContent.find((school) =>
                schoolSlugs.has(school.slug),
              )?.slug}`
            : '#missing-school-related-content-heading',
        selectedDateCount: countMatchingSlugs(missingSchoolRelatedContent, schoolSlugs),
        nextCount: countMatchingSlugs(missingSchoolRelatedContent, nextPreviewSchoolSlugs),
        totalCount: missingSchoolRelatedContent.length,
      },
      {
        label: '专业相关推荐',
        href:
          missingMajorRelatedContent.find((major) => majorSlugs.has(major.slug))?.slug
            ? `#major-related-content-${missingMajorRelatedContent.find((major) =>
                majorSlugs.has(major.slug),
              )?.slug}`
            : '#missing-major-related-content-heading',
        selectedDateCount: countMatchingSlugs(missingMajorRelatedContent, majorSlugs),
        nextCount: countMatchingSlugs(missingMajorRelatedContent, nextPreviewMajorSlugs),
        totalCount: missingMajorRelatedContent.length,
      },
    ]
      .filter((item) => item.selectedDateCount > 0 || item.nextCount > 0)
      .sort((left, right) => {
        if (left.selectedDateCount !== right.selectedDateCount) {
          return right.selectedDateCount - left.selectedDateCount;
        }

        if (left.nextCount !== right.nextCount) {
          return right.nextCount - left.nextCount;
        }

        if (left.totalCount !== right.totalCount) {
          return right.totalCount - left.totalCount;
        }

        return 0;
      });

    return gapItems[0]
      ? {
          href: `${buildPreviewDateHref(previewDate)}${gapItems[0].href}`,
          label: gapItems[0].label,
        }
      : null;
  };
  const buildSelectedDateGapHref = (itemKey: string, fallbackHref: string): string => {
    if (!selectedDatePreview) {
      return fallbackHref;
    }

    const schoolSlugByKey: Record<string, string | undefined> = {
      'school-images': schoolsMissingImages.find((school) => selectedDateSchoolSlugs.has(school.slug))?.slug,
      'school-rankings': missingSchoolRankingReferences.find((school) =>
        selectedDateSchoolSlugs.has(school.slug),
      )?.slug,
      'school-summaries': missingSchoolSummaries.find((school) =>
        selectedDateSchoolSlugs.has(school.slug),
      )?.slug,
      'school-sections': missingSchoolSections.find((school) =>
        selectedDateSchoolSlugs.has(school.slug),
      )?.slug,
      'school-related': missingSchoolRelatedContent.find((school) =>
        selectedDateSchoolSlugs.has(school.slug),
      )?.slug,
    };
    const majorSlugByKey: Record<string, string | undefined> = {
      'major-rankings': missingMajorRankingReferences.find((major) =>
        selectedDateMajorSlugs.has(major.slug),
      )?.slug,
      'major-summaries': missingMajorSummaries.find((major) =>
        selectedDateMajorSlugs.has(major.slug),
      )?.slug,
      'major-sections': missingMajorSections.find((major) =>
        selectedDateMajorSlugs.has(major.slug),
      )?.slug,
      'major-related': missingMajorRelatedContent.find((major) =>
        selectedDateMajorSlugs.has(major.slug),
      )?.slug,
    };

    const deepLinkByKey: Record<string, string | undefined> = {
      'school-images': schoolSlugByKey['school-images']
        ? `#featured-school-${schoolSlugByKey['school-images']}`
        : undefined,
      'school-rankings': schoolSlugByKey['school-rankings']
        ? `#school-ranking-reference-${schoolSlugByKey['school-rankings']}`
        : undefined,
      'major-rankings': majorSlugByKey['major-rankings']
        ? `#major-ranking-reference-${majorSlugByKey['major-rankings']}`
        : undefined,
      'school-summaries': schoolSlugByKey['school-summaries']
        ? `#school-summary-${schoolSlugByKey['school-summaries']}`
        : undefined,
      'major-summaries': majorSlugByKey['major-summaries']
        ? `#major-summary-${majorSlugByKey['major-summaries']}`
        : undefined,
      'school-sections': schoolSlugByKey['school-sections']
        ? `#school-sections-${schoolSlugByKey['school-sections']}`
        : undefined,
      'major-sections': majorSlugByKey['major-sections']
        ? `#major-sections-${majorSlugByKey['major-sections']}`
        : undefined,
      'school-related': schoolSlugByKey['school-related']
        ? `#school-related-content-${schoolSlugByKey['school-related']}`
        : undefined,
      'major-related': majorSlugByKey['major-related']
        ? `#major-related-content-${majorSlugByKey['major-related']}`
        : undefined,
    };

    return `${buildPreviewDateHref(selectedDatePreview.date)}${deepLinkByKey[itemKey] ?? fallbackHref}`;
  };
  const selectedDateGapOverviewLinks = selectedDateGapOverviewItems.map((item) => ({
    ...item,
    href: buildSelectedDateGapHref(item.key, item.href),
  }));
  const selectedDateTopPriorityGap = selectedDateGapOverviewLinks[0] ?? null;
  const scheduledPreviewDays = featuredSchedule.map((day) => {
    const scheduleDaySchoolSlugs = new Set(day.schools.map((school) => school.slug));
    const scheduleDayMajorSlugs = new Set(day.majors.map((major) => major.slug));
    const gapCount = countPreviewContentGaps(scheduleDaySchoolSlugs, scheduleDayMajorSlugs);

    return {
      ...day,
      gapCount,
      topPriorityGap: buildTopPriorityGapHref(
        day.date,
        scheduleDaySchoolSlugs,
        scheduleDayMajorSlugs,
      ),
      topPriorityGapHref: buildTopPriorityGapHref(
        day.date,
        scheduleDaySchoolSlugs,
        scheduleDayMajorSlugs,
      )?.href,
      topPriorityGapLabel: buildTopPriorityGapHref(
        day.date,
        scheduleDaySchoolSlugs,
        scheduleDayMajorSlugs,
      )?.label,
    };
  });
  const displayedScheduledPreviewDays = showScheduledGapDaysOnly
    ? scheduledPreviewDays.filter((day) => day.gapCount > 0)
    : scheduledPreviewDays;
  const scheduledGapDayCount = scheduledPreviewDays.filter((day) => day.gapCount > 0).length;
  const scheduledHighPriorityDayCount = scheduledPreviewDays.filter((day) => day.gapCount >= 2).length;
  const nearestScheduledGapDay = scheduledPreviewDays.find((day) => day.gapCount > 0) ?? null;
  const nearestScheduledTopPriorityGap = nearestScheduledGapDay?.topPriorityGap ?? {
    href: '#featured-schedule-heading',
    label: '',
  };

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

      <section aria-labelledby="content-gap-overview-heading">
        <h2 id="content-gap-overview-heading">内容缺口总览</h2>
        {contentGapOverviewItems.length === 0 ? (
          <p>当前没有待补内容缺口</p>
        ) : (
          <>
            <p>{`今日待补 ${contentGapOverviewTodayCount} 项，下一轮待补 ${contentGapOverviewNextCount} 项，总待补 ${contentGapOverviewTotalCount} 项`}</p>
            {nearestScheduledGapDay ? (
              <p>
                <a
                  href={nearestScheduledTopPriorityGap?.href ?? `${buildPreviewDateHref(nearestScheduledGapDay.date)}#featured-schedule-heading`}
                  aria-label={
                    nearestScheduledTopPriorityGap
                      ? `最近待补日期（${nearestScheduledGapDay.date}）· 优先处理${nearestScheduledTopPriorityGap.label}`
                      : undefined
                  }
                >
                  {`鏌ョ湅鏈€杩戝緟琛ユ棩鏈燂紙${nearestScheduledGapDay.date}锛?`}
                </a>
              </p>
            ) : null}
            {false && nearestScheduledGapDay && nearestScheduledTopPriorityGap ? (
              <p>
                <a href={nearestScheduledTopPriorityGap?.href ?? '#'}>
                  {/* @ts-expect-error unreachable fallback branch */}
                  {`最近待补日期（${nearestScheduledGapDay.date}）· 优先处理${nearestScheduledTopPriorityGap.label}`}
                </a>
              </p>
            ) : null}
            <ul>
              {contentGapOverviewItems.map((item) => (
                <li key={item.key}>
                  <a href={withNearestScheduledGapDate(item.key, item.href)}>
                    {`${item.todayCount > 0 ? '今日优先' : item.nextCount > 0 ? '下一轮关注' : '待补关注'} · ${item.label}：今日 ${item.todayCount}，下一轮 ${item.nextCount}，待补 ${item.totalCount}`}
                  </a>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      {selectedDatePreview ? (
        <section aria-labelledby="selected-date-gap-overview-heading">
          <h2 id="selected-date-gap-overview-heading">该日缺口优先</h2>
          {selectedDateGapOverviewItems.length === 0 ? (
            <p>该日没有需要优先处理的内容缺口</p>
          ) : (
            <>
              <p>{`该日待补 ${selectedDateGapOverviewSelectedCount} 项，下一轮待补 ${selectedDateGapOverviewNextCount} 项，总待补 ${selectedDateGapOverviewTotalCount} 项`}</p>
              {selectedDateTopPriorityGap ? (
                <p>
                  <a href={selectedDateTopPriorityGap.href}>
                    {`该日最高优先 · ${selectedDateTopPriorityGap.label}`}
                  </a>
                </p>
              ) : null}
              <p>
                <a href={`#featured-schedule-day-${selectedDatePreview.date}`}>
                  {`杩斿洖杞崲鏃ユ湡锛?${selectedDatePreview.date}锛?`}
                </a>
              </p>
              <ul>
                {selectedDateGapOverviewLinks.map((item) => (
                  <li key={item.key}>
                    <a href={item.href}>
                      {`${item.selectedDateCount > 0 ? '该日优先' : item.nextCount > 0 ? '下一轮关注' : '待补关注'} · ${item.label}：该日 ${item.selectedDateCount}，下一轮 ${item.nextCount}，待补 ${item.totalCount}`}
                    </a>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      ) : null}

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

      <section
        aria-labelledby="school-content-summary-heading"
        data-testid="school-summary-section"
      >
        <h2 id="school-content-summary-heading">学校摘要编辑</h2>

        {contentSummaryError ? <p>{contentSummaryError}</p> : null}

        {!contentSummaryError ? (
          <div>
            <p>{`已配置学校摘要 ${sortedSummarySchools.length - missingSchoolSummaries.length} 所，待补学校摘要 ${missingSchoolSummaries.length} 所`}</p>
            {showScheduledMissingSchoolSummariesOnlyHref ||
            showAllScheduledSchoolSummariesHref ? (
              <p>
                {!showScheduledMissingSchoolSummariesOnly &&
                showScheduledMissingSchoolSummariesOnlyHref ? (
                  <a href={showScheduledMissingSchoolSummariesOnlyHref}>{`仅看近期待补学校摘要（${scheduledMissingSchoolSummariesCount}）`}</a>
                ) : null}
                {showScheduledMissingSchoolSummariesOnly && showAllScheduledSchoolSummariesHref ? (
                  <a href={showAllScheduledSchoolSummariesHref}>查看全部学校摘要</a>
                ) : null}
              </p>
            ) : null}
            {displayedSummarySchools.length === 0 ? (
              <p>
                {showScheduledMissingSchoolSummariesOnly
                  ? '当前没有近期待补学校摘要'
                  : '当前没有可编辑的学校摘要'}
              </p>
            ) : null}
            {displayedSummarySchools.map((school) => (
              <div key={school.slug} id={`school-summary-${school.slug}`}>
                <ContentSummaryForm entity={school} action={updateSchoolSummaryAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section
        aria-labelledby="missing-school-summary-heading"
        data-testid="missing-school-summary-section"
      >
        <h2 id="missing-school-summary-heading">{`待补学校摘要（${missingSchoolSummaries.length}）`}</h2>

        {contentSummaryError ? null : missingSchoolSummaries.length === 0 ? (
          <p>当前没有待补学校摘要</p>
        ) : (
          <>
            <p>{`今日待补 ${missingSchoolSummaries.filter((school) => todayPreviewSchoolSlugs.has(school.slug)).length} 所，下一轮待补 ${missingSchoolSummaries.filter((school) => nextPreviewSchoolSlugs.has(school.slug)).length} 所`}</p>
            <ul>
              {missingSchoolSummaries.map((school) => (
                <li key={school.slug}>
                  <a href={`#school-summary-${school.slug}`}>{school.name}</a>
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

      <section
        aria-labelledby="major-content-summary-heading"
        data-testid="major-summary-section"
      >
        <h2 id="major-content-summary-heading">专业摘要编辑</h2>

        {contentSummaryError ? <p>{contentSummaryError}</p> : null}

        {!contentSummaryError ? (
          <div>
            <p>{`已配置专业摘要 ${sortedSummaryMajors.length - missingMajorSummaries.length} 个，待补专业摘要 ${missingMajorSummaries.length} 个`}</p>
            {showScheduledMissingMajorSummariesOnlyHref ||
            showAllScheduledMajorSummariesHref ? (
              <p>
                {!showScheduledMissingMajorSummariesOnly &&
                showScheduledMissingMajorSummariesOnlyHref ? (
                  <a href={showScheduledMissingMajorSummariesOnlyHref}>{`仅看近期待补专业摘要（${scheduledMissingMajorSummariesCount}）`}</a>
                ) : null}
                {showScheduledMissingMajorSummariesOnly && showAllScheduledMajorSummariesHref ? (
                  <a href={showAllScheduledMajorSummariesHref}>查看全部专业摘要</a>
                ) : null}
              </p>
            ) : null}
            {displayedSummaryMajors.length === 0 ? (
              <p>
                {showScheduledMissingMajorSummariesOnly
                  ? '当前没有近期待补专业摘要'
                  : '当前没有可编辑的专业摘要'}
              </p>
            ) : null}
            {displayedSummaryMajors.map((major) => (
              <div key={major.slug} id={`major-summary-${major.slug}`}>
                <ContentSummaryForm entity={major} action={updateMajorSummaryAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section
        aria-labelledby="missing-major-summary-heading"
        data-testid="missing-major-summary-section"
      >
        <h2 id="missing-major-summary-heading">{`待补专业摘要（${missingMajorSummaries.length}）`}</h2>

        {contentSummaryError ? null : missingMajorSummaries.length === 0 ? (
          <p>当前没有待补专业摘要</p>
        ) : (
          <>
            <p>{`今日待补 ${missingMajorSummaries.filter((major) => todayPreviewMajorSlugs.has(major.slug)).length} 个，下一轮待补 ${missingMajorSummaries.filter((major) => nextPreviewMajorSlugs.has(major.slug)).length} 个`}</p>
            <ul>
              {missingMajorSummaries.map((major) => (
                <li key={major.slug}>
                  <a href={`#major-summary-${major.slug}`}>{major.name}</a>
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

      <section
        aria-labelledby="school-content-sections-heading"
        data-testid="school-sections-section"
      >
        <h2 id="school-content-sections-heading">学校正文编辑</h2>

        {contentSectionError ? <p>{contentSectionError}</p> : null}

        {!contentSectionError ? (
          <div>
            <p>{`已配置学校正文 ${sortedSectionSchools.length - missingSchoolSections.length} 所，待补学校正文 ${missingSchoolSections.length} 所`}</p>
            {showScheduledMissingSchoolSectionsOnlyHref ||
            showAllScheduledSchoolSectionsHref ? (
              <p>
                {!showScheduledMissingSchoolSectionsOnly &&
                showScheduledMissingSchoolSectionsOnlyHref ? (
                  <a href={showScheduledMissingSchoolSectionsOnlyHref}>{`仅看近期待补学校正文（${scheduledMissingSchoolSectionsCount}）`}</a>
                ) : null}
                {showScheduledMissingSchoolSectionsOnly && showAllScheduledSchoolSectionsHref ? (
                  <a href={showAllScheduledSchoolSectionsHref}>查看全部学校正文</a>
                ) : null}
              </p>
            ) : null}
            {displayedSectionSchools.length === 0 ? (
              <p>
                {showScheduledMissingSchoolSectionsOnly
                  ? '当前没有近期待补学校正文'
                  : '当前没有可编辑的学校正文'}
              </p>
            ) : null}
            {displayedSectionSchools.map((school) => (
              <div key={school.slug} id={`school-sections-${school.slug}`}>
                <ContentSectionsForm entity={school} action={updateSchoolSectionsAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section
        aria-labelledby="missing-school-sections-heading"
        data-testid="missing-school-sections-section"
      >
        <h2 id="missing-school-sections-heading">{`待补学校正文（${missingSchoolSections.length}）`}</h2>

        {contentSectionError ? null : missingSchoolSections.length === 0 ? (
          <p>当前没有待补学校正文</p>
        ) : (
          <>
            <p>{`今日待补 ${missingSchoolSections.filter((school) => todayPreviewSchoolSlugs.has(school.slug)).length} 所，下一轮待补 ${missingSchoolSections.filter((school) => nextPreviewSchoolSlugs.has(school.slug)).length} 所`}</p>
            <ul>
              {missingSchoolSections.map((school) => (
                <li key={school.slug}>
                  <a href={`#school-sections-${school.slug}`}>{school.name}</a>
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

      <section
        aria-labelledby="major-content-sections-heading"
        data-testid="major-sections-section"
      >
        <h2 id="major-content-sections-heading">专业正文编辑</h2>

        {contentSectionError ? <p>{contentSectionError}</p> : null}

        {!contentSectionError ? (
          <div>
            <p>{`已配置专业正文 ${sortedSectionMajors.length - missingMajorSections.length} 个，待补专业正文 ${missingMajorSections.length} 个`}</p>
            {showScheduledMissingMajorSectionsOnlyHref ||
            showAllScheduledMajorSectionsHref ? (
              <p>
                {!showScheduledMissingMajorSectionsOnly &&
                showScheduledMissingMajorSectionsOnlyHref ? (
                  <a href={showScheduledMissingMajorSectionsOnlyHref}>{`仅看近期待补专业正文（${scheduledMissingMajorSectionsCount}）`}</a>
                ) : null}
                {showScheduledMissingMajorSectionsOnly && showAllScheduledMajorSectionsHref ? (
                  <a href={showAllScheduledMajorSectionsHref}>查看全部专业正文</a>
                ) : null}
              </p>
            ) : null}
            {displayedSectionMajors.length === 0 ? (
              <p>
                {showScheduledMissingMajorSectionsOnly
                  ? '当前没有近期待补专业正文'
                  : '当前没有可编辑的专业正文'}
              </p>
            ) : null}
            {displayedSectionMajors.map((major) => (
              <div key={major.slug} id={`major-sections-${major.slug}`}>
                <ContentSectionsForm entity={major} action={updateMajorSectionsAction} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section
        aria-labelledby="missing-major-sections-heading"
        data-testid="missing-major-sections-section"
      >
        <h2 id="missing-major-sections-heading">{`待补专业正文（${missingMajorSections.length}）`}</h2>

        {contentSectionError ? null : missingMajorSections.length === 0 ? (
          <p>当前没有待补专业正文</p>
        ) : (
          <>
            <p>{`今日待补 ${missingMajorSections.filter((major) => todayPreviewMajorSlugs.has(major.slug)).length} 个，下一轮待补 ${missingMajorSections.filter((major) => nextPreviewMajorSlugs.has(major.slug)).length} 个`}</p>
            <ul>
              {missingMajorSections.map((major) => (
                <li key={major.slug}>
                  <a href={`#major-sections-${major.slug}`}>{major.name}</a>
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

      <section
        aria-labelledby="school-related-content-heading"
        data-testid="school-related-content-section"
      >
        <h2 id="school-related-content-heading">学校相关推荐</h2>

        {relatedContentError ? <p>{relatedContentError}</p> : null}

        {!relatedContentError ? (
          <div>
            <p>{`已配置学校相关推荐 ${configuredSchoolRelatedContentCount} 所，待补学校相关推荐 ${missingSchoolRelatedContent.length} 所`}</p>
            {showMissingSchoolRelatedOnlyHref ||
            showAllSchoolRelatedContentHref ||
            showScheduledMissingSchoolRelatedOnlyHref ||
            showAllScheduledSchoolRelatedContentHref ? (
              <p>
                {!showMissingSchoolRelatedOnly && showMissingSchoolRelatedOnlyHref ? (
                  <a href={showMissingSchoolRelatedOnlyHref}>{`仅看待补学校相关推荐（${missingSchoolRelatedContent.length}）`}</a>
                ) : null}
                {!showScheduledMissingSchoolRelatedOnly && showScheduledMissingSchoolRelatedOnlyHref ? (
                  <>
                    {!showMissingSchoolRelatedOnly && showMissingSchoolRelatedOnlyHref ? ' ' : null}
                    <a href={showScheduledMissingSchoolRelatedOnlyHref}>{`仅看近期待补学校相关推荐（${scheduledMissingSchoolRelatedCount}）`}</a>
                  </>
                ) : null}
                {showMissingSchoolRelatedOnly && showAllSchoolRelatedContentHref ? (
                  <a href={showAllSchoolRelatedContentHref}>查看全部学校相关推荐</a>
                ) : null}
                {showScheduledMissingSchoolRelatedOnly && showAllScheduledSchoolRelatedContentHref ? (
                  <>
                    {showMissingSchoolRelatedOnly && showAllSchoolRelatedContentHref ? ' ' : null}
                    <a href={showAllScheduledSchoolRelatedContentHref}>查看全部近期待补学校相关推荐</a>
                  </>
                ) : null}
              </p>
            ) : null}
            {displayedRelatedSchools.length === 0 ? (
              <p>
                {showScheduledMissingSchoolRelatedOnly
                  ? '当前没有近期待补学校相关推荐'
                  : showMissingSchoolRelatedOnly
                    ? '当前没有待补学校相关推荐'
                    : '当前没有可编辑的学校相关推荐'}
              </p>
            ) : null}
            {displayedRelatedSchools.map((school) => (
              <div key={school.slug} id={`school-related-content-${school.slug}`}>
                <RelatedContentForm
                  entity={school}
                  fieldName="relatedMajors"
                  relatedSlugs={school.relatedMajors}
                  action={updateSchoolRelatedContentAction}
                />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section
        aria-labelledby="missing-school-related-content-heading"
        data-testid="missing-school-related-content-section"
      >
        <h2 id="missing-school-related-content-heading">{`待补学校相关推荐（${missingSchoolRelatedContent.length}）`}</h2>

        {relatedContentError ? null : missingSchoolRelatedContent.length === 0 ? (
          <p>当前没有待补学校相关推荐</p>
        ) : (
          <>
            <p>{`今日待补 ${todayMissingSchoolRelatedCount} 所，下一轮待补 ${nextMissingSchoolRelatedCount} 所`}</p>
            <ul>
              {missingSchoolRelatedContent.map((school) => (
                <li key={school.slug}>
                  <a href={`#school-related-content-${school.slug}`}>{school.name}</a>
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

      <section
        aria-labelledby="major-related-content-heading"
        data-testid="major-related-content-section"
      >
        <h2 id="major-related-content-heading">专业相关推荐</h2>

        {relatedContentError ? <p>{relatedContentError}</p> : null}

        {!relatedContentError ? (
          <div>
            <p>{`已配置专业相关推荐 ${configuredMajorRelatedContentCount} 个，待补专业相关推荐 ${missingMajorRelatedContent.length} 个`}</p>
            {showMissingMajorRelatedOnlyHref ||
            showAllMajorRelatedContentHref ||
            showScheduledMissingMajorRelatedOnlyHref ||
            showAllScheduledMajorRelatedContentHref ? (
              <p>
                {!showMissingMajorRelatedOnly && showMissingMajorRelatedOnlyHref ? (
                  <a href={showMissingMajorRelatedOnlyHref}>{`仅看待补专业相关推荐（${missingMajorRelatedContent.length}）`}</a>
                ) : null}
                {!showScheduledMissingMajorRelatedOnly && showScheduledMissingMajorRelatedOnlyHref ? (
                  <>
                    {!showMissingMajorRelatedOnly && showMissingMajorRelatedOnlyHref ? ' ' : null}
                    <a href={showScheduledMissingMajorRelatedOnlyHref}>{`仅看近期待补专业相关推荐（${scheduledMissingMajorRelatedCount}）`}</a>
                  </>
                ) : null}
                {showMissingMajorRelatedOnly && showAllMajorRelatedContentHref ? (
                  <a href={showAllMajorRelatedContentHref}>查看全部专业相关推荐</a>
                ) : null}
                {showScheduledMissingMajorRelatedOnly && showAllScheduledMajorRelatedContentHref ? (
                  <>
                    {showMissingMajorRelatedOnly && showAllMajorRelatedContentHref ? ' ' : null}
                    <a href={showAllScheduledMajorRelatedContentHref}>查看全部近期待补专业相关推荐</a>
                  </>
                ) : null}
              </p>
            ) : null}
            {displayedRelatedMajors.length === 0 ? (
              <p>
                {showScheduledMissingMajorRelatedOnly
                  ? '当前没有近期待补专业相关推荐'
                  : showMissingMajorRelatedOnly
                    ? '当前没有待补专业相关推荐'
                    : '当前没有可编辑的专业相关推荐'}
              </p>
            ) : null}
            {displayedRelatedMajors.map((major) => (
              <div key={major.slug} id={`major-related-content-${major.slug}`}>
                <RelatedContentForm
                  entity={major}
                  fieldName="relatedSchools"
                  relatedSlugs={major.relatedSchools}
                  action={updateMajorRelatedContentAction}
                />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section
        aria-labelledby="missing-major-related-content-heading"
        data-testid="missing-major-related-content-section"
      >
        <h2 id="missing-major-related-content-heading">{`待补专业相关推荐（${missingMajorRelatedContent.length}）`}</h2>

        {relatedContentError ? null : missingMajorRelatedContent.length === 0 ? (
          <p>当前没有待补专业相关推荐</p>
        ) : (
          <>
            <p>{`今日待补 ${todayMissingMajorRelatedCount} 个，下一轮待补 ${nextMissingMajorRelatedCount} 个`}</p>
            <ul>
              {missingMajorRelatedContent.map((major) => (
                <li key={major.slug}>
                  <a href={`#major-related-content-${major.slug}`}>{major.name}</a>
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

      <section aria-labelledby="school-ranking-reference-heading">
        <h2 id="school-ranking-reference-heading">学校榜单引用</h2>

        {rankingReferenceError ? <p>{rankingReferenceError}</p> : null}

        {!rankingReferenceError ? (
          <div>
            <p>{`已配置学校榜单 ${configuredSchoolRankingReferenceCount} 所，待补学校榜单 ${missingSchoolRankingReferences.length} 所`}</p>
            {showMissingSchoolRankingsOnlyHref ||
            showAllSchoolRankingReferencesHref ||
            showScheduledMissingSchoolRankingsOnlyHref ||
            showAllScheduledSchoolRankingReferencesHref ? (
              <p>
                {!showMissingSchoolRankingsOnly && showMissingSchoolRankingsOnlyHref ? (
                  <a href={showMissingSchoolRankingsOnlyHref}>{`仅看待补学校榜单（${missingSchoolRankingReferences.length}）`}</a>
                ) : null}
                {!showScheduledMissingSchoolRankingsOnly &&
                showScheduledMissingSchoolRankingsOnlyHref ? (
                  <>
                    {!showMissingSchoolRankingsOnly && showMissingSchoolRankingsOnlyHref ? ' ' : null}
                    <a href={showScheduledMissingSchoolRankingsOnlyHref}>{`仅看近期待补学校榜单（${scheduledMissingSchoolRankingCount}）`}</a>
                  </>
                ) : null}
                {showMissingSchoolRankingsOnly && showAllSchoolRankingReferencesHref ? (
                  <a href={showAllSchoolRankingReferencesHref}>查看全部学校榜单</a>
                ) : null}
                {showScheduledMissingSchoolRankingsOnly &&
                showAllScheduledSchoolRankingReferencesHref ? (
                  <>
                    {showMissingSchoolRankingsOnly && showAllSchoolRankingReferencesHref ? ' ' : null}
                    <a href={showAllScheduledSchoolRankingReferencesHref}>查看全部近期待补学校榜单</a>
                  </>
                ) : null}
              </p>
            ) : null}
            {displayedSchoolRankingReferences.length === 0 ? (
              <p>
                {showScheduledMissingSchoolRankingsOnly
                  ? '当前没有近期待补学校榜单'
                  : showMissingSchoolRankingsOnly
                    ? '当前没有待补学校榜单'
                    : '当前没有可编辑的学校榜单'}
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
            {showMissingMajorRankingsOnlyHref ||
            showAllMajorRankingReferencesHref ||
            showScheduledMissingMajorRankingsOnlyHref ||
            showAllScheduledMajorRankingReferencesHref ? (
              <p>
                {!showMissingMajorRankingsOnly && showMissingMajorRankingsOnlyHref ? (
                  <a href={showMissingMajorRankingsOnlyHref}>{`仅看待补专业榜单（${missingMajorRankingReferences.length}）`}</a>
                ) : null}
                {!showScheduledMissingMajorRankingsOnly &&
                showScheduledMissingMajorRankingsOnlyHref ? (
                  <>
                    {!showMissingMajorRankingsOnly && showMissingMajorRankingsOnlyHref ? ' ' : null}
                    <a href={showScheduledMissingMajorRankingsOnlyHref}>{`仅看近期待补专业榜单（${scheduledMissingMajorRankingCount}）`}</a>
                  </>
                ) : null}
                {showMissingMajorRankingsOnly && showAllMajorRankingReferencesHref ? (
                  <a href={showAllMajorRankingReferencesHref}>查看全部专业榜单</a>
                ) : null}
                {showScheduledMissingMajorRankingsOnly &&
                showAllScheduledMajorRankingReferencesHref ? (
                  <>
                    {showMissingMajorRankingsOnly && showAllMajorRankingReferencesHref ? ' ' : null}
                    <a href={showAllScheduledMajorRankingReferencesHref}>查看全部近期待补专业榜单</a>
                  </>
                ) : null}
              </p>
            ) : null}
            {displayedMajorRankingReferences.length === 0 ? (
              <p>
                {showScheduledMissingMajorRankingsOnly
                  ? '当前没有近期待补专业榜单'
                  : showMissingMajorRankingsOnly
                    ? '当前没有待补专业榜单'
                    : '当前没有可编辑的专业榜单'}
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
          {showMissingSchoolRankingsOnly ? (
            <input type="hidden" name="missing_school_rankings" value="1" />
          ) : null}
          {showMissingMajorRankingsOnly ? (
            <input type="hidden" name="missing_major_rankings" value="1" />
          ) : null}
          {showScheduledMissingSchoolRankingsOnly ? (
            <input type="hidden" name="scheduled_missing_school_rankings" value="1" />
          ) : null}
          {showScheduledMissingMajorRankingsOnly ? (
            <input type="hidden" name="scheduled_missing_major_rankings" value="1" />
          ) : null}
          {showMissingSchoolRelatedOnly ? (
            <input type="hidden" name="missing_school_related" value="1" />
          ) : null}
          {showMissingMajorRelatedOnly ? (
            <input type="hidden" name="missing_major_related" value="1" />
          ) : null}
          {showScheduledMissingSchoolRelatedOnly ? (
            <input type="hidden" name="scheduled_missing_school_related" value="1" />
          ) : null}
          {showScheduledMissingMajorRelatedOnly ? (
            <input type="hidden" name="scheduled_missing_major_related" value="1" />
          ) : null}
          {showScheduledMissingSchoolSummariesOnly ? (
            <input type="hidden" name="scheduled_missing_school_summaries" value="1" />
          ) : null}
          {showScheduledMissingMajorSummariesOnly ? (
            <input type="hidden" name="scheduled_missing_major_summaries" value="1" />
          ) : null}
          {showScheduledMissingSchoolSectionsOnly ? (
            <input type="hidden" name="scheduled_missing_school_sections" value="1" />
          ) : null}
          {showScheduledMissingMajorSectionsOnly ? (
            <input type="hidden" name="scheduled_missing_major_sections" value="1" />
          ) : null}
          {showScheduledGapDaysOnly ? (
            <input type="hidden" name="scheduled_gap_days" value="1" />
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

        {featuredContentError ? null : displayedScheduledPreviewDays.length === 0 ? (
          <>
            {showScheduledGapDaysOnly && showAllScheduledGapDaysHref ? (
              <p>
                <a href={showAllScheduledGapDaysHref}>查看全部日期</a>
              </p>
            ) : null}
            <p>{showScheduledGapDaysOnly ? '未来 7 天没有待补日期' : '当前没有未来轮换预览'}</p>
          </>
        ) : (
          <div>
            <p>{`未来 7 天中有 ${scheduledGapDayCount} 天待补内容，其中 ${scheduledHighPriorityDayCount} 天待补 2 项及以上`}</p>
            {showScheduledGapDaysOnlyHref || showAllScheduledGapDaysHref ? (
              <p>
                {!showScheduledGapDaysOnly && showScheduledGapDaysOnlyHref ? (
                  <a href={showScheduledGapDaysOnlyHref}>{`仅看待补日期（${scheduledGapDayCount}）`}</a>
                ) : null}
                {showScheduledGapDaysOnly && showAllScheduledGapDaysHref ? (
                  <a href={showAllScheduledGapDaysHref}>查看全部日期</a>
                ) : null}
              </p>
            ) : null}
            {displayedScheduledPreviewDays.map((day) => (
              <article key={day.date} id={`featured-schedule-day-${day.date}`}>
                <h3>
                  {day.date === highlightedScheduleDate ? (
                    day.date
                  ) : (
                    <a href={buildPreviewDateHref(day.date)}>
                      {day.date}
                    </a>
                  )}
                </h3>
                <p>{day.weekday}</p>
                {day.date === highlightedScheduleDate ? <p>当前查看</p> : null}
                <p>{`该日待补 ${day.gapCount} 项`}</p>
                {day.gapCount >= 2 ? <p>优先关注</p> : null}
                {day.gapCount === 1 ? <p>少量待补</p> : null}
                {day.gapCount === 0 ? <p>内容已齐备</p> : null}
                <p>学校</p>
                {day.gapCount > 0 ? (
                  <p>
                    <a href={`${buildPreviewDateHref(day.date)}#selected-date-gap-overview-heading`}>
                      澶勭悊璇ユ棩缂哄彛
                    </a>
                  </p>
                ) : null}
                {day.topPriorityGap ? (
                  <p>
                    <a href={day.topPriorityGap.href}>{`优先处理${day.topPriorityGapLabel}`}</a>{' '}
                    <a href={day.topPriorityGapHref}>鏌ョ湅鏈€浼樺厛缂哄彛</a>
                  </p>
                ) : null}
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
