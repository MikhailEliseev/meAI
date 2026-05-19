/**
 * ЮKassa Payment Client
 *
 * Полноценная интеграция с ЮKassa API v3.
 * Документация: https://yookassa.ru/developers/api
 *
 * Поддерживаемые методы оплаты:
 * - bank_card — банковские карты (Мир, Visa, Mastercard)
 * - yoo_money — ЮMoney (бывшие Яндекс.Деньги)
 * - sberbank — Сбербанк Онлайн
 * - qiwi — QIWI Кошелёк
 */

// Payment types
export type PaymentStatus =
  | "pending"
  | "waiting_for_capture"
  | "succeeded"
  | "canceled";

export type PaymentMethod = "bank_card" | "yoo_money" | "sberbank" | "qiwi";

export interface PaymentAmount {
  value: string; // "100.00"
  currency: "RUB";
}

export interface PaymentRequest {
  amount: PaymentAmount;
  description: string;
  metadata?: Record<string, string>;
  capture?: boolean; // Auto-capture payment
  confirmation?: {
    type: "redirect";
    return_url: string;
  };
  receipt?: PaymentReceipt;
}

export interface PaymentReceipt {
  customer: {
    email: string;
    phone?: string;
  };
  items: Array<{
    description: string;
    quantity: string;
    amount: PaymentAmount;
    vat_code: number; // 1 = no VAT, 2 = 0%, 3 = 10%, 4 = 20%
  }>;
}

export interface Payment {
  id: string;
  status: PaymentStatus;
  amount: PaymentAmount;
  description: string;
  metadata?: Record<string, string>;
  created_at: string;
  captured_at?: string;
  confirmation?: {
    type: "redirect";
    confirmation_url: string;
  };
  receipt_registration?: "pending" | "succeeded" | "canceled";
  paid: boolean;
  refundable: boolean;
  test: boolean;
}

export interface RefundRequest {
  payment_id: string;
  amount: PaymentAmount;
  description?: string;
}

export interface Refund {
  id: string;
  payment_id: string;
  status: "pending" | "succeeded" | "canceled";
  amount: PaymentAmount;
  description?: string;
  created_at: string;
}

export interface RecurringPaymentRequest {
  amount: PaymentAmount;
  description: string;
  payment_method_id: string;
  metadata?: Record<string, string>;
  receipt?: PaymentReceipt;
}

const YUKASSA_API_URL = "https://api.yookassa.ru/v3";

export class YuKassaClient {
  private shopId: string;
  private secretKey: string;
  private testMode: boolean;

  constructor(shopId: string, secretKey: string, testMode = true) {
    this.shopId = shopId;
    this.secretKey = secretKey;
    this.testMode = testMode;
  }

  private get authHeader(): string {
    const credentials = Buffer.from(`${this.shopId}:${this.secretKey}`).toString("base64");
    return `Basic ${credentials}`;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    idempotencyKey?: string
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Authorization": this.authHeader,
      "Content-Type": "application/json",
    };

    if (idempotencyKey) {
      headers["Idempotence-Key"] = idempotencyKey;
    }

    const response = await fetch(`${YUKASSA_API_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(
        `ЮKassa API error ${response.status}: ${errorBody}`
      );
    }

    return response.json() as Promise<T>;
  }

  /**
   * Создать платёж
   *
   * POST /payments
   * Idempotence-Key — RFC 4122 UUID для защиты от повторных списаний
   */
  async createPayment(request: PaymentRequest): Promise<Payment> {
    const idempotencyKey = crypto.randomUUID();

    const payment = await this.request<Payment>("POST", "/payments", {
      amount: request.amount,
      description: request.description,
      metadata: request.metadata,
      capture: request.capture ?? true,
      confirmation: request.confirmation,
      receipt: request.receipt,
    }, idempotencyKey);

    return payment;
  }

  /**
   * Получить информацию о платеже
   */
  async getPayment(paymentId: string): Promise<Payment> {
    return this.request<Payment>("GET", `/payments/${paymentId}`);
  }

  /**
   * Подтвердить платёж (capture)
   *
   * Для двухстадийных платежей (capture: false при создании)
   */
  async capturePayment(
    paymentId: string,
    amount?: PaymentAmount
  ): Promise<Payment> {
    const idempotencyKey = crypto.randomUUID();

    return this.request<Payment>("POST", `/payments/${paymentId}/capture`, {
      amount,
    }, idempotencyKey);
  }

  /**
   * Отменить платёж
   */
  async cancelPayment(paymentId: string): Promise<Payment> {
    const idempotencyKey = crypto.randomUUID();

    return this.request<Payment>("POST", `/payments/${paymentId}/cancel`, {}, idempotencyKey);
  }

  /**
   * Создать возврат
   */
  async createRefund(request: RefundRequest): Promise<Refund> {
    const idempotencyKey = crypto.randomUUID();

    return this.request<Refund>("POST", "/refunds", {
      payment_id: request.payment_id,
      amount: request.amount,
      description: request.description,
    }, idempotencyKey);
  }

  /**
   * Получить информацию о возврате
   */
  async getRefund(refundId: string): Promise<Refund> {
    return this.request<Refund>("GET", `/refunds/${refundId}`);
  }

  /**
   * Создать рекуррентный платёж
   *
   * Использует сохранённый payment_method_id для списания без участия плательщика
   */
  async createRecurringPayment(
    request: RecurringPaymentRequest
  ): Promise<Payment> {
    const idempotencyKey = crypto.randomUUID();

    return this.request<Payment>("POST", "/payments", {
      amount: request.amount,
      description: request.description,
      payment_method_id: request.payment_method_id,
      metadata: {
        ...request.metadata,
        recurring: "true",
      },
      capture: true,
      receipt: request.receipt,
    }, idempotencyKey);
  }

  /**
   * Проверить подпись вебхука
   *
   * ЮKassa подписывает тело запроса HMAC-SHA256 с использованием secretKey.
   * Сигнатура передаётся в заголовке X-YooKassa-Signature.
   */
  verifyWebhookSignature(body: string, signature: string): boolean {
    if (!signature) {
      console.error("[YuKassa] Missing webhook signature");
      return false;
    }

    const crypto = require("crypto");
    const hmac = crypto.createHmac("sha256", this.secretKey);
    hmac.update(body);
    const expectedSignature = hmac.digest("hex");

    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  }
}

/**
 * Создать экземпляр клиента ЮKassa
 */
export function createYuKassaClient(): YuKassaClient {
  const shopId = process.env.YUKASSA_SHOP_ID || "";
  const secretKey = process.env.YUKASSA_SECRET_KEY || "";
  const testMode = process.env.NODE_ENV !== "production";

  if (!shopId || !secretKey) {
    console.warn(
      "[YuKassa] YUKASSA_SHOP_ID or YUKASSA_SECRET_KEY not set — payments will fail. Set them in .env"
    );
  }

  return new YuKassaClient(shopId, secretKey, testMode);
}

/**
 * Форматировать сумму для ЮKassa (строка с 2 знаками после запятой)
 */
export function formatAmount(amount: number): string {
  return amount.toFixed(2);
}

/**
 * Распарсить сумму из ЮKassa (строка → число)
 */
export function parseAmount(value: string): number {
  return parseFloat(value);
}
