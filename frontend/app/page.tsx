import { ChatPanel } from '@/components/ChatPanel';
import { HealthIndicator } from '@/components/HealthIndicator';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function Page() {
  return (
    <main
      style={{
        maxWidth: 1120,
        margin: '0 auto',
        padding: '32px 24px 72px',
        display: 'grid',
        gap: 32,
      }}
    >
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          flexWrap: 'wrap',
          paddingBottom: 20,
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600, letterSpacing: '-0.01em' }}>
          agent-orchestrator
        </h1>
        <span style={{ color: 'var(--text-faint)' }}>/</span>
        <HealthIndicator />
        <div style={{ marginLeft: 'auto' }}>
          <ThemeToggle />
        </div>
      </header>

      <ChatPanel />

      <style>{`
        .layout { display: grid; grid-template-columns: 1fr; gap: 40px; }
        .rail { min-width: 0; }
        @media (min-width: 900px) {
          .layout { grid-template-columns: minmax(0, 1fr) 260px; gap: 48px; }
          .rail {
            position: sticky;
            top: 32px;
            align-self: start;
            border-left: 1px solid var(--border-subtle);
            padding-left: 24px;
          }
        }
      `}</style>
    </main>
  );
}
