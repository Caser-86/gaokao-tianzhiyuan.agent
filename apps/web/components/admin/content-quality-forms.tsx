import type {
  AdminContentSummaryEntity,
} from '../../lib/admin-content-summary-api';
import type {
  AdminContentSection,
  AdminContentSectionsEntity,
} from '../../lib/admin-content-sections-api';
import type { AdminRelatedMajorEntity, AdminRelatedSchoolEntity } from '../../lib/admin-related-content-api';
import type { AdminRankingReferenceEntity } from '../../lib/admin-ranking-reference-api';
import AdminActionForm, { type AdminAction } from './admin-action-form';

export function RankingReferenceForm({
  entity,
  entityLabel,
  action,
  submitLabel,
}: {
  entity: AdminRankingReferenceEntity;
  entityLabel: string;
  action: AdminAction;
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
    <AdminActionForm action={action}>
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
    </AdminActionForm>
  );
}

export function ContentSummaryForm({
  entity,
  action,
}: {
  entity: AdminContentSummaryEntity;
  action: AdminAction;
}) {
  return (
    <AdminActionForm action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <h3>{entity.name}</h3>
      <p>{entity.slug}</p>
      <label>
        摘要
        <textarea name="summary" defaultValue={entity.summary} />
      </label>
      <button type="submit">保存摘要</button>
    </AdminActionForm>
  );
}

export function ContentSectionsForm({
  entity,
  action,
}: {
  entity: AdminContentSectionsEntity;
  action: AdminAction;
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
    <AdminActionForm action={action}>
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
    </AdminActionForm>
  );
}

export function RelatedContentForm({
  entity,
  fieldName,
  relatedSlugs,
  action,
}: {
  entity: AdminRelatedSchoolEntity | AdminRelatedMajorEntity;
  fieldName: 'relatedMajors' | 'relatedSchools';
  relatedSlugs: string[];
  action: AdminAction;
}) {
  return (
    <AdminActionForm action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <h3>{entity.name}</h3>
      <p>{entity.slug}</p>
      <label>
        关联 slug
        <textarea name={fieldName} defaultValue={relatedSlugs.join('\n')} />
      </label>
      <button type="submit">保存相关推荐</button>
    </AdminActionForm>
  );
}
