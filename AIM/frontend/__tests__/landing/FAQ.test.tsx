import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { FAQ } from "@/components/landing/FAQ";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe("FAQ", () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = jest.fn();
  });

  it("renders section heading", () => {
    render(<FAQ />);

    const heading = screen.getByRole("heading", { name: /Часто задаваемые вопросы/i });
    expect(heading).toBeInTheDocument();
  });

  it("renders all FAQ items by default", () => {
    render(<FAQ />);

    expect(screen.getByText(/Как вы обеспечиваете соответствие ФЗ-152/i)).toBeInTheDocument();
    expect(screen.getByText(/Что означает гарантия результата/i)).toBeInTheDocument();
    expect(screen.getByText(/Какой минимальный бюджет нужен для старта/i)).toBeInTheDocument();
  });

  it("respects limit prop", () => {
    render(<FAQ limit={3} />);

    const buttons = screen.getAllByRole("button", { expanded: false });
    // 3 FAQ items + category buttons + CTA button
    expect(buttons.filter(btn => btn.getAttribute("aria-expanded") !== null)).toHaveLength(3);
  });

  it("renders search input", () => {
    render(<FAQ />);

    const searchInput = screen.getByPlaceholderText(/Поиск по вопросам/i);
    expect(searchInput).toBeInTheDocument();
  });

  it("filters FAQs by search query", async () => {
    render(<FAQ />);

    const searchInput = screen.getByPlaceholderText(/Поиск по вопросам/i);
    fireEvent.change(searchInput, { target: { value: "ФЗ-152" } });

    await waitFor(() => {
      expect(screen.getByText(/Как вы обеспечиваете соответствие ФЗ-152/i)).toBeInTheDocument();
      expect(screen.queryByText(/Какой минимальный бюджет/i)).not.toBeInTheDocument();
    });
  });

  it("shows no results message when search has no matches", async () => {
    render(<FAQ />);

    const searchInput = screen.getByPlaceholderText(/Поиск по вопросам/i);
    fireEvent.change(searchInput, { target: { value: "xyz123nonexistent" } });

    await waitFor(() => {
      expect(screen.getByText(/Вопросы не найдены/i)).toBeInTheDocument();
    });
  });

  it("renders category filter buttons", () => {
    render(<FAQ />);

    expect(screen.getByRole("button", { name: "Все вопросы" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Безопасность" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Результаты" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Цены" })).toBeInTheDocument();
  });

  it("filters FAQs by category", async () => {
    render(<FAQ />);

    const securityButton = screen.getByRole("button", { name: "Безопасность" });
    fireEvent.click(securityButton);

    await waitFor(() => {
      expect(screen.getByText(/Как вы обеспечиваете соответствие ФЗ-152/i)).toBeInTheDocument();
      expect(screen.queryByText(/Какой минимальный бюджет/i)).not.toBeInTheDocument();
    });
  });

  it("expands FAQ item when clicked", async () => {
    render(<FAQ />);

    const faqButton = screen.getByRole("button", { name: /Как вы обеспечиваете соответствие ФЗ-152/i });
    expect(faqButton).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(faqButton);

    await waitFor(() => {
      expect(faqButton).toHaveAttribute("aria-expanded", "true");
      expect(screen.getByText(/Мы полностью соблюдаем требования ФЗ-152/i)).toBeInTheDocument();
    });
  });

  it("collapses FAQ item when clicked again", async () => {
    render(<FAQ />);

    const faqButton = screen.getByRole("button", { name: /Как вы обеспечиваете соответствие ФЗ-152/i });

    // Expand
    fireEvent.click(faqButton);
    await waitFor(() => {
      expect(faqButton).toHaveAttribute("aria-expanded", "true");
    });

    // Collapse
    fireEvent.click(faqButton);
    await waitFor(() => {
      expect(faqButton).toHaveAttribute("aria-expanded", "false");
    });
  });

  it("closes previous FAQ when opening new one", async () => {
    render(<FAQ />);

    const faq1Button = screen.getByRole("button", { name: /Как вы обеспечиваете соответствие ФЗ-152/i });
    const faq2Button = screen.getByRole("button", { name: /Что означает гарантия результата/i });

    // Open first FAQ
    fireEvent.click(faq1Button);
    await waitFor(() => {
      expect(faq1Button).toHaveAttribute("aria-expanded", "true");
    });

    // Open second FAQ
    fireEvent.click(faq2Button);
    await waitFor(() => {
      expect(faq2Button).toHaveAttribute("aria-expanded", "true");
      expect(faq1Button).toHaveAttribute("aria-expanded", "false");
    });
  });

  it("displays tags for each FAQ", async () => {
    render(<FAQ />);

    const faqButton = screen.getByRole("button", { name: /Как вы обеспечиваете соответствие ФЗ-152/i });
    fireEvent.click(faqButton);

    await waitFor(() => {
      expect(screen.getByText("безопасность")).toBeInTheDocument();
      expect(screen.getByText("ФЗ-152")).toBeInTheDocument();
      expect(screen.getByText("данные")).toBeInTheDocument();
    });
  });

  it("renders CTA button", () => {
    render(<FAQ />);

    const ctaButton = screen.getByRole("button", { name: /Задать вопрос/i });
    expect(ctaButton).toBeInTheDocument();
  });

  it("scrolls to contact form when CTA clicked", () => {
    const mockContactForm = document.createElement("div");
    mockContactForm.id = "contact-form";
    document.body.appendChild(mockContactForm);

    render(<FAQ />);

    const ctaButton = screen.getByRole("button", { name: /Задать вопрос/i });
    fireEvent.click(ctaButton);

    expect(mockContactForm.scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth" });

    document.body.removeChild(mockContactForm);
  });

  it("includes Schema.org FAQPage markup", () => {
    const { container } = render(<FAQ />);

    const script = container.querySelector('script[type="application/ld+json"]');
    expect(script).toBeInTheDocument();

    const schemaData = JSON.parse(script?.textContent || "{}");
    expect(schemaData["@type"]).toBe("FAQPage");
    expect(schemaData.mainEntity).toBeDefined();
    expect(Array.isArray(schemaData.mainEntity)).toBe(true);
  });

  it("search works with question text", async () => {
    render(<FAQ />);

    const searchInput = screen.getByPlaceholderText(/Поиск по вопросам/i);
    fireEvent.change(searchInput, { target: { value: "гарантия" } });

    await waitFor(() => {
      expect(screen.getByText(/Что означает гарантия результата/i)).toBeInTheDocument();
    });
  });

  it("search works with answer text", async () => {
    render(<FAQ />);

    const searchInput = screen.getByPlaceholderText(/Поиск по вопросам/i);
    fireEvent.change(searchInput, { target: { value: "Роскомнадзор" } });

    await waitFor(() => {
      expect(screen.getByText(/Как вы обеспечиваете соответствие ФЗ-152/i)).toBeInTheDocument();
    });
  });

  it("search works with tags", async () => {
    render(<FAQ />);

    const searchInput = screen.getByPlaceholderText(/Поиск по вопросам/i);
    fireEvent.change(searchInput, { target: { value: "ROI" } });

    await waitFor(() => {
      expect(screen.getByText(/Когда мы увидим первые результаты/i)).toBeInTheDocument();
    });
  });

  it("combines search and category filters", async () => {
    render(<FAQ />);

    // Select security category
    const securityButton = screen.getByRole("button", { name: "Безопасность" });
    fireEvent.click(securityButton);

    // Search within security category
    const searchInput = screen.getByPlaceholderText(/Поиск по вопросам/i);
    fireEvent.change(searchInput, { target: { value: "данные" } });

    await waitFor(() => {
      expect(screen.getByText(/Где хранятся данные наших пациентов/i)).toBeInTheDocument();
      expect(screen.queryByText(/Какой минимальный бюджет/i)).not.toBeInTheDocument();
    });
  });

  it("resets to all categories when clicking 'Все вопросы'", async () => {
    render(<FAQ />);

    // Select security category
    const securityButton = screen.getByRole("button", { name: "Безопасность" });
    fireEvent.click(securityButton);

    await waitFor(() => {
      expect(screen.queryByText(/Какой минимальный бюджет/i)).not.toBeInTheDocument();
    });

    // Click "Все вопросы"
    const allButton = screen.getByRole("button", { name: "Все вопросы" });
    fireEvent.click(allButton);

    await waitFor(() => {
      expect(screen.getByText(/Какой минимальный бюджет/i)).toBeInTheDocument();
    });
  });

  it("has proper ARIA labels", () => {
    render(<FAQ />);

    const section = screen.getByRole("region", { name: "Часто задаваемые вопросы" });
    expect(section).toBeInTheDocument();

    const searchInput = screen.getByLabelText(/Поиск по вопросам/i);
    expect(searchInput).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<FAQ className="custom-class" />);

    const section = container.querySelector("section");
    expect(section).toHaveClass("custom-class");
  });
});
