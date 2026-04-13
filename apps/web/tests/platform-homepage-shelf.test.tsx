import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { trackPlatformEventMock } = vi.hoisted(() => ({
  trackPlatformEventMock: vi.fn(),
}));

vi.mock('../lib/platform-events', () => ({
  trackPlatformEvent: trackPlatformEventMock,
}));

import PlatformHomepageShelf from '../components/public/platform-homepage-shelf';

beforeEach(() => {
  trackPlatformEventMock.mockReset();
  trackPlatformEventMock.mockResolvedValue(undefined);
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

  fireEvent.click(screen.getByRole('button', { name: '查看志愿快报订阅' }));

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
