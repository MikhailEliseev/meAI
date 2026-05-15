import React from 'react'
import { useMetrics } from '@/hooks/useMetrics'
import { useDashboardStore } from '@/store/dashboardStore'
import { MetricsChart } from './MetricsChart'
import { ConnectionStatusIndicator } from './ConnectionStatus'

interface MetricsDashboardProps {
  projectId: string
}

export function MetricsDashboard({ projectId }: MetricsDashboardProps) {
  const { selectedMetrics, autoRefresh, setAutoRefresh } = useDashboardStore()
  const { data: metrics, isLoading, isError, error, realtimeStatus, refetch } = useMetrics(projectId)

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
          <p className="text-sm text-gray-600 dark:text-gray-400">Loading metrics...</p>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
        <h3 className="mb-2 text-lg font-semibold text-red-800 dark:text-red-400">
          Error Loading Metrics
        </h3>
        <p className="text-sm text-red-600 dark:text-red-300">
          {error instanceof Error ? error.message : 'An unknown error occurred'}
        </p>
        <button
          onClick={() => refetch()}
          className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Performance Metrics
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Real-time dashboard with live updates
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Auto-refresh toggle */}
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Auto-refresh
            </span>
          </label>

          {/* Connection status */}
          <ConnectionStatusIndicator
            status={realtimeStatus}
            onReconnect={() => refetch()}
          />
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {selectedMetrics.map((metricType) => {
          const metricData = metrics?.filter((m) => m.metric_type === metricType) || []
          const latestValue = metricData[metricData.length - 1]?.value || 0
          const previousValue = metricData[metricData.length - 2]?.value || 0
          const change = previousValue > 0
            ? ((latestValue - previousValue) / previousValue) * 100
            : 0

          return (
            <div
              key={metricType}
              className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
            >
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {metricType.charAt(0).toUpperCase() + metricType.slice(1)}
              </p>
              <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                {latestValue.toLocaleString()}
              </p>
              {change !== 0 && (
                <p
                  className={`mt-1 text-sm ${
                    change > 0
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {change > 0 ? '↑' : '↓'} {Math.abs(change).toFixed(1)}%
                </p>
              )}
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {selectedMetrics.map((metricType) => (
          <MetricsChart
            key={metricType}
            metrics={metrics || []}
            metricType={metricType}
            height={300}
          />
        ))}
      </div>

      {/* Data count */}
      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        Showing {metrics?.length || 0} data points
        {realtimeStatus === 'connected' && (
          <span className="ml-2 text-green-600 dark:text-green-400">
            • Live updates enabled
          </span>
        )}
      </div>
    </div>
  )
}
