# CI System — Детальные flow'ы

## Flow 1: Пресс-релизный CI (run_ci_analysis)

```
USER: "Сделай конкурентную разведку для https://clinic.ru"
  │
  ▼
HERMES (AI-ассистент)
  │ 1. Вызывает tool "find_competitors" → получает 3 competitor JSON
  │ 2. Вызывает tool "run_ci_analysis" с competitors
  │
  ▼
run_ci_analysis.py :: handle_run_ci_analysis()
  │ HTTP POST → /api/competitors/analyze/stream
  │ Consumes SSE stream
  │
  ▼
competitors.py :: analyze_competitors_stream()
  │ StreamingResponse(generate())
  │
  ▼
CiMarketingAnalyzer.analyze()
  │
  ├─► PipelineRunner.run(client_url, named_competitors)
  │   │
  │   ├─ Step 1: Find competitors
  │   │   if named_competitors → _named_urls_to_competitors()
  │   │   else → CompetitorMatcher.find_competitors()
  │   │
  │   ├─ For each competitor (SEQUENTIAL, not parallel!):
  │   │   │
  │   │   ├─ asyncio.gather(               ← 5 коллекторов ПАРАЛЛЕЛЬНО
  │   │   │   ├─ _collect_financials()     → bo.nalog.gov.ru
  │   │   │   ├─ _collect_seo()             → SeoAuditor.audit()
  │   │   │   ├─ _collect_social()          → SocialScanner.scan()
  │   │   │   ├─ _collect_website()         → website crawl
  │   │   │   └─ _collect_reviews()         → Yandex + ProDoctorov
  │   │   │
  │   │   └─ if doctor_names:
  │   │       _collect_doctors()            → DoctorExtractor
  │   │
  │   └─ Returns: list[CompetitorFull]
  │
  ├─► ComparisonMatrixBuilder.build(client_url, features, collected)
  │   │ Builds compact matrix (~5000 tokens)
  │   │ client: {url, features, missing, seo, social}
  │   │ competitors: [{name, url, ratings, financials, seo, social, positioning, website, doctors}]
  │   └─ Returns: ComparisonMatrix
  │
  ├─► _chat_summary_from_matrix(matrix)
  │   │ Структурная сборка markdown (НЕ LLM)
  │   │ Для каждого конкурента:
  │   │   - Название + URL
  │   │   - Рейтинги (GM, Яндекс, ПроДокторов)
  │   │   - Финансы (выручка, тренд)
  │   │   - SEO (score, issues)
  │   │   - Соцсети
  │   │   - Фишки сайта / чего нет
  │   │   - Врачи-лидеры
  │   │   - Позиционирование
  │   └─ Returns: markdown string
  │
  ├─► _feature_matrix_legacy(matrix)       → {competitors: [{name, features}]}
  ├─► _pricing_legacy(matrix)              → {competitors: [{name, has_pricing, revenue}]}
  ├─► _positioning_legacy(matrix)          → {competitors: [{name, positioning}]}
  ├─► steal_worthy_tactics = []            ← ВСЕГДА ПУСТО
  └─► _top_rec_from_matrix(matrix)         ← ЗАГЛУШКА
  │
  ▼
SSE STREAM:
  data: {"type":"progress","stage":"searching","message":"🔎 Ищу конкурентов..."}
  data: {"type":"progress","stage":"seo","message":"🔎 Сканирую сайт...","competitor":"clinic2.ru"}
  data: {"type":"progress","stage":"financials","message":"💰 Запрашиваю финансы...","competitor":"clinic2.ru"}
  ...
  data: {"type":"result","data":{...}}
  │
  ▼
HERMES показывает:
  - chat_summary (markdown текст)
  - feature_matrix
  - pricing_comparison
  - positioning_map
  - top_recommendation
```

---

## Flow 2: SEO аудит (run_seo_audit)

