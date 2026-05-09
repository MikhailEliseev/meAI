"""Technical SEO Agent - Analyzes technical SEO aspects of websites.

Responsibilities:
- Analyze robots.txt
- Parse sitemap.xml
- Extract meta tags
- Check page performance (PageSpeed API or Lighthouse CLI)
- Validate Schema.org markup

Part of SEO Analysis Workflow (Vertical Slice).
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


class TechnicalSEOAgent:
    """Technical SEO analysis agent."""

    def __init__(self):
        """Initialize Technical SEO Agent."""
        self.agent_name = "technical-agent"
        self.pagespeed_api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY")
        self.pagespeed_api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        self.timeout = aiohttp.ClientTimeout(total=60)

    async def analyze(self, url: str, correlation_id: str) -> dict[str, Any]:
        """
        Analyze technical SEO aspects of a website.

        Args:
            url: Website URL to analyze
            correlation_id: Workflow tracking ID

        Returns:
            Technical SEO analysis results
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Run all analyses in parallel
            results = await asyncio.gather(
                self._analyze_robots_txt(url),
                self._analyze_sitemap(url),
                self._extract_meta_tags(url),
                self._get_page_speed(url),
                self._validate_schema(url),
                return_exceptions=True
            )

            # Unpack results
            robots_result, sitemap_result, meta_result, performance_result, schema_result = results

            # Handle exceptions
            robots_txt = robots_result if not isinstance(robots_result, Exception) else {"error": str(robots_result)}
            sitemap = sitemap_result if not isinstance(sitemap_result, Exception) else {"error": str(sitemap_result)}
            meta_tags = meta_result if not isinstance(meta_result, Exception) else {"error": str(meta_result)}
            performance = performance_result if not isinstance(performance_result, Exception) else {"error": str(performance_result)}
            schema = schema_result if not isinstance(schema_result, Exception) else {"error": str(schema_result)}

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return {
                "agent": self.agent_name,
                "url": url,
                "correlation_id": correlation_id,
                "timestamp": start_time.isoformat(),
                "results": {
                    "robots_txt": robots_txt,
                    "sitemap": sitemap,
                    "meta_tags": meta_tags,
                    "performance": performance,
                    "schema": schema
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

    async def _analyze_robots_txt(self, url: str) -> dict[str, Any]:
        """Analyze robots.txt file."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Parse robots.txt
                        allows_crawling = "Disallow: /" not in content
                        sitemap_urls = [
                            line.split(": ", 1)[1].strip()
                            for line in content.split("\n")
                            if line.strip().lower().startswith("sitemap:")
                        ]

                        return {
                            "exists": True,
                            "allows_crawling": allows_crawling,
                            "sitemap_urls": sitemap_urls,
                            "content_length": len(content)
                        }
                    else:
                        return {
                            "exists": False,
                            "allows_crawling": True,  # Default if no robots.txt
                            "sitemap_urls": [],
                            "status_code": response.status
                        }
        except Exception as e:
            return {
                "exists": False,
                "allows_crawling": True,
                "sitemap_urls": [],
                "error": str(e)
            }

    async def _analyze_sitemap(self, url: str) -> dict[str, Any]:
        """Parse sitemap.xml file."""
        parsed = urlparse(url)
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(sitemap_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, "xml")

                        # Count URLs
                        urls = soup.find_all("url")
                        url_count = len(urls)

                        # Get last modified (if available)
                        lastmod_tags = soup.find_all("lastmod")
                        last_modified = lastmod_tags[0].text if lastmod_tags else None

                        return {
                            "exists": True,
                            "url_count": url_count,
                            "last_modified": last_modified,
                            "sitemap_url": sitemap_url
                        }
                    else:
                        return {
                            "exists": False,
                            "url_count": 0,
                            "status_code": response.status
                        }
        except Exception as e:
            return {
                "exists": False,
                "url_count": 0,
                "error": str(e)
            }

    async def _extract_meta_tags(self, url: str) -> dict[str, Any]:
        """Extract meta tags from page."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # Extract title
                        title_tag = soup.find("title")
                        title = title_tag.text.strip() if title_tag else None

                        # Extract meta description
                        desc_tag = soup.find("meta", attrs={"name": "description"})
                        description = desc_tag.get("content") if desc_tag else None

                        # Extract meta keywords
                        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
                        keywords = keywords_tag.get("content", "").split(",") if keywords_tag else []
                        keywords = [k.strip() for k in keywords if k.strip()]

                        # Extract Open Graph tags
                        og_tags = {}
                        for tag in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
                            prop = tag.get("property")
                            content = tag.get("content")
                            if prop and content:
                                og_tags[prop] = content

                        return {
                            "title": title,
                            "title_length": len(title) if title else 0,
                            "description": description,
                            "description_length": len(description) if description else 0,
                            "keywords": keywords,
                            "og_tags": og_tags
                        }
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def _get_page_speed(self, url: str) -> dict[str, Any]:
        """Get PageSpeed Insights data (or fallback to Lighthouse CLI)."""
        if self.pagespeed_api_key:
            return await self._get_page_speed_api(url)
        else:
            return await self._get_page_speed_lighthouse(url)

    async def _get_page_speed_api(self, url: str) -> dict[str, Any]:
        """Get PageSpeed Insights data via API."""
        try:
            params = {
                "url": url,
                "key": self.pagespeed_api_key,
                "category": "performance",
                "strategy": "mobile"
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(self.pagespeed_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extract metrics
                        lighthouse = data.get("lighthouseResult", {})
                        audits = lighthouse.get("audits", {})

                        # Performance score (0-100)
                        categories = lighthouse.get("categories", {})
                        performance_category = categories.get("performance", {})
                        score = performance_category.get("score", 0) * 100

                        # Core Web Vitals
                        fcp = audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000
                        lcp = audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000
                        cls = audits.get("cumulative-layout-shift", {}).get("numericValue", 0)

                        return {
                            "page_speed_score": round(score, 1),
                            "first_contentful_paint": round(fcp, 2),
                            "largest_contentful_paint": round(lcp, 2),
                            "cumulative_layout_shift": round(cls, 3),
                            "source": "pagespeed_api"
                        }
                    else:
                        return {"error": f"PageSpeed API returned {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def _get_page_speed_lighthouse(self, url: str) -> dict[str, Any]:
        """Fallback: Use Lighthouse CLI (slower, no mobile metrics)."""
        try:
            # Run Lighthouse CLI
            process = await asyncio.create_subprocess_exec(
                "lighthouse",
                url,
                "--output=json",
                "--output-path=stdout",
                "--only-categories=performance",
                "--quiet",
                "--chrome-flags='--headless'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                data = json.loads(stdout.decode())

                # Extract metrics
                audits = data.get("audits", {})
                categories = data.get("categories", {})

                score = categories.get("performance", {}).get("score", 0) * 100
                fcp = audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000
                lcp = audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000
                cls = audits.get("cumulative-layout-shift", {}).get("numericValue", 0)

                return {
                    "page_speed_score": round(score, 1),
                    "first_contentful_paint": round(fcp, 2),
                    "largest_contentful_paint": round(lcp, 2),
                    "cumulative_layout_shift": round(cls, 3),
                    "source": "lighthouse_cli",
                    "warning": "Using Lighthouse CLI (slower, no mobile metrics)"
                }
            else:
                return {
                    "error": "Lighthouse CLI failed",
                    "stderr": stderr.decode()
                }
        except FileNotFoundError:
            return {
                "error": "Lighthouse CLI not installed",
                "warning": "Install with: npm install -g lighthouse"
            }
        except Exception as e:
            return {"error": str(e)}

    async def _validate_schema(self, url: str) -> dict[str, Any]:
        """Validate Schema.org markup."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # Find JSON-LD scripts
                        schema_scripts = soup.find_all("script", type="application/ld+json")

                        if not schema_scripts:
                            return {
                                "has_schema": False,
                                "types": [],
                                "valid": False
                            }

                        # Parse schemas
                        schema_types = []
                        valid = True

                        for script in schema_scripts:
                            try:
                                schema_data = json.loads(script.string)

                                # Extract @type
                                if isinstance(schema_data, dict):
                                    schema_type = schema_data.get("@type")
                                    if schema_type:
                                        if isinstance(schema_type, list):
                                            schema_types.extend(schema_type)
                                        else:
                                            schema_types.append(schema_type)
                                elif isinstance(schema_data, list):
                                    for item in schema_data:
                                        if isinstance(item, dict):
                                            schema_type = item.get("@type")
                                            if schema_type:
                                                if isinstance(schema_type, list):
                                                    schema_types.extend(schema_type)
                                                else:
                                                    schema_types.append(schema_type)
                            except json.JSONDecodeError:
                                valid = False

                        return {
                            "has_schema": len(schema_types) > 0,
                            "types": list(set(schema_types)),
                            "valid": valid,
                            "count": len(schema_scripts)
                        }
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}
