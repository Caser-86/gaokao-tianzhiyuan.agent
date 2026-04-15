import ChatWorkspace from '../../components/public/chat-workspace';

const getApiBaseUrl = () => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';

type ChatPageProps = {
  searchParams?: Promise<{
    openid?: string;
    prompt?: string;
    user_id?: string;
  }>;
};

export default async function ChatPage({ searchParams }: ChatPageProps = {}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const userId =
    resolvedSearchParams?.user_id?.trim() ||
    resolvedSearchParams?.openid?.trim() ||
    undefined;
  const initialPrompt = resolvedSearchParams?.prompt?.trim() || undefined;

  return (
    <main className="page-shell">
      <ChatWorkspace
        apiBaseUrl={getApiBaseUrl()}
        userId={userId}
        initialPrompt={initialPrompt}
      />
    </main>
  );
}
