"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { getStoredUtm } from "@/components/UTMCapture";
import {
  contactFormSchema,
  type ContactFormData,
  specialties,
  saveDraft,
  loadDraft,
  clearDraft,
  encryptField,
} from "@/lib/validation";

interface ContactFormProps {
  className?: string;
}

type SubmissionState = "idle" | "submitting" | "success" | "error";

export function ContactForm({ className }: ContactFormProps) {
  const [submissionState, setSubmissionState] = useState<SubmissionState>("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [recaptchaToken, setRecaptchaToken] = useState<string>("");

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    reset,
    setValue,
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactFormSchema),
    defaultValues: {
      name: "",
      phone: "",
      email: "",
      clinicName: "",
      specialty: "",
      message: "",
      fz152Consent: false,
      recaptchaToken: "",
    },
  });

  // Load draft on mount
  useEffect(() => {
    const draft = loadDraft();
    if (draft) {
      Object.entries(draft).forEach(([key, value]) => {
        if (value !== undefined && key !== "recaptchaToken" && key !== "fz152Consent") {
          setValue(key as keyof ContactFormData, value as any);
        }
      });
    }
  }, [setValue]);

  // Auto-save draft
  useEffect(() => {
    if (!isDirty) return;

    const subscription = watch((formData) => {
      const { recaptchaToken: _, fz152Consent: __, ...draftData } = formData;
      saveDraft(draftData);
    });

    return () => subscription.unsubscribe();
  }, [watch, isDirty]);

  // Load reCAPTCHA script
  useEffect(() => {
    const script = document.createElement("script");
    script.src = `https://www.google.com/recaptcha/api.js?render=${process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}`;
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  const executeRecaptcha = async (): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (typeof window === "undefined" || !(window as any).grecaptcha) {
        reject(new Error("reCAPTCHA not loaded"));
        return;
      }

      (window as any).grecaptcha.ready(() => {
        (window as any).grecaptcha
          .execute(process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY, { action: "submit" })
          .then((token: string) => resolve(token))
          .catch((error: Error) => reject(error));
      });
    });
  };

  const onSubmit = async (data: ContactFormData) => {
    setSubmissionState("submitting");
    setErrorMessage("");

    try {
      // Execute reCAPTCHA
      const token = await executeRecaptcha();
      data.recaptchaToken = token;

      // Encrypt sensitive fields
      const encryptionKey = process.env.NEXT_PUBLIC_ENCRYPTION_KEY || "default-key";
      const utm = getStoredUtm();
      const encryptedData = {
        ...data,
        phone: encryptField(data.phone, encryptionKey),
        email: encryptField(data.email, encryptionKey),
        utm_source: utm.utm_source || "",
        utm_medium: utm.utm_medium || "",
        utm_campaign: utm.utm_campaign || "",
        utm_term: utm.utm_term || "",
        utm_content: utm.utm_content || "",
      };

      // Submit to API
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(encryptedData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Ошибка отправки формы");
      }

      // Calculate lead score (async, non-blocking)
      fetch("/api/lead-score", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: data.name,
          phone: data.phone,
          email: data.email,
          clinicName: data.clinicName,
          specialty: data.specialty,
          message: data.message,
          // TODO: Add enrichment data in Phase 2.2
          // clinicSize, location, currentMarketingSpend, etc.
        }),
      })
        .then((res) => res.json())
        .then((score) => {
          console.log("[Lead Score]", score);

          // Track lead tier in analytics
          if (typeof window !== "undefined" && (window as any).ym) {
            (window as any).ym(
              process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID,
              "reachGoal",
              `lead_${score.tier}`
            );
          }

          // Create Linear issue (async, non-blocking)
          fetch("/api/linear/create-lead", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              name: data.name,
              phone: data.phone,
              email: data.email,
              clinicName: data.clinicName,
              specialty: data.specialty,
              message: data.message,
              score,
            }),
          })
            .then((res) => res.json())
            .then((result) => {
              if (result.success) {
                console.log("[Linear] Issue created:", result.issue);
              } else {
                console.warn("[Linear] Failed to create issue:", result.error);
              }
            })
            .catch((err) => console.error("[Linear] Error:", err));

          // Trigger email sequence (async, non-blocking)
          fetch("/api/email/send-sequence", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              name: data.name,
              email: data.email,
              clinicName: data.clinicName,
              specialty: data.specialty,
              score,
            }),
          })
            .then((res) => res.json())
            .then((result) => {
              if (result.success) {
                console.log("[Email Sequence] Started:", result.sequenceId);
                console.log("[Email Sequence] Emails sent:", result.emailsSent);
                if (result.nextEmailAt) {
                  console.log("[Email Sequence] Next email at:", result.nextEmailAt);
                }
              } else {
                console.warn("[Email Sequence] Failed:", result.error);
              }
            })
            .catch((err) => console.error("[Email Sequence] Error:", err));
        })
        .catch((err) => console.error("[Lead Score Error]", err));

      // Success
      setSubmissionState("success");
      clearDraft();
      reset();

      // Track analytics
      if (typeof window !== "undefined" && (window as any).ym) {
        (window as any).ym(process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID, "reachGoal", "contact_form_submit");
      }
    } catch (error) {
      console.error("Form submission error:", error);
      setSubmissionState("error");
      setErrorMessage(
        error instanceof Error ? error.message : "Произошла ошибка. Попробуйте позже."
      );
    }
  };

  return (
    <section
      id="contact-form"
      className={cn("py-20 px-4 bg-canvas scroll-mt-20", className)}
      aria-labelledby="contact-heading"
    >
      <div className="max-w-3xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2
            id="contact-heading"
            className="text-3xl md:text-4xl font-bold text-ink mb-4"
          >
            Получите бесплатную консультацию
          </h2>
          <p className="text-lg text-text-muted">
            Заполните форму, и мы свяжемся с вами в течение 15 минут
          </p>
        </motion.div>

        {/* Success State */}
        {submissionState === "success" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-semantic-success/10 border border-semantic-success rounded-lg p-8 text-center"
          >
            <div className="text-6xl mb-4" aria-hidden="true">
              ✓
            </div>
            <h3 className="text-2xl font-bold text-ink mb-2">
              Спасибо за обращение!
            </h3>
            <p className="text-text-muted mb-6">
              Мы получили вашу заявку и свяжемся с вами в ближайшее время.
            </p>
            <button
              onClick={() => setSubmissionState("idle")}
              className="btn-secondary"
            >
              Отправить ещё одну заявку
            </button>
          </motion.div>
        )}

        {/* Form */}
        {submissionState !== "success" && (
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            onSubmit={handleSubmit(onSubmit)}
            className="bg-surface-2 rounded-lg border border-border-hairline p-8 space-y-6"
            noValidate
          >
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-text-muted mb-1.5">
                Ваше имя <span className="text-semantic-error">*</span>
              </label>
              <input
                {...register("name")}
                type="text"
                id="name"
                className={cn(
                  "w-full px-4 py-3 rounded-md border transition-colors bg-surface-2 text-ink placeholder:text-text-subtle",
                  errors.name
                    ? "border-semantic-error focus:border-semantic-error"
                    : "border-border-hairline focus:border-accent",
                  "focus:outline-none"
                )}
                placeholder="Иван Иванов"
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? "name-error" : undefined}
              />
              {errors.name && (
                <p id="name-error" className="mt-1 text-sm text-semantic-error" role="alert">
                  {errors.name.message}
                </p>
              )}
            </div>

            {/* Phone */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-text-muted mb-1.5">
                Телефон <span className="text-semantic-error">*</span>
              </label>
              <input
                {...register("phone")}
                type="tel"
                id="phone"
                className={cn(
                  "w-full px-4 py-3 rounded-md border transition-colors bg-surface-2 text-ink placeholder:text-text-subtle",
                  errors.phone
                    ? "border-semantic-error focus:border-semantic-error"
                    : "border-border-hairline focus:border-accent",
                  "focus:outline-none"
                )}
                placeholder="+7 999 123-45-67"
                aria-invalid={!!errors.phone}
                aria-describedby={errors.phone ? "phone-error" : undefined}
              />
              {errors.phone && (
                <p id="phone-error" className="mt-1 text-sm text-semantic-error" role="alert">
                  {errors.phone.message}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-text-muted mb-1.5">
                Email <span className="text-semantic-error">*</span>
              </label>
              <input
                {...register("email")}
                type="email"
                id="email"
                className={cn(
                  "w-full px-4 py-3 rounded-md border transition-colors bg-surface-2 text-ink placeholder:text-text-subtle",
                  errors.email
                    ? "border-semantic-error focus:border-semantic-error"
                    : "border-border-hairline focus:border-accent",
                  "focus:outline-none"
                )}
                placeholder="ivan@example.com"
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : undefined}
              />
              {errors.email && (
                <p id="email-error" className="mt-1 text-sm text-semantic-error" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Clinic Name */}
            <div>
              <label htmlFor="clinicName" className="block text-sm font-medium text-text-muted mb-1.5">
                Название клиники <span className="text-semantic-error">*</span>
              </label>
              <input
                {...register("clinicName")}
                type="text"
                id="clinicName"
                className={cn(
                  "w-full px-4 py-3 rounded-md border transition-colors bg-surface-2 text-ink placeholder:text-text-subtle",
                  errors.clinicName
                    ? "border-semantic-error focus:border-semantic-error"
                    : "border-border-hairline focus:border-accent",
                  "focus:outline-none"
                )}
                placeholder="Медицинский центр «Здоровье»"
                aria-invalid={!!errors.clinicName}
                aria-describedby={errors.clinicName ? "clinicName-error" : undefined}
              />
              {errors.clinicName && (
                <p id="clinicName-error" className="mt-1 text-sm text-semantic-error" role="alert">
                  {errors.clinicName.message}
                </p>
              )}
            </div>

            {/* Specialty */}
            <div>
              <label htmlFor="specialty" className="block text-sm font-medium text-text-muted mb-1.5">
                Специализация <span className="text-semantic-error">*</span>
              </label>
              <select
                {...register("specialty")}
                id="specialty"
                className={cn(
                  "w-full px-4 py-3 rounded-md border transition-colors bg-surface-2 text-ink placeholder:text-text-subtle",
                  errors.specialty
                    ? "border-semantic-error focus:border-semantic-error"
                    : "border-border-hairline focus:border-accent",
                  "focus:outline-none"
                )}
                aria-invalid={!!errors.specialty}
                aria-describedby={errors.specialty ? "specialty-error" : undefined}
              >
                {specialties.map((spec) => (
                  <option key={spec.value} value={spec.value}>
                    {spec.label}
                  </option>
                ))}
              </select>
              {errors.specialty && (
                <p id="specialty-error" className="mt-1 text-sm text-semantic-error" role="alert">
                  {errors.specialty.message}
                </p>
              )}
            </div>

            {/* Message */}
            <div>
              <label htmlFor="message" className="block text-sm font-medium text-text-muted mb-1.5">
                Сообщение (опционально)
              </label>
              <textarea
                {...register("message")}
                id="message"
                rows={4}
                className={cn(
                  "w-full px-4 py-3 rounded-md border transition-colors bg-surface-2 text-ink placeholder:text-text-subtle resize-none",
                  errors.message
                    ? "border-semantic-error focus:border-semantic-error"
                    : "border-border-hairline focus:border-accent",
                  "focus:outline-none"
                )}
                placeholder="Расскажите о вашей клинике и целях..."
                aria-invalid={!!errors.message}
                aria-describedby={errors.message ? "message-error" : undefined}
              />
              {errors.message && (
                <p id="message-error" className="mt-1 text-sm text-semantic-error" role="alert">
                  {errors.message.message}
                </p>
              )}
            </div>

            {/* FZ-152 Consent */}
            <div>
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  {...register("fz152Consent")}
                  type="checkbox"
                  className="mt-1 w-5 h-5 rounded border-2 border-border-hairline text-accent focus:ring-2 focus:ring-accent"
                  aria-invalid={!!errors.fz152Consent}
                  aria-describedby={errors.fz152Consent ? "consent-error" : undefined}
                />
                <span className="text-sm text-text-muted">
                  Я согласен на обработку персональных данных в соответствии с{" "}
                  <a
                    href="/privacy-policy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:text-accent underline"
                  >
                    ФЗ-152
                  </a>{" "}
                  <span className="text-semantic-error">*</span>
                </span>
              </label>
              {errors.fz152Consent && (
                <p id="consent-error" className="mt-1 text-sm text-semantic-error" role="alert">
                  {errors.fz152Consent.message}
                </p>
              )}
            </div>

            {/* Error Message */}
            {submissionState === "error" && errorMessage && (
              <div className="bg-surface-3 border-2 border-semantic-error rounded-md p-4" role="alert">
                <p className="text-sm text-semantic-error">{errorMessage}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submissionState === "submitting"}
              className={cn(
                "w-full btn-primary text-lg py-4",
                submissionState === "submitting" && "opacity-50 cursor-not-allowed"
              )}
            >
              {submissionState === "submitting" ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Отправка...
                </span>
              ) : (
                "Получить консультацию"
              )}
            </button>

            {/* reCAPTCHA Notice */}
            <p className="text-xs text-text-subtle text-center">
              Этот сайт защищён reCAPTCHA. Применяются{" "}
              <a
                href="https://policies.google.com/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-text-muted"
              >
                Политика конфиденциальности
              </a>{" "}
              и{" "}
              <a
                href="https://policies.google.com/terms"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-text-muted"
              >
                Условия использования
              </a>{" "}
              Google.
            </p>
          </motion.form>
        )}
      </div>
    </section>
  );
}
