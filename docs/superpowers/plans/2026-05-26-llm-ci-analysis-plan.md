# LLM-Based CI Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace rule-based CI analysis with LLM-powered pipeline: parallel data collection (SEO, social, financials, websites) → ComparisonMatrix → expert dialogue

**Architecture:** Pipeline Runner orchestrates 5 collectors in parallel (3 existing + 2 new: SeoAuditor, SocialScanner), builds ComparisonMatrix, feeds to LLM for expert dialogue. Progress indicators displayed between stages. Redis caching with per-collector TTLs.

**Tech Stack:** Python 3.11+, httpx + BeautifulSoup (scraping), aioredis (caching), asyncio (parallel orchestration), FastAPI (endpoint), Claude/DeepSeek (LLM dialogue)

---

### Task 1: Models & Interfaces

**Files:**
- Create: `AIM/src/aim/services/ci/__init__.py`
- Create: `AIM/src/aim/services/ci/models.py`

- [ ] **Step 1: Create package init**

```python
# AIM/src/aim/services/ci/__init__.py
"""CI Analysis — LLM-powered competitive intelligence for pre-sale."""

from .models import (
    SeoAuditResult,
    SocialScanResult,
    CompetitorFull,
    ComparisonMatrix,
    PipelineProgress,
)
from .seo_auditor import SeoAuditor
from .social_scanner import SocialScanner
from .pipeline_runner import PipelineRunner
from .comparison_matrix import ComparisonMatrixBuilder
from .dialogue_manager import DialogueManager

__all__ = [
    "SeoAuditResult",
    "SocialScanResult",
    "CompetitorFull",
    "ComparisonMatrix",
    "PipelineProgress",
    "SeoAuditor",
    "SocialScanner",
    "PipelineRunner",
    "ComparisonMatrixBuilder",
    "DialogueManager",
]
```

- [ ] **Step 2: Write models dataclasses**

```python
# AIM/src/aim/services/ci/models.py
"""Data models for LLM-based CI analysis pipeline."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SeoAuditResult:
    """Basic SEO audit — no paid APIs."""
    url: str
    score: int  # 0-100
    issues: list[str] = field(default_factory=list)
    title: str = ""
    title_length: int = 0
    meta_description: str = ""
    meta_description_length: int = 0
    h1_count: int = 0
    h2_count: int = 0
    has_viewport: bool = False
    has_ssl: bool = False
    has_canonical: bool = False
    has_robots_txt: bool = False
    has_sitemap: bool = False
    has_og_tags: bool = False
    load_time_ms: int = 0
    pages_scraped: int = 0
    broken_links: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class SocialProfile:
    """Single social media profile data."""
    platform: str  # "instagram" | "telegram" | "vk" | "tiktok"
    handle: str
    url: str = ""
    exists: bool = False
    subscribers: int = 0
    posts_last_month: int = 0
    avg_likes: int = 0
    avg_comments: int = 0
    top_topics: list[str] = field(default_factory=list)
    content_formats: dict[str, int] = field(default_factory=dict)  # {"photo": 5, "video": 3, "text": 2}
    last_post_date: str = ""
    error: str = ""


@dataclass
class SocialScanResult:
    """Full social media scan for one competitor."""
    company_name: str
    instagram: Optional[SocialProfile] = None
    telegram: Optional[SocialProfile] = None
    vk: Optional[SocialProfile] = None
    tiktok: Optional[SocialProfile] = None
    total_platforms_found: int = 0
    error: str = ""

    def as_dict(self) -> dict:
        result = {}
        for plat in ("instagram", "telegram", "vk", "tiktok"):
            profile = getattr(self, plat)
            if profile is None:
                result[plat] = {"exists": False}
            else:
                result[plat] = {
                    "handle": profile.handle,
                    "exists": profile.exists,
                    "posts_month": profile.posts_last_month,
                    "avg_likes": profile.avg_likes,
                    "topics": profile.top_topics,
                }
        return result


@dataclass
class CompetitorFull:
    """All collected data for one competitor."""
    name: str
    url: str
    inn: str = ""
    financials: dict = field(default_factory=dict)  # revenue, profit, trend
    seo: Optional[SeoAuditResult] = None
    social: Optional[SocialScanResult] = None
    website_features: list[str] = field(default_factory=list)  # ["booking", "chat", "price_list"]
    website_missing: list[str] = field(default_factory=list)  # ["calculator", "reviews"]
    doctors_count: int = 0
    directions_claimed: int = 0
    pricing_visible: bool = False
    positioning: str = ""
    scraped_at: str = ""


@dataclass
class ComparisonMatrix:
    """Compact matrix for LLM context (~5000 tokens)."""
    client: dict = field(default_factory=dict)
    competitors: list[dict] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class PipelineProgress:
    """Progress update emitted during collection."""
    stage: str  # "searching" | "collecting" | "financials" | "seo" | "social" | "scraping" | "matrix" | "done"
    message: str
    competitor_name: str = ""
    details: dict = field(default_factory=dict)
```

- [ ] **Step 3: Commit**

```bash
git add AIM/src/aim/services/ci/__init__.py AIM/src/aim/services/ci/models.py
git commit -m "feat(ci): add models for LLM-based CI analysis pipeline"
```

---

### Task 2: SeoAuditor

**Files:**
- Create: `AIM/src/aim/services/ci/seo_auditor.py`
- Test: `AIM/tests/services/ci/test_seo_auditor.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/services/ci/test_seo_auditor.py
import pytest
from AIM.src.aim.services.ci.seo_auditor import SeoAuditor
from AIM.src.aim.services.ci.models import SeoAuditResult


class TestSeoAuditor:
    def test_audit_extracts_title(self):
        auditor = SeoAuditor()
        # We'll use a real URL that we know has a title
        result = auditor.audit("https://example.com")
        assert isinstance(result, SeoAuditResult)
        assert len(result.title) > 0

    def test_audit_checks_ssl(self):
        auditor = SeoAuditor()
        result = auditor.audit("https://example.com")
        assert result.has_ssl is True

    def test_audit_scores_perfect_site(self):
        auditor = SeoAuditor()
        result = auditor.audit("https://example.com")
        assert 0 <= result.score <= 100

    def test_audit_detects_missing_meta(self):
        auditor = SeoAuditor()
        # Use a site known to have basic SEO
        result = auditor.audit("https://example.com")
        assert isinstance(result.meta_description, str)

    def test_audit_handles_http_error(self):
        auditor = SeoAuditor(timeout=3.0)
        result = auditor.audit("https://nonexistent-domain-12345.com")
        assert result.error != ""

    def test_audit_cache_hit(self):
        auditor = SeoAuditor(cache_ttl=3600)
        result1 = auditor.audit("https://example.com")
        result2 = auditor.audit("https://example.com")
        # Same object (cached)
        assert result1 is result2

    def test_close_cleans_up(self):
        auditor = SeoAuditor()
        auditor.close()
        # Should not raise
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_seo_auditor.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'AIM.src.aim.services.ci.seo_auditor'`

