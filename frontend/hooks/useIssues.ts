import { useState, useEffect } from "react";
import type { LinearIssue, IssuesResponse } from "@/types/linear";

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
