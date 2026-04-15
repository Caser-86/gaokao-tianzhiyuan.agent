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
  userId?: string;
  products: PlatformProduct[];
};

type EntitlementState =
  | { status: 'idle'; entitlements: string[] }
  | { status: 'loading'; entitlements: string[] }
  | { status: 'success'; entitlements: string[] }
  | { status: 'error'; entitlements: string[] };

export default function PlatformHomepageShelf({
  apiBaseUrl,
  userId,
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

    void evaluatePlatformEntitlements(selectedProductSlugs, apiBaseUrl, userId)
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
  }, [apiBaseUrl, selectedProductSlugs, userId]);

  const toggleProduct = (productSlug: string) => {
    setSelectedProductSlugs((current) =>
      current.includes(productSlug)
        ? current.filter((slug) => slug !== productSlug)
        : [...current, productSlug],
    );
  };

  return (
    <section className="panel" style={{ marginTop: 28 }}>
      <h2 className="panel-title">{'\u7cbe\u9009\u670d\u52a1'}</h2>
      {products.length === 0 ? (
        <p>{'\u5e73\u53f0\u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002'}</p>
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
                    {product.entitlements.map((entitlement) => {
                      const entitlementCopy = getPlatformEntitlementCopy(entitlement);

                      return (
                        <span key={entitlement}>
                          {isUnknownPlatformEntitlement(entitlement)
                            ? entitlementCopy.rawKey
                            : entitlementCopy.title}
                        </span>
                      );
                    })}
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
                    {isSelected
                      ? `\u5df2\u52a0\u5165\u80fd\u529b\u9884\u89c8${product.name}`
                      : `\u52a0\u5165\u80fd\u529b\u9884\u89c8${product.name}`}
                  </button>
                </article>
              );
            })}
          </div>

          <section className="panel" style={{ marginTop: 20 }}>
            <h3 className="panel-title">{'\u80fd\u529b\u9884\u89c8'}</h3>
            {selectedProductSlugs.length === 0 ? (
              <p>{'\u9009\u62e9\u4ea7\u54c1\u540e\u67e5\u770b\u80fd\u529b\u5305\u3002'}</p>
            ) : entitlementState.status === 'loading' ? (
              <p>{'\u6b63\u5728\u52a0\u8f7d\u80fd\u529b\u9884\u89c8...'}</p>
            ) : entitlementState.status === 'error' ? (
              <p>{'\u80fd\u529b\u9884\u89c8\u52a0\u8f7d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002'}</p>
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
