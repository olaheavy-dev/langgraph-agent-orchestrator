import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'Agent Orchestrator',
  description:
    'A LangGraph orchestrator that routes between a chat agent, a retrieval agent and a coding agent that pauses for human approval.',
};

/* Applied before first paint. Reading the stored choice from an effect would let
   the page render in the wrong theme and visibly correct itself. */
const THEME_SCRIPT = `
try {
  var stored = localStorage.getItem('orchestrator-theme');
  if (stored === 'light' || stored === 'dark') {
    document.documentElement.setAttribute('data-theme', stored);
  }
} catch (e) {}
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
