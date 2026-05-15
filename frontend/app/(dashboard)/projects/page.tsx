"use client";

import { useProjects } from "@/hooks/useProjects";
import Link from "next/link";

export default function ProjectsPage() {
  const { projects, loading, error } = useProjects();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading projects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error loading projects</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
        <p className="text-gray-600">You don't have any projects yet.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
        <p className="text-gray-600 mt-1">View and manage your projects</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/projects/${project.id}`}
            className="block bg-white rounded-lg border border-gray-200 p-6 hover:border-blue-500 hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                {project.name}
              </h3>
              <span
                className={`px-2 py-1 text-xs font-medium rounded-full ${
                  project.state === "started"
                    ? "bg-green-100 text-green-800"
                    : project.state === "planned"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {project.state}
              </span>
            </div>

            {project.description && (
              <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                {project.description}
              </p>
            )}

            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600">Progress</span>
                  <span className="font-medium text-gray-900">
                    {Math.round(project.progress * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${project.progress * 100}%` }}
                  />
                </div>
              </div>

              {project.lead && (
                <div className="flex items-center text-sm">
                  <svg
                    className="h-4 w-4 text-gray-400 mr-2"
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
                  <span className="text-gray-600">{project.lead.name}</span>
                </div>
              )}

              {project.targetDate && (
                <div className="flex items-center text-sm">
                  <svg
                    className="h-4 w-4 text-gray-400 mr-2"
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
                  <span className="text-gray-600">
                    Due {new Date(project.targetDate).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
