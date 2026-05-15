'use client'

import { NotificationCenter } from '@/components/collaboration/NotificationCenter'
import { ActivityFeed } from '@/components/collaboration/ActivityFeed'
import { TaskAssigner } from '@/components/collaboration/TaskAssigner'

export default function CollaborationPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Team Collaboration
            </h1>
            <NotificationCenter userId="current-user" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Activity Feed - 2 columns */}
          <div className="lg:col-span-2">
            <ActivityFeed limit={20} />
          </div>

          {/* Task Assignment - 1 column */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h2>
              <div className="space-y-4">
                <TaskAssigner
                  taskId="example-task-1"
                  requiredSkills={['react', 'typescript']}
                  onAssigned={(assigneeId) => {
                    console.log('Task assigned to:', assigneeId)
                  }}
                />
              </div>
            </div>

            {/* Team Stats */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Team Stats
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Active Members
                  </span>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">
                    12
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Tasks in Progress
                  </span>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">
                    24
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Completed Today
                  </span>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">
                    8
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
