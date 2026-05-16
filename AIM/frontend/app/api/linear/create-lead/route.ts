import { NextRequest, NextResponse } from "next/server";
import { createLinearClient, type CreateLeadIssueInput } from "@/lib/linear-client";
import { type LeadScore } from "@/lib/lead-scoring";

/**
 * POST /api/linear/create-lead
 *
 * Create Linear issue for a new lead
 *
 * Request body: CreateLeadIssueInput
 * Response: LinearIssue
 */
export async function POST(request: NextRequest) {
  try {
    const input: CreateLeadIssueInput = await request.json();

    // Validate required fields
    if (!input.name || !input.email || !input.clinicName || !input.specialty || !input.score) {
      return NextResponse.json(
        { error: "Missing required fields: name, email, clinicName, specialty, score" },
        { status: 400 }
      );
    }

    // Create Linear client
    const linearClient = createLinearClient();

    // Create issue
    const issue = await linearClient.createLeadIssue(input);

    // Log success
    console.log("[Linear] Lead issue created:", {
      issueId: issue.identifier,
      email: input.email,
      tier: input.score.tier,
      score: input.score.score,
      url: issue.url,
    });

    return NextResponse.json({
      success: true,
      issue: {
        id: issue.identifier,
        url: issue.url,
        priority: issue.priority,
        tier: input.score.tier,
      },
    });
  } catch (error) {
    console.error("[Linear] Failed to create lead issue:", error);

    // Return error but don't fail the entire flow
    // Lead was already saved via /api/contact
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Failed to create Linear issue",
      },
      { status: 500 }
    );
  }
}
