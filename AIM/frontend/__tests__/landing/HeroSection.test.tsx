import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { HeroSection } from "@/components/landing/HeroSection";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

describe("HeroSection", () => {
  beforeEach(() => {
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = jest.fn();
  });

  it("renders headline correctly", () => {
    render(<HeroSection />);

    const headline = screen.getByRole("heading", { level: 1 });
    expect(headline).toBeInTheDocument();
    expect(headline).toHaveTextContent("AI-маркетинг для медицинских клиник");
  });

  it("renders subheadline with value proposition", () => {
    render(<HeroSection />);

    const subheadline = screen.getByText(/Привлекаем пациентов с помощью искусственного интеллекта/i);
    expect(subheadline).toBeInTheDocument();
  });

  it("renders primary CTA button", () => {
    render(<HeroSection />);

    const ctaButton = screen.getByRole("button", { name: /Получить бесплатный аудит/i });
    expect(ctaButton).toBeInTheDocument();
    expect(ctaButton).toHaveClass("btn-primary");
  });

  it("renders secondary CTA link", () => {
    render(<HeroSection />);

    const secondaryCTA = screen.getByRole("link", { name: /Посмотреть кейсы/i });
    expect(secondaryCTA).toBeInTheDocument();
    expect(secondaryCTA).toHaveAttribute("href", "#case-studies");
  });

  it("scrolls to contact form when CTA clicked", () => {
    // Create mock contact form element
    const mockContactForm = document.createElement("div");
    mockContactForm.id = "contact-form";
    document.body.appendChild(mockContactForm);

    render(<HeroSection />);

    const ctaButton = screen.getByRole("button", { name: /Получить бесплатный аудит/i });
    fireEvent.click(ctaButton);

    expect(mockContactForm.scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth" });

    // Cleanup
    document.body.removeChild(mockContactForm);
  });

  it("renders trust badges", () => {
    render(<HeroSection />);

    expect(screen.getByText("ФЗ-152")).toBeInTheDocument();
    expect(screen.getByText("Яндекс Партнёр")).toBeInTheDocument();
    expect(screen.getByText("50+ Клиентов")).toBeInTheDocument();
    expect(screen.getByText("Гарантия результата")).toBeInTheDocument();
  });

  it("renders stats cards on desktop", () => {
    render(<HeroSection />);

    expect(screen.getByText("300%")).toBeInTheDocument();
    expect(screen.getByText("Средний рост трафика")).toBeInTheDocument();
    expect(screen.getByText("50+")).toBeInTheDocument();
    expect(screen.getByText("15K+")).toBeInTheDocument();
    expect(screen.getByText("24/7")).toBeInTheDocument();
  });

  it("has proper ARIA labels", () => {
    render(<HeroSection />);

    const section = screen.getByRole("region", { name: /hero-heading/i });
    expect(section).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<HeroSection className="custom-class" />);

    const section = container.querySelector("section");
    expect(section).toHaveClass("custom-class");
  });

  it("has accessible button labels", () => {
    render(<HeroSection />);

    const primaryCTA = screen.getByLabelText("Получить бесплатный аудит маркетинга");
    expect(primaryCTA).toBeInTheDocument();

    const secondaryCTA = screen.getByLabelText("Посмотреть кейсы наших клиентов");
    expect(secondaryCTA).toBeInTheDocument();
  });
});
