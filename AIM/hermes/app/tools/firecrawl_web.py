"""
firecrawl_web — Hermes tools: Firecrawl-powered web scraping, search, crawl, map,
extract, batch scrape, autonomous agent, file parsing (9 tools total).

Part of toolset "hermes-debug". Uses FirecrawlKeyBank for multi-key rotation
with automatic fallback on 402/credit-exhaustion errors.

v7.1: Added extract, batch_scrape, agent, agent_status, parse.
Matches Firecrawl MCP server capabilities.
"""

import asyncio
import json
import logging
import os
import pathlib
import threading

from tools.registry import registry
from app.key_bank import key_bank
from .firecrawl_key_bank import classify_exhaustion

logger = logging.getLogger(__name__)

_FALLBACK_KEY = os.environ.get("FIRECRAWL_API_KEY", "").strip()
_lock = threading.Lock()

AGENT_TIMEOUT = 300
AGENT_POLL_INTERVAL = 3
BATCH_TIMEOUT = 180
EXTRACT_TIMEOUT = 120


def _get_client():
    """Create a Firecrawl client using the next available key from the bank."""
    from firecrawl import Firecrawl

    try:
        key = key_bank.get_firecrawl_key()
    except RuntimeError:
        if _FALLBACK_KEY:
            return Firecrawl(api_key=_FALLBACK_KEY), _FALLBACK_KEY
        raise
    if not key:
        if _FALLBACK_KEY:
            return Firecrawl(api_key=_FALLBACK_KEY), _FALLBACK_KEY
        raise RuntimeError("No Firecrawl keys available")
    return Firecrawl(api_key=key), key


def _handle_credit_error(key: str, error_msg: str):
    """Mark key dead on credit exhaustion and rotate."""
    if not key:
        return
    reason = classify_exhaustion(error_msg)
    if not reason:
        return
    try:
        key_bank.mark_firecrawl_exhausted(key)
    except Exception:
        pass


async def handle_firecrawl_scrape(url=None, formats=None, only_main_content=None, **kwargs) -> str:
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        formats = d.get("formats", formats)
        only_main_content = d.get("only_main_content", only_main_content)

    if not url:
        return json.dumps({"error": "url is required"})

    fmts = formats if formats else ["markdown"]
    main_only = only_main_content if only_main_content is not None else True

    for attempt in range(3):
        try:
            fc, key = _get_client()
        except RuntimeError:
            return json.dumps({"error": "FIRECRAWL_API_KEY not set and no keys in bank"})

        logger.info("firecrawl_scrape: %s (attempt %d)", url[:120], attempt + 1)
        try:
            result = fc.scrape(url, formats=fmts, only_main_content=main_only)
            return json.dumps({
                "url": url,
                "title": result.get("metadata", {}).get("title", ""),
                "markdown": result.get("markdown", "")[:50000],
                "metadata": result.get("metadata", {}),
                "actions": result.get("actions", {}),
            }, ensure_ascii=False)
        except Exception as e:
            err = str(e)
            _handle_credit_error(key, err)
            if not classify_exhaustion(err):
                logger.error("firecrawl_scrape failed: %s", err[:200])
                return json.dumps({"error": err[:500]})

    return json.dumps({"error": "firecrawl_scrape: all keys exhausted"})


