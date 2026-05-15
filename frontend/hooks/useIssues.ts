import { useState, useEffect, useCallback } from "react";
import type { LinearIssue, IssuesResponse } from "@/types/linear";
import { useWebSocket, WebSocketMessage } from "./useWebSocket";

interface UseIssuesResult {
  issues: LinearIssue[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useIssues(projectId?: string): UseIssuesResult {
  const [issues, setIssues] = useState<LinearIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIssues = async () => {
    if (!projectId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/linear/issues?projectId=${projectId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch issues: ${response.statusText}`);
      }

      const data: IssuesResponse = await response.json();
      setIssues(data.issues);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      console.error("Error fetching issues:", err);
    } finally {
      setLoading(false);
    }
  };

  // Handle WebSocket messages for real-time updates
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'task.update') {
      setIssues((prev) => {
        const index = prev.findIndex((issue) => issue.id === message.data.id);
        if (index !== -1) {
          const updated = [...prev];
          updated[index] = { ...updated[index], ...message.data };
          return updated;
        }
        return prev;
      });
    } else if (message.type === 'task.create') {
      // Add new task if it belongs to current project
      if (message.data.project?.id === projectId) {
        setIssues((prev) => [message.data, ...prev]);
      }
    }
  }, [projectId]);

  useWebSocket({
    onMessage: handleWebSocketMessage,
  });

  useEffect(() => {
    fetchIssues();
  }, [projectId]);

  return {
    issues,
    loading,
    error,
    refetch: fetchIssues,
  };
}
