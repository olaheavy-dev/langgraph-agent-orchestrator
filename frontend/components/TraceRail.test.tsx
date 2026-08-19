import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { TraceRail } from '@/components/TraceRail';

describe('TraceRail', () => {
  it('invites the reader instead of showing an empty list', () => {
    render(<TraceRail trace={[]} held={false} />);
    expect(screen.getByText(/nodes that run will appear here/i)).toBeInTheDocument();
  });

  it('lists each node with what it did and how long it took', () => {
    render(
      <TraceRail
        trace={[{ node: 'classifier', detail: 'routed to code', elapsed_ms: 412 }]}
        held={false}
      />,
    );
    expect(screen.getByText('classifier')).toBeInTheDocument();
    expect(screen.getByText('412ms')).toBeInTheDocument();
    expect(screen.getByText('routed to code')).toBeInTheDocument();
  });
});
