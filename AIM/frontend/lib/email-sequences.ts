/**
 * Email Sequences for Lead Nurturing
 *
 * Automated email sequences based on lead tier (Hot/Warm/Cold)
 * Integrates with SendGrid Dynamic Templates (Phase 9)
 */

import { type LeadScore } from "./lead-scoring";

export interface EmailSequenceStep {
  id: string;
  name: string;
  templateId: string; // SendGrid Dynamic Template ID
  delayMinutes: number; // Delay from previous step (0 for immediate)
  subject: string;
  description: string;
}

export interface EmailSequence {
  id: string;
  name: string;
  tier: "hot" | "warm" | "cold";
  description: string;
  steps: EmailSequenceStep[];
}

/**
 * Hot Lead Sequence (immediate follow-up)
 *
 * Goal: Convert to meeting within 24 hours
 * Timeline: 0 → 1h → 2h
 */
export const HOT_LEAD_SEQUENCE: EmailSequence = {
  id: "hot-lead-sequence",
  name: "Hot Lead - Immediate Follow-up",
  tier: "hot",
  description: "Aggressive follow-up for high-intent leads. Goal: meeting within 24h.",
  steps: [
    {
      id: "hot-welcome",
      name: "Welcome & Next Steps",
      templateId: "d-hot-welcome-001", // TODO: Create in SendGrid
      delayMinutes: 0, // Immediate
      subject: "{{clinicName}} - Ваша заявка получена! Звоним через 15 минут",
      description: "Personal introduction, confirm we received their request, set expectations for call",
    },
    {
      id: "hot-case-study",
      name: "Relevant Case Study",
      templateId: "d-hot-case-study-001",
      delayMinutes: 60, // 1 hour after welcome
      subject: "Как {{similarClinic}} увеличила поток пациентов на {{growthPercent}}%",
      description: "Case study matching their specialty, show concrete results",
    },
    {
      id: "hot-meeting-invite",
      name: "Meeting Invitation",
      templateId: "d-hot-meeting-001",
      delayMinutes: 120, // 2 hours after welcome
      subject: "Готовы обсудить стратегию для {{clinicName}}?",
      description: "Calendar link for consultation, urgency (limited slots)",
    },
  ],
};

/**
 * Warm Lead Sequence (nurturing)
 *
 * Goal: Build trust, educate, convert to meeting within 7 days
 * Timeline: 0 → 1d → 3d → 5d → 7d
 */
export const WARM_LEAD_SEQUENCE: EmailSequence = {
  id: "warm-lead-sequence",
  name: "Warm Lead - Nurturing Sequence",
  tier: "warm",
  description: "Educational nurturing sequence. Goal: meeting within 7 days.",
  steps: [
    {
      id: "warm-welcome",
      name: "Welcome & Value Proposition",
      templateId: "d-warm-welcome-001",
      delayMinutes: 0, // Immediate
      subject: "{{clinicName}} - Как AI увеличивает поток пациентов на 30%+",
      description: "Introduction, value proposition, what makes us different",
    },
    {
      id: "warm-education-1",
      name: "Industry Insights",
      templateId: "d-warm-education-001",
      delayMinutes: 1440, // 1 day (24 hours)
      subject: "5 ошибок медицинского маркетинга, которые стоят вам пациентов",
      description: "Educational content, position as expert, no hard sell",
    },
    {
      id: "warm-case-study",
      name: "Success Stories",
      templateId: "d-warm-case-study-001",
      delayMinutes: 4320, // 3 days (72 hours)
      subject: "Кейс: {{similarClinic}} - от 50 до 200 пациентов в месяц",
      description: "Detailed case study with metrics, testimonial",
    },
    {
      id: "warm-roi-calculator",
      name: "ROI Calculator",
      templateId: "d-warm-roi-001",
      delayMinutes: 7200, // 5 days (120 hours)
      subject: "Рассчитайте ROI для {{clinicName}} за 2 минуты",
      description: "Interactive ROI calculator, budget justification tool",
    },
    {
      id: "warm-meeting-invite",
      name: "Consultation Offer",
      templateId: "d-warm-meeting-001",
      delayMinutes: 10080, // 7 days (168 hours)
      subject: "Бесплатная консультация для {{clinicName}} - осталось 3 слота",
      description: "Meeting invitation with urgency (limited availability)",
    },
  ],
};

/**
 * Cold Lead Sequence (long-term nurturing)
 *
 * Goal: Stay top-of-mind, re-engage when ready
 * Timeline: 0 → 7d → 14d → 21d → 28d → 30d
 */
