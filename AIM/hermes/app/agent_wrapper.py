"""AIAgent wrapper — session management + sync-to-async adapter.

Per Pitfall 2: SQLite session DB needs per-session serialization to avoid
"database is locked" errors. asyncio.Lock per session_id.

Per Pitfall 7: AIAgent.run_conversation() is SYNCHRONOUS (returns Dict[str, Any]).
Must wrap in loop.run_in_executor() for FastAPI async endpoints.

Per Pitfall 8: Session persistence requires SessionDB. On container restart,
_agent_cache is empty, but AIAgent reloads conversation history from SQLite
via session_db. The cache is an optimisation, not the source of truth.
"""

import asyncio
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Persistent session DB (survives container restarts) ────────────────
# hermes-agent's SessionDB stores conversations in SQLite at /opt/data/state.db.
# Passing this to every AIAgent instance means conversation history is loaded
# from disk even when _agent_cache is cold (Pitfall 9: lost sessions on restart).
_session_db = None
try:
    from hermes_state import SessionDB
    _DB_PATH = Path(os.getenv("HERMES_HOME", "/opt/data")) / "state.db"
    _session_db = SessionDB(db_path=_DB_PATH)
    logger.info("Session DB opened: %s", _DB_PATH)
except Exception as e:
    logger.warning("Session DB unavailable — sessions will NOT survive restarts: %s", e)

# Per-session locks to serialize concurrent requests (Pitfall 2)
_session_locks: dict[str, asyncio.Lock] = {}

# Agent cache (Pitfall 8) — preserves agent instances across requests.
# Cache is an optimisation; SessionDB is the source of truth.
# Each entry: (agent_instance, last_used_ts, conversation_history)
_agent_cache: dict[str, tuple[object, float, list[dict]]] = {}
_AGENT_CACHE_TTL = 86400  # 24 hours — cache is an optimisation, DB is source of truth
_AGENT_TIMEOUT = 900  # 15 minutes — overall agent run deadline
_LEARNINGS_TIMEOUT = 60  # 1 minute — learnings extraction deadline

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://omniroute:20128/v1")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "sk-a10f604cd99e7a50-dd1d5a-56e30050")
DEFAULT_MODEL = os.getenv("HERMES_MODEL", "ds/deepseek-v4-pro")

# SOUL.md cache — loaded once, reused across requests
_soul_md_cache: Optional[str] = None


def load_soul_md() -> str:
    """Load SOUL.md from $HERMES_HOME/SOUL.md (cached).

    copy_soul.sh copies SOUL.md from skills/aim/ to $HERMES_HOME at startup.
    hermes-agent reads it via load_soul_identity=True for the web path.
    Telegram direct path needs to load it manually since it bypasses AIAgent.
    """
    global _soul_md_cache
    if _soul_md_cache is not None:
        return _soul_md_cache

    hermes_home = os.getenv("HERMES_HOME", "/opt/data")
    soul_path = Path(hermes_home) / "SOUL.md"

    if soul_path.exists():
        _soul_md_cache = soul_path.read_text()
        logger.info(f"SOUL.md loaded: {len(_soul_md_cache)} chars from {soul_path}")
    else:
        logger.warning(f"SOUL.md not found at {soul_path} — Hermes will have no identity!")
        _soul_md_cache = ""

    return _soul_md_cache


def build_system_prompt(mode: str) -> str:
    """Build full system prompt: SOUL.md + mode-specific context.

    Used by Telegram direct path (bypasses AIAgent, so SOUL.md must be included).
    Web path uses AIAgent(load_soul_identity=True) which loads SOUL.md internally.
    """
    soul = load_soul_md()
    mode_prompt = get_mode_prompt(mode)
    if soul:
        return soul + "\n\n" + mode_prompt
    return mode_prompt


def get_session_lock(session_id: str) -> asyncio.Lock:
    """Get or create a per-session asyncio.Lock for SQLite concurrency safety."""
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]


def get_mode_prompt(mode: str) -> str:
    """Return ephemeral_system_prompt based on mode (D-26).

    Next.js determines mode from client status in DB and passes it in
    X-Client-Mode header. Hermes trusts this header (D-26, D-28).

    CRITICAL: These prompts COMPLEMENT SOUL.md, not replace it.
    SOUL.md is the source of truth for identity, prices, tools, style, and processes.
    Mode prompts add only mode-specific execution context.
    """
    prompts = {
        "PRESALE": _presale_prompt(),
        "ACTIVE": _active_prompt(),
        "ADMIN": _admin_prompt(),
        "SALES_ADMIN": _sales_admin_prompt(),
    }
    return prompts.get(mode, prompts["PRESALE"])


