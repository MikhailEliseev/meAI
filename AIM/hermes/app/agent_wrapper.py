"""AIAgent wrapper — session management + sync-to-async adapter.

Per Pitfall 2: SQLite session DB needs per-session serialization to avoid
"database is locked" errors. asyncio.Lock per session_id.

Per Pitfall 7: AIAgent.run_conversation() is SYNCHRONOUS (returns Dict[str, Any]).
Must wrap in loop.run_in_executor() for FastAPI async endpoints.

Per Pitfall 8: Session persistence requires SessionDB. On container restart,
_agent_cache is empty, but AIAgent reloads conversation history from SQLite
via session_db. The cache is an optimisation, not the source of truth.

Hermes v7: ONBOARDING mode routes to PipelineEngine (Python state machine).
ADMIN/ACTIVE/SALES_ADMIN — unchanged (LLM-first).
"""

import asyncio
import json
import logging
import os
import re
import secrets
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
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
_AGENT_CACHE_TTL = 3600  # 24 hours — cache is an optimisation, DB is source of truth
_AGENT_TIMEOUT = 900  # 15 minutes — overall agent run deadline
_LEARNINGS_TIMEOUT = 60  # 1 minute — learnings extraction deadline

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", ""))
DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# SOUL.md cache — loaded once, reused across requests
_soul_md_cache: Optional[str] = None

# 3PHASE_PIPELINE.md cache — loaded once, reused across requests
_pipeline_md_cache: Optional[str] = None


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


def load_pipeline_md() -> str:
    """Load 3PHASE_PIPELINE.md from $HERMES_HOME/3PHASE_PIPELINE.md (cached).

    copy_soul.sh copies this file from skills/aim/ to $HERMES_HOME at startup.
    Contains the detailed 3-phase presale flow that Hermes must follow.
    """
    global _pipeline_md_cache
    if _pipeline_md_cache is not None:
        return _pipeline_md_cache

    hermes_home = os.getenv("HERMES_HOME", "/opt/data")
    pipeline_path = Path(hermes_home) / "3PHASE_PIPELINE.md"

    if pipeline_path.exists():
        _pipeline_md_cache = pipeline_path.read_text()
        logger.info(f"3PHASE_PIPELINE.md loaded: {len(_pipeline_md_cache)} chars from {pipeline_path}")
    else:
        logger.warning(f"3PHASE_PIPELINE.md not found at {pipeline_path} — Hermes won't know the full pipeline!")
        _pipeline_md_cache = ""

    return _pipeline_md_cache


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
    3PHASE_PIPELINE.md provides the detailed 3-phase presale flow.
    Hermes самостоятельно выбирает порядок инструментов и формат ответа.
    """
    pipeline = load_pipeline_md()
    pipeline_section = ""
    if pipeline:
        pipeline_section = (
            "\n\n---\n\n"
            "## 🛑 ПАЙПЛАЙН ПРЕСЕЙЛА (ОБЯЗАТЕЛЕН К ИСПОЛНЕНИЮ)\n\n"
            + pipeline +
            "\n\n---\n\n"
        )

    return pipeline_section + """## ТЕКУЩИЙ РЕЖИМ: PRESALE

Ты общаешься с новым потенциальным клиентом на сайте iamaim.ru.

### Твоя задача
Показать ценность агентства через реальные цифры. Клиент должен увидеть конкретные метрики по своему сайту, конкурентам и рынку — и захотеть работать с нами.

### 🛑 ПРИВЕТСТВИЕ (КОГДА КЛИЕНТ НЕ ДАЛ URL)
Если клиент написал «здравствуйте», «привет», «test», «hello» или любое другое сообщение БЕЗ URL — представься коротко и по делу. Не «я AI-операционный директор», а «у меня под капотом тулзы».

**Формат (строго — 3 предложения):**
1. «Здравствуйте!» (или «Добрый день!»)
2. Кто ты и твой арсенал — одно короткое предложение
3. Просьба скинуть URL (+ упомяни конкурентов если есть)

**Пример (можно адаптировать):**
«Здравствуйте! Я Hermes, разведчик агентства AIM — под капотом анализ сайта, финансов, SEO, отзывов, поиск конкурентов. Скидывайте ссылку на ваш сайт и сайты конкурентов если есть — посмотрим что у вас и как.»