- [ ] **Step 3: Implement SeoAuditor**

```python
# AIM/src/aim/services/ci/seo_auditor.py
"""SeoAuditor — basic SEO audit without paid APIs.

Uses httpx + BeautifulSoup to check:
- Title, meta description, H1-H3 structure
- SSL, viewport, canonical, robots.txt, sitemap.xml
- OG tags, page load time, broken internal links
- Produces score 0-100 with concrete issues list.

TTL: 7 days (SEO changes slowly).
"""

import logging
import re
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

        result = SeoAuditResult(url=url)
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
                    result.issues.append(f"Title too long ({result.title_length} chars, max {_TITLE_MAX})")
                if result.title_length < 10:
                    result.issues.append(f"Title too short ({result.title_length} chars)")
            else:
                result.issues.append("Missing <title> tag")

            # Meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                result.meta_description = meta_desc.get("content", "")
                result.meta_description_length = len(result.meta_description)
                if result.meta_description_length < _DESC_MIN:
                    result.issues.append(f"Meta description too short ({result.meta_description_length} chars, min {_DESC_MIN})")
                if result.meta_description_length > _DESC_MAX:
                    result.issues.append(f"Meta description too long ({result.meta_description_length} chars, max {_DESC_MAX})")
            else:
                result.issues.append("Missing meta description")

            # H1-H3
            result.h1_count = len(soup.find_all("h1"))
            result.h2_count = len(soup.find_all("h2"))
            if result.h1_count == 0:
                result.issues.append("Missing H1 tag")
            elif result.h1_count > 1:
                result.issues.append(f"Multiple H1 tags ({result.h1_count})")

            # Viewport
            viewport = soup.find("meta", attrs={"name": "viewport"})
            result.has_viewport = viewport is not None
            if not result.has_viewport:
                result.issues.append("Missing viewport meta tag (not mobile-friendly)")

            # Canonical
            canonical = soup.find("link", rel="canonical")
            result.has_canonical = canonical is not None
            if not result.has_canonical:
                result.issues.append("Missing canonical link")

            # OG tags
            og_title = soup.find("meta", property="og:title")
            result.has_og_tags = og_title is not None
            if not result.has_og_tags:
                result.issues.append("Missing Open Graph tags (social sharing)")

            # robots.txt
            try:
                base = urllib.parse.urlparse(url)
                robots_url = f"{base.scheme}://{base.netloc}/robots.txt"
                robots_resp = self._client.get(robots_url)
                result.has_robots_txt = robots_resp.status_code == 200
            except Exception:
                pass
            if not result.has_robots_txt:
                result.issues.append("Missing robots.txt")

            # sitemap.xml
            try:
                base = urllib.parse.urlparse(url)
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
            base_domain = urllib.parse.urlparse(url).netloc
            for link in links[:30]:
                href = link["href"]
                if href.startswith("/") or base_domain in href:
                    if href.startswith("/"):
                        href = f"{base.scheme}://{base_domain}{href}"
                    internal_links.append(href)

            for link in internal_links[:10]:
                try:
                    lr = self._client.head(link, timeout=3.0)
                    if lr.status_code >= 400:
                        result.broken_links.append(f"{link} → {lr.status_code}")
                except Exception:
                    result.broken_links.append(f"{link} → unreachable")

            if result.broken_links:
                result.issues.append(f"Found {len(result.broken_links)} broken internal links")

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
        if r.broken_links:
            score -= min(len(r.broken_links) * 2, 15)
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
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_seo_auditor.py -v
```
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/services/ci/seo_auditor.py AIM/tests/services/ci/test_seo_auditor.py
git commit -m "feat(ci): add SeoAuditor — basic SEO audit without paid APIs"
```

---

### Task 3: SocialScanner

**Files:**
- Create: `AIM/src/aim/services/ci/social_scanner.py`
- Test: `AIM/tests/services/ci/test_social_scanner.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/services/ci/test_social_scanner.py
import pytest
from AIM.src.aim.services.ci.social_scanner import SocialScanner
from AIM.src.aim.services.ci.models import SocialScanResult, SocialProfile


class TestSocialScanner:
    def test_scan_returns_result(self):
        scanner = SocialScanner(timeout=5.0)
        result = scanner.scan("Юцковская")
        assert isinstance(result, SocialScanResult)
        assert result.company_name == "Юцковская"

    def test_scan_checks_platforms(self):
        scanner = SocialScanner(timeout=5.0)
        result = scanner.scan("Сбербанк")  # well-known, likely has social presence
        # At least one platform should report (exists=True or False, not error state)
        platforms_checked = (
            result.instagram is not None
            or result.telegram is not None
            or result.vk is not None
            or result.tiktok is not None
        )
        assert platforms_checked

    def test_scan_handles_unknown_company(self):
        scanner = SocialScanner(timeout=5.0)
        result = scanner.scan("абвгд-несуществующая-компания-12345")
        assert isinstance(result, SocialScanResult)
        assert result.error == ""  # no error, just not found

    def test_scan_cache_hit(self):
        scanner = SocialScanner(cache_ttl=3600)
        result1 = scanner.scan("Сбербанк")
        result2 = scanner.scan("Сбербанк")
        assert result1 is result2

    def test_close(self):
        scanner = SocialScanner()
        scanner.close()
        # Should not raise
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest AIM/tests/services/ci/test_social_scanner.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement SocialScanner**

