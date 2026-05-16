import { NextRequest, NextResponse } from "next/server";
import { trackEmailOpened, trackEmailClicked } from "@/lib/email-queue";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/email/track?event=open&email=X&sequenceId=Y&stepId=Z
 *
 * Track email open event (1x1 pixel)
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(request.url);
    const event = searchParams.get("event");
    const leadEmail = searchParams.get("email");
    const sequenceId = searchParams.get("sequenceId");
    const stepId = searchParams.get("stepId");

    if (!event || !leadEmail || !sequenceId || !stepId) {
      return new NextResponse("Missing parameters", { status: 400 });
    }

    if (event === "open") {
      await trackEmailOpened(leadEmail, sequenceId, stepId);

      // Return 1x1 transparent pixel
      const pixel = Buffer.from(
        "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
        "base64"
      );

      return new NextResponse(pixel, {
        status: 200,
        headers: {
          "Content-Type": "image/gif",
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
          "Pragma": "no-cache",
          "Expires": "0",
        },
      });
    }

    return new NextResponse("Invalid event type", { status: 400 });
  } catch (error) {
    console.error("[Email Tracking] Error:", error);
    return new NextResponse("Internal Server Error", { status: 500 });
  }
}

/**
 * POST /api/email/track
 *
 * Track email click event
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { event, leadEmail, sequenceId, stepId, url } = body;

    if (!event || !leadEmail || !sequenceId || !stepId) {
      return NextResponse.json(
        { success: false, error: "Missing required fields" },
        { status: 400 }
      );
    }

    if (event === "click") {
      if (!url) {
        return NextResponse.json(
          { success: false, error: "Missing url for click event" },
          { status: 400 }
        );
      }

      await trackEmailClicked(leadEmail, sequenceId, stepId, url);

      return NextResponse.json({
        success: true,
        message: "Click tracked successfully",
      });
    }

    return NextResponse.json(
      { success: false, error: "Invalid event type" },
      { status: 400 }
    );
  } catch (error) {
    console.error("[Email Tracking] Error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
