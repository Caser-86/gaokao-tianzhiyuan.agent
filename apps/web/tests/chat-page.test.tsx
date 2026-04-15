import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const SCHOOL_PROMPT = '\u67e5\u5b66\u6821';
const MAJOR_PROMPT = '\u67e5\u4e13\u4e1a';

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
        prompt: SCHOOL_PROMPT,
      }),
    }),
  );

  expect(screen.getByText(`workspace:wx-openid-123:${SCHOOL_PROMPT}`)).toBeInTheDocument();
});

test('chat page prefers user_id when both user_id and openid are present', async () => {
  render(
    await ChatPage({
      searchParams: Promise.resolve({
        user_id: 'user-1',
        openid: 'wx-openid-123',
        prompt: MAJOR_PROMPT,
      }),
    }),
  );

  expect(screen.getByText(`workspace:user-1:${MAJOR_PROMPT}`)).toBeInTheDocument();
});

test('chat page renders an anonymous workspace when search params are absent', async () => {
  render(await ChatPage({}));

  expect(screen.getByText('workspace:anon:')).toBeInTheDocument();
});
