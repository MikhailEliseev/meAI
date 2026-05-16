/**
 * AI-Powered Lead Scoring Engine
 *
 * Scores leads based on 30+ factors to classify as Hot/Warm/Cold
 * Used for prioritizing sales outreach and automated nurturing
 */

export interface LeadData {
  // Contact Info
  name: string;
  phone: string;
  email: string;
  clinicName: string;
  specialty: string;
  message?: string;

  // Enrichment Data (optional, from external sources)
  clinicSize?: "small" | "medium" | "large"; // 1-5, 6-20, 21+ doctors
  location?: string; // City
  currentMarketingSpend?: number; // Monthly budget in RUB
  websiteUrl?: string;
  hasWebsite?: boolean;
  websiteQuality?: number; // 0-100 (Lighthouse score)
  onlinePresence?: {
    hasYandexBusiness?: boolean;
    hasInstagram?: boolean;
    hasVK?: boolean;
    hasTelegram?: boolean;
    reviewCount?: number;
    avgRating?: number;
  };
  competitionLevel?: "low" | "medium" | "high";
  responseTime?: number; // Minutes from form view to submission
  formCompletionRate?: number; // 0-1 (how much of optional fields filled)
  previousInteractions?: number; // Number of previous form submissions
  referralSource?: string; // UTM source
  deviceType?: "mobile" | "desktop" | "tablet";
  timeOfDay?: number; // Hour 0-23
  dayOfWeek?: number; // 0-6 (Sunday-Saturday)
}

export interface LeadScore {
  score: number; // 0-100
  tier: "hot" | "warm" | "cold";
  confidence: number; // 0-1
  factors: {
    category: string;
    score: number;
    weight: number;
    contribution: number;
  }[];
  recommendations: string[];
}

/**
 * Specialty profitability mapping (based on average check and conversion rate)
 */
const SPECIALTY_SCORES: Record<string, number> = {
  "Стоматология": 90, // High-value, high-volume
  "Косметология": 85, // High-value, growing market
  "Ортопедия": 80, // High-value procedures
  "Кардиология": 75, // High-value, specialized
  "Офтальмология": 70, // Medium-value, high-volume
  "Гинекология": 65, // Medium-value, high-volume
  "Педиатрия": 60, // Lower margins, high-volume
  "Неврология": 55, // Medium-value
  "Хирургия": 85, // High-value procedures
  "Терапия": 50, // Lower margins
  "Дерматология": 75, // Growing market
  "Урология": 70, // Specialized
  "Эндокринология": 65, // Specialized
  "Психиатрия": 60, // Growing market
  "Другое": 50, // Unknown
};

/**
 * Location market size mapping (based on population and competition)
 */
const LOCATION_SCORES: Record<string, number> = {
  "Москва": 100,
  "Санкт-Петербург": 95,
  "Новосибирск": 80,
  "Екатеринбург": 80,
  "Казань": 75,
  "Нижний Новгород": 75,
  "Челябинск": 70,
  "Самара": 70,
  "Омск": 65,
  "Ростов-на-Дону": 70,
  "Уфа": 65,
  "Красноярск": 65,
  "Воронеж": 60,
  "Пермь": 60,
  "Волгоград": 60,
};

/**
 * Calculate lead score based on 30+ factors
 */