async def handle_firecrawl_search(query=None, limit=None, source=None, **kwargs) -> str:
    if isinstance(query, dict):
        d = query
        query = d.get("query", "")
        limit = d.get("limit", limit)
        source = d.get("source", source)

    if not query:
        return json.dumps({"error": "query is required"})

    max_results = int(limit) if limit else 5
    src = source if source else "web"

    for attempt in range(3):
        try:
            fc, key = _get_client()
        except RuntimeError:
            return json.dumps({"error": "FIRECRAWL_API_KEY not set and no keys in bank"})

        logger.info("firecrawl_search: %s (limit=%d, source=%s, attempt=%d)", query[:80], max_results, src, attempt + 1)
        try:
            result = fc.search(query, limit=max_results, source=src)
            results = []
            for r in result.get("data", [])[:max_results]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                    "markdown": r.get("markdown", "")[:10000],
                })

            return json.dumps({
                "query": query,
                "source": src,
                "results_count": len(results),
                "results": results,
            }, ensure_ascii=False)
        except Exception as e:
            err = str(e)
            _handle_credit_error(key, err)
            if not classify_exhaustion(err):
                logger.warning("firecrawl_search failed: %s", err[:200])
                return json.dumps({
                    "query": query, "source": "error",
                    "results_count": 0, "results": [],
                    "error": "search unavailable",
                })

    return json.dumps({
        "query": query, "source": "error",
        "results_count": 0, "results": [],
        "error": "all FireCrawl keys exhausted",
    })


async def handle_firecrawl_crawl(url=None, limit=None, max_pages=None, **kwargs) -> str:
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        limit = d.get("limit", d.get("max_pages", limit))

    if not url:
        return json.dumps({"error": "url is required"})

    max_pages_val = int(limit) if limit else 10

    for attempt in range(3):
        try:
            fc, key = _get_client()
        except RuntimeError:
            return json.dumps({"error": "FIRECRAWL_API_KEY not set and no keys in bank"})

        logger.info("firecrawl_crawl: %s (max_pages=%d, attempt=%d)", url[:120], max_pages_val, attempt + 1)
        try:
            result = fc.crawl(url, limit=max_pages_val, scrape_options={"formats": ["markdown"]})
            pages = []
            for p in result.get("data", [])[:max_pages_val]:
                pages.append({
                    "url": p.get("metadata", {}).get("url", ""),
                    "title": p.get("metadata", {}).get("title", ""),
                    "markdown": (p.get("markdown", "") or "")[:20000],
                })

            return json.dumps({
                "start_url": url,
                "total_pages": len(pages),
                "pages": pages,
            }, ensure_ascii=False)
        except Exception as e:
            err = str(e)
            _handle_credit_error(key, err)
            if not classify_exhaustion(err):
                logger.error("firecrawl_crawl failed: %s", err[:200])
                return json.dumps({"error": err[:500]})

    return json.dumps({"error": "firecrawl_crawl: all keys exhausted"})


async def handle_firecrawl_map(url=None, **kwargs) -> str:
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")

    if not url:
        return json.dumps({"error": "url is required"})

    for attempt in range(3):
        try:
            fc, key = _get_client()
        except RuntimeError:
            return json.dumps({"error": "FIRECRAWL_API_KEY not set and no keys in bank"})

        logger.info("firecrawl_map: %s (attempt=%d)", url[:120], attempt + 1)
        try:
            result = fc.map(url)
            urls = result.get("links", [])
            return json.dumps({
                "url": url,
                "total_urls": len(urls),
                "urls": urls[:500],
            }, ensure_ascii=False)
        except Exception as e:
            err = str(e)
            _handle_credit_error(key, err)
            if not classify_exhaustion(err):
                logger.error("firecrawl_map failed: %s", err[:200])
                return json.dumps({"error": err[:500]})

    return json.dumps({"error": "firecrawl_map: all keys exhausted"})


# ── NEW (v7.1): firecrawl_extract ───────────────────────────────────

