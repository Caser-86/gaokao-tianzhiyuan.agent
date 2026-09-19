import type { ChatEvidenceItem } from "../../lib/chat-api";

type EvidenceListProps = {
  evidence?: unknown;
  evidenceRefs?: unknown;
};

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === "string" && value.trim().length > 0;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;

const isRenderableEvidenceItem = (
  value: unknown,
): value is ChatEvidenceItem =>
  isRecord(value) &&
  isNonEmptyString(value.id) &&
  isNonEmptyString(value.source_name) &&
  isNonEmptyString(value.text);

const isUnsafeIpv4Literal = (hostname: string): boolean => {
  const parts = hostname.split(".");
  if (parts.length !== 4 || !parts.every((part) => /^\d+$/.test(part))) {
    return false;
  }
  const octets = parts.map(Number);
  if (octets.some((octet) => octet < 0 || octet > 255)) {
    return true;
  }
  const [first, second] = octets;
  return (
    first === 0 ||
    first === 10 ||
    first === 127 ||
    (first === 100 && second >= 64 && second <= 127) ||
    (first === 169 && second === 254) ||
    (first === 172 && second >= 16 && second <= 31) ||
    (first === 192 && second === 168) ||
    (first >= 224)
  );
};

const isSafeHttpUrl = (value: unknown): value is string => {
  if (!isNonEmptyString(value) || value.length > 2048) {
    return false;
  }
  if ([...value].some((character) => {
    const code = character.charCodeAt(0);
    return code < 32 || code === 127;
  })) {
    return false;
  }

  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    return false;
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    return false;
  }
  if (parsed.username || parsed.password || !parsed.hostname) {
    return false;
  }

  const hostname = parsed.hostname
    .replace(/^\[|\]$/g, "")
    .replace(/\.$/, "")
    .toLowerCase();
  return (
    hostname !== "localhost" &&
    hostname !== "::1" &&
    !/^\d+$/.test(hostname) &&
    !isUnsafeIpv4Literal(hostname) &&
    ![".internal", ".intranet", ".lan", ".local", ".localhost"].some(
      (suffix) => hostname.endsWith(suffix),
    )
  );
};

const getEvidenceMeta = (item: ChatEvidenceItem) =>
  [item.source_name, item.year, item.province, item.data_status]
    .filter(
      (value) =>
        typeof value === "number" ||
        (typeof value === "string" && value.trim().length > 0),
    )
    .map(String);

const getSourceBoundaryCopy = (sourceUrl: unknown): string =>
  isNonEmptyString(sourceUrl)
    ? "来源地址未通过安全校验，当前不提供可点击外链。"
    : "演示资料：暂无可打开来源，回答不会把它当作外部网页事实。";

export default function EvidenceList({
  evidence,
  evidenceRefs,
}: EvidenceListProps) {
  const referenceIds = Array.isArray(evidenceRefs)
    ? new Set(evidenceRefs.filter(isNonEmptyString))
    : null;
  const renderableEvidence = (Array.isArray(evidence) ? evidence : [])
    .filter(isRenderableEvidenceItem)
    .filter((item) => referenceIds?.has(item.id) ?? false);

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
                {getSourceBoundaryCopy(item.source_url)}
              </div>
            )}
            <div className="evidence-id">引用 ID：{item.id}</div>
          </article>
        ))}
      </div>
    </section>
  );
}
