// Linear API types

export interface LinearUser {
  id: string;
  name: string;
  email?: string;
}

export interface LinearLabel {
  id: string;
  name: string;
  color: string;
}

export interface LinearState {
  id: string;
  name: string;
  type: string;
}

export interface LinearIssue {
  id: string;
  title: string;
  description?: string;
  priority: number;
  estimate?: number;
  state: LinearState;
  assignee?: LinearUser;
  createdAt: string;
  updatedAt: string;
  dueDate?: string;
  labels: {
    nodes: LinearLabel[];
  };
}

export interface LinearProject {
  id: string;
  name: string;
  description?: string;
  state: string;
  progress: number;
  startedAt?: string;
  targetDate?: string;
  lead?: LinearUser;
  members: {
    nodes: LinearUser[];
  };
}

export interface LinearTeam {
  id: string;
  name: string;
  projects: {
    nodes: LinearProject[];
  };
}

// API Response types

export interface ProjectsResponse {
  team: LinearTeam;
  projects: LinearProject[];
}

export interface IssuesResponse {
  project: {
    id: string;
    name: string;
    issues: {
      nodes: LinearIssue[];
    };
  };
  issues: LinearIssue[];
}
