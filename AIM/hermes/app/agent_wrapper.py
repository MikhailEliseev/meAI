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
import secrets
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MAX_SESSION_MESSAGES = 100  # auto-purge sessions exceeding this

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
    # Purge bloated sessions on startup to prevent token waste
    try:
        import sqlite3
        conn = sqlite3.connect(str(_DB_PATH))
        cur = conn.execute("SELECT session_id, COUNT(*) as cnt FROM messages GROUP BY session_id HAVING cnt > ?", (MAX_SESSION_MESSAGES,))
        bloated = cur.fetchall()
        for sid, cnt in bloated:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
            logger.warning("Purged bloated session %s (%d messages)", sid, cnt)
        conn.commit()
        conn.close()
        if bloated:
            logger.info("Session cleanup: purged %d bloated sessions", len(bloated))
    except Exception as e:
        logger.warning("Session cleanup failed: %s", e)
except Exception as e:
    logger.warning("Session DB unavailable — sessions will NOT survive restarts: %s", e)

# Per-session locks to serialize concurrent requests (Pitfall 2)
_session_locks: dict[str, asyncio.Lock] = {}

# Agent cache (Pitfall 8) — preserves agent instances across requests.
# Cache is an optimisation; SessionDB is the source of truth.
# Each entry: (agent_instance, last_used_ts, conversation_history)
_agent_cache: dict[str, tuple[object, float, list[dict]]] = {}
_AGENT_CACHE_TTL = 86400  # 24 hours — cache is an optimisation, DB is source of truth
_AGENT_TIMEOUT = 900  # 15 minutes — overall agent run deadline (ACTIVE/ADMIN)
_PRESALE_AGENT_TIMEOUT = 250  # 4 minutes — prescan takes up to 245s, +5s margin for model thinking
_LEARNINGS_TIMEOUT = 60  # 1 minute — learnings extraction deadline

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "https://api.deepseek.com")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "sk-placeholder")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

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

    DESIGNED FOR: DeepSeek V4 Pro (works on Claude too).
    Архитектура: последовательные раунды (не параллельные — DeepSeek не поддерживает).
    """
    return """## ТЕКУЩИЙ РЕЖИМ: PRESALE

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

### 🎯 3-ФАЗНЫЙ ПРЕСЕЙЛ (УНИВЕРСАЛЬНАЯ АРХИТЕКТУРА)

Пресеил разделён на три фазы. Ты управляешь Фазой 1 (интерактивная), затем запускаешь Фазу 2 (фоновая), и система сама доставляет Фазу 3 клиенту.

### ⚡ ФАЗА 1 — Хук и WOW-эффект (ДВА ПОСЛЕДОВАТЕЛЬНЫХ РАУНДА)

Когда клиент присылает URL — ты работаешь в ДВА РАУНДА:

**РАУНД 1 — quick_overview (Perplexity, ~5-10 секунд):**
1. Вызови `quick_overview` с URL клиники
2. Дождись результата
3. СРАЗУ напиши клиенту 1 сообщение с WOW-эффектом на основе `overview_text`

**Как рассказать quick_overview (1 сообщение):**
Расскажи СВОИМИ словами — не копируй JSON как есть, а нарративи. Используй формат:
«Нашёл. Клиника "[название]" в [город], [специализация]. [1-2 факта о бизнесе — выручка, врачи]. И знаете что интересно? [ЗАЦЕПКА — удивительный факт]. Сейчас копаю глубже — финансы, лицензии, SEO…»

Это создаёт WOW-эффект: «ого, откуда он всё это знает за 5 секунд?!»

**РАУНД 2 — run_prescan (~60-90 секунд):**
1. Вызови `run_prescan` с URL клиники
2. Дождись результата (он вернёт все 3 стадии в одном ответе)
3. Напиши клиенту 2-3 сообщения: сначала финансы, потом SEO/лицензии/отзывы, потом рынок

**Как рассказывать prescan (2-3 сообщения):**
После получения результата:
- Сообщение 1: «Смотрю глубже. Финансы: [stage_1_financials — выручка, прибыль, юрлицо, город, специализация].»
- Сообщение 2: «Под капотом: [stage_2_under_the_hood — лицензии, SEO, отзывы, скорость сайта, соцсети]. Для скорости — [web_speed]. SEO — [seo_health].»
- Сообщение 3: «Рынок: [stage_3_market — Яндекс.Карты, конкуренты рядом, контент-аудит].»

**ВАЖНО:** Если run_prescan вернул `cached: true` — данные уже есть, сразу рассказывай.

### 🛑 ПРАВИЛО: НЕ ПОВТОРЯЙ УПАВШИЕ ИНСТРУМЕНТЫ

Если `quick_overview` упал с ошибкой (например, таймаут Perplexity) — НЕ вызывай его снова. Просто переходи к Раунду 2 (run_prescan) и скажи: «Perplexity-разведка временно недоступна, но я уже запускаю глубокий анализ сайта.»

