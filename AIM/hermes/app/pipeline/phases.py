"""Hermes v7 — Phase Definitions (16 фаз).

16-фазный онбординг-пайплайн. Каждая фаза — изолированный шаг сбора данных.

Поток данных:
  Phase 0:   PRE-FLIGHT — приём вводных, верификация
  Phase 0.5: INSTAGRAM PROFILE — поиск Instagram-аккаунта
  Phase 0.75: INSTAGRAM CONTENT — анализ контента IG
  Phase 0.8: ADS INTELLIGENCE — рекламная активность
  Phase 1:   TECH AUDIT: SPEED — PageSpeed
  Phase 2:   TECH AUDIT: SEO+OSINT — SEO-аудит
  Phase 3:   SOCIAL: CROSS-PLATFORM — соцсети
  Phase 3.2: TELEGRAM CHANNELS — Telegram-каналы
  Phase 3.5: KEY PERSONS — врачи, вакансии
  Phase 3.6: SMI MENTIONS — упоминания в СМИ
  Phase 4:   COMPETITOR MATRIX — поиск + CI-анализ (критическая)
  Phase 5:   RATINGS & REVIEWS — рейтинги и отзывы
  Phase 6:   FINANCIAL: FNS+ — финансовые данные
  Phase 7:   GAPS & ADVANTAGES — контентные пробелы и преимущества
  Phase 8:   DATA ASSEMBLY — сборка HTML-отчёта
  Phase 9:   VALIDATION — LLM QC проверка
  Phase 10:  PRESENTATION — финальная презентация

Все фазы выполняются СТРОГО последовательно.
NO_DATA — легитимный исход (не ошибка) для фаз с allow_no_data=True.
"""

from dataclasses import dataclass, field
from .states import PhaseContract


@dataclass
class Phase:
    """Определение одной фазы пайплайна.

    Attributes:
        id: Числовой идентификатор (float для подфаз: 0.5, 0.75, 3.2).
        name: Человекочитаемое имя фазы.
        tools: Имена инструментов для вызова (из registry).
        contract: PhaseContract с настройками ретраев и таймаутов.
        model: Модель LLM для интерпретации (None = использовать default).
        interactive: True если фаза требует ответа от клиента (пауза пайплайна).
        llm_interpret: True если нужна LLM-интерпретация данных фазы.
        interpretation_prompt: Промпт для LLM-интерпретации (None если не нужна).
    """
    id: float
    name: str
    tools: list[str] = field(default_factory=list)
    contract: PhaseContract = field(default_factory=PhaseContract)
    model: str | None = None
    interactive: bool = False
    llm_interpret: bool = True
    interpretation_prompt: str | None = None


