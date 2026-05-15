import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ActivityFeed } from '@/components/collaboration/ActivityFeed'
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

describe('ActivityFeed', () => {
  const mockActivities = [
    {
      id: '1',
      user_id: 'user-1',
      user_name: 'John Doe',
      user_avatar: null,
      type: 'task_created',
      entity_type: 'task',
      entity_id: 'task-1',
      description: 'Created a new task',
      created_at: new Date().toISOString(),
    },
    {
      id: '2',
      user_id: 'user-2',
      user_name: 'Jane Smith',
      user_avatar: null,
      type: 'comment_added',
      entity_type: 'task',
      entity_id: 'task-1',
      description: 'Added a comment',
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: '3',
      user_id: 'user-1',
      user_name: 'John Doe',
      user_avatar: null,
      type: 'task_completed',
      entity_type: 'task',
      entity_id: 'task-2',
      description: 'Completed a task',
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock Supabase query chain - create object first, then assign methods
    const mockQuery: any = {}
    mockQuery.select = vi.fn().mockReturnValue(mockQuery)
    mockQuery.eq = vi.fn().mockReturnValue(mockQuery)
    mockQuery.order = vi.fn().mockReturnValue(mockQuery)
    mockQuery.limit = vi.fn().mockReturnValue(mockQuery)
    // Make the query object thenable so it can be awaited
    mockQuery.then = vi.fn((resolve) => resolve({ data: mockActivities, error: null }))

    vi.mocked(supabase.from).mockReturnValue(mockQuery)

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

  it('should render activity feed with activities', async () => {
    render(<ActivityFeed />)

    await waitFor(() => {
      expect(screen.getByText('Activity Feed')).toBeInTheDocument()
      expect(screen.getAllByText('John Doe').length).toBeGreaterThan(0)
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    })
  })

  it('should show loading state', () => {
    const mockQuery = {
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      order: vi.fn().mockReturnThis(),
      limit: vi.fn().mockReturnValue(new Promise(() => {})),
    }
    vi.mocked(supabase.from).mockReturnValue(mockQuery as any)

    render(<ActivityFeed />)

    // Check for loading spinner
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('should filter activities by type', async () => {
    render(<ActivityFeed />)

    await waitFor(() => {
      expect(screen.getByText('Activity Feed')).toBeInTheDocument()
    })

    // Filter by tasks
    const tasksButton = screen.getByText('Tasks')
    fireEvent.click(tasksButton)

    await waitFor(() => {
      expect(screen.getByText('Created a new task')).toBeInTheDocument()
      expect(screen.getByText('Completed a task')).toBeInTheDocument()
      expect(screen.queryByText('Added a comment')).not.toBeInTheDocument()
    })

    // Filter by comments
    const commentsButton = screen.getByText('Comments')
    fireEvent.click(commentsButton)

    await waitFor(() => {
      expect(screen.getByText('Added a comment')).toBeInTheDocument()
      expect(screen.queryByText('Created a new task')).not.toBeInTheDocument()
    })

    // Show all
    const allButton = screen.getByText('All')
    fireEvent.click(allButton)

    await waitFor(() => {
      expect(screen.getByText('Created a new task')).toBeInTheDocument()
      expect(screen.getByText('Added a comment')).toBeInTheDocument()
      expect(screen.getByText('Completed a task')).toBeInTheDocument()
    })
  })

  it('should show empty state when no activities', async () => {
    vi.mocked(supabase.from).mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      order: vi.fn().mockReturnThis(),
      limit: vi.fn().mockResolvedValue({ data: [], error: null }),
    } as any)

    render(<ActivityFeed />)

    await waitFor(() => {
      expect(screen.getByText('No activity yet')).toBeInTheDocument()
    })
  })

  it('should display activity icons correctly', async () => {
    render(<ActivityFeed />)

    await waitFor(() => {
      expect(screen.getByText('Activity Feed')).toBeInTheDocument()
    })

    // Check for activity type badges
    expect(screen.getByText(/task created/i)).toBeInTheDocument()
    expect(screen.getByText(/comment added/i)).toBeInTheDocument()
    expect(screen.getByText(/task completed/i)).toBeInTheDocument()
  })

  it('should format time correctly', async () => {
    render(<ActivityFeed />)

    await waitFor(() => {
      expect(screen.getByText('Activity Feed')).toBeInTheDocument()
    })

    // Should show relative time
    const timeElements = screen.getAllByText(/ago/)
    expect(timeElements.length).toBeGreaterThan(0)
  })

  it('should filter by project ID', async () => {
    // Create fresh mock for this test
    const mockQuery: any = {}
    mockQuery.select = vi.fn().mockReturnValue(mockQuery)
    mockQuery.eq = vi.fn().mockReturnValue(mockQuery)
    mockQuery.order = vi.fn().mockReturnValue(mockQuery)
    mockQuery.limit = vi.fn().mockReturnValue(mockQuery)
    mockQuery.then = vi.fn((resolve) => resolve({ data: mockActivities, error: null }))

    vi.mocked(supabase.from).mockReturnValue(mockQuery)

    render(<ActivityFeed projectId="project-1" />)

    await waitFor(() => {
      expect(mockQuery.eq).toHaveBeenCalledWith('project_id', 'project-1')
    })
  })

  it('should filter by user ID', async () => {
    // Create fresh mock for this test
    const mockQuery: any = {}
    mockQuery.select = vi.fn().mockReturnValue(mockQuery)
    mockQuery.eq = vi.fn().mockReturnValue(mockQuery)
    mockQuery.order = vi.fn().mockReturnValue(mockQuery)
    mockQuery.limit = vi.fn().mockReturnValue(mockQuery)
    mockQuery.then = vi.fn((resolve) => resolve({ data: mockActivities, error: null }))

    vi.mocked(supabase.from).mockReturnValue(mockQuery)

    render(<ActivityFeed userId="user-1" />)

    await waitFor(() => {
      expect(mockQuery.eq).toHaveBeenCalledWith('user_id', 'user-1')
    })
  })
})
