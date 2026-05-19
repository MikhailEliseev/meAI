import { NextRequest, NextResponse } from "next/server";
import { createYuKassaClient } from "@/lib/payment/yukassa-client";
import { markInvoiceAsPaid } from "@/lib/payment/invoice-generator";
import { sendTemplateEmail } from "@/lib/sendgrid-templates";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * POST /api/webhooks/yukassa
 *
 * Обработчик вебхуков ЮKassa.
 *
 * События:
 * - payment.succeeded — платёж успешно завершён
 * - payment.canceled — платёж отменён
 * - refund.succeeded — возврат успешно выполнен
 *
 * Безопасность: HMAC-SHA256 верификация подписи в заголовке X-YooKassa-Signature.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.text();
    const signature = request.headers.get("x-yookassa-signature") || "";

    const client = createYuKassaClient();
    const isValid = client.verifyWebhookSignature(body, signature);

    if (!isValid) {
      console.error("[YuKassa Webhook] Invalid signature");
      return NextResponse.json(
        { success: false, error: "Invalid signature" },
        { status: 401 }
      );
    }

    const event = JSON.parse(body);
    console.log("[YuKassa Webhook] Received event:", event.event);

    switch (event.event) {
      case "payment.succeeded":
        await handlePaymentSucceeded(event.object);
        break;

      case "payment.canceled":
        await handlePaymentCanceled(event.object);
        break;

      case "refund.succeeded":
        await handleRefundSucceeded(event.object);
        break;

      default:
        console.log("[YuKassa Webhook] Unknown event type:", event.event);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("[YuKassa Webhook] Error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}

/**
 * Обработка успешного платежа
 */
async function handlePaymentSucceeded(payment: any): Promise<void> {
  console.log("[YuKassa Webhook] Payment succeeded:", payment.id);

  const invoiceId = payment.metadata?.invoice_id;
  const customerEmail = payment.metadata?.customer_email;
  const invoiceNumber = payment.metadata?.invoice_number;

  if (!invoiceId) {
    console.error("[YuKassa Webhook] Missing invoice_id in metadata");
    return;
  }

  // Отметить счёт как оплаченный
  await markInvoiceAsPaid(invoiceId, payment.payment_method?.type || "bank_card");

  // Отправить подтверждение оплаты клиенту
  if (customerEmail) {
    try {
      await sendTemplateEmail({
        to: customerEmail,
        templateId: "d-payment-confirmation",
        dynamicTemplateData: {
          name: payment.metadata?.customer_name || "Клиент",
          clinicName: payment.metadata?.clinic_name || "",
          amount: payment.amount?.value || "0",
          currency: payment.amount?.currency || "RUB",
          paymentId: payment.id,
          invoiceNumber: invoiceNumber || "",
          date: new Date().toLocaleDateString("ru-RU"),
        },
      });
      console.log("[YuKassa Webhook] Payment confirmation sent to:", customerEmail);
    } catch (emailError) {
      console.error("[YuKassa Webhook] Failed to send confirmation email:", emailError);
    }
  }

  // Триггер онбординга: если платёж содержит признак нового клиента
  if (payment.metadata?.trigger_onboarding === "true") {
    console.log("[YuKassa Webhook] Onboarding trigger for:", customerEmail);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/api/onboarding/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: customerEmail,
          paymentId: payment.id,
          invoiceId,
          plan: payment.metadata?.plan || "starter",
        }),
      });
    } catch (onboardingError) {
      console.error("[YuKassa Webhook] Failed to trigger onboarding:", onboardingError);
    }
  }
}

/**
 * Обработка отменённого платежа
 */
async function handlePaymentCanceled(payment: any): Promise<void> {
  console.log("[YuKassa Webhook] Payment canceled:", payment.id);

  const invoiceId = payment.metadata?.invoice_id;
  const customerEmail = payment.metadata?.customer_email;

  if (!invoiceId) {
    console.error("[YuKassa Webhook] Missing invoice_id in metadata");
    return;
  }

  // Уведомить клиента об отмене платежа
  if (customerEmail) {
    try {
      await sendTemplateEmail({
        to: customerEmail,
        templateId: "d-payment-failed",
        dynamicTemplateData: {
          name: payment.metadata?.customer_name || "Клиент",
          amount: payment.amount?.value || "0",
          currency: payment.amount?.currency || "RUB",
          paymentId: payment.id,
          reason: payment.cancellation_details?.reason || "Отменён плательщиком",
          date: new Date().toLocaleDateString("ru-RU"),
        },
      });
      console.log("[YuKassa Webhook] Payment failure notification sent to:", customerEmail);
    } catch (emailError) {
      console.error("[YuKassa Webhook] Failed to send failure email:", emailError);
    }
  }
}

/**
 * Обработка успешного возврата
 */
async function handleRefundSucceeded(refund: any): Promise<void> {
  console.log("[YuKassa Webhook] Refund succeeded:", refund.id);

  const paymentId = refund.payment_id;

  // Уведомить клиента о возврате
  try {
    // Получить информацию о платеже для email клиента
    const client = createYuKassaClient();
    const payment = await client.getPayment(paymentId);
    const customerEmail = payment.metadata?.customer_email;

    if (customerEmail) {
      await sendTemplateEmail({
        to: customerEmail,
        templateId: "d-refund-confirmation",
        dynamicTemplateData: {
          name: payment.metadata?.customer_name || "Клиент",
          amount: refund.amount?.value || "0",
          currency: refund.amount?.currency || "RUB",
          refundId: refund.id,
          paymentId,
          date: new Date().toLocaleDateString("ru-RU"),
        },
      });
      console.log("[YuKassa Webhook] Refund confirmation sent to:", customerEmail);
    }
  } catch (emailError) {
    console.error("[YuKassa Webhook] Failed to send refund email:", emailError);
  }
}

/**
 * GET /api/webhooks/yukassa
 *
 * Health check для мониторинга
 */
export async function GET(): Promise<NextResponse> {
  const configured = !!(process.env.YUKASSA_SHOP_ID && process.env.YUKASSA_SECRET_KEY);

  return NextResponse.json({
    success: true,
    message: "ЮKassa webhook endpoint is active",
    configured,
    timestamp: new Date().toISOString(),
  });
}