# ── Фаза 0: PRE-FLIGHT ────────────────────────────────────────────────
PHASE_0_PREFLIGHT = Phase(
    id=0.0,
    name="PRE-FLIGHT",
    tools=["web_search"],
    contract=PhaseContract(
        max_retries=0,
        timeout=60,
        on_permanent_failure="abort",
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Ты — аналитик, а не агент. Не говори «попробую», «запускаю» — просто анализируй.\n\n"
        "ГОРОД КЛИНИКИ УЖЕ ОПРЕДЕЛЁН: {client_city}. "
        "СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}. "
        "НЕ пытайся определить город или специализацию сам — используй указанные выше.\n\n"
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


# ── Фаза 0.5: INSTAGRAM PROFILE ───────────────────────────────────────
PHASE_0_5_INSTAGRAM_PROFILE = Phase(
    id=0.5,
    name="INSTAGRAM PROFILE",
    tools=["web_search"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Найди Instagram-аккаунт клиники. Собери: "
        "(1) подписчики, (2) количество постов, (3) bio/описание, "
        "(4) externalUrl/ссылка, (5) категория бизнеса.\n"
        "Найди также связанные аккаунты и аккаунт CEO/основателя если есть.\n"
        "Если Instagram не найден — отметь это. 4-6 предложений."
    ),
)


# ── Фаза 0.75: INSTAGRAM CONTENT ──────────────────────────────────────
PHASE_0_75_INSTAGRAM_CONTENT = Phase(
    id=0.75,
    name="INSTAGRAM CONTENT",
    tools=["web_search"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй контент Instagram клиники: "
        "(1) Engagement Rate (ER), "
        "(2) доминирующий формат (Video/Sidecar/Image), "
        "(3) темы контента (3-5 ключевых), "
        "(4) топ-3 и худший пост, "
        "(5) формат подачи (шоу/интрига/авторская/школа/до-после), "
        "(6) контентные пробелы.\n"
        "Оцени контент-стратегию, найди сильные и слабые стороны. "
        "4-6 предложений."
    ),
)


# ── Фаза 0.8: ADS INTELLIGENCE ────────────────────────────────────────
PHASE_0_8_ADS_INTELLIGENCE = Phase(
    id=0.8,
    name="ADS INTELLIGENCE",
    tools=["web_search"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Найди активную рекламу клиники: Facebook Ad Library, Telegram Ads, LinkedIn Ads.\n"
        "Собери: (1) количество объявлений, (2) платформы, (3) форматы, "
        "(4) ключевые месседжи, (5) CTA-паттерны, (6) лендинги.\n"
        "Оцени рекламную стратегию, бюджет, качество креативов. "
        "Если рекламы нет — отметь это. 4-6 предложений."
    ),
)


# ── Фаза 1: TECH AUDIT — SPEED ───────────────────────────────────────
PHASE_1_TECH_AUDIT_SPEED = Phase(
    id=1.0,
    name="TECH AUDIT: SPEED",
    tools=["run_pagespeed"],
    contract=PhaseContract(
        max_retries=2,
        retry_on_key_exhaustion=True,
        timeout=300,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй технический аудит скорости сайта клиента: "
        "Performance, Accessibility, Best Practices, SEO. "
        "Core Web Vitals: LCP, FCP, TBT, CLS. Статус CWV: Passed/Failed.\n"
        "Переведи на бизнес-язык: как проблемы скорости влияют на пациентов. "
        "4-6 предложений."
    ),
)


# ── Фаза 2: TECH AUDIT — SEO + OSINT ─────────────────────────────────
PHASE_2_TECH_AUDIT_SEO = Phase(
    id=2.0,
    name="TECH AUDIT: SEO+OSINT",
    tools=["run_seo_audit"],
    contract=PhaseContract(
        max_retries=2,
        retry_on_key_exhaustion=True,
        timeout=300,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй SEO-аудит сайта клиента: "
        "(1) технические SEO-проблемы, (2) позиции по ключевым словам, "
        "(3) CMS и аналитика (Метрика, GA4), "
        "(4) OSINT: DNS, SSL, WHOIS, HTTP-заголовки безопасности, "
        "(5) SEO Content Gap: темы конкурентов, которых нет у клиента.\n"
        "Переведи на бизнес-язык: как эти проблемы влияют на поисковую видимость и пациентов. "
        "4-6 предложений."
    ),
)


# ── Фаза 3: SOCIAL — CROSS-PLATFORM ───────────────────────────────────
PHASE_3_SOCIAL = Phase(
    id=3.0,
    name="SOCIAL: CROSS-PLATFORM",
    tools=["web_search", "run_review_platforms"],
    contract=PhaseContract(
        max_retries=2,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй присутствие клиники на всех платформах: "
        "Telegram, VK, YouTube, Дзен, Одноклассники, Rutube, Likee.\n"
        "Для каждой: подписчики, активность, дата последнего поста.\n"
        "Собери карту социального присутствия. "
        "Учитывай, что это клиника специализации «{client_specialization}» в городе {client_city}. "
        "4-6 предложений."
    ),
)


# ── Фаза 3.2: TELEGRAM CHANNELS ───────────────────────────────────────
PHASE_3_2_TELEGRAM = Phase(
    id=3.2,
    name="TELEGRAM CHANNELS",
    tools=["web_search"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Найди Telegram-каналы клиники и CEO: "
        "(1) подписчики, (2) частота постов, (3) средние просмотры, "
        "(4) формат контента (новости/экспертиза/акции/закулисье), "
        "(5) тональность, (6) вовлечение.\n"
        "Оцени Telegram-присутствие как канал привлечения пациентов. "
        "Если каналов нет — отметь это. 3-5 предложений."
    ),
)


# ── Фаза 3.5: KEY PERSONS — DOCTORS ──────────────────────────────────
PHASE_3_5_KEY_PERSONS = Phase(
    id=3.5,
    name="KEY PERSONS",
    tools=["run_doctor_dossiers", "run_hh_analysis"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй данные о врачах и ключевых сотрудниках клиники. "
        "Учитывай, что это клиника специализации «{client_specialization}» в городе {client_city}. "
        "Выдели: (1) сильные специалисты (опыт, регалии, star/core/team), "
        "(2) кадровые пробелы (вакансии на HH.ru), "
        "(3) кого можно продвигать как лицо клиники. 3-5 предложений."
    ),
)


# ── Фаза 3.6: SMI MENTIONS ────────────────────────────────────────────
PHASE_3_6_SMI = Phase(
    id=3.6,
    name="SMI MENTIONS",
    tools=["run_smi_mentions"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй упоминания клиники в СМИ: "
        "Business (forbes.ru, rbc.ru, kommersant.ru), "
        "Glossy (marieclaire.ru, vogue.ru), "
        "Medical (vademec.ru), "
        "Regional (fontanka.ru, dp.ru, sobaka.ru), "
        "Telegram-СМИ (Mash, Baza, 112, SHOT).\n"
        "Выдели: (1) тональность, (2) ключевые публикации, (3) медийный охват, "
        "(4) возможности для PR. Если упоминаний нет — отметь это. 3-5 предложений."
    ),
)


# ── Фаза 4: COMPETITOR MATRIX (КРИТИЧЕСКАЯ) ──────────────────────────
PHASE_4_COMPETITOR_MATRIX = Phase(
    id=4.0,
    name="COMPETITOR MATRIX",
    tools=["find_competitors", "run_ci_analysis"],
    contract=PhaseContract(
        max_retries=3,
        retry_on_key_exhaustion=True,
        timeout=600,
        on_permanent_failure="abort",  # Критическая фаза — без конкурентов отчёт теряет смысл
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй конкурентную среду клиники. "
        "Выдели: (1) топ-3 прямых конкурента и их преимущества, "
        "(2) SWOT для каждого конкурента, "
        "(3) Positioning Map (X: простота↔мощность, Y: бюджет↔премиум), "
        "(4) Feature Comparison Matrix, "
        "(5) Pricing Comparison Matrix, "
        "(6) слабые места конкурентов (где клиника может выиграть), "
        "(7) тактики конкурентов, которые стоит перенять, "
        "(8) рыночные gap'ы. "
        "Определи позицию клиники в матрице: лидер/претендент/нишевой/слабый. "
        "5-8 предложений."
    ),
)


# ── Фаза 5: RATINGS & REVIEWS ─────────────────────────────────────────
PHASE_5_RATINGS = Phase(
    id=5.0,
    name="RATINGS & REVIEWS",
    tools=["run_review_platforms"],
    contract=PhaseContract(
        max_retries=2,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "ГОРОД: {client_city}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: {client_specialization}.\n\n"
        "Проанализируй рейтинги и отзывы клиники: "
        "ProDoctorov, Яндекс.Карты, 2ГИС, Google Maps.\n"
        "Отзовики: otzovik.com, irecommend.ru, zoon.ru.\n"
        "Форумы: woman.ru.\n"
        "Собери: rating, count, positive_themes, negative_themes, key_quote.\n"
        "Выдели: (1) общий рейтинг по платформам, (2) что хвалят пациенты, "
        "(3) на что жалуются, (4) репутационные риски. 4-6 предложений."
    ),
)


# ── Фаза 6: FINANCIAL — FNS+ ──────────────────────────────────────────
PHASE_6_FINANCE = Phase(
    id=6.0,
    name="FINANCIAL: FNS+",
    tools=["find_company_financials"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=120,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй финансовые данные клиники: "
        "выручка, прибыль, сотрудники, ОКВЭД.\n"
        "Проверь также: HeadHunter (вакансии), госзакупки (zakupki.gov.ru), "
        "арбитражные дела (kad.arbitr.ru).\n"
        "Выдели: (1) финансовое здоровье, (2) тренд (растёт/падает/стабильно), "
        "(3) индикаторы роста или сжатия, (4) потенциал для инвестиций в маркетинг. "
        "Если данных нет — не выдумывай, отметь что данных нет. 3-4 предложения."
    ),
)


# ── Фаза 7: GAPS & ADVANTAGES ─────────────────────────────────────────
PHASE_7_GAPS = Phase(
    id=7.0,
    name="GAPS & ADVANTAGES",
    tools=["run_content_gaps", "run_content_analysis"],
    contract=PhaseContract(
        max_retries=1,
        allow_no_data=True,
        timeout=180,
    ),
    llm_interpret=True,
    interpretation_prompt=(
        "Проанализируй контентные пробелы и преимущества клиники: "
        "(1) 3+ gaps — что клиент делает ХУЖЕ конкурентов, "
        "(2) 3+ advantages — что клиент делает ЛУЧШЕ, "
        "(3) 2-3 wow_insights, "
        "(4) 5-10 Steal-Worthy Tactics (тактики конкурентов, которые стоит перенять), "
        "(5) Messaging Differentiation Strategy.\n"
        "Сформулируй стратегические выводы на основе всех собранных данных. "
        "5-8 предложений."
    ),
)


# ── Фаза 8: DATA ASSEMBLY ─────────────────────────────────────────────
PHASE_8_DATA_ASSEMBLY = Phase(
    id=8.0,
    name="DATA ASSEMBLY",
    tools=["generate_html_report"],
    contract=PhaseContract(
        max_retries=2,
        timeout=120,
    ),
    interactive=True,
    llm_interpret=False,
    interpretation_prompt=None,
)


# ── Фаза 9: VALIDATION ────────────────────────────────────────────────
PHASE_9_VALIDATION = Phase(
    id=9.0,
    name="VALIDATION",
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
        "Два цикла проверки: все фазы 0-8 проверены, [ ] → [x]. "
        "JSON валиден. Нет длинных тире (—). Нет слова «EGRUL». "
        "Все обязательные ключи присутствуют. UTF-8.\n"
        "Дай оценку по каждому пункту: PASS / FAIL / WARN. "
        "Если есть FAIL — укажи что исправить. Без комплиментов, только факты."
    ),
)


# ── Фаза 10: PRESENTATION ─────────────────────────────────────────────
PHASE_10_PRESENTATION = Phase(
    id=10.0,
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


# ── Полный список фаз в порядке выполнения (16 фаз) ───────────────────
PHASES: list[Phase] = [
    PHASE_0_PREFLIGHT,
    PHASE_0_5_INSTAGRAM_PROFILE,
    PHASE_0_75_INSTAGRAM_CONTENT,
    PHASE_0_8_ADS_INTELLIGENCE,
    PHASE_1_TECH_AUDIT_SPEED,
    PHASE_2_TECH_AUDIT_SEO,
    PHASE_3_SOCIAL,
    PHASE_3_2_TELEGRAM,
    PHASE_3_5_KEY_PERSONS,
    PHASE_3_6_SMI,
    PHASE_4_COMPETITOR_MATRIX,
    PHASE_5_RATINGS,
    PHASE_6_FINANCE,
    PHASE_7_GAPS,
    PHASE_8_DATA_ASSEMBLY,
    PHASE_9_VALIDATION,
    PHASE_10_PRESENTATION,
]
