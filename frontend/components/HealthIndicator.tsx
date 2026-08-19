'use client';

import { useEffect, useState } from 'react';

import { getHealth } from '@/lib/api';
import type { Health } from '@/lib/types';

export function HealthIndicator() {
  const [health, setHealth] = useState<Health | null | 'loading'>('loading');

  useEffect(() => {
    let live = true;
    getHealth().then((result) => live && setHealth(result));
    return () => {
      live = false;
    };
  }, []);

  if (health === 'loading') {
    return <span style={{ color: 'var(--text-faint)', fontSize: 12 }}>checking…</span>;
  }

  if (health === null) {
    return (
      <span style={{ color: 'var(--negative)', fontSize: 12 }}>
        API unreachable — is it running?
      </span>
    );
  }

  return (
    <span style={{ color: 'var(--text-faint)', fontSize: 12 }}>
      {health.corpus_documents} documents indexed
    </span>
  );
}
