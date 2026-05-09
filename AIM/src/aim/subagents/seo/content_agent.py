"""Content SEO Agent - Analyzes content quality and SEO optimization.

Responsibilities:
- Analyze header structure (H1-H6)
- Calculate keyword density
- Score readability (Flesch-Kincaid)
- Evaluate content quality metrics
- Assess content structure

Part of SEO Analysis Workflow (Vertical Slice).
"""

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import aiohttp
import textstat
from bs4 import BeautifulSoup


class ContentSEOAgent:
    """Content SEO analysis agent."""

    def __init__(self):
        """Initialize Content SEO Agent."""
        self.agent_name = "content-agent"
        self.timeout = aiohttp.ClientTimeout(total=60)

    async def analyze(self, url: str, correlation_id: str) -> dict[str, Any]:
        """
        Analyze content SEO aspects of a website.

        Args:
            url: Website URL to analyze
            correlation_id: Workflow tracking ID

        Returns:
            Content SEO analysis results
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

            # Analyze content
            headers = self._analyze_headers(soup)
            keywords = self._analyze_keywords(soup)
            readability = self._analyze_readability(soup)
            content_quality = self._analyze_content_quality(soup)
            structure = self._analyze_structure(soup)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return {
                "agent": self.agent_name,
                "url": url,
                "correlation_id": correlation_id,
                "timestamp": start_time.isoformat(),
                "results": {
                    "headers": headers,
                    "keywords": keywords,
                    "readability": readability,
                    "content_quality": content_quality,
                    "structure": structure
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

    def _analyze_headers(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Analyze header structure (H1-H6)."""
        headers = {
            "h1": [],
            "h2": [],
            "h3": [],
            "h4": [],
            "h5": [],
            "h6": []
        }

        for level in range(1, 7):
            tag = f"h{level}"
            found = soup.find_all(tag)
            headers[tag] = [h.get_text(strip=True) for h in found]

        # Count headers
        counts = {tag: len(texts) for tag, texts in headers.items()}

        # Check for issues
        issues = []
        if counts["h1"] == 0:
            issues.append("Missing H1 tag")
        elif counts["h1"] > 1:
            issues.append(f"Multiple H1 tags ({counts['h1']})")

        # Check hierarchy
        has_h1 = counts["h1"] > 0
        has_h2 = counts["h2"] > 0
        has_h3 = counts["h3"] > 0

        if has_h3 and not has_h2:
            issues.append("H3 without H2 (broken hierarchy)")

        return {
            "structure": headers,
            "counts": counts,
            "total": sum(counts.values()),
            "issues": issues,
            "has_proper_hierarchy": len(issues) == 0
        }

    def _analyze_keywords(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Calculate keyword density."""
        # Extract text content
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text)

        # Tokenize
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{3,}\b', text.lower())
        total_words = len(words)

        if total_words == 0:
            return {
                "total_words": 0,
                "unique_words": 0,
                "top_keywords": [],
                "keyword_density": {}
            }

        # Count words
        word_counts = Counter(words)

        # Top 10 keywords
        top_keywords = word_counts.most_common(10)

        # Calculate density for top keywords
        keyword_density = {
            word: {
                "count": count,
                "density": round((count / total_words) * 100, 2)
            }
            for word, count in top_keywords
        }

        return {
            "total_words": total_words,
            "unique_words": len(word_counts),
            "top_keywords": [{"word": word, "count": count} for word, count in top_keywords],
            "keyword_density": keyword_density
        }

    def _analyze_readability(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Score readability using Flesch-Kincaid and other metrics."""
        # Extract text content
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text)

        if not text or len(text) < 100:
            return {
                "flesch_reading_ease": None,
                "flesch_kincaid_grade": None,
                "gunning_fog": None,
                "automated_readability_index": None,
                "error": "Insufficient text for analysis"
            }

        try:
            # Calculate readability scores
            flesch_reading_ease = textstat.flesch_reading_ease(text)
            flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
            gunning_fog = textstat.gunning_fog(text)
            automated_readability_index = textstat.automated_readability_index(text)

            # Interpret Flesch Reading Ease
            if flesch_reading_ease >= 90:
                interpretation = "Very Easy"
            elif flesch_reading_ease >= 80:
                interpretation = "Easy"
            elif flesch_reading_ease >= 70:
                interpretation = "Fairly Easy"
            elif flesch_reading_ease >= 60:
                interpretation = "Standard"
            elif flesch_reading_ease >= 50:
                interpretation = "Fairly Difficult"
            elif flesch_reading_ease >= 30:
                interpretation = "Difficult"
            else:
                interpretation = "Very Difficult"

            return {
                "flesch_reading_ease": round(flesch_reading_ease, 1),
                "flesch_kincaid_grade": round(flesch_kincaid_grade, 1),
                "gunning_fog": round(gunning_fog, 1),
                "automated_readability_index": round(automated_readability_index, 1),
                "interpretation": interpretation
            }

        except Exception as e:
            return {
                "flesch_reading_ease": None,
                "flesch_kincaid_grade": None,
                "gunning_fog": None,
                "automated_readability_index": None,
                "error": str(e)
            }

    def _analyze_content_quality(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Evaluate content quality metrics."""
        # Extract text content
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text)

        # Count elements
        paragraphs = soup.find_all("p")
        images = soup.find_all("img")
        lists = soup.find_all(["ul", "ol"])
        links = soup.find_all("a")

        # Calculate metrics
        total_chars = len(text)
        total_words = len(re.findall(r'\b\w+\b', text))
        avg_word_length = round(total_chars / total_words, 2) if total_words > 0 else 0

        # Paragraph analysis
        paragraph_texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        avg_paragraph_length = round(sum(len(p.split()) for p in paragraph_texts) / len(paragraph_texts), 1) if paragraph_texts else 0

        # Image analysis
        images_with_alt = sum(1 for img in images if img.get("alt"))
        alt_text_coverage = round((images_with_alt / len(images)) * 100, 1) if images else 0

        # Content-to-code ratio
        html_size = len(str(soup))
        content_to_code_ratio = round((total_chars / html_size) * 100, 1) if html_size > 0 else 0

        return {
            "total_characters": total_chars,
            "total_words": total_words,
            "avg_word_length": avg_word_length,
            "paragraph_count": len(paragraph_texts),
            "avg_paragraph_length": avg_paragraph_length,
            "image_count": len(images),
            "images_with_alt": images_with_alt,
            "alt_text_coverage": alt_text_coverage,
            "list_count": len(lists),
            "link_count": len(links),
            "content_to_code_ratio": content_to_code_ratio
        }

    def _analyze_structure(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Analyze content structure."""
        # Check for main content area
        main_tag = soup.find("main")
        article_tag = soup.find("article")
        has_semantic_structure = main_tag is not None or article_tag is not None

        # Check for sections
        sections = soup.find_all("section")

        # Check for navigation
        nav_tags = soup.find_all("nav")

        # Check for footer
        footer_tag = soup.find("footer")

        # Check for header
        header_tag = soup.find("header")

        return {
            "has_main_tag": main_tag is not None,
            "has_article_tag": article_tag is not None,
            "has_semantic_structure": has_semantic_structure,
            "section_count": len(sections),
            "nav_count": len(nav_tags),
            "has_footer": footer_tag is not None,
            "has_header": header_tag is not None
        }