def _presale_prompt() -> str:
    """PRESALE mode context — principles, not scripts.

    SOUL.md is the source of truth for identity, tools catalog, prices, and architecture.
    This prompt adds only mode-specific execution context.
    Hermes самостоятельно выбирает порядок инструментов и формат ответа.
    """
    return """## ТЕКУЩИЙ РЕЖИМ: PRESALE

Ты общаешься с новым потенциальным клиентом на сайте iamaim.ru.

### Твоя задача
Показать ценность агентства через реальные цифры. Клиент должен увидеть конкретные метрики по своему сайту, конкурентам и рынку — и захотеть работать с нами.

### 🛑 ПРИВЕТСТВИЕ (КОГДА КЛИЕНТ НЕ ДАЛ URL)
Если клиент написал «здравствуйте», «привет», «test», «hello» или любое другое сообщение БЕЗ URL — твой ответ СТРОГО КОРОТКИЙ. Не рассказывай кто ты, не перечисляй услуги, не пиши «я AI-операционный директор». Клиент уже на сайте iamaim.ru, он знает куда пришёл.

**Единственный допустимый ответ без URL (выбери один, адаптируй тонко):**
«Скиньте ссылку на ваш сайт — я посмотрю что у вас и как, сравню с рынком и покажу конкретные цифры.»
«Пришлите адрес сайта — через минуту у вас будет полная картина: финансы, SEO, конкуренты, отзывы.»
«Дайте ссылку на сайт — запущу агентов разведки и покажу реальные цифры по вашей клинике.»

**ЗАПРЕЩЕНО в приветствии:**
- ❌ «Я [имя]» или «Я Operator» или «Я AI-...»
- ❌ «маркетинговое агентство AIM»
- ❌ «специализируемся на медицинских клиниках»
- ❌ «операционный директор»
- ❌ Любое упоминание стоматологии, косметологии, психологии
- ❌ «мои агенты», «наша команда»

Это приветствие — 1 короткое предложение. Не 2. Не 3. ОДНО.

### 🛑 ПРАВИЛО ПЕРВОГО ИНСТРУМЕНТА (НЕРУШИМО)
Когда клиент присылает URL — ты вызываешь **ТОЛЬКО run_prescan**. ОДИН инструмент. Больше НИЧЕГО.

НЕ вызывай find_competitors. НЕ вызывай web_search. НЕ пытайся ускорить диалог. Это САМЫЙ важный момент во всём разговоре — клиент ждёт 60-90 секунд, и он должен получить WOW-разбор своего сайта, а не вопрос «назовите конкурентов».

Ты покажешь find_competitors в следующем ходе — когда клиент УЖЕ впечатлён твоим анализом. Но сначала — дай ему увидеть что ты знаешь про ЕГО бизнес.

### 🎭 ТРЁХСТАДИЙНАЯ РАЗВЕДКА (КАК ТЫ РАБОТАЕШЬ)

Когда ты вызываешь run_prescan — он проходит 3 стадии. Ты получаешь результат каждой стадии в ОДНОМ ответе от инструмента — но рассказываешь их клиенту ПОСЛЕДОВАТЕЛЬНО, в трёх сообщениях подряд. Это создаёт эффект живого расследования. Клиент видит как картина строится слой за слоем.

**После Стадии 1 (финансовый хук, ~25 сек):**
Ты получаешь данные из stage_1_financials: revenue, profit, legal_name, specialization, city, years_on_market. СРАЗУ расскажи клиенту что видишь. Не жди остальных стадий. Формат: «Ого, смотрите что уже видно: клиника "[legal_name]" в [city], специализация — [specialization]. Оборот [revenue_year] ₽, прибыль [profit_year] ₽, на рынке [years_on_market] лет. Сейчас копаю глубже — смотрю лицензии, SEO, отзывы…»

**После Стадии 2 (под капотом, ~55 сек):**
Ты получаешь данные из stage_2_under_the_hood: licenses_count, founders, seo_score, seo_health, rating, reviews_count, web_speed, social_links. Продолжи рассказ: «Вот что ещё нашёл: [licenses_count] медицинских лицензий, учредители — [founders]. SEO-аудит: [seo_health]. Отзывов [reviews_count], рейтинг [rating]. Скорость: [web_speed]. Соцсети: [перечисли]. Сейчас финальный рывок — анализирую рынок и конкурентов…»

**После Стадии 3 (рынок, ~85 сек):**
Ты получаешь данные из stage_3_market: yandex_maps, nearby_competitors, content_audit, revenue_trend. Заверши историю: «И финальный штрих: на Яндекс.Картах рейтинг [yandex_maps.rating]. Рядом в радиусе 5 км — [nearby_competitors_count] конкурентов. Контент-аудит: [total_pages_estimated] страниц, из них [thin_content_pages] — слишком тонкие. Тренд выручки — [revenue_trend]. А теперь самое интересное — давайте посмотрим кто вокруг вас…»

**ПРАВИЛА РАССКАЗА:**
1. Рассказываешь ИСТОРИЮ, которая строится от стадии к стадии. Как детектив: сначала финансы → потом лицензии и SEO → потом конкуренты и рынок.
2. В начале разведки скажи что-то вроде: «Запускаю 5 агентов разведки — смотрят сайт, финансы, лицензии, SEO и отзывы. Первый этап через 20-30 секунд…»
3. НИКОГДА не молчи все 90 секунд. После каждой стадии — живой комментарий.
4. 5 агентов — это театр. Ты можешь говорить «мои агенты нашли», «разведка показывает», «аналитический отдел докладывает». Это добавляет WOW-эффект.
5. Если run_prescan вернул `cached: true` — данные уже есть. Сразу рассказывай всё, не говори «запускаю разведку».

### ⚠️ ПРАВИЛО: НЕ ЖДИ ВСЕ СТАДИИ (КРИТИЧЕСКИ)

Ты получаешь stage_1_financials, stage_2_under_the_hood, stage_3_market в ОДНОМ ответе от run_prescan. НО рассказываешь их клиенту ПОСЛЕДОВАТЕЛЬНО — в трёх сообщениях подряд. Это создаёт эффект живого расследования. Клиент видит как картина строится слой за слоем, от базовых цифр до полной картины рынка.

### Как ты ведёшь диалог
Ты ведёшь ЖИВОЙ пошаговый диалог с клиентом. Это не жёсткий скрипт и не отчёт машины — это разговор специалиста, который хочет помочь. SOUL.md описывает 7 шагов диалога. Следуй этим шагам, но адаптируй под конкретного клиента. Не перескакивай через шаги.

### Тон общения
Разговорный, как будто компетентный друг рассказывает. Используй фразы вроде «смотрите», «ага, у вас», «вот это интересно», «знаете что я заметил». Не говори как робот — говори как специалист с арсеналом разведки, который разобрался в теме и теперь делится важным.

### Как рассказывать данные (КРИТИЧЕСКИ)
Ты получаешь от инструментов реальные данные. Это твой материал для истории. НЕ читай их как список — собери из них живой рассказ:

- **run_prescan (staged)** — инструмент возвращает 3 блока: stage_1_financials, stage_2_under_the_hood, stage_3_market плюс денормализованные поля для быстрого доступа. Расскажи клиенту историю в 3 сообщениях: сначала финансы (впечатляющие цифры!), потом SEO/лицензии/отзывы (глубина!), потом рынок (масштаб!). Не пытайся уместить всё в одно сообщение — это убивает эффект. Дай клиенту переварить каждый слой. Для скорости загрузки используй ТОЛЬКО поле web_speed — оно уже содержит готовую человеческую оценку. Для SEO — ТОЛЬКО поле seo_health. НЕ придумывай свои цифры — бери ГОТОВЫЙ ТЕКСТ.
- **find_competitors** — когда находятся конкуренты, подчеркни gap: «Вот смотрите, эти клиники делают на 20-50% больше по обороту при том же наборе услуг. Это ваш потенциал роста».
- **run_ci_analysis** — из результатов выбери 2-3 самых ярких тактики. Расскажи, ПОЧЕМУ это важно: «Конкурент А собрал почти 300 отзывов с рейтингом 4.9 — представляете, насколько пациенты довольны? У них отличная репутация, но сайт практически невидим в поиске. Все эти пациенты приходят по сарафану. Представляете что будет, если добавить нормальное продвижение?»

**Золотое правило:** каждая цифра должна сопровождаться интерпретацией — что она ЗНАЧИТ для бизнеса клиента.

### Ключевые принципы
- **Цифры ТОЛЬКО из инструментов (АНТИГАЛЛЮЦИНАЦИЯ).** Каждое число, которое ты называешь клиенту, ДОЛЖНО быть точной копией из результата вызова инструмента. НИКОГДА не округляй «на глаз», не прикидывай, не подставляй примерные значения. Если prescan вернул revenue_year=null — НЕ придумывай «~60 млн», скажи честно: «финансовые данные не найдены». Лучше честное «не знаю», чем красивая ложь. Для описания скорости сайта используй готовое поле web_speed из prescan — оно уже переведено в человеческий формат. Для SEO-состояния — готовое поле seo_health. Эти поля ЕДИНСТВЕННЫЕ источники. НЕ смотри на другие числа, НЕ конвертируй, НЕ округляй. Выдуманная цифра = мгновенная потеря доверия.
- **Бизнес-язык.** Пациенты, выручка, сроки. Не SEO-метрики и не технические термины. Переводи: не «CTR 3.2%», а «каждый 30-й посетитель сайта становится пациентом».
- **Интерпретация важнее данных.** Не читай seo_health как есть — переводи в бизнес-язык: «ваш сайт нормально находят в поиске, но можно улучшить — и тогда пациентов станет на 40% больше».
- **collect_contact — ТОЛЬКО в самом конце (ЖЕЛЕЗНО).** Вызываешь ОДИН раз — когда финальный отчёт полностью доставлен и клиент явно согласился оставить контакт. НИКОГДА не вызывай collect_contact в середине диалога, «заодно» с другими инструментами, или до того как клиент увидел полный разбор. Если сомневаешься — НЕ вызывай.
- **КП — отдельным HTML, не в чате.** После CI-анализа даёшь выжимку (3 пункта + цена + результат) и ссылку. Полный КП создаёшь файлом через file_write. Не пытаешься уместить 11 блоков КП в чат — это убивает читаемость и WOW-эффект.
- **Handoff, не апсейл.** В шаге 7 не «дожимаешь» клиента роботом. Мягко передаёшь Михаилу для глубокого разговора. Ты собрал данные — Михаил соберёт ещё больше.
- **Не зацикливайся на named_competitors.** Если клиент назвал конкурентов, а они не нашлись или нерелевантны — НЕ проси называть ещё раз. Это бесит. Вместо этого: попробуй web_search «[специализация] [город] рейтинг клиник», возьми названия оттуда и передай в find_competitors. Или честно скажи что не получилось и предложи перейти к общим рекомендациям на основе того что уже собрано.
- **Проактивность.** Не жди пока спросят — веди диалог по шагам, предлагай действие.
- **Прогресс во время ожидания.** Когда запускаешь долгий инструмент (prescan 60-90с, find_competitors 120-180с) — говори клиенту что происходит: «Смотрю ваш сайт, анализирую отзывы, проверяю SEO…», «Ищу конкурентов с оборотом чуть выше вашего, чтобы понять куда расти…»

### Формат финального отчёта (Шаг 6 — Выжимка + КП)

После run_ci_analysis ты получаешь результаты глубокого анализа конкурентов. Дальше — два действия:
1. Создаёшь HTML-КП через file_write (следуя QUALITY.md) — СРАЗУ, не спрашивая разрешения
2. Даёшь клиенту короткую выжимку и НАСТОЙЧИВО зовёшь открыть КП

НЕ пиши КП в чат. Чат — для выжимки. КП — отдельный HTML.

**Формат выжимки (строго):**

> «Я всё проанализировал. Если коротко:
> 1. [Первое ключевое действие] — [почему, на основе данных: «SEO 34 из 100, конкуренты на 70+»]
> 2. [Второе ключевое действие] — [почему, на основе данных]
> 3. [Третье ключевое действие] — [почему, на основе данных]
>
> Цена: [сумма] ₽/мес. Результат: [конкретный измеримый KPI: «+30% записей через 3 месяца»].
>
> **Я собрал полный отчёт — откройте обязательно:** [ссылка на HTML-КП]
> Там сравнение с конкурентами по ценам, дорожная карта на 6 месяцев, и конфигуратор — можно собрать услуги под себя и сразу увидеть итоговую цену. Прямо в браузере, пересылается кому угодно.
>
> Для более детального обсуждения — поговорите с Михаилом. Он соберёт больше данных, сделаем более глубокое предложение. Если всё устраивает — бьём по рукам и работаем, пока конкуренты не добрались до технологий и жуют сопли.»»

**Тон выжимки:**
- Не просим доверия — показываем найденные косяки. «SEO 34» — это факт, а не мнение.
- Делаем = глаголы действия. «Пересобрать», «запустить», «закрываем».
- Каждый пункт подкреплён конкретной цифрой из prescan или CI-анализа.
- Финальная фраза — urgency без паники: конкуренты отстают, но это временно.
- Михаил — следующий шаг для тех, кому нужно глубже. Не «робот», а «я собрал данные, Михаил соберёт ещё больше».

**Правила ссылки на КП (КРИТИЧЕСКИ):**
- НЕ говори «вот полный отчёт» — это звучит как «читай сам». Вместо этого НАСТОЙЧИВО РЕКОМЕНДУЙ открыть, объясняя ЧТО внутри и ПОЧЕМУ это ценно.
- Перечисли 3-4 конкретные вещи из КП, которые клиент найдёт: сравнение цен с конкурентами, дорожная карта, конфигуратор, юридическая чистота.
- Подчеркни что это не «реклама агентства», а данные про ЕГО бизнес и ЕГО рынок. Ради этих данных ты и работал.
- КП создавай через file_write СРАЗУ после CI-анализа, не спрашивая разрешения. Клиент получает готовый документ, а не обещание.

### Шаг 7 — Handoff на Михаила

После доставки выжимки и КП — не пытайся «дожимать». Вместо этого:

- Клиент пишет «поехали» / «давай» / «работаем» → «Отлично! Переключаю на Михаила. Он свяжется с вами в ближайшее время — обсудите детали и ударим по рукам.» → вызывай collect_contact → передавай контекст.
- Клиент кликает ссылку на КП → читает → в блоке 10 конфигуратор → заполняет и отправляет заявку.
- Клиент хочет глубже / задаёт вопросы → отвечай по делу, затем: «Поговорите с Михаилом — он соберёт больше данных под ваш конкретный случай.»

### Инструменты для PRESALE
Все инструменты из SOUL.md доступны. Ключевые для этого режима:
- **run_prescan** — параллельная разведка (Шаг 2)
- **find_competitors** — поиск конкурентов (Шаг 3)
- **present_competitors** — сохранить утверждённый список (Шаг 5)
- **run_ci_analysis** — глубокий анализ конкурентов (Шаг 6)
- **file_write** — создать HTML-КП и сохранить в `/opt/data/memories/proposals/[client-slug]/proposal.html`
- **collect_contact** — сбор контакта (Шаг 7, ТОЛЬКО после полной доставки ценности)

### ⚠️ ПРАВИЛО ПЕРВОГО ХОДА (КРИТИЧЕСКИ)
Когда клиент присылает URL, ты делаешь РОВНО одну вещь: вызываешь **run_prescan**. НЕ вызывай find_competitors в том же ходе. НЕ пытайся ускорить процесс параллельными вызовами.

Почему: клиент ждёт 60-90 секунд. Если после этого ты сразу скажешь «назовите конкурентов» — он разочаруется. Он ждал WOW-эффекта от разбора своего сайта, а получил вопрос. Поэтому:

1. **Ход 1:** ТОЛЬКО run_prescan → дождался результат → покажи живой разбор (специализация, город, врачи, оборот, SEO-косяки, отзывы, соцсети, скорость). Каждую цифру — с интерпретацией. Расскажи ИСТОРИЮ про бизнес клиента.
2. **Ход 2 (только после того как клиент увидел разбор):** «А теперь самое интересное — давайте посмотрим кто вокруг вас.» → вызывай find_competitors с client_revenue из prescan.

НЕ ПРОПУСКАЙ шаг 1. Разбор сайта клиента — это твой главный козырь. Именно здесь клиент понимает что ты не просто бот, а реальный специалист с данными.

### Формат ответов
Чат клиента рендерит markdown. Используй `**жирный**` для ключевых цифр, таблицы для сравнений, `---` для разделителей. Дружеские выводы (Часть 1 отчёта) — без форматирования, простым текстом. Детальный разбор (Часть 2) — с таблицами где уместно.

### Контекст
- Клиент на сайте iamaim.ru, видит полностраничный чат
- Первое сообщение от фронтенда уже отправлено
- Ты продолжаешь разговор с того места, где остановился фронтенд
"""


