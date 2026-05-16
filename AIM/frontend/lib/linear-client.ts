/**
 * Linear API Client
 *
 * Wrapper for Linear GraphQL API to create issues for leads
 * Integrates with Phase 7.5 Linear CRM
 */

import { type LeadScore } from "./lead-scoring";

export interface LinearIssue {
  id: string;
  identifier: string; // e.g., "AIM-123"
  title: string;
  url: string;
  priority: number; // 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
  state: {
    id: string;
    name: string;
  };
  team: {
    id: string;
    name: string;
  };
  assignee?: {
    id: string;
    name: string;
  };
  labels: {
    id: string;
    name: string;
  }[];
  createdAt: string;
}

export interface CreateLeadIssueInput {
  // Lead data
  name: string;
  phone: string;
  email: string;
  clinicName: string;
  specialty: string;
  message?: string;

  // Lead score
  score: LeadScore;

  // Optional metadata
  source?: string; // UTM source
  referrer?: string;
  deviceType?: string;
}

export interface LinearConfig {
  apiKey: string;
  teamId: string;
  projectId?: string;
  salesPipelineStateId?: string; // "New Lead" state
}

/**
 * Linear API Client
 */
export class LinearClient {
  private apiKey: string;
  private teamId: string;
  private projectId?: string;
  private salesPipelineStateId?: string;
  private apiUrl = "https://api.linear.app/graphql";

  constructor(config: LinearConfig) {
    this.apiKey = config.apiKey;
    this.teamId = config.teamId;
    this.projectId = config.projectId;
    this.salesPipelineStateId = config.salesPipelineStateId;
  }

  /**
   * Create Linear issue for a new lead
   */
  async createLeadIssue(input: CreateLeadIssueInput): Promise<LinearIssue> {
    const { name, phone, email, clinicName, specialty, message, score, source, referrer, deviceType } = input;

    // Map tier to priority
    const priority = this.tierToPriority(score.tier);

    // Build issue title
    const title = `[Lead] ${clinicName} - ${specialty}`;

    // Build issue description
    const description = this.buildDescription(input);

    // Get label IDs (create if needed)
    const labelIds = await this.getOrCreateLabels(score);

    // Get assignee ID based on specialty
    const assigneeId = await this.getAssigneeBySpecialty(specialty);

    // Create issue via GraphQL
    const mutation = `
      mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
          success
          issue {
            id
            identifier
            title
            url
            priority
            state {
              id
              name
            }
            team {
              id
              name
            }
            assignee {
              id
              name
            }
            labels {
              nodes {
                id
                name
              }
            }
            createdAt
          }
        }
      }
    `;

    const variables = {
      input: {
        teamId: this.teamId,
        projectId: this.projectId,
        stateId: this.salesPipelineStateId,
        title,
        description,
        priority,
        assigneeId,
        labelIds,
      },
    };

    const response = await this.graphql(mutation, variables);

    if (!response.issueCreate.success) {
      throw new Error("Failed to create Linear issue");
    }

    const issue = response.issueCreate.issue;

    return {
      id: issue.id,
      identifier: issue.identifier,
      title: issue.title,
      url: issue.url,
      priority: issue.priority,
      state: issue.state,
      team: issue.team,
      assignee: issue.assignee,
      labels: issue.labels.nodes,
      createdAt: issue.createdAt,
    };
  }