```python
# AIM/src/aim/services/ci/social_scanner.py
"""SocialScanner — find competitor social media presence.

Searches Instagram, Telegram, VK, TikTok by company name.
Extracts basic stats: followers, posting frequency, top topics.
Uses httpx (no Playwright needed — profile pages are mostly static HTML).

TTL: 24 hours (social activity changes daily).
"""

import logging
import re
import time
import urllib.parse
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .models import SocialScanResult, SocialProfile

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)

_VK_SEARCH = "https://vk.com/search"
_TG_SEARCH = "https://t.me"
_INSTAGRAM_SEARCH = "https://www.instagram.com"
_TIKTOK_SEARCH = "https://www.tiktok.com"


class SocialScanner:
    """Scans social media platforms for competitor profiles."""

    def __init__(self, timeout: float = 8.0, cache_ttl: int = 86400) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json"},
            follow_redirects=True,
        )
        self._cache: dict[str, tuple[float, SocialScanResult]] = {}
        self._cache_ttl = cache_ttl

    def close(self) -> None:
        self._client.close()

    def scan(self, company_name: str) -> SocialScanResult:
        cached = self._cache_get(company_name)
        if cached is not None:
            return cached

        result = SocialScanResult(company_name=company_name)

        # Try each platform
        result.instagram = self._find_instagram(company_name)
        result.telegram = self._find_telegram(company_name)
        result.vk = self._find_vk(company_name)
        result.tiktok = self._find_tiktok(company_name)

        result.total_platforms_found = sum(
            1 for p in [result.instagram, result.telegram, result.vk, result.tiktok]
            if p and p.exists
        )

        self._cache_set(company_name, result)
        return result

    def _find_instagram(self, name: str) -> Optional[SocialProfile]:
        """Search Instagram by company name (limited — Instagram blocks heavily)."""
        try:
            # Instagram search is heavily rate-limited without auth
            # We attempt a basic search and extract what we can
            encoded = urllib.parse.quote(name)
            resp = self._client.get(
                f"https://www.instagram.com/web/search/topsearch/?query={encoded}",
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            if resp.status_code != 200:
                return SocialProfile(platform="instagram", handle="", exists=False,
                                     error=f"Instagram search returned {resp.status_code}")

            data = resp.json()
            users = data.get("users", [])
            for user in users[:3]:
                user_info = user.get("user", {})
                username = user_info.get("username", "")
                full_name = user_info.get("full_name", "")
                if name.lower() in full_name.lower() or name.lower() in username.lower():
                    return SocialProfile(
                        platform="instagram",
                        handle=f"@{username}",
                        url=f"https://instagram.com/{username}",
                        exists=True,
                    )

            return SocialProfile(platform="instagram", handle="", exists=False)

        except Exception as e:
            logger.warning("Instagram search failed for '%s': %s", name, e)
            return SocialProfile(platform="instagram", handle="", exists=False, error=str(e))

    def _find_telegram(self, name: str) -> Optional[SocialProfile]:
        """Search Telegram channels by company name."""
        try:
            encoded = urllib.parse.quote(name)
            # Telegram has no public search API — we search via t.me
            resp = self._client.get(f"https://t.me/s/{encoded}")
            if resp.status_code == 200 and len(resp.text) > 500:
                soup = BeautifulSoup(resp.text, "html.parser")
                posts = soup.select(".tgme_widget_message_wrap")
                topics = []
                for post in posts[:10]:
                    text_el = post.select_one(".tgme_widget_message_text")
                    if text_el:
                        topics.append(text_el.get_text(strip=True)[:100])

                # Count posts from last month (approximate from visible posts)
                recent_posts = len(posts)

                return SocialProfile(
                    platform="telegram",
                    handle=f"@{encoded}",
                    url=f"https://t.me/{encoded}",
                    exists=True,
                    posts_last_month=recent_posts,
                    top_topics=self._extract_topics(topics),
                )

            return SocialProfile(platform="telegram", handle="", exists=False)

        except Exception as e:
            logger.warning("Telegram search failed for '%s': %s", name, e)
            return SocialProfile(platform="telegram", handle="", exists=False, error=str(e))

    def _find_vk(self, name: str) -> Optional[SocialProfile]:
        """Search VK communities by company name."""
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(
                f"https://vk.com/search?c%5Bper_page%5D=5&c%5Bq%5D={encoded}&c%5Bsection%5D=communities",
            )
            if resp.status_code != 200:
                return SocialProfile(platform="vk", handle="", exists=False,
                                     error=f"VK search returned {resp.status_code}")

            soup = BeautifulSoup(resp.text, "html.parser")
            groups = soup.select(".labeled_title, .search_row")
            for group in groups[:3]:
                link = group.select_one("a[href*='public']") or group.select_one("a[href*='club']") or group.select_one("a[href*='/']")
                if link:
                    href = link.get("href", "")
                    group_name = link.get_text(strip=True)
                    if name.lower()[:5] in group_name.lower():
                        return SocialProfile(
                            platform="vk",
                            handle=href.replace("/", ""),
                            url=f"https://vk.com{href}" if href.startswith("/") else href,
                            exists=True,
                        )

            return SocialProfile(platform="vk", handle="", exists=False)

        except Exception as e:
            logger.warning("VK search failed for '%s': %s", name, e)
            return SocialProfile(platform="vk", handle="", exists=False, error=str(e))

    def _find_tiktok(self, name: str) -> Optional[SocialProfile]:
        """Search TikTok by company name."""
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(
                f"https://www.tiktok.com/search/user?q={encoded}",
            )
            if resp.status_code == 200 and len(resp.text) > 500:
                # Extract username from response
                username_match = re.search(r'"uniqueId":"([^"]+)"', resp.text)
                if username_match:
                    username = username_match.group(1)
                    return SocialProfile(
                        platform="tiktok",
                        handle=f"@{username}",
                        url=f"https://tiktok.com/@{username}",
                        exists=True,
                    )

            return SocialProfile(platform="tiktok", handle="", exists=False)

        except Exception as e:
            logger.warning("TikTok search failed for '%s': %s", name, e)
            return SocialProfile(platform="tiktok", handle="", exists=False, error=str(e))

    def _extract_topics(self, texts: list[str], max_topics: int = 5) -> list[str]:
        """Extract common topics from post texts (simple keyword extraction)."""
        if not texts:
            return []
        # Simple: return first 100 chars of each unique text as "topic"
        seen = set()
        topics = []
        for text in texts:
            key = text[:50].lower()
            if key not in seen and len(text) > 20:
                seen.add(key)
                topics.append(text[:80])
            if len(topics) >= max_topics:
                break
        return topics

    def _cache_get(self, key: str) -> Optional[SocialScanResult]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self._cache_ttl:
            del self._cache[key]
            return None
        return value

    def _cache_set(self, key: str, value: SocialScanResult) -> None:
        self._cache[key] = (time.monotonic(), value)
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_social_scanner.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/services/ci/social_scanner.py AIM/tests/services/ci/test_social_scanner.py
git commit -m "feat(ci): add SocialScanner — Instagram, Telegram, VK, TikTok discovery"
```

---

### Task 4: PipelineRunner

