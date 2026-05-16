import { LinearClient, type CreateLeadIssueInput } from "@/lib/linear-client";
import { type LeadScore } from "@/lib/lead-scoring";

// Mock fetch globally
global.fetch = jest.fn();

describe("LinearClient", () => {
  let client: LinearClient;
  const mockApiKey = "lin_api_test_key";
  const mockTeamId = "team_123";
  const mockProjectId = "project_456";
  const mockStateId = "state_789";

  beforeEach(() => {
    client = new LinearClient({
      apiKey: mockApiKey,
      teamId: mockTeamId,
      projectId: mockProjectId,
      salesPipelineStateId: mockStateId,
    });

    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset();
  });

  describe("createLeadIssue", () => {
    const mockLeadScore: LeadScore = {
      score: 85,
      tier: "hot",
      confidence: 0.95,
      factors: [
        { category: "Specialty", score: 90, weight: 0.15, contribution: 13.5 },
        { category: "Location", score: 100, weight: 0.1, contribution: 10 },
      ],
      recommendations: [
        "🔥 Приоритет 1: Позвонить в течение 15 минут",
        "📧 Отправить персональное предложение с кейсами",
      ],
    };

    const mockInput: CreateLeadIssueInput = {
      name: "Иван Петров",
      phone: "+79991234567",
      email: "ivan@dentaplus.ru",
      clinicName: "Стоматология Дента Плюс",
      specialty: "Стоматология",
      message: "Ищем агентство для продвижения",
      score: mockLeadScore,
      source: "google",
      deviceType: "desktop",
    };

    const mockLinearResponse = {
      data: {
        issueCreate: {
          success: true,
          issue: {
            id: "issue_123",
            identifier: "AIM-42",
            title: "[Lead] Стоматология Дента Плюс - Стоматология",
            url: "https://linear.app/aim/issue/AIM-42",
            priority: 1,
            state: {
              id: "state_789",
              name: "New Lead",
            },
            team: {
              id: "team_123",
              name: "Sales",
            },
            assignee: null,
            labels: {
              nodes: [
                { id: "label_1", name: "lead_hot" },
                { id: "label_2", name: "score_80" },
              ],
            },
            createdAt: "2026-05-16T11:20:00.000Z",
          },
        },
      },
    };

    it("should create Linear issue for hot lead", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      const issue = await client.createLeadIssue(mockInput);

      expect(issue.identifier).toBe("AIM-42");
      expect(issue.title).toBe("[Lead] Стоматология Дента Плюс - Стоматология");
      expect(issue.priority).toBe(1); // Urgent for hot lead
      expect(issue.url).toBe("https://linear.app/aim/issue/AIM-42");
      expect(issue.labels).toHaveLength(2);
    });

    it("should map hot tier to priority 1 (Urgent)", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);

      expect(body.variables.input.priority).toBe(1);
    });

    it("should map warm tier to priority 2 (High)", async () => {
      const warmInput = {
        ...mockInput,
        score: { ...mockLeadScore, tier: "warm" as const, score: 65 },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockLinearResponse,
          data: {
            ...mockLinearResponse.data,
            issueCreate: {
              ...mockLinearResponse.data.issueCreate,
              issue: {
                ...mockLinearResponse.data.issueCreate.issue,
                priority: 2,
              },
            },
          },
        }),
      });

      await client.createLeadIssue(warmInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);

      expect(body.variables.input.priority).toBe(2);
    });

    it("should map cold tier to priority 3 (Medium)", async () => {
      const coldInput = {
        ...mockInput,
        score: { ...mockLeadScore, tier: "cold" as const, score: 35 },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockLinearResponse,
          data: {
            ...mockLinearResponse.data,
            issueCreate: {
              ...mockLinearResponse.data.issueCreate,
              issue: {
                ...mockLinearResponse.data.issueCreate.issue,
                priority: 3,
              },
            },
          },
        }),
      });

      await client.createLeadIssue(coldInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);

      expect(body.variables.input.priority).toBe(3);
    });

    it("should include lead score in description", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      const description = body.variables.input.description;

      expect(description).toContain("Lead Score: 85/100 (HOT)");
      expect(description).toContain("**Confidence:** 95%");
    });

    it("should include contact information in description", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      const description = body.variables.input.description;

      expect(description).toContain("Иван Петров");
      expect(description).toContain("ivan@dentaplus.ru");
      expect(description).toContain("+79991234567");
      expect(description).toContain("Стоматология Дента Плюс");
      expect(description).toContain("Стоматология");
    });

    it("should include message in description if provided", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      const description = body.variables.input.description;

      expect(description).toContain("💬 Message");
      expect(description).toContain("Ищем агентство для продвижения");
    });

    it("should include recommendations in description", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      const description = body.variables.input.description;

      expect(description).toContain("🔥 Приоритет 1: Позвонить в течение 15 минут");
      expect(description).toContain("📧 Отправить персональное предложение с кейсами");
    });

    it("should include top contributing factors in description", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      const description = body.variables.input.description;

      expect(description).toContain("Specialty");
      expect(description).toContain("Location");
    });

    it("should include metadata in description if provided", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      const description = body.variables.input.description;

      expect(description).toContain("**Source:** google");
      expect(description).toContain("**Device:** desktop");
    });

    it("should send correct GraphQL mutation", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLinearResponse,
      });

      await client.createLeadIssue(mockInput);

      expect(global.fetch).toHaveBeenCalledWith(
        "https://api.linear.app/graphql",
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: mockApiKey,
          },
        })
      );

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);

      expect(body.query).toContain("mutation CreateIssue");
      expect(body.variables.input.teamId).toBe(mockTeamId);
      expect(body.variables.input.projectId).toBe(mockProjectId);
      expect(body.variables.input.stateId).toBe(mockStateId);
    });

    it("should throw error if Linear API returns error", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          errors: [{ message: "Invalid API key" }],
        }),
      });

      await expect(client.createLeadIssue(mockInput)).rejects.toThrow("Linear GraphQL error");
    });

    it("should throw error if HTTP request fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      });

      await expect(client.createLeadIssue(mockInput)).rejects.toThrow("Linear API error: 401");
    });

    it("should throw error if issue creation fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            issueCreate: {
              success: false,
            },
          },
        }),
      });

      await expect(client.createLeadIssue(mockInput)).rejects.toThrow("Failed to create Linear issue");
    });
  });

  describe("testConnection", () => {
    it("should return true for successful connection", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            viewer: {
              id: "user_123",
              name: "Test User",
              email: "test@example.com",
            },
          },
        }),
      });

      const result = await client.testConnection();

      expect(result).toBe(true);
    });

    it("should return false for failed connection", async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network error"));

      const result = await client.testConnection();

      expect(result).toBe(false);
    });
  });
});
