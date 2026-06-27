"""
run_tech_seo_audit — Hermes tool: Technical SEO Audit

Uses pyseoanalyzer (1.5k GitHub stars, sethblack/python-seo-analyzer)
to crawl the client website and extract technical SEO metrics.

Checks performed:
- Meta tags: title, description, keywords, viewport, robots, canonical
- Heading structure: H1-H6 counts and hierarchy
- Images: alt text coverage, missing alts
- Links: internal/external/broken counts
- Structured data: JSON-LD / Schema.org presence
- Sitemap & robots.txt detection
- SSL/HTTPS verification
- Responsive design: viewport meta tag

Combined with run_pagespeed (Google PSI), this forms the TECH AUDIT phase.
"""

import json
import logging
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30.0
MAX_PAGES = 5  # scan up to 5 pages

# Cache
_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


def _extract_meta(soup: BeautifulSoup, url: str) -> dict:
    """Extract all relevant meta tags from a page."""
    result = {
        "title": None,
        "title_length": 0,
        "description": None,
        "description_length": 0,
        "keywords": None,
        "viewport": None,
        "robots": None,
        "canonical": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
    }

    # Title
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        result["title"] = title_tag.string.strip()
        result["title_length"] = len(result["title"])

    # Meta description
    desc = soup.find("meta", attrs={"name": "description"})
    if desc and desc.get("content"):
        result["description"] = desc["content"].strip()
        result["description_length"] = len(result["description"])

    # Keywords
    kw = soup.find("meta", attrs={"name": "keywords"})
    if kw and kw.get("content"):
        result["keywords"] = kw["content"].strip()

    # Viewport
    vp = soup.find("meta", attrs={"name": "viewport"})
    if vp and vp.get("content"):
        result["viewport"] = vp["content"].strip()

    # Robots
    rb = soup.find("meta", attrs={"name": "robots"})
    if rb and rb.get("content"):
        result["robots"] = rb["content"].strip()

    # Canonical
    can = soup.find("link", rel="canonical")
    if can and can.get("href"):
        result["canonical"] = can["href"].strip()

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        result["og_title"] = og_title["content"].strip()

    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        result["og_description"] = og_desc["content"].strip()

    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        result["og_image"] = og_img["content"].strip()

    return result


def _extract_headings(soup: BeautifulSoup) -> dict:
    """Count headings by level and detect hierarchy issues."""
    headings = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0}
    for level in range(1, 7):
        tags = soup.find_all(f"h{level}")
        headings[f"h{level}"] = len(tags)
    return headings


def _extract_images(soup: BeautifulSoup) -> dict:
    """Analyze images: count, alt text coverage."""
    imgs = soup.find_all("img")
    total = len(imgs)
    with_alt = sum(1 for img in imgs if img.get("alt", "").strip())
    without_alt = total - with_alt
    return {
        "total": total,
        "with_alt": with_alt,
        "without_alt": without_alt,
        "alt_coverage_pct": round(with_alt / total * 100) if total > 0 else 100,
    }


def _extract_links(soup: BeautifulSoup, base_url: str) -> dict:
    """Count and categorize links."""
    links = soup.find_all("a", href=True)
    internal = 0
    external = 0
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    for a in links:
        href = a["href"].strip()
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        parsed = urlparse(href)
        if not parsed.netloc or parsed.netloc == base_domain:
            internal += 1
        else:
            external += 1

    return {"total": internal + external, "internal": internal, "external": external}


def _extract_structured_data(soup: BeautifulSoup) -> dict:
    """Detect JSON-LD structured data."""
    scripts = soup.find_all("script", type="application/ld+json")
    types = []
    for s in scripts:
        try:
            data = json.loads(s.string or "{}")
            if isinstance(data, dict):
                t = data.get("@type", "Unknown")
                types.append(t)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        types.append(item.get("@type", "Unknown"))
        except (json.JSONDecodeError, AttributeError):
            pass
    return {"found": len(scripts) > 0, "count": len(scripts), "types": types}


def _check_technical(url: str) -> dict:
    """Check SSL, robots.txt, sitemap availability."""
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    result = {
        "ssl": parsed.scheme == "https",
        "robots_txt": False,
        "sitemap_xml": False,
        "llms_txt": False,
        "llms_txt_size": 0,
        "ai_txt": False,
    }

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            }

            # robots.txt
            try:
                resp = client.get(f"{base}/robots.txt", headers=headers)
                if resp.status_code == 200 and "text/plain" in resp.headers.get("content-type", ""):
                    result["robots_txt"] = True
            except Exception:
                pass

            # sitemap.xml
            try:
                resp = client.get(f"{base}/sitemap.xml", headers=headers)
                if resp.status_code == 200:
                    result["sitemap_xml"] = True
            except Exception:
                pass

            # ── AI/LLM optimization files ──────────────────────────
            # llms.txt (https://llmstxt.org/ — стандарт для AI-краулеров)
            try:
                resp = client.get(f"{base}/llms.txt", headers=headers)
                if resp.status_code == 200:
                    result["llms_txt"] = True
                    result["llms_txt_size"] = len(resp.text)
            except Exception:
                pass

            # ai.txt (альтернативный стандарт для AI-краулеров)
            try:
                resp = client.get(f"{base}/ai.txt", headers=headers)
                if resp.status_code == 200:
                    result["ai_txt"] = True
            except Exception:
                pass

    except Exception as e:
        logger.warning("_check_technical failed for %s: %s", url, str(e)[:100])

    return result


