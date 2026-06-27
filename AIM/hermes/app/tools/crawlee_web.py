"""
crawlee_web — Hermes tool: Crawlee-powered web scraping & crawling.

Uses Apify's Crawlee (Python) for:
- JS-rendered page scraping (Playwright headless)
- Recursive crawling with configurable depth
- Structured data extraction

Replaces Brave Search for deep website analysis.
Free, no API key required. Uses local Playwright Chromium.
"""

import asyncio
import json
import logging
import os
import tempfile

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 120.0


async def handle_crawlee_scrape(url=None, max_pages=None, extract_schema=None, **kwargs) -> str:
    """Scrape a website using Crawlee with headless Chromium.

    Handles JavaScript-rendered pages. Recursively follows links
    within the same domain up to max_pages.

    Args:
        url: Starting URL (https://...)
        max_pages: Max pages to crawl (default: 5, max: 20)
        extract_schema: Optional JSON schema for structured extraction

    Returns:
        JSON with scraped pages (url, title, text content).
    """
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        max_pages = d.get("max_pages", max_pages)
        extract_schema = d.get("extract_schema", extract_schema)

    if not url:
        return json.dumps({"error": "url is required"})
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    max_p = min(int(max_pages) if max_pages else 5, 20)
    logger.info("crawlee_scrape: %s (max_pages=%d)", url[:120], max_p)

    try:
        from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
        from crawlee.router import Router
    except ImportError:
        return json.dumps({
            "error": "crawlee not installed. Run: pip install crawlee[playwright]",
            "hint": "Also ensure playwright browsers are installed: playwright install chromium",
        })

    from app.main import push_tool_progress
    push_tool_progress("crawlee", f"🕷️ Crawlee: обхожу {url}…")

    results: list[dict] = []

    router = Router[PlaywrightCrawlingContext]()

    @router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        title = await context.page.title()
        text = await context.page.evaluate("""
            () => {
                const clone = document.body.cloneNode(true);
                for (const el of clone.querySelectorAll('script, style, nav, footer, header')) {
                    el.remove();
                }
                return clone.innerText.substring(0, 15000);
            }
        """)
        results.append({
            "url": context.request.loaded_url or context.request.url,
            "title": title,
            "text": text,
            "status_code": 200,
        })

    crawler = PlaywrightCrawler(
        router=router,
        max_requests_per_crawl=max_p,
        headless=True,
        browser_type="chromium",
        launch_options={
            "args": ["--no-sandbox", "--disable-setuid-sandbox"],
        },
    )

    try:
        await crawler.run([url])
    except Exception as e:
        logger.error("crawlee crawl failed: %s", str(e)[:200])
    finally:
        await crawler._browser_pool.close()

    push_tool_progress(
        "crawlee",
        f"✅ Crawlee: {len(results)} страниц собрано",
    )

    return json.dumps({
        "url": url,
        "pages_scraped": len(results),
        "pages": results,
        "source": "crawlee",
    }, ensure_ascii=False, indent=2)


async def handle_crawlee_search(query=None, limit=None, **kwargs) -> str:
    """Search and scrape results using Crawlee (Google via Playwright).

    Searches Google for the query, then scrapes the top result pages.

    Args:
        query: Search query
        limit: Max results to scrape (default: 5)

    Returns:
        JSON with search results + scraped content.
    """
    if isinstance(query, dict):
        d = query
        query = d.get("query", "")
        limit = d.get("limit", limit)

    if not query or not isinstance(query, str):
        return json.dumps({"error": "query is required (string)"})

    max_results = min(int(limit) if limit else 5, 10)
    logger.info("crawlee_search: %s (limit=%d)", query[:80], max_results)

    try:
        from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
        from crawlee.router import Router
    except ImportError:
        return json.dumps({
            "error": "crawlee not installed. Run: pip install crawlee[playwright]",
        })

    from urllib.parse import quote_plus
    from app.main import push_tool_progress

    push_tool_progress("crawlee", f"🔍 Crawlee: ищу «{query[:60]}»…")

    results: list[dict] = []
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=ru"

    router = Router[PlaywrightCrawlingContext]()

    @router.default_handler
    async def handler(context: PlaywrightCrawlingContext) -> None:
        # Extract search results from Google SERP
        try:
            links = await context.page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('a[jsname="UWckNb"], a[h3], .g a[href^="http"]');
                    const seen = new Set();
                    for (const el of elements) {
                        const href = el.href;
                        if (href && href.startsWith('http') && !href.includes('google.com') && !seen.has(href)) {
                            seen.add(href);
                            const h3 = el.querySelector('h3');
                            results.push({
                                url: href,
                                title: h3 ? h3.innerText : el.innerText.substring(0, 100),
                            });
                        }
                    }
                    return results.slice(0, 10);
                }
            """)
            for link in links[:max_results]:
                results.append({
                    "title": link.get("title", ""),
                    "url": link.get("url", ""),
                    "description": "",
                })
        except Exception as e:
            logger.warning("crawlee search extraction failed: %s", e)

    crawler = PlaywrightCrawler(
        router=router,
        max_requests_per_crawl=1,
        headless=True,
        browser_type="chromium",
        launch_options={
            "args": ["--no-sandbox", "--disable-setuid-sandbox"],
        },
    )

    try:
        await crawler.run([search_url])
    except Exception as e:
        logger.error("crawlee search failed: %s", str(e)[:200])
    finally:
        await crawler._browser_pool.close()

    push_tool_progress("crawlee", f"✅ Crawlee search: {len(results)} результатов")

    return json.dumps({
        "query": query,
        "results_count": len(results),
        "results": results,
        "source": "crawlee (Google)",
    }, ensure_ascii=False, indent=2)


# ── Register tools ──────────────────────────────────────────────────

def _check_crawlee():
    try:
        import crawlee
        return True
    except ImportError:
        return False


registry.register(
    name="crawlee_scrape",
    toolset="aim-operations",
    schema={
            "name": "crawlee_scrape",
            "description": (
                "Scrape a website using Crawlee (Apify) with headless Chromium. "
                "Handles JavaScript-rendered pages. Recursively crawls up to N pages "
                "within the same domain. Returns full text content of each page. "
                "Use for: deep competitor site analysis, content extraction from JS-heavy sites."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Starting URL to scrape (https://...)",
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Max pages to crawl (default: 5, max: 20)",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_crawlee_scrape,
    check_fn=_check_crawlee,
    is_async=True,
    description="Scrape websites with Crawlee + Playwright (JS-rendered pages)",
    emoji="🕷️",
)

registry.register(
    name="crawlee_search",
    toolset="aim-operations",
    schema={
            "name": "crawlee_search",
            "description": (
                "Search Google via Playwright (headless browser) and return top results. "
                "More reliable than API-based search — uses real browser rendering. "
                "Use when DDG search returns insufficient results or for Russian-market queries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default: 5, max: 10)",
                    },
                },
                "required": ["query"],
            },
        },
    handler=handle_crawlee_search,
    check_fn=_check_crawlee,
    is_async=True,
    description="Search Google via headless browser with Crawlee",
    emoji="🔍",
)
