import { NextRequest } from "next/server";

const HERMES_URL = process.env.HERMES_URL || "http://hermes:8000";
const HERMES_API_KEY = process.env.HERMES_API_KEY || "";
const HERMES_TIMEOUT_MS = 60000; // 60s for full audit + streaming

export async function POST(req: NextRequest) {
  const body = await req.json();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), HERMES_TIMEOUT_MS);

  try {
    const response = await fetch(`${HERMES_URL}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${HERMES_API_KEY}`,
      },
      body: JSON.stringify({
        message: body.message,
        session_id: body.session_id,
        mode: body.mode || "PRESALE",
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new Response(
        JSON.stringify({ error: "Hermes stream error", detail: errorText }),
        { status: 502, headers: { "Content-Type": "application/json" } },
      );
    }

    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    if (message.includes("abort")) {
      return new Response(
        JSON.stringify({ error: "Stream timeout", detail: "Hermes took too long to respond" }),
        { status: 504, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response(
      JSON.stringify({ error: "Stream proxy error", detail: message }),
      { status: 502, headers: { "Content-Type": "application/json" } },
    );
  } finally {
    clearTimeout(timeoutId);
  }
}
