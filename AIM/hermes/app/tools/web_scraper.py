"""
web_scraper — Hermes tools: fetch web pages, search, screenshots.

Part of toolset "hermes-debug". Gives Hermes real web access:
- web_fetch: HTTP GET + HTML parsing via beautifulsoup4
- web_search: DuckDuckGo HTML search (free, no API key)
- browser_screenshot: Playwright Chromium screenshot
"""

import asyncio
import json
import logging
import re
import time

import httpx
from tools.registry import registry

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


async def handle_web_fetch(url=None, parse_html=False, max_length=None, **kwargs) -> str:
    """Fetch a web page and return its content.

    Args:
        url: Full URL to fetch (https://...)
        parse_html: If true, extract text from HTML using beautifulsoup4
        max_length: Max chars to return (default 10000)

    Returns:
        JSON with status_code, content, content_type, length.
    """
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        parse_html = d.get("parse_html", parse_html or False)
        max_length = d.get("max_length", max_length)

    if not url:
        return json.dumps({"error": "url is required"})
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must start with http:// or https://"})

    max_len = int(max_length) if max_length else 10000
    logger.info("web_fetch: %s (parse=%s)", url[:120], parse_html)

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.get(url)
            content_type = resp.headers.get("content-type", "")

            if parse_html and "text/html" in content_type:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                # Remove scripts and styles
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                # Collapse whitespace
                text = re.sub(r'\n{3,}', '\n\n', text)
                content = text[:max_len]
            else:
                content = resp.text[:max_len]

            return json.dumps({
                "status_code": resp.status_code,
                "content_type": content_type,
                "url": str(resp.url),
                "length": len(resp.text),
                "returned_chars": len(content),
                "content": content,
            }, ensure_ascii=False)

        # ── Framework-level JS fallback (v3.3++ Plan A++) ────────────────
        # If HTML is suspiciously short (< 5KB) or contains JS-render markers,
        # automatically retry via crawlee_scrape which executes JavaScript.
        # This bypasses the LLM needing to detect JS sites explicitly.
        try:
            content = resp.text  # full raw HTML for JS detection
            js_markers = [
                '<div id="root"></div>',
                '<div id="app"></div>',
                '<div id="root"/>',
                'You need to enable JavaScript',
                'Please enable JavaScript',
            ]
            looks_like_js_shell = (
                len(resp.text) < 5000
                or any(marker in resp.text for marker in js_markers)
            )
            if looks_like_js_shell and "text/html" in content_type:
                logger.info("web_fetch: JS-rendered site detected (%d bytes), auto-fallback to crawlee_scrape", len(resp.text))
                try:
                    from .crawlee_web import handle_crawlee_scrape
                    crawlee_result = await handle_crawlee_scrape(url=url)
                    # crawlee returns JSON string; parse it and merge metadata
                    import json as _json
                    try:
                        cl_data = _json.loads(crawlee_result)
                        if isinstance(cl_data, dict) and cl_data.get("content"):
                            cl_content = cl_data["content"][:max_len]
                            return _json.dumps({
                                "status_code": resp.status_code,
                                "content_type": content_type,
                                "url": str(resp.url),
                                "length": len(cl_data.get("content", "")),
                                "returned_chars": len(cl_content),
                                "content": cl_content,
                                "via": "crawlee_scrape (auto-fallback: JS site)",
                                "original_length": len(resp.text),
                            }, ensure_ascii=False)
                    except Exception:
                        pass  # fall through to normal return
                except ImportError:
                    logger.debug("crawlee_web not available for JS fallback")
                except Exception as exc:
                    logger.debug("crawlee fallback failed: %s", exc)
        except Exception:
            pass

    except httpx.TimeoutException:
        return json.dumps({"error": f"Timeout fetching {url[:120]}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def handle_web_search(query=None, limit=None, **kwargs) -> str:
    """Search the web via DuckDuckGo HTML search.

    Free, no API key required. Uses DDG's HTML endpoint (non-JS version).

    Args:
        query: Search query string
        limit: Max results to return (default 10)

    Returns:
        JSON with results list [{title, url, description}, ...].
    """
    if isinstance(query, dict):
        d = query
        query = d.get("query", "")
        limit = d.get("limit", limit)

    if not query or not isinstance(query, str):
        return json.dumps({"error": "query is required (string)"})

    max_results = int(limit) if limit else 10
    logger.info("web_search: %s (limit=%d)", query[:80], max_results)

    try:
        from app.tools._search_fallback import search as fallback_search
        results, provider = await fallback_search(query, max_results=min(max_results, 20))

        return json.dumps({
            "query": query,
            "results_count": len(results),
            "results": results,
            "source": provider,
        }, ensure_ascii=False)

    except ImportError:
        return json.dumps({"error": "Search module not available"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def handle_browser_screenshot(url=None, full_page=None, **kwargs) -> str:
    """Take a screenshot of a web page using Playwright Chromium.

    Args:
        url: Full URL to screenshot
        full_page: If true, capture full scrollable page (default: True)

    Returns:
        JSON with status, url, viewport_size, screenshot_path (saved to /tmp/).
    """
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        full_page = d.get("full_page", full_page)

    if not url:
        return json.dumps({"error": "url is required"})
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must start with http:// or https://"})

    do_full_page = full_page if full_page is not None else True
    logger.info("browser_screenshot: %s (full_page=%s)", url[:120], do_full_page)

    try:
        from playwright.async_api import async_playwright

        timestamp = int(time.time())
        output_path = f"/tmp/screenshot_{timestamp}.png"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.screenshot(path=output_path, full_page=do_full_page)
            await browser.close()

        import os
        file_size = os.path.getsize(output_path)

        return json.dumps({
            "status": "ok",
            "url": url,
            "full_page": do_full_page,
            "screenshot_path": output_path,
            "file_size_bytes": file_size,
        }, ensure_ascii=False)

    except ImportError:
        return json.dumps({"error": "playwright not installed — add to Dockerfile"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Register tools ──────────────────────────────────────────────────

registry.register(
    name="web_fetch",
    toolset="hermes-debug",
    schema={
            "name": "web_fetch",
            "description": (
                "Fetch a web page and return its content. "
                "Set parse_html=true to extract readable text from HTML via beautifulsoup4. "
                "Use to read documentation, check API responses, scrape data, inspect sites."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL to fetch (https://...)",
                    },
                    "parse_html": {
                        "type": "boolean",
                        "description": "Extract text from HTML instead of returning raw HTML (default: false)",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Max characters to return (default: 10000)",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_web_fetch,
    check_fn=lambda: True,
    is_async=True,
    description="Fetch and parse web pages",
    emoji="🌐",
)

registry.register(
    name="web_search",
    toolset="hermes-debug",
    schema={
            "name": "web_search",
            "description": (
                "Search the web via DuckDuckGo (free, no API key). "
                "Returns title, URL, and description for each result. "
                "Use to find current information, documentation, competitors, tools."
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
                        "description": "Max results to return (default: 10)",
                    },
                },
                "required": ["query"],
            },
        },
    handler=handle_web_search,
    check_fn=lambda: True,
    is_async=True,
    description="Search the web via DuckDuckGo",
    emoji="🔍",
)

registry.register(
    name="browser_screenshot",
    toolset="hermes-debug",
    schema={
            "name": "browser_screenshot",
            "description": (
                "Take a screenshot of a web page using headless Chromium (Playwright). "
                "Returns path to PNG file. Use to visually inspect sites, capture competitor "
                "landing pages, verify design changes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL to screenshot (https://...)",
                    },
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full scrollable page, not just viewport (default: true)",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_browser_screenshot,
    check_fn=lambda: True,
    is_async=True,
    description="Screenshot web pages via headless Chromium",
    emoji="📸",
)
