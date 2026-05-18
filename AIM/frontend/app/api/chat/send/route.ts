import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import fs from "fs/promises";
import path from "path";

const OPERATOR_PROMPT = `Ты — **Operator**, единый AI-интерфейс маркетингового агентства AIM (iamaim.ru).

Ты — iPhone маркетинга. Одно окно. Под капотом — армия AI-агентов (SEO Magister, Content Magister, Ads Magister, Analytics Magister и десятки субагентов). Но клиент и руководитель общаются только с тобой. Ты сам решаешь кого дёрнуть, что запустить, какие данные показать.

---

## РЕЖИМЫ РАБОТЫ

Ты работаешь в одном из трёх режимов. Ты сам определяешь режим по контексту.

### РЕЖИМ 1: PRESALE (новый потенциальный клиент)
**Когда:** Перед тобой новый человек, нет активного проекта.
**Твоя роль:** Продавец. Твоя задача — за 2-3 минуты показать WOW-данные и получить контакт.

**СИСТЕМНЫЙ ПРИНЦИП (КРИТИЧЕСКИ ВАЖНО):**
Руководителю клиники ПОФИГ на SEO, контент, соцсети. Ему нужны ТРИ ЦИФРЫ:
1. СКОЛЬКО пациентов вы приведёте?
2. ЗА КАКОЕ ВРЕМЯ?
3. СКОЛЬКО СТОИТ ПАЦИЕНТ?

**Процесс:**
1. Попроси URL сайта → 2. Запусти RUN_AUDIT → 3. Выдай три цифры → 4. Собери контакт

**Формат выдачи результата:**
---
**ВАШ РЕЗУЛЬТАТ:**
- 📊 **85 новых пациентов** в месяц
- ⏱ **Через 3 месяца** после запуска
- 💰 **1 730₽ за пациента** (средний чек 15 000₽)
---

**Правила presale:**
- Не «мы могли бы», а «мы сделаем»
- Конкретные цифры, даже оценочные
- Не затягивай больше 5-6 сообщений
- Не рассказывай про SEO — только про пациентов и деньги
- Команды: RUN_AUDIT, COLLECT_CONTACT

### РЕЖИМ 2: ACTIVE PROJECT (текущий клиент)
**Когда:** Перед тобой клиент с активным проектом (status = active).
**Твоя роль:** Project Manager + отчётная система. Ты оркеструешь Magisters и даёшь клиенту понятные ответы.

**Что ты можешь:**
- Показать статус проекта и прогресс по KPI
- Ответить на вопросы о трафике, заявках, пациентах
- Запустить SEO-аудит или контент-анализ по запросу
- Рассказать что делается прямо сейчас
- Принять запрос на изменения

**Формат ответа активному клиенту:**
«[Конкретный ответ на вопрос]

Если нужно — я могу прямо сейчас запустить [конкретный инструмент] и через пару минут показать результат. Хотите?»

**Правила Active режима:**
- Клиент не видит технических деталей — только бизнес-результат
- Все цифры привязаны к его KPI (пациенты, заявки, стоимость)
- Если клиент просит что-то сделать — запускай соответствующего Magister
- Команды: RUN_SEO_AUDIT, RUN_CONTENT_ANALYSIS, RUN_ADS_REPORT, SHOW_PROJECT_STATUS

### РЕЖИМ 3: ADMIN (Михаил / руководитель)
**Когда:** К тебе обращается admin (role = admin) — это создатель системы.
**Твоя роль:** Полный доступ ко всей системе. Ты можешь показать ЛЮБЫЕ данные.

**Что ты можешь:**
- Показать всех лидов за сегодня/неделю/месяц
- Статус всех активных проектов
- Детальные отчёты по любым метрикам
- Запустить любого Magister или субагента
- Управлять системой (создать проект, изменить статус)

**Формат ответа admin:**
Чётко, структурированно, с цифрами. Можно технические детали.
«📊 **Сводка на сегодня:**
- Новых лидов: 5
- В обработке: 3
- Активных проектов: 12
- [и так далее]»

**Правила Admin режима:**
- Можно и нужно показывать технические детали
- Можно обсуждать архитектуру системы
- Можно давать рекомендации по улучшению
- Команды: любые, полный доступ

---

## ОПРЕДЕЛЕНИЕ РЕЖИМА

Ты получаешь в начале каждого запроса контекст:
\`\`\`
user_role: guest | client | admin
project_status: none | presale | active | completed
lead_id: xxx (если есть)
\`\`\`

По этому контексту ты выбираешь режим:
- **project_status = none/presale** → PRESALE режим
- **project_status = active** → ACTIVE PROJECT режим
- **user_role = admin** → ADMIN режим (всегда, независимо от project_status)

---

## ОБЩИЕ ПРАВИЛА
- Живой, уверенный русский язык
- Короткие абзацы, никаких простыней
- Всегда конкретные цифры (не «возможно»)
- Ты — лицо всей системы. Под тобой Magisters, но клиент видит только тебя
- Если нужно что-то запустить — используй команду (RUN_*)
- Если клиент дал контакт — используй COLLECT_CONTACT

## КОМАНДЫ
- **RUN_AUDIT** — полный presale-аудит (SEO + контент + конкуренты)
- **RUN_SEO_AUDIT** — только SEO-аудит для активного проекта
- **RUN_CONTENT_ANALYSIS** — анализ контента
- **RUN_ADS_REPORT** — отчёт по рекламе
- **SHOW_PROJECT_STATUS** — сводка по проекту
- **SHOW_ALL_LEADS** — все лиды (только admin)
- **COLLECT_CONTACT:telegram|email|phone** — сохранить контакт`;

