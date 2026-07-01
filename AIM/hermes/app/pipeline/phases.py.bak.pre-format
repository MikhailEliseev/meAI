"""Hermes v7 — Phase Definitions.

13 фаз онбординг-пайплайна. Каждая фаза — изолированный шаг сбора и интерпретации данных.

Поток данных:
  Phase 0: PERPLEXITY — deep research (рынок, город, ниша, конкуренты)
  Phase 1: COMPETITORS — поиск (Apify) + CI-анализ
  Phase 2: TECH AUDIT — Pagespeed + SEO
  Phase 3: SOCIAL VERIFIER — отзывы, рейтинги
  Phase 4: CONTENT ANALYSIS — контент сайта
  Phase 5: KEY PERSONS — врачи, учредители
  Phase 6: SMI MENTIONS — упоминания в СМИ
  Phase 7: FORUM PAINS — боли пациентов с форумов
  Phase 8: FINANCE — финансовые данные
  Phase 9: CONTENT PLAN — контент-план
  Phase 10: HTML BUILD — сборка HTML-отчёта
  Phase 11: QC CRITIQUE — LLM-проверка качества (10 пунктов)
  Phase 12: PRESENTATION — финальная презентация

Все фазы выполняются СТРОГО последовательно.
NO_DATA — легитимный исход (не ошибка) для фаз с allow_no_data=True.
"""

from dataclasses import dataclass, field
from .states import PhaseContract


@dataclass
class Phase:
    """Определение одной фазы пайплайна.

    Attributes:
        id: Числовой идентификатор (0-based, порядок выполнения).
        name: Человекочитаемое имя фазы.
        tools: Имена инструментов для вызова (из registry).
        contract: PhaseContract с настройками ретраев и таймаутов.
        model: Модель LLM для интерпретации (None = использовать default).
        interactive: True если фаза требует ответа от клиента (пауза пайплайна).
        llm_interpret: True если нужна LLM-интерпретация данных фазы.
        interpretation_prompt: Промпт для LLM-интерпретации (None если не нужна).
    """
    id: int
    name: str
    tools: list[str] = field(default_factory=list)
    contract: PhaseContract = field(default_factory=PhaseContract)
    model: str | None = None
    interactive: bool = False
    llm_interpret: bool = True
    interpretation_prompt: str | None = None


# ── Фаза 0: PRE-FLIGHT ───────────────────────────────────────────────
PHASE_0_PREFLIGHT = Phase(
    id=0,
    name="PRE-FLIGHT",
    tools=[],
    contract=PhaseContract(
        max_retries=0,
        timeout=30,
        on_permanent_failure="abort",  # Без URL/City нельзя продолжать
    ),
    interactive=True,
    llm_interpret=False,
    interpretation_prompt=None,
)

# ── Фаза 0: PERPLEXITY (Deep Research) ────────────────────────────────
PHASE_0_PERPLEXITY = Phase(
    id=0,
    name="PERPLEXITY",
    tools=["perplexity_search"],
    contract=PhaseContract(
        max_retries=1,
        retry_on_key_exhaustion=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "КЛИНИКА: {client_name}. ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ: {client_specialization}.\n\n"
        "Ты работаешь с ГОТОВЫМ исследовательским отчётом Perplexity. "
        "Perplexity УЖЕ проверил источники. Твоя задача — СТРУКТУРИРОВАТЬ, а не перепроверять.\n\n"
        "ПРАВИЛА:\n"
        "1. ИЗВЛЕКАЙ всё, что есть в отчёте. Perplexity уже проверил достоверность.\n"
        "2. Оценки (estimate) — легитимные данные. Извлекай их.\n"
        "3. Если секция полностью отсутствует — «НЕТ ДАННЫХ».\n"
        "4. Город всегда {client_city}. Другой город — игнорируй.\n"
        "5. Только частные клиники (ООО, АО, ИП). Госучреждения — пропускай.\n"
        "6. БУДЬ КРАТКИМ. Каждая секция — 1-5 строк. Никаких эссе и подробных описаний.\n\n"
        "СТРУКТУРА ВЫВОДА (строго по порядку):\n\n"
        "=== РЫНОК ===\n"
        "- Объём рынка (рубли, год)\n"
        "- 2-3 тренда\n"
        "- Регулирование (лицензирование, ФЗ-152, ФЗ-38)\n\n"
        "=== КЛИЕНТ ===\n"
        "- ИНН: ...\n"
        "- ОГРН: ...\n"
        "- Полное название: ...\n"
        "- Год основания: ...\n"
        "- Лицензия: ...\n"
        "- Руководитель: ...\n\n"
        "=== ПАЦИЕНТЫ ===\n"
        "- Портрет (возраст, пол, доход)\n"
        "- Средний чек\n"
        "- Как ищут клинику\n\n"
        "=== ВОЗМОЖНОСТИ ===\n"
        "- Слабые места конкурентов\n"
        "- Незанятые ниши\n"
        "- Недоиспользованные каналы\n\n"
        "=== КОНКУРЕНТЫ ===\n"
        "ТОЛЬКО клиники с подтверждённым URL. Для каждой — СТРОГО одна строка:\n"
        "- Название: «...» | URL: https://... | Специализация: ... | Адрес: ...\n"
        "Без URL — НЕ включай. Максимум 7 конкурентов. "
        "Если нет — «НЕТ ДАННЫХ»."
    ),
)

