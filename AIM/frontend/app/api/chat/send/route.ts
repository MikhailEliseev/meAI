import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import fs from "fs/promises";
import path from "path";

// ── Configuration ──────────────────────────────────────────────
const HERMES_URL = process.env.HERMES_URL || "http://hermes:8000";
const HERMES_API_KEY = process.env.HERMES_API_KEY || "";
const HERMES_TIMEOUT_MS = 30000;  // D-34: 30s timeout
const RETRY_DELAYS_MS = [5000, 15000, 45000];  // D-35: 5s, 15s, 45s
const LEADS_DIR = process.env.LEADS_DIR || "/opt/data/leads";  // S-15-07

const ADMIN_IDS = new Set(["admin", "mikhail", "misha", "mikhaileliseev"]);

// ── Types ──────────────────────────────────────────────────────
interface LeadDossier {
  leadId: string;
  createdAt: string;
  profile: {
    website?: string;
    clinicName?: string;
    specialty?: string;
    city?: string;
    contact?: { type: string; value: string };
  };
  messages: { role: string; content: string; timestamp: string }[];
  auditResult?: Record<string, unknown>;
  status: "new" | "qualified" | "audited" | "contacted" | "active" | "completed" | "closed";
}

// ── Lead Dossier Management ────────────────────────────────────
async function ensureLeadDir(leadId: string): Promise<string> {
  const dir = path.join(LEADS_DIR, leadId);
  await fs.mkdir(dir, { recursive: true });
  return dir;
}

async function createLeadDossier(website?: string): Promise<LeadDossier> {
  const leadId = `lead-${Date.now()}-${randomUUID().slice(0, 6)}`;
  const dossier: LeadDossier = {
    leadId,
    createdAt: new Date().toISOString(),
    profile: { website },
    messages: [],
    status: website ? "qualified" : "new",
  };
  const dir = await ensureLeadDir(leadId);
  await fs.writeFile(path.join(dir, "profile.json"), JSON.stringify(dossier.profile, null, 2));
  await fs.writeFile(path.join(dir, "status.json"), JSON.stringify({ status: dossier.status, updatedAt: dossier.createdAt }, null, 2));
  await fs.writeFile(path.join(dir, "chat_history.json"), "[]");
  return dossier;
}

async function updateLeadDossier(leadId: string, updates: Partial<LeadDossier>) {
  const dir = path.join(LEADS_DIR, leadId);
  if (updates.profile) {
    await fs.writeFile(path.join(dir, "profile.json"), JSON.stringify(updates.profile, null, 2));
  }
  if (updates.status) {
    await fs.writeFile(path.join(dir, "status.json"), JSON.stringify({ status: updates.status, updatedAt: new Date().toISOString() }, null, 2));
  }
}

async function appendChatHistory(leadId: string, messages: { role: string; content: string }[]) {
  const dir = path.join(LEADS_DIR, leadId);
  const filePath = path.join(dir, "chat_history.json");
  let existing: unknown[] = [];
  try {
    const raw = await fs.readFile(filePath, "utf-8");
    existing = JSON.parse(raw);
  } catch {}
  const entries = messages.map((m) => ({ ...m, timestamp: new Date().toISOString() }));
  existing.push(...entries);
  await fs.writeFile(filePath, JSON.stringify(existing, null, 2));
}

// ── Helpers ────────────────────────────────────────────────────
function extractWebsite(text: string): string | null {
  const urlPattern = /(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:\/[^\s]*)?)/gi;
  const matches = text.match(urlPattern);
  if (matches && matches.length > 0) {
    let url = matches[0];
    if (!url.startsWith("http")) url = "https://" + url;
    return url;
  }
  return null;
}

function extractContact(text: string): { type: string; value: string } | null {
  const tgMatch = text.match(/(?:@|t\.me\/)([a-zA-Z0-9_]{5,})/);
  if (tgMatch) return { type: "telegram", value: `@${tgMatch[1]}` };
  const emailMatch = text.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
  if (emailMatch) return { type: "email", value: emailMatch[1] };
  const phoneMatch = text.match(/((?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})/);
  if (phoneMatch) return { type: "phone", value: phoneMatch[1] };
  return null;
}

// ── Mode Determination ─────────────────────────────────────────
async function determineClientMode(
  request: NextRequest,
  leadId: string | null,
): Promise<string> {
  // 1. Admin check — x-auth-role header OR username/email match
  const cookie = request.cookies.get("next-auth.session-token");
  if (cookie) {
    try {
      const authHeader = request.headers.get("x-auth-role");
      if (authHeader === "admin") return "ADMIN";
      // Check x-auth-username header (set by NextAuth middleware)
      const username = request.headers.get("x-auth-username");
      if (username && ADMIN_IDS.has(username.toLowerCase())) return "ADMIN";
      const email = request.headers.get("x-auth-email");
      if (email && ADMIN_IDS.has(email.split("@")[0]?.toLowerCase())) return "ADMIN";
    } catch {}
  }

  // 2. Active project check
  if (leadId) {
    try {
      const statusPath = path.join(LEADS_DIR, leadId, "status.json");
      const statusRaw = await fs.readFile(statusPath, "utf-8");
      const status = JSON.parse(statusRaw);
      if (status.status === "active") return "ACTIVE";
    } catch {}
  }

  return "PRESALE";
}

