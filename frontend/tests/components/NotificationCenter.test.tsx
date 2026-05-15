import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NotificationCenter } from '@/components/collaboration/NotificationCenter'
import { supabase } from '@/lib/supabase'

// Mock Supabase
vi.mock('@/lib/supabase', () => ({
  supabase: {
    from: vi.fn(),
    channel: vi.fn(),
    removeChannel: vi.fn(),
  },
}))

// Mock useRealtime
vi.mock('@/hooks/useRealtime', () => ({
  useRealtime: vi.fn(),
}))

import { useRealtime } from '@/hooks/useRealtime'

const mockUseRealtime = vi.mocked(useRealtime)

describe('NotificationCenter', () => {
  const mockNotifications = [
    {
      id: '1',
      user_id: 'user-1',
      type: 'task_assigned',
      title: 'New Task',
      message: 'You have been assigned a task',
      link: '/tasks/1',
      read: false,
      created_at: new Date().toISOString(),
    },
    {
      id: '2',
      user_id: 'user-1',
      type: 'comment_added',
      title: 'New Comment',
      message: 'Someone commented on your task',
      link: '/tasks/2',
      read: true,
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock Supabase query
    const mockSelect = vi.fn().mockReturnThis()
    const mockEq = vi.fn().mockReturnThis()
    const mockOrder = vi.fn().mockReturnThis()
    const mockLimit = vi.fn().mockResolvedValue({ data: mockNotifications, error: null })

    vi.mocked(supabase.from).mockReturnValue({
      select: mockSelect,
      update: vi.fn().mockReturnThis(),
      eq: mockEq,
      order: mockOrder,
      limit: mockLimit,
    } as any)

    mockUseRealtime.mockReturnValue({
      status: 'connected',
      reconnect: vi.fn(),
      disconnect: vi.fn(),
      isConnected: true,
      isConnecting: false,
      isDisconnected: false,
      isError: false,
      reconnectAttempts: 0,
    })
  })

  it('should render notification bell with unread count', async () => {
    render(<NotificationCenter userId="user-1" />)

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })

  it('should show notifications when bell is clicked', async () => {
    render(<NotificationCenter userId="user-1" />)

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    const bell = screen.getByRole('button')
    fireEvent.click(bell)

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument()
      expect(screen.getByText('New Task')).toBeInTheDocument()
      expect(screen.getByText('New Comment')).toBeInTheDocument()
    })
  })

  it('should mark notification as read when clicked', async () => {
    const mockUpdate = vi.fn().mockReturnThis()
    const mockEq = vi.fn().mockResolvedValue({ data: null, error: null })

    const mockSelect = vi.fn().mockReturnThis()
    const mockSelectEq = vi.fn().mockReturnThis()
    const mockOrder = vi.fn().mockReturnThis()
    const mockLimit = vi.fn().mockResolvedValue({ data: mockNotifications, error: null })

    vi.mocked(supabase.from).mockImplementation((table: string) => {
      if (table === 'notifications') {
        return {
          select: mockSelect,
          update: mockUpdate,
          eq: mockSelectEq,
          order: mockOrder,
          limit: mockLimit,
        } as any
      }
      return {} as any
    })

    render(<NotificationCenter userId="user-1" />)

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    const bell = screen.getByRole('button')
    fireEvent.click(bell)

    await waitFor(() => {
      expect(screen.getByText('New Task')).toBeInTheDocument()
    })

    const notification = screen.getByText('New Task').closest('div')
    if (notification) {
      fireEvent.click(notification)
    }

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith({ read: true })
    })
  })

  it('should mark all as read', async () => {
    const mockUpdate = vi.fn().mockReturnThis()
    const mockEq = vi.fn().mockReturnThis()

    vi.mocked(supabase.from).mockReturnValue({
      select: vi.fn().mockReturnThis(),
      update: mockUpdate,
      eq: mockEq,
      order: vi.fn().mockReturnThis(),
      limit: vi.fn().mockResolvedValue({ data: mockNotifications, error: null }),
    } as any)

    render(<NotificationCenter userId="user-1" />)

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    const bell = screen.getByRole('button')
    fireEvent.click(bell)

    await waitFor(() => {
      expect(screen.getByText('Mark all as read')).toBeInTheDocument()
    })

    const markAllButton = screen.getByText('Mark all as read')
    fireEvent.click(markAllButton)

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith({ read: true })
    })
  })

  it('should show empty state when no notifications', async () => {
    vi.mocked(supabase.from).mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      order: vi.fn().mockReturnThis(),
      limit: vi.fn().mockResolvedValue({ data: [], error: null }),
      update: vi.fn().mockReturnThis(),
    } as any)

    render(<NotificationCenter userId="user-1" />)

    const bell = screen.getByRole('button')
    fireEvent.click(bell)

    await waitFor(() => {
      expect(screen.getByText('No notifications yet')).toBeInTheDocument()
    })
  })

  it('should format time correctly', async () => {
    render(<NotificationCenter userId="user-1" />)

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    const bell = screen.getByRole('button')
    fireEvent.click(bell)

    await waitFor(() => {
      expect(screen.getByText(/ago/)).toBeInTheDocument()
    })
  })
})
