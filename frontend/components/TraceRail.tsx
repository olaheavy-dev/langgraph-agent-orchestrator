'use client';

import type { TraceEvent } from '@/lib/types';
import { Eyebrow } from '@/components/ui';

/* The signature element: the path the graph actually took, as a pipeline.
   Every other surface in this interface stays quiet so that this one reads as a
   decision. A held approval is the only thing that ever animates. */

function Node({
  event,
  held,
  last,
}: {
  event: TraceEvent;
  held: boolean;
  last: boolean;
}) {
  return (
    <li style={{ display: 'grid', gridTemplateColumns: '12px 1fr', gap: 10, position: 'relative' }}>
      <div style={{ display: 'grid', justifyItems: 'center', gap: 2 }}>
        <span
          aria-hidden
          style={{
            width: 7,
            height: 7,
            marginTop: 6,
            borderRadius: '50%',
            background: held ? 'var(--accent)' : 'var(--border-interactive)',
            boxShadow: held ? '0 0 0 3px var(--accent-tint)' : 'none',
            animation: held ? 'held 1.6s ease-in-out infinite' : 'none',
          }}
        />
        {!last && (
          <span
            aria-hidden
            style={{ width: 1, flex: 1, minHeight: 18, background: 'var(--border-subtle)' }}
          />
        )}
      </div>

      <div style={{ paddingBottom: last ? 0 : 14, minWidth: 0 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 600, color: held ? 'var(--accent)' : 'var(--text)' }}>
            {event.node}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>
            {event.elapsed_ms}ms
          </span>
        </div>
        {event.detail && (
          <div style={{ fontSize: 12, color: 'var(--text-muted)', overflowWrap: 'anywhere' }}>
            {event.detail}
          </div>
        )}
      </div>
    </li>
  );
}

export function TraceRail({ trace, held }: { trace: TraceEvent[]; held: boolean }) {
  return (
    <section aria-label="Graph trace">
      <Eyebrow>Run</Eyebrow>
      <style>{`@keyframes held { 0%,100% { opacity: 1 } 50% { opacity: .35 } }`}</style>

      {trace.length === 0 ? (
        <p style={{ color: 'var(--text-faint)', fontSize: 12, marginTop: 10 }}>
          The nodes that run will appear here, in order, with the time each took.
        </p>
      ) : (
        <ol style={{ listStyle: 'none', margin: '12px 0 0', padding: 0 }}>
          {trace.map((event, index) => (
            <Node
              key={`${event.node}-${index}`}
              event={event}
              held={held && index === trace.length - 1}
              last={index === trace.length - 1}
            />
          ))}
        </ol>
      )}
    </section>
  );
}
