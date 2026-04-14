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
  queueError,
  featuredContentError,
  approveAction,
  rejectAction,
  updateFeaturedSchoolAction,
  updateFeaturedMajorAction,
  updateSchoolRotationAction,
  updateMajorRotationAction,
}: DashboardShellProps) {
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
              <form key={school.slug} action={updateFeaturedSchoolAction}>
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
                <button type="submit">保存</button>
              </form>
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
              <input type="number" name="frequencyDays" min={1} defaultValue={schoolRotation.frequencyDays} />
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
              <input type="number" name="frequencyDays" min={1} defaultValue={majorRotation.frequencyDays} />
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
          <ul>
            {featuredSchoolPreview.map((school) => (
              <li key={school.slug}>
                <span>{school.name}</span>
                <span>{school.slug}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="featured-major-preview-heading">
        <h2 id="featured-major-preview-heading">今日展示专业</h2>

        {featuredContentError ? null : featuredMajorPreview.length === 0 ? (
          <p>当前没有可展示专业</p>
        ) : (
          <ul>
            {featuredMajorPreview.map((major) => (
              <li key={major.slug}>
                <span>{major.name}</span>
                <span>{major.slug}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="next-featured-school-preview-heading">
        <h2 id="next-featured-school-preview-heading">下一轮展示学校</h2>

        {featuredContentError ? null : nextFeaturedSchoolPreview.length === 0 ? (
          <p>当前没有下一轮展示学校</p>
        ) : (
          <ul>
            {nextFeaturedSchoolPreview.map((school) => (
              <li key={school.slug}>
                <span>{school.name}</span>
                <span>{school.slug}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="next-featured-major-preview-heading">
        <h2 id="next-featured-major-preview-heading">下一轮展示专业</h2>

        {featuredContentError ? null : nextFeaturedMajorPreview.length === 0 ? (
          <p>当前没有下一轮展示专业</p>
        ) : (
          <ul>
            {nextFeaturedMajorPreview.map((major) => (
              <li key={major.slug}>
                <span>{major.name}</span>
                <span>{major.slug}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="featured-schedule-heading">
        <h2 id="featured-schedule-heading">未来 7 天轮换预览</h2>

        {featuredContentError ? null : featuredSchedule.length === 0 ? (
          <p>当前没有未来轮换预览</p>
        ) : (
          <div>
            {featuredSchedule.map((day) => (
              <article key={day.date}>
                <h3>{day.date}</h3>
                <p>{day.weekday}</p>
                <p>学校</p>
                {day.schools.length === 0 ? (
                  <p>当天没有展示学校</p>
                ) : (
                  <ul>
                    {day.schools.map((school) => (
                      <li key={`${day.date}-${school.slug}`}>{school.slug}</li>
                    ))}
                  </ul>
                )}
                <p>专业</p>
                {day.majors.length === 0 ? (
                  <p>当天没有展示专业</p>
                ) : (
                  <ul>
                    {day.majors.map((major) => (
                      <li key={`${day.date}-${major.slug}`}>{major.slug}</li>
                    ))}
                  </ul>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
