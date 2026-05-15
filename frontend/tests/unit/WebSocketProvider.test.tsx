import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WebSocketProvider } from '@/components/dashboard/WebSocketProvider';

describe('WebSocketProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders children', () => {
    vi.mock('@/hooks/useNotifications', () => ({
      useNotifications: () => ({
        status: 'connected',
        isConnected: true,
      }),
    }));

    render(
      <WebSocketProvider>
        <div>Test Content</div>
      </WebSocketProvider>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders without errors', () => {
    const { container } = render(
      <WebSocketProvider>
        <div>Test Content</div>
      </WebSocketProvider>
    );

    expect(container).toBeInTheDocument();
  });
});
