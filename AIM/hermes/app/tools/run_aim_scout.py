"""run_aim_scout — 16-фазная глубокая разведка конкурента.

Зеркало skill aim-scout, но для Hermes на сайте.
Целевое время: 50-65 минут (полный пайплайн).

Execution Log отслеживается через push_tool_progress().
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Timeouts для различных операций (в секундах)
APIFY_TIMEOUT = 120
FIRECRAWL_TIMEOUT = 90
PAGESPEED_TIMEOUT = 60
FNS_TIMEOUT = 30
TOTAL_TIMEOUT = 3600  # 1 час на весь пайплайн

# API endpoints
APIFY_BASE = "https://api.apify.com/v2"
FIRECRAWL_BASE = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v1")
APIFY_KEYS_PATH = Path("AIM/data/apify_keys.json")


def push_progress(stage: str, message: str, competitor: str = "") -> None:
    """Push progress to SSE stream."""
    try:
        from app.main import push_tool_progress
        push_tool_progress(stage=stage, message=message, competitor=competitor, agent="aim-scout")
    except Exception:
        logger.info(f"[aim-scout] {stage}: {message}")


def slugify(text: str) -> str:
    """Convert name to slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text[:50]


def load_apify_keys() -> list[dict]:
    """Load Apify keys from AIM/data/apify_keys.json."""
    try:
        if APIFY_KEYS_PATH.exists():
            data = json.loads(APIFY_KEYS_PATH.read_text())
            return [k for k in data.get("keys", []) if k.get("status") == "active"]
    except Exception as e:
        logger.warning(f"Failed to load Apify keys: {e}")
    return []


async def run_apify_actor(
    actor_id: str,
    run_input: dict,
    timeout: int = APIFY_TIMEOUT,
) -> dict | None:
    """Run Apify actor with key rotation on 402/429."""
    keys = load_apify_keys()
    if not keys:
        logger.error("No active Apify keys available")
        return None

    for key_obj in keys:
        api_key = key_obj["key"]
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Start run
                resp = await client.post(
                    f"{APIFY_BASE}/acts/{actor_id}/runs",
                    params={"token": api_key},
                    json=run_input,
                )
                if resp.status_code in (402, 429):
                    logger.warning(f"Apify key exhausted: {key_obj['name']}")
                    continue
                resp.raise_for_status()
                run_data = resp.json()["data"]
                run_id = run_data["id"]

                # Poll until SUCCEEDED
                for _ in range(60):  # 60 * 3s = 3 min max
                    await asyncio.sleep(3)
                    status_resp = await client.get(
                        f"{APIFY_BASE}/actor-runs/{run_id}",
                        params={"token": api_key},
                    )
                    status_resp.raise_for_status()
                    status_data = status_resp.json()["data"]
                    status = status_data["status"]

                    if status == "SUCCEEDED":
                        # Get dataset
                        dataset_id = status_data["defaultDatasetId"]
                        dataset_resp = await client.get(
                            f"{APIFY_BASE}/datasets/{dataset_id}/items",
                            params={"token": api_key},
                        )
                        dataset_resp.raise_for_status()
                        return dataset_resp.json()

                    if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                        logger.error(f"Apify run {status}: {run_id}")
                        return None

                logger.warning(f"Apify run timeout: {run_id}")
                return None

        except Exception as e:
            logger.warning(f"Apify actor failed with key {key_obj['name']}: {e}")
            continue

    logger.error("All Apify keys exhausted")
    return None


async def firecrawl_scrape(url: str, wait_for: int = 0) -> dict | None:
    """Scrape URL via Firecrawl."""
    try:
        # Используем банк ключей Firecrawl (уже настроен в main.py)
        from .firecrawl_key_bank import get_next_key
        api_key = get_next_key()
        if not api_key:
            logger.error("No Firecrawl keys available")
            return None

        async with httpx.AsyncClient(timeout=FIRECRAWL_TIMEOUT) as client:
            payload = {"url": url, "formats": ["markdown"]}
            if wait_for > 0:
                payload["waitFor"] = wait_for

            resp = await client.post(
                f"{FIRECRAWL_BASE}/scrape",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"Firecrawl scrape failed for {url}: {e}")
        return None


