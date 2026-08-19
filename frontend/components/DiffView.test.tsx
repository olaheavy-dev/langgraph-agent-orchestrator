import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DiffView } from '@/components/DiffView';

describe('DiffView', () => {
  it('says so when a proposal changes nothing, rather than showing an empty box', () => {
    render(<DiffView diff="   " />);
    expect(screen.getByText(/changes no files/i)).toBeInTheDocument();
  });

  it('renders every line of the diff', () => {
    render(<DiffView diff={'@@ -1 +1 @@\n-old\n+new'} />);
    expect(screen.getByText('-old')).toBeInTheDocument();
    expect(screen.getByText('+new')).toBeInTheDocument();
  });
});
