import { describe, it, expect, beforeEach } from 'vitest'
import { useDashboardStore } from '@/store/dashboardStore'

describe('dashboardStore', () => {
  beforeEach(() => {
    // Reset store to default state
    useDashboardStore.getState().resetFilters()
  })

  it('should initialize with default state', () => {
    const state = useDashboardStore.getState()

    expect(state.selectedMetrics).toEqual(['traffic', 'keywords'])
    expect(state.selectedProjectId).toBeNull()
    expect(state.autoRefresh).toBe(true)
    expect(state.refreshInterval).toBe(30)
  })

  it('should update selected metrics', () => {
    const { setSelectedMetrics } = useDashboardStore.getState()

    setSelectedMetrics(['traffic', 'conversions', 'revenue'])

    const state = useDashboardStore.getState()
    expect(state.selectedMetrics).toEqual(['traffic', 'conversions', 'revenue'])
  })

  it('should update date range', () => {
    const { setDateRange } = useDashboardStore.getState()

    const newRange = {
      start: new Date('2026-01-01'),
      end: new Date('2026-01-31'),
    }

    setDateRange(newRange)

    const state = useDashboardStore.getState()
    expect(state.dateRange).toEqual(newRange)
  })

  it('should update selected project ID', () => {
    const { setSelectedProjectId } = useDashboardStore.getState()

    setSelectedProjectId('project-123')

    const state = useDashboardStore.getState()
    expect(state.selectedProjectId).toBe('project-123')
  })

  it('should toggle auto refresh', () => {
    const { setAutoRefresh } = useDashboardStore.getState()

    setAutoRefresh(false)
    expect(useDashboardStore.getState().autoRefresh).toBe(false)

    setAutoRefresh(true)
    expect(useDashboardStore.getState().autoRefresh).toBe(true)
  })

  it('should update refresh interval', () => {
    const { setRefreshInterval } = useDashboardStore.getState()

    setRefreshInterval(60)

    const state = useDashboardStore.getState()
    expect(state.refreshInterval).toBe(60)
  })

  it('should reset filters to default', () => {
    const { setSelectedMetrics, setAutoRefresh, setRefreshInterval, resetFilters } =
      useDashboardStore.getState()

    // Change state
    setSelectedMetrics(['revenue'])
    setAutoRefresh(false)
    setRefreshInterval(120)

    // Reset
    resetFilters()

    const state = useDashboardStore.getState()
    expect(state.selectedMetrics).toEqual(['traffic', 'keywords'])
    expect(state.autoRefresh).toBe(true)
    expect(state.refreshInterval).toBe(30)
  })

  it('should persist state to localStorage', () => {
    const { setSelectedMetrics, setAutoRefresh } = useDashboardStore.getState()

    setSelectedMetrics(['backlinks', 'conversions'])
    setAutoRefresh(false)

    // Get persisted data from localStorage
    const persisted = localStorage.getItem('dashboard-storage')
    expect(persisted).toBeTruthy()

    if (persisted) {
      const parsed = JSON.parse(persisted)
      expect(parsed.state.selectedMetrics).toEqual(['backlinks', 'conversions'])
      expect(parsed.state.autoRefresh).toBe(false)
    }
  })

  it('should not persist selectedProjectId', () => {
    const { setSelectedProjectId } = useDashboardStore.getState()

    setSelectedProjectId('project-456')

    const persisted = localStorage.getItem('dashboard-storage')
    if (persisted) {
      const parsed = JSON.parse(persisted)
      expect(parsed.state.selectedProjectId).toBeUndefined()
    }
  })
})
