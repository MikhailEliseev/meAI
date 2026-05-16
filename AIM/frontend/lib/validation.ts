import { z } from "zod";

// Phone validation for Russian format
const phoneRegex = /^(\+7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$/;

// Contact form validation schema
export const contactFormSchema = z.object({
  name: z
    .string()
    .min(2, "Имя должно содержать минимум 2 символа")
    .max(100, "Имя слишком длинное")
    .regex(/^[а-яА-ЯёЁa-zA-Z\s\-]+$/, "Имя может содержать только буквы, пробелы и дефисы"),

  phone: z
    .string()
    .regex(phoneRegex, "Введите корректный номер телефона (например: +7 999 123-45-67)")
    .transform((val) => val.replace(/[\s\-\(\)]/g, "")), // Normalize phone

  email: z
    .string()
    .email("Введите корректный email адрес")
    .max(255, "Email слишком длинный")
    .toLowerCase(),

  clinicName: z
    .string()
    .min(2, "Название клиники должно содержать минимум 2 символа")
    .max(200, "Название клиники слишком длинное"),

  specialty: z
    .string()
    .min(1, "Выберите специализацию клиники"),

  message: z
    .string()
    .min(10, "Сообщение должно содержать минимум 10 символов")
    .max(2000, "Сообщение слишком длинное (максимум 2000 символов)")
    .optional(),

  fz152Consent: z
    .boolean()
    .refine((val) => val === true, {
      message: "Необходимо согласие на обработку персональных данных",
    }),

  recaptchaToken: z
    .string()
    .min(1, "Ошибка проверки reCAPTCHA. Попробуйте обновить страницу."),
});

export type ContactFormData = z.infer<typeof contactFormSchema>;

// Specialties list
export const specialties = [
  { value: "", label: "Выберите специализацию" },
  { value: "dentistry", label: "Стоматология" },
  { value: "cosmetology", label: "Косметология" },
  { value: "cardiology", label: "Кардиология" },
  { value: "orthopedics", label: "Ортопедия" },
  { value: "pediatrics", label: "Педиатрия" },
  { value: "gynecology", label: "Гинекология" },
  { value: "ophthalmology", label: "Офтальмология" },
  { value: "neurology", label: "Неврология" },
  { value: "surgery", label: "Хирургия" },
  { value: "therapy", label: "Терапия" },
  { value: "dermatology", label: "Дерматология" },
  { value: "urology", label: "Урология" },
  { value: "endocrinology", label: "Эндокринология" },
  { value: "psychiatry", label: "Психиатрия" },
  { value: "other", label: "Другое" },
];

// Field-level encryption (simple XOR for demo, use proper encryption in production)
export function encryptField(value: string, key: string): string {
  if (!value) return "";

  let encrypted = "";
  for (let i = 0; i < value.length; i++) {
    encrypted += String.fromCharCode(
      value.charCodeAt(i) ^ key.charCodeAt(i % key.length)
    );
  }

  return Buffer.from(encrypted).toString("base64");
}

export function decryptField(encrypted: string, key: string): string {
  if (!encrypted) return "";

  try {
    const decoded = Buffer.from(encrypted, "base64").toString();
    let decrypted = "";

    for (let i = 0; i < decoded.length; i++) {
      decrypted += String.fromCharCode(
        decoded.charCodeAt(i) ^ key.charCodeAt(i % key.length)
      );
    }

    return decrypted;
  } catch {
    return "";
  }
}

// LocalStorage draft management
const DRAFT_KEY = "aim_contact_form_draft";
const DRAFT_EXPIRY_MS = 24 * 60 * 60 * 1000; // 24 hours

export interface FormDraft {
  data: Partial<ContactFormData>;
  timestamp: number;
}

export function saveDraft(data: Partial<ContactFormData>): void {
  try {
    const draft: FormDraft = {
      data,
      timestamp: Date.now(),
    };
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
  } catch (error) {
    console.error("Failed to save draft:", error);
  }
}

export function loadDraft(): Partial<ContactFormData> | null {
  try {
    const stored = localStorage.getItem(DRAFT_KEY);
    if (!stored) return null;

    const draft: FormDraft = JSON.parse(stored);

    // Check if draft expired
    if (Date.now() - draft.timestamp > DRAFT_EXPIRY_MS) {
      clearDraft();
      return null;
    }

    return draft.data;
  } catch (error) {
    console.error("Failed to load draft:", error);
    return null;
  }
}

export function clearDraft(): void {
  try {
    localStorage.removeItem(DRAFT_KEY);
  } catch (error) {
    console.error("Failed to clear draft:", error);
  }
}
