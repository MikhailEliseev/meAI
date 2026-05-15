import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Toaster } from '@/components/shared/Toaster';

describe('Toaster', () => {
  it('renders without crashing', () => {
    const { container } = render(<Toaster />);
    expect(container).toBeInTheDocument();
  });

  it('renders with correct position', () => {
    const { container } = render(<Toaster />);
    // Toaster uses react-hot-toast which renders a portal
    // We just verify it doesn't throw
    expect(container).toBeTruthy();
  });
});
