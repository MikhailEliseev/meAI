import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useIssues } from '@/hooks/useIssues';

// Mock fetch
global.fetch = vi.fn();

describe('useIssues', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with loading state', () => {
    const { result } = renderHook(() => useIssues('project-1'));

    expect(result.current.loading).toBe(true);
    expect(result.current.issues).toEqual([]);
    expect(result.current.error).toBe(null);
  });

  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHook(() => useIssues());

    expect(result.current.loading).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('fetches issues for project', async () => {
    const mockIssues = [
      { id: '1', title: 'Task 1', state: { name: 'In Progress' }, priority: 2 },
      { id: '2', title: 'Task 2', state: { name: 'Done' }, priority: 1 },
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ issues: mockIssues }),
    });

    const { result } = renderHook(() => useIssues('project-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.issues).toEqual(mockIssues);
    expect(result.current.error).toBe(null);
  });

  it('handles fetch error', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found',
    });

    const { result } = renderHook(() => useIssues('project-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.issues).toEqual([]);
    expect(result.current.error).toContain('Failed to fetch issues');
  });

  it('provides refetch function', async () => {
    const mockIssues = [{ id: '1', title: 'Task 1', state: { name: 'Todo' }, priority: 0 }];

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ issues: mockIssues }),
    });

    const { result } = renderHook(() => useIssues('project-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(typeof result.current.refetch).toBe('function');

    // Call refetch
    await result.current.refetch();

    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('includes projectId in fetch URL', async () => {
    const mockIssues = [{ id: '1', title: 'Task 1', state: { name: 'Todo' }, priority: 0 }];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ issues: mockIssues }),
    });

    renderHook(() => useIssues('project-123'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/linear/issues?projectId=project-123');
    });
  });
});
