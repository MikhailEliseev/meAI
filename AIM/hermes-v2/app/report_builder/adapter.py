"""Адаптер v2 collected_results → v1-shape data dict для build_report_html.

v2 pipeline хранит результаты тулов как ``collected_results: dict[str, str]`` где
значения — JSON-строки (или plain text для quick_overview). Этот модуль преобразует
их в структуру ``data``, которую ждёт ``build_report_html`` (перенесённая из v1).

Mapping (v2 tool → v1 phase_key → label)::

    extract_clinic_profile → PROFILE_interp      → "Профиль клиники"
    quick_overview         → OVERVIEW_interp     → "Обзор рынка"
    find_competitors       → COMPETITORS_interp  → "Конкуренты"
    run_review_platforms   → REVIEWS_interp      → "Отзывы пациентов"
"""

import json
import logging

logger = logging.getLogger(__name__)


# Mapping: v2 tool name → (v1 phase_key, label)
# phase_key используется как data[f"{phase_key}_interp"]["content"]
# COMPETITORS убран — таблица конкурентов рендерится только в revenue_block.
# Сырой JSON find_competitors всё равно передаётся в data["COMPETITORS"] (ниже)
# для revenue_block, но отдельная секция в теле отчёта не строится.
_TOOL_TO_SECTION = [
    ("extract_clinic_profile", "PROFILE",   "Профиль клиники"),
    ("quick_overview",         "OVERVIEW",  "Обзор рынка"),
    ("run_review_platforms",   "REVIEWS",   "Отзывы пациентов"),
]


