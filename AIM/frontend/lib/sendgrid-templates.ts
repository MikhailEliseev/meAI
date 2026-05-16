/**
 * SendGrid Dynamic Templates Management
 *
 * Manages SendGrid Dynamic Templates for email sequences
 * Integrates with email-sequences.ts (Phase 9)
 */

import sgMail from "@sendgrid/mail";
import { type EmailTemplateData } from "./email-sequences";

// Initialize SendGrid
if (process.env.SENDGRID_API_KEY) {
  sgMail.setApiKey(process.env.SENDGRID_API_KEY);
}

export interface SendEmailInput {
  to: string;
  templateId: string;
  dynamicTemplateData: EmailTemplateData;
  from?: string;
  replyTo?: string;
}

export interface SendEmailResult {
  success: boolean;
  messageId?: string;
  error?: string;
}

/**
 * Send email using SendGrid Dynamic Template
 */
export async function sendTemplateEmail(input: SendEmailInput): Promise<SendEmailResult> {
  try {
    // Validate API key
    if (!process.env.SENDGRID_API_KEY) {
      throw new Error("SENDGRID_API_KEY not configured");
    }

    // Prepare email
    const msg = {
      to: input.to,
      from: input.from || process.env.FROM_EMAIL || "noreply@iamaim.ru",
      replyTo: input.replyTo || process.env.CONTACT_EMAIL || "info@iamaim.ru",
      templateId: input.templateId,
      dynamicTemplateData: input.dynamicTemplateData,
    };

    // Send email
    const [response] = await sgMail.send(msg);

    return {
      success: true,
      messageId: response.headers["x-message-id"] as string,
    };
  } catch (error) {
    console.error("[SendGrid] Error sending email:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * Send multiple emails in batch
 */
export async function sendBatchEmails(inputs: SendEmailInput[]): Promise<SendEmailResult[]> {
  const results: SendEmailResult[] = [];

  for (const input of inputs) {
    const result = await sendTemplateEmail(input);
    results.push(result);

    // Rate limiting: 100 emails per second (SendGrid limit)
    // Add 10ms delay between emails to be safe
    await new Promise((resolve) => setTimeout(resolve, 10));
  }

  return results;
}

/**
 * Verify SendGrid API key
 */
export async function verifyApiKey(): Promise<boolean> {
  try {
    if (!process.env.SENDGRID_API_KEY) {
      return false;
    }

    // Test API key by sending a test request
    // Note: SendGrid doesn't have a dedicated "verify" endpoint
    // We'll just check if the API key is set
    return true;
  } catch (error) {
    console.error("[SendGrid] API key verification failed:", error);
    return false;
  }
}

/**
 * SendGrid Dynamic Template IDs
 *
 * TODO: Create these templates in SendGrid dashboard
 * https://mc.sendgrid.com/dynamic-templates
 */
export const TEMPLATE_IDS = {
  // Hot Lead Sequence
  HOT_WELCOME: "d-hot-welcome-001",
  HOT_CASE_STUDY: "d-hot-case-study-001",
  HOT_MEETING: "d-hot-meeting-001",

  // Warm Lead Sequence
  WARM_WELCOME: "d-warm-welcome-001",
  WARM_EDUCATION_1: "d-warm-education-001",
  WARM_CASE_STUDY: "d-warm-case-study-001",
  WARM_ROI: "d-warm-roi-001",
  WARM_MEETING: "d-warm-meeting-001",

  // Cold Lead Sequence
  COLD_WELCOME: "d-cold-welcome-001",
  COLD_EDUCATION_1: "d-cold-education-001",
  COLD_EDUCATION_2: "d-cold-education-002",
  COLD_EDUCATION_3: "d-cold-education-003",
  COLD_EDUCATION_4: "d-cold-education-004",
  COLD_REENGAGEMENT: "d-cold-reengagement-001",
} as const;

/**
 * Template content guidelines for SendGrid dashboard
 *
 * Each template should include:
 * 1. Subject line with dynamic variables
 * 2. Preheader text (first 50 chars visible in inbox)
 * 3. HTML body with Handlebars syntax
 * 4. Plain text fallback
 * 5. Unsubscribe link (required by law)
 */
export const TEMPLATE_GUIDELINES = {
  HOT_WELCOME: {
    subject: "{{clinicName}} - Ваша заявка получена! Звоним через 15 минут",
    preheader: "Спасибо за обращение! Мы уже готовим персональное предложение.",
    variables: ["name", "clinicName", "specialty", "phone"],
    content: `
      Здравствуйте, {{name}}!

      Спасибо за обращение в AIM Agency. Мы получили вашу заявку от клиники {{clinicName}}.

      Наш специалист свяжется с вами по телефону {{phone}} в течение 15 минут.

      Пока готовим персональное предложение для {{specialty}}.

      С уважением,
      Команда AIM Agency
    `,
  },

  HOT_CASE_STUDY: {
    subject: "Как {{similarClinic}} увеличила поток пациентов на {{growthPercent}}%",
    preheader: "Реальный кейс клиники из вашей ниши",
    variables: ["name", "clinicName", "specialty", "similarClinic", "growthPercent"],
    content: `
      Здравствуйте, {{name}}!

      Хотим поделиться кейсом клиники {{similarClinic}} ({{specialty}}), которая увеличила поток пациентов на {{growthPercent}}%.

      Что мы сделали:
      - SEO-оптимизация сайта
      - Контекстная реклама в Яндекс.Директ
      - Контент-маркетинг

      Результаты за 3 месяца:
      - +{{growthPercent}}% новых пациентов
      - -40% стоимость привлечения
      - ROI 320%

      Готовы обсудить стратегию для {{clinicName}}?

      С уважением,
      Команда AIM Agency
    `,
  },

  HOT_MEETING: {
    subject: "Готовы обсудить стратегию для {{clinicName}}?",
    preheader: "Забронируйте бесплатную консультацию (осталось 3 слота)",
    variables: ["name", "clinicName", "calendarLink"],
    content: `
      Здравствуйте, {{name}}!

      Мы подготовили персональную стратегию для {{clinicName}}.

      Забронируйте бесплатную консультацию (30 минут):
      {{calendarLink}}

      На консультации обсудим:
      - Анализ вашей ниши
      - Стратегию привлечения пациентов
      - Прогноз результатов и ROI

      ⚠️ Осталось только 3 слота на эту неделю

      С уважением,
      Команда AIM Agency
    `,
  },

  // Warm and Cold templates follow similar structure
  // (abbreviated for brevity)
} as const;