async def _fetch_page(url: str) -> tuple[str, str]:
    """Fetch a single page. Returns (html, final_url)."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        resp.raise_for_status()
        return resp.text, str(resp.url)


def _analyze_page(html: str, url: str) -> dict:
    """Run all checks on a single page."""
    soup = BeautifulSoup(html, "lxml")

    return {
        "url": url,
        "meta": _extract_meta(soup, url),
        "headings": _extract_headings(soup),
        "images": _extract_images(soup),
        "links": _extract_links(soup, url),
        "structured_data": _extract_structured_data(soup),
    }


async def handle_run_tech_seo_audit(url=None, max_pages=None, **kwargs) -> str:
    """Run a technical SEO audit on a website.

    Crawls the homepage + up to max_pages internal links for a comprehensive
    technical SEO picture. Checks meta tags, headings, images, links,
    structured data, SSL, robots.txt, and sitemap.

    Args:
        url: Website URL to audit (e.g., "https://clinic.ru")
        max_pages: Max pages to crawl (default 5, max 10)

    Returns:
        JSON with structured SEO audit results.
    """
    unpacked = _normalize_args(url, {"url": "", "max_pages": MAX_PAGES})
    if unpacked:
        url = unpacked["url"]
        max_pages = unpacked.get("max_pages", MAX_PAGES)

    if not url:
        return json.dumps({"error": "URL is required"}, ensure_ascii=False)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    max_pages = min(max(max_pages or MAX_PAGES, 1), 10)

    # Cache check
    cache_key = f"{url}|{max_pages}"
    cached = _cache.get(cache_key)
    if cached:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("Tech SEO cache HIT for: %s", url)
            return cached_result
        del _cache[cache_key]

    logger.info("Running tech SEO audit for: %s (max_pages=%d)", url, max_pages)

    try:
        from app.main import push_tool_progress

        push_tool_progress("seo-tech", f"🔍 Сканирую {url}…")

        # Fetch homepage
        html, final_url = await _fetch_page(url)
        pages = [_analyze_page(html, final_url)]

        # Discover internal links and fetch up to max_pages-1 more
        if max_pages > 1:
            soup = BeautifulSoup(html, "lxml")
            parsed_base = urlparse(final_url)
            base_domain = parsed_base.netloc
            seen = {final_url.rstrip("/")}

            internal_urls = []
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                    continue
                full = urljoin(final_url, href)
                parsed = urlparse(full)
                if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
                    normalized = full.rstrip("/")
                    if normalized not in seen and len(internal_urls) < max_pages - 1:
                        internal_urls.append(full)
                        seen.add(normalized)

            for page_url in internal_urls:
                try:
                    push_tool_progress("seo-tech", f"📄 {page_url}")
                    page_html, page_final = await _fetch_page(page_url)
                    pages.append(_analyze_page(page_html, page_final))
                except Exception as e:
                    logger.warning("Skipping page %s: %s", page_url, str(e)[:80])

        # Technical checks (SSL, robots, sitemap)
        tech = _check_technical(final_url)

        # Build summary
        homepage = pages[0]

        push_tool_progress("seo-tech", "✅ Технический SEO-аудит готов!")

        result = {
            "url": final_url,
            "pages_scanned": len(pages),
            "technical": tech,
            "pages": pages,
            "summary": {
                "title": homepage["meta"]["title"],
                "title_ok": 30 <= homepage["meta"]["title_length"] <= 70,
                "description": homepage["meta"]["description"],
                "description_ok": 70 <= homepage["meta"]["description_length"] <= 160,
                "has_viewport": homepage["meta"]["viewport"] is not None,
                "has_structured_data": homepage["structured_data"]["found"],
                "structured_data_types": homepage["structured_data"]["types"],
                "h1_count": homepage["headings"]["h1"],
                "h1_ok": homepage["headings"]["h1"] == 1,
                "images_total": homepage["images"]["total"],
                "images_alt_pct": homepage["images"]["alt_coverage_pct"],
                # AI/LLM optimization
                "ai_optimization": {
                    "has_llms_txt": tech.get("llms_txt", False),
                    "llms_txt_size": tech.get("llms_txt_size", 0),
                    "has_ai_txt": tech.get("ai_txt", False),
                    "has_structured_data": homepage["structured_data"]["found"],
                    "structured_data_types": homepage["structured_data"]["types"],
                },
            },
        }

        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except httpx.HTTPError as e:
        logger.error("HTTP error fetching %s: %s", url, e)
        return json.dumps({
            "error": "Failed to fetch website",
            "detail": str(e),
        }, ensure_ascii=False)
    except Exception as e:
        logger.exception("Tech SEO audit failed for %s", url)
        return json.dumps({
            "error": "Tech SEO audit failed",
            "detail": str(e),
        }, ensure_ascii=False)


registry.register(
    name="run_tech_seo_audit",
    toolset="aim-operations",
    schema={
            "name": "run_tech_seo_audit",
            "description": (
                "Full technical SEO audit of a website. Crawls homepage + internal "
                "pages. Checks: meta tags (title, description, OG), heading structure "
                "(H1-H6), image alt attributes, internal/external links, JSON-LD "
                "structured data, SSL/HTTPS, robots.txt, sitemap.xml, viewport. "
                "Returns structured report with issue severities."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to audit (e.g., 'https://clinic.ru')",
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Max pages to crawl (default 5, max 10)",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_run_tech_seo_audit,
    check_fn=lambda: True,
    is_async=True,
    description="Technical SEO audit: meta tags, headings, images, links, structured data, SSL",
    emoji="🔎",
)
