import { useQuery, useQueryClient } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { useRealtime } from './useRealtime'
import { useDashboardStore } from '@/store/dashboardStore'

export interface Metric {
  id: string
  project_id: string
  metric_type: string
  value: number
  recorded_at: string
}

export function useMetrics(projectId: string | null) {
  const queryClient = useQueryClient()
  const { dateRange, selectedMetrics } = useDashboardStore()

  // Fetch metrics with TanStack Query
  const query = useQuery({
    queryKey: ['metrics', projectId, dateRange, selectedMetrics],
    queryFn: async () => {
      if (!projectId) return []

      let query = supabase
        .from('metrics')
        .select('*')
        .eq('project_id', projectId)
        .gte('recorded_at', dateRange.start.toISOString())
        .lte('recorded_at', dateRange.end.toISOString())
        .order('recorded_at', { ascending: true })

      // Filter by selected metric types
      if (selectedMetrics.length > 0) {
        query = query.in('metric_type', selectedMetrics)
      }

      const { data, error } = await query

      if (error) {
        throw new Error(`Failed to fetch metrics: ${error.message}`)
      }

      return data as Metric[]
    },
    enabled: !!projectId,
    staleTime: 30000, // 30 seconds
    refetchInterval: useDashboardStore.getState().autoRefresh
      ? useDashboardStore.getState().refreshInterval * 1000
      : false,
  })

  // Real-time updates
  const { status: realtimeStatus } = useRealtime({
    table: 'metrics',
    filter: projectId ? `project_id=eq.${projectId}` : undefined,
    onInsert: (newMetric: Metric) => {
      // Check if metric matches current filters
      const { dateRange, selectedMetrics } = useDashboardStore.getState()
      const metricDate = new Date(newMetric.recorded_at)

      const isInDateRange =
        metricDate >= dateRange.start && metricDate <= dateRange.end

      const isSelectedMetric =
        selectedMetrics.length === 0 ||
        selectedMetrics.includes(newMetric.metric_type as any)

      if (isInDateRange && isSelectedMetric) {
        queryClient.setQueryData<Metric[]>(
          ['metrics', projectId, dateRange, selectedMetrics],
          (old) => {
            if (!old) return [newMetric]
            // Add new metric and keep sorted by recorded_at
            return [...old, newMetric].sort(
              (a, b) =>
                new Date(a.recorded_at).getTime() -
                new Date(b.recorded_at).getTime()
            )
          }
        )
      }
    },
    onUpdate: (updatedMetric: Metric) => {
      queryClient.setQueryData<Metric[]>(
        ['metrics', projectId, dateRange, selectedMetrics],
        (old) => {
          if (!old) return [updatedMetric]
          return old.map((m) => (m.id === updatedMetric.id ? updatedMetric : m))
        }
      )
    },
    onDelete: (deletedMetric: Metric) => {
      queryClient.setQueryData<Metric[]>(
        ['metrics', projectId, dateRange, selectedMetrics],
        (old) => {
          if (!old) return []
          return old.filter((m) => m.id !== deletedMetric.id)
        }
      )
    },
  })

  return {
    ...query,
    realtimeStatus,
    isRealtimeConnected: realtimeStatus === 'connected',
  }
}
