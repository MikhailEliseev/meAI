import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { TaskAssigner } from '@/components/collaboration/TaskAssigner'
import { supabase } from '@/lib/supabase'

// Mock Supabase
vi.mock('@/lib/supabase', () => ({
  supabase: {
    from: vi.fn(),
  },
}))

describe('TaskAssigner', () => {
  const mockTeamMembers = [
    {
      id: 'member-1',
      name: 'John Doe',
      email: 'john@example.com',
      role: 'member',
      skills: ['react', 'typescript', 'testing'],
      max_tasks: 5,
      current_tasks: 2,
      availability: 'available',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'member-2',
      name: 'Jane Smith',
      email: 'jane@example.com',
      role: 'member',
      skills: ['python', 'django', 'postgresql'],
      max_tasks: 5,
      current_tasks: 1,
      availability: 'available',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'member-3',
      name: 'Bob Wilson',
      email: 'bob@example.com',
      role: 'member',
      skills: ['react', 'node', 'mongodb'],
      max_tasks: 3,
      current_tasks: 3,
      availability: 'available',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock Supabase query
    const mockSelect = vi.fn().mockReturnThis()
    const mockEq = vi.fn().mockReturnThis()
    const mockOrder = vi.fn().mockResolvedValue({ data: mockTeamMembers, error: null })
    const mockInsert = vi.fn().mockReturnThis()
    const mockUpdate = vi.fn().mockReturnThis()
    const mockSingle = vi.fn().mockResolvedValue({ data: { id: 'assignment-1' }, error: null })

    vi.mocked(supabase.from).mockReturnValue({
      select: mockSelect,
      eq: mockEq,
      order: mockOrder,
      insert: mockInsert,
      update: mockUpdate,
      single: mockSingle,
    } as any)
  })

  it('should render assign button', () => {
    render(<TaskAssigner taskId="task-1" />)

    expect(screen.getByText('Assign Task')).toBeInTheDocument()
  })

  it('should show team members when button is clicked', async () => {
    render(<TaskAssigner taskId="task-1" />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
      expect(screen.getByText('Bob Wilson')).toBeInTheDocument()
    })
  })

  it('should show recommended assignee based on skills', async () => {
    render(<TaskAssigner taskId="task-1" requiredSkills={['react', 'typescript']} />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('⭐ Recommended')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })
  })

  it('should show required skills', async () => {
    render(<TaskAssigner taskId="task-1" requiredSkills={['react', 'typescript']} />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('Required skills:')).toBeInTheDocument()
      expect(screen.getByText('react')).toBeInTheDocument()
      expect(screen.getByText('typescript')).toBeInTheDocument()
    })
  })

  it('should disable overloaded members', async () => {
    render(<TaskAssigner taskId="task-1" />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/Bob Wilson/)).toBeInTheDocument()
      expect(screen.getByText(/overloaded/)).toBeInTheDocument()
    })
  })

  it('should show workload for each member', async () => {
    render(<TaskAssigner taskId="task-1" />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('2/5 tasks')).toBeInTheDocument()
      expect(screen.getByText('1/5 tasks')).toBeInTheDocument()
      expect(screen.getByText('3/3 tasks (overloaded)')).toBeInTheDocument()
    })
  })

  it('should allow selecting a member', async () => {
    render(<TaskAssigner taskId="task-1" />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const selectButtons = screen.getAllByText('Select')
    fireEvent.click(selectButtons[0])

    expect(selectButtons[0]).toHaveClass('bg-blue-600')
  })

  it('should call onAssigned when task is assigned', async () => {
    const onAssigned = vi.fn()
    render(<TaskAssigner taskId="task-1" onAssigned={onAssigned} />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const selectButtons = screen.getAllByText('Select')
    fireEvent.click(selectButtons[0])

    const assignButton = screen.getByText('Assign')
    fireEvent.click(assignButton)

    await waitFor(() => {
      expect(onAssigned).toHaveBeenCalledWith('member-1')
    })
  })

  it('should show match score for members with required skills', async () => {
    render(<TaskAssigner taskId="task-1" requiredSkills={['react', 'typescript']} />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      const matchScores = screen.getAllByText(/% match/)
      expect(matchScores.length).toBeGreaterThan(0)
    })
  })

  it('should close dropdown when cancel is clicked', async () => {
    render(<TaskAssigner taskId="task-1" />)

    const button = screen.getByText('Assign Task')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByText('John Doe')).not.toBeInTheDocument()
    })
  })
})
