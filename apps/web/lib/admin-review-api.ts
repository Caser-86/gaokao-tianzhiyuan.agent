import type { AdminReviewItem } from '../components/admin/dashboard-shell';

const getApiUrl = () => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';
const getAdminToken = () => process.env.GAOKAO_AGENT_ADMIN_TOKEN ?? 'dev-admin-token';

const buildHeaders = (contentType?: string) => {
  const headers: Record<string, string> = {
    'x-admin-token': getAdminToken(),
  };

  if (contentType) {
    headers['Content-Type'] = contentType;
  }

  return headers;
};

const parseResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
};

export async function listReviewQueue(): Promise<AdminReviewItem[]> {
  const response = await fetch(`${getApiUrl()}/api/admin/review-queue`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{ items: AdminReviewItem[] }>(response);
  return payload.items;
}

export async function approveReviewQueueItem(
  queueId: number,
  reviewedBy: string,
): Promise<AdminReviewItem> {
  const response = await fetch(`${getApiUrl()}/api/admin/review-queue/${queueId}/approve`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({ reviewed_by: reviewedBy }),
  });
  return parseResponse<AdminReviewItem>(response);
}

export async function rejectReviewQueueItem(
  queueId: number,
  reviewedBy: string,
  reviewNote?: string,
): Promise<AdminReviewItem> {
  const response = await fetch(`${getApiUrl()}/api/admin/review-queue/${queueId}/reject`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      reviewed_by: reviewedBy,
      review_note: reviewNote || undefined,
    }),
  });
  return parseResponse<AdminReviewItem>(response);
}