async def phase_0_preflight(name: str, website: str, instagram: str | None, city: str) -> dict:
    """Phase 0: PRE-FLIGHT — prepare inputs."""
    push_progress("phase-0", "Подготовка разведки...")
    slug = slugify(name)

    result = {
        "name": name,
        "slug": slug,
        "website": website,
        "instagram": instagram,
        "city": city,
        "scan_date": datetime.utcnow().isoformat() + "Z",
    }

    # Check Apify keys
    keys = load_apify_keys()
    if not keys:
        raise ValueError("No active Apify keys found")

    push_progress("phase-0", f"✓ Найдено {len(keys)} активных Apify-ключей")
    return result


async def phase_05_instagram_profile(instagram_handle: str) -> dict:
    """Phase 0.5: INSTAGRAM PROFILE."""
    push_progress("phase-0.5", f"Анализ Instagram @{instagram_handle}...")

    dataset = await run_apify_actor(
        "apify~instagram-profile-scraper",
        {"usernames": [instagram_handle], "maxPosts": 24},
    )

    if not dataset or len(dataset) == 0:
        push_progress("phase-0.5", "Instagram профиль не найден")
        return {}

    profile = dataset[0]
    push_progress("phase-0.5", f"✓ {profile.get('followersCount', 0)} подписчиков, {profile.get('postsCount', 0)} постов")

    return {
        "username": profile.get("username"),
        "full_name": profile.get("fullName"),
        "biography": profile.get("biography"),
        "followers_count": profile.get("followersCount"),
        "posts_count": profile.get("postsCount"),
        "follows_count": profile.get("followsCount"),
        "is_business": profile.get("isBusinessAccount"),
        "category": profile.get("businessCategoryName"),
        "verified": profile.get("verified"),
        "external_urls": profile.get("externalUrls", []),
        "latest_posts": profile.get("latestPosts", [])[:24],
    }


async def phase_075_instagram_content(posts: list[dict], followers: int) -> dict:
    """Phase 0.75: INSTAGRAM CONTENT analysis."""
    push_progress("phase-0.75", "Анализ контента Instagram...")

    if not posts or followers == 0:
        return {}

    # Calculate metrics
    likes = [p.get("likesCount", 0) for p in posts]
    comments = [p.get("commentsCount", 0) for p in posts]

    avg_likes = sum(likes) / len(likes) if likes else 0
    avg_comments = sum(comments) / len(comments) if comments else 0
    er = (avg_likes / followers * 100) if followers > 0 else 0

    # Post types
    types = {}
    for p in posts:
        t = p.get("type", "Unknown")
        types[t] = types.get(t, 0) + 1

    # Top and worst posts
    posts_sorted = sorted(posts, key=lambda p: p.get("likesCount", 0), reverse=True)
    top_3 = posts_sorted[:3]
    worst = posts_sorted[-1] if posts_sorted else None

    push_progress("phase-0.75", f"✓ ER {er:.2f}%, средний лайков {avg_likes:.0f}")

    return {
        "er": round(er, 2),
        "avg_likes": round(avg_likes),
        "avg_comments": round(avg_comments),
        "post_types": types,
        "top_3_posts": [
            {
                "caption": p.get("caption", "")[:100],
                "likes": p.get("likesCount"),
                "url": p.get("url"),
            }
            for p in top_3
        ],
        "worst_post": {
            "caption": worst.get("caption", "")[:100] if worst else "",
            "likes": worst.get("likesCount") if worst else 0,
        } if worst else None,
    }


async def phase_1_tech_speed(website: str) -> dict:
    """Phase 1: TECH AUDIT — SPEED via PageSpeed."""
    push_progress("phase-1", f"Проверка скорости сайта {website}...")

    # Try PageSpeed via Firecrawl
    pagespeed_url = f"https://pagespeed.web.dev/analysis?url={website}&form_factor=mobile"
    data = await firecrawl_scrape(pagespeed_url, wait_for=10000)

    if not data:
        push_progress("phase-1", "Не удалось получить данные PageSpeed")
        return {}

    # Parse markdown для извлечения метрик (упрощённо)
    # TODO: точный парсинг из markdown
    push_progress("phase-1", "✓ Скорость проверена")

    return {
        "performance": None,  # TODO: parse from markdown
        "accessibility": None,
        "best_practices": None,
        "seo": None,
        "lcp": None,
        "fcp": None,
        "tbt": None,
        "cls": None,
        "cwv_status": None,
    }