def _safe_load_json(raw: str) -> dict | None:
    """Безопасно распарсить JSON-строку. Вернуть None если не JSON."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _looks_like_markdown_or_text(s: str) -> bool:
    """Эвристика: строка содержит осмысленный markdown/plain-text контент
    (а не чистый JSON-объект без форматирования)."""
    if not s or not s.strip():
        return False
    stripped = s.strip()
    # Чистый JSON-объект с одной строкой без переносов — не подходит как контент
    if stripped.startswith("{") and "\n" not in stripped:
        return False
    return True


def _merge_profile_with_scrape(profile_raw: str, scrape_raw: str) -> str:
    """Объединить профиль клиники с данными скрапера (Fix Баг 5).

    format_profile() умеет рендерить врачей и соцсети, но они лежат в
    collected_results["scrape_clinic_website"], а не в extract_clinic_profile.
    Эта функция мерджит scrape-данные (doctors, socials, services) в profile dict
    и возвращает обновлённый JSON для format_profile().

    Args:
        profile_raw: JSON от extract_clinic_profile.
        scrape_raw: JSON от scrape_clinic_website (или пустая строка).

    Returns:
        JSON-строка — profile с добавленными doctors/socials/services.
    """
    profile = _safe_load_json(profile_raw) or {}
    scrape = _safe_load_json(scrape_raw) or {}

    if not isinstance(profile, dict):
        return profile_raw or "{}"
    if not isinstance(scrape, dict):
        return json.dumps(profile, ensure_ascii=False)

    # Добавляем scrape-данные только если их ещё нет в профиле
    for key in ("doctors", "socials", "services"):
        if not profile.get(key) and scrape.get(key):
            profile[key] = scrape[key]

    # phone/website_platform — тоже из скрапа, если в профиле нет
    if not profile.get("phone") and scrape.get("phone"):
        profile["phone"] = scrape["phone"]
    if not profile.get("website_platform") and scrape.get("cms"):
        profile["website_platform"] = scrape["cms"]

    return json.dumps(profile, ensure_ascii=False)


def _format_tool_result_as_markdown(
    tool_name: str, raw: str, collected_results: dict | None = None,
) -> str:
    """Преобразовать сырой результат тула в Markdown-контент для интерпретации.

    Используем v2 formatters для каждого тула — они уже дают готовый Markdown.
    Если formatter недоступен или упал — fallback на сырой текст.

    Args:
        tool_name: имя тула (extract_clinic_profile, find_competitors, ...).
        raw: сырой результат тула (JSON-строка или plain text).
        collected_results: все результаты тулов (для мерджа profile+scrape).
    """
    if not raw or not raw.strip():
        return ""

    # Быстрая проверка: если это уже plain-text (quick_overview) — отдаём как есть
    if tool_name == "quick_overview":
        # quick_overview отдаёт свободный текст — используем напрямую
        return raw.strip()

    # Для остальных тулов используем v2 formatters
    try:
        if tool_name == "extract_clinic_profile":
            from app.formatters.profile import format_profile
            # Fix Баг 5: мерджим scrape-данные (врачи, соцсети, услуги) в профиль,
            # иначе они не попадают в отчёт — format_profile их не видит.
            scrape_raw = (collected_results or {}).get("scrape_clinic_website", "")
            if scrape_raw:
                raw = _merge_profile_with_scrape(raw, scrape_raw)
            md, _ = format_profile(raw)
            return md
        if tool_name == "find_competitors":
            from app.formatters.competitors import format_competitors
            md = format_competitors(raw)
            return md
        if tool_name == "run_review_platforms":
            return _format_reviews_markdown(raw)
        if tool_name == "scrape_clinic_website":
            return _format_scrape_markdown(raw)
    except Exception as e:  # pragma: no cover — defensive
        logger.warning("adapter: formatter for %s failed: %s", tool_name, e)

    # Fallback: если это валидный JSON — показываем ключевые поля,
    # иначе отдаём как есть (plain text).
    parsed = _safe_load_json(raw)
    if parsed and isinstance(parsed, dict):
        return _dump_dict_as_markdown(parsed)
    return raw.strip()



def _format_reviews_markdown(raw: str) -> str:
    """Форматировать отзывы из JSON в Markdown для отчёта."""
    data = _safe_load_json(raw)
    if not data or not isinstance(data, dict):
        return ""

    platforms = data.get("platforms", {})
    lines = []

    platform_labels = {
        "yandex": "Яндекс.Карты",
        "prodoctorov": "ПроДокторов",
        "twogis": "2ГИС",
    }

    for key, label in platform_labels.items():
        p = platforms.get(key, {})
        rating = p.get("rating")
        reviews = p.get("reviews")
        if rating and isinstance(rating, (int, float)):
            rating_clean = f"{rating:.1f}"
            rev_str = f" ({reviews})" if reviews else ""
            lines.append(f"- **{label}:** {rating_clean}★{rev_str}")

    if not lines:
        summary = data.get("reputation_summary", "")
        return summary if summary else "Отзывы не найдены на доступных площадках."

    praise = data.get("praise_summary", "")
    if praise:
        lines.append("")
        lines.append("**Что хвалят:**")
        for topic in praise.split("|")[:4]:
            topic = topic.strip()
            if topic:
                lines.append(f"- {topic[:120]}")

    criticism = data.get("criticism_summary", "")
    if criticism:
        lines.append("")
        lines.append("**Что критикуют:**")
        for topic in criticism.split("|")[:4]:
            topic = topic.strip()
            if topic:
                lines.append(f"- {topic[:120]}")

    # AI-резюме отзывов от Яндекса (neuro_summary) — Задача 4b
    neuro = data.get("neuro_summary", "")
    if neuro:
        lines.append("")
        lines.append(f"> 🤖 **AI-резюме отзывов (Яндекс):** {neuro[:400]}")

    # Цитаты пациентов — Задача 4b
    quotes = data.get("review_quotes", [])
    if quotes:
        lines.append("")
        lines.append("**Голоса пациентов:**")
        for q in quotes[:5]:
            if isinstance(q, dict):
                text = q.get("text", "")[:200]
                src = q.get("source", "")
                if text:
                    lines.append(f'> «{text}» — *{src}*')
            elif isinstance(q, str) and len(q) > 20:
                lines.append(f'> «{q[:200]}»')

    summary = data.get("reputation_summary", "")
    if summary:
        lines.append("")
        lines.append(f"> {summary[:300]}")

    return "\n".join(lines)


def _format_scrape_markdown(raw: str) -> str:
    """Форматировать данные скрапа сайта в Markdown."""
    data = _safe_load_json(raw)
    if not data or not isinstance(data, dict):
        return ""

    lines = []

    doctors = data.get("doctors", [])
    if doctors:
        lines.append("**Врачи на сайте:**")
        for doc in doctors[:8]:
            if isinstance(doc, dict):
                name = doc.get("name", "")
                spec = doc.get("specialization", "")
                if name:
                    lines.append(f"- {name}" + (f" — {spec[:60]}" if spec else ""))
        lines.append("")

    socials = data.get("socials", {})
    if socials:
        parts = []
        emoji_map = {"instagram": "📸", "vk": "🔵", "telegram": "✈️",
                     "youtube": "▶️", "rutube": "🎬", "dzen": "📰"}
        for platform, handle in socials.items():
            emoji = emoji_map.get(platform, "🔗")
            parts.append(f"{emoji} {platform}")
        if parts:
            lines.append("**Соцсети:** " + " · ".join(parts))
            lines.append("")

    services = data.get("services", [])
    if services:
        lines.append("**Услуги:** " + ", ".join(services[:8]))
        lines.append("")

    return "\n".join(lines)


def _format_scrape_supplement(collected_results: dict) -> str:
    """Дополнение PROFILE секции данными скрапера (Fix Баг 5).

    LLM-анализ профиля не содержит врачей и соцсетей (они из scrape_clinic_website).
    Эта функция формирует Markdown-блок с врачами и соцсетями, который добавляется
    к PROFILE interpretation, когда используется llm_section.

    Возвращает пустую строку если скрапер ничего не нашёл.
    """
    scrape_raw = (collected_results or {}).get("scrape_clinic_website", "")
    data = _safe_load_json(scrape_raw)
    if not data or not isinstance(data, dict):
        return ""

    lines: list[str] = []

    doctors = data.get("doctors", [])
    if doctors:
        lines.append("**Врачи на сайте:**")
        for doc in doctors[:8]:
            if isinstance(doc, dict):
                name = doc.get("name", "")
                spec = doc.get("specialization", "")
                if name:
                    lines.append(f"- {name}" + (f" — {spec[:60]}" if spec else ""))
            elif isinstance(doc, str) and len(doc) > 3:
                lines.append(f"- {doc}")
        lines.append("")

    socials = data.get("socials", {})
    if socials and isinstance(socials, dict):
        parts = []
        emoji_map = {"instagram": "📸", "vk": "🔵", "telegram": "✈️",
                     "youtube": "▶️", "rutube": "🎬", "dzen": "📰"}
        for platform in socials:
            emoji = emoji_map.get(platform, "🔗")
            parts.append(f"{emoji} {platform}")
        if parts:
            lines.append("**Соцсети:** " + " · ".join(parts))
            lines.append("")

    return "\n".join(lines) if lines else ""



def _dump_dict_as_markdown(d: dict, max_items: int = 12) -> str:
    """Превратить dict в простой Markdown-список (fallback).

    Глубина 1 уровень; вложенные dict/list — как JSON.
    """
    lines: list[str] = []
    for i, (k, v) in enumerate(d.items()):
        if i >= max_items:
            lines.append(f"- … (+{len(d) - max_items} ещё)")
            break
        if isinstance(v, (dict, list)):
            v_str = json.dumps(v, ensure_ascii=False)[:200]
            lines.append(f"- **{k}:** `{v_str}`")
        else:
            lines.append(f"- **{k}:** {v}")
    return "\n".join(lines)


def _extract_llm_section(llm_text: str, tool_name: str) -> str:
    """Попытаться извлечь из llm_text секцию, релевантную tool_name.

    llm_text — суммарный текст ответа LLM (может содержать анализ по нескольким
    фазам). Если в нём есть заголовок/маркер соответствующей секции — возвращаем
    кусок. Иначе возвращаем пустую строку (сигнал «используй formatted block»).

    Эвристика: ищем подстроки по label или имени тула.
    """
    if not llm_text or not llm_text.strip():
        return ""

    text = llm_text.strip()

    # Если llm_text короткий и без явной разбивки на секции — считаем его
    # общим анализом и используем целиком ТОЛЬКО для первой секции (PROFILE).
    # Для остальных — форматоры точнее.
    if tool_name != "extract_clinic_profile":
        return ""

    # Маркеры начала секции профиля
    markers = ["### Профиль", "## Профиль", "ПРОФИЛЬ КЛИНИКИ", "01 — О КЛИНИКЕ"]
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            return text[idx:]

    # Если маркеров нет, но текст осмысленный (не JSON) — отдаём целиком
    if _looks_like_markdown_or_text(text) and not text.strip().startswith("{"):
        return text
    return ""


def _build_hero_meta(
    profile_raw: str,
    finance_raw: str,
    reviews_raw: str,
    profile_cache: dict,
    company_name: str,
) -> dict:
    """Собрать метаданные для hero-секции отчёта.

    Источники (приоритет точных данных):
      1. profile_cache (из pipeline — содержит url, city, inn)
      2. extract_clinic_profile JSON (address, doctors_count, reg_date)
      3. company_financials JSON (revenue, profit)
      4. run_review_platforms JSON (rating, reviews count)

    Returns:
        dict с ключами: city, address, founded_year, doctors_count,
        rating, reviews_count, revenue_str, subtitle (готовый для hero),
        nav_sections (список ID→label для навигации).
    """
    meta = {
        "city": "", "address": "", "founded_year": "",
        "doctors_count": None, "rating": None, "reviews_count": None,
        "revenue_str": "", "subtitle": "", "nav_sections": [],
    }

    cache = profile_cache or {}

    # 1. city/address — приоритет profile_cache, fallback на extract_clinic_profile
    meta["city"] = cache.get("city", "") or ""
    meta["address"] = cache.get("address", "") or ""

    profile_obj = _safe_load_json(profile_raw)
    if profile_obj:
        if not meta["city"]:
            meta["city"] = profile_obj.get("city", "") or ""
        if not meta["address"]:
            meta["address"] = profile_obj.get("address", "") or ""
        if profile_obj.get("doctors_count"):
            try:
                meta["doctors_count"] = int(profile_obj["doctors_count"])
            except (ValueError, TypeError):
                pass
        reg_date = profile_obj.get("registration_date", "") or ""
        if reg_date and len(reg_date) >= 4:
            meta["founded_year"] = str(reg_date)[:4]

    # 2. revenue_str — из finance_raw
    fin_obj = _safe_load_json(finance_raw)
    if fin_obj:
        rev = fin_obj.get("revenue") or fin_obj.get("latest_revenue")
        if rev:
            try:
                rev_num = float(rev)
                if rev_num >= 1_000_000_000:
                    meta["revenue_str"] = f"{rev_num/1_000_000_000:.1f} млрд ₽ выручки"
                elif rev_num >= 1_000_000:
                    meta["revenue_str"] = f"{int(rev_num/1_000_000)} млн ₽ выручки"
            except (ValueError, TypeError):
                pass

    # 3. rating/reviews — из run_review_platforms
    rev_obj = _safe_load_json(reviews_raw)
    if rev_obj:
        platforms = rev_obj.get("platforms", {}) if isinstance(rev_obj, dict) else {}
        yandex = platforms.get("yandex", {}) if isinstance(platforms, dict) else {}
        if isinstance(yandex, dict):
            rating = yandex.get("rating")
            if rating and isinstance(rating, (int, float)):
                meta["rating"] = float(rating)
                reviews = yandex.get("reviews", 0)
                if reviews:
                    try:
                        meta["reviews_count"] = int(reviews)
                    except (ValueError, TypeError):
                        pass

    # 4. Subtitle для hero: короткое позиционирование
    parts = []
    if meta["city"]:
        parts.append(meta["city"])
    if meta["doctors_count"]:
        parts.append(f"{meta['doctors_count']} врачей")
    if meta["revenue_str"]:
        parts.append(meta["revenue_str"])
    if meta["rating"]:
        rating_str = f"{meta['rating']:.1f}★"
        if meta["reviews_count"]:
            rating_str += f" ({meta['reviews_count']} отзывов)"
        parts.append(rating_str)
    meta["subtitle"] = " · ".join(parts) if parts else "Маркетинговый аудит и точки роста"

    return meta


def build_data_dict(
    collected_results: dict[str, str],
    profile_cache: dict,
    llm_text: str = "",
    analysis_text: str = "",
) -> dict:
    """Преобразовать v2 collected_results в v1-shape data dict.

    Args:
        collected_results: dict tool_name → JSON-строка (или plain text).
        profile_cache: dict с метаданными клиента.
        llm_text: Краткий текст анализа из чата (опционально).
        analysis_text: Глубокий LLM-анализ для отчёта (опционально).
            Содержит маркеры === ПОЗИЦИЯ ===, === СИЛЬНЫЕ ===, === РОСТ ===,
            === РЕКОМЕНДАЦИИ ===. Распределяется по секциям отчёта.

    Returns:
        dict в формате, ожидаемом ``build_report_html``.
    """

    profile_cache = profile_cache or {}
    collected_results = collected_results or {}

    # ── Metadata ──────────────────────────────────────────────────────────────
    company_name = (
        profile_cache.get("company_name")
        or profile_cache.get("brand_name")
        or "Клиника"
    )
    url = profile_cache.get("url") or profile_cache.get("website") or ""

    data: dict = {
        "metadata": {
            "company_name": company_name,
            "url": url,
            "inn": profile_cache.get("inn", ""),
        },
    }

    # ── Парсинг глубокого LLM-анализа по секциям ─────────────────────────────
    # analysis_text содержит маркеры === ПОЗИЦИЯ ===, === СИЛЬНЫЕ === и т.д.
    # Распределяем: ПОЗИЦИЯ+СИЛЬНЫЕ → PROFILE, РОСТ+РЕКОМЕНДАЦИИ → OVERVIEW.
    analysis_sections: dict[str, str] = {}
    if analysis_text:
        from app.report_builder.analysis import split_analysis_by_section
        analysis_sections = split_analysis_by_section(analysis_text)

    # ── Секции (интерпретации) ────────────────────────────────────────────────
    for tool_name, phase_key, label in _TOOL_TO_SECTION:
        raw_result = collected_results.get(tool_name, "")

        # Приоритет 1: глубокий LLM-анализ для отчёта (analysis_text)
        analysis_content = ""
        if tool_name == "extract_clinic_profile" and analysis_sections.get("profile"):
            analysis_content = analysis_sections["profile"]
        elif tool_name == "quick_overview" and analysis_sections.get("reviews"):
            # OVERVIEW секция = точки роста + рекомендации (если нет quick_overview)
            analysis_content = analysis_sections["reviews"]

        if analysis_content and analysis_content.strip():
            content = analysis_content
            # Для PROFILE: добавляем врачей/соцсети/услуги из скрапера
            if tool_name == "extract_clinic_profile":
                supplement = _format_scrape_supplement(collected_results)
                if supplement:
                    content = content.rstrip() + "\n\n" + supplement
        # Приоритет 2: чат-анализ из llm_text
        elif _looks_like_markdown_or_text(_extract_llm_section(llm_text, tool_name)):
            llm_section = _extract_llm_section(llm_text, tool_name)
            content = llm_section
            if tool_name == "extract_clinic_profile":
                supplement = _format_scrape_supplement(collected_results)
                if supplement:
                    content = content.rstrip() + "\n\n" + supplement
        # Приоритет 3: formatted block из collected_results
        else:
            content = _format_tool_result_as_markdown(
                tool_name, raw_result, collected_results,
            )

        if content and content.strip():
            data[f"{phase_key}_interp"] = {
                "content": content,
                "label": label,
            }

    # ── Сырой JSON для revenue_block (читает эти ключи) ───────────────────────
    # v1: data["FINANCE"]["find_company_financials"] — вложенный JSON с
    # company.latest_revenue. В v2 company_financials уже плоский JSON
    # {"revenue": ..., "profit": ..., ...} — оборачиваем в {"company": ...}
    # для совместимости с v1 reader-логикой.
    fin_raw = collected_results.get("company_financials", "{}")
    fin_obj = _safe_load_json(fin_raw) if fin_raw else None
    if fin_obj:
        # company_financials в v2 плоский: revenue/profit/revenue_trend на верхнем
        # уровне. v1 reader искал fin.company.latest_revenue → нормализуем.
        normalized = {
            "company": {
                "latest_revenue": fin_obj.get("revenue") or fin_obj.get("latest_revenue"),
                "latest_profit": fin_obj.get("profit") or fin_obj.get("latest_profit"),
                "revenue_trend": fin_obj.get("revenue_trend", ""),
            }
        }
        data["FINANCE"] = {"find_company_financials": json.dumps(normalized, ensure_ascii=False)}
    else:
        data["FINANCE"] = {"find_company_financials": fin_raw or "{}"}

    # COMPETITORS — отдаём как есть, структура совпадает
    data["COMPETITORS"] = {
        "find_competitors": collected_results.get("find_competitors", "{}"),
    }

    # ── HERO metadata (для новой вёрстки hero-секции) ────────────────────────
    hero_meta = _build_hero_meta(
        profile_raw=collected_results.get("extract_clinic_profile", "{}"),
        finance_raw=collected_results.get("company_financials", "{}"),
        reviews_raw=collected_results.get("run_review_platforms", "{}"),
        profile_cache=profile_cache,
        company_name=company_name,
    )

    # nav_sections: только те секции, для которых есть контент
    # (slug, label) — slug это HTML-якорь (id секции)
    nav_labels = {
        "PROFILE": "О клинике",
        "OVERVIEW": "Обзор рынка",
        "REVIEWS": "Отзывы",
    }
    nav_sections: list[dict] = []
    for tool_name, phase_key, _ in _TOOL_TO_SECTION:
        if f"{phase_key}_interp" in data:
            nav_sections.append({
                "id": f"sec-{phase_key.lower()}",
                "label": nav_labels.get(phase_key, phase_key),
            })
    hero_meta["nav_sections"] = nav_sections
    data["hero_meta"] = hero_meta

    return data