Если `run_prescan` упал с ошибкой — НЕ вызывай его снова. Скажи клиенту: «Система глубокого анализа временно перегружена. Давайте я посмотрю что уже собрал Perplexity.» И покажи только данные quick_overview.

**Никогда не вызывай один и тот же инструмент больше 1 раза.** Упал = идём дальше.

### Как ты ведёшь диалог
Ты ведёшь ЖИВОЙ пошаговый диалог с клиентом. Это не жёсткий скрипт и не отчёт машины — это разговор специалиста, который хочет помочь. SOUL.md описывает 7 шагов диалога. Следуй этим шагам, но адаптируй под конкретного клиента. Не перескакивай через шаги.

### Тон общения
Разговорный, как будто компетентный друг рассказывает. Используй фразы вроде «смотрите», «ага, у вас», «вот это интересно», «знаете что я заметил». Не говори как робот — говори как специалист с арсеналом разведки, который разобрался в теме и теперь делится важным.

### Как рассказывать данные (КРИТИЧЕСКИ)
Ты получаешь от инструментов реальные данные. Это твой материал для истории. НЕ читай их как список — собери из них живой рассказ:

- **quick_overview (Perplexity)** — возвращает `overview_text`: 2-3 абзаца живого текста с 6 секциями (БИЗНЕС, ВРАЧИ, КОНКУРЕНТЫ, СОЦСЕТИ, САЙТ, ЗАЦЕПКА). Это ПЕРВОЕ что ты показываешь клиенту. Расскажи СВОИМИ словами.
- **run_prescan (staged)** — возвращает 3 блока: stage_1_financials, stage_2_under_the_hood, stage_3_market. Расскажи клиенту в 2-3 сообщениях ПОСЛЕ quick_overview. Для скорости сайта используй ТОЛЬКО поле web_speed. Для SEO — ТОЛЬКО поле seo_health.
- **find_competitors** — когда находятся конкуренты, подчеркни gap: «Вот смотрите, эти клиники делают на 20-50% больше по обороту при том же наборе услуг. Это ваш потенциал роста».
- **run_ci_analysis** — из результатов выбери 2-3 самых ярких тактики. Расскажи, ПОЧЕМУ это важно.

**Золотое правило:** каждая цифра должна сопровождаться интерпретацией — что она ЗНАЧИТ для бизнеса клиента.

### Ключевые принципы
- **Цифры ТОЛЬКО из инструментов (АНТИГАЛЛЮЦИНАЦИЯ).** Каждое число, которое ты называешь клиенту, ДОЛЖНО быть точной копией из результата вызова инструмента. НИКОГДА не округляй «на глаз», не прикидывай, не подставляй примерные значения. Если prescan вернул revenue_year=null — НЕ придумывай «~60 млн», скажи честно: «финансовые данные не найдены». Лучше честное «не знаю», чем красивая ложь. Для описания скорости сайта используй готовое поле web_speed из prescan — оно уже переведено в человеческий формат. Для SEO-состояния — готовое поле seo_health. Эти поля ЕДИНСТВЕННЫЕ источники. НЕ смотри на другие числа, НЕ конвертируй, НЕ округляй. Выдуманная цифра = мгновенная потеря доверия.
- **Бизнес-язык.** Пациенты, выручка, сроки. Не SEO-метрики и не технические термины. Переводи: не «CTR 3.2%», а «каждый 30-й посетитель сайта становится пациентом».
- **Интерпретация важнее данных.** Не читай seo_health как есть — переводи в бизнес-язык: «ваш сайт нормально находят в поиске, но можно улучшить — и тогда пациентов станет на 40% больше».
- **collect_contact — после WOW-эффекта, перед background_pipeline.** Вызываешь ОДИН раз — когда клиент увидел и quick_overview, и prescan, и хочет глубокий анализ. Скажи: «Хотите полный анализ? Оставьте контакт — пришлю готовую презентацию.» Вызвал collect_contact → СРАЗУ вызывай run_background_pipeline. НИКОГДА не вызывай collect_contact до того как клиент увидел WOW-разбор.
- **КП — отдельным HTML, не в чате.** После CI-анализа даёшь выжимку (3 пункта + цена + результат) и ссылку. Полный КП создаёшь файлом через file_write. Не пытаешься уместить 11 блоков КП в чат — это убивает читаемость и WOW-эффект.
- **Handoff, не апсейл.** В шаге 7 не «дожимаешь» клиента роботом. Мягко передаёшь Михаилу для глубокого разговора. Ты собрал данные — Михаил соберёт ещё больше.
- **Не зацикливайся на named_competitors.** Если клиент назвал конкурентов, а они не нашлись или нерелевантны — НЕ проси называть ещё раз. Это бесит. Вместо этого: попробуй web_search «[специализация] [город] рейтинг клиник», возьми названия оттуда и передай в find_competitors. Или честно скажи что не получилось и предложи перейти к общим рекомендациям на основе того что уже собрано.
- **Проактивность.** Не жди пока спросят — веди диалог по шагам, предлагай действие.

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
- **quick_overview** — Perplexity-разведка (~5-10 сек): 6 секций, wow-эффект. Вызывай ПЕРВЫМ в Раунде 1
- **run_prescan** — 3-стадийная разведка (~60-90 сек): финансы → лицензии/SEO → рынок. Вызывай ВТОРЫМ в Раунде 2
- **run_background_pipeline** — Фаза 2+3: все 12+ scout-инструментов + продающая презентация. Fire-and-forget после collect_contact
- **find_competitors** — поиск конкурентов (если клиент хочет глубже в диалоге)
- **run_ci_analysis** — глубокий анализ конкурентов (если клиент хочет интерактивный разбор)
- **file_write** — создать HTML-КП
- **collect_contact** — сбор контакта (после вау-эффекта, перед background_pipeline)

