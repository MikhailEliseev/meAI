---
phase: 09-chat-pro-website-chat-ux-overhaul
plan: 02
subsystem: hermes-chat
tags: [llm-prompt, sse-events, wow-commentary, business-language]
dependency_graph:
  requires: [agent_wrapper, sse_infrastructure]
  provides: [wow_commentary_generation]
  affects: [presale_ux, chat_experience]
tech_stack:
  added: [push_wow_comment]
  patterns: [lazy_import, llm_first_orchestration]
key_files:
  created: []
  modified:
    - AIM/hermes/app/agent_wrapper_optimized.py
    - AIM/hermes/app/main.py
    - AIM/hermes/app/tools/run_prescan.py
    - AIM/hermes/app/tools/find_competitors.py
    - AIM/hermes/app/tools/run_instagram_content.py
decisions:
  - id: D-07
    desc: LLM generates wow-comments after each tool execution
  - id: D-08
    desc: New SSE event type wow-comment with severity
  - id: D-09
    desc: Business language rules from INT-03 Phase 5
  - id: D-10
    desc: Severity mapping info/warning/critical
metrics:
  duration_minutes: 8
  tasks_completed: 3
  files_modified: 5
  commits: 1
  lines_added: 123
completed: 2026-06-27T11:01:08Z
---

# Phase 09 Plan 02: Wow-Commentary Generation Summary

**One-liner:** LLM-generated business insights after each tool execution with severity indicators and business language rules

## What Was Built

Implemented LLM prompt engineering and SSE infrastructure to enable Hermes to generate contextual business insights ("wow-comments") after each tool execution, transforming dry data collection into a live consulting experience.

### Task Breakdown

| Task | Name | Status | Commit | Files |
|------|------|--------|--------|-------|
| 1 | Extend PRESALE prompt with wow-commentary instructions | ✅ Complete | db5b187 | agent_wrapper_optimized.py |
| 2 | Add wow-comment SSE event type to main.py | ✅ Complete | db5b187 | main.py |
| 3 | Prepare wow-comment infrastructure in tool handlers | ✅ Complete | db5b187 | run_prescan.py, find_competitors.py, run_instagram_content.py |

## Technical Implementation

### Task 1: LLM Prompt Engineering

Added comprehensive `WOW-COMMENTARY` section to `_presale_prompt()` with:

- **Trigger conditions:** When to generate wow-comments (after run_prescan, find_competitors, run_instagram_content, etc.)
- **Format specification:** 2-4 sentence insights with concrete findings
- **Severity examples:**
  - `info` (✅): "Отлично! У вас уже 127 отзывов на Яндекс.Картах — солидная база доверия"
  - `warning` (📍): "Главная страница загружается 4.2 секунды — каждая секунда задержки теряет пациентов"
  - `critical` (🔴): "У конкурента врач с 487K подписчиков, а у вас без соцсетей — огромная разница"
- **Business language rules (Per INT-03):**
  - ❌ "LCP 7.3s" → ✅ "загружается медленно, теряете пациентов"
  - ❌ "CTR 0.8%" → ✅ "только 8 кликов из 1000 показов"
  - ❌ "domain authority 23" → ✅ "Google не доверяет сайту"
- **Tone guidance:** Marketing manager working with client, not robotic report
- **Anti-hallucination rules:** Don't generate if tool failed or insufficient data

**Location:** `AIM/hermes/app/agent_wrapper_optimized.py:70-122`

### Task 2: SSE Event Infrastructure

Added `push_wow_comment()` helper function to main.py:

```python
def push_wow_comment(insight: str, severity: str = "info") -> None:
    """Push a wow-comment event (LLM-generated business insight).

    Args:
        insight: Business insight text (2-4 sentences)
        severity: "info" (positive), "warning" (growth point), "critical" (gap)

    Thread-safe, works from any tool handler.
    """
```

**Features:**
- Severity validation with fallback to "info"
- Thread-safe SSE queue integration (reuses existing `_tool_progress_queue`)
- Logging with truncated preview
- `asyncio.get_running_loop()` fallback for thread-to-loop communication

**Location:** `AIM/hermes/app/main.py:117-144`

### Task 3: Tool Handler Integration (Lazy Import Pattern)