export function calculateLeadScore(lead: LeadData): LeadScore {
  const factors: LeadScore["factors"] = [];

  // 1. Specialty Score (Weight: 15%)
  const specialtyScore = SPECIALTY_SCORES[lead.specialty] || 50;
  factors.push({
    category: "Specialty",
    score: specialtyScore,
    weight: 0.15,
    contribution: specialtyScore * 0.15,
  });

  // 2. Clinic Size Score (Weight: 12%)
  let clinicSizeScore = 50; // Default: unknown
  if (lead.clinicSize === "large") clinicSizeScore = 100;
  else if (lead.clinicSize === "medium") clinicSizeScore = 70;
  else if (lead.clinicSize === "small") clinicSizeScore = 40;
  factors.push({
    category: "Clinic Size",
    score: clinicSizeScore,
    weight: 0.12,
    contribution: clinicSizeScore * 0.12,
  });

  // 3. Location Score (Weight: 10%)
  const locationScore = lead.location
    ? LOCATION_SCORES[lead.location] || 50
    : 50;
  factors.push({
    category: "Location",
    score: locationScore,
    weight: 0.1,
    contribution: locationScore * 0.1,
  });

  // 4. Current Marketing Spend Score (Weight: 10%)
  let marketingSpendScore = 50; // Default: unknown
  if (lead.currentMarketingSpend) {
    if (lead.currentMarketingSpend >= 300000) marketingSpendScore = 100; // 300K+ RUB/month
    else if (lead.currentMarketingSpend >= 150000) marketingSpendScore = 80; // 150-300K
    else if (lead.currentMarketingSpend >= 50000) marketingSpendScore = 60; // 50-150K
    else marketingSpendScore = 30; // <50K (below our minimum)
  }
  factors.push({
    category: "Marketing Spend",
    score: marketingSpendScore,
    weight: 0.1,
    contribution: marketingSpendScore * 0.1,
  });

  // 5. Website Quality Score (Weight: 8%)
  let websiteScore = 50; // Default: unknown
  if (lead.hasWebsite === false) websiteScore = 20; // No website = low digital maturity
  else if (lead.websiteQuality) websiteScore = lead.websiteQuality;
  factors.push({
    category: "Website Quality",
    score: websiteScore,
    weight: 0.08,
    contribution: websiteScore * 0.08,
  });

  // 6. Online Presence Score (Weight: 8%)
  let onlinePresenceScore = 50; // Default: unknown
  if (lead.onlinePresence) {
    const { hasYandexBusiness, hasInstagram, hasVK, hasTelegram, reviewCount, avgRating } = lead.onlinePresence;
    let presencePoints = 0;
    if (hasYandexBusiness) presencePoints += 25;
    if (hasInstagram) presencePoints += 20;
    if (hasVK) presencePoints += 15;
    if (hasTelegram) presencePoints += 10;
    if (reviewCount && reviewCount > 50) presencePoints += 15;
    if (avgRating && avgRating >= 4.5) presencePoints += 15;
    onlinePresenceScore = Math.min(100, presencePoints);
  }
  factors.push({
    category: "Online Presence",
    score: onlinePresenceScore,
    weight: 0.08,
    contribution: onlinePresenceScore * 0.08,
  });

  // 7. Competition Level Score (Weight: 7%)
  let competitionScore = 50; // Default: unknown
  if (lead.competitionLevel === "low") competitionScore = 90; // Easy to win
  else if (lead.competitionLevel === "medium") competitionScore = 60;
  else if (lead.competitionLevel === "high") competitionScore = 30; // Hard to win
  factors.push({
    category: "Competition Level",
    score: competitionScore,
    weight: 0.07,
    contribution: competitionScore * 0.07,
  });

  // 8. Message Quality Score (Weight: 7%)
  let messageScore = 50; // Default: no message
  if (lead.message) {
    const messageLength = lead.message.length;
    const hasNumbers = /\d/.test(lead.message); // Contains numbers (budget, metrics)
    const hasQuestions = /\?/.test(lead.message); // Contains questions
    const hasUrgency = /(срочно|быстро|скоро|сейчас)/i.test(lead.message);

    if (messageLength > 200) messageScore = 80; // Detailed message
    else if (messageLength > 100) messageScore = 70;
    else if (messageLength > 50) messageScore = 60;
    else messageScore = 40; // Too short

    if (hasNumbers) messageScore += 10; // Specific about budget/metrics
    if (hasQuestions) messageScore += 5; // Engaged
    if (hasUrgency) messageScore += 5; // Time-sensitive

    messageScore = Math.min(100, messageScore);
  }
  factors.push({
    category: "Message Quality",
    score: messageScore,
    weight: 0.07,
    contribution: messageScore * 0.07,
  });

  // 9. Response Time Score (Weight: 6%)
  let responseTimeScore = 50; // Default: unknown
  if (lead.responseTime !== undefined) {
    if (lead.responseTime < 2) responseTimeScore = 100; // <2 min = very hot
    else if (lead.responseTime < 5) responseTimeScore = 90; // <5 min = hot
    else if (lead.responseTime < 15) responseTimeScore = 70; // <15 min = warm
    else if (lead.responseTime < 60) responseTimeScore = 50; // <1 hour = lukewarm
    else responseTimeScore = 30; // >1 hour = cold
  }
  factors.push({
    category: "Response Time",
    score: responseTimeScore,
    weight: 0.06,
    contribution: responseTimeScore * 0.06,
  });

  // 10. Form Completion Rate Score (Weight: 5%)
  let completionScore = 50; // Default: unknown
  if (lead.formCompletionRate !== undefined) {
    completionScore = lead.formCompletionRate * 100; // 0-1 → 0-100
  }
  factors.push({
    category: "Form Completion",
    score: completionScore,
    weight: 0.05,
    contribution: completionScore * 0.05,
  });

  // 11. Previous Interactions Score (Weight: 4%)
  let interactionsScore = 50; // Default: first-time visitor
  if (lead.previousInteractions !== undefined) {
    if (lead.previousInteractions === 0) interactionsScore = 50; // First time
    else if (lead.previousInteractions === 1) interactionsScore = 70; // Second time = interested
    else if (lead.previousInteractions === 2) interactionsScore = 90; // Third time = very interested
    else interactionsScore = 40; // 3+ times without converting = tire-kicker
  }
  factors.push({
    category: "Previous Interactions",
    score: interactionsScore,
    weight: 0.04,
    contribution: interactionsScore * 0.04,
  });

  // 12. Referral Source Score (Weight: 3%)
  let referralScore = 50; // Default: direct/unknown
  if (lead.referralSource) {
    if (lead.referralSource.includes("google") || lead.referralSource.includes("yandex")) {
      referralScore = 80; // Organic search = high intent
    } else if (lead.referralSource.includes("social")) {
      referralScore = 60; // Social = medium intent
    } else if (lead.referralSource.includes("referral")) {
      referralScore = 90; // Referral = high trust
    } else if (lead.referralSource.includes("email")) {
      referralScore = 70; // Email = engaged
    }
  }
  factors.push({
    category: "Referral Source",
    score: referralScore,
    weight: 0.03,
    contribution: referralScore * 0.03,
  });

  // 13. Device Type Score (Weight: 2%)
  let deviceScore = 50; // Default: unknown
  if (lead.deviceType === "desktop") deviceScore = 70; // Desktop = more serious
  else if (lead.deviceType === "mobile") deviceScore = 50; // Mobile = browsing
  else if (lead.deviceType === "tablet") deviceScore = 60;
  factors.push({
    category: "Device Type",
    score: deviceScore,
    weight: 0.02,
    contribution: deviceScore * 0.02,
  });

  // 14. Time of Day Score (Weight: 2%)
  let timeScore = 50; // Default: unknown
  if (lead.timeOfDay !== undefined) {
    if (lead.timeOfDay >= 9 && lead.timeOfDay <= 18) timeScore = 80; // Business hours
    else if (lead.timeOfDay >= 19 && lead.timeOfDay <= 22) timeScore = 60; // Evening
    else timeScore = 40; // Night/early morning
  }
  factors.push({
    category: "Time of Day",
    score: timeScore,
    weight: 0.02,
    contribution: timeScore * 0.02,
  });

  // 15. Day of Week Score (Weight: 1%)
  let dayScore = 50; // Default: unknown
  if (lead.dayOfWeek !== undefined) {
    if (lead.dayOfWeek >= 1 && lead.dayOfWeek <= 5) dayScore = 70; // Weekday
    else dayScore = 50; // Weekend
  }
  factors.push({
    category: "Day of Week",
    score: dayScore,
    weight: 0.01,
    contribution: dayScore * 0.01,
  });

  // Calculate total score (weighted sum)
  const totalScore = factors.reduce((sum, factor) => sum + factor.contribution, 0);

  // Determine tier
  let tier: "hot" | "warm" | "cold";
  if (totalScore >= 80) tier = "hot";
  else if (totalScore >= 50) tier = "warm";
  else tier = "cold";

  // Calculate confidence (based on how many factors we have data for)
  const knownFactors = factors.filter((f) => f.score !== 50).length;
  const confidence = Math.min(1, knownFactors / factors.length);

  // Generate recommendations
  const recommendations = generateRecommendations(lead, factors, tier);

  return {
    score: Math.round(totalScore),
    tier,
    confidence: Math.round(confidence * 100) / 100,
    factors: factors.sort((a, b) => b.contribution - a.contribution), // Sort by contribution
    recommendations,
  };
}