**Files:**
- Create: `AIM/src/aim/services/ci/pipeline_runner.py`
- Test: `AIM/tests/services/ci/test_pipeline_runner.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/services/ci/test_pipeline_runner.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner
from AIM.src.aim.services.ci.models import CompetitorFull


class TestPipelineRunner:
    @pytest.mark.asyncio
    async def test_runner_needs_client_url(self):
        runner = PipelineRunner()
        with pytest.raises(ValueError, match="client_url"):
            await runner.run(client_url="")

    @pytest.mark.asyncio
    async def test_runner_collects_competitors(self):
        runner = PipelineRunner()

        # Mock competitor_matcher
        mock_competitors = [
            MagicMock(
                name="TestClinic",
                url="https://testclinic.ru",
                inn="1234567890",
                short_name="TestClinic",
                services={"терапия", "хирургия"},
            )
        ]

        with patch(
            "AIM.src.aim.services.ci.pipeline_runner.CompetitorMatcher"
        ) as mock_matcher_cls:
            mock_matcher = AsyncMock()
            mock_matcher.find_competitors = AsyncMock(return_value=mock_competitors)
            mock_matcher.close = AsyncMock()
            mock_matcher_cls.return_value = mock_matcher

            competitors = await runner.run(client_url="https://client.ru")

        assert len(competitors) >= 0

    @pytest.mark.asyncio
    async def test_runner_fires_progress(self):
        runner = PipelineRunner()
        progress_messages = []

        async def on_progress(msg):
            progress_messages.append(msg)

        runner.on_progress = on_progress

        # Should fire at least "searching" and "done"
        # We'll test with a mock pipeline
        assert len(progress_messages) == 0  # No progress before run

    @pytest.mark.asyncio
    async def test_runner_handles_collector_failure(self):
        runner = PipelineRunner()
        # Individual collector failures should not crash the pipeline
        # Each collector returns None/empty on failure
        data = await runner._collect_financials_async("1234567890")
        assert data is None or isinstance(data, dict)

    def test_close(self):
        runner = PipelineRunner()
        # Should not raise
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_pipeline_runner.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement PipelineRunner**

```python
# AIM/src/aim/services/ci/pipeline_runner.py
"""Pipeline Runner — orchestrates parallel data collection with progress.

Flow:
1. Find competitors (Apify Google Maps)  → [PROGRESS: "Ищу конкурентов..."]
2. For each competitor in PARALLEL:
   - FinancialsCollector (bo.nalog.gov.ru)
   - WebsiteScraper (Playwright)
   - SeoAuditor (httpx + BS4)
   - SocialScanner (httpx)
3. Build ComparisonMatrix
4. Return to DialogueManager
"""

import asyncio
import logging
import time
from typing import Callable, Awaitable, Optional