**Вариации арсенала (выбери 3-4 пункта из списка, не все сразу):**
- анализ сайта (SEO, скорость, структура)
- финансы компании (оборот, прибыль, учредители)
- медицинские лицензии
- отзывы (Яндекс.Карты, 2ГИС, ПроДокторов)
- поиск и анализ конкурентов
- реклама конкурентов (Яндекс.Директ, VK)
- соцсети (VK, Telegram)

**ЗАПРЕЩЕНО в приветствии:**
- ❌ «Я Operator» или «AI-операционный директор»
- ❌ «специализируемся на медицинских клиниках: стоматологии, косметологии...»
- ❌ Длинные自我介绍 на абзац — ты не на собеседовании
- ❌ Безличное «Скиньте ссылку» без приветствия

**Длина:** 3 предложения. Не 2. Не 5. ТРИ.

### 🛑 ПРАВИЛО ПЕРВОГО ИНСТРУМЕНТА (НЕРУШИМО)
Когда клиент присылает URL — ты вызываешь **ТОЛЬКО run_full_scout**. ОДИН инструмент. Больше НИЧЕГО.

НЕ вызывай find_competitors. НЕ вызывай web_search. НЕ вызывай run_prescan. НЕ пытайся ускорить диалог. run_full_scout запускает 16-фазный пайплайн, который соберёт ВСЕ данные: рынок, Instagram, реклама, тех.аудит, SEO, соцсети, Telegram, врачи, СМИ, конкуренты, отзывы, финансы, контент-анализ. Это займёт несколько минут — клиент получит ПОЛНУЮ картину.

### 🎭 16-ФАЗНАЯ РАЗВЕДКА (run_full_scout)

Когда ты вызываешь run_full_scout — запускается 16-фазный пайплайн под управлением Python-стейт-машины (PipelineEngine). Все 16 фаз выполняются строго последовательно, LLM интерпретирует данные каждой фазы.

**Пока пайплайн работает — сообщи клиенту что происходит:**
«Запускаю полную разведку: 16 фаз анализа. Смотрю рынок, соцсети, рекламу, тех.аудит, SEO, конкурентов, отзывы, финансы — всё что есть про ваш бизнес. Это займёт несколько минут, результат будет полным.»

**Когда run_full_scout вернёт результат — ты получишь:**
- status: "completed" или "partial"
- phases_completed / phases_failed: сколько фаз выполнено
- phase_results: список всех 16 фаз со статусами
- key_findings: ключевые находки (5 пунктов)
- report_url: ссылка на HTML-отчёт

**Твоя задача после получения результата:**
1. Расскажи клиенту САМОЕ ВАЖНОЕ из key_findings — живым языком
2. Дай ссылку на HTML-отчёт: «Я собрал полный отчёт — откройте обязательно: [report_url]»
3. Предложи обсудить детали с Михаилом

### Как ты ведёшь диалог
Ты ведёшь ЖИВОЙ пошаговый диалог с клиентом. Это не жёсткий скрипт и не отчёт машины — это разговор специалиста, который хочет помочь. SOUL.md описывает 7 шагов диалога. Следуй этим шагам, но адаптируй под конкретного клиента. Не перескакивай через шаги.

### Тон общения
Разговорный, как будто компетентный друг рассказывает. Используй фразы вроде «смотрите», «ага, у вас», «вот это интересно», «знаете что я заметил». Не говори как робот — говори как специалист с арсеналом разведки, который разобрался в теме и теперь делится важным.

### Как рассказывать данные (КРИТИЧЕСКИ)
Ты получаешь от инструментов реальные данные. Это твой материал для истории. НЕ читай их как список — собери из них живой рассказ:

- **run_full_scout** — возвращает результат ВСЕХ 16 фаз. Сфокусируйся на key_findings (5 ключевых находок). Расскажи их живым языком, с интерпретацией. Дай ссылку на HTML-отчёт. Не пытайся пересказать ВСЕ 16 фаз — только самое важное.
- **run_prescan** (deprecated, fallback) — если run_full_scout недоступен, fallback на быстрый прескан.
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
- **run_full_scout** — полный 16-фазный скаутинг (ОСНОВНОЙ инструмент при URL)
- **run_prescan** — быстрый прескан (fallback)
- **collect_contact** — сбор контакта (Шаг 7, ТОЛЬКО после полной доставки ценности)

