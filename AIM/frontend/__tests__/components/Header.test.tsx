import React from "react";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Header } from "@/components/Header";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) =>
    React.createElement("a", { href, ...props }, children);
});

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    nav: ({ children, ...props }: any) => React.createElement("nav", props, children),
    div: ({ children, ...props }: any) => React.createElement("div", props, children),
    button: ({ children, ...props }: any) => React.createElement("button", props, children),
  },
  AnimatePresence: ({ children }: any) => children,
}));

describe("Header", () => {
  it("renders logo", () => {
    render(<Header />);
    expect(screen.getByText("AIM")).toBeInTheDocument();
  });

  it("renders desktop navigation links", () => {
    render(<Header />);
    expect(screen.getByText("Услуги")).toBeInTheDocument();
    expect(screen.getByText("Кейсы")).toBeInTheDocument();
    expect(screen.getByText("О нас")).toBeInTheDocument();
    expect(screen.getByText("Блог")).toBeInTheDocument();
    expect(screen.getByText("Контакты")).toBeInTheDocument();
  });

  it("renders CTA button with correct text", () => {
    render(<Header />);
    expect(screen.getByText(/аудит/i)).toBeInTheDocument();
  });

  it("has correct role attributes", () => {
    render(<Header />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: /навигация/i })).toBeInTheDocument();
  });

  it("mobile menu toggles on burger click", async () => {
    const user = userEvent.setup();
    render(<Header />);

    const burgerBtn = screen.getByRole("button", { name: /меню/i });
    await act(() => user.click(burgerBtn));

    const servicesLinks = screen.getAllByText("Услуги");
    expect(servicesLinks.length).toBeGreaterThanOrEqual(1);
  });

  it("CTA button links to contact section", () => {
    render(<Header />);
    const ctaLink = screen.getByText(/аудит/i).closest("a");
    expect(ctaLink).toHaveAttribute("href", "/contact");
  });
});
