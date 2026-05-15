export interface TeamMember {
  id: string
  name: string
  email: string
  avatar_url?: string
  role: 'admin' | 'member' | 'viewer'
  skills: string[]
  max_tasks: number
  current_tasks: number
  availability: 'available' | 'busy' | 'offline'
  created_at: string
  updated_at: string
}

export interface TaskAssignment {
  id: string
  task_id: string
  assignee_id: string
  assigned_by: string
  assigned_at: string
  status: 'pending' | 'accepted' | 'declined'
  notes?: string
}

export interface Notification {
  id: string
  user_id: string
  type: 'task_assigned' | 'task_completed' | 'comment_added' | 'mention' | 'deadline_approaching'
  title: string
  message: string
  link?: string
  read: boolean
  created_at: string
}

export interface Activity {
  id: string
  user_id: string
  user_name: string
  user_avatar?: string
  type: 'task_created' | 'task_updated' | 'task_completed' | 'comment_added' | 'task_assigned'
  entity_type: 'task' | 'project' | 'comment'
  entity_id: string
  description: string
  metadata?: Record<string, any>
  created_at: string
}

export interface NotificationPreferences {
  user_id: string
  email_enabled: boolean
  in_app_enabled: boolean
  task_assigned: boolean
  task_completed: boolean
  comments: boolean
  mentions: boolean
  deadlines: boolean
}
