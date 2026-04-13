import Link from 'next/link';
import { notFound } from 'next/navigation';

import PageSectionRenderer from '../../../components/public/page-section-renderer';
import RankingReferenceList from '../../../components/public/ranking-reference-list';
import { PublicApiError, getMajorBySlug } from '../../../lib/public-content-api';

type MajorPageProps = {
  params: Promise<{ slug: string }>;
};

export default async function MajorPage({ params }: MajorPageProps) {
  const { slug } = await params;

  try {
    const major = await getMajorBySlug(slug);

    return (
      <main className="page-shell">
        <section className="masthead">
          <span className="eyebrow">专业解读</span>
          <h1 className="hero-title">{major.name}</h1>
          <p className="hero-copy">{major.summary}</p>
          <div className="meta">
            <span>{major.discipline}</span>
            {major.recommendedRegions.map((region) => (
              <span key={region}>{region}</span>
            ))}
          </div>
          <div className="link-row">
            {major.relatedSchools.map((schoolSlug) => (
              <Link key={schoolSlug} href={`/schools/${schoolSlug}`} className="cta secondary">
                查看相关学校
              </Link>
            ))}
          </div>
        </section>

        <PageSectionRenderer sections={major.sections} />
        <RankingReferenceList references={major.rankingReferences} />
      </main>
    );
  } catch (error) {
    if (error instanceof PublicApiError && error.status === 404) {
      notFound();
    }

    return (
      <main className="page-shell">
        <section className="panel">
          <h1 className="panel-title">专业内容暂时不可用</h1>
          <p>公开内容加载失败，请稍后重试。</p>
        </section>
      </main>
    );
  }
}
