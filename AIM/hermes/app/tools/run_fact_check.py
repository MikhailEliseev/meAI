"""
run_fact_check — Hermes tool: Verify factual claims in scout report against source data.

This tool is Phase 13 (FACT_CHECK) of the pipeline. It runs AFTER HTML BUILD (Phase 10)
and BEFORE QC CRITIQUE (Phase 11).

What it does:
1. Loads all *_interpretation.json files from session archive
2. Extracts factual claims (ИНН, ОГРН, PageSpeed metrics, competitors, etc.)
3. Re-runs corresponding tools to get fresh data
4. Compares interpretation claims vs fresh data with tolerance thresholds
5. Returns fact-check score + detailed verification results

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from tools.registry import registry
from app.tools.session_archive import load_all_data

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 300.0  # fact-check может занять время (повторные вызовы tools)


# ── Типы проверяемых фактов ──

FACT_CATEGORIES = {
    "legal": {
        "name": "Юридические данные",
        "fields": ["ИНН", "ОГРН", "Полное название", "Руководитель", "Год основания"],
        "priority": "critical",
    },
    "pagespeed": {
        "name": "PageSpeed метрики",
        "fields": ["Общий балл", "LCP", "FCP", "TTI", "TBT", "CLS", "SI"],
        "priority": "critical",
    },
    "competitors": {
        "name": "Конкуренты",
        "fields": ["Список конкурентов", "URL конкурентов"],
        "priority": "critical",
    },
    "financials": {
        "name": "Финансовые данные",
        "fields": ["Выручка", "Чистая прибыль", "Рост"],
        "priority": "important",
    },
    "hh_vacancies": {
        "name": "Вакансии hh.ru",
        "fields": ["Количество вакансий"],
        "priority": "important",
    },
    "review_platforms": {
        "name": "Платформы отзывов",
        "fields": ["Количество страниц", "Рейтинг"],
        "priority": "important",
    },
    "smi_mentions": {
        "name": "Упоминания в СМИ",
        "fields": ["Количество упоминаний"],
        "priority": "important",
    },
}


# ── Извлечение фактов из интерпретаций ──

def _extract_legal_facts(interpretations: dict) -> dict:
    """Извлечь юридические данные (ИНН, ОГРН) из интерпретаций.

    Args:
        interpretations: {"PERPLEXITY_interpretation": {"content": "..."}, ...}

    Returns:
        {"inn": "7702394380", "ogrn": "5157746118602", ...} или {}
    """
    facts = {}

    # Ищем в PERPLEXITY_interpretation (там обычно первичные данные о клиенте)
    perplexity = interpretations.get("PERPLEXITY_interpretation", {})
    content = perplexity.get("content", "") if isinstance(perplexity, dict) else ""

    # Паттерны для извлечения
    inn_match = re.search(r'ИНН:\s*(\d{10,12})', content)
    if inn_match:
        facts["inn"] = inn_match.group(1)

    ogrn_match = re.search(r'ОГРН:\s*(\d{13,15})', content)
    if ogrn_match:
        facts["ogrn"] = ogrn_match.group(1)

    # Полное название
    name_match = re.search(r'Полное название:\s*([^\n]+)', content)
    if name_match:
        facts["full_name"] = name_match.group(1).strip()

    # Год основания
    year_match = re.search(r'Год основания:\s*(\d{4})', content)
    if year_match:
        facts["founded_year"] = year_match.group(1)

    # Руководитель
    ceo_match = re.search(r'Руководитель:\s*([^\n]+)', content)
    if ceo_match:
        facts["ceo"] = ceo_match.group(1).strip()

    return facts


def _extract_pagespeed_facts(interpretations: dict) -> dict:
    """Извлечь PageSpeed метрики из интерпретаций.

    Returns:
        {"score": 22, "lcp": 18.1, "fcp": 8.6, ...} или {}
    """
    facts = {}

    tech_audit = interpretations.get("TECH AUDIT_interpretation", {})
    content = tech_audit.get("content", "") if isinstance(tech_audit, dict) else ""

    # Паттерны
    score_match = re.search(r'Общий балл[^\d]*(\d+)\s*из\s*100', content)
    if score_match:
        facts["score"] = int(score_match.group(1))

    lcp_match = re.search(r'LCP[^\d]*([\d.,]+)\s*с', content)
    if lcp_match:
        facts["lcp"] = float(lcp_match.group(1).replace(',', '.'))

    fcp_match = re.search(r'FCP[^\d]*([\d.,]+)\s*с', content)
    if fcp_match:
        facts["fcp"] = float(fcp_match.group(1).replace(',', '.'))

    tti_match = re.search(r'TTI[^\d]*([\d.,]+)\s*с', content)
    if tti_match:
        facts["tti"] = float(tti_match.group(1).replace(',', '.'))

    tbt_match = re.search(r'TBT[^\d]*([\d,\s]+)\s*мс', content)
    if tbt_match:
        tbt_str = tbt_match.group(1).replace(',', '').replace(' ', '')
        facts["tbt"] = int(tbt_str)

    cls_match = re.search(r'CLS[^\d]*([\d.,]+)', content)
    if cls_match:
        facts["cls"] = float(cls_match.group(1).replace(',', '.'))

    si_match = re.search(r'SI[^\d]*([\d.,]+)\s*с', content)
    if si_match:
        facts["si"] = float(si_match.group(1).replace(',', '.'))

    return facts


def _extract_competitors_facts(interpretations: dict) -> dict:
    """Извлечь список конкурентов из интерпретаций.

    Returns:
        {"competitors": [{"name": "Gen87", "url": "https://gen87.ru"}, ...]} или {}
    """
    facts = {"competitors": []}

    # Ищем в PERPLEXITY (там первичный список) и COMPETITORS (там детали)
    for key in ["PERPLEXITY_interpretation", "COMPETITORS_interpretation"]:
        interp = interpretations.get(key, {})
        content = interp.get("content", "") if isinstance(interp, dict) else ""

        # Паттерн: "- Gen87 | URL: https://gen87.ru | Специализация: ..."
        pattern = r'-\s*([^|]+?)\s*\|\s*URL:\s*(https?://[^\s|]+)'
        matches = re.findall(pattern, content)

        for name, url in matches:
            name = name.strip()
            url = url.strip()
            # Дедупликация по URL
            if not any(c["url"] == url for c in facts["competitors"]):
                facts["competitors"].append({"name": name, "url": url})

    return facts


def _extract_review_platforms_facts(interpretations: dict) -> dict:
    """Извлечь данные о платформах отзывов из SOCIAL VERIFIER интерпретации.

    Returns:
        {"platforms_found": 5, "total_reviews": 124, "platforms": [...]} или {}
    """
    facts = {}

    social = interpretations.get("SOCIAL VERIFIER_interpretation", {})
    content = social.get("content", "") if isinstance(social, dict) else ""

    if not content:
        return facts

    # Количество найденных платформ (Яндекс, Google, Продокторов, 2ГИС, Отзовик, IRecommend, Zoon)
    platform_keywords = {
        "Яндекс.Карты": r"(?:Яндекс\.Карты|Яндекс\s*Карты|yandex\.ru/maps)",
        "Google Maps": r"(?:Google\s*Maps|google\.com/maps)",
        "ПроДокторов": r"(?:ПроДокторов|Продокторов|prodoctorov)",
        "2ГИС": r"(?:2ГИС|2GIS|2gis)",
        "Отзовик": r"(?:Отзовик|Otzovik|otzovik)",
        "IRecommend": r"(?:IRecommend|irecommend)",
        "Zoon": r"(?:Zoon|zoon\.ru)",
    }

    platforms_seen = []
    for name, pattern in platform_keywords.items():
        if re.search(pattern, content, re.IGNORECASE):
            platforms_seen.append(name)

    if platforms_seen:
        facts["platforms_found"] = len(platforms_seen)
        facts["platforms"] = platforms_seen

    # Общее количество отзывов (ищем паттерны "N отзывов" или "отзывов: N")
    review_patterns = [
        r'(\d[\d\s]*)\s*(?:отзыв(?:ов|а)?)',
        r'(?:отзыв(?:ов|а)?)[:\s]+(\d[\d\s]*)',
        r'(\d[\d\s]*)\s*(?:review)',
    ]
    total_reviews = 0
    for pattern in review_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            try:
                count = int(match.group(1).replace(' ', '').replace('\xa0', ''))
                if 0 < count < 100000:  # sanity check
                    total_reviews += count
            except ValueError:
                continue
        if total_reviews > 0:
            break  # берём первое совпадение паттерна

    if total_reviews > 0:
        facts["total_reviews"] = total_reviews

    return facts


def _extract_hh_facts(interpretations: dict) -> dict:
    """Извлечь данные о вакансиях hh.ru из KEY PERSONS интерпретации.

    Returns:
        {"vacancies_found": 3, "verdict": "data_found"} или {}
    """
    facts = {}

    key_persons = interpretations.get("KEY PERSONS_interpretation", {})
    content = key_persons.get("content", "") if isinstance(key_persons, dict) else ""

    if not content:
        return facts

    # Поиск количества вакансий
    vacancy_patterns = [
        r'(\d+)\s*(?:ваканси\w+|vacanc\w+)',
        r'(?:hh\.ru|headhunter)[^\d]*(\d+)\s*(?:ваканси\w+|vacanc\w+)?',
        r'на\s*hh\.ru[^\d]*?(\d+)\s*(?:ваканси\w+)?',
    ]
    vacancies = 0
    for pattern in vacancy_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                count = int(match.group(1))
                if 0 <= count < 1000:  # sanity check
                    vacancies = count
                    break
            except ValueError:
                continue

    # Если нашли упоминание "нет вакансий" или "вакансий не найдено"
    if vacancies == 0:
        if re.search(r'(?:нет\s+ваканси|ваканси\w+\s+не\s+найден|не\s+обнаруже\w+\s+ваканси)', content, re.IGNORECASE):
            facts["verdict"] = "no_data"
            facts["vacancies_found"] = 0
            return facts

    # Добавляем факт ТОЛЬКО если число вакансий извлечено.
    # Если hh.ru упоминается, но число не найдено — возвращаем пустой dict,
    # чтобы verify выдал "skipped", а не ложный "mismatch".
    if vacancies > 0:
        facts["vacancies_found"] = vacancies
        facts["verdict"] = "data_found"

    return facts


def _extract_smi_facts(interpretations: dict) -> dict:
    """Извлечь данные об упоминаниях в СМИ из SMI MENTIONS интерпретации.

    Returns:
        {"total_mentions": 12, "categories_with_mentions": 3} или {}
    """
    facts = {}

    smi = interpretations.get("SMI MENTIONS_interpretation", {})
    content = smi.get("content", "") if isinstance(smi, dict) else ""

    if not content:
        return facts

    # Общее количество упоминаний
    mention_patterns = [
        r'(\d+)\s*(?:упоминани\w+|mention)',
        r'(?:упоминани\w+|mention)[:\s]+(\d+)',
        r'(?:найдено|обнаружено|всего)[^\d]*(\d+)\s*(?:упоминани\w+|mention|публикаци\w+|стат\w+)',
    ]
    total_mentions = None
    for pattern in mention_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                count = int(match.group(1))
                if 0 <= count < 10000:  # sanity check
                    total_mentions = count
                    break
            except ValueError:
                continue

    # Категории СМИ (деловые, медицинские, региональные, lifestyle)
    category_keywords = {
        "business": r'(?:деловы|forbes|rbc|коммерсант|vedomosti|тасс|ria|interfax)',
        "medical": r'(?:медицинск|vademec|medvestnik|medportal|doctorpiter|medlinks)',
        "regional": r'(?:региональн|fontanka|dp\.ru|sobaka|mk\.ru|kp\.ru|aif|rg\.ru)',
        "lifestyle": r'(?:lifestyle|глянц|vogue|cosmopolitan|tatler|marieclaire|grazia|buro247)',
    }
    categories_seen = []
    for cat, pattern in category_keywords.items():
        if re.search(pattern, content, re.IGNORECASE):
            categories_seen.append(cat)

    if total_mentions is not None:
        facts["total_mentions"] = total_mentions

    if categories_seen:
        facts["categories_with_mentions"] = len(categories_seen)
        facts["categories"] = categories_seen

    return facts


# ── Проверка фактов против источников истины ──

async def _verify_legal_facts(extracted: dict, client_url: str) -> dict:
    """Проверить юридические данные через find_company_financials.

    Args:
        extracted: {"inn": "...", "ogrn": "...", ...}
        client_url: URL клиента (для получения свежих данных)

    Returns:
        {
            "status": "verified" | "mismatch" | "skipped" | "error",
            "details": [{"field": "ИНН", "claimed": "...", "actual": "...", "match": True}, ...],
            "mismatches": [],
            "critical": False
        }
    """
    if not extracted.get("inn") and not extracted.get("ogrn"):
        return {
            "status": "skipped",
            "reason": "No ИНН/ОГРН found in interpretation",
            "details": [],
            "mismatches": [],
            "critical": False,
        }

    try:
        # Вызываем find_company_financials с ИНН из интерпретации
        from app.tools.find_company_financials import handle_find_company_financials

        result_json = await handle_find_company_financials(
            inn=extracted.get("inn"),
            ogrn=extracted.get("ogrn")
        )
        result = json.loads(result_json)

        if not result.get("found"):
            return {
                "status": "error",
                "reason": result.get("error", "Company not found"),
                "details": [],
                "mismatches": [],
                "critical": True,  # если ИНН не найден — КРИТИЧНО
            }

        company = result.get("company", {})
        details = []
        mismatches = []

        # Проверка ИНН
        if extracted.get("inn"):
            actual_inn = company.get("inn")
            match = extracted["inn"] == actual_inn
            details.append({
                "field": "ИНН",
                "claimed": extracted["inn"],
                "actual": actual_inn,
                "match": match,
            })
            if not match:
                mismatches.append({
                    "field": "ИНН",
                    "claimed": extracted["inn"],
                    "actual": actual_inn,
                    "severity": "critical",
                })

        # Проверка ОГРН
        if extracted.get("ogrn"):
            actual_ogrn = company.get("ogrn")
            match = extracted["ogrn"] == actual_ogrn
            details.append({
                "field": "ОГРН",
                "claimed": extracted["ogrn"],
                "actual": actual_ogrn,
                "match": match,
            })
            if not match:
                mismatches.append({
                    "field": "ОГРН",
                    "claimed": extracted["ogrn"],
                    "actual": actual_ogrn,
                    "severity": "critical",
                })

        # Проверка полного названия (fuzzy match — допускаем кавычки, пробелы)
        if extracted.get("full_name"):
            actual_name = company.get("full_name") or company.get("name")
            claimed_norm = re.sub(r'[«»""\s]+', '', extracted["full_name"].lower())
            actual_norm = re.sub(r'[«»""\s]+', '', (actual_name or "").lower())
            match = claimed_norm in actual_norm or actual_norm in claimed_norm
            details.append({
                "field": "Полное название",
                "claimed": extracted["full_name"],
                "actual": actual_name,
                "match": match,
            })
            if not match:
                mismatches.append({
                    "field": "Полное название",
                    "claimed": extracted["full_name"],
                    "actual": actual_name,
                    "severity": "major",
                })

        status = "verified" if not mismatches else "mismatch"
        critical = any(m["severity"] == "critical" for m in mismatches)

        return {
            "status": status,
            "details": details,
            "mismatches": mismatches,
            "critical": critical,
        }

    except Exception as e:
        logger.exception("Error verifying legal facts")
        return {
            "status": "error",
            "reason": str(e),
            "details": [],
            "mismatches": [],
            "critical": False,
        }


async def _verify_pagespeed_facts(extracted: dict, client_url: str) -> dict:
    """Проверить PageSpeed метрики через run_lighthouse.

    Args:
        extracted: {"score": 22, "lcp": 18.1, "fcp": 8.6, "tti": 68.9, "tbt": 51280, "cls": 0.112, "si": 45.4}
        client_url: URL клиента

    Returns:
        {
            "status": "verified" | "mismatch" | "skipped" | "error",
            "details": [{"field": "score", "claimed": 22, "actual": 25, "match": True, "diff": "+13.6%"}, ...],
            "mismatches": [],
            "critical": False
        }
    """
    if not extracted:
        return {
            "status": "skipped",
            "reason": "No PageSpeed metrics found in interpretation",
            "details": [],
            "mismatches": [],
            "critical": False,
        }

    try:
        # Вызываем run_pagespeed (локальный инструмент Hermes) для получения свежих метрик
        from app.tools.run_pagespeed import handle_run_pagespeed

        result_json = await handle_run_pagespeed(url=client_url)
        result = json.loads(result_json)

        if result.get("error"):
            return {
                "status": "error",
                "reason": result.get("error", "PageSpeed tool error"),
                "details": [],
                "mismatches": [],
                "critical": False,
            }

        metrics = result
        details = []
        mismatches = []

        # Проверка score (допуск ±5 баллов)
        if "score" in extracted:
            claimed = extracted["score"]
            actual = metrics.get("performance_score")
            if actual is not None:
                diff = abs(actual - claimed)
                match = diff <= 5
                diff_percent = (actual - claimed) / claimed * 100 if claimed > 0 else 0
                details.append({
                    "field": "Общий балл",
                    "claimed": claimed,
                    "actual": actual,
                    "match": match,
                    "diff": f"{diff_percent:+.1f}%",
                })
                if not match:
                    severity = "critical" if diff > 15 else "major"
                    mismatches.append({
                        "field": "Общий балл",
                        "claimed": claimed,
                        "actual": actual,
                        "diff": f"{diff_percent:+.1f}%",
                        "severity": severity,
                    })

        # Проверка LCP (допуск ±15%)
        if "lcp" in extracted:
            claimed = extracted["lcp"]
            actual = metrics.get("lcp_seconds")
            if actual is not None:
                diff_percent = abs((actual - claimed) / claimed * 100) if claimed > 0 else 0
                match = diff_percent <= 15
                details.append({
                    "field": "LCP",
                    "claimed": f"{claimed}s",
                    "actual": f"{actual}s",
                    "match": match,
                    "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                })
                if not match:
                    severity = "critical" if diff_percent > 30 else "major"
                    mismatches.append({
                        "field": "LCP",
                        "claimed": f"{claimed}s",
                        "actual": f"{actual}s",
                        "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                        "severity": severity,
                    })

        # Проверка FCP (допуск ±15%)
        if "fcp" in extracted:
            claimed = extracted["fcp"]
            actual = metrics.get("fcp_seconds")
            if actual is not None:
                diff_percent = abs((actual - claimed) / claimed * 100) if claimed > 0 else 0
                match = diff_percent <= 15
                details.append({
                    "field": "FCP",
                    "claimed": f"{claimed}s",
                    "actual": f"{actual}s",
                    "match": match,
                    "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                })
                if not match and diff_percent > 30:
                    mismatches.append({
                        "field": "FCP",
                        "claimed": f"{claimed}s",
                        "actual": f"{actual}s",
                        "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                        "severity": "major",
                    })

        # Проверка TTI (допуск ±15%)
        if "tti" in extracted:
            claimed = extracted["tti"]
            actual = metrics.get("tti_seconds")
            if actual is not None:
                diff_percent = abs((actual - claimed) / claimed * 100) if claimed > 0 else 0
                match = diff_percent <= 15
                details.append({
                    "field": "TTI",
                    "claimed": f"{claimed}s",
                    "actual": f"{actual}s",
                    "match": match,
                    "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                })
                if not match and diff_percent > 30:
                    mismatches.append({
                        "field": "TTI",
                        "claimed": f"{claimed}s",
                        "actual": f"{actual}s",
                        "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                        "severity": "major",
                    })

        # Проверка TBT (допуск ±20%)
        if "tbt" in extracted:
            claimed = extracted["tbt"]
            actual = metrics.get("tbt_ms")
            if actual is not None:
                diff_percent = abs((actual - claimed) / claimed * 100) if claimed > 0 else 0
                match = diff_percent <= 20
                details.append({
                    "field": "TBT",
                    "claimed": f"{claimed}ms",
                    "actual": f"{actual}ms",
                    "match": match,
                    "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                })
                if not match and diff_percent > 30:
                    mismatches.append({
                        "field": "TBT",
                        "claimed": f"{claimed}ms",
                        "actual": f"{actual}ms",
                        "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                        "severity": "major",
                    })

        # Проверка CLS (допуск ±0.05)
        if "cls" in extracted:
            claimed = extracted["cls"]
            actual = metrics.get("cls_value")
            if actual is not None:
                diff = abs(actual - claimed)
                match = diff <= 0.05
                details.append({
                    "field": "CLS",
                    "claimed": claimed,
                    "actual": actual,
                    "match": match,
                    "diff": f"{actual - claimed:+.3f}",
                })
                if not match and diff > 0.1:
                    mismatches.append({
                        "field": "CLS",
                        "claimed": claimed,
                        "actual": actual,
                        "diff": f"{actual - claimed:+.3f}",
                        "severity": "major",
                    })

        # Проверка SI (допуск ±15%)
        if "si" in extracted:
            claimed = extracted["si"]
            actual = metrics.get("si_seconds")
            if actual is not None:
                diff_percent = abs((actual - claimed) / claimed * 100) if claimed > 0 else 0
                match = diff_percent <= 15
                details.append({
                    "field": "SI",
                    "claimed": f"{claimed}s",
                    "actual": f"{actual}s",
                    "match": match,
                    "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                })
                if not match and diff_percent > 30:
                    mismatches.append({
                        "field": "SI",
                        "claimed": f"{claimed}s",
                        "actual": f"{actual}s",
                        "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                        "severity": "major",
                    })

        status = "verified" if not mismatches else "mismatch"
        critical = any(m["severity"] == "critical" for m in mismatches)

        return {
            "status": status,
            "details": details,
            "mismatches": mismatches,
            "critical": critical,
        }

    except Exception as e:
        logger.exception("Error verifying PageSpeed facts")
        return {
            "status": "error",
            "reason": str(e),
            "details": [],
            "mismatches": [],
            "critical": False,
        }


async def _verify_competitors_facts(extracted: dict, client_url: str) -> dict:
    """Проверить список конкурентов через find_competitors.

    Args:
        extracted: {"competitors": [{"name": "Gen87", "url": "https://gen87.ru"}, ...]}
        client_url: URL клиента

    Returns:
        {
            "status": "verified" | "mismatch" | "skipped" | "error",
            "details": [{"field": "Конкурент", "claimed": "Gen87", "actual": "found", "match": True}, ...],
            "mismatches": [],
            "critical": False
        }
    """
    if not extracted.get("competitors"):
        return {
            "status": "skipped",
            "reason": "No competitors found in interpretation",
            "details": [],
            "mismatches": [],
            "critical": False,
        }

    try:
        # Вызываем find_competitors (локальный инструмент Hermes) для получения свежего списка
        from app.tools.find_competitors import handle_find_competitors

        result_json = await handle_find_competitors(url=client_url)
        result = json.loads(result_json)

        if result.get("error"):
            return {
                "status": "error",
                "reason": result.get("error", "Competitors tool error"),
                "details": [],
                "mismatches": [],
                "critical": False,
            }

        actual_competitors = result.get("competitors", [])
        actual_urls = {c.get("url") for c in actual_competitors if c.get("url")}

        claimed_competitors = extracted["competitors"]
        claimed_urls = {c["url"] for c in claimed_competitors}

        # Вычисляем пересечение
        intersection = claimed_urls & actual_urls
        overlap_percent = len(intersection) / len(claimed_urls) * 100 if claimed_urls else 0

        details = []
        for competitor in claimed_competitors:
            url = competitor["url"]
            match = url in actual_urls
            details.append({
                "field": "Конкурент",
                "claimed": f"{competitor['name']} ({url})",
                "actual": "найден" if match else "не найден",
                "match": match,
            })

        mismatches = []
        critical = False

        # Если пересечение < 70% — это критично
        if overlap_percent < 70:
            mismatches.append({
                "field": "Список конкурентов",
                "claimed": f"{len(claimed_urls)} URL",
                "actual": f"{len(intersection)} совпадений из {len(actual_urls)}",
                "overlap_percent": round(overlap_percent, 1),
                "severity": "critical" if overlap_percent < 50 else "major",
            })
            critical = overlap_percent < 50

        status = "verified" if overlap_percent >= 70 else "mismatch"

        return {
            "status": status,
            "details": details,
            "mismatches": mismatches,
            "critical": critical,
        }

    except Exception as e:
        logger.exception("Error verifying competitors facts")
        return {
            "status": "error",
            "reason": str(e),
            "details": [],
            "mismatches": [],
            "critical": False,
        }


async def _verify_review_platforms_facts(extracted: dict, client_url: str, city: str = "") -> dict:
    """Проверить данные о платформах отзывов через run_review_platforms.

    Args:
        extracted: {"platforms_found": 5, "total_reviews": 124, "platforms": [...]}
        client_url: URL клиента
        city: Город (для уточнения поиска)

    Returns:
        {
            "status": "verified"|"mismatch"|"skipped"|"error",
            "details": [...],
            "mismatches": [],
            "critical": False
        }
    """
    if not extracted:
        return {
            "status": "skipped",
            "reason": "No review platforms data found in interpretation",
            "details": [],
            "mismatches": [],
            "critical": False,
        }

    try:
        from app.tools.run_review_platforms import handle_run_review_platforms

        result_json = await handle_run_review_platforms(url=client_url, city=city)
        result = json.loads(result_json)

        if result.get("error"):
            return {
                "status": "error",
                "reason": result.get("error", "Review tool error"),
                "details": [],
                "mismatches": [],
                "critical": False,
            }

        actual_platforms = result.get("platforms_found", 0)
        actual_reviews = result.get("total_reviews_estimated")

        details = []
        mismatches = []

        # Проверка platforms_found (точное сравнение, допуск ±1)
        if "platforms_found" in extracted:
            claimed = extracted["platforms_found"]
            actual = actual_platforms
            diff = abs(actual - claimed)
            match = diff <= 1  # допуск ±1 платформа
            details.append({
                "field": "Количество платформ",
                "claimed": claimed,
                "actual": actual,
                "match": match,
                "diff": f"{actual - claimed:+d}",
            })
            if not match and diff > 2:
                mismatches.append({
                    "field": "Количество платформ",
                    "claimed": claimed,
                    "actual": actual,
                    "severity": "major",
                })

        # Проверка total_reviews (допуск ±30% — Perplexity вариативен)
        if "total_reviews" in extracted and actual_reviews is not None:
            claimed = extracted["total_reviews"]
            actual = actual_reviews
            if claimed > 0:
                diff_percent = abs((actual - claimed) / claimed * 100)
                match = diff_percent <= 30
                details.append({
                    "field": "Всего отзывов",
                    "claimed": claimed,
                    "actual": actual,
                    "match": match,
                    "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                })
                if not match and diff_percent > 50:
                    mismatches.append({
                        "field": "Всего отзывов",
                        "claimed": claimed,
                        "actual": actual,
                        "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                        "severity": "major",
                    })

        status = "verified" if not mismatches else "mismatch"
        critical = any(m["severity"] == "critical" for m in mismatches)

        return {
            "status": status,
            "details": details,
            "mismatches": mismatches,
            "critical": critical,
        }

    except Exception as e:
        logger.exception("Error verifying review platforms facts")
        return {
            "status": "error",
            "reason": str(e),
            "details": [],
            "mismatches": [],
            "critical": False,
        }


async def _verify_hh_facts(extracted: dict, client_url: str, company_name: str = "", city: str = "") -> dict:
    """Проверить данные о вакансиях hh.ru через run_hh_analysis.

    Args:
        extracted: {"vacancies_found": 3, "verdict": "data_found"} или
                   {"vacancies_found": 0, "verdict": "no_data"}
        client_url: URL клиента

    Returns:
        {status, details, mismatches, critical}
    """
    if not extracted:
        return {
            "status": "skipped",
            "reason": "No HH vacancies data found in interpretation",
            "details": [],
            "mismatches": [],
            "critical": False,
        }

    try:
        from app.tools.run_hh_analysis import handle_run_hh_analysis

        result_json = await handle_run_hh_analysis(
            url=client_url, company_name=company_name, city=city
        )
        result = json.loads(result_json)

        if result.get("error"):
            return {
                "status": "error",
                "reason": result.get("error", "HH analysis error"),
                "details": [],
                "mismatches": [],
                "critical": False,
            }

        actual_vacancies = result.get("vacancies_found", 0)
        actual_verdict = result.get("verdict", "no_data")

        details = []
        mismatches = []

        # Проверка verdict (data_found vs no_data)
        claimed_verdict = extracted.get("verdict")
        if claimed_verdict and claimed_verdict != actual_verdict:
            # Расхождение в самом факте наличия вакансий — критично
            mismatches.append({
                "field": "Наличие вакансий (verdict)",
                "claimed": claimed_verdict,
                "actual": actual_verdict,
                "severity": "major",
            })
            details.append({
                "field": "Наличие вакансий",
                "claimed": claimed_verdict,
                "actual": actual_verdict,
                "match": False,
            })
        elif claimed_verdict:
            details.append({
                "field": "Наличие вакансий",
                "claimed": claimed_verdict,
                "actual": actual_verdict,
                "match": True,
            })

        # Проверка количества вакансий (точное или ±1)
        if "vacancies_found" in extracted:
            claimed = extracted["vacancies_found"]
            actual = actual_vacancies
            diff = abs(actual - claimed)
            match = diff <= 1  # допуск ±1 (между запусками могут быть изменения)
            details.append({
                "field": "Количество вакансий",
                "claimed": claimed,
                "actual": actual,
                "match": match,
                "diff": f"{actual - claimed:+d}",
            })
            if not match and diff > 2:
                mismatches.append({
                    "field": "Количество вакансий",
                    "claimed": claimed,
                    "actual": actual,
                    "severity": "minor",
                })

        status = "verified" if not mismatches else "mismatch"
        critical = any(m["severity"] == "critical" for m in mismatches)

        return {
            "status": status,
            "details": details,
            "mismatches": mismatches,
            "critical": critical,
        }

    except Exception as e:
        logger.exception("Error verifying HH facts")
        return {
            "status": "error",
            "reason": str(e),
            "details": [],
            "mismatches": [],
            "critical": False,
        }


async def _verify_smi_facts(extracted: dict, client_url: str, company_name: str = "") -> dict:
    """Проверить данные об упоминаниях в СМИ через run_smi_mentions.

    Args:
        extracted: {"total_mentions": 12, "categories_with_mentions": 3, "categories": [...]}
        client_url: URL клиента

    Returns:
        {status, details, mismatches, critical}
    """
    if not extracted:
        return {
            "status": "skipped",
            "reason": "No SMI mentions data found in interpretation",
            "details": [],
            "mismatches": [],
            "critical": False,
        }

    try:
        from app.tools.run_smi_mentions import handle_run_smi_mentions

        result_json = await handle_run_smi_mentions(url=client_url, company_name=company_name)
        result = json.loads(result_json)

        if result.get("error"):
            return {
                "status": "error",
                "reason": result.get("error", "SMI mentions tool error"),
                "details": [],
                "mismatches": [],
                "critical": False,
            }

        actual_total = result.get("total_mentions", 0)
        actual_categories = result.get("categories_with_mentions", 0)

        details = []
        mismatches = []

        # Проверка total_mentions (допуск ±30% — DDG вариативен)
        if "total_mentions" in extracted:
            claimed = extracted["total_mentions"]
            actual = actual_total
            if claimed > 0:
                diff_percent = abs((actual - claimed) / claimed * 100)
                match = diff_percent <= 30
                details.append({
                    "field": "Всего упоминаний",
                    "claimed": claimed,
                    "actual": actual,
                    "match": match,
                    "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                })
                if not match and diff_percent > 50:
                    mismatches.append({
                        "field": "Всего упоминаний",
                        "claimed": claimed,
                        "actual": actual,
                        "diff": f"{(actual - claimed) / claimed * 100:+.1f}%",
                        "severity": "minor",
                    })
            elif claimed == 0 and actual == 0:
                # Оба нуля — совпадение
                details.append({
                    "field": "Всего упоминаний",
                    "claimed": 0,
                    "actual": 0,
                    "match": True,
                })

        # Проверка categories_with_mentions (допуск ±1)
        if "categories_with_mentions" in extracted:
            claimed = extracted["categories_with_mentions"]
            actual = actual_categories
            diff = abs(actual - claimed)
            match = diff <= 1
            details.append({
                "field": "Категорий с упоминаниями",
                "claimed": claimed,
                "actual": actual,
                "match": match,
                "diff": f"{actual - claimed:+d}",
            })
            if not match and diff > 1:
                mismatches.append({
                    "field": "Категорий с упоминаниями",
                    "claimed": claimed,
                    "actual": actual,
                    "severity": "minor",
                })

        status = "verified" if not mismatches else "mismatch"
        critical = any(m["severity"] == "critical" for m in mismatches)

        return {
            "status": status,
            "details": details,
            "mismatches": mismatches,
            "critical": critical,
        }

    except Exception as e:
        logger.exception("Error verifying SMI facts")
        return {
            "status": "error",
            "reason": str(e),
            "details": [],
            "mismatches": [],
            "critical": False,
        }


# ── Главная функция fact-check ──

async def handle_run_fact_check(session_hash=None, client_url=None, **kwargs) -> str:
    """Run fact-check on a completed scout report.

    Args:
        session_hash: Session ID (8-char hex, e.g., "8a6aafb7-7f7")
        client_url: Client URL (e.g., "https://seline.ru")

    Returns:
        JSON with fact-check results: {
            "status": "completed",
            "session_hash": "...",
            "checked_at": "...",
            "total_facts": 47,
            "verified": 42,
            "mismatched": 5,
            "score": 89.4,
            "grade": "GOOD",
            "critical_issues": [...],
            "details": [...]
        }
    """
    # Нормализация аргументов
    if isinstance(session_hash, dict):
        d = session_hash
        session_hash = d.get("session_hash", "")
        client_url = d.get("client_url", "")

    if not session_hash:
        return json.dumps({
            "error": "session_hash is required",
            "detail": "Provide the session ID to fact-check (e.g., '8a6aafb7-7f7')",
        })

    if not client_url:
        return json.dumps({
            "error": "client_url is required",
            "detail": "Provide the client URL to re-run verification tools (e.g., 'https://seline.ru')",
        })

    logger.info("Starting fact-check for session %s, client %s", session_hash[:12], client_url)

    try:
        # 1. Загрузить все интерпретации из session archive
        all_data = load_all_data(session_hash)

        if not all_data or len(all_data) <= 1:
            return json.dumps({
                "error": f"Session data not found for {session_hash}",
                "detail": f"Checked /opt/data/sessions-archive/{session_hash}/data/ — no interpretation files found",
            })

        logger.info("Loaded %d files from session archive", len(all_data))

        # 2. Извлечь факты из интерпретаций
        legal_facts = _extract_legal_facts(all_data)
        pagespeed_facts = _extract_pagespeed_facts(all_data)
        logger.info("DEBUG: all_data keys = %s", list(all_data.keys())[:10])
        logger.info("DEBUG: pagespeed_facts = %s", pagespeed_facts)
        competitors_facts = _extract_competitors_facts(all_data)
        review_facts = _extract_review_platforms_facts(all_data)
        hh_facts = _extract_hh_facts(all_data)
        smi_facts = _extract_smi_facts(all_data)

        # Попробовать извлечь city/company_name из metadata для уточнения поиска
        metadata = all_data.get("metadata", {}) if isinstance(all_data.get("metadata"), dict) else {}
        client_city = metadata.get("client_city", "") or ""
        client_company = metadata.get("client_name", "") or ""

        logger.info(
            "Extracted facts: legal=%d, pagespeed=%d, competitors=%d, reviews=%d, hh=%d, smi=%d",
            len(legal_facts),
            len(pagespeed_facts),
            len(competitors_facts.get("competitors", [])),
            len(review_facts),
            len(hh_facts),
            len(smi_facts),
        )

        # 3. Проверить факты против источников истины
        verification_results = []
        total_facts = 0
        verified_count = 0
        mismatched_count = 0
        critical_issues = []

        # Проверка юридических данных
        if legal_facts:
            logger.info("Verifying legal facts (ИНН/ОГРН)...")
            legal_verification = await _verify_legal_facts(legal_facts, client_url)
            verification_results.append({
                "category": "legal",
                "name": "Юридические данные",
                **legal_verification,
            })

            for detail in legal_verification.get("details", []):
                total_facts += 1
                if detail["match"]:
                    verified_count += 1
                else:
                    mismatched_count += 1

            if legal_verification.get("critical"):
                for mismatch in legal_verification.get("mismatches", []):
                    critical_issues.append(
                        f"{mismatch['field']}: отчёт {mismatch['claimed']}, факт {mismatch['actual']}"
                    )

        # Проверка PageSpeed метрик
        if pagespeed_facts:
            logger.info("Verifying PageSpeed metrics...")
            pagespeed_verification = await _verify_pagespeed_facts(pagespeed_facts, client_url)
            verification_results.append({
                "category": "pagespeed",
                "name": "PageSpeed метрики",
                **pagespeed_verification,
            })

            for detail in pagespeed_verification.get("details", []):
                total_facts += 1
                if detail["match"]:
                    verified_count += 1
                else:
                    mismatched_count += 1

            if pagespeed_verification.get("critical"):
                for mismatch in pagespeed_verification.get("mismatches", []):
                    critical_issues.append(
                        f"{mismatch['field']}: отчёт {mismatch['claimed']}, факт {mismatch['actual']} (расхождение {mismatch['diff']})"
                    )

        # Проверка конкурентов
        if competitors_facts.get("competitors"):
            logger.info("Verifying competitors (count: %d)...", len(competitors_facts["competitors"]))
            competitors_verification = await _verify_competitors_facts(competitors_facts, client_url)
            verification_results.append({
                "category": "competitors",
                "name": "Конкуренты",
                **competitors_verification,
            })

            for detail in competitors_verification.get("details", []):
                total_facts += 1
                if detail["match"]:
                    verified_count += 1
                else:
                    mismatched_count += 1

            if competitors_verification.get("critical"):
                for mismatch in competitors_verification.get("mismatches", []):
                    critical_issues.append(
                        f"Конкуренты: совпадение {mismatch['overlap_percent']}% (порог 70%)"
                    )

        # Проверка платформ отзывов (Review Platforms)
        if review_facts:
            logger.info("Verifying review platforms facts...")
            review_verification = await _verify_review_platforms_facts(
                review_facts, client_url, city=client_city
            )
            verification_results.append({
                "category": "review_platforms",
                "name": "Платформы отзывов",
                **review_verification,
            })

            for detail in review_verification.get("details", []):
                total_facts += 1
                if detail["match"]:
                    verified_count += 1
                else:
                    mismatched_count += 1

            if review_verification.get("critical"):
                for mismatch in review_verification.get("mismatches", []):
                    critical_issues.append(
                        f"{mismatch['field']}: отчёт {mismatch['claimed']}, факт {mismatch['actual']}"
                    )

        # Проверка вакансий hh.ru
        if hh_facts:
            logger.info("Verifying HH vacancies facts...")
            hh_verification = await _verify_hh_facts(
                hh_facts, client_url, company_name=client_company, city=client_city
            )
            verification_results.append({
                "category": "hh_vacancies",
                "name": "Вакансии hh.ru",
                **hh_verification,
            })

            for detail in hh_verification.get("details", []):
                total_facts += 1
                if detail["match"]:
                    verified_count += 1
                else:
                    mismatched_count += 1

            if hh_verification.get("critical"):
                for mismatch in hh_verification.get("mismatches", []):
                    critical_issues.append(
                        f"{mismatch['field']}: отчёт {mismatch['claimed']}, факт {mismatch['actual']}"
                    )

        # Проверка упоминаний в СМИ
        if smi_facts:
            logger.info("Verifying SMI mentions facts...")
            smi_verification = await _verify_smi_facts(
                smi_facts, client_url, company_name=client_company
            )
            verification_results.append({
                "category": "smi_mentions",
                "name": "Упоминания в СМИ",
                **smi_verification,
            })

            for detail in smi_verification.get("details", []):
                total_facts += 1
                if detail["match"]:
                    verified_count += 1
                else:
                    mismatched_count += 1

            if smi_verification.get("critical"):
                for mismatch in smi_verification.get("mismatches", []):
                    critical_issues.append(
                        f"{mismatch['field']}: отчёт {mismatch['claimed']}, факт {mismatch['actual']}"
                    )

        # 4. Вычислить score
        score = (verified_count / total_facts * 100) if total_facts > 0 else 0.0

        # 5. Определить grade
        if score >= 95:
            grade = "EXCELLENT"
        elif score >= 85:
            grade = "GOOD"
        elif score >= 70:
            grade = "ACCEPTABLE"
        elif score >= 50:
            grade = "POOR"
        else:
            grade = "FAILED"

        # 6. Сформировать результат
        result = {
            "status": "completed",
            "session_hash": session_hash,
            "client_url": client_url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "total_facts": total_facts,
            "verified": verified_count,
            "mismatched": mismatched_count,
            "score": round(score, 1),
            "grade": grade,
            "critical_issues": critical_issues,
            "details": verification_results,
        }

        logger.info("Fact-check completed: score=%.1f%%, grade=%s, critical=%d",
                    score, grade, len(critical_issues))

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("Unexpected error in run_fact_check")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "session_hash": session_hash,
        })


# ── Регистрация инструмента ──

registry.register(
    name="run_fact_check",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_fact_check",
            "description": (
                "Verify factual claims in the scout report against source data. "
                "This tool runs AFTER HTML BUILD and BEFORE QC CRITIQUE. "
                "It re-runs tools (find_company_financials, run_pagespeed, find_competitors, etc.) "
                "to get fresh data and compares it with what's in the interpretation files. "
                "Returns fact-check score (0-100%) and detailed verification results. "
                "Call this tool ONCE per session, after all phases are complete."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_hash": {
                        "type": "string",
                        "description": "Session ID (8-char hex, e.g., '8a6aafb7-7f7'). Required.",
                    },
                    "client_url": {
                        "type": "string",
                        "description": "Client URL (e.g., 'https://seline.ru'). Required for re-running verification tools.",
                    },
                },
                "required": ["session_hash", "client_url"],
            },
        },
    },
    handler=handle_run_fact_check,
    check_fn=lambda: True,
    is_async=True,
    description="Verify factual claims in scout report by re-running tools and comparing results",
    emoji="✅",
)