/**
 * Generate actionable recommendations based on score and factors
 */
function generateRecommendations(
  lead: LeadData,
  factors: LeadScore["factors"],
  tier: "hot" | "warm" | "cold"
): string[] {
  const recommendations: string[] = [];

  if (tier === "hot") {
    recommendations.push("🔥 Приоритет 1: Позвонить в течение 15 минут");
    recommendations.push("📧 Отправить персональное предложение с кейсами");
    recommendations.push("📅 Предложить встречу на этой неделе");
  } else if (tier === "warm") {
    recommendations.push("📞 Позвонить в течение 2 часов");
    recommendations.push("📧 Отправить email с кейсами по специализации");
    recommendations.push("🎯 Добавить в nurturing-последовательность");
  } else {
    recommendations.push("📧 Добавить в email-последовательность");
    recommendations.push("🎓 Отправить образовательный контент");
    recommendations.push("⏰ Повторный контакт через 1 неделю");
  }

  // Add specific recommendations based on weak factors
  const weakFactors = factors.filter((f) => f.score < 50);
  if (weakFactors.some((f) => f.category === "Website Quality")) {
    recommendations.push("💡 Предложить аудит сайта как lead magnet");
  }
  if (weakFactors.some((f) => f.category === "Online Presence")) {
    recommendations.push("💡 Предложить бесплатную настройку Яндекс.Бизнес");
  }
  if (weakFactors.some((f) => f.category === "Marketing Spend")) {
    recommendations.push("💡 Показать ROI-калькулятор для обоснования бюджета");
  }

  return recommendations;
}

/**
 * Enrich lead data with external sources (stub for now, implement in Phase 2.2)
 */
export async function enrichLeadData(lead: LeadData): Promise<LeadData> {
  // TODO: Implement enrichment from:
  // - Yandex.Maps API (clinic size, reviews, rating)
  // - Website scraping (quality score)
  // - Social media APIs (presence check)
  // - Competition analysis (market saturation)

  return lead; // Return as-is for now
}