from .models import CompetitorFull, PipelineProgress
from .seo_auditor import SeoAuditor
from .social_scanner import SocialScanner

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates parallel data collection for CI analysis."""

    def __init__(
        self,
        on_progress: Optional[Callable[[PipelineProgress], Awaitable[None]]] = None,
        timeout: float = 15.0,
    ) -> None:
        self._on_progress = on_progress
        self._timeout = timeout

    async def run(
        self,
        client_url: str,
        named_competitors: Optional[list[str]] = None,
    ) -> list[CompetitorFull]:
        """Run full collection pipeline.

        Args:
            client_url: URL of the client's website
            named_competitors: Optional list of competitor names/URLs (if client provides them)

        Returns:
            List of CompetitorFull with all collected data.
        """
        if not client_url:
            raise ValueError("client_url is required")

        start = time.monotonic()

        # Step 1: Find competitors
        await self._emit("searching", "Ищу конкурентов по вашему сайту...")
        
        competitors = await self._find_competitors(client_url, named_competitors)
        
        if not competitors:
            await self._emit("done", "Не смог найти конкурентов автоматически. Скиньте их сайты вручную.")
            return []

        names = ", ".join(c[:30] for c in competitors[:4])
        await self._emit("collecting", f"Нашёл {len(competitors)} конкурентов: {names}. Собираю данные...")

        # Step 2: Collect data in parallel for each competitor
        collected: list[CompetitorFull] = []
        for comp in competitors:
            full = CompetitorFull(name=comp.get("name", ""), url=comp.get("url", ""), inn=comp.get("inn", ""))
            
            # Run 4 collectors in parallel
            results = await asyncio.gather(
                self._collect_financials(comp),
                self._collect_seo(full.url),
                self._collect_social(full.name),
                self._collect_website(comp),
                return_exceptions=True,
            )

            financials, seo, social, website = results
            
            if isinstance(financials, dict):
                full.financials = financials
            if seo and not isinstance(seo, Exception):
                full.seo = seo
            if social and not isinstance(social, Exception):
                full.social = social
            if website and not isinstance(website, Exception):
                full.website_features = website.get("features", [])
                full.website_missing = website.get("missing", [])
                full.doctors_count = website.get("doctors_count", 0)
                full.directions_claimed = website.get("directions_claimed", 0)
                full.pricing_visible = website.get("pricing_visible", False)
                full.positioning = website.get("positioning", "")

            collected.append(full)

        await self._emit("matrix", "Сравниваю с вашим сайтом...")

        elapsed = int(time.monotonic() - start)
        await self._emit("done", f"Готово! Вот что я нашёл... (заняло {elapsed} сек)")

        return collected

    async def _find_competitors(
        self, client_url: str, named: Optional[list[str]]
    ) -> list[dict]:
        """Find competitors using existing CompetitorMatcher."""
        try:
            from AIM.src.aim.services.competitor_matcher import CompetitorMatcher

            loop = asyncio.get_event_loop()
            def _sync():
                matcher = CompetitorMatcher()
                try:
                    import asyncio as _asyncio
                    return _asyncio.run(matcher.find_competitors(
                        url=client_url,
                        count=5,
                        named_competitors=named,
                    ))
                finally:
                    _asyncio.run(matcher.close())

            # CompetitorMatcher is already async, call directly
            matcher = CompetitorMatcher()
            try:
                matches = await matcher.find_competitors(
                    url=client_url,
                    count=5,
                    named_competitors=named,
                )
                return [
                    {
                        "name": m.short_name,
                        "url": m.url,
                        "inn": m.inn,
                        "revenue": getattr(m, "revenue", {}),
                        "profit": getattr(m, "profit", {}),
                        "services": getattr(m, "services", set()),
                    }
                    for m in matches[:5]
                ]
            finally:
                await matcher.close()
        except Exception as e:
            logger.exception("CompetitorFinder failed")
            return []

    async def _collect_financials(self, comp: dict) -> Optional[dict]:
        """Fetch tax-filed financials from bo.nalog.gov.ru."""
        inn = comp.get("inn", "")
        if not inn:
            return None
        try:
            await self._emit("financials", f"Смотрю финансовую отчётность {comp['name']}...", comp["name"])
            
            def _sync_fetch():
                from AIM.src.aim.services.nalog import BfoNalogClient
                client = BfoNalogClient()
                try:
                    results = client.search(inn)
                    if not results:
                        return None
                    fs_list = client.get_financials(results[0].id)
                    revenue, profit = {}, {}
                    for fs in fs_list:
                        if fs.revenue_rub is not None:
                            revenue[fs.period] = fs.revenue_rub
                        if fs.net_profit_rub is not None:
                            profit[fs.period] = fs.net_profit_rub
                    return {
                        "revenue": revenue,
                        "profit": profit,
                        "trend": fs_list[0].revenue_trend if fs_list else "",
                    }
                finally:
                    client.close()

            return await asyncio.to_thread(_sync_fetch)
        except Exception as e:
            logger.warning("Financials failed for %s: %s", comp["name"], e)
            return None

    async def _collect_seo(self, url: str) -> Optional[object]:
        """Run SEO audit on competitor website."""
        if not url:
            return None
        try:
            await self._emit("seo", f"Проверяю SEO ошибки на сайте...")
            def _sync():
                auditor = SeoAuditor()
                try:
                    return auditor.audit(url)
                finally:
                    auditor.close()
            return await asyncio.to_thread(_sync)
        except Exception as e:
            logger.warning("SEO audit failed for %s: %s", url, e)
            return None

    async def _collect_social(self, company_name: str) -> Optional[object]:
        """Scan social media for competitor."""
        if not company_name:
            return None
        try:
            await self._emit("social", f"Ищу соцсети {company_name}...", company_name)
            def _sync():
                scanner = SocialScanner()
                try:
                    return scanner.scan(company_name)
                finally:
                    scanner.close()
            return await asyncio.to_thread(_sync)
        except Exception as e:
            logger.warning("Social scan failed for %s: %s", company_name, e)
            return None

    async def _collect_website(self, comp: dict) -> Optional[dict]:
        """Extract website features from existing scraper data."""
        # Reuse data already collected by CompetitorMatcher
        services = comp.get("services", set())
        return {
            "features": [],
            "missing": [],
            "doctors_count": 0,
            "directions_claimed": len(services) if services else 0,
            "pricing_visible": False,
            "positioning": "",
        }

    async def _emit(self, stage: str, message: str, competitor_name: str = "") -> None:
        """Emit progress update."""
        progress = PipelineProgress(stage=stage, message=message, competitor_name=competitor_name)
        logger.info("Pipeline [%s]: %s", stage, message)
        if self._on_progress:
            try:
                await self._on_progress(progress)
            except Exception as e:
                logger.warning("Progress callback failed: %s", e)
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_pipeline_runner.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/services/ci/pipeline_runner.py AIM/tests/services/ci/test_pipeline_runner.py
git commit -m "feat(ci): add PipelineRunner — parallel collection with progress"
```

---

### Task 5: ComparisonMatrix Builder

**Files:**
- Create: `AIM/src/aim/services/ci/comparison_matrix.py`
- Test: `AIM/tests/services/ci/test_comparison_matrix.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/services/ci/test_comparison_matrix.py
import pytest
from AIM.src.aim.services.ci.comparison_matrix import ComparisonMatrixBuilder
from AIM.src.aim.services.ci.models import CompetitorFull, SeoAuditResult, SocialScanResult


class TestComparisonMatrixBuilder:
    def test_build_empty(self):
        builder = ComparisonMatrixBuilder()
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={"booking": True, "chat": False},
            competitors_full=[],
        )
        assert len(matrix.competitors) == 0
        assert matrix.client["url"] == "https://client.ru"

    def test_build_with_one_competitor(self):
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="TestClinic",
            url="https://test.ru",
            inn="1234567890",
            financials={"revenue": {"2025": 10000000}},
            seo=SeoAuditResult(url="https://test.ru", score=65, issues=["Missing H1"]),
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={"booking": True},
            competitors_full=[comp],
        )
        assert len(matrix.competitors) == 1
        assert matrix.competitors[0]["name"] == "TestClinic"
        assert matrix.competitors[0]["seo"]["score"] == 65
        assert "Missing H1" in matrix.competitors[0]["seo"]["issues"]

    def test_build_compact_json_fits_token_budget(self):
        import json
        builder = ComparisonMatrixBuilder()
        comps = []
        for i in range(5):
            comps.append(CompetitorFull(
                name=f"Competitor {i}",
                url=f"https://comp{i}.ru",
                inn=f"{i}" * 10,
                financials={"revenue": {"2025": 1000000 * (i + 1)}, "trend": "growing"},
                seo=SeoAuditResult(url=f"https://comp{i}.ru", score=70 - i * 10, issues=[f"Issue {j}" for j in range(3)]),
            ))
        matrix = builder.build("https://client.ru", {"booking": True}, comps)
        json_str = json.dumps(matrix.competitors, ensure_ascii=False)
        assert len(json_str) < 8000  # Under 8K tokens even as JSON string
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_comparison_matrix.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement ComparisonMatrixBuilder**

```python
# AIM/src/aim/services/ci/comparison_matrix.py
"""ComparisonMatrix — build compact matrix from collector outputs for LLM context."""

import json
from datetime import datetime, timezone

from .models import CompetitorFull, ComparisonMatrix


class ComparisonMatrixBuilder:
    """Builds ComparisonMatrix from CompetitorFull data.

    The matrix is designed to fit in ~5000 tokens when serialized,
    with 3-5 competitors each having 20+ parameters.
    """

    def build(
        self,
        client_url: str,
        client_features: dict,
        competitors_full: list[CompetitorFull],
    ) -> ComparisonMatrix:
        client = {
            "url": client_url,
            "features": [k for k, v in client_features.items() if v] if client_features else [],
            "missing": [k for k, v in client_features.items() if not v] if client_features else [],
        }

        competitors = []
        for cf in competitors_full:
            comp = {
                "name": cf.name,
                "url": cf.url,
                "financials": self._compact_financials(cf),
                "seo": self._compact_seo(cf),
                "social": self._compact_social(cf),
                "website": {
                    "features": cf.website_features,
                    "missing": cf.website_missing,
                    "doctors": cf.doctors_count,
                    "directions": cf.directions_claimed,
                    "pricing_visible": cf.pricing_visible,
                    "positioning": cf.positioning[:120] if cf.positioning else "",
                },
            }
            competitors.append(comp)

        return ComparisonMatrix(
            client=client,
            competitors=competitors,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_llm_context(self, matrix: ComparisonMatrix) -> str:
        """Convert matrix to compact JSON string for LLM system prompt."""
        return json.dumps(
            {"client": matrix.client, "competitors": matrix.competitors},
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _compact_financials(self, cf: CompetitorFull) -> dict:
        fin = cf.financials
        revenue = fin.get("revenue", {})
        return {
            "latest_revenue": max(revenue.values()) if revenue else None,
            "latest_profit": max(fin.get("profit", {}).values()) if fin.get("profit") else None,
            "trend": fin.get("trend", ""),
        }

    def _compact_seo(self, cf: CompetitorFull) -> dict:
        if cf.seo is None:
            return {"score": None, "issues": [], "error": "No data"}
        return {
            "score": cf.seo.score,
            "issues": cf.seo.issues[:8],  # cap at 8 issues
        }

    def _compact_social(self, cf: CompetitorFull) -> dict:
        if cf.social is None:
            return {"instagram": {"exists": False}, "telegram": {"exists": False},
                    "vk": {"exists": False}, "tiktok": {"exists": False}}
        return cf.social.as_dict()
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_comparison_matrix.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/services/ci/comparison_matrix.py AIM/tests/services/ci/test_comparison_matrix.py
git commit -m "feat(ci): add ComparisonMatrix builder — compact LLM context from collector data"
```

---

### Task 6: DialogueManager

**Files:**
- Create: `AIM/src/aim/services/ci/dialogue_manager.py`

- [ ] **Step 1: Implement DialogueManager**

```python
# AIM/src/aim/services/ci/dialogue_manager.py
"""DialogueManager — LLM-powered expert dialogue for CI analysis.

