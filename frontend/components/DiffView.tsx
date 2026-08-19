'use client';

/* A unified diff, coloured by line kind. Wide content scrolls inside its own
   container so the page body never does. */

function lineStyle(line: string): React.CSSProperties {
  if (line.startsWith('+++') || line.startsWith('---'))
    return { color: 'var(--text-faint)' };
  if (line.startsWith('@@')) return { color: 'var(--accent)' };
  if (line.startsWith('+'))
    return { background: 'var(--diff-add-bg)', color: 'var(--diff-add-text)' };
  if (line.startsWith('-'))
    return { background: 'var(--diff-del-bg)', color: 'var(--diff-del-text)' };
  return { color: 'var(--text-muted)' };
}

export function DiffView({ diff }: { diff: string }) {
  if (!diff.trim()) {
    return (
      <p style={{ padding: 14, margin: 0, color: 'var(--text-faint)', fontSize: 12 }}>
        This proposal changes no files.
      </p>
    );
  }

  return (
    <pre
      aria-label="Proposed changes"
      style={{
        margin: 0,
        padding: '10px 0',
        overflowX: 'auto',
        background: 'var(--surface-subtle)',
        fontSize: 12,
        lineHeight: 1.6,
      }}
    >
      {diff.split('\n').map((line, index) => (
        <code
          key={index}
          style={{ display: 'block', padding: '0 14px', whiteSpace: 'pre', ...lineStyle(line) }}
        >
          {line || ' '}
        </code>
      ))}
    </pre>
  );
}
