import {
  YuKassaClient,
  formatAmount,
  parseAmount,
} from "@/lib/payment/yukassa-client";
import type {
  PaymentRequest,
  RefundRequest,
  RecurringPaymentRequest,
} from "@/lib/payment/yukassa-client";

describe("YuKassaClient", () => {
  let client: YuKassaClient;

  beforeEach(() => {
    client = new YuKassaClient("test-shop-id", "test-secret-key", true);
  });

  describe("createPayment", () => {
    it("should create payment with confirmation URL", async () => {
      const request: PaymentRequest = {
        amount: { value: "150000.00", currency: "RUB" },
        description: "Test payment",
        capture: true,
        confirmation: {
          type: "redirect",
          return_url: "https://example.com/success",
        },
      };

      const payment = await client.createPayment(request);

      expect(payment.id).toMatch(/^STUB-/);
      expect(payment.status).toBe("pending");
      expect(payment.amount).toEqual(request.amount);
      expect(payment.description).toBe(request.description);
      expect(payment.confirmation?.confirmation_url).toMatch(
        /^https:\/\/yookassa\.ru\/checkout\//
      );
      expect(payment.paid).toBe(false);
      expect(payment.test).toBe(true);
    });

    it("should create payment with metadata", async () => {
      const request: PaymentRequest = {
        amount: { value: "150000.00", currency: "RUB" },
        description: "Test payment",
        metadata: {
          invoice_id: "INV-001",
          customer_email: "test@example.com",
        },
      };

      const payment = await client.createPayment(request);

      expect(payment.metadata).toEqual(request.metadata);
    });

    it("should create payment with receipt", async () => {
      const request: PaymentRequest = {
        amount: { value: "150000.00", currency: "RUB" },
        description: "Test payment",
        receipt: {
          customer: {
            email: "test@example.com",
            phone: "+79991234567",
          },
          items: [
            {
              description: "Service",
              quantity: "1",
              amount: { value: "150000.00", currency: "RUB" },
              vat_code: 4,
            },
          ],
        },
      };

      const payment = await client.createPayment(request);

      expect(payment.receipt_registration).toBe("pending");
    });
  });

  describe("getPayment", () => {
    it("should get payment by ID", async () => {
      const payment = await client.getPayment("test-payment-id");

      expect(payment.id).toBe("test-payment-id");
      expect(payment.status).toBe("succeeded");
      expect(payment.paid).toBe(true);
      expect(payment.refundable).toBe(true);
    });
  });

  describe("capturePayment", () => {
    it("should capture payment", async () => {
      const payment = await client.capturePayment("test-payment-id");

      expect(payment.status).toBe("succeeded");
      expect(payment.paid).toBe(true);
      expect(payment.captured_at).toBeDefined();
    });

    it("should capture payment with custom amount", async () => {
      const amount = { value: "100000.00", currency: "RUB" as const };
      const payment = await client.capturePayment("test-payment-id", amount);

      expect(payment.amount).toEqual(amount);
    });
  });

  describe("cancelPayment", () => {
    it("should cancel payment", async () => {
      const payment = await client.cancelPayment("test-payment-id");

      expect(payment.status).toBe("canceled");
      expect(payment.paid).toBe(false);
      expect(payment.refundable).toBe(false);
    });
  });

  describe("createRefund", () => {
    it("should create refund", async () => {
      const request: RefundRequest = {
        payment_id: "test-payment-id",
        amount: { value: "150000.00", currency: "RUB" },
        description: "Test refund",
      };

      const refund = await client.createRefund(request);

      expect(refund.id).toMatch(/^REFUND-/);
      expect(refund.payment_id).toBe(request.payment_id);
      expect(refund.status).toBe("succeeded");
      expect(refund.amount).toEqual(request.amount);
      expect(refund.description).toBe(request.description);
    });
  });

  describe("getRefund", () => {
    it("should get refund by ID", async () => {
      const refund = await client.getRefund("test-refund-id");

      expect(refund.id).toBe("test-refund-id");
      expect(refund.status).toBe("succeeded");
      expect(refund.payment_id).toBeDefined();
    });
  });

  describe("createRecurringPayment", () => {
    it("should create recurring payment", async () => {
      const request: RecurringPaymentRequest = {
        amount: { value: "150000.00", currency: "RUB" },
        description: "Monthly subscription",
        payment_method_id: "test-method-id",
        metadata: {
          subscription_id: "SUB-001",
        },
      };

      const payment = await client.createRecurringPayment(request);

      expect(payment.id).toMatch(/^RECURRING-/);
      expect(payment.status).toBe("succeeded");
      expect(payment.paid).toBe(true);
      expect(payment.metadata?.recurring).toBe("true");
      expect(payment.metadata?.payment_method_id).toBe(
        request.payment_method_id
      );
    });
  });

  describe("verifyWebhookSignature", () => {
    it("should verify webhook signature", () => {
      const body = JSON.stringify({ event: "payment.succeeded" });
      const signature = "test-signature";

      const isValid = client.verifyWebhookSignature(body, signature);

      // STUB always returns true
      expect(isValid).toBe(true);
    });
  });
});

describe("formatAmount", () => {
  it("should format amount with 2 decimals", () => {
    expect(formatAmount(150000)).toBe("150000.00");
    expect(formatAmount(150000.5)).toBe("150000.50");
    expect(formatAmount(150000.123)).toBe("150000.12");
  });
});

describe("parseAmount", () => {
  it("should parse amount string to number", () => {
    expect(parseAmount("150000.00")).toBe(150000);
    expect(parseAmount("150000.50")).toBe(150000.5);
    expect(parseAmount("0.01")).toBe(0.01);
  });
});
