"""
Web Scraper for Content Gap Analysis

Scrapes content from client and competitor sites.
Supports both static HTML (BeautifulSoup) and JS-heavy sites (Playwright).
"""

import asyncio
import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser
import textstat

from ..schemas import ScrapedPageData, ContentType


class WebScraper:
    """Web scraper with rate limiting and robots.txt compliance"""

    def __init__(
        self,
        rate_limit: float = 2.0,  # requests per second
        timeout: int = 30,  # seconds
        user_agent: str = "Mozilla/5.0 (compatible; ContentGapBot/1.0)",
        use_playwright: bool = False,
    ):
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.user_agent = user_agent
        self.use_playwright = use_playwright

        # HTTP client for static sites
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

        # Playwright browser for JS-heavy sites
        self._playwright = None
        self.browser: Optional[Browser] = None

        # Rate limiting
        self._last_request_time: Dict[str, float] = {}

        # Robots.txt cache
        self._robots_cache: Dict[str, RobotFileParser] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        if self.use_playwright:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{domain}/robots.txt"

        # Check cache
        if domain not in self._robots_cache:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                response = await self.client.get(robots_url)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    # No robots.txt = allow all
                    parser.parse([])
            except Exception:
                # Error fetching robots.txt = allow all
                parser.parse([])

            self._robots_cache[domain] = parser

        parser = self._robots_cache[domain]
        return parser.can_fetch(self.user_agent, url)

    async def _rate_limit_wait(self, domain: str) -> None:
        """Wait to respect rate limit"""
        if domain in self._last_request_time:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time[domain]
            wait_time = (1.0 / self.rate_limit) - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self._last_request_time[domain] = asyncio.get_event_loop().time()

    async def scrape_page(self, url: str) -> Optional[ScrapedPageData]:
        """Scrape a single page

        Args:
            url: Page URL to scrape

        Returns:
            ScrapedPageData or None if scraping failed
        """
        # Check robots.txt
        if not await self._check_robots_txt(url):
            return None

        # Rate limiting
        parsed = urlparse(url)
        domain = parsed.netloc
        await self._rate_limit_wait(domain)

        # Scrape
        try:
            if self.use_playwright and self.browser:
                html = await self._scrape_with_playwright(url)
            else:
                html = await self._scrape_with_httpx(url)

            if not html:
                return None

            # Parse HTML
            return await self._parse_html(url, html)

        except Exception as e:
            # Log error but don't raise (graceful degradation)
            print(f"Error scraping {url}: {e}")
            return None

    async def _scrape_with_httpx(self, url: str) -> Optional[str]:
        """Scrape with httpx (static HTML)"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception:
            return None

    async def _scrape_with_playwright(self, url: str) -> Optional[str]:
        """Scrape with Playwright (JS-heavy sites)"""
        if not self.browser:
            return None

        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
            html = await page.content()
            await page.close()
            return html
        except Exception:
            return None

    async def _parse_html(self, url: str, html: str) -> ScrapedPageData:
        """Parse HTML and extract content"""
        soup = BeautifulSoup(html, "html.parser")
        parsed = urlparse(url)

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc.get("content", "").strip() if meta_desc else None

        # Extract headings
        h1_tag = soup.find("h1")
        h1 = h1_tag.get_text(strip=True) if h1_tag else None

        h2_list = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]
        h3_list = [h3.get_text(strip=True) for h3 in soup.find_all("h3")]

        # Extract body text (remove scripts, styles, nav, footer)
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        body_text = soup.get_text(separator=" ", strip=True)
        word_count = len(body_text.split())

        # Detect content type
        content_type = self._detect_content_type(url, title, h1, body_text)

        # Extract author info
        author_name, author_credentials, is_doctor = self._extract_author_info(soup)

        # Extract medical citations
        pubmed_links = self._extract_pubmed_links(soup)
        journal_refs = self._extract_journal_references(body_text)
        medical_citations_count = len(pubmed_links) + len(journal_refs)

        # Calculate readability
        readability_score = self._calculate_readability(body_text) if body_text else None

        # Check technical features
        has_https = parsed.scheme == "https"
        has_contact_info = self._has_contact_info(soup)
        has_privacy_policy = self._has_privacy_policy(soup)

        return ScrapedPageData(
            url=url,
            domain=parsed.netloc,
            is_client=False,  # Will be set by caller
            title=title,
            meta_description=meta_description,
            h1=h1,
            h2_list=h2_list if h2_list else None,
            h3_list=h3_list if h3_list else None,
            body_text=body_text,
            word_count=word_count,
            content_type=content_type,
            author_name=author_name,
            author_credentials=author_credentials,
            is_doctor_authored=is_doctor,
            medical_citations_count=medical_citations_count,
            pubmed_links=pubmed_links if pubmed_links else None,
            journal_references=journal_refs if journal_refs else None,
            readability_score=readability_score,
            has_https=has_https,
            has_contact_info=has_contact_info,
            has_privacy_policy=has_privacy_policy,
        )

    def _detect_content_type(
        self, url: str, title: Optional[str], h1: Optional[str], body: str
    ) -> ContentType:
        """Detect content type from URL and content"""
        url_lower = url.lower()
        title_lower = (title or "").lower()
        h1_lower = (h1 or "").lower()

        # Check URL patterns
        if "/blog/" in url_lower or "/article/" in url_lower:
            return ContentType.BLOG_POST
        if "/service" in url_lower or "/treatment" in url_lower:
            return ContentType.SERVICE_PAGE
        if "/faq" in url_lower or "frequently asked" in title_lower:
            return ContentType.FAQ
        if "/about" in url_lower:
            return ContentType.ABOUT_PAGE
        if "/contact" in url_lower:
            return ContentType.CONTACT_PAGE

        # Check content patterns
        if "frequently asked questions" in body.lower()[:500]:
            return ContentType.FAQ

        return ContentType.OTHER

    def _extract_author_info(self, soup: BeautifulSoup) -> tuple[Optional[str], Optional[str], bool]:
        """Extract author name, credentials, and doctor status"""
        author_name = None
        author_credentials = None
        is_doctor = False

        # Look for author meta tags
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta:
            author_name = author_meta.get("content", "").strip()

        # Look for author in common patterns
        if not author_name:
            author_patterns = [
                soup.find("span", class_=re.compile(r"author", re.I)),
                soup.find("div", class_=re.compile(r"author", re.I)),
                soup.find("p", class_=re.compile(r"byline", re.I)),
            ]
            for pattern in author_patterns:
                if pattern:
                    author_name = pattern.get_text(strip=True)
                    break

        # Extract credentials (DDS, DMD, MD, etc.)
        if author_name:
            cred_pattern = r"\b(DDS|DMD|MD|DO|PhD|RN|NP)\b"
            match = re.search(cred_pattern, author_name)
            if match:
                author_credentials = match.group(1)
                is_doctor = author_credentials in ["DDS", "DMD", "MD", "DO"]

        return author_name, author_credentials, is_doctor

    def _extract_pubmed_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract PubMed links"""
        pubmed_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "pubmed.ncbi.nlm.nih.gov" in href or "ncbi.nlm.nih.gov/pubmed" in href:
                pubmed_links.append(href)
        return pubmed_links

    def _extract_journal_references(self, text: str) -> List[str]:
        """Extract journal references from text"""
        # Simple pattern: "Journal Name, Year, Volume(Issue): Pages"
        pattern = r"[A-Z][a-z\s&]+,\s*\d{4},\s*\d+\(\d+\):\s*\d+-\d+"
        matches = re.findall(pattern, text)
        return matches[:10]  # Limit to 10 references

    def _calculate_readability(self, text: str) -> float:
        """Calculate Flesch-Kincaid grade level"""
        try:
            return textstat.flesch_kincaid_grade(text)
        except Exception:
            return 0.0

    def _has_contact_info(self, soup: BeautifulSoup) -> bool:
        """Check if page has contact information"""
        contact_patterns = ["contact", "phone", "email", "address"]
        text = soup.get_text().lower()
        return any(pattern in text for pattern in contact_patterns)

    def _has_privacy_policy(self, soup: BeautifulSoup) -> bool:
        """Check if site has privacy policy link"""
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            text = link.get_text().lower()
            if "privacy" in href or "privacy" in text:
                return True
        return False

    async def crawl_site(
        self,
        start_url: str,
        max_pages: int = 30,
        same_domain_only: bool = True,
    ) -> List[ScrapedPageData]:
        """Crawl a site starting from start_url

        Args:
            start_url: Starting URL
            max_pages: Maximum pages to scrape
            same_domain_only: Only follow links on same domain

        Returns:
            List of scraped pages
        """
        parsed_start = urlparse(start_url)
        start_domain = parsed_start.netloc

        visited = set()
        to_visit = [start_url]
        scraped_pages = []

        while to_visit and len(scraped_pages) < max_pages:
            url = to_visit.pop(0)

            if url in visited:
                continue

            visited.add(url)

            # Scrape page
            page_data = await self.scrape_page(url)
            if page_data:
                scraped_pages.append(page_data)

                # Extract links for crawling
                if len(scraped_pages) < max_pages:
                    try:
                        response = await self.client.get(url)
                        soup = BeautifulSoup(response.text, "html.parser")

                        for link in soup.find_all("a", href=True):
                            href = link["href"]
                            absolute_url = urljoin(url, href)
                            parsed = urlparse(absolute_url)

                            # Filter links
                            if same_domain_only and parsed.netloc != start_domain:
                                continue

                            # Skip non-HTTP(S) links
                            if parsed.scheme not in ["http", "https"]:
                                continue

                            # Skip already visited
                            if absolute_url in visited or absolute_url in to_visit:
                                continue

                            to_visit.append(absolute_url)

                    except Exception:
                        pass

        return scraped_pages
