import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import type { TeamMember, TaskAssignment } from '@/types/collaboration'

interface TaskAssignerProps {
  taskId: string
  requiredSkills?: string[]
  onAssigned?: (assigneeId: string) => void
}

export function TaskAssigner({ taskId, requiredSkills = [], onAssigned }: TaskAssignerProps) {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [selectedMember, setSelectedMember] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  // Fetch team members
  useEffect(() => {
    const fetchTeamMembers = async () => {
      const { data, error } = await supabase
        .from('team_members')
        .select('*')
        .eq('availability', 'available')
        .order('current_tasks', { ascending: true })

      if (data && !error) {
        setTeamMembers(data)
      }
    }

    fetchTeamMembers()
  }, [])

  // Calculate match score for skill-based routing
  const calculateMatchScore = (member: TeamMember): number => {
    if (requiredSkills.length === 0) return 1

    const matchedSkills = member.skills.filter(skill =>
      requiredSkills.some(req => req.toLowerCase() === skill.toLowerCase())
    )

    const skillScore = matchedSkills.length / requiredSkills.length
    const workloadScore = 1 - (member.current_tasks / member.max_tasks)

    // Weighted: 70% skills, 30% workload
    return skillScore * 0.7 + workloadScore * 0.3
  }

  // Get recommended assignee
  const getRecommendedAssignee = (): TeamMember | null => {
    if (teamMembers.length === 0) return null

    const scored = teamMembers
      .filter(m => m.current_tasks < m.max_tasks)
      .map(member => ({
        member,
        score: calculateMatchScore(member),
      }))
      .sort((a, b) => b.score - a.score)

    return scored[0]?.member || null
  }

  const handleAssign = async () => {
    if (!selectedMember) return

    setIsLoading(true)

    try {
      // Create assignment
      const { data: assignment, error: assignError } = await supabase
        .from('task_assignments')
        .insert({
          task_id: taskId,
          assignee_id: selectedMember,
          assigned_by: 'current_user', // TODO: Get from auth context
          status: 'pending',
        })
        .select()
        .single()

      if (assignError) throw assignError

      // Update team member workload
      const member = teamMembers.find(m => m.id === selectedMember)
      if (member) {
        await supabase
          .from('team_members')
          .update({ current_tasks: member.current_tasks + 1 })
          .eq('id', selectedMember)
      }

      // Create notification
      await supabase.from('notifications').insert({
        user_id: selectedMember,
        type: 'task_assigned',
        title: 'New Task Assigned',
        message: `You have been assigned a new task`,
        link: `/tasks/${taskId}`,
        read: false,
      })

      // Create activity
      await supabase.from('activities').insert({
        user_id: 'current_user', // TODO: Get from auth context
        user_name: 'Current User',
        type: 'task_assigned',
        entity_type: 'task',
        entity_id: taskId,
        description: `Assigned task to ${member?.name}`,
      })

      onAssigned?.(selectedMember)
      setIsOpen(false)
    } catch (error) {
      console.error('Failed to assign task:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const recommended = getRecommendedAssignee()

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      >
        Assign Task
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Assign Task
            </h3>
            {requiredSkills.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                <span className="text-xs text-gray-600 dark:text-gray-400">Required skills:</span>
                {requiredSkills.map(skill => (
                  <span
                    key={skill}
                    className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Recommended */}
          {recommended && (
            <div className="p-4 bg-green-50 dark:bg-green-900/20 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  ⭐ Recommended
                </span>
                <span className="text-xs text-green-600 dark:text-green-400">
                  {Math.round(calculateMatchScore(recommended) * 100)}% match
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 font-semibold">
                  {recommended.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {recommended.name}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {recommended.current_tasks}/{recommended.max_tasks} tasks
                  </p>
                </div>
                <button
                  onClick={() => setSelectedMember(recommended.id)}
                  className={`px-3 py-1 text-sm rounded-md ${
                    selectedMember === recommended.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Select
                </button>
              </div>
            </div>
          )}

          {/* Team Members List */}
          <div className="max-h-64 overflow-y-auto">
            {teamMembers
              .filter(m => m.id !== recommended?.id)
              .map(member => {
                const matchScore = calculateMatchScore(member)
                const isOverloaded = member.current_tasks >= member.max_tasks

                return (
                  <div
                    key={member.id}
                    className={`p-4 border-b border-gray-200 dark:border-gray-700 ${
                      isOverloaded ? 'opacity-50' : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 font-semibold">
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {member.name}
                          </p>
                          {requiredSkills.length > 0 && (
                            <span className="text-xs text-gray-500">
                              {Math.round(matchScore * 100)}% match
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {member.current_tasks}/{member.max_tasks} tasks
                          {isOverloaded && ' (overloaded)'}
                        </p>
                      </div>
                      <button
                        onClick={() => setSelectedMember(member.id)}
                        disabled={isOverloaded}
                        className={`px-3 py-1 text-sm rounded-md ${
                          selectedMember === member.id
                            ? 'bg-blue-600 text-white'
                            : isOverloaded
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                        }`}
                      >
                        Select
                      </button>
                    </div>
                  </div>
                )
              })}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex gap-2">
            <button
              onClick={() => setIsOpen(false)}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              onClick={handleAssign}
              disabled={!selectedMember || isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Assigning...' : 'Assign'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
