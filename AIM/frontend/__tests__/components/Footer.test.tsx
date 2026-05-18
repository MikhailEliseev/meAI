import React from "react";
import { render, screen } from "@testing-library/react";
import { Footer } from "@/components/Footer";

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) =>
    React.createElement("a", { href, ...props }, children);
});

describe("Footer", () => {
  it("renders all column headings", () => {
    render(<Footer />);
    expect(screen.getByText("Услуги")).toBeInTheDocument();
    expect(screen.getByText("Компания")).toBeInTheDocument();
    expect(screen.getByText("Клиентам")).toBeInTheDocument();
    // "Контакты" появляется дважды — как ссылка и как заголовок колонки
    expect(screen.getAllByText("Контакты")).toHaveLength(2);
  });

  it("renders privacy policy link", () => {
    render(<Footer />);
    const link = screen.getByText("Политика конфиденциальности");
    expect(link).toBeInTheDocument();
    expect(link.closest("a")).toHaveAttribute("href", "/privacy-policy");
  });

  it("renders cookie settings link", () => {
    render(<Footer />);
    expect(screen.getByText("Cookie-файлы")).toBeInTheDocument();
  });

  it("renders copyright", () => {
    render(<Footer />);
    expect(screen.getByText(/© 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/AIM Agency/i)).toBeInTheDocument();
  });

  it("renders social media links", () => {
    render(<Footer />);
    expect(screen.getByText("Telegram")).toBeInTheDocument();
    expect(screen.getByText("VK")).toBeInTheDocument();
  });

  it("renders service links", () => {
    render(<Footer />);
    expect(screen.getByText("SEO-продвижение")).toBeInTheDocument();
    expect(screen.getByText("Яндекс.Директ")).toBeInTheDocument();
    expect(screen.getByText("Контент-маркетинг")).toBeInTheDocument();
    expect(screen.getByText("AI-аналитика")).toBeInTheDocument();
  });

  it("renders about links", () => {
    render(<Footer />);
    expect(screen.getByText("О нас").closest("a")).toHaveAttribute("href", "/about");
    expect(screen.getByText("Кейсы").closest("a")).toHaveAttribute("href", "/case-studies");
  });

  it("renders contact info", () => {
    render(<Footer />);
    expect(screen.getByText(/\+7/i)).toBeInTheDocument();
    expect(screen.getByText(/hello@iamaim\.ru/i)).toBeInTheDocument();
  });
});