async def handle_firecrawl_extract(urls=None, prompt=None, schema=None, **kwargs) -> str:
    """Extract structured data from URLs using Firecrawl LLM.

    Args:
        urls: List of URLs to extract from
        prompt: Natural language description of what to extract
        schema: Optional JSON schema for structured output
    """
    if isinstance(urls, dict):
        d = urls
        urls = d.get("urls", [])
        prompt = d.get("prompt", prompt)
        schema = d.get("schema", schema)

    if not urls:
        return json.dumps({"error": "urls is required (list of URLs)"})
    if not prompt:
        return json.dumps({"error": "prompt is required"})

    if isinstance(urls, str):
        urls = [urls]

    logger.info("firecrawl_extract: %d urls, prompt=%s", len(urls), prompt[:80])

    from app.main import push_tool_progress
    push_tool_progress("firecrawl", f"🧠 Firecrawl Extract: извлекаю данные из {len(urls)} URL…")

    try:
        fc, key = _get_client()
    except RuntimeError:
        return json.dumps({"error": "No Firecrawl keys available"})

    try:
        result = await asyncio.to_thread(
            fc.extract,
            urls=urls,
            prompt=prompt,
            schema=schema,
            timeout=EXTRACT_TIMEOUT * 1000,
        )
        push_tool_progress("firecrawl", "✅ Firecrawl Extract: данные извлечены")
        return json.dumps({
            "urls": urls,
            "prompt": prompt[:200],
            "data": result.get("data", result) if isinstance(result, dict) else str(result),
            "source": "firecrawl_extract",
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        err = str(e)
        _handle_credit_error(key, err)
        logger.error("firecrawl_extract failed: %s", err[:200])
        return json.dumps({"error": err[:500], "urls": urls})


# ── NEW (v7.1): firecrawl_batch_scrape ────────────────────────────────

async def handle_firecrawl_batch_scrape(urls=None, formats=None, only_main_content=None, **kwargs) -> str:
    """Scrape multiple URLs in batch using Firecrawl.

    Args:
        urls: List of URLs to scrape
        formats: Output formats (default: ['markdown'])
        only_main_content: Extract only main content (default: true)
    """
    if isinstance(urls, dict):
        d = urls
        urls = d.get("urls", [])
        formats = d.get("formats", formats)
        only_main_content = d.get("only_main_content", only_main_content)

    if not urls:
        return json.dumps({"error": "urls is required (list of URLs)"})
    if isinstance(urls, str):
        urls = [urls]

    fmts = formats if formats else ["markdown"]
    main_only = only_main_content if only_main_content is not None else True

    logger.info("firecrawl_batch_scrape: %d urls", len(urls))

    from app.main import push_tool_progress
    push_tool_progress("firecrawl", f"📦 Firecrawl Batch: скраплю {len(urls)} URL…")

    try:
        fc, key = _get_client()
    except RuntimeError:
        return json.dumps({"error": "No Firecrawl keys available"})

    try:
        result = await asyncio.to_thread(
            fc.batch_scrape,
            urls=urls,
            formats=fmts,
            only_main_content=main_only,
            timeout=BATCH_TIMEOUT * 1000,
        )
        pages = []
        data = result.get("data", []) if isinstance(result, dict) else []
        for p in data:
            pages.append({
                "url": p.get("metadata", {}).get("url", "") if isinstance(p, dict) else getattr(p, "metadata", {}).get("url", ""),
                "title": (p.get("metadata", {}) if isinstance(p, dict) else getattr(p, "metadata", {})).get("title", ""),
                "markdown": (p.get("markdown", "") if isinstance(p, dict) else getattr(p, "markdown", ""))[:20000],
            })

        push_tool_progress("firecrawl", f"✅ Firecrawl Batch: {len(pages)} страниц собрано")
        return json.dumps({
            "total_urls": len(urls),
            "pages_scraped": len(pages),
            "pages": pages,
            "source": "firecrawl_batch",
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        err = str(e)
        _handle_credit_error(key, err)
        logger.error("firecrawl_batch_scrape failed: %s", err[:200])
        return json.dumps({"error": err[:500], "urls": urls})


# ── NEW (v7.1): firecrawl_agent ───────────────────────────────────────

async def handle_firecrawl_agent(prompt=None, urls=None, schema=None, max_credits=None, **kwargs) -> str:
    """Launch autonomous Firecrawl research agent.

    The agent independently browses the web, searches, and extracts data.
    Use for complex multi-source research tasks.

    Args:
        prompt: Natural language description of what to research (REQUIRED)
        urls: Optional list of URLs to focus on
        schema: Optional JSON schema for structured output
        max_credits: Max credits to spend (default: 10)
    """
    if isinstance(prompt, dict):
        d = prompt
        prompt = d.get("prompt", "")
        urls = d.get("urls", urls)
        schema = d.get("schema", schema)
        max_credits = d.get("max_credits", max_credits)

    if not prompt:
        return json.dumps({"error": "prompt is required"})

    logger.info("firecrawl_agent: prompt=%s", prompt[:120])

    from app.main import push_tool_progress
    push_tool_progress("firecrawl", f"🤖 Firecrawl Agent: исследую «{prompt[:60]}»…")

    try:
        fc, key = _get_client()
    except RuntimeError:
        return json.dumps({"error": "No Firecrawl keys available"})

    try:
        job = fc.start_agent(
            prompt=prompt,
            urls=urls,
            schema=schema,
            max_credits=max_credits or 10,
        )
        job_id = job.get("id", "") if isinstance(job, dict) else getattr(job, "id", "")

        # Poll until complete or timeout
        elapsed = 0
        while elapsed < AGENT_TIMEOUT:
            await asyncio.sleep(AGENT_POLL_INTERVAL)
            elapsed += AGENT_POLL_INTERVAL

            status = fc.get_agent_status(job_id)
            state = status.get("status", "") if isinstance(status, dict) else getattr(status, "status", "")

            if state == "completed":
                data = status.get("data", status) if isinstance(status, dict) else status
                push_tool_progress("firecrawl", "✅ Firecrawl Agent: исследование завершено")
                return json.dumps({
                    "prompt": prompt[:200],
                    "status": "completed",
                    "job_id": job_id,
                    "data": data,
                    "source": "firecrawl_agent",
                }, ensure_ascii=False, indent=2, default=str)
            elif state == "failed":
                error_msg = status.get("error", "Unknown error") if isinstance(status, dict) else "Unknown error"
                return json.dumps({"error": f"Agent failed: {error_msg}", "job_id": job_id})

            push_tool_progress("firecrawl", f"🤖 Firecrawl Agent: в процессе… ({elapsed}s)")

        # Timeout — return whatever we have
        push_tool_progress("firecrawl", f"⏰ Firecrawl Agent: таймаут ({AGENT_TIMEOUT}s), возвращаю промежуточный результат")
        status = fc.get_agent_status(job_id)
        return json.dumps({
            "prompt": prompt[:200],
            "status": "timeout",
            "job_id": job_id,
            "partial_data": str(status)[:5000],
            "source": "firecrawl_agent",
        }, ensure_ascii=False, indent=2, default=str)

    except Exception as e:
        err = str(e)
        _handle_credit_error(key, err)
        logger.error("firecrawl_agent failed: %s", err[:200])
        return json.dumps({"error": err[:500], "prompt": prompt[:200]})


# ── NEW (v7.1): firecrawl_agent_status ────────────────────────────────

async def handle_firecrawl_agent_status(job_id=None, **kwargs) -> str:
    """Check the status of a running Firecrawl agent job.

    Args:
        job_id: The agent job ID returned by firecrawl_agent
    """
    if isinstance(job_id, dict):
        job_id = job_id.get("job_id", "")

    if not job_id:
        return json.dumps({"error": "job_id is required"})

    try:
        fc, _ = _get_client()
    except RuntimeError:
        return json.dumps({"error": "No Firecrawl keys available"})

    try:
        status = fc.get_agent_status(job_id)
        return json.dumps({
            "job_id": job_id,
            "status": status.get("status", "unknown") if isinstance(status, dict) else "unknown",
            "data": str(status)[:10000],
        }, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)[:500], "job_id": job_id})


# ── NEW (v7.1): firecrawl_parse ──────────────────────────────────────

async def handle_firecrawl_parse(file_path=None, formats=None, **kwargs) -> str:
    """Parse a local file (PDF, DOCX, HTML, etc.) using Firecrawl.

    Args:
        file_path: Absolute path to the file on disk
        formats: Output formats (default: ['markdown'])
    """
    if isinstance(file_path, dict):
        d = file_path
        file_path = d.get("file_path", d.get("path", ""))
        formats = d.get("formats", formats)

    if not file_path:
        return json.dumps({"error": "file_path is required"})

    p = pathlib.Path(file_path)
    if not p.exists():
        return json.dumps({"error": f"File not found: {file_path}"})

    fmts = formats if formats else ["markdown"]

    logger.info("firecrawl_parse: %s", file_path)

    from app.main import push_tool_progress
    push_tool_progress("firecrawl", f"📄 Firecrawl Parse: {p.name}…")

    try:
        fc, key = _get_client()
    except RuntimeError:
        return json.dumps({"error": "No Firecrawl keys available"})

    try:
        result = await asyncio.to_thread(
            fc.parse,
            file=str(p),
            options={"formats": fmts},
        )
        push_tool_progress("firecrawl", f"✅ Firecrawl Parse: {p.name} обработан")
        return json.dumps({
            "file": str(p),
            "filename": p.name,
            "markdown": (result.get("markdown", "") if isinstance(result, dict) else "")[:50000],
            "metadata": result.get("metadata", {}) if isinstance(result, dict) else {},
            "source": "firecrawl_parse",
        }, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        err = str(e)
        _handle_credit_error(key, err)
        logger.error("firecrawl_parse failed: %s", err[:200])
        return json.dumps({"error": err[:500], "file": str(p)})


# ── Register tools ──────────────────────────────────────────────────

def _check():
    try:
        return key_bank.get_firecrawl_key() is not None or bool(_FALLBACK_KEY)
    except Exception:
        return bool(_FALLBACK_KEY)


registry.register(
    name="firecrawl_scrape",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_scrape",
            "description": (
                "Scrape a single URL and return clean markdown via Firecrawl. "
                "Handles JavaScript-rendered pages, bypasses anti-bot protection. "
                "Returns title, markdown content, metadata, and available actions. "
                "Use for: reading competitor pages, extracting pricing, analyzing content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "[REQUIRED] Full URL to scrape (https://...)",
                    },
                    "formats": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Output formats: markdown, html, screenshot (default: ['markdown'])",
                    },
                    "only_main_content": {
                        "type": "boolean",
                        "description": "Extract only main content, skip nav/footer (default: true)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_firecrawl_scrape,
    check_fn=_check,
    is_async=True,
    description="Scrape URLs to clean markdown via Firecrawl",
    emoji="🔥",
)

registry.register(
    name="firecrawl_search",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_search",
            "description": (
                "Search the web via Firecrawl and return results with full page content. "
                "Better than simple search — returns markdown of each result page. "
                "Use for: finding competitors, researching topics, discovering tools. "
                "Source can be 'web' (default), 'news', or 'images'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "[REQUIRED] Search query string",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default: 5)",
                    },
                    "source": {
                        "type": "string",
                        "enum": ["web", "news", "images"],
                        "description": "Search source (default: web)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    handler=handle_firecrawl_search,
    check_fn=_check,
    is_async=True,
    description="Search web with page content via Firecrawl",
    emoji="🔎",
)

registry.register(
    name="firecrawl_crawl",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_crawl",
            "description": (
                "Crawl multiple pages from a domain and return combined markdown. "
                "Follows internal links, extracts content from each page. "
                "Use for: full site analysis, content inventory, competitor research."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "[REQUIRED] Starting URL for crawl (https://...)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max pages to crawl (default: 10)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_firecrawl_crawl,
    check_fn=_check,
    is_async=True,
    description="Crawl multiple pages via Firecrawl",
    emoji="🕷️",
)

registry.register(
    name="firecrawl_map",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_map",
            "description": (
                "Discover all URLs on a website without scraping content. "
                "Fast and lightweight — returns URL list only. "
                "Use for: sitemap discovery, site structure analysis, finding all pages."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "[REQUIRED] Website URL to map (https://...)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_firecrawl_map,
    check_fn=_check,
    is_async=True,
    description="Discover all URLs on a site via Firecrawl",
    emoji="🗺️",
)

# ── NEW (v7.1) registrations ────────────────────────────────────────

registry.register(
    name="firecrawl_extract",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_extract",
            "description": (
                "Extract structured data from web pages using Firecrawl LLM. "
                "Describe what you want in natural language — the AI extracts it. "
                "Use for: competitor pricing extraction, doctor lists, service catalogs, "
                "any structured data from one or multiple URLs. "
                "IMPORTANT: pass urls as a JSON array, e.g. [\"https://...\", \"https://...\"]"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "[REQUIRED] List of URLs to extract data from",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "[REQUIRED] Natural language description of what data to extract",
                    },
                    "schema": {
                        "type": "object",
                        "description": "Optional JSON schema for structured output",
                    },
                },
                "required": ["urls", "prompt"],
            },
        },
    },
    handler=handle_firecrawl_extract,
    check_fn=_check,
    is_async=True,
    description="Extract structured data from web pages with Firecrawl LLM",
    emoji="🧠",
)

registry.register(
    name="firecrawl_batch_scrape",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_batch_scrape",
            "description": (
                "Scrape MULTIPLE URLs at once and return their markdown content. "
                "More efficient than calling firecrawl_scrape repeatedly. "
                "Use for: scraping all competitor sites at once, bulk content extraction. "
                "IMPORTANT: pass urls as a JSON array."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "[REQUIRED] List of URLs to scrape (max 50)",
                    },
                    "formats": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Output formats (default: ['markdown'])",
                    },
                    "only_main_content": {
                        "type": "boolean",
                        "description": "Extract only main content (default: true)",
                    },
                },
                "required": ["urls"],
            },
        },
    },
    handler=handle_firecrawl_batch_scrape,
    check_fn=_check,
    is_async=True,
    description="Scrape multiple URLs at once with Firecrawl",
    emoji="📦",
)