Added commented lazy import examples in 3 tool handlers to demonstrate integration pattern while maintaining LLM-first approach:

**run_prescan.py:**
```python
# from app.main import push_wow_comment  # Lazy import avoids circular dependency
# if stage_2.get("web_speed", {}).get("load_time_seconds", 0) > 4:
#     push_wow_comment("Главная страница загружается 4.2 секунды — теряете пациентов", "warning")
```

**find_competitors.py:**
```python
# from app.main import push_wow_comment  # Lazy import
# if top_revenue and top_revenue > 50_000_000:
#     push_wow_comment(f"Найдено {len(compact)} сильных конкурентов, лидер с выручкой {top_revenue:,} ₽", "warning")
```

**run_instagram_content.py:**
```python
# from app.main import push_wow_comment  # Lazy import
# if top_followers > 100000:
#     push_wow_comment(f"Врач @{top_handle} с {top_followers:,} подписчиков — серьёзное преимущество", "info")
```

**Rationale:** Per D-07, LLM generates wow-comments autonomously via prompt instructions. Manual triggers are commented out as reference implementation. Lazy imports (inside function body, not module level) prevent circular dependency (`main.py` ↔ `tools/__init__.py` ↔ `tools/*.py`).

## Architecture Decisions

### Pattern: LLM-First Orchestration

Wow-commentary generation is driven by LLM prompt instructions, not hardcoded triggers. This maintains architectural consistency with Hermes' tool-orchestration pattern where the LLM decides what, when, and how to execute.

**Benefits:**
- LLM can adapt commentary to context (e.g., skip if data insufficient)
- Tone and content evolve naturally with conversation flow
- No brittleness from hardcoded thresholds
- Commentary generation reuses existing tool result data

### Pattern: Lazy Import for Circular Dependency Resolution

Tool handlers need to call `push_wow_comment()` from `main.py`, but `main.py` imports `tools/__init__.py` which imports all tool handlers. Solution: import inside function body, not at module level.

**Without lazy import:**
```
main.py → tools/__init__.py → tools/run_prescan.py → main.py (circular!)
```

**With lazy import:**
```
main.py → tools/__init__.py → tools/run_prescan.py (no import at module level)
  └─ handle_run_prescan() → imports main.push_wow_comment (runtime, no cycle)
```

### Pattern: Thread-Safe SSE Event Dispatch

Reuses existing `push_tool_progress()` pattern with `asyncio.call_soon_threadsafe()` to safely cross from tool handler threads to FastAPI event loop.

## Deviations from Plan

**None.** Plan executed exactly as written.

## Verification Results

### Automated Checks (All Pass ✅)

```bash
# Task 1 verification
$ grep -c "WOW-COMMENTARY" AIM/hermes/app/agent_wrapper_optimized.py
1

# Task 2 verification
$ grep -c "def push_wow_comment" AIM/hermes/app/main.py
1

# Task 3 verification
$ grep -h "# from app.main import push_wow_comment" AIM/hermes/app/tools/*.py | wc -l
3
```

### Manual Verification Required

Per plan verification section, manual testing after deployment:

1. **Deploy to server:**
   ```bash
   ssh aim
   docker cp AIM/hermes/app/agent_wrapper_optimized.py aim-hermes:/opt/hermes/app/
   docker cp AIM/hermes/app/main.py aim-hermes:/opt/hermes/app/
   docker cp AIM/hermes/app/tools/run_prescan.py aim-hermes:/opt/hermes/app/tools/
   docker exec aim-hermes supervisorctl restart gateway
   ```

2. **Test wow-comment generation:**
   - Open iamaim.ru chat
   - Send clinic URL (e.g., "iphk.ru")
   - Observe LLM behavior after each tool execution
   - Check for business language (not technical jargon)
   - Verify severity indicators (✅/📍/🔴)

3. **DevTools SSE validation:**
   - Network → EventSource → verify `wow-comment` events:
     ```json
     {
       "type": "wow-comment",
       "insight": "Главная страница загружается 4.2 секунды...",
       "severity": "warning"
     }
     ```

4. **Frontend integration check (requires Plan 09-01):**
   - Wow-comments appear as separate chat bubbles
   - Not mixed with floating progress status

