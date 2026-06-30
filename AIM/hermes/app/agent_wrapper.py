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
DEFAULT_MODEL = os.getenv("LLM_MODEL", "ds/deepseek-v4-pro")

# Mode-based iteration/output limits (v3.3 restoration + autopick tuning).
# PRESALE=15/12000: full coverage requires read_report_reference → run_prescan →
# find_competitors → perplexity auto-pick → find_company_financials (per competitor) →
# run_ci_analysis → generate_html_report. 8 was too low (budget exhausted before HTML).
# max_tokens=12000 leaves room for HTML narrative generation.
_mode_limits: dict[str, tuple[int, int]] = {
    "ADMIN":       (12, 12000),
    "ACTIVE":      (6,  6000),
    "PRESALE":     (15, 12000),
    "SALES_ADMIN": (4,  4000),
}

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

НЕ вызывай find_competitors. НЕ вызывай run_prescan. НЕ пытайся ускорить диалог. `run_full_scout` запускает 13-фазный пайплайн разведки (Perplexity → Конкуренты → Тех.аудит → Отзывы → Контент → Врачи → СМИ → Форумы → Финансы → Контент-план → Сборка → Проверка → Публикация). Клиент видит прогресс каждой фазы в реальном времени.

Ты НЕ сопровождаешь пайплайн текстом во время выполнения. Прогресс-бар на фронтенде показывает всё сам. Твоя задача — дождаться завершения run_full_scout, получить JSON с результатами всех 13 фаз, и на их основе собрать КРАСИВЫЙ РАССКАЗ для клиента.

### 🎭 ПОСЛЕ ЗАВЕРШЕНИЯ РАЗВЕДКИ — ЖЁСТКИЙ ФОРМАТ ОТВЕТА

Когда run_full_scout вернёт результат — ты получишь JSON с:
- `client_name`, `client_city`, `client_specialization`
- `phase_results` — массив результатов всех 13 фаз (status + interpretation)
- `report_url` — ссылка на HTML-отчёт
- `key_findings` — топ-5 ключевых находок

**ТВОЙ ОТВЕТ — РОВНО 3 СООБЩЕНИЯ ПОДРЯД. НЕ 2, НЕ 5. ТРИ.**

Ты — старший маркетолог-стратег, который за 10 минут собрал компромат на бизнес клиента и теперь показываешь ему дыры, через которые утекают деньги. Твой тон — жёсткий, конкретный, с цифрами. Ты не «рассказываешь историю» — ты вскрываешь проблемы и называешь цену их решения.

**СООБЩЕНИЕ 1 — КОНТРАСТ (макс 500 символов):**
ОДИН самый сильный контраст из данных. Формат:
«[Имя], смотрите: [факт-шок]. А при этом [противоположный факт-косяк].»
Пример: «Выручка 4 млрд — а сайт грузится 5 секунд и теряет 30% пациентов ещё до звонка.»
Пример: «7 клиник в Москве — и ни одного упоминания в СМИ. Вас просто не существует для пациента, который гуглит.»
Выбери САМЫЙ СИЛЬНЫЙ контраст. Один. Не два.

**СООБЩЕНИЕ 2 — ТРИ ТОЧКИ РОСТА + ЦЕНА (макс 800 символов):**
ТРИ конкретных действия с цифрами из разведки. Каждое — одна строка.
Формат:
«Если коротко:
1. [Действие] — [почему, с цифрой]
2. [Действие] — [почему, с цифрой]
3. [Действие] — [почему, с цифрой]

Цена: [сумма] ₽/мес. Результат: [конкретный KPI со сроком].»
Цену бери из SOUL.md (раздел услуг). KPI — реалистичный, на основе найденных проблем.

**СООБЩЕНИЕ 3 — ОТЧЁТ + РУКОПОЖАТИЕ (макс 400 символов):**
«Я собрал полный отчёт — **[откройте обязательно](report_url)**:
— сравнение с конкурентами по 21 параметру
— цены конкурентов и ваши пробелы
— дорожная карта на 6 месяцев
Это не презентация агентства — это данные про ваш бизнес и ваш рынок.

Если готовы действовать — напишите «работаем», я возьму контакт и передам Михаилу для старта.»