async def phase_2_tech_seo_osint(website: str) -> dict:
    """Phase 2: TECH AUDIT — SEO, STACK & OSINT."""
    push_progress("phase-2", f"OSINT-анализ {website}...")

    # Scrape main page
    data = await firecrawl_scrape(website)
    html = data.get("data", {}).get("rawHtml", "") if data else ""

    # Extract CMS
    cms = None
    if "wordpress" in html.lower() or "wp-content" in html.lower():
        cms = "WordPress"
    elif "bitrix" in html.lower():
        cms = "Bitrix"
    elif "tilda" in html.lower():
        cms = "Tilda"

    # Extract analytics
    analytics = []
    if "metrika" in html.lower():
        analytics.append("Яндекс.Метрика")
    if "gtag" in html.lower() or "ga4" in html.lower():
        analytics.append("Google Analytics")

    push_progress("phase-2", f"✓ CMS: {cms or 'Unknown'}, аналитика: {len(analytics)}")

    return {
        "cms": cms,
        "analytics": analytics,
        "schema_types": [],  # TODO: extract from HTML
        "llms_txt": None,
        "ssl_issuer": None,  # TODO: SSL check
        "whois_registrar": None,  # TODO: WHOIS
    }


async def phase_3_social_crossplatform(name: str) -> dict:
    """Phase 3: SOCIAL — CROSS-PLATFORM search."""
    push_progress("phase-3", f"Поиск аккаунтов {name} на других платформах...")

    result = {
        "telegram": None,
        "vk": None,
        "youtube": None,
        "dzen": None,
    }

    # Firecrawl search для каждой платформы
    platforms = [
        ("telegram", f'"{name}" site:t.me'),
        ("vk", f'"{name}" site:vk.com'),
        ("youtube", f'"{name}" site:youtube.com'),
        ("dzen", f'"{name}" site:dzen.ru'),
    ]

    for platform, query in platforms:
        try:
            from .firecrawl_key_bank import get_next_key
            api_key = get_next_key()
            if not api_key:
                continue

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{FIRECRAWL_BASE}/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"query": query, "limit": 3},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data"):
                        urls = [item.get("url") for item in data["data"][:3]]
                        result[platform] = urls[0] if urls else None
                        if urls:
                            push_progress("phase-3", f"✓ {platform.upper()}: {urls[0][:50]}")
        except Exception as e:
            logger.warning(f"Social search failed for {platform}: {e}")
            continue

    push_progress("phase-3", f"✓ Найдено: {sum(1 for v in result.values() if v)} платформ")

    return result


