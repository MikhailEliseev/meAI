"""QC Gate -- проверка качества данных перед публикацией отчета.

Адаптация v1 qc_checklist.py (18 пунктов) под v2 архитектуру.
Проверяет 4 блока: профиль, выручка, конкуренты, отзывы.

PASS_THRESHOLD = 75% -- минимум 3 из 4 пунктов.
Fallback для города: если city пустой, извлекаем из address.
Если FAIL -- отчет НЕ публикуется.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

PASS_THRESHOLD = 0.75  # 75% -- минимум 3 из 4 пунктов


def _safe_json(raw: str) -> dict | list | None:
    """Безопасно распарсить JSON."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _check_profile(
    collected_results: dict, profile_cache: dict
) -> dict:
    """Пункт 1: Профиль клиники.

    PASS: есть название + (ИНН или город).
    Источники: extract_clinic_profile (collected_results) или profile_cache.
    """
    name = (
        profile_cache.get("company_name")
        or profile_cache.get("brand_name")
        or ""
    )
    inn = profile_cache.get("inn", "") or ""
    city = profile_cache.get("city", "") or ""

    # Fallback: попробовать извлечь из extract_clinic_profile
    if not name or not inn:
        raw = collected_results.get("extract_clinic_profile", "")
        data = _safe_json(raw)
        if data and isinstance(data, dict):
            name = name or data.get("company_name") or data.get("brand_name") or ""
            inn = inn or data.get("inn", "") or ""
            city = city or data.get("city", "") or ""

    # Task 3: Fallback — извлечь город из address (website_scraper данные)
    if not city:
        address = profile_cache.get("address", "") or ""
        if address:
            # Эвристика: "г. Москва", "Москва,", "Санкт-Петербург,"
            city_match = re.search(
                r'(?:г\.?\s*|г\.?\s+)([А-ЯЁ][а-яё]+(?:[-\s][А-ЯЁа-яё]+)*)',
                address
            )
            if city_match:
                city = city_match.group(1)
            else:
                # Попробовать извлечь первое слово с заглавной (Москва, Казань)
                city_match2 = re.match(r'^([А-ЯЁ][а-яё]+(?:[-\s][А-ЯЁа-яё]+)*)', address.strip())
                if city_match2:
                    candidate = city_match2.group(1)
                    # Фильтр: не "ул.", "пр.", "пер."
                    if candidate.lower() not in ("ул", "пр", "пер", "ш", "наб"):
                        city = candidate

    has_name = bool(name and len(name) > 2)
    has_identifier = bool(inn or city)

    passed = has_name and has_identifier
    details = {"name": name[:50], "inn": inn[:12], "city": city[:30]}
    return {"id": 1, "category": "profile", "passed": passed, "details": details}


def _check_financials(collected_results: dict, profile_cache: dict) -> dict:
    """Пункт 2: Выручка клиента (ФНС).

    PASS: есть company_financials с revenue > 0.
    """
    raw = collected_results.get("company_financials", "")
    data = _safe_json(raw)

    revenue = None
    if data and isinstance(data, dict):
        revenue = data.get("revenue") or data.get("latest_revenue")

    # Fallback: profile_cache может содержать revenue от auto-call
    if not revenue:
        revenue = profile_cache.get("revenue")

    has_revenue = False
    revenue_val = 0
    if revenue is not None:
        try:
            revenue_val = float(revenue)
            has_revenue = revenue_val > 0
        except (ValueError, TypeError):
            pass

    return {
        "id": 2,
        "category": "financials",
        "passed": has_revenue,
        "details": {"revenue": revenue_val},
    }


def _check_competitors(collected_results: dict) -> dict:
    """Пункт 3: Конкуренты (>=3 с выручкой).

    PASS: find_competitors вернул >=3 конкурента с revenue_year > 0.
    """
    raw = collected_results.get("find_competitors", "")
    data = _safe_json(raw)

    competitor_count = 0
    competitors_with_revenue = 0

    if data and isinstance(data, dict):
        comps = data.get("competitors", [])
        if isinstance(comps, list):
            competitor_count = len(comps)
            for c in comps:
                if isinstance(c, dict) and c.get("revenue_year"):
                    try:
                        if float(c["revenue_year"]) > 0:
                            competitors_with_revenue += 1
                    except (ValueError, TypeError):
                        pass

    passed = competitors_with_revenue >= 3
    return {
        "id": 3,
        "category": "competitors",
        "passed": passed,
        "details": {
            "total_found": competitor_count,
            "with_revenue": competitors_with_revenue,
        },
    }


def _check_reviews(collected_results: dict) -> dict:
    """Пункт 4: Отзывы (рейтинг на >=1 платформе).

    PASS: run_review_platforms вернул рейтинг хотя бы на одной платформе.
    """
    raw = collected_results.get("run_review_platforms", "")
    data = _safe_json(raw)

    platforms_with_rating = 0
    platforms_detail = {}

    if data and isinstance(data, dict):
        platforms = data.get("platforms", {})
        if isinstance(platforms, dict):
            for platform_name, pdata in platforms.items():
                if isinstance(pdata, dict) and pdata.get("rating"):
                    try:
                        rating = float(pdata["rating"])
                        if rating > 0:
                            platforms_with_rating += 1
                            platforms_detail[platform_name] = {
                                "rating": rating,
                                "reviews": pdata.get("reviews", 0),
                            }
                    except (ValueError, TypeError):
                        pass

    passed = platforms_with_rating >= 1
    return {
        "id": 4,
        "category": "reviews",
        "passed": passed,
        "details": platforms_detail,
    }


def run_qc_gate(
    collected_results: dict, profile_cache: dict
) -> dict:
    """Запустить QC проверку данных перед публикацией отчёта.

    Args:
        collected_results: dict tool_name → JSON-строка.
        profile_cache: dict с метаданными клиента.

    Returns:
        {
            "passed": bool,           # True если coverage >= PASS_THRESHOLD
            "coverage": float,        # 0.0 - 1.0 (доля пройденных проверок)
            "coverage_pct": int,      # 0-100
            "items": list[dict],      # детали по каждому пункту
            "critical_failures": list, # названия проваленных критических пунктов
            "threshold": float,       # PASS_THRESHOLD
        }
    """
    items = [
        _check_profile(collected_results, profile_cache),
        _check_financials(collected_results, profile_cache),
        _check_competitors(collected_results),
        _check_reviews(collected_results),
    ]

    passed_count = sum(1 for item in items if item["passed"])
    coverage = passed_count / len(items)
    coverage_pct = int(coverage * 100)

    overall_passed = coverage >= PASS_THRESHOLD

    critical_failures = [
        item["category"] for item in items if not item["passed"]
    ]

    result = {
        "passed": overall_passed,
        "coverage": round(coverage, 2),
        "coverage_pct": coverage_pct,
        "items": items,
        "critical_failures": critical_failures,
        "threshold": PASS_THRESHOLD,
    }

    logger.info(
        "QC Gate: %s (coverage=%d%%, passed=%d/%d, failures=%s)",
        "PASS" if overall_passed else "FAIL",
        coverage_pct,
        passed_count,
        len(items),
        critical_failures,
    )

    return result
