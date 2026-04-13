'use client';

import type { PlatformProduct } from '../../lib/platform-api';
import { trackPlatformEvent } from '../../lib/platform-events';

type PlatformHomepageShelfProps = {
  apiBaseUrl: string;
  products: PlatformProduct[];
};

export default function PlatformHomepageShelf({
  apiBaseUrl,
  products,
}: PlatformHomepageShelfProps) {
  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <h2 className="panel-title">精选服务</h2>
      {products.length === 0 ? (
        <p>平台服务暂时不可用，请稍后再试。</p>
      ) : (
        <div className="catalog-list">
          {products.map((product) => (
            <article key={product.slug} className="catalog-card">
              <strong>{product.name}</strong>
              <p>{product.description}</p>
              <div className="meta">
                {product.entitlements.map((entitlement) => (
                  <span key={entitlement}>{entitlement}</span>
                ))}
              </div>
              <button
                type="button"
                className="chip"
                onClick={() => {
                  void trackPlatformEvent({
                    eventName: 'product_cta_clicked',
                    step: 'homepage_product_shelf',
                    metadata: { productSlug: product.slug },
                  }, apiBaseUrl);
                }}
              >
                {`查看${product.name}`}
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