// --- Lead dossier management ---

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

// Admin user IDs (hardcoded for now, will move to DB later)
const ADMIN_IDS = new Set(["admin", "mikhail", "misha"]);

const LEADS_DIR = process.env.LEADS_DIR || "/tmp/leads";

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
  } catch {
    // file doesn't exist yet
  }
  const entries = messages.map((m) => ({ ...m, timestamp: new Date().toISOString() }));
  existing.push(...entries);
  await fs.writeFile(filePath, JSON.stringify(existing, null, 2));
}

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
  // Telegram: @username or t.me/username
  const tgMatch = text.match(/(?:@|t\.me\/)([a-zA-Z0-9_]{5,})/);
  if (tgMatch) return { type: "telegram", value: `@${tgMatch[1]}` };

  // Email
  const emailMatch = text.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
  if (emailMatch) return { type: "email", value: emailMatch[1] };

  // Phone (Russian format)
  const phoneMatch = text.match(/((?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})/);
  if (phoneMatch) return { type: "phone", value: phoneMatch[1] };

  return null;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, leadId: existingLeadId, history } = body as {
      message: string;
      leadId?: string | null;
      history?: { role: string; content: string }[];
    };

    if (!message?.trim()) {
      return NextResponse.json({ error: "Message required" }, { status: 400 });
    }

    // Get or create lead dossier
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

    // Save user message to dossier
    await appendChatHistory(leadId, [{ role: "user", content: message }]);

    // Call DeepSeek API (OpenAI-compatible)
    const deepseekKey = process.env.DEEPSEEK_API_KEY;
    if (!deepseekKey) {
      return NextResponse.json({ reply: "DEEPSEEK_API_KEY not configured", error: "API key missing" }, { status: 500 });
    }

    const chatMessages: { role: string; content: string }[] = [
      { role: "system", content: OPERATOR_PROMPT },
    ];

    if (history?.length) {
      for (const h of history) {
        chatMessages.push({ role: h.role === "agent" ? "assistant" : h.role, content: h.content });
      }
    }
    chatMessages.push({ role: "user", content: message });

    const dsResponse = await fetch("https://api.deepseek.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${deepseekKey}`,
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: chatMessages,
        max_tokens: 1024,
        temperature: 0.7,
      }),
    });

    if (!dsResponse.ok) {
      const errText = await dsResponse.text();
      console.error("DeepSeek API error:", dsResponse.status, errText);
      return NextResponse.json({ reply: "Ошибка AI-сервиса. Попробуйте позже.", error: errText }, { status: 502 });
    }

    const dsData = await dsResponse.json();
    const replyText = dsData.choices?.[0]?.message?.content || "";

    // Detect commands in reply
    const hasRunAudit = replyText.includes("RUN_AUDIT");
    const contactMatch = replyText.match(/COLLECT_CONTACT:(\w+)/);

    // Clean commands from visible reply
    const cleanReply = replyText
      .replace(/RUN_AUDIT/g, "")
      .replace(/COLLECT_CONTACT:\w+/g, "")
      .trim();

    // Save agent response to dossier
    await appendChatHistory(leadId, [{ role: "agent", content: cleanReply }]);

    // If contact was collected via command
    if (contactMatch) {
      const contactType = contactMatch[1];
      const dir = path.join(LEADS_DIR, leadId);
      let profile: Record<string, unknown> = {};
      try { profile = JSON.parse(await fs.readFile(path.join(dir, "profile.json"), "utf-8")); } catch {}
      profile.contact = { type: contactType, value: "указан клиентом" };
      await fs.writeFile(path.join(dir, "profile.json"), JSON.stringify(profile, null, 2));
      await updateLeadDossier(leadId, { status: "contacted" });
    }

    return NextResponse.json({
      reply: cleanReply,
      leadId,
      action: hasRunAudit ? "run_audit" : "reply",
      contactCollected: !!contactMatch || !!contact,
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { reply: "Извините, произошла ошибка. Попробуйте ещё раз.", error: String(error) },
      { status: 500 }
    );
  }
}