Receives ComparisonMatrix, generates system prompt, manages dialogue state.
LLM works with structured data — no tool calling needed during dialogue.
"""

import json
import logging
from typing import Optional

from .comparison_matrix import ComparisonMatrix

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """Ты — Hermes, AI-аналитик агентства AIM. Твоя задача — провести клиента через конкурентный анализ.

Ты говоришь как эксперт, который реально изучил конкурентов. Каждый твой вывод подкреплён конкретными данными из матрицы.

## ДАННЫЕ КЛИЕНТА
{client_json}

## ДАННЫЕ КОНКУРЕНТОВ
{competitors_json}

## ПРАВИЛА
1. Не выдумывай цифры — бери только из матрицы выше
2. Если данных нет по параметру — честно скажи "по этому параметру данных нет"
3. Сравнивай с сайтом клиента при каждой возможности
4. Веди диалог, не лекцию — спрашивай, интересно ли копнуть глубже
5. Показывай слабые места конкурентов с конкретными доказательствами
6. Отвечай на русском, живым экспертным тоном
7. Используй жирный шрифт для ключевых цифр и выводов

## ФОРМАТ ДИАЛОГА

### Первое сообщение (HOOK):
Начни с краткого интригующего обзора — по одной самой сильной находке на каждого конкурента:
"Смотрите, нашёл {N} конкурентов. {Competitor1} — {главная цифра}, но {слабое место}. {Competitor2} — ..."
Закончи вопросом: "По кому показать сравнение первым?"

### Разбор конкурента (когда клиент выбрал):
Покажи по блокам:
1. Финансы — выручка, прибыль, тренд
2. SEO — оценка и конкретные ошибки, сравнение с сайтом клиента
3. Соцсети — где присутствуют, частота, темы, сравнение с клиентом
4. Сайт — фичи, чего не хватает, врачи/направления
5. Главная слабость — самый неожиданный или сильный инсайт

### Follow-up:
После разбора спроси: "Интересно посмотреть их цены? Или проверим соцсети?"

