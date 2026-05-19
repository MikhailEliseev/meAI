import { NextRequest, NextResponse } from "next/server";
import { createYuKassaClient } from "@/lib/payment/yukassa-client";
import { generateInvoice, type InvoiceGenerateRequest } from "@/lib/payment/invoice-generator";
import type { PaymentRequest } from "@/lib/payment/yukassa-client";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * POST /api/payment/create
 *
 * Создание платежа и счёта через ЮKassa API.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();

    // Validate request
    if (!body.customer || !body.items || body.items.length === 0) {
      return NextResponse.json(
        { success: false, error: "Missing required fields" },
        { status: 400 }
      );
    }

    // Generate invoice
    const invoiceRequest: InvoiceGenerateRequest = {
      customer: body.customer,
      items: body.items,
      dueInDays: body.dueInDays || 7,
      notes: body.notes,
    };

    const invoice = await generateInvoice(invoiceRequest);

    // Create payment
    const client = createYuKassaClient();
    const paymentRequest: PaymentRequest = {
      amount: {
        value: invoice.total.toFixed(2),
        currency: "RUB",
      },
      description: `Счёт ${invoice.number} - AIM Agency`,
      metadata: {
        invoice_id: invoice.id,
        invoice_number: invoice.number,
        customer_email: invoice.customer.email,
        customer_name: invoice.customer.name,
        clinic_name: invoice.customer.name,
        plan: body.plan || "starter",
        trigger_onboarding: body.triggerOnboarding ? "true" : "false",
      },
      capture: true, // Auto-capture
      confirmation: {
        type: "redirect",
        return_url: `${process.env.NEXT_PUBLIC_BASE_URL}/billing/payment-success`,
      },
      receipt: {
        customer: {
          email: invoice.customer.email,
          phone: invoice.customer.phone,
        },
        items: invoice.items.map((item) => ({
          description: item.description,
          quantity: item.quantity.toString(),
          amount: {
            value: item.total.toFixed(2),
            currency: "RUB",
          },
          vat_code: item.vatRate === 0 ? 1 : item.vatRate === 10 ? 3 : 4,
        })),
      },
    };

    const payment = await client.createPayment(paymentRequest);

    return NextResponse.json({
      success: true,
      invoice,
      payment: {
        id: payment.id,
        status: payment.status,
        confirmation_url: payment.confirmation?.confirmation_url,
      },
    });
  } catch (error) {
    console.error("[Payment Create] Error:", error);
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
 * GET /api/payment/create
 *
 * Get payment creation form data (pricing plans)
 */
export async function GET(): Promise<NextResponse> {
  // Pricing plans
  const plans = [
    {
      id: "starter",
      name: "Стартовый",
      price: 150000, // 150K RUB/month
      features: [
        "AI-анализ конкурентов",
        "Настройка Яндекс.Директ",
        "SEO-оптимизация сайта",
        "Email-маркетинг",
        "Еженедельные отчёты",
      ],
      recommended: false,
    },
    {
      id: "professional",
      name: "Профессиональный",
      price: 250000, // 250K RUB/month
      features: [
        "Всё из Стартового",
        "Контент-маркетинг (8 статей/месяц)",
        "SMM (VK, Instagram)",
        "Ретаргетинг",
        "Персональный менеджер",
        "Ежедневные отчёты",
      ],
      recommended: true,
    },
    {
      id: "enterprise",
      name: "Корпоративный",
      price: 500000, // 500K RUB/month
      features: [
        "Всё из Профессионального",
        "Контент-маркетинг (20 статей/месяц)",
        "Видео-маркетинг",
        "PR и медиа",
        "Выделенная команда",
        "24/7 поддержка",
        "Гарантия результата",
      ],
      recommended: false,
    },
  ];

  return NextResponse.json({
    success: true,
    plans,
  });
}