### ⚠️ ПРАВИЛО ПЕРВОГО ХОДА (КРИТИЧЕСКИ)
Когда клиент присылает URL, ты делаешь РОВНО одну вещь: вызываешь **run_full_scout**. НЕ вызывай run_prescan, find_competitors или другие инструменты в том же ходе.

run_full_scout выполнит все 16 фаз автоматически — Python-стейт-машина гарантирует последовательность. Ты получишь готовый результат со всеми данными.

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

    Hermes v7: uses get_toolsets_for_mode(mode) instead of hardcoded toolset list.
    ONBOARDING → ["aim-operations"], ADMIN → ["aim-operations", "hermes-debug"].
    """
    from run_agent import AIAgent
    from app.pipeline.mode_gate import get_toolsets_for_mode
    from app.pipeline.file_guard import set_current_mode

    if enabled_toolsets is None:
        enabled_toolsets = get_toolsets_for_mode(mode)

    # Hermes v7: сообщаем file_guard текущий режим для проверок file_write
    set_current_mode(mode)

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
        max_iterations=25,
        quiet_mode=True,
        max_tokens=16000,
    )


def _extract_url_from_message(message: str) -> str | None:
    """Extract first URL from a user message.

    Handles both full URLs (https://example.ru) and bare domains (example.ru).
    """
    # Try full URL first: https://example.ru/page
    full_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(full_pattern, message)
    if match:
        return match.group(0)

    # Try bare domain: example.ru, clinic-name.com, site.рф
    bare_pattern = (
        r'(?:^|\s)([a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.'
        r'(?:ru|com|net|org|рф|su|io|pro|dev|digital|agency|'
        r'club|online|site|tech|med|health|clinic|center|care|'
        r'msk|spb|rf|info|biz))(?:\s|$|[,.!?;:")]|$)'
    )
    match = re.search(bare_pattern, message)
    if match:
        return match.group(1)
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


def _run_onboarding_pipeline(
    message: str,
    session_id: str,
    client_url: str,
    mode: str = "ONBOARDING",
) -> dict:
    """Run Hermes v7 PipelineEngine for ONBOARDING mode with URL.

    Python-стейт-машина: выполняет фазы последовательно, LLM — только интерпретатор.

    Args:
        message: Исходное сообщение пользователя (с URL).
        session_id: ID сессии.
        client_url: Извлечённый URL сайта клиента.
        mode: Режим работы.

    Returns:
        dict с reply, session_id, tool_calls.
    """
    from app.pipeline.engine import PipelineEngine
    from app.tools.session_archive import save_tool_output, upsert_metadata

    logger.info(
        "PipelineEngine: starting onboarding for %s (session=%s)",
        client_url, session_id,
    )

    engine = PipelineEngine()

    try:
        # Запускаем пайплайн синхронно (asyncio.run в отдельном потоке)
        import asyncio as _asyncio

        state = _asyncio.run(engine.execute(
            session_id=session_id,
            client_url=client_url,
            mode=mode,
        ))

        # ── Сохраняем metadata (данные уже сохранены engine.py при HTML BUILD) ─
        completed = sum(
            1 for r in state.phases.values()
            if r.status.value in ("completed", "no_data")
        )
        failed = sum(
            1 for r in state.phases.values()
            if r.status.value in ("permanent_failure", "tool_failed", "timed_out")
        )

        upsert_metadata(
            session_id,
            url=client_url,
            completed_phases=completed,
            failed_phases=failed,
            total_phases=len(state.phases),
            started_at=state.started_at,
        )
        logger.info(
            "PipelineEngine: metadata saved for %s (%d/%d phases completed)",
            session_id, completed, len(state.phases),
        )

        # ── Формируем ответ со ВСЕМИ фазами ────────────────────────
        reply_parts = [
            f"Разведка завершена: {completed}/{len(state.phases)} фаз собраны.",
        ]

        # Все фазы в порядке выполнения (из PHASES)
        from app.pipeline.phases import PHASES as _PHASES
        for phase in _PHASES:
            interp_key = f"{phase.name}_interpretation"
            if interp_key in state.accumulated_data:
                interp = str(state.accumulated_data[interp_key])
                if interp and len(interp) > 20:
                    # Обрезаем длинные интерпретации (чат не резиновый)
                    if len(interp) > 600:
                        interp = interp[:600] + "..."
                    reply_parts.append(f"\n### {phase.name}\n{interp}")

        if failed > 0:
            reply_parts.append(f"\n⚠️ {failed} фаз не удалось выполнить.")

        # ── Пробуем сгенерировать HTML-отчёт ──────────────────────
        try:
            from app.tools.generate_html_report import handle_generate_html_report
            report_result = _asyncio.run(handle_generate_html_report(
                session_hash=session_id,
                client_url=client_url,
            ))
            if isinstance(report_result, str):
                report_result = json.loads(report_result)
            if report_result.get("url"):
                reply_parts.insert(
                    1,
                    f"\n📊 [Открыть полный отчёт]({report_result['url']})",
                )
        except Exception as _report_err:
            logger.warning("HTML report generation skipped: %s", _report_err)

        reply = "\n".join(reply_parts)

        tool_calls = []
        for pr in state.phases.values():
            for tc in pr.tool_calls_made:
                if tc not in [t["name"] for t in tool_calls]:
                    tool_calls.append({"name": tc})

        return {
            "reply": reply,
            "session_id": session_id,
            "tool_calls": tool_calls,
        }

    except Exception as e:
        logger.exception("PipelineEngine: onboarding failed for %s", client_url)
        return {
            "reply": (
                f"Я запустил разведку вашего сайта, но произошла ошибка: {e}.\n"
                "Дайте мне минуту и попробуйте ещё раз."
            ),
            "session_id": session_id,
            "tool_calls": [],
        }
    finally:
        # Очищаем in-memory state после завершения пайплайна
        try:
            from app.pipeline.engine import cleanup_pipeline_state
            cleanup_pipeline_state(session_id)
        except Exception:
            pass


def run_agent_sync(
    message: str,
    session_id: str | None = None,
    mode: str = "PRESALE",
) -> dict:
    """Run AIAgent synchronously — for Telegram (polling thread) and direct calls.

    Hermes v7 routing:
    - ONBOARDING mode + URL → PipelineEngine (Python state machine)
    - ONBOARDING mode без URL → обычный AIAgent (приветствие)
    - ADMIN/ACTIVE/SALES_ADMIN → без изменений (LLM-first)

    Returns dict with reply, session_id, tool_calls.
    Uses threading.Lock per session_id for SQLite concurrency safety (Pitfall 2).
    Caches AIAgent instances per session_id (Pitfall 8) so conversation history
    is preserved across web requests.

    After the main turn completes with tool usage (ADMIN mode), automatically
    triggers a learnings-extraction turn that writes to /opt/data/memories/learnings/.
    """
    import threading

    sid = session_id or "new"

    # ── Hermes v7: ONBOARDING routing ─────────────────────────────
    mode_upper = mode.upper()
    if mode_upper in ("ONBOARDING", "PRESALE"):
        client_url = _extract_url_from_message(message)
        if client_url:
            # Tool-based подход: вместо прямого вызова PipelineEngine,
            # инструктируем LLM вызвать run_full_scout.
            # Python-стейт-машина запускается внутри tool handler'а.
            logger.info(
                "v7 routing: ONBOARDING + URL → tool-based run_full_scout (%s)",
                client_url,
            )
            # Инжектируем инструкцию в сообщение для LLM
            message = (
                f"Пользователь дал ссылку: {client_url}\n\n"
                f"Исходное сообщение: {message}\n\n"
                f"Вызови инструмент run_full_scout с параметрами url=\"{client_url}\", client_name=\"\". "
                f"НЕ вызывай run_prescan — используй ТОЛЬКО run_full_scout."
            )
            # Fallback: _run_onboarding_pipeline остаётся доступным
            # для прямого вызова из других мест (например, Telegram webhook)
        else:
            logger.info("v7 routing: ONBOARDING без URL → AIAgent (приветствие)")
    # ───────────────────────────────────────────────────────────────

    # Use thread lock (not asyncio.Lock) — this runs in OS threads
    lock = _get_thread_lock(sid)

    with lock:
        # Pitfall 8: Reuse cached agent + conversation history
        agent, _, history = _agent_cache.get(sid, (None, 0, []))
        if agent is None:
            agent = _create_agent(session_id, mode)
            if not history:
                history = []

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
        cache_key = agent.session_id
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
