'use client';

import { useRef, useState } from 'react';

import { ApprovalCard } from '@/components/ApprovalCard';
import { Citations } from '@/components/Citations';
import { PullRequestCard } from '@/components/PullRequestCard';
import { TraceRail } from '@/components/TraceRail';
import { Badge, Button, Eyebrow } from '@/components/ui';
import { sendDecision, sendMessage } from '@/lib/api';
import type { ChatResponse, Outcome } from '@/lib/types';

type Turn = { role: 'user'; text: string } | { role: 'agent'; response: ChatResponse };

/** What happened to the proposal shown in turn `index`.
 *
 * The answer is in the *next* agent turn: resuming replays the approval node,
 * and its trace entry records which way the human went. Reading it from there
 * beats tracking a parallel copy of the decision in component state. */
function outcomeOf(turns: Turn[], index: number, lastAgentIndex: number): Outcome {
  if (index === lastAgentIndex) return 'pending';

  for (let i = index + 1; i < turns.length; i += 1) {
    const turn = turns[i];
    if (turn.role !== 'agent') continue;
    const detail = turn.response.trace.find((event) => event.node === 'approval')?.detail ?? '';
    if (detail.startsWith('approved')) return 'approved';
    if (detail.startsWith('denied')) return 'denied';
    if (detail.startsWith('revision')) return 'revised';
    break;
  }
  return 'revised';
}

const EXAMPLES = [
  'Why is the rate limit 100 requests per minute?',
  'What happens if a tenant sees another tenant’s task?',
  'Fix the rate limit boundary so the 101st request is rejected.',
];

export function ChatPanel() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const threadId = useRef<string | null>(null);

  const lastAgentIndex = turns.reduce((last, turn, i) => (turn.role === 'agent' ? i : last), -1);
  const latest = lastAgentIndex >= 0 ? turns[lastAgentIndex] : undefined;
  const pending = latest?.role === 'agent' ? latest.response : null;
  const awaiting = pending?.status === 'awaiting_approval';

  async function run(work: () => Promise<ChatResponse>) {
    setBusy(true);
    setError(null);
    try {
      const response = await work();
      threadId.current = response.thread_id;
      setTurns((previous) => [...previous, { role: 'agent', response }]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  }

  function submit(text: string) {
    if (!text.trim() || busy) return;
    setTurns((previous) => [...previous, { role: 'user', text }]);
    setDraft('');
    void run(() => sendMessage(text, threadId.current));
  }

  function decide(decision: string) {
    const id = threadId.current;
    if (!id) return;
    void run(() => sendDecision(id, decision));
  }

  return (
    <div className="layout">
      <div style={{ minWidth: 0 }}>
        {turns.length === 0 && !busy && (
          <div style={{ display: 'grid', gap: 14 }}>
            <p className="prose" style={{ margin: 0, color: 'var(--text-muted)' }}>
              Ask about TaskVault and the retrieval agent answers from its documentation. Ask
              for a change and the coding agent reads that same documentation, proposes a
              diff, and stops here for your approval before anything is written.
            </p>
            <div style={{ display: 'grid', gap: 6 }}>
              {EXAMPLES.map((example) => (
                <button key={example} className="example" onClick={() => submit(example)}>
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 20 }}>
          {turns.map((turn, index) =>
            turn.role === 'user' ? (
              <li key={index} style={{ display: 'flex', gap: 10 }}>
                <span aria-hidden style={{ color: 'var(--accent)' }}>
                  ▸
                </span>
                <span className="prose" style={{ margin: 0 }}>
                  {turn.text}
                </span>
              </li>
            ) : (
              <li key={index} className="enters" style={{ display: 'grid', gap: 12 }}>
                {/* justifySelf, or the grid stretches the badge across the column. */}
                {turn.response.intent && (
                  <span style={{ justifySelf: 'start' }}>
                    <Badge tone="neutral">{turn.response.intent}</Badge>
                  </span>
                )}

                {turn.response.status === 'awaiting_approval' && turn.response.proposal ? (
                  <ApprovalCard
                    proposal={turn.response.proposal}
                    diff={turn.response.diff}
                    violations={turn.response.violations ?? []}
                    busy={busy}
                    outcome={outcomeOf(turns, index, lastAgentIndex)}
                    onDecide={decide}
                  />
                ) : (
                  <p className="prose" style={{ margin: 0 }}>
                    {turn.response.reply}
                  </p>
                )}

                {turn.response.pull_request && (
                  <PullRequestCard pullRequest={turn.response.pull_request} />
                )}
              </li>
            ),
          )}
        </ol>

        {busy && (
          <p aria-live="polite" style={{ color: 'var(--text-faint)', marginTop: 20 }}>
            Running…
          </p>
        )}

        {error && (
          <p role="alert" style={{ color: 'var(--negative)', marginTop: 20 }}>
            {error}
          </p>
        )}

        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit(draft);
          }}
          style={{ display: 'flex', gap: 8, marginTop: 28 }}
        >
          <input
            className="field"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            disabled={busy || awaiting}
            placeholder={
              awaiting ? 'Answer the approval above to continue' : 'Ask, or request a change'
            }
            aria-label="Message"
            style={{ flex: 1 }}
          />
          <Button type="submit" variant="primary" disabled={busy || awaiting || !draft.trim()}>
            Send
          </Button>
        </form>
      </div>

      <aside className="rail">
        <TraceRail trace={pending?.trace ?? []} held={Boolean(awaiting)} />
        <Citations citations={pending?.citations ?? []} />
      </aside>
    </div>
  );
}