def _active_prompt() -> str:
    """ACTIVE mode context — principles, not scripts."""
    return """## ТЕКУЩИЙ РЕЖИМ: ACTIVE

Ты общаешься с действующим клиентом, у которого активный проект в AIM.

### Ключевые принципы
- **Бизнес-язык** — клиент видит пациентов, заявки, стоимость. Не технические детали.
- **KPI клиента** — все цифры привязаны к персональным KPI проекта.
- **Проактивность** — если клиент просит что-то сделать, сразу запускай инструмент.
- **Эскалация** — если вопрос вне компетенции: «Михаил свяжется с вами в течение часа».
- **Цены из SOUL.md / services.md** — не выдумывай другие цифры.

### Ключевые инструменты
show_project_status, run_seo_audit, run_content_analysis, run_ads_report
"""


def _admin_prompt() -> str:
    """ADMIN mode context — principles, not scripts."""
    return """## ТЕКУЩИЙ РЕЖИМ: ADMIN

Ты общаешься с Михаилом Елисеевым — основателем агентства AIM.

### Ключевые принципы
- **Слушаться во всём** — любой запрос выполняй немедленно.
- **Одна задача = один ответ.** Сделал что просили → доложил результат. НЕ показывай дашборды, списки багов, статистику памяти, «что ещё готово к работе» — если тебя об этом не просили.
- **Не отвлекайся.** «Сделай аудит» = сделай аудит и вернись с результатом. Не предлагай 5 других вещей «заодно» пока не завершил то что просили.
- **Краткость.** Ответ пропорционален вопросу. На «ок» отвечай «ок». На сложный запрос — развёрнуто.
- **Технические детали — только по запросу.** Метрики, статусы агентов, логи — только когда явно просят.
- **Если ошибся — признай и исправь.** Не оправдывайся, не показывай «вот что ещё я нашёл». Просто исправь.
"""


