/**
 * Payment API Client
 *
 * Integrates with AIM Payment Service (Task 3.1).
 * Connects frontend to backend payment processing.
 *
 * Part of: Phase 11 Sprint 3 - Task 3.2
 */

// Payment types (matching backend schemas)
export type PaymentStatus = "pending" | "processing" | "completed" | "failed" | "refunded";
export type PaymentMethod = "card" | "bank_transfer" | "yookassa";

export interface PaymentRequest {
  amount: number;
  currency: string;
  payment_method: PaymentMethod;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  card_number?: string;
  card_expiry?: string;
  card_cvv?: string;
  lead_id?: string;
  metadata?: Record<string, any>;
}

export interface PaymentResponse {
  payment_id: string;
  status: PaymentStatus;
  amount: number;
  currency: string;
  external_transaction_id?: string;
  created_at: string;
  message: string;
}

export interface PaymentStatusResponse {
  payment_id: string;
  status: PaymentStatus;
  amount: number;
  currency: string;
  payment_method: string;
  card_last4?: string;
  card_brand?: string;
  external_transaction_id?: string;
  error_code?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface RefundRequest {
  payment_id: string;
  amount?: number;
  reason: string;
}

export interface RefundResponse {
  payment_id: string;
  refunded_amount: number;
  status: PaymentStatus;
  refunded_at: string;
  message: string;
}

/**
 * Payment API Client
 */
export class PaymentAPI {
  private baseUrl: string;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  /**
   * Create a new payment
   */
  async createPayment(request: PaymentRequest): Promise<PaymentResponse> {
    const response = await fetch(`${this.baseUrl}/payments/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Payment creation failed");
    }

    return response.json();
  }

  /**
   * Get payment status
   */
  async getPaymentStatus(paymentId: string): Promise<PaymentStatusResponse> {
    const response = await fetch(`${this.baseUrl}/payments/${paymentId}/status`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get payment status");
    }

    return response.json();
  }

  /**
   * Refund a payment
   */
  async refundPayment(request: RefundRequest): Promise<RefundResponse> {
    const response = await fetch(`${this.baseUrl}/payments/${request.payment_id}/refund`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount: request.amount,
        reason: request.reason,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Refund failed");
    }

    return response.json();
  }
}

// Singleton instance
export const paymentAPI = new PaymentAPI();
