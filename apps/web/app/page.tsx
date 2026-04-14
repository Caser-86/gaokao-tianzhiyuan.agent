import Link from 'next/link';

import PlatformHomepageShelf from '../components/public/platform-homepage-shelf';
import PlatformUnavailablePanel from '../components/public/platform-unavailable-panel';
import SearchEntry from '../components/public/search-entry';
import { type PlatformProduct, listPlatformProducts } from '../lib/platform-api';
import { getSearchEntry, listMajors, listSchools } from '../lib/public-content-api';

const getApiBaseUrl = () => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';

export default async function HomePage() {
  try {
    const apiBaseUrl = getApiBaseUrl();
    const [searchEntry, schoolPayload, majorPayload] = await Promise.all([
      getSearchEntry(),
      listSchools(),
      listMajors(),
    ]);
    let productPayload: { items: PlatformProduct[] } | null = null;

    try {
      productPayload = await listPlatformProducts();
    } catch {
      productPayload = null;
    }

    return (
      <main className="page-shell">
        <SearchEntry
          apiBaseUrl={apiBaseUrl}
          title={searchEntry.title}
          description={searchEntry.description}
          quickPrompts={searchEntry.quickPrompts}
        />

        <section className="grid two" style={{ marginTop: 28 }}>
          <article id="school-catalog" className="panel">
            <h2 className="panel-title">{'学校速查'}</h2>
            <div className="catalog-list">
              {schoolPayload.items.map((school) => (
                <Link key={school.slug} href={`/schools/${school.slug}`} className="catalog-card">
                  {school.heroImageUrl ? (
                    <img
                      src={school.heroImageUrl}
                      alt={school.name}
                      style={{ width: '100%', aspectRatio: '16 / 9', objectFit: 'cover' }}
                    />
                  ) : null}
                  <strong>{school.name}</strong>
                  <p>{school.summary}</p>
                  <div className="meta">
                    <span>{school.region}</span>
                    <span>{school.city}</span>
                    {school.tags.map((tag) => (
                      <span key={tag}>{tag}</span>
                    ))}
                    {school.hasRankingReferences ? <span>{'含参考榜单'}</span> : null}
                  </div>
                </Link>
              ))}
            </div>
          </article>

          <article className="panel">
            <h2 className="panel-title">{'专业速查'}</h2>
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
                    {major.hasRankingReferences ? <span>{'含参考榜单'}</span> : null}
                  </div>
                </Link>
              ))}
            </div>
          </article>
        </section>

        {productPayload ? (
          <PlatformHomepageShelf apiBaseUrl={apiBaseUrl} products={productPayload.items} />
        ) : (
          <PlatformUnavailablePanel />
        )}
      </main>
    );
  } catch {
    return (
      <main className="page-shell">
        <section className="panel">
          <h1 className="panel-title">{'公开内容暂时不可用'}</h1>
          <p>{'公开内容加载失败，请稍后重试。'}</p>
        </section>
      </main>
    );
  }
}
