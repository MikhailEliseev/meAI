import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type MetricType = 'traffic' | 'keywords' | 'backlinks' | 'conversions' | 'revenue'

interface DashboardState {
  selectedMetrics: MetricType[]
  dateRange: {
    start: Date
    end: Date
  }
  selectedProjectId: string | null
  autoRefresh: boolean
  refreshInterval: number // seconds

  // Actions
  setSelectedMetrics: (metrics: MetricType[]) => void
  setDateRange: (range: { start: Date; end: Date }) => void
  setSelectedProjectId: (projectId: string | null) => void
  setAutoRefresh: (enabled: boolean) => void
  setRefreshInterval: (interval: number) => void
  resetFilters: () => void
}

const defaultState = {
  selectedMetrics: ['traffic', 'keywords'] as MetricType[],
  dateRange: {
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    end: new Date(),
  },
  selectedProjectId: null,
  autoRefresh: true,
  refreshInterval: 30, // 30 seconds
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      ...defaultState,

      setSelectedMetrics: (metrics) => set({ selectedMetrics: metrics }),

      setDateRange: (range) => set({ dateRange: range }),

      setSelectedProjectId: (projectId) => set({ selectedProjectId: projectId }),

      setAutoRefresh: (enabled) => set({ autoRefresh: enabled }),

      setRefreshInterval: (interval) => set({ refreshInterval: interval }),

      resetFilters: () => set(defaultState),
    }),
    {
      name: 'dashboard-storage',
      partialize: (state) => ({
        selectedMetrics: state.selectedMetrics,
        dateRange: state.dateRange,
        autoRefresh: state.autoRefresh,
        refreshInterval: state.refreshInterval,
      }),
    }
  )
)
