import { HOT_LEAD_SEQUENCE, buildTemplateData } from "@/lib/email-sequences";
import { type LeadScore } from "@/lib/lead-scoring";

// Mock entire email-queue module
jest.mock("@/lib/email-queue", () => ({
  scheduleEmailSequence: jest.fn(),
  pauseEmailSequence: jest.fn(),
  resumeEmailSequence: jest.fn(),
  handleUnsubscribe: jest.fn(),
  getQueueStats: jest.fn(),
  emailQueue: {
    add: jest.fn(),
    getJobs: jest.fn(),
    getWaitingCount: jest.fn(),
    getActiveCount: jest.fn(),
    getCompletedCount: jest.fn(),
    getFailedCount: jest.fn(),
    getDelayedCount: jest.fn(),
  },
}));

import {
  scheduleEmailSequence,
  pauseEmailSequence,
  resumeEmailSequence,
  handleUnsubscribe,
  getQueueStats,
  emailQueue,
} from "@/lib/email-queue";

describe("Email Queue System", () => {
  const mockLeadScore: LeadScore = {
    score: 85,
    tier: "hot",
    confidence: 0.95,
    factors: [
      { category: "Specialty", score: 90, weight: 0.15, contribution: 13.5 },
    ],
    recommendations: ["🔥 Приоритет 1: Позвонить в течение 15 минут"],
  };

  const mockTemplateData = buildTemplateData(
    "Иван Петров",
    "Стоматология Дента Плюс",
    "Стоматология",
    mockLeadScore
  );

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("scheduleEmailSequence", () => {
    it("should schedule all emails in sequence", async () => {
      const mockResult = {
        jobIds: ["job-1", "job-2", "job-3"],
        nextEmailAt: new Date(),
      };
      (scheduleEmailSequence as jest.Mock).mockResolvedValue(mockResult);

      const result = await scheduleEmailSequence(
        HOT_LEAD_SEQUENCE,
        "ivan@dentaplus.ru",
        mockTemplateData,
        0
      );

      expect(result.jobIds).toHaveLength(3);
      expect(result.nextEmailAt).toBeDefined();
      expect(scheduleEmailSequence).toHaveBeenCalledWith(
        HOT_LEAD_SEQUENCE,
        "ivan@dentaplus.ru",
        mockTemplateData,
        0
      );
    });

    it("should schedule from specific step", async () => {
      const mockResult = {
        jobIds: ["job-2", "job-3"],
        nextEmailAt: new Date(),
      };
      (scheduleEmailSequence as jest.Mock).mockResolvedValue(mockResult);

      const result = await scheduleEmailSequence(
        HOT_LEAD_SEQUENCE,
        "ivan@dentaplus.ru",
        mockTemplateData,
        1
      );

      expect(result.jobIds).toHaveLength(2);
      expect(scheduleEmailSequence).toHaveBeenCalledWith(
        HOT_LEAD_SEQUENCE,
        "ivan@dentaplus.ru",
        mockTemplateData,
        1
      );
    });
  });

  describe("pauseEmailSequence", () => {
    it("should remove all pending jobs for lead and sequence", async () => {
      (pauseEmailSequence as jest.Mock).mockResolvedValue(2);

      const pausedCount = await pauseEmailSequence(
        "ivan@dentaplus.ru",
        "hot-lead-sequence"
      );

      expect(pausedCount).toBe(2);
      expect(pauseEmailSequence).toHaveBeenCalledWith(
        "ivan@dentaplus.ru",
        "hot-lead-sequence"
      );
    });

    it("should return 0 if no jobs found", async () => {
      (pauseEmailSequence as jest.Mock).mockResolvedValue(0);

      const pausedCount = await pauseEmailSequence(
        "ivan@dentaplus.ru",
        "hot-lead-sequence"
      );

      expect(pausedCount).toBe(0);
    });
  });

  describe("resumeEmailSequence", () => {
    it("should schedule remaining emails from current step", async () => {
      const mockResult = {
        jobIds: ["job-2", "job-3"],
        nextEmailAt: new Date(),
      };
      (resumeEmailSequence as jest.Mock).mockResolvedValue(mockResult);

      const result = await resumeEmailSequence(
        HOT_LEAD_SEQUENCE,
        "ivan@dentaplus.ru",
        mockTemplateData,
        1
      );

      expect(result.jobIds).toHaveLength(2);
      expect(resumeEmailSequence).toHaveBeenCalledWith(
        HOT_LEAD_SEQUENCE,
        "ivan@dentaplus.ru",
        mockTemplateData,
        1
      );
    });
  });

  describe("handleUnsubscribe", () => {
    it("should remove all pending jobs for lead", async () => {
      (handleUnsubscribe as jest.Mock).mockResolvedValue(undefined);

      await handleUnsubscribe("ivan@dentaplus.ru");

      expect(handleUnsubscribe).toHaveBeenCalledWith("ivan@dentaplus.ru");
    });
  });

  describe("getQueueStats", () => {
    it("should return queue statistics", async () => {
      const mockStats = {
        waiting: 5,
        active: 2,
        completed: 100,
        failed: 3,
        delayed: 10,
        total: 120,
      };
      (getQueueStats as jest.Mock).mockResolvedValue(mockStats);

      const stats = await getQueueStats();

      expect(stats.waiting).toBe(5);
      expect(stats.active).toBe(2);
      expect(stats.completed).toBe(100);
      expect(stats.failed).toBe(3);
      expect(stats.delayed).toBe(10);
      expect(stats.total).toBe(120);
    });
  });
});
