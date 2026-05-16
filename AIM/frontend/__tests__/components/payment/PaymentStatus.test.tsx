/**
 * PaymentStatus Component Tests
 *
 * Part of: Phase 11 Sprint 3 - Task 3.2
 */

import { render, screen, waitFor } from "@testing-library/react";
import { useRouter } from "next/router";
import PaymentStatus from "@/components/payment/PaymentStatus";
import { paymentAPI } from "@/lib/api/payment";

// Mock Next.js router
jest.mock("next/router", () => ({
  useRouter: jest.fn(),
}));

// Mock payment API
jest.mock("@/lib/api/payment", () => ({
  paymentAPI: {
    getPaymentStatus: jest.fn(),
  },
}));

describe("PaymentStatus", () => {
  const mockPush = jest.fn();
  const mockRouter = {
    push: mockPush,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
  });

  describe("Loading State", () => {
    it("should show loading spinner while fetching status", () => {
      (paymentAPI.getPaymentStatus as jest.Mock).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<PaymentStatus paymentId="pay_123" />);

      expect(screen.getByRole("status", { hidden: true })).toBeInTheDocument();
    });
  });

  describe("Success State", () => {
    const successResponse = {
      payment_id: "pay_20260517123456_abc123",
      status: "completed" as const,
      amount: 5000,
      currency: "RUB",
      payment_method: "card",
      card_last4: "1111",
      card_brand: "visa",
      external_transaction_id: "STUB-123456",
      created_at: "2026-05-17T12:34:56Z",
      completed_at: "2026-05-17T12:35:00Z",
    };

    beforeEach(() => {
      (paymentAPI.getPaymentStatus as jest.Mock).mockResolvedValue(successResponse);
    });

    it("should display success message", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("Платёж успешен")).toBeInTheDocument();
      });
    });

    it("should display transaction details", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("pay_20260517123456_abc123")).toBeInTheDocument();
        expect(screen.getByText(/5 000/)).toBeInTheDocument();
        expect(screen.getByText("RUB")).toBeInTheDocument();
        expect(screen.getByText("VISA •••• 1111")).toBeInTheDocument();
        expect(screen.getByText("STUB-123456")).toBeInTheDocument();
      });
    });

    it("should show download receipt button", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("Скачать чек")).toBeInTheDocument();
      });
    });

    it("should show return to dashboard button", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("Вернуться в панель управления")).toBeInTheDocument();
      });
    });
  });

  describe("Failed State", () => {
    const failedResponse = {
      payment_id: "pay_20260517123456_abc123",
      status: "failed" as const,
      amount: 5000,
      currency: "RUB",
      payment_method: "card",
      error_code: "INSUFFICIENT_FUNDS",
      error_message: "Недостаточно средств на карте",
      created_at: "2026-05-17T12:34:56Z",
    };

    beforeEach(() => {
      (paymentAPI.getPaymentStatus as jest.Mock).mockResolvedValue(failedResponse);
    });

    it("should display failure message", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("Платёж не прошёл")).toBeInTheDocument();
      });
    });

    it("should display error details", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText(/Недостаточно средств на карте/)).toBeInTheDocument();
        expect(screen.getByText(/INSUFFICIENT_FUNDS/)).toBeInTheDocument();
      });
    });

    it("should not show download receipt button", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.queryByText("Скачать чек")).not.toBeInTheDocument();
      });
    });
  });

  describe("Refunded State", () => {
    const refundedResponse = {
      payment_id: "pay_20260517123456_abc123",
      status: "refunded" as const,
      amount: 5000,
      currency: "RUB",
      payment_method: "card",
      card_last4: "1111",
      card_brand: "visa",
      created_at: "2026-05-17T12:34:56Z",
      completed_at: "2026-05-17T12:35:00Z",
    };

    beforeEach(() => {
      (paymentAPI.getPaymentStatus as jest.Mock).mockResolvedValue(refundedResponse);
    });

    it("should display refunded message", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("Платёж возвращён")).toBeInTheDocument();
      });
    });
  });

  describe("Error State", () => {
    beforeEach(() => {
      (paymentAPI.getPaymentStatus as jest.Mock).mockRejectedValue(
        new Error("Payment not found")
      );
    });

    it("should display error message", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("Ошибка")).toBeInTheDocument();
        expect(screen.getByText("Payment not found")).toBeInTheDocument();
      });
    });

    it("should show return to dashboard button on error", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        expect(screen.getByText("Вернуться в панель управления")).toBeInTheDocument();
      });
    });
  });

  describe("Navigation", () => {
    const successResponse = {
      payment_id: "pay_123",
      status: "completed" as const,
      amount: 5000,
      currency: "RUB",
      payment_method: "card",
      created_at: "2026-05-17T12:34:56Z",
    };

    beforeEach(() => {
      (paymentAPI.getPaymentStatus as jest.Mock).mockResolvedValue(successResponse);
    });

    it("should navigate to dashboard when button clicked", async () => {
      render(<PaymentStatus paymentId="pay_123" />);

      await waitFor(() => {
        const button = screen.getByText("Вернуться в панель управления");
        button.click();
      });

      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  describe("API Integration", () => {
    it("should call getPaymentStatus with correct payment ID", async () => {
      const successResponse = {
        payment_id: "pay_test_123",
        status: "completed" as const,
        amount: 5000,
        currency: "RUB",
        payment_method: "card",
        created_at: "2026-05-17T12:34:56Z",
      };

      (paymentAPI.getPaymentStatus as jest.Mock).mockResolvedValue(successResponse);

      render(<PaymentStatus paymentId="pay_test_123" />);

      await waitFor(() => {
        expect(paymentAPI.getPaymentStatus).toHaveBeenCalledWith("pay_test_123");
      });
    });
  });
});
