import { NextRequest, NextResponse } from "next/server";
import {
  pauseEmailSequence,
  resumeEmailSequence,
  handleUnsubscribe,
  getSequenceStatus,
} from "@/lib/email-queue";
import { getSequenceByTier, buildTemplateData } from "@/lib/email-sequences";
import { type LeadScore } from "@/lib/lead-scoring";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * POST /api/email/manage-sequence
 *
 * Manage email sequences (pause, resume, unsubscribe)
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { action, leadEmail, sequenceId, leadData } = body;

    if (!action || !leadEmail) {
      return NextResponse.json(
        { success: false, error: "Missing required fields: action, leadEmail" },
        { status: 400 }
      );
    }

    switch (action) {
      case "pause": {
        if (!sequenceId) {
          return NextResponse.json(
            { success: false, error: "Missing sequenceId for pause action" },
            { status: 400 }
          );
        }

        const pausedCount = await pauseEmailSequence(leadEmail, sequenceId);
        return NextResponse.json({
          success: true,
          action: "pause",
          pausedCount,
          message: `Paused ${pausedCount} pending emails`,
        });
      }

      case "resume": {
        if (!sequenceId || !leadData) {
          return NextResponse.json(
            { success: false, error: "Missing sequenceId or leadData for resume action" },
            { status: 400 }
          );
        }

        const { name, clinicName, specialty, score, currentStep } = leadData;
        const sequence = getSequenceByTier(score.tier);
        const templateData = buildTemplateData(name, clinicName, specialty, score);

        const { jobIds, nextEmailAt } = await resumeEmailSequence(
          sequence,
          leadEmail,
          templateData,
          currentStep || 0
        );

        return NextResponse.json({
          success: true,
          action: "resume",
          jobIds,
          emailsScheduled: jobIds.length,
          nextEmailAt: nextEmailAt?.toISOString(),
        });
      }

      case "unsubscribe": {
        await handleUnsubscribe(leadEmail);
        return NextResponse.json({
          success: true,
          action: "unsubscribe",
          message: "Successfully unsubscribed from all email sequences",
        });
      }

      default:
        return NextResponse.json(
          { success: false, error: `Unknown action: ${action}` },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error("[Manage Sequence] Error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/email/manage-sequence?email=X&sequenceId=Y
 *
 * Get sequence status for a lead
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(request.url);
    const leadEmail = searchParams.get("email");
    const sequenceId = searchParams.get("sequenceId");

    if (!leadEmail || !sequenceId) {
      return NextResponse.json(
        { error: "Missing required parameters: email, sequenceId" },
        { status: 400 }
      );
    }

    const status = await getSequenceStatus(leadEmail, sequenceId);

    if (!status) {
      return NextResponse.json(
        { error: "Sequence not found" },
        { status: 404 }
      );
    }

    return NextResponse.json(status);
  } catch (error) {
    console.error("[Manage Sequence] Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}
