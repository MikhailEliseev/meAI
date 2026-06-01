"""
bitrix_scraper — Hermes tool: extract content from Bitrix (1C-Bitrix) websites.

Bitrix sites render content dynamically via JavaScript/AJAX. Standard HTTP
scrapers get empty shells. This tool uses Playwright Chromium to render pages,
extract actual text content, and discover site structure via sitemap.xml.

Used by SEO audit as fallback when web_fetch returns empty/sparse content.
"""

import asyncio
import json
import logging
import re
import time
from urllib.parse import urljoin, urlparse

import httpx
from tools.registry import registry

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ── Bitrix detection ──────────────────────────────────────────────────

BITRIX_MARKERS = [
    "/bitrix/templates/",
    "/bitrix/js/",
    "/bitrix/components/",
    "bitrix24",
    "bx-core",
    "BX.message",
    "1C-Bitrix",
    "bx_site_",
    "bitrix_sessid",
    "/bitrix/panel/",
]

CONTENT_SELECTORS = [
    ".bx-content",
    ".workarea",
    ".content",
    "main",
    "article",
    ".catalog-section",
    ".news-list",
    ".news-detail",
    ".catalog-element",
    ".services-list",
    ".service-item",
    ".doctors-list",
    ".doctor-card",
]

KEY_PATHS = [
    "/about/", "/o-klinike/", "/o-kompanii/",
    "/services/", "/uslugi/", "/napravleniya/",
    "/doctors/", "/vrachi/", "/specialisty/",
    "/prices/", "/price/", "/tseny/",
    "/contacts/", "/kontakty/",
    "/reviews/", "/otzyvy/",
    "/news/", "/blog/", "/stati/",
    "/licenses/", "/liczenzii/",
    "/foto/", "/gallery/",
]

BLOCK_SELECTORS = [
    "header", "footer", "nav", ".header", ".footer", ".nav", ".navbar",
    ".menu", ".sidebar", ".banner", ".popup", ".modal", ".cookie",
    ".breadcrumb", ".navigation", ".bx-panel",
]


def _is_bitrix(html: str) -> bool:
    """Detect Bitrix site from HTML source or page content."""
    html_lower = html.lower()
    for marker in BITRIX_MARKERS:
        if marker.lower() in html_lower:
            return True
    return False


def _is_valid_page_url(url: str, base_domain: str) -> bool:
    """Filter out non-page URLs (assets, admin, API)."""
    if not url.startswith(("http://", "https://")):
        return False
    parsed = urlparse(url)
    if parsed.netloc != base_domain and not parsed.netloc.endswith(f".{base_domain}"):
        return False
    skip_extensions = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                       ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
                       ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip",
                       ".ico", ".mp4", ".webm", ".mp3")
    if url.lower().endswith(skip_extensions):
        return False
    skip_prefixes = (
        "mailto:", "tel:", "javascript:", "#", "whatsapp:", "viber:", "tg:",
    )
    if url.startswith(skip_prefixes):
        return False
    skip_paths = ("/bitrix/admin/", "/bitrix/tools/", "/bitrix/php_interface/",
                  "/personal/", "/auth/", "/login/", "/cart/", "/basket/", "/order/")
    for sp in skip_paths:
        if sp in url.lower():
            return False
    return True


async def _fetch_sitemap(url: str) -> list[str]:
    """Try to fetch sitemap.xml and extract page URLs."""
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    sitemap_urls = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/upload/sitemap.xml",
    ]

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for sm_url in sitemap_urls:
            try:
                resp = await client.get(sm_url, headers={"User-Agent": USER_AGENT})
                if resp.status_code != 200:
                    continue

                text = resp.text
                urls = re.findall(r"<loc>(.*?)</loc>", text)
                domain = urlparse(base_url).netloc

                pages = [u for u in urls if _is_valid_page_url(u, domain)]
                if pages:
                    logger.info(
                        "bitrix_scrape: found %d pages in %s", len(pages), sm_url
                    )
                    return pages
            except Exception:
                continue
    return []


async def _render_page(url: str, timeout_ms: int = 30000) -> dict:
    """Render a single page with Playwright and extract content."""
    result = {"url": url, "title": "", "text": "", "links": [], "status": "ok"}

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = await browser.new_page(viewport={"width": 1280, "height": 800})

            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                await page.wait_for_timeout(2000)
            except Exception as goto_err:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    await page.wait_for_timeout(3000)
                except Exception:
                    result["status"] = f"goto_failed: {goto_err}"
                    await browser.close()
                    return result

            result["title"] = await page.title() or ""

            # Remove non-content blocks
            for selector in BLOCK_SELECTORS:
                try:
                    await page.eval_on_selector_all(
                        selector,
                        "els => els.forEach(el => { try { el.remove() } catch(e) {} })",
                    )
                except Exception:
                    pass

            # Try each content selector
            text = ""
            for selector in CONTENT_SELECTORS:
                try:
                    elements = page.locator(selector)
                    count = await elements.count()
                    for i in range(count):
                        try:
                            el_text = await elements.nth(i).inner_text()
                            if el_text and len(el_text.strip()) > 20:
                                text += el_text.strip() + "\n\n"
                        except Exception:
                            continue
                    if text.strip():
                        break
                except Exception:
                    continue

            # Fallback: grab full body text
            if not text.strip():
                try:
                    text = await page.inner_text("body")
                except Exception:
                    text = ""

            # Limit text per page
            if len(text) > 15000:
                text = text[:15000] + "\n\n[truncated]"

            result["text"] = text.strip()

            # Collect internal links
            try:
                hrefs = await page.eval_on_selector_all(
                    "a[href]",
                    "els => els.map(el => el.href).filter(h => h && !h.startsWith('javascript:'))",
                )
                base_domain = urlparse(url).netloc
                result["links"] = [h for h in (hrefs or [])[:50]
                                   if _is_valid_page_url(h, base_domain)]
            except Exception:
                pass

            await browser.close()

    except ImportError:
        result["status"] = "error"
        result["text"] = "playwright not installed — add to Dockerfile"
    except Exception as e:
        result["status"] = f"error: {e}"

    return result


