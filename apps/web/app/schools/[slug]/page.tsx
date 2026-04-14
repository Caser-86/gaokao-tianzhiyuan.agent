import Link from 'next/link';
import { notFound } from 'next/navigation';

import PageSectionRenderer from '../../../components/public/page-section-renderer';
import RankingReferenceList from '../../../components/public/ranking-reference-list';
import { PublicApiError, getSchoolBySlug } from '../../../lib/public-content-api';

type SchoolPageProps = {
  params: Promise<{ slug: string }>;
};

export default async function SchoolPage({ params }: SchoolPageProps) {
  const { slug } = await params;

  try {
    const school = await getSchoolBySlug(slug);

    return (
      <main className="page-shell">
        <section className="masthead">
          <span className="eyebrow">{'学校解读'}</span>
          <h1 className="hero-title">{school.name}</h1>
          <p className="hero-copy">{school.summary}</p>
          <div className="meta">
            <span>{school.region}</span>
            <span>{school.city}</span>
            {school.tags.map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
          <div className="link-row">
            {school.relatedMajors.map((majorSlug) => (
              <Link key={majorSlug} href={`/majors/${majorSlug}`} className="cta secondary">
                {'查看相关专业'}
              </Link>
            ))}
            {school.rankingReferences.length > 0 ? (
              <Link href="#ranking-references" className="cta secondary">
                {'查看参考榜单'}
              </Link>
            ) : null}
          </div>
        </section>

        <PageSectionRenderer sections={school.sections} />
        <RankingReferenceList references={school.rankingReferences} />
      </main>
    );
  } catch (error) {
    if (error instanceof PublicApiError && error.status === 404) {
      notFound();
    }

    return (
      <main className="page-shell">
        <section className="panel">
          <h1 className="panel-title">{'学校内容暂时不可用'}</h1>
          <p>{'公开内容加载失败，请稍后重试。'}</p>
        </section>
      </main>
    );
  }
}
