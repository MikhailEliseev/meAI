import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/analytics/email
 *
 * Get email performance analytics
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(request.url);
    const startDate = searchParams.get("startDate");
    const endDate = searchParams.get("endDate");

    // TODO: Implement database queries (Phase 2.5)
    // For now, return mock data for UI development

    const mockData = {
      summary: {
        totalSent: 468,
        totalOpened: 312,
        totalClicked: 156,
        openRate: 0.667, // 66.7%
        clickRate: 0.333, // 33.3%
        clickToOpenRate: 0.5, // 50%
        unsubscribeRate: 0.021, // 2.1%
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
        {
          sequenceId: "warm-lead-sequence",
          name: "Warm Lead - Nurturing Sequence",
          sent: 204,
          opened: 143,
          clicked: 71,
          openRate: 0.701,
          clickRate: 0.348,
          completed: 51,
          completionRate: 0.25,
        },
        {
          sequenceId: "cold-lead-sequence",
          name: "Cold Lead - Long-term Nurturing",
          sent: 138,
          opened: 64,
          clicked: 22,
          openRate: 0.464,
          clickRate: 0.159,
          completed: 14,
          completionRate: 0.101,
        },
      ],
      stepPerformance: [
        {
          stepId: "hot-welcome",
          name: "Welcome & Next Steps",
          sent: 42,
          opened: 39,
          clicked: 28,
          openRate: 0.929,
          clickRate: 0.667,
        },
        {
          stepId: "hot-case-study",
          name: "Relevant Case Study",
          sent: 42,
          opened: 35,
          clicked: 21,
          openRate: 0.833,
          clickRate: 0.5,
        },
        {
          stepId: "hot-meeting-invite",
          name: "Meeting Invitation",
          sent: 42,
          opened: 31,
          clicked: 14,
          openRate: 0.738,
          clickRate: 0.333,
        },
      ],
      dailyPerformance: [
        { date: "2026-05-10", sent: 45, opened: 30, clicked: 15 },
        { date: "2026-05-11", sent: 52, opened: 35, clicked: 18 },
        { date: "2026-05-12", sent: 68, opened: 46, clicked: 23 },
        { date: "2026-05-13", sent: 74, opened: 50, clicked: 25 },
        { date: "2026-05-14", sent: 81, opened: 54, clicked: 27 },
        { date: "2026-05-15", sent: 89, opened: 59, clicked: 30 },
        { date: "2026-05-16", sent: 59, opened: 38, clicked: 18 },
      ],
      topLinks: [
        {
          url: "https://iamaim.ru/calendar",
          clicks: 89,
          uniqueClicks: 67,
          clickRate: 0.143,
        },
        {
          url: "https://iamaim.ru/roi-calculator",
          clicks: 45,
          uniqueClicks: 38,
          clickRate: 0.096,
        },
        {
          url: "https://iamaim.ru/case-studies",
          clicks: 22,
          uniqueClicks: 19,
          clickRate: 0.047,
        },
      ],
      deviceBreakdown: [
        { device: "desktop", count: 187, percentage: 59.9 },
        { device: "mobile", count: 93, percentage: 29.8 },
        { device: "tablet", count: 32, percentage: 10.3 },
      ],
      timeOfDayPerformance: [
        { hour: "09:00", openRate: 0.72, clickRate: 0.38 },
        { hour: "10:00", openRate: 0.68, clickRate: 0.35 },
        { hour: "11:00", openRate: 0.65, clickRate: 0.33 },
        { hour: "12:00", openRate: 0.58, clickRate: 0.29 },
        { hour: "13:00", openRate: 0.54, clickRate: 0.27 },
        { hour: "14:00", openRate: 0.61, clickRate: 0.31 },
        { hour: "15:00", openRate: 0.67, clickRate: 0.34 },
        { hour: "16:00", openRate: 0.71, clickRate: 0.36 },
      ],
    };

    return NextResponse.json({
      success: true,
      data: mockData,
      filters: {
        startDate: startDate || "2026-05-10",
        endDate: endDate || "2026-05-16",
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("[Email Analytics] Error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
