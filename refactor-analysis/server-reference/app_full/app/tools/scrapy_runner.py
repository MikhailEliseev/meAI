"""
scrapy_runner — Hermes tool: Scrapy-based web scraping.

Runs Scrapy spiders as subprocesses (Scrapy uses Twisted reactor,
incompatible with asyncio). Extracts structured data from websites.

Replaces Brave Search for deep structured data extraction.
Free, no API key required.
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 120.0


def _generate_spider_script(url: str, max_pages: int, spider_name: str) -> str:
    """Generate a standalone Scrapy spider script for the given URL."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc

    return f'''
import json
import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class {spider_name}(CrawlSpider):
    name = "{spider_name.lower()}"
    start_urls = ["{url}"]
    allowed_domains = ["{domain}"]

    rules = (
        Rule(LinkExtractor(allow_domains="{domain}"), callback="parse_item", follow=True),
    )

    custom_settings = {{
        "CLOSESPIDER_PAGECOUNT": {max_pages},
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 4,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "LOG_LEVEL": "WARNING",
    }}

    def parse_item(self, response):
        yield {{
            "url": response.url,
            "title": response.css("title::text").get("").strip(),
            "h1": " | ".join(response.css("h1::text").getall()),
            "h2_summary": " | ".join(response.css("h2::text").getall()[:5]),
            "text_length": len(response.text),
            "status": response.status,
        }}

# Run
process = CrawlerProcess(settings={{
    "FEEDS": {{"/tmp/scrapy_output.json": {{"format": "json", "encoding": "utf-8"}}}},
    "LOG_LEVEL": "WARNING",
}})
process.crawl({spider_name})
process.start()

# Read output
try:
    with open("/tmp/scrapy_output.json") as f:
        data = json.load(f)
    print(json.dumps(data, ensure_ascii=False))
except Exception:
    print("[]")
'''


async def handle_scrapy_crawl(url=None, max_pages=None, **kwargs) -> str:
    """Crawl a website using Scrapy.

    Generates and runs a CrawlSpider as a subprocess. Extracts
    titles, headers, and text length from each page.

    Args:
        url: Starting URL (https://...)
        max_pages: Max pages to crawl (default: 20, max: 100)

    Returns:
        JSON with scraped pages.
    """
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        max_pages = d.get("max_pages", max_pages)

    if not url:
        return json.dumps({"error": "url is required"})
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    max_p = min(int(max_pages) if max_pages else 20, 100)
    logger.info("scrapy_crawl: %s (max_pages=%d)", url[:120], max_p)

    try:
        import scrapy
    except ImportError:
        return json.dumps({
            "error": "scrapy not installed. Run: pip install scrapy",
        })

    from app.main import push_tool_progress
    push_tool_progress("scrapy", f"🕸️ Scrapy: обхожу {url}…")

    spider_name = f"Spider{uuid.uuid4().hex[:8]}"
    script = _generate_spider_script(url, max_p, spider_name)

    # Write script to temp file
    script_path = f"/tmp/scrapy_{spider_name}.py"
    with open(script_path, "w") as f:
        f.write(script)

    try:
        # Run scrapy as subprocess with timeout
        proc = await asyncio.create_subprocess_exec(
            "python", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=REQUEST_TIMEOUT
        )

        output = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace")

        if stderr_text and "ERROR" in stderr_text:
            logger.warning("scrapy stderr: %s", stderr_text[:500])

        try:
            pages = json.loads(output) if output else []
        except json.JSONDecodeError:
            # Try to extract JSON from mixed output
            import re
            match = re.search(r'\[.*\]', output, re.DOTALL)
            pages = json.loads(match.group(0)) if match else []

    except asyncio.TimeoutError:
        logger.warning("scrapy crawl timed out after %ds", REQUEST_TIMEOUT)
        pages = [{"error": "timeout", "url": url}]
    except Exception as e:
        logger.error("scrapy crawl failed: %s", str(e)[:200])
        pages = [{"error": str(e)[:300], "url": url}]
    finally:
        # Cleanup
        try:
            os.unlink(script_path)
        except Exception:
            pass
        try:
            os.unlink("/tmp/scrapy_output.json")
        except Exception:
            pass

    push_tool_progress("scrapy", f"✅ Scrapy: {len(pages)} страниц собрано")

    return json.dumps({
        "url": url,
        "pages_scraped": len(pages),
        "pages": pages,
        "source": "scrapy",
    }, ensure_ascii=False, indent=2)


# ── Register tools ──────────────────────────────────────────────────

def _check_scrapy():
    try:
        import scrapy
        return True
    except ImportError:
        return False


registry.register(
    name="scrapy_crawl",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "scrapy_crawl",
            "description": (
                "Crawl a website using Scrapy framework. Follows internal links, "
                "extracts titles, headers, and page metadata. "
                "Use for: full site content inventory, finding all pages on a competitor site, "
                "structured data extraction at scale."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Starting URL to crawl (https://...)",
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Max pages to crawl (default: 20, max: 100)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_scrapy_crawl,
    check_fn=_check_scrapy,
    is_async=True,
    description="Crawl websites with Scrapy framework (structured data extraction)",
    emoji="🕸️",
)