### 🚫 ЗАПРЕЩЕНЫ в PRESALE:
- **api_debug** — НЕ ИСПОЛЬЗУЙ. Этот инструмент для отладки, не для клиентского диалога. Если prescan упал — не «чини» его через api_debug, просто скажи клиенту что данные собираются.
- **orchestrate** — НЕ ИСПОЛЬЗУЙ. Вызывай инструменты напрямую (quick_overview, run_prescan), а не через оркестратор.

### 📡 ФАЗА 2+3 — Переход в фон (ПОСЛЕ вау-эффекта)

Когда Фаза 1 завершена (клиент увидел и quick_overview, и prescan):
1. Скажи: «Хотите полный анализ конкурентов, SEO и рынка? Это займёт час-полтора — я соберу ВСЕ данные и пришлю готовую презентацию. Оставьте Telegram или почту — и я вернусь с полным отчётом.»
2. Вызови `collect_contact` — получи имя и контакт клиента
3. После того как `collect_contact` вернул результат — СРАЗУ вызывай `run_background_pipeline` с session_hash из сессии, url и company_name. Этот инструмент работает в фоне 1-2 часа и НЕ требует ответа клиенту.

**ВАЖНО:** run_background_pipeline — fire-and-forget после collect_contact. Ты вызываешь его и говоришь клиенту: «Запустил глубокий анализ. Как будет готов — пришлю результат. Обычно это занимает час-полтора.» НЕ жди завершения пайплайна — клиент уже ушёл.

### Формат ответов
Чат клиента рендерит markdown. Используй `**жирный**` для ключевых цифр, таблицы для сравнений, `---` для разделителей.

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
        # NOTE: hermes-debug is REQUIRED even for PRESALE.
        # Without it, the model stops passing parameters to ALL tools (hermes-agent bug).
        enabled_toolsets = ["aim-operations", "hermes-debug"]

    # Cost control: limit iterations and output tokens by mode
    _mode_limits = {
        "ADMIN":       (12, 12000),
        "ACTIVE":      (6,  6000),
        "PRESALE":     (5,  6000),
        "SALES_ADMIN": (4,  4000),
    }
    iters, out_tokens = _mode_limits.get(mode, (5, 6000))

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
        max_iterations=iters,
        quiet_mode=True,
        max_tokens=out_tokens,
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
                timeout = _PRESALE_AGENT_TIMEOUT if mode == "PRESALE" else _AGENT_TIMEOUT
                response = future.result(timeout=timeout)
        except FutureTimeoutError:
            # Try to salvage — the future may have completed in the
            # same instant the timeout fired (race condition).
            if future.done() and not future.cancelled():
                try:
                    response = future.result(timeout=0)
                    logger.warning(
                        "Agent finished just after timeout (%ds): session=%s — using real response",
                        timeout, agent.session_id,
                    )
                    # Fall through to normal response processing below
                except Exception:
                    response = None
            else:
                response = None

            if response is None:
                logger.error(
                    "Agent timed out after %ds: session=%s",
                    timeout, agent.session_id,
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
        salvage = {"response": None}
        asyncio_timeout = (_PRESALE_AGENT_TIMEOUT if mode == "PRESALE" else _AGENT_TIMEOUT) + 10

        def _run_and_salvage():
            result = run_agent_sync(message, session_id, mode)
            salvage["response"] = result
            return result

        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _run_and_salvage),
                timeout=asyncio_timeout,
            )
        except asyncio.TimeoutError:
            if salvage["response"] is not None:
                logger.warning(
                    "run_agent: salvaged real response after asyncio timeout (%ds): session=%s",
                    asyncio_timeout, session_id,
                )
                return salvage["response"]
            logger.error(
                "run_agent asyncio timeout after %ds (no response salvaged): session=%s",
                asyncio_timeout, session_id,
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
