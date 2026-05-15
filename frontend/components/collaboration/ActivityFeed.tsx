import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { useRealtime } from '@/hooks/useRealtime'
import type { Activity } from '@/types/collaboration'

interface ActivityFeedProps {
  projectId?: string
  userId?: string
  limit?: number
}

export function ActivityFeed({ projectId, userId, limit = 50 }: ActivityFeedProps) {
  const [activities, setActivities] = useState<Activity[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'tasks' | 'comments'>('all')

  // Fetch initial activities
  useEffect(() => {
    const fetchActivities = async () => {
      setIsLoading(true)
      let query = supabase
        .from('activities')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit)

      if (projectId) {
        query = query.eq('project_id', projectId)
      }

      if (userId) {
        query = query.eq('user_id', userId)
      }

      const { data, error } = await query

      if (data && !error) {
        setActivities(data)
      }
      setIsLoading(false)
    }

    fetchActivities()
  }, [projectId, userId, limit])

  // Real-time updates
  useRealtime({
    table: 'activities',
    filter: projectId ? `project_id=eq.${projectId}` : undefined,
    onInsert: (payload) => {
      setActivities(prev => [payload as Activity, ...prev.slice(0, limit - 1)])
    },
  })

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'task_created':
        return '➕'
      case 'task_updated':
        return '✏️'
      case 'task_completed':
        return '✅'
      case 'comment_added':
        return '💬'
      case 'task_assigned':
        return '👤'
      default:
        return '📝'
    }
  }

  const getActivityColor = (type: Activity['type']) => {
    switch (type) {
      case 'task_created':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'task_updated':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'task_completed':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      case 'comment_added':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'task_assigned':
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString()
  }

  const filteredActivities = activities.filter(activity => {
    if (filter === 'all') return true
    if (filter === 'tasks') {
      return ['task_created', 'task_updated', 'task_completed', 'task_assigned'].includes(activity.type)
    }
    if (filter === 'comments') {
      return activity.type === 'comment_added'
    }
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Activity Feed
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-sm rounded-md ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('tasks')}
              className={`px-3 py-1 text-sm rounded-md ${
                filter === 'tasks'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              Tasks
            </button>
            <button
              onClick={() => setFilter('comments')}
              className={`px-3 py-1 text-sm rounded-md ${
                filter === 'comments'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              Comments
            </button>
          </div>
        </div>
      </div>

      {/* Activity List */}
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {filteredActivities.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            No activity yet
          </div>
        ) : (
          filteredActivities.map(activity => (
            <div key={activity.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700">
              <div className="flex items-start gap-3">
                {/* Avatar */}
                <div className="flex-shrink-0">
                  {activity.user_avatar ? (
                    <img
                      src={activity.user_avatar}
                      alt={activity.user_name}
                      className="w-10 h-10 rounded-full"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 font-semibold">
                      {activity.user_name.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {activity.user_name}
                    </span>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${getActivityColor(activity.type)}`}>
                      {getActivityIcon(activity.type)} {activity.type.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {activity.description}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {formatTime(activity.created_at)}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Load More */}
      {filteredActivities.length >= limit && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-center">
          <button className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400">
            Load more
          </button>
        </div>
      )}
    </div>
  )
}
