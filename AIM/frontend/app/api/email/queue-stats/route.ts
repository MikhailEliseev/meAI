import { NextRequest, NextResponse } from "next/server";
import { getQueueStats, cleanupOldJobs } from "@/lib/email-queue";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/email/queue-stats
 *
 * Get email queue statistics
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const stats = await getQueueStats();

    return NextResponse.json({
      success: true,
      stats,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("[Queue Stats] Error:", error);
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
 * POST /api/email/queue-stats
 *
 * Cleanup old jobs
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { action } = body;

    if (action === "cleanup") {
      await cleanupOldJobs();

      return NextResponse.json({
        success: true,
        message: "Old jobs cleaned up successfully",
      });
    }

    return NextResponse.json(
      { success: false, error: "Invalid action" },
      { status: 400 }
    );
  } catch (error) {
    console.error("[Queue Stats] Error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