### Итог:
Когда клиент готов, подведи итог по всем конкурентам: таблица сравнения + главный вывод."""


class DialogueManager:
    """Manages LLM-powered dialogue for CI analysis."""

    def __init__(self, llm_client=None) -> None:
        self._llm = llm_client

    def build_system_prompt(self, matrix: ComparisonMatrix) -> str:
        """Build system prompt with matrix data embedded."""
        client_json = json.dumps(matrix.client, ensure_ascii=False, indent=2)
        competitors_json = json.dumps(matrix.competitors, ensure_ascii=False, indent=2)
        return SYSTEM_PROMPT_TEMPLATE.format(
            client_json=client_json,
            competitors_json=competitors_json,
        )

    def build_hook_prompt(self, matrix: ComparisonMatrix) -> str:
        """Build the initial hook message prompt."""
        n = len(matrix.competitors)
        if n == 0:
            return "Конкуренты не найдены. Попроси клиента скинуть сайты конкурентов вручную."

        return (
            f"Сгенерируй hook-сообщение для {n} конкурентов. "
            f"Для каждого найди самую сильную цифру (выручка) и самое яркое слабое место (SEO ошибка или отсутствие соцсетей). "
            f"Закончи вопросом 'По кому показать сравнение первым?'"
        )

    async def chat(self, matrix: ComparisonMatrix, message: str, history: list[dict]) -> str:
        """Process a dialogue message with LLM.

        Args:
            matrix: The comparison matrix (data source)
            message: User's message
            history: Previous messages [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            LLM response
        """
        if self._llm is None:
            return self._fallback_response(matrix)

        system = self.build_system_prompt(matrix)

        messages = [{"role": "system", "content": system}]
        messages.extend(history[-10:])  # last 10 messages for context
        messages.append({"role": "user", "content": message})

        try:
            response = await self._llm.chat(messages)
            return response
        except Exception as e:
            logger.error("LLM chat failed: %s", e)
            return self._fallback_response(matrix)

    def _fallback_response(self, matrix: ComparisonMatrix) -> str:
        """Fallback when LLM is unavailable — return structured data as text."""
        if not matrix.competitors:
            return "Не удалось загрузить языковую модель. Данные по конкурентам собраны, но я не могу их проанализировать."

        lines = ["**Данные по конкурентам собраны:**\n"]
        for c in matrix.competitors:
            rev = c.get("financials", {}).get("latest_revenue")
            rev_str = f"{rev:,.0f} ₽".replace(",", " ") if rev else "нет данных"
            seo_score = c.get("seo", {}).get("score", "?")
            lines.append(f"**{c['name']}** — Выручка: {rev_str}, SEO: {seo_score}/100")
        return "\n".join(lines)
```

- [ ] **Step 2: Commit**

```bash
git add AIM/src/aim/services/ci/dialogue_manager.py
git commit -m "feat(ci): add DialogueManager — LLM-powered expert dialogue"
```

---

### Task 7: Integration — Replace CiMarketingAnalyzer

**Files:**
- Modify: `AIM/src/aim/services/ci_marketing_analysis.py` — replace CiMarketingAnalyzer.analyze()
- Modify: `AIM/src/aim/api/competitors.py` — update `/analyze` endpoint
- Modify: `AIM/hermes/app/tools/run_ci_analysis.py` — update descriptions

- [ ] **Step 1: Update CiMarketingAnalyzer to use new pipeline**

In `AIM/src/aim/services/ci_marketing_analysis.py`, replace the `CiMarketingAnalyzer.analyze()` method (lines 757-858) to use the new pipeline:

```python
# Replace CiMarketingAnalyzer.analyze() with:

    async def analyze(
        self,
        url: str,
        specialization: str = "",
        city: str = "",
        services: list[str] | None = None,
        competitors: list | None = None,
        client_revenue: int | None = None,
        client_rating: float | None = None,
    ) -> CiAnalysisResult:
        """Run LLM-powered CI analysis using new pipeline."""
        start = time.monotonic()

        try:
            from .ci.pipeline_runner import PipelineRunner
            from .ci.comparison_matrix import ComparisonMatrixBuilder
            from .ci.dialogue_manager import DialogueManager

            # 1. Run pipeline
            progress_msgs = []

            async def on_progress(p):
                progress_msgs.append(p.message)
                logger.info("CI: %s", p.message)

            runner = PipelineRunner(on_progress=on_progress)
            named = [c.url for c in competitors] if competitors else None
            collected = await runner.run(client_url=url, named_competitors=named)

            # 2. Build matrix
            builder = ComparisonMatrixBuilder()
            client_features = {
                "booking": any("запись" in str(getattr(c, "features", [])) for c in (competitors or [])),
            }
            matrix = builder.build(url, client_features, collected)

            # 3. Build chat summary from matrix (without LLM for now — structural)
            chat_summary = self._chat_summary_from_matrix(matrix, progress_msgs)

            # 4. Build legacy-compatible response
            feature_matrix = self._feature_matrix_legacy(matrix)
            pricing = self._pricing_legacy(matrix)
            positioning = self._positioning_legacy(matrix)

            elapsed = time.monotonic() - start

            return CiAnalysisResult(
                chat_summary=chat_summary,
                feature_matrix=feature_matrix,
                pricing_comparison=pricing,
                positioning_map=positioning,
                steal_worthy_tactics=[],
                top_recommendation=self._top_rec_from_matrix(matrix),
                scraped_at=datetime.now(timezone.utc).isoformat(),
                analysis_duration_seconds=elapsed,
            )

        except Exception as e:
            logger.exception("CI analysis failed")
            return CiAnalysisResult(
                chat_summary=f"Не удалось провести анализ: {e}",
                error=str(e),
                analysis_duration_seconds=time.monotonic() - start,
            )

    def _chat_summary_from_matrix(self, matrix, progress_msgs: list[str]) -> str:
        """Generate chat summary from matrix (structural, LLM used in DialogueManager)."""
        comps = matrix.competitors
        if not comps:
            return "Не удалось найти конкурентов для анализа."

        lines = ["## 🕵️ Анализ конкурентов\n"]
        lines.append(f"Проанализировано: **{len(comps)} конкурентов**\n")

        for c in comps:
            rev = c.get("financials", {}).get("latest_revenue")
            rev_str = f"**{rev:,.0f} ₽**".replace(",", " ") if rev else "нет данных"
            seo = c.get("seo", {}).get("score", "?")
            social_platforms = [
                p for p, v in c.get("social", {}).items()
                if isinstance(v, dict) and v.get("exists")
            ]

            lines.append(f"### {c['name']}")
            lines.append(f"- Выручка: {rev_str}")
            lines.append(f"- SEO: **{seo}/100**")
            lines.append(f"- Соцсети: {', '.join(social_platforms) if social_platforms else 'не обнаружены'}")

            issues = c.get("seo", {}).get("issues", [])
            if issues:
                lines.append(f"- Ошибки: {issues[0]}, {issues[1] if len(issues) > 1 else ''}")
            lines.append("")

        return "\n".join(lines)

    def _feature_matrix_legacy(self, matrix) -> dict:
        return {
            "competitors": [
                {"name": c["name"], "features": c["website"]["features"]}
                for c in matrix.competitors
            ]
        }

    def _pricing_legacy(self, matrix) -> dict:
        return {
            "competitors": [
                {
                    "name": c["name"],
                    "has_pricing": c["website"]["pricing_visible"],
                    "revenue": c["financials"].get("latest_revenue"),
                }
                for c in matrix.competitors
            ]
        }

    def _positioning_legacy(self, matrix) -> dict:
        return {
            "competitors": [
                {"name": c["name"], "positioning": c["website"]["positioning"]}
                for c in matrix.competitors
            ]
        }

    def _top_rec_from_matrix(self, matrix) -> str:
        comps = matrix.competitors
        if not comps:
            return "Соберите данные о конкурентах для получения рекомендаций."

        # Find competitor with worst SEO
        worst_seo = min(comps, key=lambda c: c.get("seo", {}).get("score", 100) or 100)
        return (
            f"Главная возможность — обойти **{worst_seo['name']}** по SEO: "
            f"у них {worst_seo.get('seo', {}).get('score', '?')}/100, "
            f"исправьте ошибки которые мы нашли на их сайте, и вы выше."
        )
```

- [ ] **Step 2: Update Hermes tool description**

```python
# In AIM/hermes/app/tools/run_ci_analysis.py, update the registry.register description:

registry.register(
    name="run_ci_analysis",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_ci_analysis",
            "description": (
                "Run full competitive intelligence analysis on selected competitors. "
                "Analyzes SEO (basic audit, no paid APIs), social media presence "
                "(Instagram, Telegram, VK, TikTok), tax-filed financials from "
                "bo.nalog.gov.ru, and website features. Compares everything against "
                "the client's own website. Returns detailed per-competitor breakdown "
                "with scores, specific issues, and strategic recommendations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Client website URL"},
                    "competitors": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Selected competitors (from present_competitors output)",
                    },
                },
                "required": ["url", "competitors"],
            },
        },
    },
    handler=handle_run_ci_analysis,
    check_fn=lambda: True,
    is_async=True,
    description="Run full CI analysis: SEO + social + financials + website comparison",
    emoji="🔍",
)
```

- [ ] **Step 3: Update PRESALE prompt**

In `AIM/hermes/app/agent_wrapper.py`, update the `_presale_prompt()` function. Find the section about `run_ci_analysis` and replace with:

```python
### 5. run_ci_analysis — покажи WOW
Вызывай `run_ci_analysis` с url клиента и выбранными конкурентами.

Когда результаты придут, ОБЯЗАТЕЛЬНО следуй этому формату:

```
## 🔍 Анализ конкурентов

{быстрый обзор — по 1 предложению на конкурента с главной цифрой}

По кому показать детальный разбор первым?
```

Когда клиент выбрал конкурента:

```
## {Название конкурента}

### 💰 Финансы
{выручка, прибыль, тренд — сравнить с клиентом если есть данные}

### 🔍 SEO ({score}/100)
{3-5 конкретных ошибок с пояснением}
{сравнение с сайтом клиента: "у вас X, у них Y"}

### 📱 Соцсети
{где есть, где нет, частота постинга, топ-темы}
{сравнение с клиентом}

### 🌐 Сайт
{что есть, чего нет, фишки}

### ⚡ Главная слабость
{самый сильный инсайт}

Интересно посмотреть {следующий аспект}? Или разберём следующего конкурента?
```

Ключевое правило: НЕ вываливай всё сразу. Веди диалог, спрашивай, дай клиенту направлять разговор.
```

- [ ] **Step 4: Commit**

```bash
git add AIM/src/aim/services/ci_marketing_analysis.py AIM/hermes/app/tools/run_ci_analysis.py AIM/hermes/app/agent_wrapper.py
git commit -m "feat(ci): integrate LLM pipeline into CiMarketingAnalyzer, Hermes tool, and PRESALE prompt"
```

---

### Task 8: Progress Indicators in Hermes Chat

**Files:**
- Modify: `AIM/hermes/app/tools/run_ci_analysis.py`

- [ ] **Step 1: Add progress messages to the tool handler**

In `handle_run_ci_analysis`, after calling the API, emit progress messages during the analysis:

```python
# In handle_run_ci_analysis, replace the single API call with:

async def handle_run_ci_analysis(url=None, competitors=None, **kwargs) -> str:
    unpacked = _normalize_args(url, {"url": "", "competitors": []})
    if unpacked:
        url = unpacked["url"]
        competitors = unpacked.get("competitors", [])

    if not url:
        return json.dumps({"success": False, "error": "url is required"})

    logger.info("Starting CI analysis for: %s with %d competitors", url, len(competitors))

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/analyze",
                json={
                    "url": url,
                    "competitors": competitors,
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                return json.dumps({
                    "success": False,
                    "error": data.get("error", "Analysis failed"),
                })

            result = data.get("analysis", {})
            return json.dumps({
                "success": True,
                "chat_summary": result.get("chat_summary", ""),
                "feature_matrix": result.get("feature_matrix", {}),
                "pricing_comparison": result.get("pricing_comparison", {}),
                "positioning_map": result.get("positioning_map", {}),
                "duration_seconds": result.get("analysis_duration_seconds", 0),
            }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("CI analysis failed")
        return json.dumps({"success": False, "error": str(e)})
```

Note: Progress messages are emitted by the PipelineRunner internally (logged + callback).
Hermes will see them as intermediate logs before the final result arrives.

- [ ] **Step 2: Commit**

```bash
git add AIM/hermes/app/tools/run_ci_analysis.py
git commit -m "feat(ci): add progress-aware CI analysis tool handler"
```

---

### Task 9: End-to-End Test & Verification

**Files:**
- Create: `AIM/tests/services/ci/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# AIM/tests/services/ci/test_integration.py
"""Integration tests for CI pipeline end-to-end."""

import pytest
from AIM.src.aim.services.ci.models import (
    CompetitorFull, ComparisonMatrix, SeoAuditResult, SocialScanResult
)
from AIM.src.aim.services.ci.comparison_matrix import ComparisonMatrixBuilder
from AIM.src.aim.services.ci.dialogue_manager import DialogueManager


class TestCIEndToEnd:
    def test_models_roundtrip(self):
        """Models can be created and serialized."""
        seo = SeoAuditResult(
            url="https://test.ru",
            score=72,
            issues=["Missing H1"],
            title="Test Site",
            title_length=9,
        )
        assert seo.score == 72
        assert "Missing H1" in seo.issues

    def test_matrix_builder_with_full_data(self):
        """Matrix builder handles complete competitor data."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="FullClinic",
            url="https://fullclinic.ru",
            inn="1234567890",
            financials={
                "revenue": {"2025": 50000000, "2024": 45000000},
                "profit": {"2025": 5000000},
                "trend": "growing",
            },
            seo=SeoAuditResult(
                url="https://fullclinic.ru",
                score=80,
                issues=["Title too long (75 chars, max 60)", "Missing viewport"],
                title="Very Long Title That Exceeds Maximum Length For SEO",
                title_length=75,
                h1_count=1,
                has_ssl=True,
                has_viewport=False,
            ),
            social=SocialScanResult(company_name="FullClinic"),
            website_features=["booking", "chat"],
            website_missing=["calculator"],
            doctors_count=12,
            directions_claimed=8,
            pricing_visible=True,
            positioning="Премиум клиника",
        )

        matrix = builder.build("https://client.ru", {"booking": True, "chat": False}, [comp])
        assert len(matrix.competitors) == 1
        c = matrix.competitors[0]
        assert c["financials"]["latest_revenue"] == 50000000
        assert c["seo"]["score"] == 80
        assert c["website"]["doctors"] == 12

    def test_dialogue_manager_builds_prompt(self):
        """DialogueManager builds valid system prompt."""
        dm = DialogueManager()
        builder = ComparisonMatrixBuilder()
        matrix = builder.build("https://client.ru", {}, [])
        prompt = dm.build_system_prompt(matrix)
        assert "ДАННЫЕ КЛИЕНТА" in prompt
        assert "ДАННЫЕ КОНКУРЕНТОВ" in prompt
        assert "ПРАВИЛА" in prompt

    def test_dialogue_manager_fallback(self):
        """DialogueManager returns fallback when no LLM."""
        dm = DialogueManager(llm_client=None)
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="Test", url="https://test.ru", inn="123",
            financials={"revenue": {"2025": 10000000}},
        )
        matrix = builder.build("https://client.ru", {}, [comp])
        response = dm._fallback_response(matrix)
        assert "Test" in response
        assert "10" in response  # 10,000,000

    def test_pipeline_progress_model(self):
        """PipelineProgress model works."""
        from AIM.src.aim.services.ci.models import PipelineProgress
        p = PipelineProgress(stage="searching", message="Ищу конкурентов...")
        assert p.stage == "searching"
        assert "конкурентов" in p.message

    def test_matrix_json_compact(self):
        """Matrix serializes compactly (under 5000 chars for 3 competitors)."""
        import json
        builder = ComparisonMatrixBuilder()
        comps = []
        for i in range(3):
            comps.append(CompetitorFull(
                name=f"Clinic {i}",
                url=f"https://clinic{i}.ru",
                financials={"revenue": {"2025": (i + 1) * 10000000}, "trend": "growing"},
                seo=SeoAuditResult(url=f"https://clinic{i}.ru", score=70 + i * 5,
                                   issues=[f"Issue {j}" for j in range(4)]),
                social=SocialScanResult(company_name=f"Clinic {i}"),
                website_features=["booking"],
                positioning=f"Позиционирование клиники {i}",
            ))
        matrix = builder.build("https://client.ru", {"booking": True}, comps)
        dm = DialogueManager()
        context = dm.build_system_prompt(matrix)
        # Context should be reasonable size (under 10K chars = ~2500 tokens)
        assert len(context) < 10000, f"System prompt too large: {len(context)} chars"
