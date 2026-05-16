import { NextRequest, NextResponse } from "next/server";
import { createYuKassaClient } from "@/lib/payment/yukassa-client";
import { markInvoiceAsPaid } from "@/lib/payment/invoice-generator";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * POST /api/webhooks/yukassa
 *
 * Handle ЮKassa webhook notifications
 *
 * STUB: Mock webhook handler for development
 * Real implementation in Phase 12
 *
 * Webhook events:
 * - payment.succeeded - Payment completed
 * - payment.canceled - Payment canceled
 * - refund.succeeded - Refund completed
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.text();
    const signature = request.headers.get("x-yookassa-signature") || "";

    // Verify webhook signature
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

    // Handle different event types
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
 * Handle payment.succeeded event
 */
async function handlePaymentSucceeded(payment: any): Promise<void> {
  console.log("[YuKassa Webhook] Payment succeeded:", payment.id);

  // Extract metadata
  const invoiceId = payment.metadata?.invoice_id;
  const customerEmail = payment.metadata?.customer_email;

  if (!invoiceId) {
    console.error("[YuKassa Webhook] Missing invoice_id in metadata");
    return;
  }

  // Mark invoice as paid
  await markInvoiceAsPaid(invoiceId, "bank_card");

  // TODO: Send payment confirmation email (Phase 2.3 email sequences)
  console.log("[YuKassa Webhook] TODO: Send payment confirmation email");

  // TODO: Update Linear issue status (Phase 7.5)
  console.log("[YuKassa Webhook] TODO: Update Linear issue status");

  // TODO: Trigger onboarding workflow (Phase 3.4)
  console.log("[YuKassa Webhook] TODO: Trigger onboarding workflow");

  console.log("[YuKassa Webhook] Payment processed successfully");
}

/**
 * Handle payment.canceled event
 */
async function handlePaymentCanceled(payment: any): Promise<void> {
  console.log("[YuKassa Webhook] Payment canceled:", payment.id);

  const invoiceId = payment.metadata?.invoice_id;
  const customerEmail = payment.metadata?.customer_email;

  // TODO: Update invoice status to canceled
  console.log("[YuKassa Webhook] TODO: Update invoice status");

  // TODO: Send payment failed email
  console.log("[YuKassa Webhook] TODO: Send payment failed email");

  // TODO: Update Linear issue with payment failure
  console.log("[YuKassa Webhook] TODO: Update Linear issue");
}

/**
 * Handle refund.succeeded event
 */
async function handleRefundSucceeded(refund: any): Promise<void> {
  console.log("[YuKassa Webhook] Refund succeeded:", refund.id);

  const paymentId = refund.payment_id;

  // TODO: Update invoice status to refunded
  console.log("[YuKassa Webhook] TODO: Update invoice status");

  // TODO: Send refund confirmation email
  console.log("[YuKassa Webhook] TODO: Send refund confirmation email");

  // TODO: Update Linear issue with refund info
  console.log("[YuKassa Webhook] TODO: Update Linear issue");
}

/**
 * GET /api/webhooks/yukassa
 *
 * Health check endpoint
 */
export async function GET(): Promise<NextResponse> {
  return NextResponse.json({
    success: true,
    message: "ЮKassa webhook endpoint is active (STUB)",
    timestamp: new Date().toISOString(),
  });
}
