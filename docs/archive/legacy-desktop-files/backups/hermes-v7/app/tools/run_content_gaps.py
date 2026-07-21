"""
run_content_gaps — Hermes tool: Content Gap Analysis (Competitor vs Client)

Fetches sitemaps from both competitor and client websites, extracts page URLs
and content themes. The LLM then analyses the data to identify:
- Topics the competitor covers that the client doesn't (critical gaps)
- Content depth comparison (long-form vs short pages)
- Quick wins (topics that can be covered in 1-2 days)

Uses Firecrawl to scrape sitemaps and key pages.
Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from .firecrawl_key_bank import get_key_with_fallback, mark_exhausted, classify_exhaustion
from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 120.0
FIRECRAWL_SCRAPE = "https://api.firecrawl.dev/v2/scrape"
FIRECRAWL_MAP = "https://api.firecrawl.dev/v2/map"
_MAX_RETRIES = 3


async def handle_run_content_gaps(competitor_site=None, client_site=None, **kwargs) -> str:
    """Analyse content gaps between a competitor and our client.

    Fetches sitemaps from both websites, extracts page URLs, and
    identifies topic areas each site covers. The LLM uses this data
    to pinpoint content gaps.

    Args:
        competitor_site: Competitor website URL (e.g., "https://competitor.ru")
        client_site: Our client's website URL (e.g., "https://client.ru")

    Returns:
        JSON with both sites' page inventories and identified gap topics.
    """
    if isinstance(competitor_site, dict):
        d = competitor_site
        competitor_site = d.get("competitor_site", "")
        if client_site is None:
            client_site = d.get("client_site", "")

    # Fallback: if LLM forgot the URL, try the cache from run_prescan
    if not competitor_site:
        try:
            cached = Path("/tmp/hermes_last_url.txt").read_text().strip()
            if cached:
                logger.info("Using cached URL from prescan: %s", cached)
                competitor_site = cached
        except Exception:
            pass

    if not competitor_site:
        return json.dumps({"error": "competitor_site is required"})

    if not competitor_site.startswith(("http://", "https://")):
        competitor_site = "https://" + competitor_site
    if client_site and not client_site.startswith(("http://", "https://")):
        client_site = "https://" + client_site

    logger.info("Content gap analysis: competitor=%s, client=%s", competitor_site, client_site)

    from app.main import push_tool_progress

    push_tool_progress("content-gaps", f"Сканирую структуру сайтов и ищу контентные разрывы…")

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Fetch sitemaps from both sites
            comp_pages, client_pages = [], []

            push_tool_progress("content-gaps", f"Извлекаю sitemap конкурента: {competitor_site}")
            comp_pages = await _get_site_pages(client, competitor_site)

            if client_site:
                push_tool_progress("content-gaps", f"Извлекаю sitemap клиента: {client_site}")
                client_pages = await _get_site_pages(client, client_site)
            else:
                push_tool_progress(
                    "content-gaps",
                    "Сайт клиента не указан — покажу только структуру конкурента",
                )

        comp_themes = _extract_themes(comp_pages, competitor_site)
        client_themes = _extract_themes(client_pages, client_site) if client_site else {}

        push_tool_progress(
            "content-gaps",
            f"✅ Конкурент: {len(comp_pages)} стр., {len(comp_themes)} тем"
            + (f" | Клиент: {len(client_pages)} стр., {len(client_themes)} тем" if client_site else ""),
        )

        result = {
            "competitor": {
                "site": competitor_site,
                "total_pages": len(comp_pages),
                "themes": comp_themes,
                "top_pages": comp_pages[:30],
            },
        }

        if client_site:
            result["client"] = {
                "site": client_site,
                "total_pages": len(client_pages),
                "themes": client_themes,
                "top_pages": client_pages[:30],
            }
            # Compute gap hints
            gaps = []
            for theme, urls in comp_themes.items():
                if theme not in client_themes:
                    gaps.append({
                        "theme": theme,
                        "competitor_pages": len(urls),
                        "client_pages": 0,
                        "severity": "critical" if len(urls) >= 3 else "high",
                        "suggestion": f"Создать контент по теме «{theme}» — конкурент имеет {len(urls)} стр.",
                    })
                elif len(urls) > len(client_themes.get(theme, [])):
                    gaps.append({
                        "theme": theme,
                        "competitor_pages": len(urls),
                        "client_pages": len(client_themes.get(theme, [])),
                        "severity": "partial",
                        "suggestion": f"Углубить контент по теме «{theme}»: {len(urls)} vs {len(client_themes.get(theme, []))} стр.",
                    })
            result["gaps"] = gaps[:15]
            result["total_gaps"] = len(gaps)

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("Content gap analysis failed")
        return json.dumps({"error": "Content gap analysis failed", "detail": str(e)})


async def _get_site_pages(
    client: httpx.AsyncClient, site: str
) -> list[dict]:
    """Fetch page inventory from a website via Firecrawl map + sitemap with key rotation."""
    pages = []
    domain = urlparse(site).netloc

    # Try sitemap first
    for sitemap_path in ["/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml", "/sitemap"]:
        sitemap_url = urljoin(site, sitemap_path)
        try:
            response = await client.get(sitemap_url, timeout=15.0)
            if response.status_code == 200:
                text = response.text
                urls = re.findall(r'<loc>([^<]+)</loc>', text)
                for u in urls:
                    path = urlparse(u).path or "/"
                    pages.append({
                        "url": u,
                        "path": path,
                        "depth": path.strip("/").count("/"),
                    })
                if pages:
                    logger.info("Found %d pages in sitemap %s", len(pages), sitemap_path)
                    break
        except Exception:
            continue

    # Fallback to Firecrawl map
    if not pages:
        for attempt in range(_MAX_RETRIES):
            try:
                key = get_key_with_fallback()
            except RuntimeError:
                logger.warning("No Firecrawl keys for map: %s", site)
                break

            try:
                response = await client.post(
                    FIRECRAWL_MAP,
                    headers={"Authorization": f"Bearer {key}"},
                    json={"url": site, "limit": 100},
                )
                if response.status_code == 402:
                    reason = classify_exhaustion(response.text)
                    if reason:
                        mark_exhausted(key, reason)
                        logger.warning("Firecrawl 402 on content map, rotating key (attempt %d)", attempt + 1)
                        continue

                response.raise_for_status()
                data = response.json()
                urls = data.get("data", []) if isinstance(data.get("data"), list) else []
                for u in urls[:100]:
                    path = urlparse(u).path or "/"
                    pages.append({
                        "url": u,
                        "path": path,
                        "depth": path.strip("/").count("/"),
                    })
                break  # success
            except httpx.HTTPStatusError as e:
                reason = classify_exhaustion(str(e))
                if reason:
                    mark_exhausted(key, reason)
                    continue
                logger.warning("Firecrawl map failed for %s: %s", site, e)
                break
            except Exception as e:
                logger.warning("Firecrawl map failed for %s: %s", site, e)
                break

    return pages


def _extract_themes(pages: list[dict], site: str) -> dict[str, list[str]]:
    """Extract content themes from page URLs.

    Groups pages by topic based on URL path segments.
    Medical-specific categorisation for clinic websites.
    """
    themes: dict[str, list[str]] = {}

    # Known medical clinic content categories
    category_map = {
        "услуги": "Услуги и процедуры",
        "services": "Услуги и процедуры",
        "service": "Услуги и процедуры",
        "цены": "Цены и прайс-лист",
        "price": "Цены и прайс-лист",
        "прайс": "Цены и прайс-лист",
        "cost": "Цены и прайс-лист",
        "врачи": "Врачи и специалисты",
        "doctors": "Врачи и специалисты",
        "специалисты": "Врачи и специалисты",
        "specialists": "Врачи и специалисты",
        "staff": "Врачи и специалисты",
        "отзывы": "Отзывы пациентов",
        "reviews": "Отзывы пациентов",
        "отзыв": "Отзывы пациентов",
        "review": "Отзывы пациентов",
        "акции": "Акции и спецпредложения",
        "promo": "Акции и спецпредложения",
        "скидки": "Акции и спецпредложения",
        "sale": "Акции и спецпредложения",
        "о-клинике": "О клинике",
        "about": "О клинике",
        "контакты": "Контакты",
        "contacts": "Контакты",
        "contact": "Контакты",
        "статьи": "Блог и статьи",
        "articles": "Блог и статьи",
        "blog": "Блог и статьи",
        "новости": "Блог и статьи",
        "news": "Блог и статьи",
        "faq": "FAQ / Вопросы-ответы",
        "вопросы": "FAQ / Вопросы-ответы",
        "questions": "FAQ / Вопросы-ответы",
        "лицензии": "Лицензии и документы",
        "license": "Лицензии и документы",
        "вакансии": "Вакансии",
        "vacancy": "Вакансии",
        "jobs": "Вакансии",
        "фото": "Фото / Галерея",
        "gallery": "Фото / Галерея",
        "до-после": "До/После",
        "before-after": "До/После",
    }

    seen_themes: set[str] = set()

    for page in pages:
        path = page["path"].lower().rstrip("/")
        if not path:
            path = "/"

        # Try to categorise by URL segments
        for segment in path.split("/"):
            if not segment or segment == site.replace("https://", "").replace("http://", ""):
                continue
            segment_clean = re.sub(r'[-_]', ' ', segment).strip()
            for keyword, theme in category_map.items():
                if keyword in segment_clean and theme not in seen_themes:
                    if theme not in themes:
                        themes[theme] = []
                    themes[theme].append(page["url"])
                    seen_themes.add(theme)
                    break

        # Uncategorised pages
        if not any(page["url"] in urls for urls in themes.values()):
            if "Прочее" not in themes:
                themes["Прочее"] = []
            themes["Прочее"].append(page["url"])

    return themes


registry.register(
    name="run_content_gaps",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_content_gaps",
            "description": (
                "Compare content coverage between a competitor's website and our client's website. "
                "Fetches sitemaps, categorises pages by topic (services, doctors, prices, reviews, "
                "blog, FAQ, before/after gallery, etc.), and identifies gaps. "
                "Shows: which topics the competitor covers that the client doesn't, "
                "content depth comparison, and severity ratings (critical/high/partial). "
                "Use this to advise the client on what content they need to create "
                "to match or beat the competitor in search visibility."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "competitor_site": {
                        "type": "string",
                        "description": "[REQUIRED] Competitor website URL (e.g., 'https://competitor-clinic.ru')",
                    },
                    "client_site": {
                        "type": "string",
                        "description": "Our client's website URL for comparison (e.g., 'https://client-clinic.ru')",
                    },
                },
                "required": ["competitor_site"],
            },
        },
    },
    handler=handle_run_content_gaps,
    check_fn=lambda: True,
    is_async=True,
    description="Compare competitor vs client website content: find gaps in services, blog, FAQ, and SEO pages",
    emoji="📝",
)
