import type { ChatEvidenceItem } from "../../lib/chat-api";

type EvidenceListProps = {
  evidence: ChatEvidenceItem[];
};

const isSafeHttpUrl = (value: string | null | undefined): value is string =>
  typeof value === "string" && /^https?:\/\//i.test(value);

const getEvidenceMeta = (item: ChatEvidenceItem) =>
  [item.source_name, item.year, item.province, item.data_status]
    .filter((value) => value !== null && value !== undefined && String(value).trim())
    .map(String);

export default function EvidenceList({ evidence }: EvidenceListProps) {
  const renderableEvidence = evidence.filter(
    (item) =>
      typeof item.id === "string" &&
      item.id.trim() &&
      typeof item.source_name === "string" &&
      item.source_name.trim() &&
      typeof item.text === "string" &&
      item.text.trim(),
  );

  if (!renderableEvidence.length) {
    return null;
  }

  return (
    <section aria-labelledby="evidence-heading" className="evidence-section">
      <div className="evidence-heading-row">
        <div>
          <div className="meta-label">基于目录证据</div>
          <h3 id="evidence-heading">证据与引用</h3>
        </div>
        <span className="evidence-count">{renderableEvidence.length} 条</span>
      </div>
      <div className="catalog-list">
        {renderableEvidence.map((item, index) => (
          <article key={`${item.id}-${index}`} className="catalog-card evidence-card">
            <div className="meta">
              {getEvidenceMeta(item).map((value, metaIndex) => (
                <span key={`${item.id}-meta-${metaIndex}`}>{value}</span>
              ))}
            </div>
            <p>{item.text}</p>
            {isSafeHttpUrl(item.source_url) ? (
              <a
                className="evidence-source-link"
                href={item.source_url}
                target="_blank"
                rel="noreferrer"
              >
                打开来源
              </a>
            ) : (
              <div className="evidence-boundary">
                演示资料：暂无可打开来源，回答不会把它当作外部网页事实。
              </div>
            )}
            <div className="evidence-id">引用 ID：{item.id}</div>
          </article>
        ))}
      </div>
    </section>
  );
}
