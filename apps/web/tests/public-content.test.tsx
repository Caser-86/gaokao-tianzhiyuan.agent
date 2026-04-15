import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { trackPlatformEventMock } = vi.hoisted(() => ({
  trackPlatformEventMock: vi.fn(),
}));

vi.mock('../lib/platform-events', () => ({
  trackPlatformEvent: trackPlatformEventMock,
}));

import PageSectionRenderer from '../components/public/page-section-renderer';
import SearchEntry from '../components/public/search-entry';

beforeEach(() => {
  trackPlatformEventMock.mockReset();
  trackPlatformEventMock.mockResolvedValue(undefined);
});

test('renders modular public sections', () => {
  render(
    <PageSectionRenderer
      sections={[
        {
          type: 'highlights',
          title: '学校亮点',
          items: ['工科强', '实习机会多'],
        },
        {
          type: 'pitfalls',
          title: '报考坑点',
          items: ['转专业难', '热门专业分流强'],
        },
      ]}
    />,
  );

  expect(screen.getByRole('heading', { name: '学校亮点' })).toBeInTheDocument();
  expect(screen.getByText('工科强')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '报考坑点' })).toBeInTheDocument();
  expect(screen.getByText('转专业难')).toBeInTheDocument();
});

test('renders search entry prompts as chat links for candidates and parents', () => {
  render(
    <SearchEntry
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-123"
      title="高考志愿助手"
      description="帮你看学校、专业、地域、就业和坑点。"
      quickPrompts={['查学校', '查专业', '看地域对比']}
    />,
  );

  expect(screen.getByRole('heading', { name: '高考志愿助手' })).toBeInTheDocument();
  expect(screen.getByText('帮你看学校、专业、地域、就业和坑点。')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '查学校' })).toHaveAttribute(
    'href',
    '/chat?prompt=%E6%9F%A5%E5%AD%A6%E6%A0%A1&user_id=wx-openid-123',
  );
  expect(screen.getByRole('link', { name: '看地域对比' })).toHaveAttribute(
    'href',
    '/chat?prompt=%E7%9C%8B%E5%9C%B0%E5%9F%9F%E5%AF%B9%E6%AF%94&user_id=wx-openid-123',
  );
});

test('tracks quick prompt clicks with the server-provided API base URL', async () => {
  render(
    <SearchEntry
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-123"
      title="高考志愿助手"
      description="帮你看学校、专业、地域、就业和坑点。"
      quickPrompts={['查学校']}
    />,
  );

  const quickPromptLink = screen.getByRole('link', { name: '查学校' });
  quickPromptLink.addEventListener('click', (event) => {
    event.preventDefault();
  });

  fireEvent.click(quickPromptLink);

  await waitFor(() => {
    expect(trackPlatformEventMock).toHaveBeenCalledWith(
      {
        eventName: 'quick_prompt_clicked',
        step: 'homepage_masthead',
        metadata: { prompt: '查学校' },
      },
      'https://api.gaokao.test',
    );
  });
});
