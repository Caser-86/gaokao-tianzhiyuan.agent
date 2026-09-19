import ChatWorkspace from '../../components/public/chat-workspace';

const getApiBaseUrl = () => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';

type ChatPageProps = {
  searchParams?: Promise<{
    prompt?: string;
    session_id?: string;
  }>;
};

export default async function ChatPage({ searchParams }: ChatPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const initialPrompt = resolvedSearchParams?.prompt?.trim() || undefined;
  const sessionId = resolvedSearchParams?.session_id?.trim() || undefined;

  return (
    <main className="page-shell">
      <ChatWorkspace
        apiBaseUrl={getApiBaseUrl()}
        initialPrompt={initialPrompt}
        sessionId={sessionId}
      />
    </main>
  );
}
