"use client";

import { useState } from "react";
import { useProjects } from "@/hooks/useProjects";
import { useIssues } from "@/hooks/useIssues";
import type { LinearIssue } from "@/types/linear";

const priorityColors = {
  0: "bg-gray-100 text-gray-800",
  1: "bg-blue-100 text-blue-800",
  2: "bg-yellow-100 text-yellow-800",
  3: "bg-orange-100 text-orange-800",
  4: "bg-red-100 text-red-800",
};

const priorityLabels = {
  0: "No priority",
  1: "Low",
  2: "Medium",
  3: "High",
  4: "Urgent",
};

export default function TasksPage() {
  const { projects, loading: projectsLoading } = useProjects();
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [filterPriority, setFilterPriority] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const { issues, loading: issuesLoading } = useIssues(selectedProject || undefined);

  const filteredIssues = issues.filter((issue) => {
    if (filterPriority !== "all" && issue.priority.toString() !== filterPriority) {
      return false;
    }
    if (filterStatus !== "all" && issue.state.type !== filterStatus) {
      return false;
    }
    return true;
  });

  const groupedIssues = filteredIssues.reduce((acc, issue) => {
    const status = issue.state.name;
    if (!acc[status]) {
      acc[status] = [];
    }
    acc[status].push(issue);
    return acc;
  }, {} as Record<string, LinearIssue[]>);

  const loading = projectsLoading || issuesLoading;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
        <p className="text-gray-600 mt-1">View and filter your tasks</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Project
            </label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={projectsLoading}
            >
              <option value="">All Projects</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Priority
            </label>
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Priorities</option>
              <option value="4">Urgent</option>
              <option value="3">High</option>
              <option value="2">Medium</option>
              <option value="1">Low</option>
              <option value="0">No priority</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="backlog">Backlog</option>
              <option value="unstarted">Unstarted</option>
              <option value="started">Started</option>
              <option value="completed">Completed</option>
              <option value="canceled">Canceled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tasks */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading tasks...</p>
          </div>
        </div>
      ) : filteredIssues.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks found</h3>
          <p className="text-gray-600">
            {selectedProject
              ? "This project doesn't have any tasks matching your filters."
              : "Select a project to view tasks."}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedIssues).map(([status, statusIssues]) => (
            <div key={status}>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                {status} ({statusIssues.length})
              </h2>
              <div className="space-y-3">
                {statusIssues.map((issue) => (
                  <div
                    key={issue.id}
                    className="bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-500 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-base font-medium text-gray-900 flex-1">
                        {issue.title}
                      </h3>
                      <span
                        className={`ml-4 px-2 py-1 text-xs font-semibold rounded-full whitespace-nowrap ${
                          priorityColors[issue.priority as keyof typeof priorityColors]
                        }`}
                      >
                        {priorityLabels[issue.priority as keyof typeof priorityLabels]}
                      </span>
                    </div>

                    {issue.description && (
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {issue.description}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      {issue.assignee && (
                        <div className="flex items-center">
                          <svg
                            className="h-4 w-4 mr-1"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                          </svg>
                          {issue.assignee.name}
                        </div>
                      )}

                      {issue.dueDate && (
                        <div className="flex items-center">
                          <svg
                            className="h-4 w-4 mr-1"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                            />
                          </svg>
                          {new Date(issue.dueDate).toLocaleDateString()}
                        </div>
                      )}

                      {issue.estimate && (
                        <div className="flex items-center">
                          <svg
                            className="h-4 w-4 mr-1"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          {issue.estimate}h
                        </div>
                      )}
                    </div>

                    {issue.labels.nodes.length > 0 && (
                      <div className="flex gap-1 mt-3">
                        {issue.labels.nodes.map((label) => (
                          <span
                            key={label.id}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                            style={{
                              backgroundColor: `${label.color}20`,
                              color: label.color,
                            }}
                          >
                            {label.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
