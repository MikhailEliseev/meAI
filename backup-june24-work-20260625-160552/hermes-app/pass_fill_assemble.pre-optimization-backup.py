"""Pass 3 — Fill gaps + Assemble HTML report.

Per Phase 2 RESEARCH.md Section 5.2 — orchestrator-first, Option 2.
Per Plan 02-02 Task 1: Pass 3 receives the gap_report produced by Pass 2
and asks the LLM to (a) call additional tools if any gaps are fillable,
then (b) invoke ``generate_html_report`` with the full collected data set.
If the LLM cannot fill a gap, it must honestly mark the section as
"данные недоступны" — no fabrication (per ORC-04).

Phase 3 / D-07 (Plan 03-05 Task 3): the Pass 3 prompt now explicitly
instructs the LLM to pass ``niche`` (from
``state.collected_data.niche_detection.niche`` — populated by the
Plan 03-02 mini-call between Pass 1 and Pass 2) and ``instagram_data``
(the full ``run_instagram_content`` batch response from Pass 1
tool-call history, or None if Instagram wasn't called) as kwargs to
``generate_html_report``. These kwargs drive the conditional rendering
of the "Instagram: данные недоступны" block in sections 03 + 04 of the
HTML report (Plan 03-05 Task 1). Without this prompt-level instruction,
the LLM has no way to know these kwargs exist — closing the cross-plan
data-contract gap flagged by Checker issue #1.

Phase 4 / Plan 04-05: Pass 3 prompt extended with generation rules for
5 new sections (Strategy, Offer, Whitefields, Experts+регалии,
Content+страхи) + 4 data rendering rules (revenue dynamics, clinic
metrics, media URLs, ratings, competitor cards).
Items 7-15 added to the existing 6-item prompt.

Phase 5 / Plan 05-01: Pass 3 prompt extended with cross-cutting
narrative quality rules (items 16-21). Items 16-18 added in Task 1
(narrative style, business language, cross-references). Items 19-21
added in Task 2 (gap-block format, section blockquote, reference
calibration). INT-01..05 prompt-layer satisfied. HTML rendering layer
for gap_blocks + insight kwargs in Plan 05-02.

Phase 5 / Plan 05-03: Pass 3 prompt extended with EXAMPLES BY SECTION
calibration block. 10+ narrative examples extracted from reference
``ИПХиК (2).html`` (one per section, Секция 01..10) + 2 cross-reference
examples (Content → Experts, Strategy → Content fears) + 2 gap-block
examples (1 strength with ✅, 1 growth point with 📍) + 2 blockquote
examples (Market + Strategy). D-11 fully satisfied — Plan 05-01 added
short pointer in item 21; this plan adds the comprehensive section-
by-section calibration. Examples embedded inline in the prompt as
few-shot anchors so DeepSeek V4 Pro can emulate reference style with
high fidelity instead of guessing from abstract rules.

Exit criteria: LLM has invoked ``generate_html_report`` (visible in
tool_calls) and returned a final response. Pass 3 result is stored in
``state.collected_data["pass_fill_assemble_result"]``.
"""

import asyncio
import logging

from app.orchestrator.states import OrchestratorState, PASS_FILL_ASSEMBLE, PASS_GAP_ANALYZE

logger = logging.getLogger(__name__)

# Pass 3 may invoke additional tools AND call generate_html_report — give it
# the same 10-minute ceiling as Pass 1 since tool execution dominates the
# wall-clock time, not LLM reasoning.
_PASS_FILL_TIMEOUT = 600


