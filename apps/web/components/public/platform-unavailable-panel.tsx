'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function PlatformUnavailablePanel() {
  const router = useRouter();

  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <div className="label">平台服务</div>
      <h2 className="panel-title">平台服务暂时不可用</h2>
      <p>产品方案和能力预览暂时无法加载，你可以先继续查看学校、专业和地区信息。</p>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
        <Link href="#school-catalog" className="chip">
          先去查学校
        </Link>
        <button type="button" className="chip" onClick={() => router.refresh()}>
          稍后再试
        </button>
      </div>
    </section>
  );
}