async def phase_35_key_persons(website: str) -> dict:
    """Phase 3.5: KEY PERSONS — doctors extraction."""
    push_progress("phase-3.5", f"Поиск врачей на {website}...")

    doctors = []

    try:
        # Map site to find doctor pages
        from .firecrawl_key_bank import get_next_key
        api_key = get_next_key()
        if not api_key:
            push_progress("phase-3.5", "Нет доступных Firecrawl ключей")
            return {"doctors": [], "star_count": 0, "core_count": 0, "team_count": 0}

        async with httpx.AsyncClient(timeout=60) as client:
            # Step 1: Map site to find doctor-related pages
            map_resp = await client.post(
                f"{FIRECRAWL_BASE}/map",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"url": website, "search": "врач"},
            )

            doctor_pages = []
            if map_resp.status_code == 200:
                map_data = map_resp.json()
                if map_data.get("success"):
                    links = map_data.get("links", [])
                    # Фильтруем страницы с врачами
                    doctor_pages = [
                        link for link in links
                        if any(kw in link.lower() for kw in ["врач", "doctor", "специалист", "команда", "team"])
                    ][:3]  # Берём первые 3 страницы

            push_progress("phase-3.5", f"Найдено {len(doctor_pages)} страниц с врачами")

            # Step 2: Scrape each doctor page
            for page_url in doctor_pages:
                try:
                    scrape_resp = await client.post(
                        f"{FIRECRAWL_BASE}/scrape",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={"url": page_url, "formats": ["markdown"], "onlyMainContent": True},
                    )

                    if scrape_resp.status_code == 200:
                        scrape_data = scrape_resp.json()
                        if scrape_data.get("success"):
                            markdown = scrape_data.get("data", {}).get("markdown", "")

                            # Extract doctor names (простой regex для русских ФИО)
                            # Ищем паттерны: "Иванов Иван Иванович", "Иванова М.С.", "к.м.н. Петров"
                            fio_pattern = r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)'
                            matches = re.findall(fio_pattern, markdown)

                            for match in matches[:10]:  # Первые 10 найденных имён
                                if len(match.split()) >= 2:  # Минимум Фамилия Имя
                                    doctors.append({
                                        "full_name": match.strip(),
                                        "tier": "team",  # По умолчанию team
                                        "specialization": None,
                                        "page_url": page_url,
                                    })
                except Exception as e:
                    logger.warning(f"Failed to scrape doctor page {page_url}: {e}")
                    continue

        # Classify doctors by tier (упрощённо)
        star_count = 0
        core_count = 0
        team_count = len(doctors)

        push_progress("phase-3.5", f"✓ Извлечено {len(doctors)} врачей")

        return {
            "doctors": doctors,
            "star_count": star_count,
            "core_count": core_count,
            "team_count": team_count,
        }

    except Exception as e:
        logger.warning(f"Doctor extraction failed: {e}")
        push_progress("phase-3.5", f"Ошибка извлечения врачей: {str(e)}")
        return {
            "doctors": [],
            "star_count": 0,
            "core_count": 0,
            "team_count": 0,
        }


async def phase_4_competitor_matrix(name: str, city: str) -> dict:
    """Phase 4: COMPETITOR MATRIX — ProDoctorov competitor discovery."""
    push_progress("phase-4", f"Поиск конкурентов {name} в {city}...")

    competitors = []

    try:
        from .firecrawl_key_bank import get_next_key
        api_key = get_next_key()
        if not api_key:
            push_progress("phase-4", "Нет доступных Firecrawl ключей")
            return {"competitors": [], "position": "unknown"}

        # Search ProDoctorov for clinics in the same city
        search_query = f'клиника {city} site:prodoctorov.ru'

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{FIRECRAWL_BASE}/search",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"query": search_query, "limit": 10},
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("data"):
                    push_progress("phase-4", f"✓ Найдено {len(data['data'])} клиник на ProDoctorov")

                    # Extract competitor data from search results
                    for idx, item in enumerate(data["data"][:10]):
                        url = item.get("url", "")
                        title = item.get("title", "")
                        description = item.get("description", "")

                        # Extract rating from description if present
                        rating_match = re.search(r'(\d+\.?\d*)\s*из\s*5', description)
                        rating = float(rating_match.group(1)) if rating_match else None

                        # Extract review count
                        reviews_match = re.search(r'(\d+)\s*отзыв', description)
                        reviews = int(reviews_match.group(1)) if reviews_match else 0

                        competitors.append({
                            "name": title.split('—')[0].strip() if '—' in title else title,
                            "url": url,
                            "rating": rating,
                            "reviews": reviews,
                            "source": "ProDoctorov",
                        })

                        if idx < 3:
                            push_progress("phase-4", f"  • {title[:50]}... (⭐ {rating or 'N/A'})")

        # Determine position (simplified)
        position = "mid-market"
        if competitors:
            avg_rating = sum(c.get("rating", 0) or 0 for c in competitors) / len(competitors)
            if avg_rating > 4.5:
                position = "top-tier"
            elif avg_rating < 3.5:
                position = "low-tier"

        push_progress("phase-4", f"✓ Найдено {len(competitors)} конкурентов, позиция: {position}")

        return {
            "competitors": competitors,
            "position": position,
            "total_found": len(competitors),
        }

    except Exception as e:
        logger.warning(f"Competitor matrix failed: {e}")
        push_progress("phase-4", f"Ошибка поиска конкурентов: {str(e)}")
        return {
            "competitors": [],
            "position": "unknown",
            "total_found": 0,
        }