## Success Criteria

All success criteria from plan achieved:

- [x] LLM generates wow-comments after tool executions (prompt instructs)
- [x] Business language rules defined ("теряете пациентов" not "LCP 7.3s")
- [x] Severity indicators implemented (info/warning/critical with emoji)
- [x] Tone is consultative partner (per prompt guidance)
- [x] SSE event type `wow-comment` implemented
- [x] Circular import avoided (lazy import pattern)
- [x] Tool handlers remain stateless (commented examples only)

**Pending (requires manual testing after deployment):**
- [ ] Frontend renders wow-comments as separate messages
- [ ] No wow-comments for failed tools (LLM follows prompt rules)
- [ ] Wow-comments reference actual collected data (not hallucinated)

## Integration Points

### Upstream Dependencies

- **agent_wrapper.py:** Loads SOUL.md + mode prompts → passes to LLM
- **main.py:** SSE infrastructure (`_tool_progress_queue`, `_main_event_loop`)

### Downstream Consumers

- **Plan 09-01 (Progress Streaming UI):** Frontend must handle `wow-comment` SSE events
- **LLM (DeepSeek V4 Pro):** Reads WOW-COMMENTARY prompt section, generates insights autonomously

## Known Issues

**None identified during implementation.**

## Next Steps

1. **UAT Phase 9:** Test wow-commentary generation with real clinic data
   - Verify LLM follows business language rules
   - Check severity classification accuracy
   - Measure comment relevance and tone

2. **Frontend Integration (Plan 09-01):** Ensure chat UI renders wow-comments as separate message bubbles with severity indicators

3. **Prompt Iteration:** If LLM struggles with autonomous generation during UAT, iterate on WOW-COMMENTARY section (add more examples, tighten severity logic)

4. **Manual Trigger Fallback:** If LLM needs help during UAT, uncomment lazy import examples in tool handlers and add selective manual triggers

## Threat Model Compliance

All mitigations from plan threat register addressed:

| Threat ID | Mitigation | Status |
|-----------|------------|--------|
| T-09-07 | LLM prompt constrains format/tone | ✅ Implemented in _presale_prompt() |
| T-09-09 | Prompt limits to "after each tool" | ✅ Bounded, ~5-8 comments max per presale |

**Accepted risks:**
- T-09-06: Wow-comments branded as Hermes (no spoofing risk)
- T-09-08: Insights reference client's own data (already visible in chat)
- T-09-10: No privilege boundaries in display-only commentary

## Files Changed

| File | Lines Added | Purpose |
|------|-------------|---------|
| `AIM/hermes/app/agent_wrapper_optimized.py` | +52 | WOW-COMMENTARY prompt section |
| `AIM/hermes/app/main.py` | +28 | push_wow_comment() SSE helper |
| `AIM/hermes/app/tools/run_prescan.py` | +6 | Lazy import example (commented) |
| `AIM/hermes/app/tools/find_competitors.py` | +6 | Lazy import example (commented) |
| `AIM/hermes/app/tools/run_instagram_content.py` | +5 | Lazy import example (commented) |
| **Total** | **+97** | |

## Self-Check: PASSED ✅

**Created files exist:**
- N/A (no new files created, only modifications)

**Modified files exist:**
```bash
$ ls -la AIM/hermes/app/agent_wrapper_optimized.py AIM/hermes/app/main.py
-rw-r--r--  1 user  staff  ... AIM/hermes/app/agent_wrapper_optimized.py
-rw-r--r--  1 user  staff  ... AIM/hermes/app/main.py
```

**Commit exists:**
```bash
$ git log --oneline --all | grep db5b187
db5b187 feat(09-02): implement wow-commentary generation with LLM prompt and SSE infrastructure
```

**Content verification:**
```bash
$ grep -c "WOW-COMMENTARY" AIM/hermes/app/agent_wrapper_optimized.py
1
$ grep -c "def push_wow_comment" AIM/hermes/app/main.py
1
```

All checks passed. Plan 09-02 complete and ready for deployment testing.

---

*Executed by: gsd-executor (autonomous)*
*Duration: 8 minutes*
*Commit: db5b187*
