import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MetricsDashboard } from '@/components/dashboard/MetricsDashboard'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock hooks
vi.mock('@/hooks/useMetrics', () => ({
  useMetrics: vi.fn(),
}))

vi.mock('@/store/dashboardStore', () => ({
  useDashboardStore: vi.fn(),
}))

import { useMetrics } from '@/hooks/useMetrics'
import { useDashboardStore } from '@/store/dashboardStore'

const mockUseMetrics = vi.mocked(useMetrics)
const mockUseDashboardStore = vi.mocked(useDashboardStore)

describe('MetricsDashboard', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })

    // Mock dashboardStore
    mockUseDashboardStore.mockReturnValue({
      selectedMetrics: ['traffic', 'keywords'],
      dateRange: { start: new Date(), end: new Date() },
      selectedProjectId: null,
      autoRefresh: true,
      refreshInterval: 30,
      setSelectedMetrics: vi.fn(),
      setDateRange: vi.fn(),
      setSelectedProjectId: vi.fn(),
      setAutoRefresh: vi.fn(),
      setRefreshInterval: vi.fn(),
      resetFilters: vi.fn(),
    })
  })

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  it('should show loading state', () => {
    mockUseMetrics.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      realtimeStatus: 'connecting',
      refetch: vi.fn(),
    } as any)

    renderWithProviders(<MetricsDashboard projectId="project-1" />)

    expect(screen.getByText('Loading metrics...')).toBeInTheDocument()
  })

  it('should show error state', () => {
    const error = new Error('Failed to fetch metrics')
    mockUseMetrics.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error,
      realtimeStatus: 'error',
      refetch: vi.fn(),
    } as any)

    renderWithProviders(<MetricsDashboard projectId="project-1" />)

    expect(screen.getByText('Error Loading Metrics')).toBeInTheDocument()
    expect(screen.getByText('Failed to fetch metrics')).toBeInTheDocument()
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('should render metrics dashboard with data', async () => {
    const mockMetrics = [
      {
        id: '1',
        project_id: 'project-1',
        metric_type: 'traffic',
        value: 1000,
        recorded_at: '2026-05-15T10:00:00Z',
      },
      {
        id: '2',
        project_id: 'project-1',
        metric_type: 'keywords',
        value: 50,
        recorded_at: '2026-05-15T10:00:00Z',
      },
    ]

    mockUseMetrics.mockReturnValue({
      data: mockMetrics,
      isLoading: false,
      isError: false,
      error: null,
      realtimeStatus: 'connected',
      refetch: vi.fn(),
    } as any)

    renderWithProviders(<MetricsDashboard projectId="project-1" />)

    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
      expect(screen.getByText('Real-time dashboard with live updates')).toBeInTheDocument()
    })

    // Check stats cards
    expect(screen.getAllByText('Traffic').length).toBeGreaterThan(0)
    expect(screen.getByText('1,000')).toBeInTheDocument()
    expect(screen.getAllByText('Keywords').length).toBeGreaterThan(0)
    expect(screen.getByText('50')).toBeInTheDocument()
  })

  it('should show connection status', () => {
    mockUseMetrics.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      realtimeStatus: 'connected',
      refetch: vi.fn(),
    } as any)

    renderWithProviders(<MetricsDashboard projectId="project-1" />)

    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('should show live updates indicator when connected', () => {
    mockUseMetrics.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      realtimeStatus: 'connected',
      refetch: vi.fn(),
    } as any)

    renderWithProviders(<MetricsDashboard projectId="project-1" />)

    expect(screen.getByText(/Live updates enabled/)).toBeInTheDocument()
  })

  it('should display data count', () => {
    const mockMetrics = Array.from({ length: 10 }, (_, i) => ({
      id: `${i}`,
      project_id: 'project-1',
      metric_type: 'traffic',
      value: 100 * i,
      recorded_at: '2026-05-15T10:00:00Z',
    }))

    mockUseMetrics.mockReturnValue({
      data: mockMetrics,
      isLoading: false,
      isError: false,
      error: null,
      realtimeStatus: 'connected',
      refetch: vi.fn(),
    } as any)

    renderWithProviders(<MetricsDashboard projectId="project-1" />)

    expect(screen.getByText('Showing 10 data points')).toBeInTheDocument()
  })

  it('should calculate percentage change correctly', () => {
    const mockMetrics = [
      {
        id: '1',
        project_id: 'project-1',
        metric_type: 'traffic',
        value: 1000,
        recorded_at: '2026-05-14T10:00:00Z',
      },
      {
        id: '2',
        project_id: 'project-1',
        metric_type: 'traffic',
        value: 1200,
        recorded_at: '2026-05-15T10:00:00Z',
      },
    ]

    mockUseMetrics.mockReturnValue({
      data: mockMetrics,
      isLoading: false,
      isError: false,
      error: null,
      realtimeStatus: 'connected',
      refetch: vi.fn(),
    } as any)

    renderWithProviders(<MetricsDashboard projectId="project-1" />)

    // 20% increase: (1200 - 1000) / 1000 * 100 = 20%
    expect(screen.getByText(/↑ 20.0%/)).toBeInTheDocument()
  })
})
