import { NextRequest, NextResponse } from "next/server";
import {
  getSequenceByTier,
  buildTemplateData,
  type EmailSequence,
} from "@/lib/email-sequences";
import { type LeadScore } from "@/lib/lead-scoring";
import { scheduleEmailSequence } from "@/lib/email-queue";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface SendSequenceRequest {
  // Lead data
  name: string;
  email: string;
  clinicName: string;
  specialty: string;

  // Lead score
  score: LeadScore;

  // Optional: Start from specific step (default: 0)
  startStep?: number;
}

interface SendSequenceResponse {
  success: boolean;
  sequenceId: string;
  jobIds: string[];
  emailsScheduled: number;
  nextEmailAt?: string;
  error?: string;
}

/**
 * POST /api/email/send-sequence
 *
 * Schedule email sequence for a lead based on their tier
 */
export async function POST(request: NextRequest): Promise<NextResponse<SendSequenceResponse>> {
  try {
    const body: SendSequenceRequest = await request.json();

    // Validate required fields
    if (!body.name || !body.email || !body.clinicName || !body.specialty || !body.score) {
      return NextResponse.json(
        {
          success: false,
          sequenceId: "",
          jobIds: [],
          emailsScheduled: 0,
          error: "Missing required fields",
        },
        { status: 400 }
      );
    }

    // Get sequence by tier
    const sequence = getSequenceByTier(body.score.tier);
    const startStep = body.startStep || 0;

    // Build template data
    const templateData = buildTemplateData(
      body.name,
      body.clinicName,
      body.specialty,
      body.score
    );

    // Schedule email sequence
    const { jobIds, nextEmailAt } = await scheduleEmailSequence(
      sequence,
      body.email,
      templateData,
      startStep
    );

    return NextResponse.json({
      success: true,
      sequenceId: sequence.id,
      jobIds,
      emailsScheduled: jobIds.length,
      nextEmailAt: nextEmailAt?.toISOString(),
    });
  } catch (error) {
    console.error("[Email Sequence] Error:", error);
    return NextResponse.json(
      {
        success: false,
        sequenceId: "",
        jobIds: [],
        emailsScheduled: 0,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/email/send-sequence?email=X
 *
 * Get email sequence status for a lead
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(request.url);
    const email = searchParams.get("email");

    if (!email) {
      return NextResponse.json(
        { error: "Email parameter required" },
        { status: 400 }
      );
    }

    // TODO: Implement sequence status tracking (Phase 2.4)
    // For now, return stub response
    return NextResponse.json({
      email,
      sequences: [],
      message: "Sequence tracking not yet implemented",
    });
  } catch (error) {
    console.error("[Email Sequence] Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}