registry.register(
    name="firecrawl_agent",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_agent",
            "description": (
                "Launch an AUTONOMOUS web research agent. The agent independently searches, "
                "browses, and extracts data to answer your research question. "
                "Much more powerful than a single search — it navigates multiple sites, "
                "follows leads, and synthesizes findings. Takes 1-5 minutes. "
                "Use for: deep competitor analysis, market research, finding specific "
                "information across multiple sources. "
                "Returns a job_id — use firecrawl_agent_status to check progress if needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "[REQUIRED] Research question or task description",
                    },
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: specific URLs to focus the agent on",
                    },
                    "schema": {
                        "type": "object",
                        "description": "Optional JSON schema for structured output",
                    },
                    "max_credits": {
                        "type": "integer",
                        "description": "Max credits to spend (default: 10)",
                    },
                },
                "required": ["prompt"],
            },
        },
    },
    handler=handle_firecrawl_agent,
    check_fn=_check,
    is_async=True,
    description="Autonomous web research agent via Firecrawl",
    emoji="🤖",
)

registry.register(
    name="firecrawl_agent_status",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_agent_status",
            "description": (
                "Check the status of a running firecrawl_agent job. "
                "Returns current progress and results if complete. "
                "Use when you started a firecrawl_agent and want to check if it's done."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "[REQUIRED] The agent job ID from firecrawl_agent",
                    },
                },
                "required": ["job_id"],
            },
        },
    },
    handler=handle_firecrawl_agent_status,
    check_fn=_check,
    is_async=True,
    description="Check Firecrawl agent job status",
    emoji="📊",
)

registry.register(
    name="firecrawl_parse",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "firecrawl_parse",
            "description": (
                "Parse a local file (PDF, DOCX, HTML, XLSX) into clean markdown. "
                "Use for: extracting text from uploaded documents, reading PDF reports, "
                "converting spreadsheets to text for analysis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "[REQUIRED] Absolute path to the file on disk (e.g., '/opt/data/report.pdf')",
                    },
                    "formats": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Output formats (default: ['markdown'])",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    handler=handle_firecrawl_parse,
    check_fn=_check,
    is_async=True,
    description="Parse local files (PDF, DOCX, HTML) with Firecrawl",
    emoji="📄",
)
