import { NextRequest, NextResponse } from "next/server";
import { calculateLeadScore, enrichLeadData, type LeadData } from "@/lib/lead-scoring";

/**
 * POST /api/lead-score
 *
 * Calculate lead score for a given lead
 *
 * Request body: LeadData
 * Response: LeadScore
 */
export async function POST(request: NextRequest) {
  try {
    const leadData: LeadData = await request.json();

    // Validate required fields
    if (!leadData.name || !leadData.email || !leadData.clinicName || !leadData.specialty) {
      return NextResponse.json(
        { error: "Missing required fields: name, email, clinicName, specialty" },
        { status: 400 }
      );
    }

    // Enrich lead data (stub for now, implement in Phase 2.2)
    const enrichedLead = await enrichLeadData(leadData);

    // Calculate score
    const score = calculateLeadScore(enrichedLead);

    // Log score for analytics (TODO: save to database in Phase 7.5)
    console.log("[Lead Score]", {
      email: leadData.email,
      score: score.score,
      tier: score.tier,
      confidence: score.confidence,
      timestamp: new Date().toISOString(),
    });

    return NextResponse.json(score);
  } catch (error) {
    console.error("[Lead Score Error]", error);
    return NextResponse.json(
      { error: "Failed to calculate lead score" },
      { status: 500 }
    );
  }
}

/**
 * GET /api/lead-score?email=test@example.com
 *
 * Get lead score history for a given email (stub for now)
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const email = searchParams.get("email");

    if (!email) {
      return NextResponse.json(
        { error: "Missing required parameter: email" },
        { status: 400 }
      );
    }

    // TODO: Implement in Phase 7.5 (fetch from database)
    // For now, return empty history
    return NextResponse.json({
      email,
      history: [],
      message: "Score history will be available in Phase 7.5",
    });
  } catch (error) {
    console.error("[Lead Score History Error]", error);
    return NextResponse.json(
      { error: "Failed to fetch lead score history" },
      { status: 500 }
    );
  }
}