async def run_pass_fill_assemble(state: OrchestratorState) -> OrchestratorState:
    """Execute Pass 3 — Fill gaps and assemble the HTML report.

    The LLM continues on the SAME session_id, so its SQLite-backed
    conversation history from Pass 1 and Pass 2 is available. We just
    hand it the structured gap_report and instruct it to fill the
    remaining gaps + invoke ``generate_html_report``.

    Best-effort on Pass 2 status: if Pass 2 did not complete (e.g. parse
    error), we still run Pass 3 with an empty gap_report — the LLM has
    the Pass 1 data in its history and can produce a best-effort report.
    """
    if state.pass_status.get(PASS_GAP_ANALYZE) != "completed":
        logger.warning(
            "Orchestrator Pass 3 (Fill+Assemble): Pass 2 status=%s, "
            "continuing with gap_report=%s (best-effort)",
            state.pass_status.get(PASS_GAP_ANALYZE),
            state.gap_report,
        )

    state.mark_pass(PASS_FILL_ASSEMBLE, "running")
    logger.info(
        "Orchestrator Pass 3 (Fill+Assemble): starting for %s (session=%s)",
        state.client_url, state.session_id,
    )

    try:
        from app.orchestrator.pass_collect import _get_agent_for_session
        agent = await _get_agent_for_session(state.session_id, state.mode)

        prompt = _build_prompt(state)

        result = await asyncio.wait_for(
            asyncio.to_thread(agent.run_conversation, prompt),
            timeout=_PASS_FILL_TIMEOUT,
        )

        state.collected_data["pass_fill_assemble_result"] = result
        state.mark_pass(PASS_FILL_ASSEMBLE, "completed")
        logger.info(
            "Orchestrator Pass 3 (Fill+Assemble): completed for %s — result keys=%s",
            state.client_url,
            list(result.keys()) if isinstance(result, dict) else type(result).__name__,
        )
    except Exception as exc:
        state.mark_pass(PASS_FILL_ASSEMBLE, "failed")
        state.error_message = str(exc)
        logger.exception(
            "Orchestrator Pass 3 (Fill+Assemble): FAILED for %s — %s",
            state.client_url, exc,
        )

    return state


