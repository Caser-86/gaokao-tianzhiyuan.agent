'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';

import { type ChatMessageResponse, sendChatMessage } from '../../lib/chat-api';

type ChatWorkspaceProps = {
  apiBaseUrl: string;
  userId?: string;
  initialPrompt?: string;
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
            {content.follow_up_questions?.length ? (
              <ul style={{ margin: '12px 0 0', paddingLeft: 20 }}>
                {content.follow_up_questions.map((question) => (
                  <li key={question}>{question}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </section>
    </section>
  );
}
