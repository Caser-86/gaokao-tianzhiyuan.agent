type SearchEntryProps = {
  title: string;
  description: string;
  quickPrompts: string[];
};

export default function SearchEntry({ title, description, quickPrompts }: SearchEntryProps) {
  return (
    <section className="masthead">
      <span className="eyebrow">考生与家长对话助手</span>
      <h1 className="hero-title">{title}</h1>
      <p className="hero-copy">{description}</p>

      <div className="chip-row">
        {quickPrompts.map((prompt) => (
          <span key={prompt} className="chip">
            {prompt}
          </span>
        ))}
      </div>

      <section className="grid two">
        <article className="panel">
          <h2 className="panel-title">适合什么问题</h2>
          <ul className="feature-list">
            <li>同分数段里怎么选学校和城市更稳。</li>
            <li>某个专业到底学什么、就业去哪、风险在哪。</li>
            <li>学校名气、专业实力、地域资源该怎么平衡。</li>
          </ul>
        </article>
        <article className="panel">
          <h2 className="panel-title">适合什么入口</h2>
          <ul className="feature-list">
            <li>公众号推送专题页，用来讲清一所学校或一个专业。</li>
            <li>公众号菜单查询页，用来快速跳转学校页和专业页。</li>
            <li>后续接入订阅提醒、会员权益和专题包也不会推倒重来。</li>
          </ul>
        </article>
      </section>
    </section>
  );
}