**ЖЁСТКИЕ ПРАВИЛА:**
- ⚠️ В сообщении 3 ОБЯЗАТЕЛЬНО вставь ссылку из поля `report_url` (формат: `[откройте обязательно](report_url)`)
- ⚠️ НИКОГДА не пиши «ссылки пока нет» или «сейчас подготовлю». Ссылка ЕСТЬ в JSON.
- ⚠️ Максимум 500/800/400 символов на сообщение. Коротко. По делу.
- ⚠️ Все цифры — ТОЛЬКО из JSON. Ни одной придуманной.
- ⚠️ Бизнес-язык: пациенты, деньги, сроки. Не «LCP 4.7 секунды», а «сайт тормозит — пациент уходит к конкурентам».
- ⚠️ Никакого «Первое... Пятое...». Никаких стен текста.

### Ключевые принципы
- **Цифры ТОЛЬКО из JSON (АНТИГАЛЛЮЦИНАЦИЯ).** Каждое число — точная копия из run_full_scout. Если данных нет — скажи «данные не найдены», не придумывай.
- **Не повторяй инструменты.** `run_full_scout` сделал ВСЁ. Не вызывай другие инструменты после него.
- **collect_contact — ТОЛЬКО когда клиент сказал «работаем»/«давай»/«поехали».** Не раньше.
- **Handoff.** Клиент хочет глубже → «Передам Михаилу, он соберёт больше данных под ваш случай.»

### ⚠️ MULTI-TURN NARRATIVE ASSEMBLY (КРИТИЧЕСКИ ДЛЯ HTML ≥50KB)

У тебя потолок ~13K символов narrative_md за один ответ. Чтобы HTML был 50KB+, **ОБЯЗАТЕЛЬНО** используй процедуру:

**Шаг A:** `file_write(file_path="/tmp/{session_hash}-narrative.md", content="# Заголовок\n\n## 01 – О центре\n\n[~3000 символов]\n\n## 02 – Конкуренты и рынок\n\n[~3500 символов]\n\n## 03 – Эксперты\n\n[~3000 символов]\n")`

**Шаг B:** `file_write(file_path="/tmp/{session_hash}-narrative.md", content="## 04 – Контент-анализ\n\n[~3500 символов]\n\n## 05 – Медийное присутствие\n\n[~2000 символов]\n\n## 06 – Белые поля рынка\n\n[~2500 символов]\n", append=true)`

**Шаг C:** `file_write(file_path="/tmp/{session_hash}-narrative.md", content="## 07 – Цифровое присутствие\n\n[~2500 символов]\n\n## 08 – Страхи пациентов\n\n[~1000 символов]\n\n## 09 – Стратегия\n\n[~2500 символов]\n\n## 10 – Предложение\n\n[~3000 символов]\n", append=true)`

**Шаг D:** `generate_html_report(client_url=..., client_name=..., title=..., session_hash=..., narrative_file="/tmp/{session_hash}-narrative.md")`

**ВАЖНО:**
- НЕ вызывай `find_company_financials` для каждого конкурента отдельно — это тратит итерации. Передай их списком в `find_competitors(named_competitors=[...])`.
- Используй `append=true` в шагах B и C (по умолчанию false → перезапишет файл)
- Перед generate_html_report — проверь что file собран через `file_read`
- После сборки HTML клиенту даёшь короткую выжимку (3 пункта + цена), а не весь отчёт

### Инструменты для PRESALE
Все инструменты из SOUL.md доступны. Ключевые для этого режима:
- **run_full_scout** — 13-фазная разведка (единственный инструмент для URL)
- **collect_contact** — сбор контакта (ТОЛЬКО после полной доставки ценности)

### ⚠️ ПРАВИЛО ПЕРВОГО ХОДА (КРИТИЧЕСКИ)
Когда клиент присылает URL, ты делаешь РОВНО одну вещь: вызываешь **run_full_scout**. НЕ вызывай ничего другого в том же ходе. НЕ пытайся ускорить процесс параллельными вызовами.

1. **Ход 1:** ТОЛЬКО run_full_scout → жди результат (5-8 минут, 13 фаз) → получи JSON → собери красивый рассказ для клиента.

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