// ── Hermes Proxy ───────────────────────────────────────────────
async function callHermes(
  message: string,
  sessionId: string | null,
  mode: string,
): Promise<{ reply: string; session_id: string | null }> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), HERMES_TIMEOUT_MS);

      const response = await fetch(`${HERMES_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${HERMES_API_KEY}`,
          "X-Client-Mode": mode,
        },
        body: JSON.stringify({
          message,
          session_id: sessionId || null,
          mode,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return {
          reply: data.reply || data.response || "",
          session_id: data.session_id || null,
        };
      }

      if (response.status === 401 || response.status === 403) {
        throw new Error(`Hermes auth error: ${response.status}`);
      }

      lastError = new Error(`Hermes returned ${response.status}`);
    } catch (error: any) {
      lastError = error;
      if (error.name === "AbortError") {
        lastError = new Error("Hermes request timed out");
      }
    }

    if (attempt < RETRY_DELAYS_MS.length) {
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAYS_MS[attempt]));
    }
  }

  throw lastError || new Error("All Hermes retries exhausted");
}

// ── Redis Queue Fallback ───────────────────────────────────────
async function enqueueMessage(
  message: string,
  sessionId: string | null,
  leadId: string,
  mode: string,
): Promise<void> {
  const REDIS_URL = process.env.REDIS_URL || "redis://redis:6379/0";

  try {
    const Redis = (await import("ioredis")).default;
    const redis = new Redis(REDIS_URL, { lazyConnect: true, maxRetriesPerRequest: 1 });
    await redis.connect();

    const queueItem = JSON.stringify({
      message,
      session_id: sessionId,
      lead_id: leadId,
      mode,
      queued_at: new Date().toISOString(),
      retries: 0,
    });
    await redis.lpush("hermes:message_queue", queueItem);
    await redis.quit();
  } catch (redisError) {
    console.error("Failed to enqueue message in Redis:", redisError);
    const fallbackPath = path.join(LEADS_DIR, leadId, "pending_messages.json");
    try {
      let pending: unknown[] = [];
      try {
        const raw = await fs.readFile(fallbackPath, "utf-8");
        pending = JSON.parse(raw);
      } catch {}
      pending.push({ message, session_id: sessionId, mode, queued_at: new Date().toISOString() });
      await fs.writeFile(fallbackPath, JSON.stringify(pending, null, 2));
    } catch (fsError) {
      console.error("Failed to save pending message to filesystem:", fsError);
    }
  }
}

// ── POST Handler ───────────────────────────────────────────────
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, leadId: existingLeadId } = body as {
      message: string;
      leadId?: string | null;
      history?: { role: string; content: string }[];
    };

    if (!message?.trim()) {
      return NextResponse.json({ error: "Message required" }, { status: 400 });
    }

    let leadId = existingLeadId;
    const website = extractWebsite(message);
    const contact = extractContact(message);

    if (!leadId) {
      const dossier = await createLeadDossier(website || undefined);
      leadId = dossier.leadId;
    } else if (website) {
      const dir = path.join(LEADS_DIR, leadId);
      let profile: Record<string, unknown> = {};
      try { profile = JSON.parse(await fs.readFile(path.join(dir, "profile.json"), "utf-8")); } catch {}
      profile.website = website;
      await fs.writeFile(path.join(dir, "profile.json"), JSON.stringify(profile, null, 2));
      await updateLeadDossier(leadId, { status: "qualified" });
    }

    if (contact) {
      const dir = path.join(LEADS_DIR, leadId);
      let profile: Record<string, unknown> = {};
      try { profile = JSON.parse(await fs.readFile(path.join(dir, "profile.json"), "utf-8")); } catch {}
      profile.contact = contact;
      await fs.writeFile(path.join(dir, "profile.json"), JSON.stringify(profile, null, 2));
      await updateLeadDossier(leadId, { status: "contacted" });
    }

    await appendChatHistory(leadId, [{ role: "user", content: message }]);

    const mode = await determineClientMode(request, leadId);

    try {
      const result = await callHermes(message, leadId, mode);

      await appendChatHistory(leadId, [{ role: "agent", content: result.reply }]);

      return NextResponse.json({
        reply: result.reply,
        leadId,
        sessionId: result.session_id || leadId,
      });
    } catch (hermesError: any) {
      console.error("Hermes unavailable, enqueuing message:", hermesError.message);

      await enqueueMessage(message, leadId, leadId, mode);

      return NextResponse.json({
        reply: "Оператор скоро ответит. Ваше сообщение принято и будет обработано в ближайшее время.",
        leadId,
        queued: true,
      });
    }
  } catch (error: any) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { reply: "Извините, произошла ошибка. Попробуйте ещё раз.", error: String(error) },
      { status: 500 }
    );
  }
}
