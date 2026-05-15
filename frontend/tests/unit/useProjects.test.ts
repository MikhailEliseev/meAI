import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useProjects } from '@/hooks/useProjects';

// Mock fetch
global.fetch = vi.fn();

describe('useProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with loading state', () => {
    const { result } = renderHook(() => useProjects());

    expect(result.current.loading).toBe(true);
    expect(result.current.projects).toEqual([]);
    expect(result.current.error).toBe(null);
  });

  it('fetches projects on mount', async () => {
    const mockProjects = [
      { id: '1', name: 'Project 1', state: 'started' },
      { id: '2', name: 'Project 2', state: 'planned' },
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: mockProjects }),
    });

    const { result } = renderHook(() => useProjects());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.projects).toEqual(mockProjects);
    expect(result.current.error).toBe(null);
  });

  it('handles fetch error', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    });

    const { result } = renderHook(() => useProjects());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.projects).toEqual([]);
    expect(result.current.error).toContain('Failed to fetch projects');
  });

  it('provides refetch function', async () => {
    const mockProjects = [{ id: '1', name: 'Project 1', state: 'started' }];

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ projects: mockProjects }),
    });

    const { result } = renderHook(() => useProjects());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(typeof result.current.refetch).toBe('function');

    // Call refetch
    await result.current.refetch();

    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('filters by teamId when provided', async () => {
    const mockProjects = [{ id: '1', name: 'Project 1', state: 'started' }];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: mockProjects }),
    });

    renderHook(() => useProjects('team-123'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/linear/projects?teamId=team-123');
    });
  });
});