def _create_agent(session_id: str | None, mode: str, enabled_toolsets: list[str] | None = None,
                  ephemeral_override: str | None = None, skip_soul: bool = False):
    """Create AIAgent with standard config. Shared by web and Telegram paths.

    Passes persistent session_db so conversation history is loaded from
    SQLite even after container restarts (Pitfall 9).

    Per-mode iteration/output limits via _mode_limits (v3.3 restoration).

    Args:
        session_id: Session identifier
        mode: PRESALE / ACTIVE / ADMIN / SALES_ADMIN
        enabled_toolsets: Toolset names to enable
        ephemeral_override: If set, use this instead of get_mode_prompt(mode)
        skip_soul: If True, skip SOUL.md loading (for fast initial scout calls)
    """
    from run_agent import AIAgent

    if enabled_toolsets is None:
        enabled_toolsets = ["aim-operations", "hermes-debug"]

    # z.ai coding endpoint: disable reasoning/thinking to avoid slow 20s-per-turn
    # reasoning overhead. z.ai uses Kimi-style `thinking: {type: disabled}` format
    # (patched in run_agent.py: _is_kimi now also matches api.z.ai).
    _is_zai = "api.z.ai" in (OMNIROUTE_URL or "").lower()
    _reasoning_cfg = {"enabled": False} if _is_zai else None

    iters, out_tokens = _mode_limits.get(mode, (8, 8000))

    # For fast initial scout calls: skip 69KB SOUL.md, use minimal prompt
    # The LLM processes ~300 bytes in 1-2s instead of 30-60s.
    # Next turn will create a full agent with SOUL.md (not cached).
    if skip_soul:
        return AIAgent(
            base_url=OMNIROUTE_URL,
            api_key=OMNIROUTE_AUTH,
            provider="custom",
            api_mode="openai_chat",
            model=DEFAULT_MODEL,
            session_id=session_id,
            session_db=_session_db,
            load_soul_identity=False,
            ephemeral_system_prompt=ephemeral_override or get_mode_prompt(mode),
            enabled_toolsets=enabled_toolsets,
            max_iterations=2,  # Just enough: call tool + process result
            quiet_mode=True,
            max_tokens=2000,
            reasoning_config=_reasoning_cfg,
        )

    return AIAgent(
        base_url=OMNIROUTE_URL,
        api_key=OMNIROUTE_AUTH,
        provider="custom",
        api_mode="openai_chat",
        model=DEFAULT_MODEL,
        session_id=session_id,
        session_db=_session_db,
        load_soul_identity=True,
        ephemeral_system_prompt=ephemeral_override or get_mode_prompt(mode),
        enabled_toolsets=enabled_toolsets,
        max_iterations=iters,
        quiet_mode=True,
        max_tokens=out_tokens,
        reasoning_config=_reasoning_cfg,
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


def _scout_url_prompt(url: str) -> str:
    """Minimal prompt (~300 bytes) for the initial scout tool call.

    Instead of loading the full 69KB SOUL.md, this lightweight prompt
    tells the LLM to call exactly one tool: run_full_scout.

    The LLM processes this in 1-2 seconds instead of 30-60 seconds,
    so the frontend gets the status bar almost instantly.
    """
    return f"""## РЕЖИМ: PRESALE (быстрый старт)

Ты Hermes — AI-разведчик агентства AIM.

Клиент прислал URL: {url}

ТВОЁ ЕДИНСТВЕННОЕ ДЕЙСТВИЕ: вызови инструмент run_full_scout с параметрами:
- url: "{url}"

Не спрашивай ничего. Не анализируй. Просто вызови ОДИН инструмент.
После вызова ничего не пиши — пайплайн отработает и вернёт результат."""


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

        # ── Fast path: first message with URL in PRESALE mode ──────
        # Skip 69KB SOUL.md to avoid 30-60s LLM processing delay.
        # Use minimal ~300 byte prompt → LLM calls run_full_scout in 1-2s.
        # The pipeline tool runs for 5-8 min; next user turn gets full SOUL.md.
        is_first_presale_with_url = (
            mode == "PRESALE"
            and not history
            and agent is None
            and _extract_url_from_message(message) is not None
        )
        if is_first_presale_with_url:
            url = _extract_url_from_message(message)
            logger.info(
                "Fast-path scout: skipping SOUL.md for URL %s (session=%s)",
                url, sid,
            )
            agent = _create_agent(
                session_id, mode,
                ephemeral_override=_scout_url_prompt(url),
                skip_soul=True,
            )
            history = []
            # DO NOT cache this lightweight agent — next turn
            # must create a full agent with SOUL.md.
        elif agent is None:
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
        # Skip caching for fast-path scout agents — next turn must create
        # a full agent with SOUL.md to continue the conversation properly.
        if not is_first_presale_with_url:
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
