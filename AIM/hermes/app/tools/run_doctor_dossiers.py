"""
run_doctor_dossiers — Hermes tool: Doctor Dossier Intelligence

Searches for doctor profiles across Russian medical platforms:
- ProDoctorov (ratings, reviews, specializations)
- DocDoc / SberHealth (appointment platforms)
- eLibrary / CyberLeninka (scientific publications)
- General web search for media mentions, interviews, social profiles

Uses Firecrawl search API for each platform in parallel.
Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging

from tools.registry import registry

logger = logging.getLogger(__name__)

# Platforms to search for doctor profiles
DOCTOR_PLATFORMS = [
    {
        "name": "ProDoctorov",
        "domain": "prodoctorov.ru",
        "query_template": '{doctor_name} site:prodoctorov.ru',
        "category": "ratings",
    },
    {
        "name": "DocDoc",
        "domain": "docdoc.ru",
        "query_template": '{doctor_name} site:docdoc.ru',
        "category": "appointments",
    },
    {
        "name": "СберЗдоровье",
        "domain": "sberhealth.ru",
        "query_template": '{doctor_name} site:sberhealth.ru',
        "category": "appointments",
    },
    {
        "name": "НаПоправку",
        "domain": "napopravku.ru",
        "query_template": '{doctor_name} site:napopravku.ru',
        "category": "appointments",
    },
    {
        "name": "eLibrary",
        "domain": "elibrary.ru",
        "query_template": '{doctor_name} site:elibrary.ru',
        "category": "publications",
    },
    {
        "name": "CyberLeninka",
        "domain": "cyberleninka.ru",
        "query_template": '{doctor_name} site:cyberleninka.ru',
        "category": "publications",
    },
    {
        "name": "Web Search",
        "query_template": '{doctor_name} врач отзывы',
        "category": "general",
    },
]


async def handle_run_doctor_dossiers(doctor_name=None, company_name=None, specialization=None, **kwargs) -> str:
    """Search for doctor profiles and reputation across Russian medical platforms.

    Scans ProDoctorov, DocDoc, SberHealth, eLibrary, and general web
    for doctor ratings, reviews, publications, and professional presence.

    Args:
        doctor_name: Doctor's full name for individual search (e.g., "Иванова Мария Сергеевна")
        company_name: Clinic name to find ALL doctors working there (alternative mode)
        specialization: Optional — specialization for better search precision

    Returns:
        JSON with profiles found per platform, ratings, publications count,
        and an overall visibility score.
    """
    if isinstance(doctor_name, dict):
        d = doctor_name
        doctor_name = d.get("doctor_name", "")
        company_name = d.get("company_name", company_name)
        if specialization is None:
            specialization = d.get("specialization", "")

    # company_name mode: search for all doctors at a clinic
    if company_name and not doctor_name:
        return await _search_clinic_doctors(company_name, specialization)

    if not doctor_name:
        return json.dumps({"error": "doctor_name or company_name is required"})

    logger.info("Doctor dossier search: %s (specialization: %s)", doctor_name, specialization)

    from app.main import push_tool_progress

    push_tool_progress("doctor-dossier", f"Ищу профили врача «{doctor_name}» на медицинских платформах…")

    # Build search query with specialization if available
    search_name = f"{doctor_name} {specialization}".strip()

    try:
        results = []

        # Search in batches of 3 to avoid rate limits
        platforms_to_search = DOCTOR_PLATFORMS[:7]

        for i in range(0, len(platforms_to_search), 3):
            batch = platforms_to_search[i:i + 3]

            tasks = [
                _search_platform(platform, search_name)
                for platform in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, result in enumerate(batch_results):
                platform = batch[j]
                if isinstance(result, Exception):
                    logger.warning("Doctor search failed for %s: %s", platform["name"], result)
                    results.append({
                        "platform": platform["name"],
                        "category": platform["category"],
                        "found": False,
                        "error": str(result),
                    })
                else:
                    results.append(result)

            if i + 3 < len(platforms_to_search):
                await asyncio.sleep(1)

        # Aggregate findings
        platforms_with_profiles = [r for r in results if r.get("found")]
        total_profiles = sum(len(r.get("profiles", [])) for r in platforms_with_profiles)

        # Visibility score
        if len(platforms_with_profiles) >= 4:
            visibility = "высокая — врач активно представлен в профессиональных сетях"
        elif len(platforms_with_profiles) >= 2:
            visibility = "средняя — врач имеет профили на основных платформах"
        elif len(platforms_with_profiles) >= 1:
            visibility = "низкая — врач почти невидим онлайн"
        else:
            visibility = "отсутствует — врач не найден на медицинских платформах"

        push_tool_progress(
            "doctor-dossier",
            f"✅ Врач «{doctor_name}»: {total_profiles} профилей на {len(platforms_with_profiles)} платформах — {visibility}",
        )

        # Build structured dossier
        dossier = {
            "doctor_name": doctor_name,
            "specialization": specialization,
            "total_profiles_found": total_profiles,
            "platforms_with_presence": len(platforms_with_profiles),
            "visibility": visibility,
            "platforms": results,
        }

        # Extract best rating if available
        ratings = []
        for r in results:
            for p in r.get("profiles", []):
                if p.get("rating"):
                    try:
                        ratings.append(float(p["rating"]))
                    except (ValueError, TypeError):
                        pass
        if ratings:
            dossier["best_rating"] = max(ratings)
            dossier["avg_rating"] = round(sum(ratings) / len(ratings), 1)
            dossier["ratings_count"] = len(ratings)

        # Count publications
        pub_platforms = [r for r in results if r.get("category") == "publications"]
        pub_count = sum(p.get("count", 0) for p in pub_platforms)
        dossier["publications_found"] = pub_count

        return json.dumps(dossier, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("Doctor dossier search failed")
        return json.dumps({"error": "Doctor dossier search failed", "detail": str(e)})


async def _search_platform(platform: dict, doctor: str) -> dict:
    """Search a single platform for doctor profiles using unified search fallback."""
    from app.tools._search_fallback import search as fallback_search

    query = platform["query_template"].format(doctor_name=doctor)
    results, provider = await fallback_search(query, max_results=8)

    if not results:
        return {
            "platform": platform["name"],
            "category": platform["category"],
            "found": False,
            "count": 0,
            "profiles": [],
            "source": provider,
        }

    profiles = []
    for item in results:
        title = item.get("title", "")
        url = item.get("url", "")
        snippet = (item.get("description", ""))[:300]

        # Try to extract rating from snippet
        rating = None
        import re
        rating_match = re.search(r'(\d[\.,]\d)\s*(?:/|из)\s*\d', snippet)
        if rating_match:
            rating = rating_match.group(1).replace(",", ".")
        else:
            # Try "4.5 звезд" pattern
            rating_match = re.search(r'(\d[\.,]?\d*)\s*(?:звезд|балл|star)', snippet, re.IGNORECASE)
            if rating_match:
                rating = rating_match.group(1).replace(",", ".")

        profiles.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "rating": rating,
        })

    return {
        "platform": platform["name"],
        "category": platform["category"],
        "found": len(profiles) > 0,
        "count": len(profiles),
        "profiles": profiles,
        "source": provider,
    }



async def _search_clinic_doctors(company_name: str, specialization: str = "") -> str:
    """Search for all doctors working at a clinic.

    Uses search fallback to find the clinic page on ProDoctorov and other platforms,
    then extracts doctor names from the results.
    """
    logger.info("Clinic doctor search: %s (specialization: %s)", company_name, specialization)

    from app.main import push_tool_progress
    from app.tools._search_fallback import search as fallback_search

    push_tool_progress("doctor-dossier", f"Ищу врачей клиники «{company_name}» на медицинских платформах…")

    search_query = f"{company_name} {specialization} врачи специалисты".strip()

    try:
        # Search for clinic on ProDoctorov
        clinic_results = []
        results, provider = await fallback_search(f"{search_query} site:prodoctorov.ru", max_results=5)
        for item in results:
            clinic_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": (item.get("description", ""))[:500],
            })

        # Extract doctor names from clinic page titles/descriptions
        import re
        doctor_names = set()
        for r in clinic_results:
            combined = r["title"] + " " + r["description"]
            # Russian name patterns: Surname Firstname Patronymic
            name_pattern = re.findall(r'[А-Я][а-яё]+\s+[А-Я][а-яё]+(?:\s+[А-Я][а-яё]+)?', combined)
            for name in name_pattern:
                if len(name) > 10 and not any(w in name.lower() for w in ("клиник", "центр", "город", "медицинск", "отзыв", "запись", "приём", "консультаци")):
                    doctor_names.add(name)

        if not doctor_names:
            # Fallback: search general web
            results2, provider2 = await fallback_search(f"{search_query} врачи клиники отзывы", max_results=5)
            for item in results2:
                clinic_results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": (item.get("description", ""))[:500],
                })

        push_tool_progress(
            "doctor-dossier",
            f"✅ Клиника «{company_name}»: найдено {len(doctor_names)} потенциальных врачей",
        )

        return json.dumps({
            "mode": "clinic_search",
            "company_name": company_name,
            "specialization": specialization,
            "doctors_found": len(doctor_names),
            "doctor_names": sorted(list(doctor_names))[:15],
            "clinic_pages": clinic_results[:5],
            "note": "Company name mode — searched for clinic on ProDoctorov to find all doctors",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("Clinic doctor search failed")
        return json.dumps({"error": "Clinic doctor search failed", "detail": str(e)})


registry.register(
    name="run_doctor_dossiers",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_doctor_dossiers",
            "description": (
                "Search for doctor profiles or find all doctors at a clinic's professional profiles across Russian medical platforms: "
                "ProDoctorov (ratings/reviews), DocDoc, SberHealth, Napopravku (appointment platforms), "
                "eLibrary, CyberLeninka (scientific publications), plus general web search. "
                "Returns structured dossier: which platforms the doctor is on, ratings, "
                "publication count, and overall online visibility score. "
                "Use this to evaluate a competitor clinic's key doctors — "
                "star doctors with high ratings and publications are powerful patient magnets. "
                "Also reveals if competitors are investing in doctor personal branding."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name": {
                        "type": "string",
                        "description": "[REQUIRED] Doctor's full name in Russian (e.g., 'Иванова Мария Сергеевна')",
                    },
                    "doctor_name": {
                        "type": "string",
                        "description": "Doctor's full name in Russian (e.g., 'Иванова Мария Сергеевна'). Use with or instead of company_name.",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Clinic name to find ALL doctors working there. Alternative to doctor_name.",
                    },
                    "specialization": {
                        "type": "string",
                        "description": "Optional specialization for better search precision (e.g., 'пластический хирург', 'дерматолог')",
                    },
                },
                "required": [],
            },
        },
    },
    handler=handle_run_doctor_dossiers,
    check_fn=lambda: True,
    is_async=True,
    description="Search doctor profiles on ProDoctorov/DocDoc/SberHealth/eLibrary — ratings, publications, visibility score",
    emoji="👨‍⚕️",
)
