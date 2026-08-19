'use client';

import { DiffView } from '@/components/DiffView';
import { Badge, Panel } from '@/components/ui';
import type { PullRequest } from '@/lib/types';

export function PullRequestCard({ pullRequest }: { pullRequest: PullRequest }) {
  const failed = pullRequest.checks.filter((check) => !check.passed);

  return (
    <Panel>
      <header
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'center',
          flexWrap: 'wrap',
          padding: '12px 14px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <Badge tone={failed.length ? 'negative' : 'positive'}>
          {failed.length ? `${failed.length} check failed` : 'All checks passed'}
        </Badge>
        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{pullRequest.branch}</span>
      </header>

      <div style={{ padding: 14, display: 'grid', gap: 10 }}>
        <strong style={{ fontWeight: 600 }}>{pullRequest.title}</strong>
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 4 }}>
          {pullRequest.checks.map((check) => (
            <li key={check.name} style={{ display: 'flex', gap: 8, fontSize: 12 }}>
              <span
                aria-hidden
                style={{ color: check.passed ? 'var(--positive)' : 'var(--negative)' }}
              >
                {check.passed ? '✓' : '✕'}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>{check.name}</span>
              {/* Never colour alone: the word carries the state too. */}
              <span style={{ color: 'var(--text-faint)' }}>
                {check.passed ? 'passed' : 'failed'}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <details>
        <summary
          style={{
            padding: '10px 14px',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            fontSize: 12,
            borderTop: '1px solid var(--border-subtle)',
          }}
        >
          Pull request body
        </summary>
        <pre
          style={{
            margin: 0,
            padding: 14,
            overflowX: 'auto',
            fontSize: 12,
            color: 'var(--text-muted)',
            background: 'var(--surface-subtle)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {pullRequest.body}
        </pre>
      </details>

      <DiffView diff={pullRequest.diff} />
    </Panel>
  );
}
