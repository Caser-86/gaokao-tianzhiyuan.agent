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
  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
      ]}
    />,
  );

  expect(screen.getByText('选择产品后查看能力包。')).toBeInTheDocument();
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

  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
        {
          slug: 'deep-dive-pack',
          name: '深度报告包',
          description: '适合需要学校、专业、地域和就业深度分析的家庭。',
          entitlements: ['school_deep_dive_access'],
        },
      ]}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));
  fireEvent.click(screen.getByRole('button', { name: '选择深度报告包' }));

  await waitFor(() => {
    expect(evaluatePlatformEntitlementsMock).toHaveBeenLastCalledWith(
      ['insight-weekly', 'deep-dive-pack'],
      'https://api.gaokao.test',
    );
  });

  const previewSection = screen.getByRole('heading', { name: '能力预览' }).closest('section');

  expect(previewSection).not.toBeNull();
  expect(within(previewSection as HTMLElement).getByText('major_basic_access')).toBeInTheDocument();
  expect(
    within(previewSection as HTMLElement).getByText('school_deep_dive_access'),
  ).toBeInTheDocument();
});

test('shows a local error when entitlement evaluation fails', async () => {
  evaluatePlatformEntitlementsMock.mockRejectedValueOnce(new Error('boom'));

  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
      ]}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));

  await waitFor(() => {
    expect(screen.getByText('能力预览加载失败，请稍后再试。')).toBeInTheDocument();
  });
});

test('tracks product CTA clicks with the server-provided API base URL', async () => {
  render(
    <PlatformHomepageShelf
      apiBaseUrl="https://api.gaokao.test"
      products={[
        {
          slug: 'insight-weekly',
          name: '志愿快报订阅',
          description: '持续跟踪学校、专业和风险变化。',
          entitlements: ['school_basic_access'],
        },
      ]}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: '选择志愿快报订阅' }));

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
