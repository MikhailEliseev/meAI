"""Глубокий LLM-анализ для публикуемого отчёта.

Отличие от чат-анализа (llm.py):
- LLM видит ПОЛНЫЕ данные (не заглушки) — выручку, отзывы, врачей, нейросводку
- Промпт просит развёрнутый анализ с цифрами (4 секции по 3-4 абзаца)
- Результат парсится по маркерам === и распределяется по секциям отчёта

Вызывается из _auto_publish_report() ПОСЛЕ QC gate, ДО build_data_dict().
Стоимость: +1 LLM-вызов (~$0.01, glm-5.2).
"""
import json
import logging
import re

import openai

from app.config import LLM_MODEL, LLM_TEMPERATURE, OMNIROUTE_AUTH, OMNIROUTE_URL
from app.prompts.report_analysis import REPORT_ANALYSIS_SYSTEM

logger = logging.getLogger(__name__)

# Маркеры секций в ответе LLM
_SECTION_MARKERS = ["ПОЗИЦИЯ", "СИЛЬНЫЕ", "РОСТ", "РЕКОМЕНДАЦИИ"]


def _safe_load(raw: str) -> dict | None:
    """Безопасно распарсить JSON-строку."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _fmt_money(val) -> str:
    """121000000 → '121 млн ₽'. None → 'нет данных'."""
    if not val:
        return "нет данных"
    try:
        n = float(val)
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f} млрд ₽"
        if n >= 1_000_000:
            return f"{n/1_000_000:.0f} млн ₽"
        return f"{n:,.0f} ₽".replace(",", " ")
    except (ValueError, TypeError):
        return "нет данных"


def _fmt_followers(val) -> str:
    """31000 → '31K'. None → '—'."""
    if not val:
        return "—"
    try:
        n = int(val)
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n//1_000}K"
        return str(n)
    except (ValueError, TypeError):
        return "—"


def _fmt_age(reg_date: str | None) -> str:
    """'2018-06-15' → '8 лет'. None → '—'."""
    if not reg_date:
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(str(reg_date)[:10])
        years = (datetime.now() - dt).days // 365
        return f"{years} лет" if years > 0 else "—"
    except (ValueError, TypeError):
        return "—"


def _build_context(collected_results: dict, profile_cache: dict) -> str:
    """Собрать структурированный context со ВСЕМИ данными для LLM.

    Это «глаза» аналитика — всё, что LLM должен видеть, чтобы писать анализ.
    Возвращает текст с разделами: ПРОФИЛЬ, ФИНАНСЫ, КОНКУРЕНТЫ, ОТЗЫВЫ.
    """
    cr = collected_results or {}
    pc = profile_cache or {}
    lines: list[str] = []

    # ── ПРОФИЛЬ ──────────────────────────────────────────────────────────────
    company_name = pc.get("company_name") or pc.get("brand_name") or "Клиника"
    lines.append("## ПРОФИЛЬ КЛИЕНТА")
    lines.append(f"Название: {company_name}")
    if pc.get("inn"):
        lines.append(f"ИНН: {pc['inn']}")
    if pc.get("city"):
        lines.append(f"Город: {pc['city']}")
    if pc.get("address"):
        lines.append(f"Адрес: {pc['address']}")

    # Специализация, услуги — из extract_clinic_profile
    profile = _safe_load(cr.get("extract_clinic_profile", ""))
    if profile:
        if profile.get("specialization"):
            lines.append(f"Специализация: {profile['specialization']}")
        if profile.get("services"):
            lines.append(f"Услуги: {', '.join(profile['services'][:8])}")

    # Врачи — из скрапера
    scrape = _safe_load(cr.get("scrape_clinic_website", ""))
    if scrape:
        if scrape.get("doctors"):
            docs = scrape["doctors"]
            doc_lines = []
            for d in docs[:8]:
                if isinstance(d, dict):
                    name = d.get("name", "")
                    spec = d.get("specialization", "")
                    doc_lines.append(f"  - {name}" + (f" ({spec})" if spec else ""))
            if doc_lines:
                lines.append(f"Врачи на сайте ({len(docs)} найдено):")
                lines.extend(doc_lines)
        if scrape.get("socials"):
            socials = scrape["socials"]
            parts = [f"{k}: {v}" for k, v in socials.items()]
            lines.append(f"Соцсети: {', '.join(parts)}")
        if scrape.get("cms"):
            lines.append(f"Платформа сайта: {scrape['cms']}")

    # ── ФИНАНСЫ КЛИЕНТА ───────────────────────────────────────────────────────
    lines.append("")
    lines.append("## ФИНАНСЫ КЛИЕНТА")
    fin = _safe_load(cr.get("company_financials", ""))
    if fin:
        rev = fin.get("revenue") or fin.get("latest_revenue")
        profit = fin.get("profit") or fin.get("latest_profit")
        trend = fin.get("revenue_trend", "")
        if rev:
            lines.append(f"Выручка: {_fmt_money(rev)}")
        else:
            lines.append("Выручка: нет данных (ФНС не нашёл)")
        if profit:
            lines.append(f"Прибыль: {_fmt_money(profit)}")
        if trend:
            lines.append(f"Тренд: {trend}")
    else:
        lines.append("Выручка: нет данных (ФНС не нашёл)")

    # ── КОНКУРЕНТЫ ────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("## КОНКУРЕНТЫ")
    comp_data = _safe_load(cr.get("find_competitors", ""))
    comps = comp_data.get("competitors", []) if isinstance(comp_data, dict) else []
    if comps:
        lines.append(f"Найдено конкурентов: {len(comps)}")
        for c in comps:
            brand = c.get("brand_name") or c.get("legal_name") or "?"
            rev = _fmt_money(c.get("revenue_year"))
            profit = _fmt_money(c.get("profit_year"))
            trend = c.get("revenue_trend", "—")
            age = _fmt_age(c.get("registration_date"))
            docs = c.get("surgeons_count") or c.get("employee_count") or "—"
            ig = _fmt_followers(c.get("instagram_followers"))
            cms = c.get("website_cms") or "—"
            lines.append(
                f"  - {brand}: выручка {rev}, прибыль {profit}, "
                f"тренд {trend}, возраст {age}, врачей {docs}, "
                f"Instagram {ig}, сайт {cms}"
            )
    else:
        lines.append("Конкуренты: не найдены")

    # ── ОТЗЫВЫ ────────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("## ОТЗЫВЫ И РЕПУТАЦИЯ")
    reviews = _safe_load(cr.get("run_review_platforms", ""))
    if reviews and isinstance(reviews, dict):
        platforms = reviews.get("platforms", {})
        for key, label in [("yandex", "Яндекс.Карты"), ("twogis", "2ГИС"), ("prodoctorov", "ПроДокторов")]:
            p = platforms.get(key, {})
            if isinstance(p, dict) and p.get("rating"):
                rating = p.get("rating")
                rev_count = p.get("reviews", "")
                rev_str = f" ({rev_count} отзывов)" if rev_count else ""
                lines.append(f"{label}: {rating}★{rev_str}")
        # AI-резюме отзывов от Яндекса (neuro_summary)
        neuro = reviews.get("neuro_summary", "")
        if neuro:
            lines.append(f"\nAI-резюме отзывов (от Яндекса): {neuro}")
        # Темы отзывов
        praise = reviews.get("praise_summary", "")
        if praise:
            lines.append(f"Что хвалят: {praise}")
        criticism = reviews.get("criticism_summary", "")
        if criticism:
            lines.append(f"Что критикуют: {criticism}")
        # Цитаты пациентов
        quotes = reviews.get("review_quotes", [])
        if quotes:
            lines.append("\nЦитаты пациентов:")
            for q in quotes[:5]:
                if isinstance(q, dict):
                    text = q.get("text", "")[:200]
                    src = q.get("source", "")
                    lines.append(f'  - "{text}" ({src})')
                elif isinstance(q, str):
                    lines.append(f'  - "{q[:200]}"')
        rep = reviews.get("reputation_summary", "")
        if rep:
            lines.append(f"\nОбщая репутация: {rep}")
    else:
        lines.append("Отзывы: не найдены")

    return "\n".join(lines)


def _parse_analysis_sections(text: str) -> dict[str, str]:
    """Разбить ответ LLM по маркерам === на dict.

    Возвращает {"position": "...", "strengths": "...", "growth": "...", "recommendations": "..."}.
    Если маркер не найден — пустая строка.
    """
    result = {key.lower(): "" for key in _SECTION_MARKERS}
    if not text:
        return result

    # Разрезаем по маркерам === SECTION ===
    pattern = r"===\s*(ПОЗИЦИЯ|СИЛЬНЫЕ|РОСТ|РЕКОМЕНДАЦИИ)\s*==="
    parts = re.split(pattern, text)

    # parts = ['', 'ПОЗИЦИЯ', 'текст...', 'СИЛЬНЫЕ', 'текст...', ...]
    for i in range(1, len(parts) - 1, 2):
        marker = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        key = marker.lower()
        if key in result:
            result[key] = content

    return result


async def generate_report_analysis(
    collected_results: dict,
    profile_cache: dict,
) -> str:
    """Сгенерировать глубокий LLM-анализ для отчёта.

    Args:
        collected_results: все результаты тулов (JSON-строки).
        profile_cache: метаданные клиента.

    Returns:
        Markdown-текст анализа с маркерами === СЕКЦИЯ ===.
        Пустая строка при ошибке (отчёт публикуется без анализа).
    """
    context = _build_context(collected_results, profile_cache)
    company_name = (profile_cache or {}).get("company_name", "клиники")

    logger.info("report_analysis: context=%d chars, generating analysis...", len(context))

    client = openai.AsyncOpenAI(
        base_url=OMNIROUTE_URL,
        api_key=OMNIROUTE_AUTH,
    )

    messages = [
        {"role": "system", "content": REPORT_ANALYSIS_SYSTEM},
        {"role": "user", "content": f"## ДАННЫЕ\n\n{context}\n\n## ЗАДАЧА\nНапиши глубокий маркетинговый анализ для {company_name}. Используй ВСЕ данные выше."},
    ]

    try:
        resp = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=4096,
            temperature=LLM_TEMPERATURE,
        )
        text = ""
        if resp.choices:
            # glm-5.2 reasoning model — content в message.content
            text = resp.choices[0].message.content or ""

        sections = _parse_analysis_sections(text)
        filled = sum(1 for v in sections.values() if v)
        logger.info("report_analysis: OK, %d/%d sections filled", filled, len(sections))

        if filled == 0:
            logger.warning("report_analysis: no sections parsed, returning raw text")
            return text

        return text
    except Exception as e:
        logger.error("report_analysis: LLM call failed: %s", e)
        return ""


def split_analysis_by_section(analysis_text: str) -> dict[str, str]:
    """Разбить analysis_text на секции для распределения по отчёту.

    Возвращает dict с ключами:
        - "profile": ПОЗИЦИЯ + СИЛЬНЫЕ (для секции «О клинике»)
        - "reviews": РОСТ + РЕКОМЕНДАЦИИ (для секции «Рынок/точки роста»)
        - "position": ПОЗИЦИЯ (для hero subtitle, если нужно)
        - "strengths": СИЛЬНЫЕ
        - "growth": РОСТ
        - "recommendations": РЕКОМЕНДАЦИИ
    """
    sections = _parse_analysis_sections(analysis_text)
    return {
        "profile": sections.get("позиция", "") + "\n\n" + sections.get("сильные", ""),
        "reviews": sections.get("рост", "") + "\n\n" + sections.get("рекомендации", ""),
        "position": sections.get("позиция", ""),
        "strengths": sections.get("сильные", ""),
        "growth": sections.get("рост", ""),
        "recommendations": sections.get("рекомендации", ""),
    }