export const COLD_LEAD_SEQUENCE: EmailSequence = {
  id: "cold-lead-sequence",
  name: "Cold Lead - Long-term Nurturing",
  tier: "cold",
  description: "Long-term educational sequence. Goal: re-engagement when ready.",
  steps: [
    {
      id: "cold-welcome",
      name: "Welcome & Introduction",
      templateId: "d-cold-welcome-001",
      delayMinutes: 0, // Immediate
      subject: "{{clinicName}} - Спасибо за интерес к AI-маркетингу",
      description: "Soft introduction, set expectations for educational content",
    },
    {
      id: "cold-education-1",
      name: "Educational Series - Week 1",
      templateId: "d-cold-education-001",
      delayMinutes: 10080, // 7 days
      subject: "Неделя 1: Основы медицинского маркетинга в 2026",
      description: "Educational content, industry trends, no sales pitch",
    },
    {
      id: "cold-education-2",
      name: "Educational Series - Week 2",
      templateId: "d-cold-education-002",
      delayMinutes: 20160, // 14 days
      subject: "Неделя 2: Как AI меняет привлечение пациентов",
      description: "AI in healthcare marketing, use cases, benefits",
    },
    {
      id: "cold-education-3",
      name: "Educational Series - Week 3",
      templateId: "d-cold-education-003",
      delayMinutes: 30240, // 21 days
      subject: "Неделя 3: SEO для медицинских клиник - что работает в 2026",
      description: "SEO best practices, Yandex algorithm updates",
    },
    {
      id: "cold-education-4",
      name: "Educational Series - Week 4",
      templateId: "d-cold-education-004",
      delayMinutes: 40320, // 28 days
      subject: "Неделя 4: Яндекс.Директ для клиник - полное руководство",
      description: "Yandex.Direct guide, budget optimization, targeting",
    },
    {
      id: "cold-reengagement",
      name: "Re-engagement Offer",
      templateId: "d-cold-reengagement-001",
      delayMinutes: 43200, // 30 days
      subject: "{{clinicName}} - Специальное предложение на аудит (только 3 дня)",
      description: "Special offer, free audit, urgency to re-engage",
    },
  ],
};

/**
 * Get email sequence by lead tier
 */
export function getSequenceByTier(tier: "hot" | "warm" | "cold"): EmailSequence {
  switch (tier) {
    case "hot":
      return HOT_LEAD_SEQUENCE;
    case "warm":
      return WARM_LEAD_SEQUENCE;
    case "cold":
      return COLD_LEAD_SEQUENCE;
  }
}

/**
 * Get all email sequences
 */
export function getAllSequences(): EmailSequence[] {
  return [HOT_LEAD_SEQUENCE, WARM_LEAD_SEQUENCE, COLD_LEAD_SEQUENCE];
}

/**
 * Calculate send times for a sequence
 */
export function calculateSendTimes(sequence: EmailSequence, startTime: Date = new Date()): Date[] {
  const sendTimes: Date[] = [];
  let currentTime = new Date(startTime);

  for (const step of sequence.steps) {
    currentTime = new Date(currentTime.getTime() + step.delayMinutes * 60 * 1000);
    sendTimes.push(new Date(currentTime));
  }

  return sendTimes;
}

/**
 * Email template data (personalization)
 */
export interface EmailTemplateData {
  // Lead data
  name: string;
  clinicName?: string;
  specialty?: string;

  // Score data
  score?: number;
  tier?: string;
  confidence?: number;

  // Personalization
  similarClinic?: string;
  growthPercent?: number;
  recommendations?: string[];

  // Links
  calendarLink?: string;
  roiCalculatorLink?: string;
  unsubscribeLink?: string;

  // Payment data (transactional emails)
  amount?: string;
  currency?: string;
  paymentId?: string;
  refundId?: string;
  invoiceNumber?: string;
  reason?: string;
  date?: string;
}

/**
 * Build template data from lead information
 */
export function buildTemplateData(
  name: string,
  clinicName: string,
  specialty: string,
  score: LeadScore
): EmailTemplateData {
  return {
    name,
    clinicName,
    specialty,
    score: score.score,
    tier: score.tier,
    confidence: score.confidence,
    recommendations: score.recommendations.slice(0, 3), // Top 3
    // TODO: Add dynamic data in Phase 2.4
    similarClinic: "Стоматология Дента Плюс", // Placeholder
    growthPercent: 320, // Placeholder
    calendarLink: "https://iamaim.ru/calendar", // Placeholder
    roiCalculatorLink: "https://iamaim.ru/roi-calculator", // Placeholder
    unsubscribeLink: "https://iamaim.ru/unsubscribe", // Placeholder
  };
}
