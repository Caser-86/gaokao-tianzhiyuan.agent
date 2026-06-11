import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

const { sendChatMessageMock } = vi.hoisted(() => ({
  sendChatMessageMock: vi.fn(),
}));

vi.mock("../lib/chat-api", () => ({
  sendChatMessage: sendChatMessageMock,
}));

import ChatWorkspace from "../components/public/chat-workspace";

beforeEach(() => {
  sendChatMessageMock.mockReset();
  sendChatMessageMock.mockResolvedValue({
    request_id: "chat_test",
    output: {
      type: "structured_json",
      content: {
        summary: "\u5fd7\u613f\u5efa\u8bae\u6458\u8981",
        analysis:
          "\u4f18\u5148\u770b\u5b66\u6821\u5c42\u6b21\u548c\u4e13\u4e1a\u5339\u914d\u3002",
        follow_up_questions: [
          "\u4f60\u7684\u7701\u4efd\u548c\u5206\u6570\u662f\u591a\u5c11\uff1f",
        ],
        rendered_reply:
          "\u53ef\u4ee5\u5148\u628a\u76ee\u6807\u5b66\u6821\u8303\u56f4\u7f29\u5c0f\u5230 985/211\u3002",
        suggestions: [
          {
            type: "school",
            title: "\u4e1c\u5357\u5927\u5b66",
            slug: "southeast-university",
            reason:
              "\u5de5\u79d1\u5b9e\u529b\u5f3a\uff0c\u9002\u5408\u4f5c\u4e3a\u51b2\u523a\u9879\u3002",
            confidence: 0.81,
          },
        ],
        actions: [
          {
            type: "open_school",
            label: "\u67e5\u770b\u5b66\u6821\u8be6\u60c5",
            target: "/schools/southeast-university",
          },
        ],
        risk_flags: ["financial_industry_competition"],
      },
    },
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("auto-sends the initial prompt when the chat page opens from a quick prompt", async () => {
  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-123"
      initialPrompt={"\u67e5\u5b66\u6821"}
    />,
  );

  await waitFor(() => {
    expect(sendChatMessageMock).toHaveBeenCalledWith(
      {
        userId: "wx-openid-123",
        message: "\u67e5\u5b66\u6821",
      },
      "https://api.gaokao.test",
    );
  });

  expect(screen.getByDisplayValue("\u67e5\u5b66\u6821")).toBeInTheDocument();
  expect(
    screen.getByText(
      "\u53ef\u4ee5\u5148\u628a\u76ee\u6807\u5b66\u6821\u8303\u56f4\u7f29\u5c0f\u5230 985/211\u3002",
    ),
  ).toBeInTheDocument();
});

test("renders suggestion cards and action links from the chat response", async () => {
  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-123"
      initialPrompt={"\u67e5\u5b66\u6821"}
    />,
  );

  await waitFor(() => {
    expect(
      screen.getByRole("link", { name: "\u4e1c\u5357\u5927\u5b66" }),
    ).toHaveAttribute("href", "/schools/southeast-university");
  });

  expect(
    screen.getByText(
      "\u5de5\u79d1\u5b9e\u529b\u5f3a\uff0c\u9002\u5408\u4f5c\u4e3a\u51b2\u523a\u9879\u3002",
    ),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: "\u67e5\u770b\u5b66\u6821\u8be6\u60c5" }),
  ).toHaveAttribute("href", "/schools/southeast-university");
});

test("renders duplicate action labels without duplicate React key warnings", async () => {
  const consoleErrorSpy = vi
    .spyOn(console, "error")
    .mockImplementation(() => undefined);

  sendChatMessageMock.mockResolvedValueOnce({
    request_id: "chat_duplicate_actions",
    output: {
      type: "structured_json",
      content: {
        rendered_reply: "\u53ef\u4ee5\u67e5\u770b\u4e24\u4e2a\u76f8\u5173\u94fe\u63a5\u3002",
        actions: [
          {
            label: "\u67e5\u770b\u8be6\u60c5",
            target: "/schools/henan-university",
          },
          {
            label: "\u67e5\u770b\u8be6\u60c5",
            target: "/majors/computer-science",
          },
        ],
      },
    },
  });

  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      initialPrompt={"\u6cb3\u5357\u5927\u5b66\u600e\u4e48\u6837"}
    />,
  );

  await waitFor(() => {
    expect(
      screen.getAllByRole("link", { name: "\u67e5\u770b\u8be6\u60c5" }),
    ).toHaveLength(2);
  });

  expect(consoleErrorSpy).not.toHaveBeenCalledWith(
    expect.stringContaining("Encountered two children with the same key"),
    expect.anything(),
  );
});

test("ignores provider actions without link targets", async () => {
  const consoleErrorSpy = vi
    .spyOn(console, "error")
    .mockImplementation(() => undefined);

  sendChatMessageMock.mockResolvedValueOnce({
    request_id: "chat_missing_action_target",
    output: {
      type: "structured_json",
      content: {
        rendered_reply: "\u6cb3\u5357\u5927\u5b66\u5206\u6790\u5df2\u751f\u6210\u3002",
        actions: [
          {
            label: "\u7ee7\u7eed\u8ffd\u95ee",
          },
        ],
      },
    },
  });

  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      initialPrompt={"\u6cb3\u5357\u5927\u5b66\u600e\u4e48\u6837"}
    />,
  );

  await waitFor(() => {
    expect(
      screen.getByText("\u6cb3\u5357\u5927\u5b66\u5206\u6790\u5df2\u751f\u6210\u3002"),
    ).toBeInTheDocument();
  });

  expect(
    screen.queryByRole("link", { name: "\u7ee7\u7eed\u8ffd\u95ee" }),
  ).not.toBeInTheDocument();
  expect(consoleErrorSpy).not.toHaveBeenCalledWith(
    expect.stringContaining("The prop `href` expects a `string` or `object`"),
    expect.anything(),
  );
});

test("renders user-facing risk copy for known risk flags", async () => {
  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-123"
      initialPrompt={"\u67e5\u5b66\u6821"}
    />,
  );

  await waitFor(() => {
    expect(
      screen.getByText("\u91d1\u878d\u884c\u4e1a\u7ade\u4e89\u98ce\u9669"),
    ).toBeInTheDocument();
  });

  expect(
    screen.getByText(
      "\u9002\u5408\u63d0\u9192\u7528\u6237\u5173\u6ce8\u91d1\u878d\u76f8\u5173\u4e13\u4e1a\u548c\u5c31\u4e1a\u65b9\u5411\u7684\u7ade\u4e89\u5f3a\u5ea6\u3002",
    ),
  ).toBeInTheDocument();
});

test("allows manually sending a question when there is no initial prompt", async () => {
  render(
    <ChatWorkspace
      apiBaseUrl="https://api.gaokao.test"
      userId="wx-openid-456"
    />,
  );

  fireEvent.change(
    screen.getByRole("textbox", {
      name: "\u8f93\u5165\u4f60\u7684\u95ee\u9898",
    }),
    {
      target: { value: "\u5e2e\u6211\u5206\u6790\u6c5f\u82cf985" },
    },
  );
  fireEvent.click(
    screen.getByRole("button", { name: "\u53d1\u9001\u95ee\u9898" }),
  );

  await waitFor(() => {
    expect(sendChatMessageMock).toHaveBeenCalledWith(
      {
        userId: "wx-openid-456",
        message: "\u5e2e\u6211\u5206\u6790\u6c5f\u82cf985",
      },
      "https://api.gaokao.test",
    );
  });
});
