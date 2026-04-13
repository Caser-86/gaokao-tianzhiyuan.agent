import Link from 'next/link';

import SearchEntry from '../components/public/search-entry';
import { getSearchEntry, listMajors, listSchools } from '../lib/public-content-api';

export default async function HomePage() {
  try {
    const [searchEntry, schoolPayload, majorPayload] = await Promise.all([
      getSearchEntry(),
      listSchools(),
      listMajors(),
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
