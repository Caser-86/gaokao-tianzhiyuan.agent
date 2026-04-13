type DashboardShellProps = {
  title: string;
};

const cards = ['待审核内容', '最近发布', '抓取状态'];

export default function DashboardShell({ title }: DashboardShellProps) {
  return (
    <main>
      <h1>{title}</h1>
      <section>
        {cards.map((card) => (
          <article key={card}>
            <h2>{card}</h2>
          </article>
        ))}
      </section>
    </main>
  );
}
