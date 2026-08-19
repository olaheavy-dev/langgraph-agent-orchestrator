'use client';

import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'quiet';
};

export function Button({ variant = 'secondary', className, ...props }: ButtonProps) {
  return <button {...props} className={`btn btn-${variant} ${className ?? ''}`.trim()} />;
}

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: 'neutral' | 'accent' | 'positive' | 'negative';
  children: ReactNode;
}) {
  const color = {
    neutral: 'var(--text-muted)',
    accent: 'var(--accent)',
    positive: 'var(--positive)',
    negative: 'var(--negative)',
  }[tone];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        color,
        border: `1px solid currentColor`,
        borderRadius: 'var(--radius-sm)',
        padding: '1px 6px',
        fontSize: 11,
        fontWeight: 500,
        letterSpacing: '0.02em',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  );
}

export function Panel({
  children,
  accent = false,
  style,
}: {
  children: ReactNode;
  accent?: boolean;
  style?: React.CSSProperties;
}) {
  return (
    <div
      style={{
        background: 'var(--surface-raised)',
        border: `1px solid ${accent ? 'var(--accent)' : 'var(--border-subtle)'}`,
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/** A section label. Uppercase and faint, so it names a region without competing
    with the data inside it. */
export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: 'var(--text-faint)',
      }}
    >
      {children}
    </div>
  );
}
