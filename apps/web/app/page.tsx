import Link from 'next/link';

import SearchEntry from '../components/public/search-entry';
import { listPlatformProducts } from '../lib/platform-api';
import { getSearchEntry, listMajors, listSchools } from '../lib/public-content-api';

export default async function HomePage() {
  try {
    const [searchEntry, schoolPayload, majorPayload, productPayload] = await Promise.all([
      getSearchEntry(),
      listSchools(),
      listMajors(),
      listPlatformProducts().catch(() => ({ items: [] })),
    ]);

    return (
      <main className="page-shell">
        <SearchEntry
          title={searchEntry.title}
          description={searchEntry.description}
          quickPrompts={searchEntry.quickPrompts}
        />

        <section className="grid two" style={{ marginTop: 28 }}>
          <article className="panel">
            <h2 className="panel-title">学校速查</h2>
            <div className="catalog-list">
              {schoolPayload.items.map((school) => (
                <Link key={school.slug} href={`/schools/${school.slug}`} className="catalog-card">
                  <strong>{school.name}</strong>
                  <p>{school.summary}</p>
                  <div className="meta">
                    <span>{school.region}</span>
                    <span>{school.city}</span>
                    {school.tags.map((tag) => (
                      <span key={tag}>{tag}</span>
                    ))}
                  </div>
                </Link>
              ))}
            </div>
          </article>

          <article className="panel">
            <h2 className="panel-title">专业速查</h2>
            <div className="catalog-list">
              {majorPayload.items.map((major) => (
                <Link key={major.slug} href={`/majors/${major.slug}`} className="catalog-card">
                  <strong>{major.name}</strong>
                  <p>{major.summary}</p>
                  <div className="meta">
                    <span>{major.discipline}</span>
                    {major.recommendedRegions.slice(0, 3).map((region) => (
                      <span key={region}>{region}</span>
                    ))}
                  </div>
                </Link>
              ))}
            </div>
          </article>
        </section>

        <section className="panel" style={{ marginTop: 28 }}>
          <h2 className="panel-title">精选服务</h2>
          {productPayload.items.length === 0 ? (
            <p>平台服务暂时不可用，请稍后再试。</p>
          ) : (
            <div className="catalog-list">
              {productPayload.items.map((product) => (
                <article key={product.slug} className="catalog-card">
                  <strong>{product.name}</strong>
                  <p>{product.description}</p>
                  <div className="meta">
                    {product.entitlements.map((entitlement) => (
                      <span key={entitlement}>{entitlement}</span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    );
  } catch {
    return (
      <main className="page-shell">
        <section className="panel">
          <h1 className="panel-title">公开内容暂时不可用</h1>
          <p>公开内容加载失败，请稍后重试。</p>
        </section>
      </main>
    );
  }
}
