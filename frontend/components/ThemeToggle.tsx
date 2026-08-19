'use client';

import { useSyncExternalStore } from 'react';

const KEY = 'orchestrator-theme';

/** Subscribe to both the things that can change the resolved theme: an explicit
    choice on the root element, and the system preference behind it. */
function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  const media = window.matchMedia('(prefers-color-scheme: dark)');
  media.addEventListener('change', onChange);

  return () => {
    observer.disconnect();
    media.removeEventListener('change', onChange);
  };
}

/** Read what the document is actually showing rather than mirroring it into
    state: one source of truth, and no setState-in-effect. */
function resolvedTheme(): 'light' | 'dark' {
  const explicit = document.documentElement.getAttribute('data-theme');
  if (explicit === 'light' || explicit === 'dark') return explicit;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function ThemeToggle() {
  // The server has no theme to read, so it renders the light-mode label and the
  // client corrects it on hydration. The page itself is already correct by then:
  // the inline script in <head> set the attribute before first paint.
  const theme = useSyncExternalStore(subscribe, resolvedTheme, () => 'light' as const);

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem(KEY, next);
  }

  return (
    <button
      onClick={toggle}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
      className="icon-button"
    >
      <span aria-hidden>{theme === 'dark' ? '☾' : '☀'}</span>
    </button>
  );
}