```
USER: "Сделай SEO-аудит https://clinic.ru"
  │
  ▼
HERMES
  │ Вызывает tool "run_seo_audit" с url
  │
  ▼
run_seo_audit.py :: handle_run_seo_audit()
  │
  ├─► POST /api/seo/audit  {"url": "...", "tier": "quick"}
  │   │
  │   ▼
  │ seo.py :: start_seo_audit()
  │   │ task_id = f"seo-audit-{timestamp}"
  │   │ _tasks[task_id] = AuditTask(status="pending")
  │   │ asyncio.create_task(_run_audit_background(task, payload))
  │   └─ Returns: {task_id, status: "pending"}
  │
  ├─► POLLING LOOP (каждые 2 сек):
  │   │ GET /api/seo/audit/{task_id}
  │   │
  │   │ status == "running" → push progress message
  │   │ status == "done"    → _compact_audit_result(data)
  │   │ status == "error"   → return error
  │   │
  │   ▼
  │ _run_audit_background() [в фоне]:
  │   │
  │   ├─► extract_client_profile(url) → city, specialization
  │   │
  │   └─► CIOrchestrator.execute_ci_analysis(task_data)
  │       │ tier = "quick" → phases = [1, 2, 3, 4]
  │       │
  │       ├─ Phase 1: _execute_single_phase(1, "ci-scout", task_data)
  │       │   _get_agent("ci-scout") → CIScoutAgent
  │       │   agent.execute_task(task) → результат
  │       │
  │       ├─ Phase 2: _execute_single_phase(2, "ci-auditor", task_data)
  │       │   _get_agent("ci-auditor") → CIAuditorAgent
  │       │   agent.execute_task(task) → результат
  │       │
  │       ├─ Phase 3: _execute_single_phase(3, "ci-deep-analyzer", task_data)
  │       │   _get_agent("ci-deep-analyzer") → CIDeepAnalyzer
  │       │   agent.execute_task(task) → результат
  │       │
  │       ├─ Phase 4: _execute_single_phase(4, "ci-reputation", task_data)
  │       │   _get_agent("ci-reputation") → CIReputationAgent
  │       │   agent.execute_task(task) → результат
  │       │
  │       └─ Phases 5-16: ПРОПУЩЕНЫ (tier="quick")
  │       │
  │       ▼
  │     findings = {
  │       "phase_1": {"status": "completed", "result": {...}},
  │       "phase_2": {"status": "completed", "result": {...}},
  │       "phase_3": {"status": "completed", "result": {...}},
  │       "phase_4": {"status": "completed", "result": {...}},
  │       # phase_5 ... phase_16 — НЕ СУЩЕСТВУЮТ
  │     }
  │     │
  │     └─► Возвращает findings в task.result
  │
  ▼
_compact_audit_result(data):
  │
  ├─► phase7 = findings.get("phase_7", {})   ← НЕ СУЩЕСТВУЕТ ПРИ QUICK!
  │   estimates = phase7.get("result", {}).get("estimates", {}) or {}
  │   → patients_per_month: None
  │   → time_to_result_weeks: None
  │   → cost_per_patient_rub: None
  │
  ├─► phase1 = findings.get("phase_1", {})
  │   competitors = scout_result.get("top_for_analysis", [])
  │   → может быть [], если scout вернул ошибку
  │
  ├─► phase9 = findings.get("phase_9", {})   ← НЕ СУЩЕСТВУЕТ ПРИ QUICK!
  │   actions = prio_result.get("action_items", [])
  │   → []
  │
  └─► Returns: {wow: {все null}, market: {все unknown}, competitors: [], insights: [], ...}
  │
  ▼
HERMES показывает: "Вот результаты SEO-аудита..." (с пустыми WOW-цифрами)
```

---

## Flow 3: Полный CI (16 фаз) — КАК ДОЛЖНО БЫТЬ

```
CIOrchestrator.execute_ci_analysis(task_data)
  tier = "full" → phases = [1..16]
  │
  ├─ Phase 1: ci-scout           ← поиск конкурентов
  ├─ Phase 2: ci-auditor         ← аудит сайтов (28 проверок)
  ├─ Phase 3: ci-deep-analyzer   ← глубокий анализ
  ├─ Phase 4: ci-reputation      ← репутация
  ├─ Phase 5: 9 agents PARALLEL  ← finance, vacancies, tech, crawler, content, pricing, ecosystem, backlink, rank
  ├─ Phase 6: ci-factchecker     ← проверка фактов
  ├─ Phase 7: ci-strategist      ← стратегия (часть 1)
  ├─ Phase 8: ci-strategist      ← стратегия (часть 2)
  ├─ Phase 9: ci-prioritizer     ← приоритизация
  ├─ Phase 10: ci-marketing-strategy
  ├─ Phase 11: tw-competitor-scout    ← ❌ STUB
  ├─ Phase 12: tw-creative-collector  ← ❌ STUB
  ├─ Phase 13: tw-creative-analyzer   ← ❌ STUB
  ├─ Phase 14: tw-pattern-finder      ← ❌ STUB
  ├─ Phase 15: tw-traffic-analyzer    ← ❌ STUB
  └─ Phase 16: ci-offer-generator ← генерация КП
```

---

## Flow 4: Второй путь CIOrchestrator (execute_task — STUB)

```
CIOrchestrator.execute_task(task)
  │ Этот метод НИКОГДА не вызывается из seo.py
  │ Он существует как стандартный интерфейс Agent
  │
  ├─ tier = _detect_tier(task.payload)    ← deep (default)
  ├─ _execute_phases(tier, payload)
  │   │
  │   └─ For each phase:
  │       _execute_single_agent(agent_id, payload, prev_results)
  │         │
  │         └─ _delegate_to_agent(agent_id, task)
  │             │
  │             ├─ event_bus.publish(Event(...))   ← публикует событие
  │             └─ return {"agent_id": ..., "status": "delegated"}  ← STUB!
  │
  └─ Все фазы возвращают {"status": "delegated"} — никто не ждёт ответа
```

---

## Ключевое различие: два пути в CIOrchestrator

```
Путь 1 (execute_ci_analysis) — РАБОТАЕТ:
  seo.py → execute_ci_analysis()
    → _execute_single_phase()
      → _get_agent()           ← импортирует реальный класс
      → agent.execute_task()   ← запускает реальную логику
    → возвращает реальный результат

Путь 2 (execute_task) — STUB:
  ??? → execute_task()
    → _execute_single_agent()
      → _delegate_to_agent()
        → event_bus.publish()  ← только публикует событие
        → return {"status": "delegated"}  ← STUB
    → возвращает заглушку
```

**Вывод:** Путь 1 — реальный, Путь 2 — нефункциональный. Путь 2 никогда не вызывается извне (seo.py использует execute_ci_analysis), но существует в коде и сбивает с толку.
