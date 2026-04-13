'use client';

import { useEffect, useState } from 'react';

import {
  getPlatformEntitlementCopy,
  isUnknownPlatformEntitlement,
} from '../../lib/platform-entitlement-labels';
import type { PlatformProduct } from '../../lib/platform-api';
import { evaluatePlatformEntitlements } from '../../lib/platform-entitlements';
import { trackPlatformEvent } from '../../lib/platform-events';

type PlatformHomepageShelfProps = {
  apiBaseUrl: string;
  products: PlatformProduct[];
};

type EntitlementState =
  | { status: 'idle'; entitlements: string[] }
  | { status: 'loading'; entitlements: string[] }
  | { status: 'success'; entitlements: string[] }
  | { status: 'error'; entitlements: string[] };

export default function PlatformHomepageShelf({
  apiBaseUrl,
  products,
}: PlatformHomepageShelfProps) {
  const [selectedProductSlugs, setSelectedProductSlugs] = useState<string[]>([]);
  const [entitlementState, setEntitlementState] = useState<EntitlementState>({
    status: 'idle',
    entitlements: [],
  });

  useEffect(() => {
    if (selectedProductSlugs.length === 0) {
      setEntitlementState({ status: 'idle', entitlements: [] });
      return;
    }

    let cancelled = false;

    setEntitlementState((current) => ({
      status: 'loading',
      entitlements: current.entitlements,
    }));

    void evaluatePlatformEntitlements(selectedProductSlugs, apiBaseUrl)
      .then((payload) => {
        if (cancelled) {
          return;
        }

        setEntitlementState({
          status: 'success',
          entitlements: payload.entitlements,
        });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        setEntitlementState({
          status: 'error',
          entitlements: [],
        });
      });

    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, selectedProductSlugs]);

  const toggleProduct = (productSlug: string) => {
    setSelectedProductSlugs((current) =>
      current.includes(productSlug)
        ? current.filter((slug) => slug !== productSlug)
        : [...current, productSlug],
    );
  };

  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <h2 className="panel-title">精选服务</h2>
      {products.length === 0 ? (
        <p>平台服务暂时不可用，请稍后再试。</p>
      ) : (
        <>
          <div className="catalog-list">
            {products.map((product) => {
              const isSelected = selectedProductSlugs.includes(product.slug);

              return (
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
                    aria-pressed={isSelected}
                    onClick={() => {
                      toggleProduct(product.slug);
                      void trackPlatformEvent(
                        {
                          eventName: 'product_cta_clicked',
                          step: 'homepage_product_shelf',
                          metadata: { productSlug: product.slug },
                        },
                        apiBaseUrl,
                      );
                    }}
                  >
                    {isSelected ? `取消选择${product.name}` : `选择${product.name}`}
                  </button>
                </article>
              );
            })}
          </div>

          <section className="panel" style={{ marginTop: 20 }}>
            <h3 className="panel-title">能力预览</h3>
            {selectedProductSlugs.length === 0 ? (
              <p>选择产品后查看能力包。</p>
            ) : entitlementState.status === 'loading' ? (
              <p>正在加载能力预览...</p>
            ) : entitlementState.status === 'error' ? (
              <p>能力预览加载失败，请稍后再试。</p>
            ) : (
              <ul className="feature-list">
                {entitlementState.entitlements.map((entitlement) => {
                  const entitlementCopy = getPlatformEntitlementCopy(entitlement);

                  return (
                    <li key={entitlement}>
                      <strong>{entitlementCopy.title}</strong>
                      <p>{entitlementCopy.description}</p>
                      {isUnknownPlatformEntitlement(entitlement) ? (
                        <small>{entitlementCopy.rawKey}</small>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  );
}
