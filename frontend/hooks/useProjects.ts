import { useState, useEffect, useCallback } from "react";
import type { LinearProject, ProjectsResponse } from "@/types/linear";
import { useWebSocket, WebSocketMessage } from "./useWebSocket";

interface UseProjectsResult {
  projects: LinearProject[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useProjects(teamId?: string): UseProjectsResult {
  const [projects, setProjects] = useState<LinearProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);

      const url = teamId
        ? `/api/linear/projects?teamId=${teamId}`
        : "/api/linear/projects";

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.statusText}`);
      }

      const data: ProjectsResponse = await response.json();
      setProjects(data.projects);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      console.error("Error fetching projects:", err);
    } finally {
      setLoading(false);
    }
  };

  // Handle WebSocket messages for real-time updates
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'project.update') {
      setProjects((prev) => {
        const index = prev.findIndex((p) => p.id === message.data.id);
        if (index !== -1) {
          const updated = [...prev];
          updated[index] = { ...updated[index], ...message.data };
          return updated;
        }
        return prev;
      });
    }
  }, []);

  useWebSocket({
    onMessage: handleWebSocketMessage,
  });

  useEffect(() => {
    fetchProjects();
  }, [teamId]);

  return {
    projects,
    loading,
    error,
    refetch: fetchProjects,
  };
}
