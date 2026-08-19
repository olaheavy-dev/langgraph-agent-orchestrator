import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ApprovalCard } from '@/components/ApprovalCard';
import type { CodeProposal, Outcome } from '@/lib/types';

const proposal: CodeProposal = {
  summary: 'Reject the 101st request.',
  rationale: 'adr-003 requires it.',
  verification: 'A boundary test fails without it.',
  adrs_consulted: ['adr-003-rate-limiting.md'],
  branch: 'fix/rate-limit-boundary',
  commit_message: 'fix(rate_limit): reject the 101st request',
  edits: [],
};

function setup(busy = false, violations: string[] = [], outcome: Outcome = 'pending') {
  const onDecide = vi.fn();
  render(
    <ApprovalCard
      proposal={proposal}
      diff={'-a\n+b'}
      violations={violations}
      busy={busy}
      outcome={outcome}
      onDecide={onDecide}
    />,
  );
  return onDecide;
}

describe('ApprovalCard', () => {
  it('shows what the change is grounded in, so a reviewer can check it', () => {
    setup();
    expect(screen.getByText('adr-003-rate-limiting.md')).toBeInTheDocument();
    expect(screen.getByText('fix/rate-limit-boundary')).toBeInTheDocument();
  });

  it('sends approve and deny as decisions', async () => {
    const onDecide = setup();
    await userEvent.click(screen.getByRole('button', { name: /approve and apply/i }));
    expect(onDecide).toHaveBeenCalledWith('approve');

    await userEvent.click(screen.getByRole('button', { name: /^deny$/i }));
    expect(onDecide).toHaveBeenCalledWith('deny');
  });

  it('sends revision text verbatim, preserving its casing', async () => {
    const onDecide = setup();
    await userEvent.click(screen.getByRole('button', { name: /revise/i }));
    await userEvent.type(screen.getByPlaceholderText(/differently/i), 'Use a Leaky Bucket');
    await userEvent.click(screen.getByRole('button', { name: /send revision/i }));
    expect(onDecide).toHaveBeenCalledWith('Use a Leaky Bucket');
  });

  it('warns before the approve button when review rules are broken', () => {
    setup(false, ['adr-drift: architectural code changed with no ADR update.']);
    const warning = screen.getByRole('alert');
    expect(warning).toHaveTextContent(/would be rejected in review/i);
    expect(warning).toHaveTextContent(/adr-drift/);
  });

  it('says nothing when the proposal is clean', () => {
    setup();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('offers no decision once a revision has replaced it', () => {
    setup(false, ['adr-drift: no ADR update.'], 'revised');
    expect(screen.getByText(/superseded by a revision/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /approve and apply/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /revise/i })).not.toBeInTheDocument();
    // Its warning goes too: it described a change that no longer exists.
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('names the decision that was actually made, not a generic one', () => {
    // Calling an approved change "superseded" misreports the reviewer's own act.
    const { unmount } = render(<div />);
    unmount();
    setup(false, [], 'approved');
    expect(screen.getByText(/approved and applied/i)).toBeInTheDocument();
    expect(screen.queryByText(/superseded/i)).not.toBeInTheDocument();
  });

  it('still shows what a decided proposal was, as history', () => {
    setup(false, [], 'approved');
    expect(screen.getByText('fix/rate-limit-boundary')).toBeInTheDocument();
    expect(screen.getByText(/reject the 101st request/i)).toBeInTheDocument();
  });

  it('disables every decision while a request is in flight', () => {
    setup(true);
    expect(screen.getByRole('button', { name: /approve and apply/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^deny$/i })).toBeDisabled();
  });
});
