import { calculateLeadScore, type LeadData } from "@/lib/lead-scoring";

describe("Lead Scoring Engine", () => {
  describe("calculateLeadScore", () => {
    it("should score high-value lead as HOT (80+)", () => {
      const lead: LeadData = {
        name: "Иван Петров",
        phone: "+79991234567",
        email: "ivan@dentaplus.ru",
        clinicName: "Стоматология Дента Плюс",
        specialty: "Стоматология",
        message: "Ищем агентство для продвижения. Бюджет 300К/месяц. Нужно срочно увеличить поток пациентов.",
        clinicSize: "large",
        location: "Москва",
        currentMarketingSpend: 300000,
        hasWebsite: true,
        websiteQuality: 85,
        onlinePresence: {
          hasYandexBusiness: true,
          hasInstagram: true,
          hasVK: true,
          hasTelegram: true,
          reviewCount: 120,
          avgRating: 4.8,
        },
        competitionLevel: "medium",
        responseTime: 1.5,
        formCompletionRate: 1.0,
        previousInteractions: 0,
        referralSource: "google",
        deviceType: "desktop",
        timeOfDay: 14,
        dayOfWeek: 2,
      };

      const score = calculateLeadScore(lead);

      expect(score.score).toBeGreaterThanOrEqual(80);
      expect(score.tier).toBe("hot");
      expect(score.confidence).toBeGreaterThan(0.9);
      expect(score.factors.length).toBe(15);
      expect(score.recommendations).toContain("🔥 Приоритет 1: Позвонить в течение 15 минут");
    });

    it("should score medium-value lead as WARM (50-79)", () => {
      const lead: LeadData = {
        name: "Мария Иванова",
        phone: "+79991234568",
        email: "maria@clinic.ru",
        clinicName: "Клиника Здоровье",
        specialty: "Терапия",
        message: "Интересует продвижение клиники",
        clinicSize: "small",
        location: "Воронеж",
        currentMarketingSpend: 80000,
        hasWebsite: true,
        websiteQuality: 60,
        onlinePresence: {
          hasYandexBusiness: true,
          hasInstagram: false,
          hasVK: false,
          hasTelegram: false,
          reviewCount: 15,
          avgRating: 4.2,
        },
        competitionLevel: "medium",
        responseTime: 10,
        formCompletionRate: 0.7,
        previousInteractions: 0,
        referralSource: "yandex",
        deviceType: "mobile",
        timeOfDay: 19,
        dayOfWeek: 3,
      };

      const score = calculateLeadScore(lead);

      expect(score.score).toBeGreaterThanOrEqual(50);
      expect(score.score).toBeLessThan(80);
      expect(score.tier).toBe("warm");
      expect(score.recommendations).toContain("📞 Позвонить в течение 2 часов");
    });

    it("should score low-value lead as COLD (<50)", () => {
      const lead: LeadData = {
        name: "Петр Сидоров",
        phone: "+79991234569",
        email: "petr@example.com",
        clinicName: "Клиника",
        specialty: "Другое",
        message: "Хочу узнать цены",
        clinicSize: "small",
        currentMarketingSpend: 20000,
        hasWebsite: false,
        competitionLevel: "high",
        responseTime: 120,
        formCompletionRate: 0.3,
        previousInteractions: 5,
        deviceType: "mobile",
        timeOfDay: 2,
        dayOfWeek: 0,
      };

      const score = calculateLeadScore(lead);

      expect(score.score).toBeLessThan(50);
      expect(score.tier).toBe("cold");
      expect(score.recommendations).toContain("📧 Добавить в email-последовательность");
    });

    it("should handle minimal lead data (only required fields)", () => {
      const lead: LeadData = {
        name: "Тест Тестов",
        phone: "+79991234570",
        email: "test@test.ru",
        clinicName: "Тестовая клиника",
        specialty: "Стоматология",
      };

      const score = calculateLeadScore(lead);

      expect(score.score).toBeGreaterThan(0);
      expect(score.score).toBeLessThan(100);
      expect(score.tier).toMatch(/hot|warm|cold/);
      expect(score.confidence).toBeLessThan(0.5); // Low confidence due to missing data
      expect(score.factors.length).toBe(15);
    });

    it("should give high specialty score for dentistry", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
      };

      const score = calculateLeadScore(lead);
      const specialtyFactor = score.factors.find((f) => f.category === "Specialty");

      expect(specialtyFactor).toBeDefined();
      expect(specialtyFactor!.score).toBe(90);
    });

    it("should give high location score for Moscow", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        location: "Москва",
      };

      const score = calculateLeadScore(lead);
      const locationFactor = score.factors.find((f) => f.category === "Location");

      expect(locationFactor).toBeDefined();
      expect(locationFactor!.score).toBe(100);
    });

    it("should give high clinic size score for large clinics", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        clinicSize: "large",
      };

      const score = calculateLeadScore(lead);
      const sizeFactor = score.factors.find((f) => f.category === "Clinic Size");

      expect(sizeFactor).toBeDefined();
      expect(sizeFactor!.score).toBe(100);
    });

    it("should give high marketing spend score for 300K+ budget", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        currentMarketingSpend: 350000,
      };

      const score = calculateLeadScore(lead);
      const spendFactor = score.factors.find((f) => f.category === "Marketing Spend");

      expect(spendFactor).toBeDefined();
      expect(spendFactor!.score).toBe(100);
    });

    it("should give low marketing spend score for <50K budget", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        currentMarketingSpend: 30000,
      };

      const score = calculateLeadScore(lead);
      const spendFactor = score.factors.find((f) => f.category === "Marketing Spend");

      expect(spendFactor).toBeDefined();
      expect(spendFactor!.score).toBe(30);
    });

    it("should give low website score for no website", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        hasWebsite: false,
      };

      const score = calculateLeadScore(lead);
      const websiteFactor = score.factors.find((f) => f.category === "Website Quality");

      expect(websiteFactor).toBeDefined();
      expect(websiteFactor!.score).toBe(20);
    });

    it("should calculate online presence score correctly", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        onlinePresence: {
          hasYandexBusiness: true,
          hasInstagram: true,
          hasVK: true,
          hasTelegram: true,
          reviewCount: 100,
          avgRating: 4.8,
        },
      };

      const score = calculateLeadScore(lead);
      const presenceFactor = score.factors.find((f) => f.category === "Online Presence");

      expect(presenceFactor).toBeDefined();
      expect(presenceFactor!.score).toBe(100); // 25+20+15+10+15+15 = 100
    });

    it("should give high response time score for <2 min", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        responseTime: 1.5,
      };

      const score = calculateLeadScore(lead);
      const timeFactor = score.factors.find((f) => f.category === "Response Time");

      expect(timeFactor).toBeDefined();
      expect(timeFactor!.score).toBe(100);
    });

    it("should give low response time score for >1 hour", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        responseTime: 90,
      };

      const score = calculateLeadScore(lead);
      const timeFactor = score.factors.find((f) => f.category === "Response Time");

      expect(timeFactor).toBeDefined();
      expect(timeFactor!.score).toBe(30);
    });

    it("should score detailed message higher than short message", () => {
      const leadDetailed: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        message: "Ищем агентство для комплексного продвижения нашей стоматологии. Текущий бюджет 200К/месяц на Яндекс.Директ, но результаты не устраивают. Хотим увеличить поток пациентов на 50% за 3 месяца. Готовы обсудить детали на встрече.",
      };

      const leadShort: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        message: "Интересует продвижение",
      };

      const scoreDetailed = calculateLeadScore(leadDetailed);
      const scoreShort = calculateLeadScore(leadShort);

      const messageFactorDetailed = scoreDetailed.factors.find((f) => f.category === "Message Quality");
      const messageFactorShort = scoreShort.factors.find((f) => f.category === "Message Quality");

      expect(messageFactorDetailed!.score).toBeGreaterThan(messageFactorShort!.score);
    });

    it("should boost message score for urgency keywords", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        message: "Нужно срочно увеличить поток пациентов. Готовы обсудить бюджет 200К/месяц.",
      };

      const score = calculateLeadScore(lead);
      const messageFactor = score.factors.find((f) => f.category === "Message Quality");

      expect(messageFactor).toBeDefined();
      expect(messageFactor!.score).toBeGreaterThan(60); // 60 (base for 50-100 chars) + 10 (numbers) + 5 (urgency) = 75
    });

    it("should sort factors by contribution (descending)", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        clinicSize: "large",
        location: "Москва",
      };

      const score = calculateLeadScore(lead);

      for (let i = 0; i < score.factors.length - 1; i++) {
        expect(score.factors[i].contribution).toBeGreaterThanOrEqual(
          score.factors[i + 1].contribution
        );
      }
    });

    it("should calculate confidence based on known factors", () => {
      const leadMinimal: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
      };

      const leadComplete: LeadData = {
        ...leadMinimal,
        clinicSize: "large",
        location: "Москва",
        currentMarketingSpend: 300000,
        hasWebsite: true,
        websiteQuality: 85,
        onlinePresence: {
          hasYandexBusiness: true,
          hasInstagram: true,
          hasVK: true,
          hasTelegram: true,
          reviewCount: 100,
          avgRating: 4.8,
        },
        competitionLevel: "medium",
        responseTime: 2,
        formCompletionRate: 1.0,
        previousInteractions: 0,
        referralSource: "google",
        deviceType: "desktop",
        timeOfDay: 14,
        dayOfWeek: 2,
      };

      const scoreMinimal = calculateLeadScore(leadMinimal);
      const scoreComplete = calculateLeadScore(leadComplete);

      expect(scoreComplete.confidence).toBeGreaterThan(scoreMinimal.confidence);
    });

    it("should provide website audit recommendation for low website quality", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        hasWebsite: false,
      };

      const score = calculateLeadScore(lead);

      expect(score.recommendations).toContain("💡 Предложить аудит сайта как lead magnet");
    });

    it("should provide Yandex.Business recommendation for low online presence", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        onlinePresence: {
          hasYandexBusiness: false,
          hasInstagram: false,
          hasVK: false,
          hasTelegram: false,
          reviewCount: 0,
          avgRating: 0,
        },
      };

      const score = calculateLeadScore(lead);

      expect(score.recommendations).toContain("💡 Предложить бесплатную настройку Яндекс.Бизнес");
    });

    it("should provide ROI calculator recommendation for low marketing spend", () => {
      const lead: LeadData = {
        name: "Test",
        phone: "+79991234567",
        email: "test@test.ru",
        clinicName: "Test",
        specialty: "Стоматология",
        currentMarketingSpend: 20000,
      };

      const score = calculateLeadScore(lead);

      expect(score.recommendations).toContain("💡 Показать ROI-калькулятор для обоснования бюджета");
    });
  });
});