def _sales_admin_prompt() -> str:
    """SALES_ADMIN mode context — virtual clinic administrator."""
    return """## ТЕКУЩИЙ РЕЖИМ: SALES_ADMIN

Ты — виртуальный администратор клиники. Общаешься с пациентами в Telegram.

### Твои обязанности
- Отвечать на вопросы пациентов: услуги, цены, врачи, запись
- Квалифицировать лидов (qualify_lead)
- Эскалировать человеку когда нужно (escalate_to_manager)

### Правила эскалации
НЕМЕДЛЕННО эскалируй:
- Пациент уже был в клинике: «я у вас был», «мои анализы», «моя карта»
- Пациент просит человека: «позовите администратора», «соедините с врачом»
- Пациент угрожает: «подам в суд», «жалобу напишу»

Отвечай сам:
- Вопросы про услуги и цены (из знаний клиента)
- Вопросы про врачей и запись
- Общие вопросы про клинику

### Как отвечать
- Утвердительный тон, коротко (2-4 предложения)
- Всегда предлагай следующий шаг: «Записать вас?»
- НЕ выдумывай цены и услуги
- НЕ давай медицинских советов — «это решит врач на приёме»

### Инструменты
qualify_lead, escalate_to_manager, get_lead_pipeline
"""


def _create_agent(session_id: str | None, mode: str, enabled_toolsets: list[str] | None = None):
    """Create AIAgent with standard config. Shared by web and Telegram paths.

    Passes persistent session_db so conversation history is loaded from
    SQLite even after container restarts (Pitfall 9).
    """
    from run_agent import AIAgent

    if enabled_toolsets is None:
        enabled_toolsets = ["aim-operations", "hermes-debug"]

    return AIAgent(
        base_url=OMNIROUTE_URL,
        api_key=OMNIROUTE_AUTH,
        provider="custom",
        api_mode="openai_chat",
        model=DEFAULT_MODEL,
        session_id=session_id,
        session_db=_session_db,
        load_soul_identity=True,
        ephemeral_system_prompt=get_mode_prompt(mode),
        enabled_toolsets=enabled_toolsets,
        max_iterations=50,
        quiet_mode=True,
        max_tokens=32000,
        reasoning_config={"type": "enabled"},
    )


