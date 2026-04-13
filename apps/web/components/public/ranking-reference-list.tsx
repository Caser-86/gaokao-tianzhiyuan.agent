import type { RankingReference } from '../../lib/public-content-api';

type RankingReferenceListProps = {
  references: RankingReference[];
};

export default function RankingReferenceList({ references }: RankingReferenceListProps) {
  if (references.length === 0) {
    return null;
  }

  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <h2 className="panel-title">{'\u53c2\u8003\u699c\u5355'}</h2>
      <p>{'\u4e0d\u540c\u699c\u5355\u53e3\u5f84\u4e0d\u540c\uff0c\u7ed3\u679c\u4ec5\u4f9b\u53c2\u8003\u3002'}</p>
      <div className="section-grid">
        {references.map((reference) => (
          <article
            key={`${reference.source}-${reference.year}-${reference.label}`}
            className="section-card"
          >
            <p>{`${reference.source} ${reference.year}`}</p>
            <strong>{reference.label}</strong>
            {reference.scope ? <p>{reference.scope}</p> : null}
            {reference.note ? <p>{reference.note}</p> : null}
            {reference.url ? (
              <a href={reference.url} target="_blank" rel="noreferrer">
                {'\u67e5\u770b\u6765\u6e90\u539f\u6587'}
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
