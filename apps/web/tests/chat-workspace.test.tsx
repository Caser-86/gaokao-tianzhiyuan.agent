import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { sendChatMessageMock } = vi.hoisted(() => ({
  sendChatMessageMock: vi.fn(),
}));

vi.mock('../lib/chat-api', () => ({
  sendChatMessage: sendChatMessageMock,
}));

import ChatWorkspace from '../components/public/chat-workspace';

beforeEach(() => {
  sendChatMessageMock.mockReset();
  sendChatMessageMock.mockResolvedValue({
    request_id: 'chat_test',
    output: {
      type: 'structured_json',
      content: {
        summary: '志愿建议摘要',
        analysis: '优先看学校层次和专业匹配。',
        follow_up_questions: ['你的省份和分数是多少？'],
        rendered_reply: '可以先把目标学校范围缩小到 985/211。',
        suggestions: [
          {
            type: 'school',
            title: '东南大学',
            slug: 'southeast-university',
            reason: '工科实力强，适合作为冲刺项。',
            confidence: 0.81,
          },
        ],
        actions: [
          {
            type: 'open_school',
            label: '查看学校详情',
            target: '/schools/southeast-university',
          },
        ],
      },
    },
  });
});

test('auto-sends the initial prompt when the chat page opens from a quick prompt', async () => {
  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-123"
      initialPrompt="查学校"
    />,
  );

  await waitFor(() => {
    expect(sendChatMessageMock).toHaveBeenCalledWith(
      {
        userId: 'wx-openid-123',
        message: '查学校',
      },
      'https://api.gaokao.test',
    );
  });

  expect(screen.getByDisplayValue('查学校')).toBeInTheDocument();
  expect(screen.getByText('可以先把目标学校范围缩小到 985/211。')).toBeInTheDocument();
});

test('renders suggestion cards and action links from the chat response', async () => {
  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-123"
      initialPrompt="查学校"
    />,
  );

  await waitFor(() => {
    expect(screen.getByRole('link', { name: '东南大学' })).toHaveAttribute(
      'href',
      '/schools/southeast-university',
    );
  });

  expect(screen.getByText('工科实力强，适合作为冲刺项。')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '查看学校详情' })).toHaveAttribute(
    'href',
    '/schools/southeast-university',
  );
});

test('allows manually sending a question when there is no initial prompt', async () => {
  render(<ChatWorkspace apiBaseUrl="https://api.gaokao.test" userId="wx-openid-456" />);

  fireEvent.change(screen.getByRole('textbox', { name: '输入你的问题' }), {
    target: { value: '帮我分析江苏985' },
  });
  fireEvent.click(screen.getByRole('button', { name: '发送问题' }));

  await waitFor(() => {
    expect(sendChatMessageMock).toHaveBeenCalledWith(
      {
        userId: 'wx-openid-456',
        message: '帮我分析江苏985',
      },
      'https://api.gaokao.test',
    );
  });
});