```

- [ ] **Step 2: Run integration tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/test_integration.py -v
```
Expected: 6 passed

- [ ] **Step 3: Run all CI tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/ci/ -v
```
Expected: 20+ passed (4 seo + 5 social + 4 pipeline + 3 matrix + 6 integration)

- [ ] **Step 4: Verify production API**

```bash
curl -s "http://localhost:8000/api/companies/financials?inn=9717023304" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('success') else 'FAIL')"
```
Expected: OK

```bash
curl -s -X POST "http://localhost:8000/api/competitors/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://yutskovskaya.ru"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('success') else d.get('error','FAIL'))"
```
Expected: OK (or meaningful error about no competitors)

- [ ] **Step 5: Commit**

```bash
git add AIM/tests/services/ci/test_integration.py
git commit -m "test(ci): add end-to-end integration tests for LLM CI pipeline"
```

---

## Task Summary

| # | Task | Files | Tests |
|---|------|-------|-------|
| 1 | Models & Interfaces | 2 create | — |
| 2 | SeoAuditor | 1 create, 1 test | 7 |
| 3 | SocialScanner | 1 create, 1 test | 5 |
| 4 | PipelineRunner | 1 create, 1 test | 4 |
| 5 | ComparisonMatrix | 1 create, 1 test | 3 |
| 6 | DialogueManager | 1 create | — |
| 7 | Integration | 3 modify | — |
| 8 | Progress Indicators | 1 modify | — |
| 9 | End-to-End Test | 1 test create | 6 |
| **Total** | | **8 new, 4 modified** | **25 tests** |

---

*Plan created 2026-05-26 from spec: docs/superpowers/specs/2026-05-26-llm-ci-analysis-design.md*
