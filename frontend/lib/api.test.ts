import { afterEach, describe, expect, it, vi } from 'vitest';

import { getHealth, sendDecision, sendMessage } from '@/lib/api';

afterEach(() => vi.unstubAllGlobals());

function stubFetch(response: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => response,
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('api', () => {
  it('sends the thread id so a turn continues the same conversation', async () => {
    const fetchMock = stubFetch({ thread_id: 't1' });
    await sendMessage('hello', 't1');
    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body)).toEqual({ message: 'hello', thread_id: 't1' });
  });

  it('posts a decision to the approve endpoint', async () => {
    const fetchMock = stubFetch({ thread_id: 't1' });
    await sendDecision('t1', 'approve');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/approve');
    expect(JSON.parse(init.body)).toEqual({ thread_id: 't1', decision: 'approve' });
  });

  it('surfaces the backend detail rather than a bare status', async () => {
    stubFetch({ detail: 'no such thread' }, false, 404);
    await expect(sendMessage('hi', null)).rejects.toThrow('no such thread');
  });

  it('reports the API as unreachable rather than throwing at the caller', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('ECONNREFUSED')));
    expect(await getHealth()).toBeNull();
  });
});
