import { NextRequest, NextResponse } from "next/server";
import {
  getSequenceByTier,
  buildTemplateData,
  type EmailSequence,
  type LeadScore,
} from "@/lib/email-sequences";
import { sendTemplateEmail } from "@/lib/sendgrid-templates";

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
  emailsSent: number;
  nextEmailAt?: string;
  error?: string;
}

/**
 * POST /api/email/send-sequence
 *
 * Trigger email sequence for a lead based on their tier
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
          emailsSent: 0,
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

    // Send first email immediately
    const firstStep = sequence.steps[startStep];
    if (!firstStep) {
      return NextResponse.json(
        {
          success: false,
          sequenceId: sequence.id,
          emailsSent: 0,
          error: "Invalid start step",
        },
        { status: 400 }
      );
    }

    const result = await sendTemplateEmail({
      to: body.email,
      templateId: firstStep.templateId,
      dynamicTemplateData: templateData,
    });

    if (!result.success) {
      return NextResponse.json(
        {
          success: false,
          sequenceId: sequence.id,
          emailsSent: 0,
          error: result.error || "Failed to send email",
        },
        { status: 500 }
      );
    }

    // Schedule remaining emails
    // TODO: Implement email scheduling (Phase 2.4)
    // For now, we only send the first email
    // Future: Use a job queue (BullMQ, Inngest, etc.) to schedule delayed emails

    // Calculate next email time
    const nextStep = sequence.steps[startStep + 1];
    const nextEmailAt = nextStep
      ? new Date(Date.now() + nextStep.delayMinutes * 60 * 1000).toISOString()
      : undefined;

    return NextResponse.json({
      success: true,
      sequenceId: sequence.id,
      emailsSent: 1,
      nextEmailAt,
    });
  } catch (error) {
    console.error("[Email Sequence] Error:", error);
    return NextResponse.json(
      {
        success: false,
        sequenceId: "",
        emailsSent: 0,
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