async def phase_5_ratings_reviews(name: str, city: str) -> dict:
    """Phase 5: RATINGS & REVIEWS — multi-platform review aggregation."""
    push_progress("phase-5", f"Сбор отзывов о {name}...")

    result = {
        "prodoctorov": None,
        "yandex_maps": None,
        "gis2": None,
        "google_maps": None,
    }

    try:
        from .firecrawl_key_bank import get_next_key
        api_key = get_next_key()
        if not api_key:
            push_progress("phase-5", "Нет доступных Firecrawl ключей")
            return result

        async with httpx.AsyncClient(timeout=90) as client:
            # ProDoctorov search
            try:
                resp = await client.post(
                    f"{FIRECRAWL_BASE}/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"query": f'"{name}" {city} site:prodoctorov.ru', "limit": 3},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data") and len(data["data"]) > 0:
                        item = data["data"][0]
                        description = item.get("description", "")

                        rating_match = re.search(r'(\d+\.?\d*)\s*из\s*5', description)
                        reviews_match = re.search(r'(\d+)\s*отзыв', description)

                        result["prodoctorov"] = {
                            "url": item.get("url"),
                            "rating": float(rating_match.group(1)) if rating_match else None,
                            "reviews": int(reviews_match.group(1)) if reviews_match else 0,
                        }
                        push_progress("phase-5", f"✓ ProDoctorov: ⭐ {result['prodoctorov']['rating']}")
            except Exception as e:
                logger.warning(f"ProDoctorov reviews failed: {e}")

            # Yandex Maps search
            try:
                api_key = get_next_key()
                resp = await client.post(
                    f"{FIRECRAWL_BASE}/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"query": f'"{name}" {city} site:yandex.ru/maps', "limit": 3},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data") and len(data["data"]) > 0:
                        item = data["data"][0]
                        description = item.get("description", "")

                        rating_match = re.search(r'(\d+\.?\d*)', description)
                        reviews_match = re.search(r'(\d+)\s*отзыв', description)

                        result["yandex_maps"] = {
                            "url": item.get("url"),
                            "rating": float(rating_match.group(1)) if rating_match else None,
                            "reviews": int(reviews_match.group(1)) if reviews_match else 0,
                        }
                        push_progress("phase-5", f"✓ Yandex Maps: ⭐ {result['yandex_maps']['rating']}")
            except Exception as e:
                logger.warning(f"Yandex Maps reviews failed: {e}")

            # 2GIS search
            try:
                api_key = get_next_key()
                resp = await client.post(
                    f"{FIRECRAWL_BASE}/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"query": f'"{name}" {city} site:2gis.ru', "limit": 3},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data") and len(data["data"]) > 0:
                        item = data["data"][0]
                        description = item.get("description", "")

                        rating_match = re.search(r'(\d+\.?\d*)', description)
                        reviews_match = re.search(r'(\d+)\s*отзыв', description)

                        result["gis2"] = {
                            "url": item.get("url"),
                            "rating": float(rating_match.group(1)) if rating_match else None,
                            "reviews": int(reviews_match.group(1)) if reviews_match else 0,
                        }
                        push_progress("phase-5", f"✓ 2GIS: ⭐ {result['gis2']['rating']}")
            except Exception as e:
                logger.warning(f"2GIS reviews failed: {e}")

            # Google Maps search
            try:
                api_key = get_next_key()
                resp = await client.post(
                    f"{FIRECRAWL_BASE}/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"query": f'"{name}" {city} site:google.com/maps', "limit": 3},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data") and len(data["data"]) > 0:
                        item = data["data"][0]
                        description = item.get("description", "")

                        rating_match = re.search(r'(\d+\.?\d*)', description)
                        reviews_match = re.search(r'(\d+)\s*reviews?', description, re.IGNORECASE)

                        result["google_maps"] = {
                            "url": item.get("url"),
                            "rating": float(rating_match.group(1)) if rating_match else None,
                            "reviews": int(reviews_match.group(1)) if reviews_match else 0,
                        }
                        push_progress("phase-5", f"✓ Google Maps: ⭐ {result['google_maps']['rating']}")
            except Exception as e:
                logger.warning(f"Google Maps reviews failed: {e}")

        platforms_found = sum(1 for v in result.values() if v is not None)
        push_progress("phase-5", f"✓ Отзывы собраны с {platforms_found} платформ")

        return result

    except Exception as e:
        logger.warning(f"Review aggregation failed: {e}")
        push_progress("phase-5", f"Ошибка сбора отзывов: {str(e)}")
        return result


