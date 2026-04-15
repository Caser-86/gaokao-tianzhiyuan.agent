import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { chatWorkspaceMock } = vi.hoisted(() => ({
  chatWorkspaceMock: vi.fn(
    ({ userId, initialPrompt }: { userId?: string; initialPrompt?: string }) => (
      <div>{`workspace:${userId ?? 'anon'}:${initialPrompt ?? ''}`}</div>
    ),
  ),
}));

vi.mock('../components/public/chat-workspace', () => ({
  default: chatWorkspaceMock,
}));

import ChatPage from '../app/chat/page';

beforeEach(() => {
  chatWorkspaceMock.mockClear();
});

test('chat page forwards openid query params to the chat workspace', async () => {
  render(
    await ChatPage({
      searchParams: Promise.resolve({
        openid: 'wx-openid-123',
        prompt: '查学校',
      }),
    }),
  );

  expect(screen.getByText('workspace:wx-openid-123:查学校')).toBeInTheDocument();
});

test('chat page prefers user_id when both user_id and openid are present', async () => {
  render(
    await ChatPage({
      searchParams: Promise.resolve({
        user_id: 'user-1',
        openid: 'wx-openid-123',
        prompt: '查专业',
      }),
    }),
  );

  expect(screen.getByText('workspace:user-1:查专业')).toBeInTheDocument();
});
