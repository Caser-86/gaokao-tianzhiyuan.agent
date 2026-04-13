import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { evaluatePlatformEntitlementsMock, trackPlatformEventMock } = vi.hoisted(() => ({
  evaluatePlatformEntitlementsMock: vi.fn(),
  trackPlatformEventMock: vi.fn(),
}));

vi.mock('../lib/platform-entitlements', () => ({
  evaluatePlatformEntitlements: evaluatePlatformEntitlementsMock,
}));

vi.mock('../lib/platform-events', () => ({
  trackPlatformEvent: trackPlatformEventMock,
}));

import PlatformHomepageShelf from '../components/public/platform-homepage-shelf';

const homepageProducts = [
  {
    slug: 'insight-weekly',
    name: '\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605',
    description:
      '\u9002\u5408\u6301\u7eed\u63a5\u6536\u5b66\u6821\u3001\u4e13\u4e1a\u548c\u98ce\u9669\u53d8\u5316\u63d0\u9192\u3002',
    entitlements: ['school_basic_access'],
  },
  {
    slug: 'deep-dive-pack',
    name: '\u6df1\u5ea6\u62a5\u544a\u5305',
    description:
      '\u9002\u5408\u9700\u8981\u5b66\u6821\u3001\u4e13\u4e1a\u3001\u5730\u533a\u548c\u5c31\u4e1a\u6df1\u5ea6\u5206\u6790\u7684\u5bb6\u5ead\u3002',
    entitlements: ['school_deep_dive_access'],
  },
];

const renderShelf = () =>
  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={homepageProducts}
    />,
  );

const getPreviewSection = (container: HTMLElement) => {
  const previewSection = container.querySelectorAll('section.panel')[1];

  expect(previewSection).toBeTruthy();
  return previewSection as HTMLElement;
};

beforeEach(() => {
  evaluatePlatformEntitlementsMock.mockReset();
  evaluatePlatformEntitlementsMock.mockResolvedValue({
    product_slugs: ['insight-weekly'],
    entitlements: ['school_basic_access'],
  });
  trackPlatformEventMock.mockReset();
  trackPlatformEventMock.mockResolvedValue(undefined);
});

test('shows an empty prompt before any products are selected', () => {
  const { container } = renderShelf();

  expect(evaluatePlatformEntitlementsMock).not.toHaveBeenCalled();
  expect(within(getPreviewSection(container)).queryByRole('list')).not.toBeInTheDocument();
});

test('renders user-facing entitlement titles in product card metadata', () => {
  renderShelf();

  const firstCard = screen.getAllByRole('article')[0];

  expect(
    within(firstCard).getByText('\u9662\u6821\u57fa\u7840\u4fe1\u606f\u67e5\u770b'),
  ).toBeInTheDocument();
  expect(within(firstCard).queryByText('school_basic_access')).not.toBeInTheDocument();
});

test('keeps raw keys visible for unknown product entitlements', () => {
  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'future-pack',
          name: 'Future Pack',
          description: 'Upcoming capability bundle.',
          entitlements: ['future_capability'],
        },
      ]}
    />,
  );

  const onlyCard = screen.getAllByRole('article')[0];

  expect(within(onlyCard).getByText('future_capability')).toBeInTheDocument();
});

test('selecting products renders merged entitlements from the API', async () => {
  evaluatePlatformEntitlementsMock.mockImplementation((productSlugs: string[]) => {
    if (productSlugs.length === 2) {
      return Promise.resolve({
        product_slugs: ['insight-weekly', 'deep-dive-pack'],
        entitlements: ['major_basic_access', 'school_deep_dive_access'],
      });
    }

    return Promise.resolve({
      product_slugs: ['insight-weekly'],
      entitlements: ['school_basic_access'],
    });
  });

  const { container } = renderShelf();

  fireEvent.click(
    screen.getByRole('button', { name: '\u9009\u62e9\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605' }),
  );
  fireEvent.click(screen.getByRole('button', { name: '\u9009\u62e9\u6df1\u5ea6\u62a5\u544a\u5305' }));

  await waitFor(() => {
    expect(evaluatePlatformEntitlementsMock).toHaveBeenLastCalledWith(
      ['insight-weekly', 'deep-dive-pack'],
      'https://api.gaokao.test',
    );
  });

  const previewSection = getPreviewSection(container);

  await waitFor(() => {
    expect(
      within(previewSection).getByText('\u4e13\u4e1a\u57fa\u7840\u4fe1\u606f\u67e5\u770b'),
    ).toBeInTheDocument();
  });

  expect(
    within(previewSection).getByText(
      '\u67e5\u770b\u4e13\u4e1a\u7684\u57f9\u517b\u65b9\u5411\u3001\u9009\u79d1\u8981\u6c42\u548c\u57fa\u7840\u89e3\u8bfb\u3002',
    ),
  ).toBeInTheDocument();
  expect(
    within(previewSection).getByText('\u9662\u6821\u6df1\u5ea6\u5206\u6790'),
  ).toBeInTheDocument();
  expect(
    within(previewSection).getByText(
      '\u67e5\u770b\u9662\u6821\u5206\u6570\u8d8b\u52bf\u3001\u5f55\u53d6\u5c42\u6b21\u548c\u6df1\u5ea6\u89e3\u8bfb\u3002',
    ),
  ).toBeInTheDocument();
});

test('renders fallback copy and keeps the raw key for unknown entitlements', async () => {
  evaluatePlatformEntitlementsMock.mockResolvedValueOnce({
    product_slugs: ['insight-weekly'],
    entitlements: ['future_capability'],
  });

  const { container } = renderShelf();

  fireEvent.click(
    screen.getByRole('button', { name: '\u9009\u62e9\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605' }),
  );

  const previewSection = getPreviewSection(container);

  await waitFor(() => {
    expect(
      within(previewSection).getByText('\u66f4\u591a\u5e73\u53f0\u80fd\u529b'),
    ).toBeInTheDocument();
  });

  expect(
    within(previewSection).getByText(
      '\u8be5\u80fd\u529b\u5df2\u5f00\u901a\uff0c\u8be6\u7ec6\u8bf4\u660e\u5373\u5c06\u8865\u5145\u3002',
    ),
  ).toBeInTheDocument();
  expect(within(previewSection).getByText('future_capability')).toBeInTheDocument();
});

test('shows a local error when entitlement evaluation fails', async () => {
  evaluatePlatformEntitlementsMock.mockRejectedValueOnce(new Error('boom'));

  const { container } = renderShelf();

  fireEvent.click(
    screen.getByRole('button', { name: '\u9009\u62e9\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605' }),
  );

  await waitFor(() => {
    expect(evaluatePlatformEntitlementsMock).toHaveBeenCalledWith(
      ['insight-weekly'],
      'https://api.gaokao.test',
    );
  });

  expect(within(getPreviewSection(container)).queryByRole('list')).not.toBeInTheDocument();
});

test('tracks product CTA clicks with the server-provided API base URL', async () => {
  renderShelf();

  fireEvent.click(
    screen.getByRole('button', { name: '\u9009\u62e9\u5fd7\u613f\u5feb\u62a5\u8ba2\u9605' }),
  );

  await waitFor(() => {
    expect(trackPlatformEventMock).toHaveBeenCalledWith(
      {
        eventName: 'product_cta_clicked',
        step: 'homepage_product_shelf',
        metadata: { productSlug: 'insight-weekly' },
      },
      'https://api.gaokao.test',
    );
  });
});
