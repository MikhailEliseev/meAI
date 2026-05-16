import { NextRequest, NextResponse } from "next/server";
import { contactFormSchema, decryptField } from "@/lib/validation";
import { z } from "zod";

// reCAPTCHA verification
async function verifyRecaptcha(token: string): Promise<boolean> {
  const secretKey = process.env.RECAPTCHA_SECRET_KEY;
  if (!secretKey) {
    console.error("RECAPTCHA_SECRET_KEY not configured");
    return false;
  }

  try {
    const response = await fetch("https://www.google.com/recaptcha/api/siteverify", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `secret=${secretKey}&response=${token}`,
    });

    const data = await response.json();
    return data.success && data.score >= 0.5; // Minimum score threshold
  } catch (error) {
    console.error("reCAPTCHA verification error:", error);
    return false;
  }
}

// Send email via SendGrid (Phase 9 integration)
async function sendEmail(data: z.infer<typeof contactFormSchema>): Promise<void> {
  const sendgridApiKey = process.env.SENDGRID_API_KEY;
  if (!sendgridApiKey) {
    throw new Error("SENDGRID_API_KEY not configured");
  }

  const emailBody = `
Новая заявка с сайта iamaim.ru

Имя: ${data.name}
Телефон: ${data.phone}
Email: ${data.email}
Клиника: ${data.clinicName}
Специализация: ${data.specialty}
Сообщение: ${data.message || "Не указано"}

---
Согласие на обработку данных (ФЗ-152): Да
Дата: ${new Date().toLocaleString("ru-RU", { timeZone: "Europe/Moscow" })}
  `.trim();

  try {
    const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sendgridApiKey}`,
      },
      body: JSON.stringify({
        personalizations: [
          {
            to: [{ email: process.env.CONTACT_EMAIL || "info@iamaim.ru" }],
            subject: `Новая заявка: ${data.clinicName} (${data.specialty})`,
          },
        ],
        from: {
          email: process.env.FROM_EMAIL || "noreply@iamaim.ru",
          name: "AIM Agency",
        },
        content: [
          {
            type: "text/plain",
            value: emailBody,
          },
        ],
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`SendGrid error: ${error}`);
    }
  } catch (error) {
    console.error("Email sending error:", error);
    throw error;
  }
}

// Save to database (optional - for lead tracking)
async function saveToDatabase(data: z.infer<typeof contactFormSchema>): Promise<void> {
  // TODO: Implement database save when Phase 7.5 (Linear) is integrated
  // For now, just log
  console.log("Lead saved:", {
    name: data.name,
    clinic: data.clinicName,
    specialty: data.specialty,
    timestamp: new Date().toISOString(),
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Decrypt sensitive fields
    const encryptionKey = process.env.ENCRYPTION_KEY || "default-key";
    const decryptedData = {
      ...body,
      phone: decryptField(body.phone, encryptionKey),
      email: decryptField(body.email, encryptionKey),
    };

    // Validate data
    const validatedData = contactFormSchema.parse(decryptedData);

    // Verify reCAPTCHA
    const isRecaptchaValid = await verifyRecaptcha(validatedData.recaptchaToken);
    if (!isRecaptchaValid) {
      return NextResponse.json(
        { message: "Ошибка проверки reCAPTCHA. Попробуйте обновить страницу." },
        { status: 400 }
      );
    }

    // Send email
    await sendEmail(validatedData);

    // Save to database (optional)
    await saveToDatabase(validatedData);

    // Track analytics
    // TODO: Integrate with Yandex.Metrika server-side API

    return NextResponse.json(
      { message: "Заявка успешно отправлена" },
      { status: 200 }
    );
  } catch (error) {
    console.error("Contact form API error:", error);

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { message: "Ошибка валидации данных", errors: error.errors },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { message: "Произошла ошибка. Попробуйте позже." },
      { status: 500 }
    );
  }
}
