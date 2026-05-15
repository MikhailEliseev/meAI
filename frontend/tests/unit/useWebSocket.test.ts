import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with disconnected status', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.status).toBe('disconnected');
    expect(result.current.isConnected).toBe(false);
    expect(result.current.isConnecting).toBe(false);
  });

  it('provides send function', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(typeof result.current.send).toBe('function');
  });

  it('provides connect function', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(typeof result.current.connect).toBe('function');
  });

  it('provides disconnect function', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(typeof result.current.disconnect).toBe('function');
  });

  it('tracks reconnection attempts', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.reconnectAttempts).toBe(0);
  });

  it('accepts onConnect callback', () => {
    const onConnect = vi.fn();
    const { result } = renderHook(() => useWebSocket({ onConnect }));

    expect(result.current).toBeDefined();
  });

  it('accepts onMessage callback', () => {
    const onMessage = vi.fn();
    const { result } = renderHook(() => useWebSocket({ onMessage }));

    expect(result.current).toBeDefined();
  });

  it('accepts onDisconnect callback', () => {
    const onDisconnect = vi.fn();
    const { result } = renderHook(() => useWebSocket({ onDisconnect }));

    expect(result.current).toBeDefined();
  });
});
