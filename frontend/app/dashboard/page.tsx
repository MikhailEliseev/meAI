import { MetricsDashboard } from '@/components/dashboard/MetricsDashboard'
import { QueryProvider } from '@/components/QueryProvider'

export default function DashboardPage() {
  return (
    <QueryProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <MetricsDashboard projectId="demo-project" />
        </div>
      </div>
    </QueryProvider>
  )
}
