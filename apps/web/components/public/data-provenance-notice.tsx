import type { DataProvenance } from '../../lib/public-content-api';

type DataProvenanceNoticeProps = {
  provenance?: DataProvenance;
};

const STATUS_LABELS: Record<DataProvenance['status'], string> = {
  demo: '演示数据',
  secondary: '二手整理数据',
  official: '官方数据',
};

export default function DataProvenanceNotice({ provenance }: DataProvenanceNoticeProps) {
  if (!provenance) {
    return null;
  }

  return (
    <aside className="data-provenance" aria-label="数据来源声明">
      <div className="data-provenance-heading">
        <strong>{STATUS_LABELS[provenance.status]}</strong>
        <span>{`更新时间：${provenance.updatedAt}`}</span>
      </div>
      <p>{provenance.disclaimer}</p>
      <div className="data-provenance-meta">
        <span>{`来源：${provenance.sourceName}`}</span>
        <span>{`适用范围：${provenance.region}`}</span>
        {provenance.applicableYear ? <span>{`适用年份：${provenance.applicableYear}`}</span> : null}
        {provenance.sourceUrl ? (
          <a href={provenance.sourceUrl} target="_blank" rel="noreferrer">
            {'查看来源'}
          </a>
        ) : null}
      </div>
    </aside>
  );
}
