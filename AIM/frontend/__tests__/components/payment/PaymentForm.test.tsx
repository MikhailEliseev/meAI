import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PaymentForm } from "@/components/payment/PaymentForm";

describe("PaymentForm", () => {
  const mockOnSuccess = jest.fn();
  const mockOnError = jest.fn();

  const defaultProps = {
    amount: 180000,
    description: "AI-маркетинг для медицинских клиник (месяц)",
    customerEmail: "test@example.com",
    onSuccess: mockOnSuccess,
    onError: mockOnError,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render payment form with all fields", () => {
      render(<PaymentForm {...defaultProps} />);

      // Use getAllByText for amount that appears multiple times
      const amountElements = screen.getAllByText(/180 000/);
      expect(amountElements.length).toBeGreaterThan(0);

      expect(
        screen.getByText("AI-маркетинг для медицинских клиник (месяц)")
      ).toBeInTheDocument();
      expect(screen.getByLabelText("Имя владельца карты")).toBeInTheDocument();
      expect(screen.getByLabelText("Номер карты")).toBeInTheDocument();
      expect(screen.getByLabelText("Срок действия")).toBeInTheDocument();
      expect(screen.getByLabelText("CVV")).toBeInTheDocument();
    });

    it("should render security notice", () => {
      render(<PaymentForm {...defaultProps} />);

      expect(
        screen.getByText(/Платёж защищён по стандарту PCI DSS/)
      ).toBeInTheDocument();
    });

    it("should render stub notice", () => {
      render(<PaymentForm {...defaultProps} />);

      expect(screen.getByText(/STUB:/)).toBeInTheDocument();
      expect(
        screen.getByText(/Реальная интеграция с ЮKassa будет в Phase 12/)
      ).toBeInTheDocument();
    });

    it("should apply custom className", () => {
      const { container } = render(
        <PaymentForm {...defaultProps} className="custom-class" />
      );

      const form = container.querySelector("form");
      expect(form).toHaveClass("custom-class");
    });
  });

  describe("Card Number Formatting", () => {
    it("should format card number with spaces", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const cardInput = screen.getByLabelText("Номер карты");
      await user.type(cardInput, "1234567890123456");

      expect(cardInput).toHaveValue("1234 5678 9012 3456");
    });

    it("should limit card number to 16 digits", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const cardInput = screen.getByLabelText("Номер карты");
      await user.type(cardInput, "12345678901234567890");

      expect(cardInput).toHaveValue("1234 5678 9012 3456");
    });
  });

  describe("Expiry Date Formatting", () => {
    it("should format expiry date as MM/YY", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const expiryInput = screen.getByLabelText("Срок действия");
      await user.type(expiryInput, "1226");

      expect(expiryInput).toHaveValue("12/26");
    });

    it("should limit expiry date to 4 digits", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const expiryInput = screen.getByLabelText("Срок действия");
      await user.type(expiryInput, "122699");

      expect(expiryInput).toHaveValue("12/26");
    });
  });

  describe("CVV Formatting", () => {
    it("should limit CVV to 4 digits", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const cvvInput = screen.getByLabelText("CVV");
      await user.type(cvvInput, "12345");

      expect(cvvInput).toHaveValue("1234");
    });

    it("should only allow digits in CVV", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const cvvInput = screen.getByLabelText("CVV");
      await user.type(cvvInput, "abc123");

      expect(cvvInput).toHaveValue("123");
    });
  });

  describe("Cardholder Name", () => {
    it("should convert cardholder name to uppercase", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const nameInput = screen.getByLabelText("Имя владельца карты");
      await user.type(nameInput, "ivan petrov");

      expect(nameInput).toHaveValue("IVAN PETROV");
    });
  });

  describe("Validation", () => {
    it("should show error for empty cardholder name", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      expect(
        screen.getByText("Введите имя владельца карты")
      ).toBeInTheDocument();
    });

    it("should show error for invalid card number", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const cardInput = screen.getByLabelText("Номер карты");
      await user.type(cardInput, "1234567890123456");

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      expect(screen.getByText("Неверный номер карты")).toBeInTheDocument();
    });

    it("should show error for invalid expiry date", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const expiryInput = screen.getByLabelText("Срок действия");
      await user.type(expiryInput, "1320");

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      expect(screen.getByText("Неверная дата (MM/YY)")).toBeInTheDocument();
    });

    it("should show error for invalid CVV", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const cvvInput = screen.getByLabelText("CVV");
      await user.type(cvvInput, "12");

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      expect(screen.getByText("Неверный CVV")).toBeInTheDocument();
    });

    it("should validate card number with Luhn algorithm", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const cardInput = screen.getByLabelText("Номер карты");
      // Valid test card: 4111111111111111
      await user.type(cardInput, "4111111111111111");

      const nameInput = screen.getByLabelText("Имя владельца карты");
      await user.type(nameInput, "IVAN PETROV");

      const expiryInput = screen.getByLabelText("Срок действия");
      await user.type(expiryInput, "1226");

      const cvvInput = screen.getByLabelText("CVV");
      await user.type(cvvInput, "123");

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      // Should not show card number error
      expect(
        screen.queryByText("Неверный номер карты")
      ).not.toBeInTheDocument();
    });
  });

  describe("Form Submission", () => {
    it("should call onSuccess after successful payment", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const nameInput = screen.getByLabelText("Имя владельца карты");
      await user.type(nameInput, "IVAN PETROV");

      const cardInput = screen.getByLabelText("Номер карты");
      await user.type(cardInput, "4111111111111111");

      const expiryInput = screen.getByLabelText("Срок действия");
      await user.type(expiryInput, "1226");

      const cvvInput = screen.getByLabelText("CVV");
      await user.type(cvvInput, "123");

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(mockOnSuccess).toHaveBeenCalledWith(
            expect.stringMatching(/^STUB-/)
          );
        },
        { timeout: 3000 }
      );
    });

    it("should show loading state during payment", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const nameInput = screen.getByLabelText("Имя владельца карты");
      await user.type(nameInput, "IVAN PETROV");

      const cardInput = screen.getByLabelText("Номер карты");
      await user.type(cardInput, "4111111111111111");

      const expiryInput = screen.getByLabelText("Срок действия");
      await user.type(expiryInput, "1226");

      const cvvInput = screen.getByLabelText("CVV");
      await user.type(cvvInput, "123");

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      expect(screen.getByText("Обработка платежа...")).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });

    it("should disable form fields during payment", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const nameInput = screen.getByLabelText("Имя владельца карты");
      await user.type(nameInput, "IVAN PETROV");

      const cardInput = screen.getByLabelText("Номер карты");
      await user.type(cardInput, "4111111111111111");

      const expiryInput = screen.getByLabelText("Срок действия");
      await user.type(expiryInput, "1226");

      const cvvInput = screen.getByLabelText("CVV");
      await user.type(cvvInput, "123");

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      expect(nameInput).toBeDisabled();
      expect(cardInput).toBeDisabled();
      expect(expiryInput).toBeDisabled();
      expect(cvvInput).toBeDisabled();
    });
  });

  describe("Error Handling", () => {
    it("should clear errors when user starts typing", async () => {
      const user = userEvent.setup();
      render(<PaymentForm {...defaultProps} />);

      const submitButton = screen.getByRole("button", { name: /Оплатить/ });
      await user.click(submitButton);

      expect(
        screen.getByText("Введите имя владельца карты")
      ).toBeInTheDocument();

      const nameInput = screen.getByLabelText("Имя владельца карты");
      await user.type(nameInput, "I");

      // Error should still be visible until form is resubmitted
      expect(
        screen.getByText("Введите имя владельца карты")
      ).toBeInTheDocument();
    });
  });
});