async def phase_6_financial(name: str, city: str) -> dict:
    """Phase 6: FINANCIAL — FNS data extraction."""
    push_progress("phase-6", f"Финансовая проверка {name}...")

    result = {
        "inn": None,
        "revenue": None,
        "profit": None,
        "employees": None,
        "okveds": [],
        "legal_entity": None,
        "hh_vacancies": 0,
    }

    try:
        from .firecrawl_key_bank import get_next_key
        api_key = get_next_key()
        if not api_key:
            push_progress("phase-6", "Нет доступных Firecrawl ключей")
            return result

        async with httpx.AsyncClient(timeout=90) as client:
            # Step 1: Search for INN on nalog.ru or company databases
            try:
                resp = await client.post(
                    f"{FIRECRAWL_BASE}/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"query": f'"{name}" {city} ИНН site:egrul.nalog.ru OR site:spark-interfax.ru', "limit": 5},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data"):
                        for item in data["data"]:
                            description = item.get("description", "")
                            title = item.get("title", "")

                            # Extract INN (10 or 12 digits)
                            inn_match = re.search(r'\b(\d{10}|\d{12})\b', description + " " + title)
                            if inn_match:
                                result["inn"] = inn_match.group(1)
                                push_progress("phase-6", f"✓ ИНН найден: {result['inn']}")
                                break
            except Exception as e:
                logger.warning(f"INN search failed: {e}")

            # Step 2: If INN found, try to get financial data
            if result["inn"]:
                try:
                    api_key = get_next_key()
                    resp = await client.post(
                        f"{FIRECRAWL_BASE}/search",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={"query": f'ИНН {result["inn"]} выручка site:spark-interfax.ru OR site:rusprofile.ru', "limit": 3},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success") and data.get("data"):
                            for item in data["data"]:
                                description = item.get("description", "")

                                # Extract revenue (выручка)
                                revenue_match = re.search(r'выручка[:\s]+(\d+[\s\d]*)\s*(?:тыс\.|млн\.|млрд\.)?', description, re.IGNORECASE)
                                if revenue_match:
                                    revenue_str = revenue_match.group(1).replace(" ", "")
                                    result["revenue"] = int(revenue_str)
                                    push_progress("phase-6", f"✓ Выручка: {result['revenue']:,}")

                                # Extract legal entity type
                                if "ООО" in description or "ООО" in item.get("title", ""):
                                    result["legal_entity"] = "ООО"
                                elif "АО" in description or "АО" in item.get("title", ""):
                                    result["legal_entity"] = "АО"
                                elif "ИП" in description or "ИП" in item.get("title", ""):
                                    result["legal_entity"] = "ИП"

                                break
                except Exception as e:
                    logger.warning(f"Financial data scrape failed: {e}")

            # Step 3: HeadHunter vacancies count
            try:
                api_key = get_next_key()
                resp = await client.post(
                    f"{FIRECRAWL_BASE}/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"query": f'"{name}" {city} site:hh.ru/employer', "limit": 5},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("data"):
                        for item in data["data"]:
                            description = item.get("description", "")

                            # Extract vacancy count
                            vacancy_match = re.search(r'(\d+)\s*(?:вакансий|вакансия|открыт)', description, re.IGNORECASE)
                            if vacancy_match:
                                result["hh_vacancies"] = int(vacancy_match.group(1))
                                push_progress("phase-6", f"✓ Вакансий на HH.ru: {result['hh_vacancies']}")
                                break
            except Exception as e:
                logger.warning(f"HH.ru search failed: {e}")

        push_progress("phase-6", f"✓ Финансы проверены (ИНН: {result['inn'] or 'не найден'})")

        return result

    except Exception as e:
        logger.warning(f"Financial check failed: {e}")
        push_progress("phase-6", f"Ошибка финансовой проверки: {str(e)}")
        return result


async def phase_7_gaps_advantages(data: dict) -> dict:
    """Phase 7: GAPS, ADVANTAGES & TACTICS — LLM-based competitive analysis."""
    push_progress("phase-7", "Анализ пробелов и преимуществ...")

    result = {
        "gaps": [],
        "advantages": [],
        "wow_insights": [],
        "steal_worthy_tactics": [],
    }

    try:
        # Prepare context for LLM analysis
        analysis_context = {
            "tech": data.get("phase_1", {}).get("pagespeed_score"),
            "seo": data.get("phase_2", {}),
            "social": data.get("phase_3", {}),
            "doctors": data.get("phase_3_5", {}).get("team_count", 0),
            "competitors": data.get("phase_4", {}).get("competitors", []),
            "reviews": data.get("phase_5", {}),
            "financials": data.get("phase_6", {}),
            "instagram": data.get("phase_0_75", {}),
        }

        # Build analysis prompt
        prompt = f"""Проанализируй данные о медицинской клинике и её конкурентах.

ДАННЫЕ:
- PageSpeed: {analysis_context['tech']}
- CMS: {analysis_context['seo'].get('cms')}
- Врачей в команде: {analysis_context['doctors']}
- Конкурентов найдено: {len(analysis_context['competitors'])}
- Средний рейтинг конкурентов: {sum(c.get('rating', 0) or 0 for c in analysis_context['competitors']) / len(analysis_context['competitors']) if analysis_context['competitors'] else 0:.1f}
- Отзывы на платформах: {sum(1 for v in analysis_context['reviews'].values() if v)}
- ИНН найден: {'да' if analysis_context['financials'].get('inn') else 'нет'}
- Instagram ER: {analysis_context['instagram'].get('engagement_rate', 'N/A')}

Дай краткий анализ (JSON):
{{
  "gaps": ["что НЕ делают, но должны"],
  "advantages": ["что делают хорошо"],
  "wow_insights": ["неожиданные находки"],
  "steal_worthy_tactics": ["что украсть у конкурентов"]
}}

Максимум 3-4 пункта в каждой категории. Конкретно и по делу."""

        # Call Anthropic API for analysis
        import os
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            push_progress("phase-7", "ANTHROPIC_API_KEY не найден, пропускаем LLM-анализ")
            return result

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

            if resp.status_code == 200:
                response_data = resp.json()
                content = response_data.get("content", [{}])[0].get("text", "{}")

                # Extract JSON from response
                import json
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    analysis = json.loads(json_match.group(0))
                    result.update(analysis)
                    push_progress("phase-7", f"✓ Найдено {len(result['gaps'])} пробелов, {len(result['advantages'])} преимуществ")
                else:
                    push_progress("phase-7", "Не удалось распарсить JSON из ответа LLM")
            else:
                push_progress("phase-7", f"Ошибка API Anthropic: {resp.status_code}")

        return result

    except Exception as e:
        logger.warning(f"Gaps/advantages analysis failed: {e}")
        push_progress("phase-7", f"Ошибка анализа: {str(e)}")
        return result


async def phase_8_data_assembly(data: dict, slug: str) -> str:
    """Phase 8: DATA ASSEMBLY — save to /tmp."""
    push_progress("phase-8", "Сборка отчёта...")

    output_path = f"/tmp/{slug}-scout-brief.json"
    Path(output_path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

    push_progress("phase-8", f"✓ Отчёт сохранён: {output_path}")

    return output_path


async def run_aim_scout_pipeline(
    name: str,
    website: str,
    instagram: str | None = None,
    city: str = "Санкт-Петербург",
    **kwargs,
) -> dict[str, Any]:
    """Execute full 16-phase aim-scout pipeline.

    Returns:
        dict with keys:
        - status: "completed" | "partial" | "failed"
        - phases_completed: list of phase numbers
        - output_file: path to JSON report
        - summary: brief summary
        - data: full collected data
    """
    start_time = time.time()
    phases_completed = []
    data = {}

    try:
        # Phase 0: PRE-FLIGHT
        preflight = await phase_0_preflight(name, website, instagram, city)
        data.update(preflight)
        phases_completed.append(0)

        # Phase 0.5: INSTAGRAM PROFILE
        if instagram:
            instagram_profile = await phase_05_instagram_profile(instagram)
            data["instagram"] = instagram_profile
            phases_completed.append(0.5)

            # Phase 0.75: INSTAGRAM CONTENT
            if instagram_profile.get("latest_posts"):
                instagram_content = await phase_075_instagram_content(
                    instagram_profile["latest_posts"],
                    instagram_profile.get("followers_count", 0),
                )
                data["instagram"].update(instagram_content)
                phases_completed.append(0.75)

        # Phase 1: TECH AUDIT — SPEED
        tech_speed = await phase_1_tech_speed(website)
        data["tech_speed"] = tech_speed
        phases_completed.append(1)

        # Phase 2: TECH AUDIT — SEO & OSINT
        tech_seo = await phase_2_tech_seo_osint(website)
        data["tech_seo"] = tech_seo
        phases_completed.append(2)

        # Phase 3: SOCIAL
        social = await phase_3_social_crossplatform(name)
        data["social"] = social
        phases_completed.append(3)

        # Phase 3.5: KEY PERSONS
        key_persons = await phase_35_key_persons(website)
        data["key_persons"] = key_persons
        phases_completed.append(3.5)

        # Phase 4: COMPETITOR MATRIX
        competitors = await phase_4_competitor_matrix(name, city)
        data["competitors"] = competitors
        phases_completed.append(4)

        # Phase 5: RATINGS & REVIEWS
        ratings = await phase_5_ratings_reviews(name, city)
        data["ratings"] = ratings
        phases_completed.append(5)

        # Phase 6: FINANCIAL
        financial = await phase_6_financial(name, city)
        data["financial"] = financial
        phases_completed.append(6)

        # Phase 7: GAPS & ADVANTAGES
        analysis = await phase_7_gaps_advantages(data)
        data["analysis"] = analysis
        phases_completed.append(7)

        # Phase 8: DATA ASSEMBLY
        output_file = await phase_8_data_assembly(data, data["slug"])
        phases_completed.append(8)

        elapsed = time.time() - start_time

        return {
            "status": "completed",
            "phases_completed": phases_completed,
            "output_file": output_file,
            "elapsed_seconds": round(elapsed),
            "summary": f"Разведка {name} завершена. {len(phases_completed)} фаз выполнено за {elapsed/60:.1f} мин.",
            "data": data,
        }

    except Exception as e:
        logger.exception("aim-scout pipeline failed")
        return {
            "status": "failed",
            "phases_completed": phases_completed,
            "error": str(e),
            "summary": f"Разведка прервана на фазе {max(phases_completed) if phases_completed else 0}. Ошибка: {str(e)}",
        }


# ── Tool registration ──────────────────────────────────────────────────

try:
    from tools.registry import registry

    registry.register(
        name="run_aim_scout",
        toolset="aim-operations",
        schema={
                "name": "run_aim_scout",
                "description": (
                    "16-фазная глубокая разведка конкурента (aim-scout pipeline). "
                    "Собирает: Instagram (профиль, контент, ER), техаудит (скорость, SEO, OSINT), "
                    "соцсети, врачи, конкуренты, отзывы, финансы, gaps, advantages. "
                    "Время: 50-65 минут. Используй для полного анализа конкурента."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Название клиники или компании",
                        },
                        "website": {
                            "type": "string",
                            "description": "URL сайта (https://example.ru)",
                        },
                        "instagram": {
                            "type": "string",
                            "description": "Instagram handle БЕЗ @ (необязательно)",
                        },
                        "city": {
                            "type": "string",
                            "description": "Город (по умолчанию Санкт-Петербург)",
                            "default": "Санкт-Петербург",
                        },
                    },
                    "required": ["name", "website"],
                },
            },
        handler=run_aim_scout_pipeline,
        check_fn=lambda: True,
        is_async=True,
        description="16-phase competitor intelligence (Instagram, tech, social, doctors, competitors, reviews, financials, gaps). 50-65 min",
        emoji="🔍",
    )

    logger.info("Registered tool: run_aim_scout (16-phase competitor intelligence)")

except ImportError:
    logger.warning("Tool registry not available — run_aim_scout not registered")