  /**
   * Build issue description from lead data
   */
  private buildDescription(input: CreateLeadIssueInput): string {
    const { name, phone, email, clinicName, specialty, message, score, source, referrer, deviceType } = input;

    let description = `## 📊 Lead Score: ${score.score}/100 (${score.tier.toUpperCase()})\n\n`;
    description += `**Confidence:** ${(score.confidence * 100).toFixed(0)}%\n\n`;

    description += `## 👤 Contact Information\n\n`;
    description += `- **Name:** ${name}\n`;
    description += `- **Email:** ${email}\n`;
    description += `- **Phone:** ${phone}\n`;
    description += `- **Clinic:** ${clinicName}\n`;
    description += `- **Specialty:** ${specialty}\n\n`;

    if (message) {
      description += `## 💬 Message\n\n${message}\n\n`;
    }

    description += `## 🎯 Recommendations\n\n`;
    score.recommendations.forEach((rec) => {
      description += `- ${rec}\n`;
    });
    description += `\n`;

    description += `## 📈 Top Contributing Factors\n\n`;
    score.factors.slice(0, 5).forEach((factor) => {
      description += `- **${factor.category}:** ${factor.score}/100 (weight: ${(factor.weight * 100).toFixed(0)}%)\n`;
    });
    description += `\n`;

    if (source || referrer || deviceType) {
      description += `## 🔍 Metadata\n\n`;
      if (source) description += `- **Source:** ${source}\n`;
      if (referrer) description += `- **Referrer:** ${referrer}\n`;
      if (deviceType) description += `- **Device:** ${deviceType}\n`;
      description += `\n`;
    }

    description += `---\n\n`;
    description += `*Created automatically by AIM Lead Scoring Engine*\n`;

    return description;
  }

  /**
   * Map lead tier to Linear priority
   */
  private tierToPriority(tier: "hot" | "warm" | "cold"): number {
    switch (tier) {
      case "hot":
        return 1; // Urgent
      case "warm":
        return 2; // High
      case "cold":
        return 3; // Medium
      default:
        return 0; // No priority
    }
  }

  /**
   * Get or create labels for lead
   */
  private async getOrCreateLabels(score: LeadScore): Promise<string[]> {
    const labelNames = [
      `lead_${score.tier}`, // lead_hot, lead_warm, lead_cold
      `score_${Math.floor(score.score / 10) * 10}`, // score_80, score_70, etc.
    ];

    // TODO: Implement label creation/lookup
    // For now, return empty array (labels will be created manually in Linear)
    return [];
  }

  /**
   * Get assignee ID based on specialty
   */
  private async getAssigneeBySpecialty(specialty: string): Promise<string | undefined> {
    // TODO: Implement specialty → assignee mapping
    // For now, return undefined (no auto-assignment)
    // In Phase 7.5, this will query Linear for team members with specialty tags
    return undefined;
  }

  /**
   * Execute GraphQL query/mutation
   */
  private async graphql(query: string, variables?: Record<string, any>): Promise<any> {
    const response = await fetch(this.apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: this.apiKey,
      },
      body: JSON.stringify({
        query,
        variables,
      }),
    });

    if (!response.ok) {
      throw new Error(`Linear API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    if (data.errors) {
      throw new Error(`Linear GraphQL error: ${JSON.stringify(data.errors)}`);
    }

    return data.data;
  }

  /**
   * Test connection to Linear API
   */
  async testConnection(): Promise<boolean> {
    try {
      const query = `
        query Viewer {
          viewer {
            id
            name
            email
          }
        }
      `;

      const response = await this.graphql(query);
      return !!response.viewer;
    } catch (error) {
      console.error("[Linear] Connection test failed:", error);
      return false;
    }
  }
}

/**
 * Create Linear client from environment variables
 */
export function createLinearClient(): LinearClient {
  const apiKey = process.env.LINEAR_API_KEY;
  const teamId = process.env.LINEAR_TEAM_ID;
  const projectId = process.env.LINEAR_PROJECT_ID;
  const salesPipelineStateId = process.env.LINEAR_SALES_PIPELINE_STATE_ID;

  if (!apiKey) {
    throw new Error("LINEAR_API_KEY environment variable is required");
  }

  if (!teamId) {
    throw new Error("LINEAR_TEAM_ID environment variable is required");
  }

  return new LinearClient({
    apiKey,
    teamId,
    projectId,
    salesPipelineStateId,
  });
}
