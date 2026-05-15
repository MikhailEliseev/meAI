import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useRealtime } from '@/hooks/useRealtime'
import { supabase } from '@/lib/supabase'

// Mock Supabase
vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn(),
    removeChannel: vi.fn(),
  },
}))

describe('useRealtime', () => {
  let mockChannel: any

  beforeEach(() => {
    vi.clearAllMocks()

    mockChannel = {
      on: vi.fn().mockReturnThis(),
      subscribe: vi.fn((callback) => {
        // Immediately call callback with SUBSCRIBED for successful connection
        setTimeout(() => callback('SUBSCRIBED'), 0)
        return mockChannel
      }),
    }

    vi.mocked(supabase.channel).mockReturnValue(mockChannel)
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('should initialize with connecting status', () => {
    const { result } = renderHook(() =>
      useRealtime({
        table: 'metrics',
        onInsert: vi.fn(),
      })
    )

    expect(result.current.status).toBe('connecting')
  })

  it('should connect successfully', async () => {
    const { result } = renderHook(() =>
      useRealtime({
        table: 'metrics',
        onInsert: vi.fn(),
      })
    )

    await waitFor(() => {
      expect(result.current.status).toBe('connected')
      expect(result.current.isConnected).toBe(true)
    })
  })

  it('should handle connection error', async () => {
    mockChannel.subscribe = vi.fn((callback) => {
      setTimeout(() => callback('CHANNEL_ERROR'), 0)
      return mockChannel
    })

    const { result } = renderHook(() =>
      useRealtime({
        table: 'metrics',
        onInsert: vi.fn(),
        autoReconnect: false,
      })
    )

    await waitFor(() => {
      expect(result.current.status).toBe('error')
      expect(result.current.isError).toBe(true)
    })
  })

  it('should call onInsert when INSERT event occurs', async () => {
    const onInsert = vi.fn()
    const { result } = renderHook(() =>
      useRealtime({
        table: 'metrics',
        onInsert,
      })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    // Get the INSERT handler
    const insertHandler = mockChannel.on.mock.calls.find(
      (call: any) => call[1].event === 'INSERT'
    )?.[2]

    expect(insertHandler).toBeDefined()

    // Simulate INSERT event
    const newMetric = { id: '1', value: 100 }
    act(() => {
      insertHandler({ new: newMetric })
    })

    expect(onInsert).toHaveBeenCalledWith(newMetric)
  })

  it('should call onUpdate when UPDATE event occurs', async () => {
    const onUpdate = vi.fn()
    const { result } = renderHook(() =>
      useRealtime({
        table: 'metrics',
        onUpdate,
      })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const updateHandler = mockChannel.on.mock.calls.find(
      (call: any) => call[1].event === 'UPDATE'
    )?.[2]

    const updatedMetric = { id: '1', value: 200 }
    act(() => {
      updateHandler({ new: updatedMetric })
    })

    expect(onUpdate).toHaveBeenCalledWith(updatedMetric)
  })

  it('should call onDelete when DELETE event occurs', async () => {
    const onDelete = vi.fn()
    const { result } = renderHook(() =>
      useRealtime({
        table: 'metrics',
        onDelete,
      })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const deleteHandler = mockChannel.on.mock.calls.find(
      (call: any) => call[1].event === 'DELETE'
    )?.[2]

    const deletedMetric = { id: '1' }
    act(() => {
      deleteHandler({ old: deletedMetric })
    })

    expect(onDelete).toHaveBeenCalledWith(deletedMetric)
  })

  it('should disconnect and cleanup on unmount', async () => {
    const { unmount } = renderHook(() =>
      useRealtime({
        table: 'metrics',
        onInsert: vi.fn(),
      })
    )

    await waitFor(() => {
      expect(supabase.channel).toHaveBeenCalled()
    })

    unmount()

    expect(supabase.removeChannel).toHaveBeenCalledWith(mockChannel)
  })
})
