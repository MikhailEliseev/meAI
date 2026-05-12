"""
Text extraction utilities using trafilatura.

Adapted from python-seo-analyzer (https://github.com/sethblack/python-seo-analyzer)
Production-tested library for clean text extraction from HTML.
"""

import hashlib
import json
import re
from collections import Counter
from typing import Optional

import trafilatura
from bs4 import BeautifulSoup


class TextExtractor:
    """
    Extract clean text and metadata from HTML using trafilatura.

    Based on python-seo-analyzer implementation (300+ stars on GitHub).
    """

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def extract_content(self, html: str, url: str) -> dict:
        """
        Extract clean content and metadata from HTML.

        Args:
            html: Raw HTML content
            url: Page URL (for metadata extraction)

        Returns:
            Dictionary with extracted content and metadata
        """
        # Calculate content hash for duplicate detection
        content_hash = hashlib.sha1(html.encode(self.encoding)).hexdigest()

        # Extract metadata using trafilatura
        metadata = trafilatura.extract_metadata(
            filecontent=html,
            default_url=url,
            extensive=True,
        )

        metadata_dict = metadata.as_dict() if metadata else {}

        # Extract clean text content
        content = trafilatura.extract(
            html,
            include_links=True,
            include_formatting=False,
            include_tables=True,
            include_images=True,
            output_format="json",
        )

        content_json = json.loads(content) if content else None

        # Parse HTML for additional analysis
        html_without_comments = re.sub(r"<!--.*?-->", r"", html, flags=re.DOTALL)
        soup = BeautifulSoup(html_without_comments, "html.parser")

        return {
            "content_hash": content_hash,
            "title": self._get_meta_value(metadata_dict, "title"),
            "author": self._get_meta_value(metadata_dict, "author"),
            "description": self._get_meta_value(metadata_dict, "description"),
            "hostname": self._get_meta_value(metadata_dict, "hostname"),
            "sitename": self._get_meta_value(metadata_dict, "sitename"),
            "date": self._get_meta_value(metadata_dict, "date"),
            "text": content_json.get("text", "") if content_json else "",
            "raw_text": content_json.get("raw_text", "") if content_json else "",
            "soup": soup,
        }

    def _get_meta_value(self, metadata_dict: dict, key: str) -> str:
        """Get metadata value, defaulting to empty string if None or 'None'."""
        value = metadata_dict.get(key)
        return "" if value is None or value == "None" else value

    def calculate_keyword_density(
        self, text: str, stopwords: Optional[set] = None
    ) -> dict:
        """
        Calculate keyword density (unigrams, bigrams, trigrams).

        Args:
            text: Clean text content
            stopwords: Set of stopwords to filter out

        Returns:
            Dictionary with keyword counts and density
        """
        if not text:
            return {
                "total_words": 0,
                "keywords": {},
                "bigrams": {},
                "trigrams": {},
            }

        # Tokenize
        tokens = self._tokenize(text, stopwords)
        raw_tokens = self._raw_tokenize(text)

        total_words = len(raw_tokens)

        # Count unigrams
        keywords = Counter(tokens)

        # Count bigrams
        bigrams = Counter()
        for ng in self._get_ngrams(raw_tokens, 2):
            bigrams[" ".join(ng)] += 1

        # Count trigrams
        trigrams = Counter()
        for ng in self._get_ngrams(raw_tokens, 3):
            trigrams[" ".join(ng)] += 1

        return {
            "total_words": total_words,
            "keywords": dict(keywords),
            "bigrams": dict(bigrams),
            "trigrams": dict(trigrams),
        }

    def _tokenize(self, text: str, stopwords: Optional[set] = None) -> list[str]:
        """Tokenize text and filter stopwords."""
        # Simple tokenization (word boundaries)
        token_regex = re.compile(r"(?u)\b\w\w+\b")
        tokens = token_regex.findall(text.lower())

        if stopwords:
            tokens = [t for t in tokens if t not in stopwords]

        return tokens

    def _raw_tokenize(self, text: str) -> list[str]:
        """Tokenize text without filtering."""
        token_regex = re.compile(r"(?u)\b\w\w+\b")
        return token_regex.findall(text.lower())

    def _get_ngrams(self, tokens: list[str], n: int) -> list[tuple]:
        """Generate n-grams from token list."""
        return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]

    def extract_meta_tags(self, soup: BeautifulSoup) -> dict:
        """
        Extract meta tags from BeautifulSoup object.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dictionary with meta tag values
        """
        meta_tags = {}

        # Title
        title_tag = soup.find("title")
        if title_tag:
            meta_tags["title"] = title_tag.get_text()

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            meta_tags["meta_description"] = meta_desc.get("content", "")

        # Canonical
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if canonical:
            meta_tags["canonical"] = canonical.get("href", "")

        # Open Graph
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title:
            meta_tags["og_title"] = og_title.get("content", "")

        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc:
            meta_tags["og_description"] = og_desc.get("content", "")

        og_image = soup.find("meta", attrs={"property": "og:image"})
        if og_image:
            meta_tags["og_image"] = og_image.get("content", "")

        return meta_tags

    def extract_headings(self, soup: BeautifulSoup) -> dict:
        """
        Extract heading tags (h1-h6) from HTML.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dictionary with heading tags and their text
        """
        headings = {}

        for level in range(1, 7):
            tag = f"h{level}"
            tags = soup.find_all(tag)
            if tags:
                headings[tag] = [h.get_text().strip() for h in tags]

        return headings