def _build_prompt(state: OrchestratorState) -> str:
    """Build the Pass 3 prompt — fill gaps then assemble HTML."""
    gap_report = state.gap_report or {}
    gap_summary = gap_report.get("summary", {}) if isinstance(gap_report, dict) else {}
    gap_items = gap_report.get("items", []) if isinstance(gap_report, dict) else []

    missing_items = [
        item for item in gap_items
        if isinstance(item, dict) and item.get("status") in ("missing", "partial")
    ]

    summary_line = (
        f"filled={gap_summary.get('filled', '?')}, "
        f"missing={gap_summary.get('missing', '?')}, "
        f"total={gap_summary.get('total', '?')}"
    ) if gap_summary else "нет данных (Pass 2 не завершился)"

    missing_block = ""
    if missing_items:
        lines = []
        for item in missing_items:
            name = item.get("name", "?")
            status = item.get("status", "?")
            detail = item.get("detail", "")
            lines.append(f"  - {name} ({status}){': ' + detail if detail else ''}")
        missing_block = "\nПробелы для допосбора:\n" + "\n".join(lines)
    else:
        missing_block = "\nПробелов не обнаружено — переходи сразу к сборке отчёта."

    # Optional: attach coverage_report_final if Pass 3 has access to it
    # (populated by three_pass.py between Pass 2 and Pass 3 via
    # state.collected_data["coverage_report_after_pass2"]; final value is
    # computed AFTER Pass 3 — so during Pass 3 we only have the post-Pass-2
    # snapshot to hand the LLM, which is still useful as a hint).
    coverage_hint = ""
    coverage_after_p2 = state.collected_data.get("coverage_report_after_pass2") or {}
    if coverage_after_p2:
        coverage_hint = (
            f"\n\nТекущий coverage (после Pass 2): "
            f"{len(coverage_after_p2.get('filled_items', []))}/15 "
            f"({coverage_after_p2.get('coverage_pct', 0) * 100:.1f}%) — "
            f"{coverage_after_p2.get('status', 'UNKNOWN')}."
        )

    return (
        f"Вот твой gap report из Pass 2: summary=[{summary_line}].{missing_block}"
        f"{coverage_hint}\n\n"
        "ЗАДАЧА:\n"
        "1. Если есть fillable пробелы — вызови ЕЩЁ инструменты чтобы их заполнить "
        "(используй свой каталог из 49 tools). Не повторяй инструменты которые уже "
        "вызывал в Pass 1 — они уже в твоей истории.\n"
        "2. Затем ВЫЗОВИ generate_html_report с полным набором собранных данных.\n"
        "3. Если данные недоступны — честно отметь в отчёте «данные недоступны», "
        "НЕ выдумывай. Это требование ORC-04.\n"
        "4. КОГДА ВЫЗЫВАЕШЬ generate_html_report — ОБЯЗАТЕЛЬНО передай параметр "
        "coverage_metadata из доступного тебе state.collected_data.coverage_report_after_pass2 "
        "(если он есть). Это нужно для отображения секции 'QC Coverage Report' "
        "в конце HTML-отчёта (per QC-03).\n"
        "5. КОГДА ВЫЗЫВАЕШЬ generate_html_report — ОБЯЗАТЕЛЬНО передай параметр "
        "niche со значением из state.collected_data.niche_detection.niche "
        "(это ниша клиники, определённая мини-коллом между Pass 1 и Pass 2 — "
        "нужно для рендеринга 'Instagram: данные недоступны' блока в секциях 03+04 "
        "для critical ниш, per Phase 3 D-07).\n"
        "6. КОГДА ВЫЗЫВАЕШЬ generate_html_report — ОБЯЗАТЕЛЬНО передай параметр "
        "instagram_data с полным ответом инструмента run_instagram_content из твоей "
        "Pass 1 tool-call history (если вызов был). Если Instagram не вызывался — "
        "передай instagram_data=None. Это нужно для определения 'no data' vs 'no account' "
        "причины в HTML блоке (per Phase 3 D-07).\n"
        "7. STRATEGY SECTION (секция 09): Сгенерируй секцию Strategy с 5 "
        "конкретными направлениями для ЭТОЙ клиники. Направления фиксированы: "
        "(1) Контент, (2) Telegram, (3) GEO, (4) Репутация, (5) Кросс-промо. "
        "СОДЕРЖИМОЕ каждого направления генерируй ИЗ СОБРАННЫХ ДАННЫХ:\n"
        "   - Базис 1: КОНКУРЕНТЫ — что работает у топ-3 конкурентов (из "
        "find_competitors + run_ci_analysis)? Какие их тактики клиент может "
        "повторить?\n"
        "   - Базис 2: CONTENT GAPS — где врачи слабы в Instagram (из секции "
        "04 content_gaps)? Какой контент создать, чтобы закрыть пробелы?\n"
        "   - Базис 3: СТРАХИ ПАЦИЕНТОВ — топ-5 страхов из run_forum_pains. "
        "Какой контент-план закроет эти страхи (например, 'до/после' для "
        "страха 'неэффективное лечение')?\n"
        "   - Базис 4: REPUTATION GAPS — где клиент проигрывает в рейтингах "
        "(из run_review_platforms)? Как улучшить репутацию?\n"
        "   Для КАЖДОГО направления: 2-3 конкретных шага с цифрами из данных. "
        "НЕ общие советы ('создайте контент'), а конкретные ('создайте "
        "Telegram-канал, 3 поста/нед, контент: до/после пациентов, потому "
        "что конкурент X имеет 50K подписчиков при +20%/мес').\n"
        "   Передай strategy_data как kwarg в generate_html_report (dict с keys: directions list[{name, basis, expected_impact}]).\n\n"
        "8. OFFER SECTION (секция 10): Сгенерируй секцию 'Что AIM может "
        "сделать для клиники' с конкретными шагами + CTA. Используй тот же "
        "паттерн что и Strategy: НА ОСНОВЕ собранных данных предложи "
        "конкретные услуги AIM (контент-продакшн, SEO, репутация-менеджмент, "
        "Telegram-маркетинг) с измеримыми результатами. Заканчивай CTA "
        "('Запишитесь на бесплатный аудит →').\n"
        "   Передай offer_data как kwarg в generate_html_report (dict с keys: steps list[str], cta str).\n\n"
        "9. WHITEFIELDS MATRIX (секция 07): Построй матрицу сравнения "
        "КЛИЕНТ vs топ-3 КОНКУРЕНТА. 4 категории колонок:\n"
        "   (1) УСЛУГИ — пластика груди/липосакция/инъекции/лазер/нити (✓/✗)\n"
        "   (2) ЦЕНЫ — топ-3 услуги (диапазон ₽)\n"
        "   (3) ВРАЧИ — количество хирургов/косметологов, регалии (КМН, "
        "профессор) — из find_doctor_handles structured_regalia\n"
        "   (4) DIGITAL PRESENCE — Instagram K (из run_instagram_content "
        "followers_count), Telegram, SEO rank, рейтинг (из "
        "run_review_platforms)\n"
        "   Минимум 4 колонки: клиент + 3 конкурента. Если прескан нашёл "
        "больше — взять топ-3 по выручке или релевантности. Каждая ячейка "
        "из собранных данных (competitors analysis, find_doctor_handles, "
        "run_instagram_content, find_company_financials).\n"
        "   Передай whitefields_data как kwarg в generate_html_report (dict с keys: categories list[str], columns list[{name, is_client}], cells dict[section_key → list]).\n\n"
        "10. EXPERTS SECTION (03) С РЕГАЛИЯМИ: Для каждого топ-5 врача "
        "покажи: ФИО, регалии (degree, academic_title, experience_years, "
        "education — из find_doctor_handles structured_regalia), Instagram "
        "метрики (followers_count, avg_likes, avg_views — из "
        "run_instagram_content top_by_followers). Мёрдж по ФИО: "
        "site-scraped регалии + Instagram метрики. Если врач есть на сайте "
        "но без Instagram — покажи только регалии (это валидный эксперт). "
        "Если врач есть в Instagram но не на сайте — покажи только метрики "
        "(source: instagram_only).\n"
        "   Передай experts_data как kwarg в generate_html_report (list of dicts: name, structured_regalia, instagram_metrics, source).\n\n"
        "11. CONTENT ANALYSIS (04) СО СТРАХАМИ: Для каждого топ-5 врача "
        "(Instagram-active когорта) покажи: стиль контента, темы (в %), "
        "пробелы, потенциал — из run_instagram_content. ПЛЮС ТОП-5 "
        "СТРАХОВ ПАЦИЕНТОВ из run_forum_pains patient_fears_hint: каждый "
        "страх с количеством упоминаний. Формат: '{страх} — {почему "
        "упоминается} ({кол-во упоминаний})'. Например: 'Больно — 47 "
        "упоминаний из 120 отзывов'.\n"
        "   Передай content_data как kwarg в generate_html_report (dict с keys: doctor_analyses list, patient_fears list[{fear, mention_count}], total_reviews int).\n\n"
        "12. REVENUE DYNAMICS: Если find_company_financials вернул "
        "revenue_dynamics.dynamics_available=True — покажи таблицу: "
        "год → выручка → YoY % (3 строки). Blockquote с выводом из "
        "summary_text ('+79% за 3 года, растёт быстрее рынка'). "
        "ЕСЛИ dynamics_available=False — НЕ показывай секцию динамики "
        "ВОВСЕ. Честная надпись 'Динамика выручки недоступна — "
        "недостаточно данных в открытых источниках'. Это D-13 strict "
        "rule — не нарушай.\n"
        "   Передай revenue_dynamics как kwarg в generate_html_report.\n\n"
        "13. CLINIC METRICS: В секции About покажи метрики клиники из "
        "find_company_financials clinic_metrics: выручка, прибыль, "
        "сотрудники (если есть), лицензии (из prescan), ОКВЭД. ТЫ (LLM) "
        "переводи ОКВЭД-коды на человеческий язык: '86.21' → 'Общая "
        "медицинская практика', '86.23' → 'Стоматологическая практика'. "
        "Используй свои знания ОКВЭД классификатора.\n"
        "   Передай clinic_metrics_humanized как kwarg (где ОКВЭД уже "
        "переведён) в generate_html_report.\n\n"
        "14. MEDIA URLS: В секции Media (05) покажи ПРОСТОЙ СПИСОК "
        "гиперссылок из run_media_urls: For each mention: '{Source} — "
        "\"{Title}\" — {Date} → {URL}'. НЕ карточки с лого (избыточно для "
        "MVP). Если run_media_urls вернул 0 упоминаний (pr_needed=True) — "
        "покажи честный блок 'В СМИ не упоминалась за последние 3 года' + "
        "в Strategy (09) рекомендуй PR-активность.\n"
        "   Передай media_urls как kwarg в generate_html_report.\n\n"
        "15. RATINGS: Покажи рейтинги из run_review_platforms для "
        "минимум 2 платформ: ПроДокторов + Яндекс.Карты. Для каждой: "
        "рейтинг (звёзды), количество отзывов, главные темы положительных "
        "и отрицательных отзывов.\n"
        "   Передай ratings_data как kwarg в generate_html_report.\n\n"
        "16. NARRATIVE STYLE (D-02 — ОБЯЗАТЕЛЬНО для всех секций 7-15 выше): "
        "КАЖДАЯ секция отчёта = 2-3 параграфа связного текста с выводами и "
        "цифрами, НЕ маркированный список метрик. Образец — референс "
        "ИПХиК (2).html секция Market: «Клиника ИПХиК стабильно удерживает "
        "топ-3 позицию по выручке. 4.3 млрд выручки против 2.3 млрд у "
        "Seline (ближайший конкурент)» — это нарратив с цифрой внутри, "
        "НЕ «Выручка: 4.3 млрд, Рост: +26%». "
        "Правила: (a) первый параграф = главный вывод секции одной фразой "
        "с цифрой; (b) второй параграф = раскрытие вывода (откуда цифра, "
        "сравнение с конкурентами); (c) третий параграф (опционально) = "
        "что это значит для бизнеса клиента. "
        "Запрещено: «Скорость загрузки: 7.3s, Bounce rate: 65%» без "
        "интерпретации. Разрешено: «Сайт грузится 7.3 секунды — каждая "
        "секунда задержки теряет пациентов; две трети посетителей уходят, "
        "не дочитав (bounce rate 65%)».\n\n"
        "17. BUSINESS LANGUAGE (D-05, D-06): Технические метрики СОПРОВОЖДАЙ "
        "человеческой интерпретацией. Цифры ОСТАЮТСЯ (LCP 7.3s, выручка "
        "4.3 млрд), но сопровождаются объяснением. Словарь замен (используй "
        "ВМЕСТЕ с цифрой, не вместо): "
        "(a) LCP / скорость загрузки → «каждая секунда задержки теряет "
        "пациентов»; "
        "(b) Bounce rate 65% → «две трети посетителей уходят, не дочитав»; "
        "(c) CLS 0.4 → «контент прыгает при загрузке — выглядит "
        "непрофессионально»; "
        "(d) DA 25 → «поисковики слабо доверяют сайту»; "
        "(e) Backlinks 45 → «45 сайтов ссылаются на клинику — мало для "
        "топ-3». "
        "Образец: «LCP 7.3s — каждая секунда задержки теряет пациентов; "
        "при отраслевом бенчмарке 2.5s клиника теряет ~5% лидов с каждого "
        "визита».\n\n"
        "18. CROSS-REFERENCES (D-03, D-04): КАЖДАЯ секция должна ссылаться "
        "на данные из других секций — НЕ изолированные блоки. Минимум 1 "
        "cross-reference на секцию. Паттерны: "
        "(a) Strategy (09) → упоминает конкретные страхи пациентов из "
        "секции 04 (Content Analysis), конкретные пробелы врачей из "
        "секции 04, конкретные рейтинги из Reviews; "
        "(b) Offer (10) → каждый пункт привязан к цифре или gap из других "
        "секций; "
        "(c) Content Analysis (04) → ссылается на топ-врачей из секции 03 "
        "(Experts); "
        "(d) Whitefields matrix (07) → ячейки заполнены из competitors "
        "(02), doctors (03), instagram (04), financials (About). "
        "Формулировка (пример для Strategy): «Видя, что {top_fear} из "
        "секции 04 — главный страх пациентов, стратегия по направлению "
        "Контент должна закрыть именно этот страх через формат {format}». "
        "LLM генерирует cross-references САМ на основе собранных данных, "
        "никаких хардкод-линков.\n\n"
        "19. GAP-BLOCK FORMAT (D-07 — ОБЯЗАТЕЛЬНО для каждой секции 7-15): "
        "В каждой секции после нарративных параграфов добавляй 2-4 "
        "gap-блока по единому формату: "
        "✅ Сильная сторона: {что} ({цифра из данных}) — почему это сильная "
        "сторона. "
        "📍 Точка роста: {что улучшить} — ориентир: {конкурент} ({цифра "
        "конкурента}). "
        "Правила: (a) каждый gap-блок содержит ЦИФРУ из собранных данных "
        "(не общие слова); (b) точка роста ОБЯЗАТЕЛЬНО содержит бенчмарк "
        "на конкретного конкурента с цифрой; (c) если нет данных для "
        "gap-блока — НЕ выдумывай, пропусти секцию. "
        "Передай section_gap_blocks как kwarg в generate_html_report — dict где ключи это section_key "
        "('strategy', 'offer', 'experts', 'content', 'ratings'), значения — списки gap-блоков "
        "[{'type': 'strength'|'growth', 'title': str, 'description': str}] для этой секции. "
        "Образец из референса: «✅ Сильная сторона: масштаб и академическая "
        "база (150+ хирургов, 88 лет истории)» / «📍 Точка роста: цифровое "
        "присутствие — ориентир: Олимп Клиник (Telegram-канал 15K, "
        "MedicalBusiness Schema внедрена)».\n\n"
        "20. SECTION BLOCKQUOTE (D-09, D-10 — ОБЯЗАТЕЛЬНО для каждой секции "
        "7-15): КАЖДАЯ секция заканчивается blockquote с главным strategic "
        "insight (1-2 предложения, бизнес-язык). Формат HTML: "
        "`<blockquote class=\"section-insight\">{главный вывод секции}"
        "</blockquote>`. Передай section_insights как kwarg в generate_html_report — dict где ключи это "
        "section_key ('strategy', 'offer', 'whitefields', 'experts', 'content', 'revenue-dynamics', "
        "'media-urls', 'ratings', 'competitor-cards', 'about'), значения — 1-2 предложения strategic "
        "insight для этой секции. Правила: (a) insight = ВЫВОД, не пересказ "
        "данных (не «Выручка 4.3 млрд», а «ИПХиК — безусловный лидер рынка "
        "по выручке, отрыв от ближайшего конкурента в 2 раза»); "
        "(b) 1-2 предложения максимум; (c) если нет данных для вывода — "
        "честно «данные недоступны, инсайт сформировать нельзя» "
        "(ORC-04 honest principle). "
        "Образцы из референса: секция 02 — «Отрыв не в деньгах - отрыв в "
        "масштабе»; секция 09 — «У ИПХиК есть 150+ хирургов, 15 из которых "
        "уже имеют соцсети с аудиторией 587K. Не надо создавать маркетинг "
        "с нуля».\n\n"
        "21. REFERENCE CALIBRATION (D-11): ИСТИНА для всех narrative "
        "правил — референс `/Users/mikhaileliseev/Downloads/ИПХиК (2).html` "
        "(78KB, 965 строк, 10 секций). ПОДРАЖАЙ стилю и глубине референса. "
        "Конкретные образцы стиля (few-shot): "
        "Секция About: «Динамика выручки: +79% за 3 года (2.4 млрд в 2022, "
        "3.4 млрд в 2024, 4.3 млрд в 2025). Чистая прибыль 139 млн руб. в "
        "2025. Рост сотрудников: +74% за 4 года» — нарратив с цифрами, не "
        "метрик-дамп. "
        "Секция Market: «ИПХиК — безусловный лидер по выручке» — вывод "
        "первой фразой, затем раскрытие. "
        "Секция Strategy: «У ИПХиК есть все активы для лидерства в "
        "digital: масштаб, аудитория врачей, академический вес» — цепочка "
        "аргументов. "
        "Секция Offer: «AIM не даёт одного человека — мы даём систему: "
        "AI-агент, который делает работу 3 человек» — конкретное УСП. "
        "КАЖДОЕ правило 16-20 выше — это формализация того, что уже есть в "
        "референсе. Если сомневаешься в стиле — возвращайся к референсу "
        "как канону.\n\n"
        "ПРИМЕРЫ ИЗ РЕФЕРЕНСА (стиль и глубина — CANON, НЕ копируй "
        "конкретные цифры — бери цифры из данных клиента; эти образцы "
        "показывают СТИЛЬ и ГЛУБИНУ нарратива):\n"
        "Секция 01 (About): «Динамика выручки: +79% за 3 года (2.4 млрд "
        "в 2022, 3.4 млрд в 2024, 4.3 млрд в 2025). Чистая прибыль 139 "
        "млн руб. в 2025. Рост сотрудников: +74% за 4 года (364 в 2021, "
        "632 в 2025)» — нарратив с цифрами, не метрик-дамп.\n\n"
        "Секция 02 (Market): «ИПХиК — безусловный лидер по выручке. 4.3 "
        "млрд выручки против 2.3 млрд у Seline (ближайший конкурент). По "
        "числу хирургов (150+) отрыв от Seline (10+) в 15 раз» — вывод "
        "первой фразой, затем раскрытие с цифрами и сравнением.\n"
        "  Gap-блок (сильная сторона): «✅ Сильная сторона: масштаб и "
        "академическая база (150+ хирургов, 88 лет истории, 6 товарных "
        "знаков) — ни один конкурент не может предложить аналогичную "
        "глубину».\n"
        "  Gap-блок (точка роста): «📍 Точка роста: цифровое присутствие "
        "— ориентир: Олимп Клиник (Telegram-канал, MedicalBusiness "
        "Schema)».\n"
        "  Blockquote (секция 02): «Отрыв не в деньгах — отрыв в "
        "масштабе».\n\n"
        "Секция 03 (Experts): «Мельников (318K) — абсолютный лидер рынка "
        "пластической хирургии по аудитории. Ни у одного конкурента нет "
        "врача с аудиторией даже близкой к этой цифре» — вывод + "
        "сравнение.\n\n"
        "Секция 04 (Content Analysis): «Только Авдошенко системно "
        "работает со страхами пациентов (3 из 5). Мельников имеет "
        "колоссальную аудиторию (318K), но не использует её для закрытия "
        "страхов» — анализ с цифрами.\n"
        "  Cross-reference пример: «Если Мельников запустит рубрику про "
        "наркоз и реабилитацию — охват будет измеряться сотнями тысяч "
        "просмотров» (ссылка на топ-страх из списка ниже + на топ-врача "
        "из секции 03).\n\n"
        "Секция 05 (Media): «Институт регулярно упоминается в профильных "
        "и деловых изданиях. Тон преимущественно нейтральный/позитивный. "
        "Ключевые нарративы: лидер рынка, инновации, экспансия, "
        "образование» — структурированный вывод с классификацией.\n\n"
        "Секция 06 (Competitor Cards): «Seline — 2.3 млрд выручки, 10+ "
        "хирургов, 27K Instagram. Растёт +19.1% (медленнее ИПХиК). Сильна "
        "в B2B-сегменте» — карточка с динамикой и УТП.\n\n"
        "Секция 07 (Whitefields): «Рынок пластической хирургии Москвы — "
        "абсолютно белое поле для цифрового маркетинга. Telegram-каналов "
        "нет ни у кого. MedicalBusiness Schema отсутствует у всех» — "
        "вывод по матрице.\n\n"
        "Секция 08 (Presence): «При отраслевом бенчмарке 2.5s сайт "
        "грузится 7.3s — каждая секунда задержки теряет пациентов» — "
        "бизнес-язык для тех. метрики.\n\n"
        "Секция 09 (Strategy): «У ИПХиК есть 150+ хирургов, 15 из которых "
        "уже имеют соцсети с аудиторией 587K. Не надо создавать маркетинг "
        "с нуля — достаточно системно интегрировать то, что уже работает» "
        "— стратегический вывод из данных.\n"
        "  Cross-reference: «Видя, что страх 'наркоз' из секции 04 — "
        "главный страх пациентов, стратегия по направлению Контент должна "
        "закрыть именно этот страх через формат до/после».\n"
        "  Blockquote (секция 09): «Это даст рост органического трафика в "
        "3-5x при бюджете ниже, чем у конкурентов».\n\n"
        "Секция 10 (Offer): «AIM не даёт одного человека — мы даём "
        "систему: AI-агент, который делает работу 3 человек. Разведка, "
        "контент-план, анализ конкурентов, GEO, Telegram — всё в одном "
        "автоматизированном процессе» — конкретное УТП с отстройкой от "
        "альтернатив.\n\n"
        "ОБЩИЕ ПРИНЦИПЫ (извлечённые из примеров выше — ОБЯЗАТЕЛЬНО):\n"
        "- Первая фраза секции = ВЫВОД с цифрой, не пересказ данных.\n"
        "- Каждая цифра сопровождается сравнением (с конкурентом, с "
        "отраслью, с предыдущим периодом).\n"
        "- Каждая секция заканчивается blockquote с главным strategic "
        "insight.\n"
        "- Cross-references делаются НЕ хардкодом, а органически "
        "вплетаются в нарратив.\n"
        "- Бизнес-язык: «теряет пациентов», «отрыв в масштабе», «белое "
        "поле для маркетинга».\n\n"
        "═══ ФИНАЛЬНОЕ И ОБЯЗАТЕЛЬНОЕ ДЕЙСТВИЕ ═══\n"
        "Твой ответ в ЭТОМ проходе ДОЛЖЕН быть tool_call к generate_html_report. "
        "НЕ пиши описательный текст — LLM-потребитель (three_pass.py) ждёт от тебя "
        "именно вызов инструмента. Все данные уже собраны, все секции спроектированы "
        "выше в этом промпте — тебе осталось только УПОРЯДОЧИТЬ их в kwargs и вызвать.\n"
        "Минимальный набор kwargs (все обязательны):\n"
        "  - client_url, client_name (str)\n"
        "  - niche (str), instagram_data (dict|None), coverage_metadata (dict)\n"
        "  - strategy_data, offer_data, whitefields_data, experts_data, content_data (dicts)\n"
        "  - revenue_dynamics, clinic_metrics (из find_company_financials)\n"
        "  - media_urls (из run_media_urls), ratings_data (из run_review_platforms)\n"
        "  - section_insights (dict section_key→str), section_gap_blocks (dict section_key→list)\n"
        "Если какая-то секция не имеет данных — передай пустую структуру (например []), "
        "НО вызов генерации НЕ откладывай. Вызови generate_html_report СЕЙЧАС.\n\n"
    )
