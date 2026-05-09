"""Links SEO Agent - Analyzes link structure and quality.

Responsibilities:
- Map internal links
- Analyze external links
- Detect broken links
- Evaluate anchor text quality
- Assess link structure

Part of SEO Analysis Workflow (Vertical Slice).
"""

import asyncio
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


class LinksSEOAgent:
    """Links SEO analysis agent."""

    def __init__(self):
        """Initialize Links SEO Agent."""
        self.agent_name = "links-agent"
        self.timeout = aiohttp.ClientTimeout(total=60)
        self.max_concurrent_checks = 10

    async def analyze(self, url: str, correlation_id: str) -> dict[str, Any]:
        """
        Analyze link SEO aspects of a website.

        Args:
            url: Website URL to analyze
            correlation_id: Workflow tracking ID

        Returns:
            Links SEO analysis results
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Fetch page content
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {
                            "agent": self.agent_name,
                            "url": url,
                            "correlation_id": correlation_id,
                            "timestamp": start_time.isoformat(),
                            "results": {},
                            "status": "error",
                            "error": f"HTTP {response.status}",
                            "duration_seconds": 0
                        }

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    base_url = url

            # Extract all links
            all_links = soup.find_all("a", href=True)

            # Analyze links
            internal_links = self._analyze_internal_links(all_links, base_url)
            external_links = self._analyze_external_links(all_links, base_url)
            anchor_text = self._analyze_anchor_text(all_links)

            # Check for broken links (sample check for performance)
            broken_links = await self._check_broken_links(all_links, base_url)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return {
                "agent": self.agent_name,
                "url": url,
                "correlation_id": correlation_id,
                "timestamp": start_time.isoformat(),
                "results": {
                    "internal_links": internal_links,
                    "external_links": external_links,
                    "anchor_text": anchor_text,
                    "broken_links": broken_links
                },
                "status": "success",
                "duration_seconds": round(duration, 2)
            }

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return {
                "agent": self.agent_name,
                "url": url,
                "correlation_id": correlation_id,
                "timestamp": start_time.isoformat(),
                "results": {},
                "status": "error",
                "error": str(e),
                "duration_seconds": round(duration, 2)
            }

    def _analyze_internal_links(self, links: list, base_url: str) -> dict[str, Any]:
        """Analyze internal links."""
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        internal = []
        for link in links:
            href = link.get("href", "")

            # Skip empty, anchor-only, or javascript links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)

            # Check if internal (same domain)
            if parsed_url.netloc == base_domain or not parsed_url.netloc:
                internal.append({
                    "url": absolute_url,
                    "text": link.get_text(strip=True),
                    "rel": link.get("rel", [])
                })

        # Count unique internal links
        unique_urls = set(link["url"] for link in internal)

        # Find most linked pages
        url_counts = Counter(link["url"] for link in internal)
        most_linked = [{"url": url, "count": count} for url, count in url_counts.most_common(10)]

        return {
            "total": len(internal),
            "unique": len(unique_urls),
            "most_linked": most_linked,
            "links": internal[:50]  # Limit to first 50 for response size
        }

    def _analyze_external_links(self, links: list, base_url: str) -> dict[str, Any]:
        """Analyze external links."""
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        external = []
        for link in links:
            href = link.get("href", "")

            # Skip empty, anchor-only, or javascript links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)

            # Check if external (different domain)
            if parsed_url.netloc and parsed_url.netloc != base_domain:
                rel_attr = link.get("rel", [])
                if isinstance(rel_attr, str):
                    rel_attr = [rel_attr]

                external.append({
                    "url": absolute_url,
                    "text": link.get_text(strip=True),
                    "rel": rel_attr,
                    "nofollow": "nofollow" in rel_attr,
                    "sponsored": "sponsored" in rel_attr,
                    "ugc": "ugc" in rel_attr
                })

        # Count unique external links
        unique_urls = set(link["url"] for link in external)

        # Count nofollow links
        nofollow_count = sum(1 for link in external if link["nofollow"])

        # Group by domain
        domains = Counter(urlparse(link["url"]).netloc for link in external)
        top_domains = [{"domain": domain, "count": count} for domain, count in domains.most_common(10)]

        return {
            "total": len(external),
            "unique": len(unique_urls),
            "nofollow_count": nofollow_count,
            "nofollow_percentage": round((nofollow_count / len(external)) * 100, 1) if external else 0,
            "top_domains": top_domains,
            "links": external[:50]  # Limit to first 50 for response size
        }

    def _analyze_anchor_text(self, links: list) -> dict[str, Any]:
        """Analyze anchor text quality."""
        anchor_texts = []
        for link in links:
            href = link.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            text = link.get_text(strip=True)
            anchor_texts.append(text)

        # Count empty anchors
        empty_count = sum(1 for text in anchor_texts if not text)

        # Count generic anchors
        generic_terms = ["click here", "read more", "here", "link", "more", "click", "this"]
        generic_count = sum(1 for text in anchor_texts if text.lower() in generic_terms)

        # Count exact match anchors (very short)
        exact_match_count = sum(1 for text in anchor_texts if len(text.split()) == 1 and len(text) > 0)

        # Average anchor text length
        non_empty_texts = [text for text in anchor_texts if text]
        avg_length = round(sum(len(text) for text in non_empty_texts) / len(non_empty_texts), 1) if non_empty_texts else 0

        # Most common anchor texts
        anchor_counts = Counter(text for text in anchor_texts if text)
        most_common = [{"text": text, "count": count} for text, count in anchor_counts.most_common(10)]

        return {
            "total": len(anchor_texts),
            "empty_count": empty_count,
            "empty_percentage": round((empty_count / len(anchor_texts)) * 100, 1) if anchor_texts else 0,
            "generic_count": generic_count,
            "generic_percentage": round((generic_count / len(anchor_texts)) * 100, 1) if anchor_texts else 0,
            "exact_match_count": exact_match_count,
            "avg_length": avg_length,
            "most_common": most_common
        }

    async def _check_broken_links(self, links: list, base_url: str) -> dict[str, Any]:
        """Check for broken links (sample check for performance)."""
        # Extract unique URLs (limit to first 20 for performance)
        unique_urls = set()
        for link in links:
            href = link.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            absolute_url = urljoin(base_url, href)
            unique_urls.add(absolute_url)

            if len(unique_urls) >= 20:
                break

        # Check links concurrently
        broken = []
        working = []

        async def check_link(url: str, session: aiohttp.ClientSession) -> tuple[str, int]:
            """Check single link status."""
            try:
                async with session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return url, response.status
            except Exception:
                # If HEAD fails, try GET
                try:
                    async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        return url, response.status
                except Exception:
                    return url, 0  # 0 indicates connection error

        async with aiohttp.ClientSession() as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent_checks)

            async def check_with_semaphore(url: str) -> tuple[str, int]:
                async with semaphore:
                    return await check_link(url, session)

            # Check all links
            results = await asyncio.gather(
                *[check_with_semaphore(url) for url in unique_urls],
                return_exceptions=True
            )

            for result in results:
                if isinstance(result, Exception):
                    continue

                url, status = result
                if status == 0 or status >= 400:
                    broken.append({"url": url, "status": status})
                else:
                    working.append({"url": url, "status": status})

        return {
            "checked": len(unique_urls),
            "broken_count": len(broken),
            "working_count": len(working),
            "broken_percentage": round((len(broken) / len(unique_urls)) * 100, 1) if unique_urls else 0,
            "broken_links": broken,
            "note": f"Checked first {len(unique_urls)} unique links for performance"
        }
