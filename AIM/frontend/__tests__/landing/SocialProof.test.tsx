import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { CaseStudies } from "@/components/landing/CaseStudies";
import { Testimonials } from "@/components/landing/Testimonials";
import { Awards } from "@/components/landing/Awards";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    article: ({ children, ...props }: any) => <article {...props}>{children}</article>,
  },
}));

// Mock next/image
jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

describe("CaseStudies", () => {
  it("renders section heading", () => {
    render(<CaseStudies />);

    const heading = screen.getByRole("heading", { name: /Наши кейсы/i });
    expect(heading).toBeInTheDocument();
  });

  it("renders all case studies by default", () => {
    render(<CaseStudies />);

    // Check for specific case study titles
    expect(screen.getByText(/Стоматология «Дента Плюс»/i)).toBeInTheDocument();
    expect(screen.getByText(/Кардиологический центр «Здоровое Сердце»/i)).toBeInTheDocument();
  });

  it("respects limit prop", () => {
    render(<CaseStudies limit={2} />);

    const articles = screen.getAllByRole("article");
    expect(articles).toHaveLength(2);
  });

  it("displays metrics for each case study", () => {
    render(<CaseStudies limit={1} />);

    expect(screen.getByText(/\+320%/i)).toBeInTheDocument();
    expect(screen.getByText(/5\.8%/i)).toBeInTheDocument();
    expect(screen.getByText(/₽850/i)).toBeInTheDocument();
  });

  it("includes Schema.org markup", () => {
    const { container } = render(<CaseStudies />);

    const script = container.querySelector('script[type="application/ld+json"]');
    expect(script).toBeInTheDocument();

    const schemaData = JSON.parse(script?.textContent || "{}");
    expect(schemaData["@type"]).toBe("ItemList");
  });

  it("displays ROI badge", () => {
    render(<CaseStudies limit={1} />);

    expect(screen.getByText(/450%/i)).toBeInTheDocument();
  });

  it("shows 'View all' link when limited", () => {
    render(<CaseStudies limit={3} />);

    const viewAllLink = screen.getByRole("link", { name: /Посмотреть все кейсы/i });
    expect(viewAllLink).toBeInTheDocument();
    expect(viewAllLink).toHaveAttribute("href", "/case-studies");
  });
});

describe("Testimonials", () => {
  it("renders section heading", () => {
    render(<Testimonials />);

    const heading = screen.getByRole("heading", { name: /Что говорят наши клиенты/i });
    expect(heading).toBeInTheDocument();
  });

  it("renders testimonials with author info", () => {
    render(<Testimonials limit={1} />);

    expect(screen.getByText(/Анна Петрова/i)).toBeInTheDocument();
    expect(screen.getByText(/Главный врач/i)).toBeInTheDocument();
  });

  it("displays testimonial text", () => {
    render(<Testimonials limit={1} />);

    expect(screen.getByText(/За 3 месяца работы с AIM/i)).toBeInTheDocument();
  });

  it("shows results badges", () => {
    render(<Testimonials limit={1} />);

    expect(screen.getByText(/ROI 450%/i)).toBeInTheDocument();
    expect(screen.getByText(/\+320% трафика/i)).toBeInTheDocument();
  });

  it("includes Schema.org review markup", () => {
    const { container } = render(<Testimonials />);

    const script = container.querySelector('script[type="application/ld+json"]');
    expect(script).toBeInTheDocument();

    const schemaData = JSON.parse(script?.textContent || "{}");
    expect(schemaData["@type"]).toBe("Organization");
    expect(schemaData.review).toBeDefined();
  });

  it("displays stats summary", () => {
    render(<Testimonials />);

    expect(screen.getByText(/50\+/i)).toBeInTheDocument();
    expect(screen.getByText(/Довольных клиентов/i)).toBeInTheDocument();
    expect(screen.getByText(/15K\+/i)).toBeInTheDocument();
    expect(screen.getByText(/Новых пациентов/i)).toBeInTheDocument();
  });

  it("respects limit prop", () => {
    render(<Testimonials limit={2} />);

    const articles = screen.getAllByRole("article");
    expect(articles).toHaveLength(2);
  });
});

describe("Awards", () => {
  it("renders section heading", () => {
    render(<Awards />);

    const heading = screen.getByRole("heading", { name: /Награды и сертификации/i });
    expect(heading).toBeInTheDocument();
  });

  it("displays all awards", () => {
    render(<Awards />);

    expect(screen.getByText(/Сертифицированный партнёр Яндекс\.Директ/i)).toBeInTheDocument();
    expect(screen.getByText(/Лучшее медицинское маркетинговое агентство/i)).toBeInTheDocument();
    expect(screen.getByText(/Инновации в AI-маркетинге/i)).toBeInTheDocument();
    expect(screen.getByText(/Сертификат соответствия ФЗ-152/i)).toBeInTheDocument();
  });

  it("shows award organizations and years", () => {
    render(<Awards />);

    expect(screen.getByText(/Яндекс • 2025/i)).toBeInTheDocument();
    expect(screen.getByText(/Роскомнадзор • 2025/i)).toBeInTheDocument();
  });

  it("includes Schema.org organization markup", () => {
    const { container } = render(<Awards />);

    const script = container.querySelector('script[type="application/ld+json"]');
    expect(script).toBeInTheDocument();

    const schemaData = JSON.parse(script?.textContent || "{}");
    expect(schemaData["@type"]).toBe("Organization");
    expect(schemaData.award).toBeDefined();
  });

  it("displays FZ-152 compliance statement", () => {
    render(<Awards />);

    expect(screen.getByText(/Полное соответствие ФЗ-152/i)).toBeInTheDocument();
  });

  it("renders award icons", () => {
    render(<Awards />);

    // Icons are rendered as text emojis
    const container = screen.getByRole("region", { name: /awards-heading/i });
    expect(container).toBeInTheDocument();
  });
});
