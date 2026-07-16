# Phase 9: Chat Pro — Website Chat UX Overhaul - Discussion Log

**Date:** 2026-06-27
**Participants:** User (Mikhail), Claude
**Mode:** --auto (user sleeping)
**Duration:** ~25 minutes

---

## Discussion Flow

### 1. Initial Request

**User:** "ssh aim ключись найди чат на сайте iamaim.ru должен быть подключен к гермесу -я хочу переделать логику выдачи инфорсации"

**Context:** User wants to redesign how Hermes delivers information to clients through the website chat.

**Action:** Connected to Polish server, found chat at `/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat.html`.

**Key finding:** Current implementation only handles `content` events from SSE stream, ignores `tool-progress` events that backend already sends.

```javascript
if (data.type === 'content' && data.text) {
    assistantMessage += data.text;
}
// tool-progress events are NOT handled
```

---

### 2. Phase Addition

**User:** "добавь как Phase 9 в конец roadmap"

**Action:** Added Phase 9 to `.planning/ROADMAP.md` after Phase 8 with:
- Title: "Chat Pro: Website chat UX overhaul"
- Success criteria placeholders
- Updated progress table and execution order

**Result:** Phase 9 now officially in project roadmap.

---

### 3. Requirements Breakdown

**User provided 5 areas:**

1. **Стиль отображения**: "просто статус сообщения в чате для клиента чтобы он видел прогресс - как стриминг в телеграме там гермес это делает"
   - **Translation:** Progress display like Telegram streaming — floating status message that updates
   - **Key insight:** User explicitly referenced Telegram pattern from `main.py:66-84` with `_telegram_progress_lines` accumulator

2. **Промежуточные комментарии**: "после каждого инструмента - провел сбор данных - показал клиенту первые находки и комент дал"
   - **Translation:** After every tool execution, show findings + wow-commentary
   - **Key insight:** "Ого, ваша главная страница не оптимизирована" / "У конкурента доктор с 500K подписчиков"

3. **Финальный отчет**: "формирует он его криво... полным крахом верстки"
   - **Translation:** Fix HTML report generation — current `generate_html_report.py` breaks layout completely
   - **Key insight:** Need canonical template approach — LLM generates content, Python assembles HTML from fixed structure

4. **Сбор контакта**: "в чате - только в диалоге с клиентлм - гермес должен быть как живой челвоке и запрашивать контакты нативно"
   - **Translation:** Native conversational contact collection, not forms
   - **Key insight:** Tool `collect_contact` already exists, just needs dialog flow integration

5. **Продавец услуг**: "гермес должен знать что умеет aim и мы кожаные и должен сказать 0 ого у вас тут дыры в том и этом - мы можем предложить решить это с помощью наших инструментов за такие то деньги"
   - **Translation:** Services sales assistant — LLM knows AIM capabilities, matches findings to services with pricing
   - **Key insight:** Need `/opt/data/services.md` catalogue, semantic matching logic

---

### 4. Gray Areas Identification

**Claude presented 4 gray areas** for discussion:

#### Area 1: Progress Display Pattern
- **Question:** Telegram-style (floating single message) vs separate messages per stage?
- **User answer:** "как стриминг в телеграме" (like Telegram streaming)
- **Decision locked:** D-01 through D-06 — floating status, stage/message/competitor hierarchy

#### Area 2: Wow-Commentary Logic
- **Question:** LLM-generated after every tool? Tone? Severity levels?
- **User answer:** Implicit approval through "после каждого инструмента"
- **Decision locked:** D-07 through D-13 — LLM generates insights, business language, severity mapping (info/warning/critical)

#### Area 3: Report Page Generation
- **Question:** How to fix layout breakdown? Template approach? WordPress publishing?
- **User answer:** Implicit — "полным крахом верстки" signals urgency
- **Decision locked:** D-14 through D-20 — canonical template from design-showcase-dual-theme.html, WordPress REST API publish

