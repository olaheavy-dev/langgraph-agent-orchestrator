'use client';

import { useState } from 'react';

import { DiffView } from '@/components/DiffView';
import { Badge, Button, Panel } from '@/components/ui';
import type { CodeProposal, Outcome } from '@/lib/types';

const LABEL: Record<Outcome, string> = {
  pending: 'Awaiting approval',
  approved: 'Approved and applied',
  denied: 'Denied',
  revised: 'Superseded by a revision',
};

/* Inline rather than a modal. Approving a change means reading a diff, and a
   dialog that traps a 200-line diff in a scrolling box encourages approving
   without reading -- which is the one thing this gate exists to prevent. */

export function ApprovalCard({
  proposal,
  diff,
  violations,
  busy,
  outcome = 'pending',
  onDecide,
}: {
  proposal: CodeProposal;
  diff: string;
  violations: string[];
  busy: boolean;
  /** What happened to this proposal. Anything but 'pending' stays on the page as
      history and must not look decidable -- offering buttons for a change that
      was already decided is worse than showing nothing. The label has to say
      which decision it was: "superseded" on a change someone approved is a lie
      about their own action. */
  outcome?: Outcome;
  onDecide: (decision: string) => void;
}) {
  const decided = outcome !== 'pending';
  const [revising, setRevising] = useState(false);
  const [revision, setRevision] = useState('');

  return (
    <Panel accent={!decided} style={decided ? { opacity: 0.72 } : undefined}>
      <header
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'center',
          flexWrap: 'wrap',
          padding: '12px 14px',
          background: decided ? 'var(--surface-subtle)' : 'var(--accent-tint)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <Badge tone={outcome === 'approved' ? 'positive' : outcome === 'denied' ? 'negative' : decided ? 'neutral' : 'accent'}>
          {LABEL[outcome]}
        </Badge>
        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{proposal.branch}</span>
      </header>

      {violations.length > 0 && !decided && (
        <div
          role="alert"
          style={{
            padding: '12px 14px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'grid',
            gap: 6,
          }}
        >
          <strong style={{ color: 'var(--negative)', fontWeight: 600, fontSize: 12 }}>
            {violations.length === 1
              ? 'This change would be rejected in review'
              : `This change breaks ${violations.length} review rules`}
          </strong>
          <ul style={{ margin: 0, paddingLeft: 18, color: 'var(--text-muted)', fontSize: 12 }}>
            {violations.map((violation) => (
              <li key={violation}>{violation}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ padding: 14, display: 'grid', gap: 12 }}>
        <p className="prose" style={{ margin: 0, fontSize: 14 }}>
          {proposal.summary}
        </p>

        <dl style={{ margin: 0, display: 'grid', gap: 8, fontSize: 12 }}>
          <Field label="Why now" value={proposal.rationale} />
          <Field label="Verified by" value={proposal.verification} />
          <Field
            label="Grounded in"
            value={proposal.adrs_consulted.join(', ') || 'no documents cited'}
          />
        </dl>
      </div>

      <DiffView diff={diff} />

      {decided ? null : (
      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          padding: 14,
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        {revising ? (
          <form
            style={{ display: 'grid', gap: 8, width: '100%' }}
            onSubmit={(event) => {
              event.preventDefault();
              if (revision.trim()) onDecide(revision.trim());
            }}
          >
            <textarea
              autoFocus
              className="field"
              rows={3}
              value={revision}
              onChange={(event) => setRevision(event.target.value)}
              placeholder="What should it do differently?"
              style={{ resize: 'vertical' }}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <Button type="submit" variant="primary" disabled={busy || !revision.trim()}>
                Send revision
              </Button>
              <Button type="button" variant="quiet" onClick={() => setRevising(false)}>
                Cancel
              </Button>
            </div>
          </form>
        ) : (
          <>
            <Button variant="primary" disabled={busy} onClick={() => onDecide('approve')}>
              Approve and apply
            </Button>
            <Button disabled={busy} onClick={() => onDecide('deny')}>
              Deny
            </Button>
            <Button variant="quiet" disabled={busy} onClick={() => setRevising(true)}>
              Revise…
            </Button>
          </>
        )}
      </div>
      )}
    </Panel>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '92px 1fr', gap: 10 }}>
      <dt style={{ color: 'var(--text-faint)' }}>{label}</dt>
      <dd style={{ margin: 0, color: 'var(--text-muted)' }}>{value}</dd>
    </div>
  );
}