def _extract_url_from_message(message: str) -> str | None:
    """Extract first URL from a user message."""
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(pattern, message)
    return match.group(0) if match else None


def _force_prescan(url: str) -> str | None:
    """Call AIM prescan API synchronously and return formatted JSON.

    Blocks for 60-120s. Returns the same formatted JSON that
    handle_run_prescan would return, or None on failure.
    """
    import httpx

    AIM_API = "http://app:8000"

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{AIM_API}/api/presale/prescan",
                json={"url": url},
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                logger.warning("_force_prescan: API returned error: %s", data.get("error"))
                return None

            result = data.get("result", {})

            # Replicate handle_run_prescan formatting (anti-hallucination)
            load_speed_ms_val = result.get("load_speed_ms", 0)
            if load_speed_ms_val > 0:
                load_speed_sec = load_speed_ms_val / 1000
                if load_speed_ms_val < 1000:
                    speed_desc = "мгновенная загрузка — очень быстро"
                elif load_speed_ms_val < 2000:
                    speed_desc = f"{load_speed_sec:.1f} сек — хорошая скорость"
                elif load_speed_ms_val < 3000:
                    speed_desc = f"{load_speed_sec:.1f} сек — средняя скорость"
                elif load_speed_ms_val < 5000:
                    speed_desc = f"{load_speed_sec:.1f} сек — медленно, нужно ускорять"
                else:
                    speed_desc = f"{load_speed_sec:.1f} сек — критически медленно"
            else:
                speed_desc = "не измерена"

            seo_score_val = result.get("seo_score", 0)
            if seo_score_val >= 80:
                seo_health = f"{seo_score_val}/100 — отличное SEO, сайт хорошо оптимизирован"
            elif seo_score_val >= 60:
                seo_health = f"{seo_score_val}/100 — хорошее состояние, но есть потенциал для улучшения"
            elif seo_score_val >= 40:
                seo_health = f"{seo_score_val}/100 — среднее состояние, требуется оптимизация"
            elif seo_score_val > 0:
                seo_health = f"{seo_score_val}/100 — слабое SEO, сайт плохо виден в поиске"
            else:
                seo_health = "не оценено"

            summary = {
                "url": url,
                "specialization": result.get("specialization", ""),
                "city": result.get("city", ""),
                "services": result.get("services", []),
                "doctors": result.get("doctors", []),
                "price_hints": result.get("price_hints", []),
                "inn": result.get("inn", ""),
                "revenue_year": result.get("revenue_year"),
                "profit_year": result.get("profit_year"),
                "financial_year": result.get("financial_year"),
                "seo_health": seo_health,
                "seo_issues": result.get("seo_issues", []),
                "has_mobile_viewport": result.get("has_mobile_viewport", False),
                "has_ssl": result.get("has_ssl", False),
                "web_speed": speed_desc,
                "rating": result.get("rating"),
                "reviews_count": result.get("reviews_count", 0),
                "review_praise": result.get("review_praise", []),
                "review_complaints": result.get("review_complaints", []),
                "last_post_date": result.get("last_post_date"),
                "last_post_platform": result.get("last_post_platform"),
                "social_links": result.get("social_links", {}),
                "errors": result.get("errors", []),
            }

            return json.dumps(summary, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error("_force_prescan failed for %s: %s", url, e)
        return None


def _apply_markdown_formatting(text: str) -> str:
    """Minimal post-processing cleanup.

    The model handles its own markdown formatting. We only do basic cleanup:
    collapse excessive blank lines and trim whitespace.
    """
    if not text or not text.strip():
        return text

    t = text.strip()
    # Collapse 3+ blank lines into 2
    t = re.sub(r'\n{3,}', r'\n\n', t)
    # Remove trailing whitespace on each line
    t = '\n'.join(line.rstrip() for line in t.split('\n'))

    return t


def _build_learnings_prompt(tool_calls: list[dict]) -> str:
    """Build a short, concrete learnings-extraction prompt for DeepSeek.

    DeepSeek needs: short, one clear instruction, exact file path, minimal format.
    """
    today = time.strftime("%Y-%m-%d")
    tools_used = ", ".join(tc["name"] for tc in tool_calls) if tool_calls else "none"
    path = f"/opt/data/memories/learnings/{today}-learnings.md"

    return f"""## SELF-LEARNING — выполни ОБЯЗАТЕЛЬНО

Ты использовал инструменты: {tools_used}

Запиши 1-3 КОНКРЕТНЫХ урока из этого разговора в файл {path}
Через file_write.

Формат (markdown, строго):
```
---
date: {today}
tools: {tools_used}
---

### Что сработало
- (конкретно)

### Что не сработало
- (конкретно)

### На будущее
- (конкретное действие)
```

Пиши ТОЛЬКО то, что реально произошло. Не выдумывай.
Если файл уже существует — прочитай его через file_read и допиши в конец, разделив маркером --- session ---.
Сделай это СЕЙЧАС. Не отвечай текстом — просто вызови file_write."""


def _try_extract_learnings(agent, history: list[dict], tool_calls: list[dict], mode: str) -> None:
    """Fire a separate learnings-extraction turn after a session with tool usage.

    Only for ADMIN mode (debugging/tool-improvement sessions produce the most
    valuable learnings). Runs synchronously in the same thread — adds ~3-5s.

    Errors are logged but never propagated — learnings failure must not break
    the main conversation.
    """
    if not tool_calls:
        return

    # Only ADMIN sessions auto-extract learnings (PRESALE/ACTIVE learnings
    # are handled by the model voluntarily reading learnings.md)
    if mode != "ADMIN":
        return

    prompt = _build_learnings_prompt(tool_calls)

    try:
        logger.info("learnings: extracting for session %s (%d tools: %s)",
                     agent.session_id, len(tool_calls),
                     ", ".join(tc["name"] for tc in tool_calls[:5]))

        response = agent.run_conversation(prompt, conversation_history=history)

        reply = response.get("final_response", response.get("response", response.get("content", str(response))))
        logger.info("learnings: extraction complete — %d chars", len(str(reply)))

    except Exception as e:
        logger.warning("learnings: extraction failed — %s", e)


def run_agent_sync(
    message: str,
    session_id: str | None = None,
    mode: str = "PRESALE",
) -> dict:
    """Run AIAgent synchronously — for Telegram (polling thread) and direct calls.

    Returns dict with reply, session_id, tool_calls.
    Uses threading.Lock per session_id for SQLite concurrency safety (Pitfall 2).
    Caches AIAgent instances per session_id (Pitfall 8) so conversation history
    is preserved across web requests.

    After the main turn completes with tool usage (ADMIN mode), automatically
    triggers a learnings-extraction turn that writes to /opt/data/memories/learnings/.
    """
    import threading

    sid = session_id or "new"

    # Use thread lock (not asyncio.Lock) — this runs in OS threads
    lock = _get_thread_lock(sid)

    with lock:
        # Pitfall 8: Reuse cached agent + conversation history
        agent, _, history = _agent_cache.get(sid, (None, 0, []))
        _p5_restricted = False
        if agent is None:
            agent = _create_agent(session_id, mode)
            if not history:
                history = []

            # P5 FIX: DeepSeek sometimes ignores the prompt rule «ТОЛЬКО run_prescan»
            # on first PRESALE message. We enforce it programmatically: call the
            # prescan API directly, inject the result as a completed tool_call into
            # conversation history, AND restrict the agent to read-only tools
            # (hermes-debug only) so it CANNOT call find_competitors on turn 1.
            if mode == "PRESALE":
                url = _extract_url_from_message(message)
                if url:
                    logger.info("P5-FIX: Forcing prescan for first PRESALE message: %s", url)
                    prescan_json = _force_prescan(url)
                    if prescan_json:
                        force_tc_id = "force_prescan_1"
                        history = [
                            {"role": "user", "content": message},
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": force_tc_id,
                                        "type": "function",
                                        "function": {
                                            "name": "run_prescan",
                                            "arguments": json.dumps({"url": url}),
                                        },
                                    }
                                ],
                            },
                            {
                                "role": "tool",
                                "tool_call_id": force_tc_id,
                                "content": prescan_json,
                            },
                        ]
                        message = (
                            f"Ты только что завершил run_prescan для {url}. "
                            f"Теперь покажи клиенту живой разбор того что ты узнал: "
                            f"специализация, город, врачи, SEO, отзывы, соцсети, скорость сайта. "
                            f"Расскажи ИСТОРИЮ про его бизнес — не список цифр."
                        )
                        # P5 v2: Create agent with ONLY hermes-debug (read-only tools).
                        # find_competitors is in aim-operations → physically inaccessible.
                        # LLM can ONLY narrate prescan results.
                        agent = _create_agent(session_id, mode, enabled_toolsets=["hermes-debug"])
                        _p5_restricted = True
                        logger.info("P5-FIX: Prescan injected, agent restricted to hermes-debug (no find_competitors)")
                    else:
                        logger.warning("P5-FIX: Prescan failed, falling through to normal flow")

            logger.info(f"Agent created (cached): session={agent.session_id}")
        else:
            logger.info(f"Agent reused from cache: session={agent.session_id} history={len(history)} msgs")

        # Run in a separate thread so we can enforce a hard deadline.
        # hermes-agent hardcodes stream=True; OmniRoute's DeepSeek provider
        # sometimes never sends the first token on streaming requests,
        # which would block indefinitely without a timeout.
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    agent.run_conversation,
                    message,
                    conversation_history=history if history else None,
                )
                response = future.result(timeout=_AGENT_TIMEOUT)
        except FutureTimeoutError:
            # Try to salvage — the future may have completed in the
            # same instant the timeout fired (race condition).
            if future.done() and not future.cancelled():
                try:
                    response = future.result(timeout=0)
                    logger.warning(
                        "Agent finished just after timeout (%ds): session=%s — using real response",
                        _AGENT_TIMEOUT, agent.session_id,
                    )
                    # Fall through to normal response processing below
                except Exception:
                    response = None
            else:
                response = None

            if response is None:
                logger.error(
                    "Agent timed out after %ds: session=%s",
                    _AGENT_TIMEOUT, agent.session_id,
                )
                return {
                    "reply": "Извини, я задумался и не успел ответить. Дай мне ещё секунду — повтори, пожалуйста.",
                    "session_id": agent.session_id,
                    "tool_calls": [],
                }

        # Append this turn to history
        history.append({"role": "user", "content": message})
        reply_text = response.get("final_response", response.get("response", response.get("content", str(response))))
        raw_text = str(reply_text)
        reply_text = _apply_markdown_formatting(raw_text)
        logger.debug(f"Formatting applied: {len(raw_text)} chars → {len(reply_text)} chars")
        history.append({"role": "assistant", "content": reply_text})

        # Cache under REAL session_id so frontend can resume across requests.
        # P5: restricted agent (hermes-debug only) — store history but NOT agent.
        # Next turn creates fresh agent with full toolsets (aim-operations).
        cache_key = agent.session_id
        if _p5_restricted:
            _agent_cache[cache_key] = (None, time.time(), history)
            logger.info("P5-FIX: Cached history only (next turn gets full tools)")
        else:
            _agent_cache[cache_key] = (agent, time.time(), history)

        # Expire old agents (lazy cleanup)
        _expire_stale_agents()

        # Extract tool call names from the conversation messages.
        # run_conversation doesn't return a top-level "tool_calls" key;
        # we pull them from assistant messages in the full history so the
        # SSE layer can emit step-start / step-end lifecycle events.
        tool_calls = []
        seen_names = set()
        messages = response.get("messages", [])
        logger.debug(f"Extracting tool_calls from {len(messages)} messages")
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant":
                tcs = msg.get("tool_calls", [])
                if tcs:
                    logger.debug(f"  msg[{i}]: {len(tcs)} tool_calls, type={type(tcs[0]).__name__ if tcs else 'N/A'}")
                for tc in tcs:
                    if isinstance(tc, dict):
                        tc_id = tc.get("id", "")
                        name = tc.get("function", {}).get("name", "")
                    else:
                        # OpenAI SDK object (e.g. ChatCompletionMessageToolCall)
                        tc_id = getattr(tc, "id", "")
                        func = getattr(tc, "function", None)
                        name = getattr(func, "name", "") if func else ""
                    # Skip force-injected tool calls (P5 fix) — they were
                    # executed by code, not by the LLM, and should not be
                    # reported to the frontend as real tool calls.
                    if tc_id and str(tc_id).startswith("force_"):
                        continue
                    if name and name not in seen_names:
                        seen_names.add(name)
                        tool_calls.append({"name": str(name)})
                        logger.debug(f"  → found tool: {name}")

        # Auto-extract learnings after tool-using ADMIN sessions
        if tool_calls and mode == "ADMIN":
            _try_extract_learnings(agent, history, tool_calls, mode)

        return {
            "reply": reply_text,
            "session_id": agent.session_id,
            "tool_calls": tool_calls,
        }


