"""Hermes v7 — Phase Definitions.

13 фаз онбординг-пайплайна. Каждая фаза — изолированный шаг сбора и интерпретации данных.

Поток данных:
  Phase 0: PERPLEXITY — deep research (рынок, город, ниша, конкуренты)
  Phase 2: TECH AUDIT — Pagespeed + SEO
  Phase 3: SOCIAL VERIFIER — отзывы, рейтинги
  Phase 4: CONTENT ANALYSIS — контент сайта
  Phase 5: KEY PERSONS — врачи, учредители
  Phase 6: SMI MENTIONS — упоминания в СМИ
  Phase 7: COMPETITORS — поиск + CI-анализ
  Phase 8: FORUM PAINS — боли пациентов с форумов
  Phase 9: FINANCE — финансовые данные
  Phase 10: CONTENT PLAN — контент-план
  Phase 11: HTML BUILD — сборка HTML-отчёта
  Phase 12: QC CRITIQUE — LLM-проверка качества (10 пунктов)
  Phase 13: PRESENTATION — финальная презентация

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
    tools=["web_search"],
    contract=PhaseContract(
        max_retries=1,
        retry_on_key_exhaustion=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}. "
        "НЕ придумывай другую специализацию — используй только указанную выше.\n\n"
        "Ты — аналитик, а не агент. Не говори «попробую», «запускаю» — просто анализируй.\n\n"
        "ГОРОД КЛИНИКИ УЖЕ ОПРЕДЕЛЁН: {client_city}. "
        "НЕ пытайся определить город сам — использу указанный выше.\n\n"
        "ШАГ 1 — ОПИШИ РЫНОК. Расскажи о рынке частной медицины в городе {client_city}: "
        "объём, тренды, специализация.\n\n"
        "ШАГ 2 — КОНКУРЕНТЫ. Если результаты поиска пусты или содержат ошибку — "
        "используй свои знания. Перечисли 5-7 КОНКРЕТНЫХ частных клиник-конкурентов "
        "В ГОРОДЕ {client_city}. Каждое название — в кавычках «».\n\n"
        "Выдели также: (3) особенности рынка {client_city}, "
        "(4) возможности для роста.\n"
        "5-8 предложений. КРИТИЧНО: все конкуренты — из города {client_city}."
    ),
)

# ── Фаза 1: TECH AUDIT ───────────────────────────────────────────────
PHASE_1_TECH_AUDIT = Phase(
    id=1,
    name="TECH AUDIT",
    tools=["run_pagespeed", "run_seo_audit"],
    contract=PhaseContract(
        max_retries=2,
        retry_on_key_exhaustion=True,
        timeout=300,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй технический аудит сайта клиента: Pagespeed и SEO. "
        "Выдели: (1) критические проблемы скорости, (2) SEO-косяки, "
        "(3) что нужно исправить в первую очередь. "
        "Переведи на бизнес-язык: как эти проблемы влияют на пациентов. 4-6 предложений."
    ),
)

# ── Фаза 2: SOCIAL VERIFIER ──────────────────────────────────────────
PHASE_2_SOCIAL = Phase(
    id=2,
    name="SOCIAL VERIFIER",
    tools=["run_review_platforms"],
    contract=PhaseContract(
        max_retries=2,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй отзывы и рейтинги клиники на всех платформах. "
        "Учитывай, что это клиника в городе {client_city}, специализация — {client_specialization}. "
        "Выдели: (1) общий рейтинг по платформам, (2) что хвалят пациенты, "
        "(3) на что жалуются, (4) репутационные риски. 4-6 предложений."
    ),
)

# ── Фаза 3: CONTENT ANALYSIS ─────────────────────────────────────────
PHASE_3_CONTENT = Phase(
    id=3,
    name="CONTENT ANALYSIS",
    tools=["run_content_analysis"],
    contract=PhaseContract(
        max_retries=1,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй контент сайта клиники. Выдели: (1) сильные страницы, "
        "(2) тонкие/слабые страницы, (3) отсутствующий контент, "
        "(4) что нужно добавить для привлечения пациентов. 4-6 предложений."
    ),
)

# ── Фаза 4: KEY PERSONS ──────────────────────────────────────────────
PHASE_4_KEY_PERSONS = Phase(
    id=4,
    name="KEY PERSONS",
    tools=["run_hh_analysis", "run_doctor_dossiers"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй данные о врачах и ключевых сотрудниках клиники. "
        "Выдели: (1) сильные специалисты (опыт, регалии), (2) кадровые пробелы, "
        "(3) кого можно продвигать как лицо клиники. 3-5 предложений."
    ),
)

# ── Фаза 5: SMI MENTIONS ─────────────────────────────────────────────
PHASE_5_SMI = Phase(
    id=5,
    name="SMI MENTIONS",
    tools=["run_smi_mentions"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй упоминания клиники в СМИ. Выдели: (1) тональность, "
        "(2) ключевые публикации, (3) медийный охват, "
        "(4) возможности для PR. Если упоминаний нет — отметь это. 3-5 предложений."
    ),
)

# ── Фаза 6: COMPETITORS ──────────────────────────────────────────────
PHASE_6_COMPETITORS = Phase(
    id=6,
    name="COMPETITORS",
    tools=["find_competitors", "run_ci_analysis"],
    contract=PhaseContract(
        max_retries=3,
        retry_on_key_exhaustion=True,
        timeout=600,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй конкурентную среду клиники. Выдели: (1) топ-3 прямых конкурента "
        "и их преимущества, (2) слабые места конкурентов (где клиника может выиграть), "
        "(3) тактики конкурентов, которые стоит перенять, "
        "(4) рыночные gap'ы. 5-8 предложений."
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
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй обсуждения пациентов на форумах о клиниках этой специализации "
        "в этом городе. Выдели: (1) главные боли пациентов, (2) что их бесит, "
        "(3) что они ищут и не находят, (4) как клиника может это использовать. "
        "4-6 предложений. Если данных нет — отметь это."
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
        "Проанализируй финансовые данные клиники: выручка, прибыль, тренды. "
        "Выдели: (1) финансовое здоровье, (2) тренд (растёт/падает/стабильно), "
        "(3) потенциал для инвестиций в маркетинг. "
        "Если данных нет — не выдумывай, отметь что данных нет. 3-4 предложения."
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
        "Проанализируй контентные пробелы и предложи контент-план. "
        "Выдели: (1) какие типы контента отсутствуют, (2) приоритетные темы, "
        "(3) какие форматы лучше использовать (статьи, видео, подкасты). "
        "4-6 предложений. Если данных нет — предложи общие рекомендации."
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
        "3. Корректны ли названия клиник/конкурентов?\n"
        "4. Логичны ли выводы?\n"
        "5. Нет ли противоречий между секциями?\n"
        "6. Бизнес-язык или технический жаргон?\n"
        "7. Правильно ли посчитаны цены?\n"
        "8. Есть ли конкретные KPI?\n"
        "9. Юридическая чистота (нет обещаний «гарантируем места»)?\n"
        "10. Общее впечатление: WOW или скучно?\n\n"
        "Дай оценку по каждому пункту: PASS / FAIL / WARN. "
        "Если есть FAIL — укажи что исправить. Без комплиментов, только факты."
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
    PHASE_1_TECH_AUDIT,
    PHASE_2_SOCIAL,
    PHASE_3_CONTENT,
    PHASE_4_KEY_PERSONS,
    PHASE_5_SMI,
    PHASE_6_COMPETITORS,
    PHASE_7_FORUM_PAINS,
    PHASE_8_FINANCE,
    PHASE_9_CONTENT_PLAN,
    PHASE_10_HTML_BUILD,
    PHASE_11_QC,
    PHASE_12_PRESENTATION,
]