# ── Фаза 1: COMPETITORS ──────────────────────────────────────────────
PHASE_1_COMPETITORS = Phase(
    id=1,
    name="COMPETITORS",
    tools=["find_competitors", "run_ci_analysis"],
    contract=PhaseContract(
        max_retries=3,
        retry_on_key_exhaustion=True,
        timeout=600,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Ты — старший аналитик агентства AIM. Твоя задача — построить "
        "СТРУКТУРИРОВАННЫЙ конкурентный анализ на основе данных, собранных инструментами "
        "find_competitors и run_ci_analysis.\n\n"

        "Данные, которые ты получишь:\n"
        "- competitor_details (список конкурентов с полями: name, url, revenue, revenue_trend, "
        "doctors_count, instagram_subscribers, instagram_username, seo_score, gm_rating, gm_reviews_count)\n"
        "- chat_summary (текстовый анализ из CI)\n"
        "- feature_matrix (сравнение фич)\n\n"

        "## ФОРМАТ ОТВЕТА (СТРОГО):\n\n"

        "### 1. Сравнительная таблица\n"
        "Markdown-таблица с колонками:\n"
        "| Конкурент | Выручка | Тренд | Врачей | Instagram | SEO |\n"
        "|-----------|---------|-------|--------|-----------|-----|\n\n"

        "Правила заполнения:\n"
        "- **Первая строка — КЛИЕНТ**, имя жирным (**Клиника X**)\n"
        "- Выручка: «4.3 млрд ₽», «742 млн ₽», «12.5 млн ₽» — форматируй читаемо\n"
        "- Тренд: «↑ Растущий (+79%)», «→ Стабильный», «↓ Падение (-15%)», «—»\n"
        "- Врачей: число из doctors_count, «—» если нет\n"
        "- Instagram: «@username (~587K)», «27K», «Нет» если нет username\n"
        "- SEO: «85/100», «—» если нет\n"
        "- Если данных нет — «—»\n\n"

        "### 2. Главный вывод\n"
        "> BLOCKQUOTE (1-2 предложения). Главный стратегический инсайт: "
        "где находится клиент относительно рынка, какая ключевая возможность или угроза.\n\n"

        "### 3. Сильные стороны клиента\n"
        "2-3 пункта, каждый с конкретным фактом (цифра из competitor_details):\n"
        "- Что у клиента лучше конкурентов? Где он уже выигрывает?\n\n"

        "### 4. Точки роста\n"
        "2-3 пункта, каждый с конкретным ориентиром (цифра конкурента-лидера):\n"
        "- Где клиент отстаёт? Что нужно догонять?\n\n"

        "**ВАЖНО:** Не выдумывай цифры. Если данных нет — честно пиши «—». "
        "Используй ТОЛЬКО данные из competitor_details.\n\n"

        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}"
    ),
)

