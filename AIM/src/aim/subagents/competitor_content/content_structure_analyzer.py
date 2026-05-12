"""
Content Structure Analyzer for competitor content analysis.

Analyzes content structure, readability, and quality metrics.
"""

import re
from typing import Optional

import nltk
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


class ContentStructureAnalyzer:
    """
    Analyze content structure and quality metrics.

    Metrics:
    - Readability (Flesch Reading Ease)
    - Heading hierarchy quality
    - Content length (word count)
    - Paragraph and sentence length
    - Use of lists, tables, images
    - Overall content quality score
    """

    def __init__(
        self,
        min_word_count: int = 300,
        ideal_paragraph_length: int = 100,
        ideal_sentence_length: int = 20,
    ):
        """
        Initialize Content Structure Analyzer.

        Args:
            min_word_count: Minimum word count for quality content
            ideal_paragraph_length: Ideal paragraph length in words
            ideal_sentence_length: Ideal sentence length in words
        """
        self.min_word_count = min_word_count
        self.ideal_paragraph_length = ideal_paragraph_length
        self.ideal_sentence_length = ideal_sentence_length

    def analyze(self, html: str, text: str) -> dict:
        """
        Analyze content structure and quality.

        Args:
            html: Raw HTML content
            text: Clean text content

        Returns:
            Dictionary with structure analysis results
        """
        soup = BeautifulSoup(html, "html.parser")

        # Readability
        readability = self._calculate_readability(text)

        # Heading hierarchy
        headings = self._extract_headings(soup)
        hierarchy_score = self._score_heading_hierarchy(headings)

        # Content length
        word_count = len(text.split())

        # Paragraph analysis
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        avg_paragraph_length = (
            sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            if paragraphs
            else 0
        )

        # Sentence analysis
        sentences = sent_tokenize(text)
        avg_sentence_length = (
            sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        )

        # Visual elements
        lists_count = len(soup.find_all(["ul", "ol"]))
        tables_count = len(soup.find_all("table"))
        images_count = len(soup.find_all("img"))

        # Quality score
        quality_score = self._calculate_quality_score(
            readability=readability,
            hierarchy_score=hierarchy_score,
            word_count=word_count,
            avg_paragraph_length=avg_paragraph_length,
            avg_sentence_length=avg_sentence_length,
            lists_count=lists_count,
            tables_count=tables_count,
            images_count=images_count,
        )

        return {
            "readability": {
                "score": round(readability, 2),
                "level": self._get_readability_level(readability),
            },
            "heading_hierarchy": {
                "score": round(hierarchy_score, 2),
                "headings": headings,
            },
            "content_length": {
                "word_count": word_count,
                "meets_minimum": word_count >= self.min_word_count,
            },
            "paragraph_analysis": {
                "count": len(paragraphs),
                "avg_length": round(avg_paragraph_length, 2),
                "ideal_length": self.ideal_paragraph_length,
            },
            "sentence_analysis": {
                "count": len(sentences),
                "avg_length": round(avg_sentence_length, 2),
                "ideal_length": self.ideal_sentence_length,
            },
            "visual_elements": {
                "lists": lists_count,
                "tables": tables_count,
                "images": images_count,
            },
            "quality_score": round(quality_score, 2),
            "quality_level": self._get_quality_level(quality_score),
        }

    def _calculate_readability(self, text: str) -> float:
        """
        Calculate Flesch Reading Ease score.

        Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)

        Score interpretation:
        - 90-100: Very easy (5th grade)
        - 80-89: Easy (6th grade)
        - 70-79: Fairly easy (7th grade)
        - 60-69: Standard (8th-9th grade)
        - 50-59: Fairly difficult (10th-12th grade)
        - 30-49: Difficult (college)
        - 0-29: Very difficult (college graduate)
        """
        if not text:
            return 0.0

        sentences = sent_tokenize(text)
        words = text.split()

        if not sentences or not words:
            return 0.0

        # Count syllables
        total_syllables = sum(self._count_syllables(word) for word in words)

        # Calculate metrics
        words_per_sentence = len(words) / len(sentences)
        syllables_per_word = total_syllables / len(words)

        # Flesch Reading Ease
        score = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word

        # Clamp to 0-100
        return max(0.0, min(100.0, score))

    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word (heuristic).

        Simple heuristic:
        - Count vowel groups
        - Subtract silent 'e' at end
        - Minimum 1 syllable per word
        """
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith("e"):
            syllable_count -= 1

        # Minimum 1 syllable
        return max(1, syllable_count)

    def _extract_headings(self, soup: BeautifulSoup) -> dict[str, int]:
        """Extract heading counts by level."""
        headings = {}
        for level in range(1, 7):
            tag = f"h{level}"
            count = len(soup.find_all(tag))
            if count > 0:
                headings[tag] = count
        return headings

    def _score_heading_hierarchy(self, headings: dict[str, int]) -> float:
        """
        Score heading hierarchy quality.

        Good hierarchy:
        - Has H1 (exactly 1)
        - Has H2 (multiple)
        - Logical progression (H1 → H2 → H3, not H1 → H4)
        - Not too many levels (max 3-4)
        """
        score = 0.0

        # Check H1 (should have exactly 1)
        h1_count = headings.get("h1", 0)
        if h1_count == 1:
            score += 30.0
        elif h1_count == 0:
            score += 0.0  # Missing H1 is bad
        else:
            score += 10.0  # Multiple H1s is not ideal

        # Check H2 (should have multiple)
        h2_count = headings.get("h2", 0)
        if h2_count >= 3:
            score += 30.0
        elif h2_count >= 1:
            score += 20.0
        else:
            score += 0.0

        # Check logical progression
        has_h3 = headings.get("h3", 0) > 0
        has_h4 = headings.get("h4", 0) > 0
        has_h5 = headings.get("h5", 0) > 0

        if has_h3 and h2_count > 0:
            score += 20.0  # H3 after H2 is good
        if has_h4 and not has_h3:
            score -= 10.0  # H4 without H3 is bad
        if has_h5 and not has_h4:
            score -= 10.0  # H5 without H4 is bad

        # Check depth (not too many levels)
        depth = max((int(h[1]) for h in headings.keys()), default=0)
        if depth <= 3:
            score += 20.0
        elif depth == 4:
            score += 10.0
        else:
            score += 0.0  # Too deep

        return max(0.0, min(100.0, score))

    def _calculate_quality_score(
        self,
        readability: float,
        hierarchy_score: float,
        word_count: int,
        avg_paragraph_length: float,
        avg_sentence_length: float,
        lists_count: int,
        tables_count: int,
        images_count: int,
    ) -> float:
        """
        Calculate overall content quality score.

        Weighted components:
        - Readability: 20%
        - Heading hierarchy: 20%
        - Content length: 15%
        - Paragraph length: 15%
        - Sentence length: 10%
        - Visual elements: 20%
        """
        score = 0.0

        # Readability (20%)
        # Target: 60-70 (standard, 8th-9th grade)
        if 60 <= readability <= 70:
            score += 20.0
        elif 50 <= readability < 60 or 70 < readability <= 80:
            score += 15.0
        elif 40 <= readability < 50 or 80 < readability <= 90:
            score += 10.0
        else:
            score += 5.0

        # Heading hierarchy (20%)
        score += hierarchy_score * 0.20

        # Content length (15%)
        if word_count >= self.min_word_count * 3:
            score += 15.0
        elif word_count >= self.min_word_count * 2:
            score += 12.0
        elif word_count >= self.min_word_count:
            score += 10.0
        else:
            score += 5.0

        # Paragraph length (15%)
        # Target: 80-120 words
        if 80 <= avg_paragraph_length <= 120:
            score += 15.0
        elif 60 <= avg_paragraph_length < 80 or 120 < avg_paragraph_length <= 150:
            score += 12.0
        elif 40 <= avg_paragraph_length < 60 or 150 < avg_paragraph_length <= 200:
            score += 8.0
        else:
            score += 4.0

        # Sentence length (10%)
        # Target: 15-25 words
        if 15 <= avg_sentence_length <= 25:
            score += 10.0
        elif 10 <= avg_sentence_length < 15 or 25 < avg_sentence_length <= 30:
            score += 7.0
        elif 5 <= avg_sentence_length < 10 or 30 < avg_sentence_length <= 40:
            score += 4.0
        else:
            score += 2.0

        # Visual elements (20%)
        visual_score = 0.0
        if lists_count > 0:
            visual_score += 7.0
        if tables_count > 0:
            visual_score += 7.0
        if images_count > 0:
            visual_score += 6.0
        score += visual_score

        return max(0.0, min(100.0, score))

    def _get_readability_level(self, score: float) -> str:
        """Get readability level description."""
        if score >= 90:
            return "very_easy"
        elif score >= 80:
            return "easy"
        elif score >= 70:
            return "fairly_easy"
        elif score >= 60:
            return "standard"
        elif score >= 50:
            return "fairly_difficult"
        elif score >= 30:
            return "difficult"
        else:
            return "very_difficult"

    def _get_quality_level(self, score: float) -> str:
        """Get quality level description."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"
