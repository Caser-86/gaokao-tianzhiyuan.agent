"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

import { type ChatMessageResponse, sendChatMessage } from "../../lib/chat-api";
import {
  getChatRiskFlagCopy,
  isUnknownChatRiskFlag,
} from "../../lib/chat-risk-flags";

type ChatWorkspaceProps = {
  apiBaseUrl: string;
  userId?: string;
  initialPrompt?: string;
};

const resolveSuggestionHref = (
  suggestion: NonNullable<
    ChatMessageResponse["output"]["content"]["suggestions"]
  >[number],
) => {
  if (!suggestion.slug) {
    return null;
  }
  if (suggestion.type === "school") {
    return `/schools/${suggestion.slug}`;
  }
  if (suggestion.type === "major") {
    return `/majors/${suggestion.slug}`;
  }
  return null;
};

const getGeneratedItemKey = (
  namespace: string,
  parts: Array<number | string | null | undefined>,
  index: number,
) =>
  [namespace, ...parts.filter((part) => part !== null && part !== undefined), index]
    .map(String)
    .join("-");

type ChatAction = NonNullable<
  ChatMessageResponse["output"]["content"]["actions"]
>[number];

const hasActionTarget = (
  action: ChatAction,
): action is ChatAction & { target: string } =>
  typeof action.target === "string" && action.target.trim().length > 0;

export default function ChatWorkspace({
  apiBaseUrl,
  userId,
  initialPrompt,
}: ChatWorkspaceProps) {
  const [draft, setDraft] = useState(initialPrompt ?? "");
  const [response, setResponse] = useState<ChatMessageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const didAutoSendInitialPrompt = useRef(false);

  const submitMessage = async (message: string) => {
    const normalized = message.trim();
    if (!normalized) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const nextResponse = await sendChatMessage(
        {
          userId,
          message: normalized,
        },
        apiBaseUrl,
      );
      setResponse(nextResponse);
    } catch {
      setError(
        "\u5f53\u524d\u5bf9\u8bdd\u6682\u65f6\u4e0d\u53ef\u7528\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (didAutoSendInitialPrompt.current) {
      return;
    }
    if (!initialPrompt?.trim()) {
      return;
    }

    didAutoSendInitialPrompt.current = true;
    void submitMessage(initialPrompt);
  }, [initialPrompt]);

  const content = response?.output.content;
  const actions = content?.actions?.filter(hasActionTarget) ?? [];

  return (
    <section className="panel">
      <h1 className="panel-title">{"\u9ad8\u8003\u95ee\u7b54\u5165\u53e3"}</h1>
      <p style={{ margin: "0 0 16px", color: "var(--muted)", lineHeight: 1.7 }}>
        {
          "\u8f93\u5165\u4f60\u7684\u95ee\u9898\uff0c\u7cfb\u7edf\u4f1a\u76f4\u63a5\u8c03\u7528\u73b0\u6709\u9ad8\u8003\u5bf9\u8bdd\u63a5\u53e3\u8fd4\u56de\u7ed3\u6784\u5316\u5206\u6790\u7ed3\u679c\u3002"
        }
      </p>

      <form
        onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault();
          void submitMessage(draft);
        }}
      >
        <label
          htmlFor="chat-question"
          style={{ display: "block", marginBottom: 8, fontWeight: 600 }}
        >
          {"\u8f93\u5165\u4f60\u7684\u95ee\u9898"}
        </label>
        <textarea
          id="chat-question"
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value);
          }}
          rows={5}
          style={{
            width: "100%",
            resize: "vertical",
            borderRadius: 18,
            border: "1px solid var(--line)",
            padding: 14,
            background: "rgba(255, 255, 255, 0.82)",
            font: "inherit",
            lineHeight: 1.7,
          }}
        />
        <div className="link-row">
          <button type="submit" className="cta" disabled={isSubmitting}>
            {isSubmitting
              ? "\u53d1\u9001\u4e2d..."
              : "\u53d1\u9001\u95ee\u9898"}
          </button>
        </div>
      </form>

      <section className="panel" style={{ marginTop: 20 }}>
        <h2 className="panel-title">{"\u5206\u6790\u7ed3\u679c"}</h2>
        {error ? <p>{error}</p> : null}
        {!error && !content ? (
          <p>
            {
              "\u63d0\u4ea4\u95ee\u9898\u540e\uff0c\u8fd9\u91cc\u4f1a\u663e\u793a\u5206\u6790\u7ed3\u8bba\u548c\u8ffd\u95ee\u5efa\u8bae\u3002"
            }
          </p>
        ) : null}
        {content ? (
          <div className="feature-list">
            <div>
              <strong>
                {content.rendered_reply ??
                  content.summary ??
                  "\u5df2\u6536\u5230\u5206\u6790\u7ed3\u679c"}
              </strong>
            </div>
            {content.analysis ? (
              <p style={{ margin: "8px 0 0" }}>{content.analysis}</p>
            ) : null}
            {content.risk_flags?.length ? (
              <section>
                <h3 style={{ margin: "16px 0 8px" }}>
                  {"\u98ce\u9669\u63d0\u9192"}
                </h3>
                <div className="catalog-list">
                  {content.risk_flags.map((riskFlag, index) => {
                    const riskCopy = getChatRiskFlagCopy(riskFlag);

                    return (
                      <article
                        key={getGeneratedItemKey("risk", [riskFlag], index)}
                        className="catalog-card"
                      >
                        <strong>{riskCopy.title}</strong>
                        <p>{riskCopy.description}</p>
                        {isUnknownChatRiskFlag(riskFlag) ? (
                          <div className="meta">
                            <span>{riskCopy.rawKey}</span>
                          </div>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              </section>
            ) : null}
            {content.suggestions?.length ? (
              <section>
                <h3 style={{ margin: "16px 0 8px" }}>
                  {"\u63a8\u8350\u5185\u5bb9"}
                </h3>
                <div className="catalog-list">
                  {content.suggestions.map((suggestion, index) => {
                    const href = resolveSuggestionHref(suggestion);

                    return (
                      <article
                        key={getGeneratedItemKey(
                          "suggestion",
                          [suggestion.type, suggestion.slug, suggestion.title],
                          index,
                        )}
                        className="catalog-card"
                      >
                        {href ? (
                          <Link href={href}>
                            <strong>{suggestion.title}</strong>
                          </Link>
                        ) : (
                          <strong>{suggestion.title}</strong>
                        )}
                        {suggestion.reason ? <p>{suggestion.reason}</p> : null}
                        {typeof suggestion.confidence === "number" ? (
                          <div className="meta">
                            <span>{`\u7f6e\u4fe1\u5ea6 ${(suggestion.confidence * 100).toFixed(0)}%`}</span>
                          </div>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              </section>
            ) : null}
            {content.follow_up_questions?.length ? (
              <ul style={{ margin: "12px 0 0", paddingLeft: 20 }}>
                {content.follow_up_questions.map((question, index) => (
                  <li
                    key={getGeneratedItemKey("follow-up", [question], index)}
                  >
                    {question}
                  </li>
                ))}
              </ul>
            ) : null}
            {actions.length ? (
              <section>
                <h3 style={{ margin: "16px 0 8px" }}>
                  {"\u4e0b\u4e00\u6b65\u52a8\u4f5c"}
                </h3>
                <div className="link-row">
                  {actions.map((action, index) => (
                    <Link
                      key={getGeneratedItemKey(
                        "action",
                        [action.type, action.target, action.label],
                        index,
                      )}
                      href={action.target}
                      className="cta secondary"
                    >
                      {action.label}
                    </Link>
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        ) : null}
      </section>
    </section>
  );
}