# ── Фаза 2: TECH AUDIT ───────────────────────────────────────────────
PHASE_2_TECH_AUDIT = Phase(
    id=2,
    name="TECH AUDIT",
    tools=["run_pagespeed", "run_seo_audit"],
    contract=PhaseContract(
        max_retries=2,
        retry_on_key_exhaustion=True,
        timeout=300,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Технический аудит» финального отчёта для клиента. "
        "Ты пишешь для директора клиники — переводи технические метрики на язык бизнеса: "
        "как каждая проблема влияет на пациентов и запись.\n\n"
        "Проанализируй технический аудит сайта клиента: Pagespeed и SEO.\n\n"
        "## Формат ответа\n"
        "1. **Текущее состояние** — ключевые метрики (скорость загрузки, SEO-оценка, мобильная адаптация)\n"
        "2. **Что хорошо** — где сайт уже силён\n"
        "3. **Критические проблемы** — что влияет на пациентов и поисковую выдачу\n"
        "4. **Рекомендация** — что исправить в первую очередь (1-2 конкретных действия)\n\n"
        "Сравнивай с конкурентами из competitors_context. "
        "Если данные конкурентов недоступны — дай абсолютную оценку.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 3: SOCIAL VERIFIER ──────────────────────────────────────────
PHASE_3_SOCIAL = Phase(
    id=3,
    name="SOCIAL VERIFIER",
    tools=["run_review_platforms"],
    contract=PhaseContract(
        max_retries=2,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Репутация и отзывы» финального отчёта для клиента.\n\n"
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй отзывы и рейтинги клиники на всех платформах.\n\n"
        "## Формат ответа\n"
        "1. **Текущее состояние** — рейтинги по платформам, общее количество отзывов\n"
        "2. **Что хвалят** — главные сильные стороны в глазах пациентов (с примерами)\n"
        "3. **На что жалуются** — системные проблемы и репутационные риски\n"
        "4. **Рекомендация** — как улучшить репутацию (1-2 конкретных действия)\n\n"
        "Сравнивай с конкурентами из competitors_context: у кого выше рейтинг, "
        "больше отзывов, лучше вовлечённость. "
        "Если данные конкурентов недоступны — дай абсолютную оценку.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 4: CONTENT ANALYSIS ─────────────────────────────────────────
PHASE_4_CONTENT = Phase(
    id=4,
    name="CONTENT ANALYSIS",
    tools=["run_content_analysis"],
    contract=PhaseContract(
        max_retries=1,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Контент-анализ» финального отчёта для клиента.\n\n"
        "Проанализируй контент сайта клиники.\n\n"
        "## Формат ответа\n"
        "1. **Текущее состояние** — какие типы страниц есть, общий объём, качество текстов\n"
        "2. **Сильные страницы** — что работает хорошо (с конкретными примерами)\n"
        "3. **Пробелы vs конкуренты** — каких страниц/тем нет, что есть у конкурентов\n"
        "4. **Рекомендация** — что добавить в первую очередь (1-2 типа контента)\n\n"
        "Сравнивай с конкурентами из competitors_context: у кого больше контента, "
        "какие темы покрыты, какие форматы используют. "
        "Если данные конкурентов недоступны — дай абсолютную оценку.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 5: KEY PERSONS ──────────────────────────────────────────────
PHASE_5_KEY_PERSONS = Phase(
    id=5,
    name="KEY PERSONS",
    tools=["run_hh_analysis", "run_doctor_dossiers"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Команда» финального отчёта для клиента.\n\n"
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй данные о врачах и ключевых сотрудниках клиники. "
        "Учитывай, что это клиника специализации «{client_specialization}» в городе {client_city}. "
        "Оцени команду против конкурентов из Perplexity-контекста — в чём их преимущество или отставание. "
        "Выдели: (1) сильные специалисты (опыт, регалии), (2) кадровые пробелы, "
        "(3) кого можно продвигать как лицо клиники. 3-5 предложений.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, конкуренты, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 6: SMI MENTIONS ─────────────────────────────────────────────
PHASE_6_SMI = Phase(
    id=6,
    name="SMI MENTIONS",
    tools=["run_smi_mentions"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Медийность» финального отчёта для клиента.\n\n"
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй упоминания клиники в СМИ. "
        "Учитывай, что это клиника в городе {client_city}, специализация — {client_specialization}. "
        "Оцени медийный охват относительно конкурентов из competitors_context. "
        "Выдели: (1) тональность, "
        "(2) ключевые публикации, (3) медийный охват, "
        "(4) возможности для PR. Если упоминаний нет — отметь это. 3-5 предложений.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 7: FORUM PAINS ──────────────────────────────────────────────
PHASE_7_FORUM_PAINS = Phase(
    id=7,
    name="FORUM PAINS",
    tools=["web_search"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Боли пациентов» финального отчёта для клиента.\n\n"
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй обсуждения пациентов на форумах о клиниках этой специализации "
        "в этом городе. Сопоставь с рыночной картиной из Perplexity-контекста. "
        "Выдели: (1) главные боли пациентов, (2) что их бесит, "
        "(3) что они ищут и не находят, (4) как клиника может это использовать. "
        "4-6 предложений. Если данных нет — отметь это.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 8: FINANCE ──────────────────────────────────────────────────
PHASE_8_FINANCE = Phase(
    id=8,
    name="FINANCE",
    tools=["find_company_financials"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=60,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Финансы» финального отчёта для клиента.\n\n"
        "Проанализируй финансовые данные клиники: выручка, прибыль, тренды. "
        "Оцени их в контексте рынка из Perplexity-анализа — "
        "это много или мало для ниши {client_specialization} в городе {client_city}? "
        "Сравни с выручкой конкурентов из competitors_context — "
        "клиника крупнее, сопоставима или меньше конкурентов? "
        "Выдели: (1) финансовое здоровье, (2) тренд (растёт/падает/стабильно), "
        "(3) потенциал для инвестиций в маркетинг. "
        "Если данных нет — не выдумывай, отметь что данных нет. 3-4 предложения.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 9: CONTENT PLAN ────────────────────────────────────────────
PHASE_9_CONTENT_PLAN = Phase(
    id=9,
    name="CONTENT PLAN",
    tools=["run_content_gaps"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Твой анализ попадёт в секцию «Контент-план» финального отчёта для клиента.\n\n"
        "Проанализируй контентные пробелы и предложи контент-план. "
        "Используй Perplexity-контекст: какие темы и форматы выигрывают у конкурентов? "
        "На какие боли пациентов (из форумов) нужно ответить контентом? "
        "Выдели: (1) какие типы контента отсутствуют, (2) приоритетные темы, "
        "(3) какие форматы лучше использовать (статьи, видео, подкасты). "
        "4-6 предложений. Если данных нет — предложи общие рекомендации.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):\n{perplexity_context}\n\n"
        "КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):\n{competitors_context}"
    ),
)

# ── Фаза 10: HTML BUILD ──────────────────────────────────────────────
PHASE_10_HTML_BUILD = Phase(
    id=10,
    name="HTML BUILD",
    tools=["generate_html_report"],
    contract=PhaseContract(
        max_retries=2,
        timeout=120,
    ),
    interactive=True,
    llm_interpret=False,
    interpretation_prompt=None,
)

# ── Фаза 11: QC CRITIQUE ─────────────────────────────────────────────
PHASE_11_QC = Phase(
    id=11,
    name="QC CRITIQUE",
    tools=[],
    contract=PhaseContract(
        max_retries=0,
        timeout=90,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Ты — контролёр качества. Проверь готовый отчёт по 10 пунктам:\n"
        "1. Все ли цифры из реальных данных (не выдуманы)?\n"
        "2. Нет ли пустых секций?\n"
        "3. Корректны ли названия клиник/конкурентов? Сверь с Perplexity-контекстом.\n"
        "4. Логичны ли выводы?\n"
        "5. Нет ли противоречий между секциями?\n"
        "6. Бизнес-язык или технический жаргон?\n"
        "7. Правильно ли посчитаны цены?\n"
        "8. Есть ли конкретные KPI?\n"
        "9. Юридическая чистота (нет обещаний «гарантируем места»)?\n"
        "10. Общее впечатление: WOW или скучно?\n\n"
        "Дай оценку по каждому пункту: PASS / FAIL / WARN. "
        "Если есть FAIL — укажи что исправить. Без комплиментов, только факты.\n\n"
        "КОНТЕКСТ ОТ PERPLEXITY (для сверки фактов):\n{perplexity_context}"
    ),
)

# ── Фаза 12: PRESENTATION ────────────────────────────────────────────
PHASE_12_PRESENTATION = Phase(
    id=12,
    name="PRESENTATION",
    tools=["publish_scout_report"],
    contract=PhaseContract(
        max_retries=2,
        timeout=60,
    ),
    interactive=True,
    llm_interpret=False,
    interpretation_prompt=None,
)


# ── Полный список фаз в порядке выполнения ──────────────────────────
PHASES: list[Phase] = [
    PHASE_0_PERPLEXITY,
    PHASE_1_COMPETITORS,
    PHASE_2_TECH_AUDIT,
    PHASE_3_SOCIAL,
    PHASE_4_CONTENT,
    PHASE_5_KEY_PERSONS,
    PHASE_6_SMI,
    PHASE_7_FORUM_PAINS,
    PHASE_8_FINANCE,
    PHASE_9_CONTENT_PLAN,
    PHASE_10_HTML_BUILD,
    PHASE_11_QC,
    PHASE_12_PRESENTATION,
]
