export interface Project {
  id: string
  client_id: string
  name: string
  description: string | null
  status: 'active' | 'paused' | 'completed'
  linear_project_id: string | null
  created_at: string
  updated_at: string
}

export interface Metric {
  id: string
  project_id: string
  metric_type: string
  value: number
  recorded_at: string
}

export type MetricType = 'traffic' | 'keywords' | 'backlinks' | 'conversions' | 'revenue'

export interface DashboardFilters {
  selectedMetrics: MetricType[]
  dateRange: {
    start: Date
    end: Date
  }
  selectedProjectId: string | null
  autoRefresh: boolean
  refreshInterval: number
}