async def _crawl_site(start_url: str, sitemap_urls: list[str], max_pages: int) -> dict:
    """Crawl key pages of a Bitrix site and extract structured content."""
    all_pages = list(sitemap_urls) if sitemap_urls else []
    base = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"

    # Add key paths if not already in sitemap
    for path in KEY_PATHS:
        full_url = urljoin(base, path)
        if full_url not in all_pages:
            all_pages.append(full_url)

    # Also add the homepage
    if base not in all_pages:
        all_pages.insert(0, base)

    # Deduplicate and limit
    seen = set()
    unique_pages = []
    for u in all_pages:
        if u not in seen:
            seen.add(u)
            unique_pages.append(u)

    if max_pages and len(unique_pages) > max_pages:
        unique_pages = unique_pages[:max_pages]

    logger.info("bitrix_scrape: rendering %d pages", len(unique_pages))

    results = []
    for url in unique_pages:
        page_data = await _render_page(url)
        results.append(page_data)

    return {
        "url": start_url,
        "base_domain": urlparse(base).netloc,
        "pages_crawled": len(results),
        "pages_with_content": sum(1 for r in results if len(r.get("text", "")) > 100),
        "pages": results,
    }


async def handle_bitrix_scrape(url=None, max_pages=None, **kwargs) -> str:
    """Scrape a Bitrix website using Playwright to render JavaScript content.

    Use when web_fetch returns empty/sparse content (common with Bitrix sites).
    Renders pages with Chromium, waits for AJAX, extracts actual text.

    Args:
        url: Website URL (https://...)
        max_pages: Max pages to crawl (default: 10)

    Returns:
        JSON with is_bitrix, pages_crawled, pages (each with url, title, text),
        and a combined_text summary of all extracted content.
    """
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        max_pages = d.get("max_pages", max_pages)

    if not url:
        return json.dumps({"error": "url is required"}, ensure_ascii=False)
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must start with http:// or https://"})

    max_pages = max_pages if max_pages else 10

    logger.info("bitrix_scrape: %s (max_pages=%d)", url, max_pages)

    # 1. Quick fetch to detect Bitrix
    is_bitrix = False
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200:
                is_bitrix = _is_bitrix(resp.text)
    except Exception:
        pass

    # 2. Get sitemap
    sitemap_urls = await _fetch_sitemap(url)

    # 3. Crawl with Playwright
    result = await _crawl_site(url, sitemap_urls, max_pages)
    result["is_bitrix"] = is_bitrix

    # 4. Build combined text summary
    combined_parts = []
    for page in result.get("pages", []):
        title = page.get("title", "")
        text = page.get("text", "")
        if text:
            if title:
                combined_parts.append(f"=== {title} ===\n{text}")
            else:
                combined_parts.append(text)

    result["combined_text"] = "\n\n".join(combined_parts)
    result["text_length"] = len(result["combined_text"])

    # Trim to avoid blowing context
    if len(result["combined_text"]) > 8000:
        result["combined_text"] = result["combined_text"][:8000] + "\n\n[truncated]"

    return json.dumps(result, ensure_ascii=False)


# ── Register tool ─────────────────────────────────────────────────────

registry.register(
    name="bitrix_scrape",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "bitrix_scrape",
            "description": (
                "Scrape a Bitrix (1C-Bitrix) website using Playwright Chromium. "
                "Bitrix sites load content via JavaScript/AJAX — standard HTTP "
                "scrapers fail on them. This tool renders pages in a real browser, "
                "waits for AJAX content to load, and extracts actual text. "
                "Automatically discovers sitemap.xml and crawls key pages "
                "(about, services, doctors, prices, contacts). "
                "Use as a fallback when web_fetch returns empty or sparse content, "
                "especially for Russian medical sites (most are on Bitrix)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to scrape (https://...)",
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Max pages to crawl (default: 10)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_bitrix_scrape,
    check_fn=lambda: True,
    is_async=True,
    description="Scrape Bitrix websites via Playwright (renders JavaScript)",
    emoji="🧱",
)
