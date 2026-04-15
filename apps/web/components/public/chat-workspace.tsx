'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useRef, useState } from 'react';

import { type ChatMessageResponse, sendChatMessage } from '../../lib/chat-api';

type ChatWorkspaceProps = {
  apiBaseUrl: string;
  userId?: string;
  initialPrompt?: string;
};

const resolveSuggestionHref = (
  suggestion: NonNullable<ChatMessageResponse['output']['content']['suggestions']>[number],
) => {
  if (!suggestion.slug) {
    return null;
  }
  if (suggestion.type === 'school') {
    return `/schools/${suggestion.slug}`;
  }
  if (suggestion.type === 'major') {
    return `/majors/${suggestion.slug}`;
  }
  return null;
};

export default function ChatWorkspace({
  apiBaseUrl,
  userId,
  initialPrompt,
}: ChatWorkspaceProps) {
  const [draft, setDraft] = useState(initialPrompt ?? '');
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
      setError('当前对话暂时不可用，请稍后重试。');
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

  return (
    <section className="panel">
      <h1 className="panel-title">高考问答入口</h1>
      <p style={{ margin: '0 0 16px', color: 'var(--muted)', lineHeight: 1.7 }}>
        输入你的问题，系统会直接调用现有高考对话接口返回结构化分析结果。
      </p>

      <form
        onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault();
          void submitMessage(draft);
        }}
      >
        <label
          htmlFor="chat-question"
          style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}
        >
          输入你的问题
        </label>
        <textarea
          id="chat-question"
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value);
          }}
          rows={5}
          style={{
            width: '100%',
            resize: 'vertical',
            borderRadius: 18,
            border: '1px solid var(--line)',
            padding: 14,
            background: 'rgba(255, 255, 255, 0.82)',
            font: 'inherit',
            lineHeight: 1.7,
          }}
        />
        <div className="link-row">
          <button type="submit" className="cta" disabled={isSubmitting}>
            {isSubmitting ? '发送中...' : '发送问题'}
          </button>
        </div>
      </form>

      <section className="panel" style={{ marginTop: 20 }}>
        <h2 className="panel-title">分析结果</h2>
        {error ? <p>{error}</p> : null}
        {!error && !content ? <p>提交问题后，这里会显示分析结论和追问建议。</p> : null}
        {content ? (
          <div className="feature-list">
            <div>
              <strong>{content.rendered_reply ?? content.summary ?? '已收到分析结果'}</strong>
            </div>
            {content.analysis ? <p style={{ margin: '8px 0 0' }}>{content.analysis}</p> : null}
            {content.risk_flags?.length ? (
              <section>
                <h3 style={{ margin: '16px 0 8px' }}>风险提醒</h3>
                <div className="meta">
                  {content.risk_flags.map((riskFlag) => (
                    <span key={riskFlag}>{riskFlag}</span>
                  ))}
                </div>
              </section>
            ) : null}
            {content.suggestions?.length ? (
              <section>
                <h3 style={{ margin: '16px 0 8px' }}>推荐内容</h3>
                <div className="catalog-list">
                  {content.suggestions.map((suggestion) => {
                    const href = resolveSuggestionHref(suggestion);

                    return (
                      <article
                        key={`${suggestion.type ?? 'suggestion'}-${suggestion.title}`}
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
                        {typeof suggestion.confidence === 'number' ? (
                          <div className="meta">
                            <span>{`置信度 ${(suggestion.confidence * 100).toFixed(0)}%`}</span>
                          </div>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              </section>
            ) : null}
            {content.follow_up_questions?.length ? (
              <ul style={{ margin: '12px 0 0', paddingLeft: 20 }}>
                {content.follow_up_questions.map((question) => (
                  <li key={question}>{question}</li>
                ))}
              </ul>
            ) : null}
            {content.actions?.length ? (
              <section>
                <h3 style={{ margin: '16px 0 8px' }}>下一步动作</h3>
                <div className="link-row">
                  {content.actions.map((action) => (
                    <Link
                      key={`${action.type ?? 'action'}-${action.label}`}
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
