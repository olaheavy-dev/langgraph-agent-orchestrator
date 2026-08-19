'use client';

import type { Citation } from '@/lib/types';
import { Eyebrow } from '@/components/ui';

/* What the answer was drawn from. Shown for retrieval answers and for coding
   proposals alike -- the point of the project is that the coding agent reads the
   same documents, so hiding them on that branch would hide the argument. */

export function Citations({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <section aria-label="Retrieved passages" style={{ marginTop: 28 }}>
      <Eyebrow>Sources</Eyebrow>
      <ul style={{ listStyle: 'none', margin: '12px 0 0', padding: 0, display: 'grid', gap: 12 }}>
        {citations.map((citation, index) => (
          <li key={`${citation.source}-${index}`}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
              <span style={{ color: 'var(--accent)', fontSize: 12, fontWeight: 600 }}>
                {citation.source}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>
                {citation.score.toFixed(2)}
              </span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{citation.heading}</div>
            <p
              style={{
                margin: '4px 0 0',
                fontSize: 12,
                color: 'var(--text-faint)',
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {citation.text}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
