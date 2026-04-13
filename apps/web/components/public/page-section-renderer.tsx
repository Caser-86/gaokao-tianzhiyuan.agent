type PageSection = {
  type: string;
  title: string;
  items: string[];
};

type PageSectionRendererProps = {
  sections: PageSection[];
};

export default function PageSectionRenderer({ sections }: PageSectionRendererProps) {
  return (
    <section className="section-grid">
      {sections.map((section) => (
        <article key={`${section.type}-${section.title}`} className="section-card" data-tone={section.type}>
          <h2>{section.title}</h2>
          <ul>
            {section.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      ))}
    </section>
  );
}
