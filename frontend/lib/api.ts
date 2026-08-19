import type { ChatResponse, Health } from '@/lib/types';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    // The backend sends FastAPI's {detail} shape; anything else is a network or
    // proxy failure and the status is the only thing worth reporting.
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function sendMessage(message: string, threadId: string | null) {
  return post<ChatResponse>('/chat', { message, thread_id: threadId });
}

/** Answer a pending approval: 'approve', 'deny', or revised instructions. */
export function sendDecision(threadId: string, decision: string) {
  return post<ChatResponse>('/approve', { thread_id: threadId, decision });
}

export async function getHealth(): Promise<Health | null> {
  try {
    const response = await fetch(`${BASE}/health`);
    return response.ok ? ((await response.json()) as Health) : null;
  } catch {
    return null;
  }
}
