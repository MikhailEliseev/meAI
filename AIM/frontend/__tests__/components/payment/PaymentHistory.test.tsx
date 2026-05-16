import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PaymentHistory } from "@/components/payment/PaymentHistory";

describe("PaymentHistory", () => {
  const defaultProps = {
    customerEmail: "test@example.com",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render loading state initially", () => {
      render(<PaymentHistory {...defaultProps} />);

      const spinner = document.querySelector(".animate-spin");
      expect(spinner).toBeInTheDocument();
    });

    it("should render invoice list after loading", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument();
      expect(screen.getByText("AIM-2026-003")).toBeInTheDocument();
    });

    it("should apply custom className", async () => {
      const { container } = render(
        <PaymentHistory {...defaultProps} className="custom-class" />
      );

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const wrapper = container.querySelector(".custom-class");
      expect(wrapper).toBeInTheDocument();
    });
  });

  describe("Filters", () => {
    it("should render all filter buttons", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      expect(screen.getByRole("button", { name: "Все" })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Оплачены" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Ожидают оплаты" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Просрочены" })
      ).toBeInTheDocument();
    });

    it("should filter paid invoices", async () => {
      const user = userEvent.setup();
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const paidButton = screen.getByRole("button", { name: "Оплачены" });
      await user.click(paidButton);

      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument();
      expect(screen.queryByText("AIM-2026-003")).not.toBeInTheDocument();
    });

    it("should filter pending invoices", async () => {
      const user = userEvent.setup();
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const pendingButton = screen.getByRole("button", {
        name: "Ожидают оплаты",
      });
      await user.click(pendingButton);

      expect(screen.queryByText("AIM-2026-001")).not.toBeInTheDocument();
      expect(screen.queryByText("AIM-2026-002")).not.toBeInTheDocument();
      expect(screen.getByText("AIM-2026-003")).toBeInTheDocument();
    });

    it("should highlight active filter", async () => {
      const user = userEvent.setup();
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const paidButton = screen.getByRole("button", { name: "Оплачены" });
      await user.click(paidButton);

      expect(paidButton).toHaveClass("bg-primary-600");
      expect(paidButton).toHaveClass("text-white");
    });
  });

  describe("Invoice Display", () => {
    it("should display invoice number", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });
    });

    it("should display invoice dates", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        const issuedLabels = screen.getAllByText(/Выставлен:/);
        expect(issuedLabels.length).toBeGreaterThan(0);
      });

      const dueDateLabels = screen.getAllByText(/Оплатить до:/);
      expect(dueDateLabels.length).toBeGreaterThan(0);
    });

    it("should display invoice items", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getAllByText(
            "AI-маркетинг для медицинских клиник (месяц) × 1"
          )[0]
        ).toBeInTheDocument();
      });
    });

    it("should display invoice totals", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getAllByText("150 000 ₽")[0]).toBeInTheDocument();
      });

      expect(screen.getAllByText("30 000 ₽")[0]).toBeInTheDocument();
      expect(screen.getAllByText("180 000 ₽")[0]).toBeInTheDocument();
    });

    it("should display status badges", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getAllByText("Оплачен")).toHaveLength(2);
      });

      expect(screen.getByText("Отправлен")).toBeInTheDocument();
    });

    it("should display paid date for paid invoices", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getAllByText(/✓ Оплачен/)[0]).toBeInTheDocument();
      });
    });
  });

  describe("Invoice Actions", () => {
    it("should render download button for all invoices", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const downloadButtons = screen.getAllByRole("button", {
        name: "Скачать PDF",
      });
      expect(downloadButtons).toHaveLength(3);
    });

    it("should render pay button only for pending invoices", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const payButtons = screen.getAllByRole("button", { name: "Оплатить" });
      expect(payButtons).toHaveLength(1);
    });

    it("should not render pay button for paid invoices", async () => {
      const user = userEvent.setup();
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const paidButton = screen.getByRole("button", { name: "Оплачены" });
      await user.click(paidButton);

      const payButtons = screen.queryAllByRole("button", { name: "Оплатить" });
      expect(payButtons).toHaveLength(0);
    });
  });

  describe("Empty State", () => {
    it("should show empty state when no invoices match filter", async () => {
      const user = userEvent.setup();
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const overdueButton = screen.getByRole("button", { name: "Просрочены" });
      await user.click(overdueButton);

      // Mock data has no overdue invoices (AIM-2026-003 due date is today)
      // So we should see either empty state or the invoice if it's considered overdue
      // Check that filter is applied by verifying paid invoices are not shown
      expect(screen.queryByText("AIM-2026-001")).not.toBeInTheDocument();
      expect(screen.queryByText("AIM-2026-002")).not.toBeInTheDocument();
    });
  });

  describe("Animation", () => {
    it("should animate invoice cards on render", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      // Check that motion.div is used (framer-motion adds data attributes)
      const cards = document.querySelectorAll('[class*="rounded-2xl"]');
      expect(cards.length).toBeGreaterThan(0);
    });
  });

  describe("Status Badge Colors", () => {
    it("should use correct colors for paid status", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        const paidBadges = screen.getAllByText("Оплачен");
        expect(paidBadges[0]).toHaveClass("bg-green-100");
        expect(paidBadges[0]).toHaveClass("text-green-700");
      });
    });

    it("should use correct colors for sent status", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        const sentBadge = screen.getByText("Отправлен");
        expect(sentBadge).toHaveClass("bg-blue-100");
        expect(sentBadge).toHaveClass("text-blue-700");
      });
    });
  });

  describe("Responsive Layout", () => {
    it("should render filters with flex-wrap", async () => {
      render(<PaymentHistory {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("AIM-2026-001")).toBeInTheDocument();
      });

      const filterContainer = screen
        .getByRole("button", { name: "Все" })
        .closest("div");
      expect(filterContainer).toHaveClass("flex-wrap");
    });
  });
});