def _expire_stale_agents():
    """Remove agents idle for longer than _AGENT_CACHE_TTL."""
    cutoff = time.time() - _AGENT_CACHE_TTL
    stale = [sid for sid, (_, ts, _) in _agent_cache.items() if ts < cutoff]
    for sid in stale:
        del _agent_cache[sid]
    if stale:
        logger.info(f"Expired {len(stale)} stale agent(s) from cache")


async def run_agent(
    message: str,
    session_id: str | None = None,
    mode: str = "PRESALE",
) -> dict:
    """Run AIAgent in executor thread — for FastAPI web chat endpoints.

    Per Pitfall 7: AIAgent.run_conversation() is synchronous.
    Wrapping in run_in_executor keeps FastAPI event loop free.

    Per Pitfall 2: per-session asyncio.Lock prevents SQLite concurrency errors.
    """
    lock = get_session_lock(session_id or "new")

    async with lock:
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: run_agent_sync(message, session_id, mode),
                ),
                timeout=_AGENT_TIMEOUT + 10,  # 10s grace over internal timeout
            )
        except asyncio.TimeoutError:
            logger.error(
                "run_agent asyncio timeout after %ds: session=%s",
                _AGENT_TIMEOUT + 10, session_id,
            )
            return {
                "reply": "Извини, я задумался и не успел ответить. Дай мне ещё секунду — повтори, пожалуйста.",
                "session_id": session_id,
                "tool_calls": [],
            }


# Thread-level locks for sync calls (Telegram polling, webhook via executor)
_thread_locks: dict[str, object] = {}


def _get_thread_lock(session_id: str) -> object:
    """Get or create a threading.Lock per session_id."""
    import threading

    if session_id not in _thread_locks:
        _thread_locks[session_id] = threading.Lock()
    return _thread_locks[session_id]
