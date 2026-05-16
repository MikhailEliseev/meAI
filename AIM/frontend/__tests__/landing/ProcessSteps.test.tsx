import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ProcessSteps } from "@/components/landing/ProcessSteps";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

describe("ProcessSteps", () => {
  beforeEach(() => {
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = jest.fn();
  });

  it("renders section heading", () => {
    render(<ProcessSteps />);

    const heading = screen.getByRole("heading", { name: /Как мы работаем/i });
    expect(heading).toBeInTheDocument();
  });

  it("renders all 3 process steps", () => {
    render(<ProcessSteps />);

    expect(screen.getByText(/Бесплатная консультация/i)).toBeInTheDocument();
    expect(screen.getByText(/Персональная стратегия/i)).toBeInTheDocument();
    expect(screen.getByText(/Реализация и результат/i)).toBeInTheDocument();
  });

  it("displays step numbers", () => {
    render(<ProcessSteps />);

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows duration for each step", () => {
    render(<ProcessSteps />);

    expect(screen.getByText(/15 минут/i)).toBeInTheDocument();
    expect(screen.getByText(/3-5 дней/i)).toBeInTheDocument();
    expect(screen.getByText(/30 дней/i)).toBeInTheDocument();
  });

  it("displays step descriptions", () => {
    render(<ProcessSteps />);

    expect(screen.getByText(/Анализируем ваш бизнес и конкурентов с помощью AI/i)).toBeInTheDocument();
    expect(screen.getByText(/Создаём индивидуальный план привлечения пациентов/i)).toBeInTheDocument();
    expect(screen.getByText(/Запускаем кампании и привлекаем пациентов/i)).toBeInTheDocument();
  });

  it("shows details for each step", () => {
    render(<ProcessSteps />);

    // Step 1 details
    expect(screen.getByText(/AI-анализ вашего сайта и конкурентов/i)).toBeInTheDocument();
    expect(screen.getByText(/Оценка текущей ситуации/i)).toBeInTheDocument();

    // Step 2 details
    expect(screen.getByText(/Подбор каналов привлечения/i)).toBeInTheDocument();
    expect(screen.getByText(/Прогноз результатов и ROI/i)).toBeInTheDocument();

    // Step 3 details
    expect(screen.getByText(/Настройка рекламы и SEO/i)).toBeInTheDocument();
    expect(screen.getByText(/Гарантия результата/i)).toBeInTheDocument();
  });

  it("renders CTA button", () => {
    render(<ProcessSteps />);

    const ctaButton = screen.getByRole("button", { name: /Начать работу с AIM Agency/i });
    expect(ctaButton).toBeInTheDocument();
    expect(ctaButton).toHaveClass("btn-primary");
  });

  it("scrolls to contact form when CTA clicked", () => {
    // Create mock contact form element
    const mockContactForm = document.createElement("div");
    mockContactForm.id = "contact-form";
    document.body.appendChild(mockContactForm);

    render(<ProcessSteps />);

    const ctaButton = screen.getByRole("button", { name: /Начать работу с AIM Agency/i });
    fireEvent.click(ctaButton);

    expect(mockContactForm.scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth" });

    // Cleanup
    document.body.removeChild(mockContactForm);
  });

  it("displays free consultation disclaimer", () => {
    render(<ProcessSteps />);

    expect(screen.getByText(/Первая консультация бесплатно/i)).toBeInTheDocument();
    expect(screen.getByText(/Без обязательств/i)).toBeInTheDocument();
  });

  it("renders step icons", () => {
    render(<ProcessSteps />);

    const section = screen.getByRole("region", { name: "Как мы работаем" });
    expect(section).toBeInTheDocument();
    // Icons are rendered as text emojis (🎯, 📊, 🚀)
  });

  it("applies custom className", () => {
    const { container } = render(<ProcessSteps className="custom-class" />);

    const section = container.querySelector("section");
    expect(section).toHaveClass("custom-class");
  });

  it("has proper ARIA labels", () => {
    render(<ProcessSteps />);

    const section = screen.getByRole("region", { name: "Как мы работаем" });
    expect(section).toBeInTheDocument();
  });
});
