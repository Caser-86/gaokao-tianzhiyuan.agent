import type {
  AdminFeaturedMajor,
  AdminFeaturedPreviewDay,
  AdminFeaturedPreviewItem,
  AdminFeaturedSchool,
  AdminRotationRule,
} from '../../lib/admin-featured-content-api';

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
  highlightedScheduleDate?: string;
  selectedPreviewDateValue: string;
  selectedDatePreview: AdminFeaturedPreviewDay | null;
  selectedDateError?: string;
  todayPreviewDateHref?: string;
  previousPreviewDateHref?: string;
  nextPreviewDateHref?: string;
  queueError?: string;
  featuredContentError?: string;
  approveAction: (formData: FormData) => Promise<void>;
  rejectAction: (formData: FormData) => Promise<void>;
  updateFeaturedSchoolAction: (formData: FormData) => Promise<void>;
  updateFeaturedMajorAction: (formData: FormData) => Promise<void>;
  updateSchoolRotationAction: (formData: FormData) => Promise<void>;
  updateMajorRotationAction: (formData: FormData) => Promise<void>;
};

const cards = ['待审核内容', '最近发布', '抓取状态'];

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
          <span>{item.name}</span>
          <span>{item.slug}</span>
          {imageAvailabilityBySlug ? (
            <span>{imageAvailabilityBySlug[item.slug] ? '已配置图片' : '未配置图片'}</span>
          ) : null}
        </li>
      ))}
    </ul>
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
  highlightedScheduleDate,
  selectedPreviewDateValue,
  selectedDatePreview,
  selectedDateError,
  todayPreviewDateHref,
  previousPreviewDateHref,
  nextPreviewDateHref,
  queueError,
  featuredContentError,
  approveAction,
  rejectAction,
  updateFeaturedSchoolAction,
  updateFeaturedMajorAction,
  updateSchoolRotationAction,
  updateMajorRotationAction,
}: DashboardShellProps) {
  const showSelectedDateHelper =
    !selectedPreviewDateValue && !selectedDatePreview && !selectedDateError;
  const schoolImageAvailabilityBySlug = Object.fromEntries(
    featuredSchools.map((school) => [school.slug, Boolean(school.heroImageUrl)]),
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

        {featuredContentError ? <p>{featuredContentError}</p> : null}

        {!featuredContentError ? (
          <div>
            {featuredSchools.map((school) => (
              <div key={school.slug}>
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
                    <a href={school.heroImageUrl} target="_blank" rel="noreferrer">
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
                    <a href={`/admin?preview_date=${day.date}`}>{day.date}</a>
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