#### Area 4: Services Sales Assistant
- **Question:** Services catalogue location? Matching algorithm? Offer timing?
- **User answer:** "гермес должен знать что умеет aim" (Hermes must know AIM capabilities)
- **Decision locked:** D-28 through D-34 — services.md catalogue, semantic matching, consultative tone, post-analysis timing

---

### 5. Final Approval

**User:** "да я вроде развернуто ответил - дополни сам исходя из моих ответов еще более проработаеннеее и развернуто каждый из 4 пунктов"

**Claude:** Expanded each area with 7-10 detailed decisions per area, covering:
- Technical implementation patterns
- User experience flows
- Integration points with existing code
- Error handling
- Visual design constraints

**User:** "давай" (let's go)

**Interpretation:** Approval to proceed with writing CONTEXT.md.

---

## Key Decisions Summary

### Progress Streaming (D-01 to D-06)
- Telegram-style floating status
- Stage → Message → Competitor hierarchy
- Backend already sends events, frontend needs handling
- Visual indicators: spinner + checkmark
- Non-blocking placement in chat

### Wow-Commentary (D-07 to D-13)
- LLM-generated after each tool success
- New SSE event: `{"type": "wow-comment", "insight": "...", "severity": "..."}`
- Business language (INT-03 from Phase 5)
- Severity levels: info (✅), warning (📍), critical (🔴)
- Tone: marketing manager, not robot

### Report Fix (D-14 to D-20)
- Canonical template approach (LLM = content, Python = assembly)
- Template from design-showcase-dual-theme.html
- WordPress REST API publish: `/wp-json/wp/v2/pages`
- 10 sections from ИПХиК reference
- SSE event: `{"type": "report-ready", "url": "..."}`

### Contact + Sales (D-21 to D-34)
- Conversational dialog flow (no forms)
- Existing `collect_contact` tool
- Timing: after analysis, before final offer
- Services catalogue: `/opt/data/services.md`
- Semantic matching: findings → relevant AIM services
- Consultative offer with 3-5 services + prices
- CTA: "Обсудить с менеджером" → `escalate_to_manager`

---

## Implementation Split (D-35)

**4 plans:**
1. **09-01:** Progress streaming UI (frontend + SSE)
2. **09-02:** Wow-commentary generation (LLM prompt + new event type)
3. **09-03:** Report template + WordPress publishing
4. **09-04:** Contact collection + services sales assistant

---

## Deferred to Backlog

- A/B testing different UX approaches
- Multi-language report support (English)
- Voice input in web chat
- Real-time report preview during generation
- Niche-specific report templates
- CRM integration for auto-deal creation

---

## Canonical References Identified (10 files)

### Design & Frontend
1. `/var/www/iamaim.ru/wp-content/themes/aim-theme/design-showcase-dual-theme.html` — design canon
2. `/var/www/iamaim.ru/wp-content/themes/aim-theme/theme.css` — CSS variables
3. `/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat.html` — current chat

### Backend
4. `AIM/hermes/app/main.py` — SSE streaming, push_tool_progress()
5. `AIM/hermes/app/agent_wrapper.py` — AIAgent lifecycle
6. `AIM/hermes/app/agent_wrapper_optimized.py` — mode prompts
7. `AIM/hermes/app/tools/collect_contact.py` — contact collection tool

### Reports
8. `AIM/hermes/scripts/generate_html_report.py` — broken generator (needs fix)
9. `/Users/mikhaileliseev/Downloads/ИПХиК (2).html` — reference report

### Business
10. `/opt/data/services.md` — AIM services catalogue (create if missing)

---

## Next Steps

1. ✅ Write CONTEXT.md (done)
2. ✅ Write DISCUSSION-LOG.md (this file)
3. Commit phase context files
4. Update STATE.md
5. User can proceed with `/gsd-plan-phase 9` when ready

---

*Discussion captured: 2026-06-27*
*Total decisions: 35 (D-01 through D-35)*
*Gray areas resolved: 4/4*
*Scope creep prevented: 6 ideas deferred to backlog*
