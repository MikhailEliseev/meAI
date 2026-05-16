import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/analytics/leads
 *
 * Get lead analytics data
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
        totalLeads: 156,
        hotLeads: 42,
        warmLeads: 68,
        coldLeads: 46,
        averageScore: 62.5,
        conversionRate: 0.27, // 27%
      },
      scoreDistribution: [
        { range: "0-20", count: 12 },
        { range: "21-40", count: 34 },
        { range: "41-60", count: 48 },
        { range: "61-80", count: 42 },
        { range: "81-100", count: 20 },
      ],
      tierBreakdown: [
        { tier: "hot", count: 42, percentage: 26.9 },
        { tier: "warm", count: 68, percentage: 43.6 },
        { tier: "cold", count: 46, percentage: 29.5 },
      ],
      dailyLeads: [
        { date: "2026-05-10", hot: 3, warm: 5, cold: 2 },
        { date: "2026-05-11", hot: 4, warm: 6, cold: 3 },
        { date: "2026-05-12", hot: 5, warm: 7, cold: 4 },
        { date: "2026-05-13", hot: 6, warm: 8, cold: 5 },
        { date: "2026-05-14", hot: 7, warm: 9, cold: 6 },
        { date: "2026-05-15", hot: 8, warm: 10, cold: 7 },
        { date: "2026-05-16", hot: 9, warm: 11, cold: 8 },
      ],
      topSpecialties: [
        { specialty: "Стоматология", count: 45, avgScore: 72.3 },
        { specialty: "Косметология", count: 32, avgScore: 68.5 },
        { specialty: "Офтальмология", count: 28, avgScore: 65.2 },
        { specialty: "Кардиология", count: 24, avgScore: 71.8 },
        { specialty: "Ортопедия", count: 18, avgScore: 69.4 },
      ],
      conversionFunnel: [
        { stage: "Заявка", count: 156, percentage: 100 },
        { stage: "Квалификация", count: 124, percentage: 79.5 },
        { stage: "Консультация", count: 89, percentage: 57.1 },
        { stage: "Предложение", count: 56, percentage: 35.9 },
        { stage: "Сделка", count: 42, percentage: 26.9 },
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
    console.error("[Lead Analytics] Error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
