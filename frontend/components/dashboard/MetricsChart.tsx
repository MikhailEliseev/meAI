import React, { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { Metric } from '@/hooks/useMetrics'

interface MetricsChartProps {
  metrics: Metric[]
  metricType: string
  height?: number
}

export function MetricsChart({ metrics, metricType, height = 300 }: MetricsChartProps) {
  const chartData = useMemo(() => {
    // Filter metrics by type and transform for Recharts
    const filtered = metrics.filter((m) => m.metric_type === metricType)

    return filtered.map((m) => ({
      date: new Date(m.recorded_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      value: m.value,
      timestamp: new Date(m.recorded_at).getTime(),
    }))
  }, [metrics, metricType])

  const getMetricLabel = (type: string) => {
    const labels: Record<string, string> = {
      traffic: 'Traffic',
      keywords: 'Keywords',
      backlinks: 'Backlinks',
      conversions: 'Conversions',
      revenue: 'Revenue ($)',
    }
    return labels[type] || type
  }

  const getMetricColor = (type: string) => {
    const colors: Record<string, string> = {
      traffic: '#8884d8',
      keywords: '#82ca9d',
      backlinks: '#ffc658',
      conversions: '#ff7c7c',
      revenue: '#8dd1e1',
    }
    return colors[type] || '#8884d8'
  }

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800"
        style={{ height }}
      >
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No data available for {getMetricLabel(metricType)}
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        {getMetricLabel(metricType)}
      </h3>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#fff',
            }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <Legend
            wrapperStyle={{ fontSize: '14px' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={getMetricColor(metricType)}
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name={getMetricLabel(metricType)}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
