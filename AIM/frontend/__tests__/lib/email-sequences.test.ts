import {
  getSequenceByTier,
  getAllSequences,
  calculateSendTimes,
  buildTemplateData,
  HOT_LEAD_SEQUENCE,
  WARM_LEAD_SEQUENCE,
  COLD_LEAD_SEQUENCE,
  type LeadScore,
} from "@/lib/email-sequences";

describe("Email Sequences", () => {
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

  describe("getSequenceByTier", () => {
    it("should return hot sequence for hot tier", () => {
      const sequence = getSequenceByTier("hot");
      expect(sequence.id).toBe("hot-lead-sequence");
      expect(sequence.tier).toBe("hot");
      expect(sequence.steps).toHaveLength(3);
    });

    it("should return warm sequence for warm tier", () => {
      const sequence = getSequenceByTier("warm");
      expect(sequence.id).toBe("warm-lead-sequence");
      expect(sequence.tier).toBe("warm");
      expect(sequence.steps).toHaveLength(5);
    });

    it("should return cold sequence for cold tier", () => {
      const sequence = getSequenceByTier("cold");
      expect(sequence.id).toBe("cold-lead-sequence");
      expect(sequence.tier).toBe("cold");
      expect(sequence.steps).toHaveLength(6);
    });
  });

  describe("getAllSequences", () => {
    it("should return all three sequences", () => {
      const sequences = getAllSequences();
      expect(sequences).toHaveLength(3);
      expect(sequences.map((s) => s.tier)).toEqual(["hot", "warm", "cold"]);
    });
  });

  describe("HOT_LEAD_SEQUENCE", () => {
    it("should have correct structure", () => {
      expect(HOT_LEAD_SEQUENCE.id).toBe("hot-lead-sequence");
      expect(HOT_LEAD_SEQUENCE.tier).toBe("hot");
      expect(HOT_LEAD_SEQUENCE.steps).toHaveLength(3);
    });

    it("should have immediate first email", () => {
      const firstStep = HOT_LEAD_SEQUENCE.steps[0];
      expect(firstStep.delayMinutes).toBe(0);
      expect(firstStep.id).toBe("hot-welcome");
    });

    it("should have 1 hour delay for second email", () => {
      const secondStep = HOT_LEAD_SEQUENCE.steps[1];
      expect(secondStep.delayMinutes).toBe(60);
      expect(secondStep.id).toBe("hot-case-study");
    });

    it("should have 2 hour delay for third email", () => {
      const thirdStep = HOT_LEAD_SEQUENCE.steps[2];
      expect(thirdStep.delayMinutes).toBe(120);
      expect(thirdStep.id).toBe("hot-meeting-invite");
    });

    it("should have SendGrid template IDs", () => {
      HOT_LEAD_SEQUENCE.steps.forEach((step) => {
        expect(step.templateId).toMatch(/^d-hot-/);
      });
    });
  });

  describe("WARM_LEAD_SEQUENCE", () => {
    it("should have correct structure", () => {
      expect(WARM_LEAD_SEQUENCE.id).toBe("warm-lead-sequence");
      expect(WARM_LEAD_SEQUENCE.tier).toBe("warm");
      expect(WARM_LEAD_SEQUENCE.steps).toHaveLength(5);
    });

    it("should have immediate first email", () => {
      const firstStep = WARM_LEAD_SEQUENCE.steps[0];
      expect(firstStep.delayMinutes).toBe(0);
    });

    it("should have 1 day delay for second email", () => {
      const secondStep = WARM_LEAD_SEQUENCE.steps[1];
      expect(secondStep.delayMinutes).toBe(1440); // 24 hours
    });

    it("should have 3 day delay for third email", () => {
      const thirdStep = WARM_LEAD_SEQUENCE.steps[2];
      expect(thirdStep.delayMinutes).toBe(4320); // 72 hours
    });

    it("should have 7 day delay for last email", () => {
      const lastStep = WARM_LEAD_SEQUENCE.steps[4];
      expect(lastStep.delayMinutes).toBe(10080); // 168 hours
    });
  });

  describe("COLD_LEAD_SEQUENCE", () => {
    it("should have correct structure", () => {
      expect(COLD_LEAD_SEQUENCE.id).toBe("cold-lead-sequence");
      expect(COLD_LEAD_SEQUENCE.tier).toBe("cold");
      expect(COLD_LEAD_SEQUENCE.steps).toHaveLength(6);
    });

    it("should have immediate first email", () => {
      const firstStep = COLD_LEAD_SEQUENCE.steps[0];
      expect(firstStep.delayMinutes).toBe(0);
    });

    it("should have 7 day intervals for educational series", () => {
      const delays = COLD_LEAD_SEQUENCE.steps.slice(1, 5).map((s) => s.delayMinutes);
      expect(delays).toEqual([
        10080, // 7 days
        20160, // 14 days
        30240, // 21 days
        40320, // 28 days
      ]);
    });

    it("should have 30 day delay for re-engagement", () => {
      const lastStep = COLD_LEAD_SEQUENCE.steps[5];
      expect(lastStep.delayMinutes).toBe(43200); // 30 days
    });
  });

  describe("calculateSendTimes", () => {
    it("should calculate send times for hot sequence", () => {
      const startTime = new Date("2026-05-16T10:00:00Z");
      const sendTimes = calculateSendTimes(HOT_LEAD_SEQUENCE, startTime);

      expect(sendTimes).toHaveLength(3);
      expect(sendTimes[0].toISOString()).toBe("2026-05-16T10:00:00.000Z"); // Immediate
      expect(sendTimes[1].toISOString()).toBe("2026-05-16T11:00:00.000Z"); // +1 hour
      expect(sendTimes[2].toISOString()).toBe("2026-05-16T13:00:00.000Z"); // +2 hours from second
    });

    it("should calculate send times for warm sequence", () => {
      const startTime = new Date("2026-05-16T10:00:00Z");
      const sendTimes = calculateSendTimes(WARM_LEAD_SEQUENCE, startTime);

      expect(sendTimes).toHaveLength(5);
      expect(sendTimes[0].toISOString()).toBe("2026-05-16T10:00:00.000Z"); // Immediate
      expect(sendTimes[1].toISOString()).toBe("2026-05-17T10:00:00.000Z"); // +1 day
      expect(sendTimes[2].toISOString()).toBe("2026-05-20T10:00:00.000Z"); // +3 days from second
    });

    it("should use current time if no start time provided", () => {
      const before = Date.now();
      const sendTimes = calculateSendTimes(HOT_LEAD_SEQUENCE);
      const after = Date.now();

      const firstSendTime = sendTimes[0].getTime();
      expect(firstSendTime).toBeGreaterThanOrEqual(before);
      expect(firstSendTime).toBeLessThanOrEqual(after);
    });
  });

  describe("buildTemplateData", () => {
    it("should build template data with all required fields", () => {
      const data = buildTemplateData(
        "Иван Петров",
        "Стоматология Дента Плюс",
        "Стоматология",
        mockLeadScore
      );

      expect(data.name).toBe("Иван Петров");
      expect(data.clinicName).toBe("Стоматология Дента Плюс");
      expect(data.specialty).toBe("Стоматология");
      expect(data.score).toBe(85);
      expect(data.tier).toBe("hot");
      expect(data.confidence).toBe(0.95);
    });

    it("should include top 3 recommendations", () => {
      const data = buildTemplateData(
        "Иван Петров",
        "Стоматология Дента Плюс",
        "Стоматология",
        mockLeadScore
      );

      expect(data.recommendations).toHaveLength(2);
      expect(data.recommendations).toEqual([
        "🔥 Приоритет 1: Позвонить в течение 15 минут",
        "📧 Отправить персональное предложение с кейсами",
      ]);
    });

    it("should include placeholder data for personalization", () => {
      const data = buildTemplateData(
        "Иван Петров",
        "Стоматология Дента Плюс",
        "Стоматология",
        mockLeadScore
      );

      expect(data.similarClinic).toBeDefined();
      expect(data.growthPercent).toBeDefined();
      expect(data.calendarLink).toBeDefined();
      expect(data.roiCalculatorLink).toBeDefined();
      expect(data.unsubscribeLink).toBeDefined();
    });

    it("should limit recommendations to 3", () => {
      const scoreWithManyRecommendations: LeadScore = {
        ...mockLeadScore,
        recommendations: [
          "Recommendation 1",
          "Recommendation 2",
          "Recommendation 3",
          "Recommendation 4",
          "Recommendation 5",
        ],
      };

      const data = buildTemplateData(
        "Иван Петров",
        "Стоматология Дента Плюс",
        "Стоматология",
        scoreWithManyRecommendations
      );

      expect(data.recommendations).toHaveLength(3);
    });
  });
});
