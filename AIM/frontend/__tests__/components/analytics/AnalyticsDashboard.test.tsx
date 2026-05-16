import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AnalyticsDashboard } from "@/components/analytics/AnalyticsDashboard";

// Mock fetch globally
global.fetch = jest.fn();

const mockLeadData = {
  summary: {
    totalLeads: 156,
    hotLeads: 42,
    warmLeads: 68,
    coldLeads: 46,
    averageScore: 62.5,
    conversionRate: 0.27,
  },
  tierBreakdown: [
    { tier: "hot", count: 42, percentage: 26.9 },
    { tier: "warm", count: 68, percentage: 43.6 },
    { tier: "cold", count: 46, percentage: 29.5 },
  ],
  dailyLeads: [
    { date: "2026-05-10", hot: 3, warm: 5, cold: 2 },
    { date: "2026-05-11", hot: 4, warm: 6, cold: 3 },
  ],
  topSpecialties: [
    { specialty: "Стоматология", count: 45, avgScore: 72.3 },
    { specialty: "Косметология", count: 32, avgScore: 68.5 },
  ],
};

const mockEmailData = {
  summary: {
    totalSent: 468,
    totalOpened: 312,
    totalClicked: 156,
    openRate: 0.667,
    clickRate: 0.333,
    clickToOpenRate: 0.5,
    unsubscribeRate: 0.021,
  },
  sequencePerformance: [
    {
      sequenceId: "hot-lead-sequence",
      name: "Hot Lead - Immediate Follow-up",
      sent: 126,
      opened: 105,
      clicked: 63,
      openRate: 0.833,
      clickRate: 0.5,
      completed: 42,
      completionRate: 0.333,
    },
  ],
  dailyPerformance: [
    { date: "2026-05-10", sent: 45, opened: 30, clicked: 15 },
    { date: "2026-05-11", sent: 52, opened: 35, clicked: 18 },
  ],
};

const mockQueueData = {
  waiting: 5,
  active: 2,
  completed: 100,
  failed: 3,
  delayed: 10,
};

describe("AnalyticsDashboard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes("/api/analytics/leads")) {
        return Promise.resolve({
          json: () => Promise.resolve({ success: true, data: mockLeadData }),
        });
      }
      if (url.includes("/api/analytics/email")) {
        return Promise.resolve({
          json: () => Promise.resolve({ success: true, data: mockEmailData }),
        });
      }
      if (url.includes("/api/email/queue-stats")) {
        return Promise.resolve({
          json: () => Promise.resolve({ success: true, stats: mockQueueData }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    });
  });

  it("fetches and displays lead analytics", async () => {
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Аналитика")).toBeInTheDocument();
    });

    expect(screen.getByText("Всего лидов")).toBeInTheDocument();
    expect(screen.getByText("156")).toBeInTheDocument();
    expect(screen.getByText("Горячие лиды")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Средний балл")).toBeInTheDocument();
    expect(screen.getByText("62.5")).toBeInTheDocument();
  });

  it("switches to email tab and displays email analytics", async () => {
    const user = userEvent.setup();
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Аналитика")).toBeInTheDocument();
    });

    const emailTab = screen.getByRole("button", { name: /email/i });
    await user.click(emailTab);

    await waitFor(() => {
      expect(screen.getByText("Отправлено")).toBeInTheDocument();
      expect(screen.getByText("468")).toBeInTheDocument();
      expect(screen.getByText("Open Rate")).toBeInTheDocument();
      expect(screen.getByText("66.7%")).toBeInTheDocument();
    });
  });

  it("switches to queue tab and displays queue stats", async () => {
    const user = userEvent.setup();
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Аналитика")).toBeInTheDocument();
    });

    const queueTab = screen.getByRole("button", { name: /очередь/i });
    await user.click(queueTab);

    await waitFor(() => {
      expect(screen.getByText("В ожидании")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
      expect(screen.getByText("Активные")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
    });
  });

  it("handles fetch errors gracefully", async () => {
    const consoleError = jest.spyOn(console, "error").mockImplementation();
    (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalledWith(
        "[Analytics] Error fetching data:",
        expect.any(Error)
      );
    });

    consoleError.mockRestore();
  });

  it("displays tier breakdown chart", async () => {
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Распределение по уровням")).toBeInTheDocument();
    });
  });

  it("displays daily leads chart", async () => {
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Лиды по дням")).toBeInTheDocument();
    });
  });

  it("displays top specialties", async () => {
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Топ специализаций")).toBeInTheDocument();
      expect(screen.getByText("Стоматология")).toBeInTheDocument();
      expect(screen.getByText("Косметология")).toBeInTheDocument();
    });
  });

  it("displays sequence performance in email tab", async () => {
    const user = userEvent.setup();
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Аналитика")).toBeInTheDocument();
    });

    const emailTab = screen.getByRole("button", { name: /email/i });
    await user.click(emailTab);

    await waitFor(() => {
      expect(
        screen.getByText("Эффективность последовательностей")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Hot Lead - Immediate Follow-up")
      ).toBeInTheDocument();
    });
  });

  it("applies custom className to outer container", async () => {
    const { container } = render(
      <AnalyticsDashboard className="custom-class" />
    );

    await waitFor(() => {
      expect(screen.getByText("Аналитика")).toBeInTheDocument();
    });

    const outerDiv = container.querySelector(".custom-class");
    expect(outerDiv).toBeInTheDocument();
  });
});
