"""SeoAuditor — basic SEO audit without paid APIs.

Uses httpx + BeautifulSoup to check:
- Title, meta description, H1-H3 structure
- SSL, viewport, canonical, robots.txt, sitemap.xml
- OG tags, page load time, broken internal links
- Produces score 0-100 with concrete issues list.

TTL: 7 days (SEO changes slowly).
"""

import logging
import time
import urllib.parse
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .models import SeoAuditResult

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)

_TITLE_MAX = 60
_DESC_MIN = 70
_DESC_MAX = 160


class SeoAuditor:
    """Basic SEO auditor — no paid APIs, no Playwright."""

    def __init__(self, timeout: float = 8.0, cache_ttl: int = 604800) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            follow_redirects=True,
        )
        self._cache: dict[str, tuple[float, SeoAuditResult]] = {}
        self._cache_ttl = cache_ttl

    def close(self) -> None:
        self._client.close()

    def audit(self, url: str) -> SeoAuditResult:
        # Check cache
        cached = self._cache_get(url)
        if cached is not None:
            return cached

        result = SeoAuditResult(url=url, score=0)
        start = time.monotonic()

        try:
            resp = self._client.get(url)
            result.load_time_ms = int((time.monotonic() - start) * 1000)

            # SSL check
            result.has_ssl = url.startswith("https://")

            soup = BeautifulSoup(resp.text, "html.parser")

            # Title
            title_tag = soup.find("title")
            if title_tag:
                result.title = title_tag.get_text(strip=True)
                result.title_length = len(result.title)
                if result.title_length > _TITLE_MAX:
                    result.issues.append(
                        f"Title too long ({result.title_length} chars, max {_TITLE_MAX})"
                    )
                if result.title_length < 10:
                    result.issues.append(
                        f"Title too short ({result.title_length} chars)"
                    )
            else:
                result.issues.append("Missing <title> tag")

            # Meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                result.meta_description = meta_desc.get("content", "")
                result.meta_description_length = len(result.meta_description)
                if result.meta_description_length < _DESC_MIN:
                    result.issues.append(
                        f"Meta description too short "
                        f"({result.meta_description_length} chars, min {_DESC_MIN})"
                    )
                if result.meta_description_length > _DESC_MAX:
                    result.issues.append(
                        f"Meta description too long "
                        f"({result.meta_description_length} chars, max {_DESC_MAX})"
                    )
            else:
                result.issues.append("Missing meta description")

            # H1-H3
            result.h1_count = len(soup.find_all("h1"))
            result.h2_count = len(soup.find_all("h2"))
            result.h3_count = len(soup.find_all("h3"))
            if result.h1_count == 0:
                result.issues.append("Missing H1 tag")
            elif result.h1_count > 1:
                result.issues.append(f"Multiple H1 tags ({result.h1_count})")
            if result.h2_count == 0:
                result.issues.append("No H2 tags found")
            if result.h3_count == 0:
                result.issues.append("No H3 tags found (recommended for structure)")

            # Viewport
            viewport = soup.find("meta", attrs={"name": "viewport"})
            result.has_viewport = viewport is not None
            if not result.has_viewport:
                result.issues.append(
                    "Missing viewport meta tag (not mobile-friendly)"
                )

            # Canonical
            canonical = soup.find("link", rel="canonical")
            result.has_canonical = canonical is not None
            if not result.has_canonical:
                result.issues.append("Missing canonical link")

            # OG tags
            og_title = soup.find("meta", property="og:title")
            result.has_og_tags = og_title is not None
            if not result.has_og_tags:
                result.issues.append(
                    "Missing Open Graph tags (social sharing)"
                )

            # Parse base URL once for reuse across robots.txt, sitemap, and link checks
            base = urllib.parse.urlparse(url)
            base_domain = base.netloc

            # robots.txt
            try:
                robots_url = f"{base.scheme}://{base.netloc}/robots.txt"
                robots_resp = self._client.get(robots_url)
                result.has_robots_txt = robots_resp.status_code == 200
            except Exception:
                pass
            if not result.has_robots_txt:
                result.issues.append("Missing robots.txt")

            # sitemap.xml
            try:
                sitemap_url = f"{base.scheme}://{base.netloc}/sitemap.xml"
                sitemap_resp = self._client.get(sitemap_url)
                result.has_sitemap = sitemap_resp.status_code == 200
            except Exception:
                pass
            if not result.has_sitemap:
                result.issues.append("Missing sitemap.xml")

            # Broken internal links (sample up to 10)
            result.pages_scraped = 1
            links = soup.find_all("a", href=True)
            internal_links = []
            for link in links[:30]:
                href = link["href"]
                if href.startswith("/"):
                    href = f"{base.scheme}://{base_domain}{href}"
                    internal_links.append(href)
                elif "://" in href:
                    # Absolute URL — check if same domain via proper hostname extraction
                    try:
                        if urllib.parse.urlparse(href).netloc == base_domain:
                            internal_links.append(href)
                    except Exception:
                        pass
                else:
                    # Relative URL (e.g., "about.html", "./page")
                    resolved = urllib.parse.urljoin(
                        f"{base.scheme}://{base_domain}/", href
                    )
                    internal_links.append(resolved)

            for link in internal_links[:10]:
                try:
                    lr = self._client.head(link, timeout=3.0)
                    if lr.status_code >= 400:
                        result.broken_links.append(
                            f"{link} → {lr.status_code}"
                        )
                except Exception:
                    result.broken_links.append(f"{link} → unreachable")

            if result.broken_links:
                result.issues.append(
                    f"Found {len(result.broken_links)} broken internal links"
                )

            # Score calculation
            result.score = self._calculate_score(result)

        except httpx.HTTPError as e:
            result.error = f"HTTP error: {e}"
            result.score = 0
        except Exception as e:
            result.error = f"Unexpected error: {e}"
            result.score = 0

        self._cache_set(url, result)
        return result

    def _calculate_score(self, r: SeoAuditResult) -> int:
        score = 100
        if not r.title:
            score -= 20
        elif r.title_length > _TITLE_MAX:
            score -= 10
        if not r.meta_description:
            score -= 15
        elif r.meta_description_length < _DESC_MIN:
            score -= 5
        elif r.meta_description_length > _DESC_MAX:
            score -= 5
        if r.h1_count == 0:
            score -= 15
        elif r.h1_count > 1:
            score -= 5
        if not r.has_viewport:
            score -= 10
        if not r.has_ssl:
            score -= 10
        if not r.has_canonical:
            score -= 5
        if not r.has_og_tags:
            score -= 5
        if not r.has_robots_txt:
            score -= 3
        if not r.has_sitemap:
            score -= 3
        if r.broken_links:
            score -= min(len(r.broken_links) * 2, 15)
        if r.load_time_ms:
            lt = r.load_time_ms
            if lt > 3000:
                score -= 15
            elif lt > 1500:
                score -= 5
        return max(0, score)

    def _cache_get(self, key: str) -> Optional[SeoAuditResult]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self._cache_ttl:
            del self._cache[key]
            return None
        return value

    def _cache_set(self, key: str, value: SeoAuditResult) -> None:
        self._cache[key] = (time.monotonic(), value)
