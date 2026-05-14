"""
Content Quality Checker - Content Quality Analysis.

Analyzes content quality across multiple dimensions: readability, grammar,
uniqueness, E-E-A-T signals, content depth, and engagement potential.

Based on: Google Quality Rater Guidelines + Content Marketing Best Practices
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog


@dataclass
class ReadabilityAnalysis:
    """Readability analysis."""

    flesch_reading_ease: float  # 0-100 (higher = easier)
    flesch_kincaid_grade: float  # US grade level
    avg_sentence_length: float
    avg_word_length: float
    complex_words_percent: float
    readability_level: str  # very_easy, easy, medium, difficult, very_difficult
    issues: list[str]
    recommendations: list[str]


@dataclass
class GrammarAnalysis:
    """Grammar and spelling analysis."""

    total_errors: int
    spelling_errors: int
    grammar_errors: int
    punctuation_errors: int
    style_issues: int
    error_rate: float  # errors per 100 words
    issues: list[dict[str, Any]]
    recommendations: list[str]


@dataclass
class UniquenessAnalysis:
    """Content uniqueness analysis."""

    uniqueness_score: float  # 0-100 (100 = fully unique)
    duplicate_phrases: list[str]
    plagiarism_detected: bool
    ai_generated_probability: float  # 0-100
    issues: list[str]
    recommendations: list[str]


@dataclass
class EEATAnalysis:
    """E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) analysis."""

    experience_score: float  # 0-100
    expertise_score: float  # 0-100
    authoritativeness_score: float  # 0-100
    trustworthiness_score: float  # 0-100
    overall_eeat_score: float  # 0-100
    signals_found: list[str]
    missing_signals: list[str]
    recommendations: list[str]


@dataclass
class ContentDepthAnalysis:
    """Content depth and comprehensiveness analysis."""

    word_count: int
    topic_coverage_score: float  # 0-100
    subtopics_covered: int
    subtopics_missing: list[str]
    has_examples: bool
    has_data: bool
    has_visuals: bool
    depth_level: str  # shallow, moderate, comprehensive, expert
    recommendations: list[str]


@dataclass
class EngagementAnalysis:
    """Content engagement potential analysis."""

    hook_strength: float  # 0-100
    storytelling_score: float  # 0-100
    emotional_appeal: float  # 0-100
    call_to_action_present: bool
    multimedia_usage: float  # 0-100
    engagement_score: float  # 0-100
    recommendations: list[str]


@dataclass
class ContentQualityReport:
    """Complete content quality report."""

    url: str
    timestamp: str

    # Core analyses
    readability: ReadabilityAnalysis
    grammar: GrammarAnalysis
    uniqueness: UniquenessAnalysis
    eeat: EEATAnalysis
    depth: ContentDepthAnalysis
    engagement: EngagementAnalysis

    # Overall metrics
    overall_quality_score: float  # 0-100
    quality_grade: str  # A+, A, B, C, D, F
    priority_issues: list[str]
    quick_wins: list[str]


class ContentQualityChecker:
    """
    Content Quality Checker.

    Analyzes content quality across multiple dimensions.
    """

    def __init__(self):
        """Initialize Content Quality Checker."""
        self.logger = structlog.get_logger()

    async def check(
        self,
        url: str,
        content: str,
        target_keyword: str | None = None,
    ) -> ContentQualityReport:
        """
        Check content quality.

        Args:
            url: URL of the content
            content: Text content to analyze
            target_keyword: Optional target keyword

        Returns:
            Complete content quality report
        """
        self.logger.info(
            "content_quality_check_start",
            url=url,
            content_length=len(content),
        )

        # Step 1: Analyze readability
        readability = await self._analyze_readability(content)

        # Step 2: Analyze grammar
        grammar = await self._analyze_grammar(content)

        # Step 3: Analyze uniqueness
        uniqueness = await self._analyze_uniqueness(content)

        # Step 4: Analyze E-E-A-T
        eeat = await self._analyze_eeat(content)

        # Step 5: Analyze content depth
        depth = await self._analyze_depth(content, target_keyword)

        # Step 6: Analyze engagement potential
        engagement = await self._analyze_engagement(content)

        # Step 7: Calculate overall quality score
        overall_score = self._calculate_overall_score(
            readability,
            grammar,
            uniqueness,
            eeat,
            depth,
            engagement,
        )

        # Step 8: Determine quality grade
        quality_grade = self._determine_grade(overall_score)

        # Step 9: Identify priority issues and quick wins
        priority_issues = self._identify_priority_issues(
            readability,
            grammar,
            uniqueness,
            eeat,
        )
        quick_wins = self._identify_quick_wins(
            grammar,
            engagement,
            depth,
        )

        report = ContentQualityReport(
            url=url,
            timestamp=datetime.now().isoformat(),
            readability=readability,
            grammar=grammar,
            uniqueness=uniqueness,
            eeat=eeat,
            depth=depth,
            engagement=engagement,
            overall_quality_score=round(overall_score, 1),
            quality_grade=quality_grade,
            priority_issues=priority_issues,
            quick_wins=quick_wins,
        )

        self.logger.info(
            "content_quality_check_complete",
            url=url,
            score=overall_score,
            grade=quality_grade,
        )

        return report

    async def _analyze_readability(self, content: str) -> ReadabilityAnalysis:
        """Analyze content readability."""
        # Count sentences, words, syllables
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        words = content.split()
        word_count = len(words)

        # Calculate average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0

        # Count complex words (3+ syllables, simplified)
        complex_words = sum(1 for word in words if len(word) > 8)
        complex_words_percent = (complex_words / word_count * 100) if word_count > 0 else 0

        # Flesch Reading Ease (simplified formula)
        flesch_reading_ease = 206.835 - 1.015 * avg_sentence_length - 84.6 * (avg_word_length / 5)
        flesch_reading_ease = max(0, min(100, flesch_reading_ease))

        # Flesch-Kincaid Grade Level (simplified)
        flesch_kincaid_grade = 0.39 * avg_sentence_length + 11.8 * (avg_word_length / 5) - 15.59
        flesch_kincaid_grade = max(0, flesch_kincaid_grade)

        # Determine readability level
        if flesch_reading_ease >= 80:
            readability_level = "very_easy"
        elif flesch_reading_ease >= 60:
            readability_level = "easy"
        elif flesch_reading_ease >= 40:
            readability_level = "medium"
        elif flesch_reading_ease >= 20:
            readability_level = "difficult"
        else:
            readability_level = "very_difficult"

        # Identify issues
        issues = []
        recommendations = []

        if avg_sentence_length > 25:
            issues.append(f"Long sentences (avg {avg_sentence_length:.1f} words)")
            recommendations.append("Break long sentences into shorter ones (15-20 words)")

        if complex_words_percent > 15:
            issues.append(f"Too many complex words ({complex_words_percent:.1f}%)")
            recommendations.append("Simplify vocabulary for better readability")

        if flesch_reading_ease < 40:
            issues.append(f"Low readability score ({flesch_reading_ease:.1f})")
            recommendations.append("Aim for Flesch score 60+ for general audience")

        return ReadabilityAnalysis(
            flesch_reading_ease=round(flesch_reading_ease, 1),
            flesch_kincaid_grade=round(flesch_kincaid_grade, 1),
            avg_sentence_length=round(avg_sentence_length, 1),
            avg_word_length=round(avg_word_length, 1),
            complex_words_percent=round(complex_words_percent, 1),
            readability_level=readability_level,
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_grammar(self, content: str) -> GrammarAnalysis:
        """Analyze grammar and spelling."""
        # Mock data (real implementation would use LanguageTool or similar)
        words = content.split()
        word_count = len(words)

        # Simulate error detection
        spelling_errors = 2
        grammar_errors = 3
        punctuation_errors = 1
        style_issues = 2

        total_errors = spelling_errors + grammar_errors + punctuation_errors + style_issues
        error_rate = (total_errors / word_count * 100) if word_count > 0 else 0

        issues = [
            {"type": "spelling", "word": "recieve", "suggestion": "receive", "position": 45},
            {"type": "grammar", "text": "they was", "suggestion": "they were", "position": 120},
            {"type": "punctuation", "text": "Hello,world", "suggestion": "Hello, world", "position": 200},
        ]

        recommendations = []
        if error_rate > 1:
            recommendations.append("Run spell checker and fix errors")
        if grammar_errors > 0:
            recommendations.append("Review grammar issues")
        if style_issues > 0:
            recommendations.append("Improve writing style consistency")

        return GrammarAnalysis(
            total_errors=total_errors,
            spelling_errors=spelling_errors,
            grammar_errors=grammar_errors,
            punctuation_errors=punctuation_errors,
            style_issues=style_issues,
            error_rate=round(error_rate, 2),
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_uniqueness(self, content: str) -> UniquenessAnalysis:
        """Analyze content uniqueness."""
        # Mock data (real implementation would use plagiarism detection API)
        uniqueness_score = 92.5
        duplicate_phrases = [
            "best practices for dental care",
            "according to recent studies",
        ]
        plagiarism_detected = False
        ai_generated_probability = 15.0  # Low probability

        issues = []
        recommendations = []

        if uniqueness_score < 80:
            issues.append(f"Low uniqueness score ({uniqueness_score:.1f}%)")
            recommendations.append("Rewrite duplicate content sections")

        if ai_generated_probability > 50:
            issues.append(f"High AI-generated probability ({ai_generated_probability:.1f}%)")
            recommendations.append("Add more human touch and personal insights")

        if len(duplicate_phrases) > 5:
            issues.append(f"Many duplicate phrases ({len(duplicate_phrases)})")
            recommendations.append("Paraphrase common phrases")

        return UniquenessAnalysis(
            uniqueness_score=round(uniqueness_score, 1),
            duplicate_phrases=duplicate_phrases,
            plagiarism_detected=plagiarism_detected,
            ai_generated_probability=round(ai_generated_probability, 1),
            issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_eeat(self, content: str) -> EEATAnalysis:
        """Analyze E-E-A-T signals."""
        # Check for E-E-A-T signals
        experience_signals = [
            "in my experience",
            "I have worked",
            "we tested",
            "our team",
        ]
        expertise_signals = [
            "certified",
            "degree",
            "years of experience",
            "expert",
            "specialist",
        ]
        authority_signals = [
            "published in",
            "cited by",
            "award",
            "recognized",
        ]
        trust_signals = [
            "source:",
            "reference:",
            "study shows",
            "according to",
            "research",
        ]

        content_lower = content.lower()

        experience_score = sum(20 for signal in experience_signals if signal in content_lower)
        expertise_score = sum(20 for signal in expertise_signals if signal in content_lower)
        authoritativeness_score = sum(20 for signal in authority_signals if signal in content_lower)
        trustworthiness_score = sum(20 for signal in trust_signals if signal in content_lower)

        # Cap at 100
        experience_score = min(100, experience_score)
        expertise_score = min(100, expertise_score)
        authoritativeness_score = min(100, authoritativeness_score)
        trustworthiness_score = min(100, trustworthiness_score)

        overall_eeat_score = (
            experience_score + expertise_score + authoritativeness_score + trustworthiness_score
        ) / 4

        signals_found = []
        missing_signals = []

        if experience_score > 0:
            signals_found.append("Experience signals present")
        else:
            missing_signals.append("Add personal experience examples")

        if expertise_score > 0:
            signals_found.append("Expertise signals present")
        else:
            missing_signals.append("Mention credentials or expertise")

        if authoritativeness_score > 0:
            signals_found.append("Authority signals present")
        else:
            missing_signals.append("Add authoritative references")

        if trustworthiness_score > 0:
            signals_found.append("Trust signals present")
        else:
            missing_signals.append("Cite credible sources")

        recommendations = []
        if overall_eeat_score < 50:
            recommendations.append("Strengthen E-E-A-T signals throughout content")
        if not signals_found:
            recommendations.append("Add author bio with credentials")

        return EEATAnalysis(
            experience_score=round(experience_score, 1),
            expertise_score=round(expertise_score, 1),
            authoritativeness_score=round(authoritativeness_score, 1),
            trustworthiness_score=round(trustworthiness_score, 1),
            overall_eeat_score=round(overall_eeat_score, 1),
            signals_found=signals_found,
            missing_signals=missing_signals,
            recommendations=recommendations,
        )

    async def _analyze_depth(
        self,
        content: str,
        target_keyword: str | None,
    ) -> ContentDepthAnalysis:
        """Analyze content depth."""
        words = content.split()
        word_count = len(words)

        # Mock subtopic analysis
        subtopics_covered = 5
        subtopics_missing = ["cost analysis", "maintenance tips"]

        # Check for examples and data
        has_examples = "example" in content.lower() or "for instance" in content.lower()
        has_data = bool(re.search(r'\d+%|\d+ percent', content))
        has_visuals = "image" in content.lower() or "chart" in content.lower()

        # Calculate topic coverage (simplified)
        topic_coverage_score = min(100, (subtopics_covered / 8) * 100)

        # Determine depth level
        if word_count < 500:
            depth_level = "shallow"
        elif word_count < 1000:
            depth_level = "moderate"
        elif word_count < 2000:
            depth_level = "comprehensive"
        else:
            depth_level = "expert"

        recommendations = []
        if word_count < 1000:
            recommendations.append(f"Expand content (current: {word_count} words, target: 1500+)")
        if not has_examples:
            recommendations.append("Add practical examples")
        if not has_data:
            recommendations.append("Include statistics and data")
        if subtopics_missing:
            recommendations.append(f"Cover missing subtopics: {', '.join(subtopics_missing)}")

        return ContentDepthAnalysis(
            word_count=word_count,
            topic_coverage_score=round(topic_coverage_score, 1),
            subtopics_covered=subtopics_covered,
            subtopics_missing=subtopics_missing,
            has_examples=has_examples,
            has_data=has_data,
            has_visuals=has_visuals,
            depth_level=depth_level,
            recommendations=recommendations,
        )

    async def _analyze_engagement(self, content: str) -> EngagementAnalysis:
        """Analyze engagement potential."""
        # Check hook strength (first 100 words)
        first_100 = " ".join(content.split()[:100])
        hook_words = ["discover", "learn", "secret", "proven", "ultimate"]
        hook_strength = sum(20 for word in hook_words if word in first_100.lower())
        hook_strength = min(100, hook_strength)

        # Check storytelling elements
        storytelling_words = ["story", "journey", "experience", "challenge", "success"]
        storytelling_score = sum(20 for word in storytelling_words if word in content.lower())
        storytelling_score = min(100, storytelling_score)

        # Check emotional appeal
        emotional_words = ["amazing", "incredible", "transform", "breakthrough", "powerful"]
        emotional_appeal = sum(20 for word in emotional_words if word in content.lower())
        emotional_appeal = min(100, emotional_appeal)

        # Check for CTA (use word boundaries to avoid false positives)
        cta_patterns = [
            r'\bcontact\b', r'\bcall us\b', r'\bcall now\b', r'\bbook\b',
            r'\bget started\b', r'\bdownload\b', r'\bsubscribe\b',
            r'\bзапись\b', r'\bзвоните\b', r'\bзаказать\b'
        ]
        call_to_action_present = any(re.search(pattern, content.lower()) for pattern in cta_patterns)

        # Check multimedia usage (simplified)
        multimedia_usage = 0
        if "image" in content.lower():
            multimedia_usage += 30
        if "video" in content.lower():
            multimedia_usage += 40
        if "infographic" in content.lower():
            multimedia_usage += 30

        # Calculate overall engagement score
        engagement_score = (
            hook_strength * 0.2 +
            storytelling_score * 0.2 +
            emotional_appeal * 0.2 +
            (100 if call_to_action_present else 0) * 0.2 +
            multimedia_usage * 0.2
        )

        recommendations = []
        if hook_strength < 50:
            recommendations.append("Strengthen opening hook")
        if not call_to_action_present:
            recommendations.append("Add clear call-to-action")
        if multimedia_usage < 50:
            recommendations.append("Add more visuals (images, videos)")

        return EngagementAnalysis(
            hook_strength=round(hook_strength, 1),
            storytelling_score=round(storytelling_score, 1),
            emotional_appeal=round(emotional_appeal, 1),
            call_to_action_present=call_to_action_present,
            multimedia_usage=round(multimedia_usage, 1),
            engagement_score=round(engagement_score, 1),
            recommendations=recommendations,
        )

    def _calculate_overall_score(
        self,
        readability: ReadabilityAnalysis,
        grammar: GrammarAnalysis,
        uniqueness: UniquenessAnalysis,
        eeat: EEATAnalysis,
        depth: ContentDepthAnalysis,
        engagement: EngagementAnalysis,
    ) -> float:
        """Calculate overall quality score."""
        # Readability (15%)
        readability_score = readability.flesch_reading_ease

        # Grammar (20%)
        grammar_score = max(0, 100 - grammar.error_rate * 10)

        # Uniqueness (20%)
        uniqueness_score = uniqueness.uniqueness_score

        # E-E-A-T (25%)
        eeat_score = eeat.overall_eeat_score

        # Depth (10%)
        depth_score = depth.topic_coverage_score

        # Engagement (10%)
        engagement_score = engagement.engagement_score

        overall = (
            readability_score * 0.15 +
            grammar_score * 0.20 +
            uniqueness_score * 0.20 +
            eeat_score * 0.25 +
            depth_score * 0.10 +
            engagement_score * 0.10
        )

        return overall

    def _determine_grade(self, score: float) -> str:
        """Determine quality grade."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _identify_priority_issues(
        self,
        readability: ReadabilityAnalysis,
        grammar: GrammarAnalysis,
        uniqueness: UniquenessAnalysis,
        eeat: EEATAnalysis,
    ) -> list[str]:
        """Identify priority issues."""
        priority = []

        # Critical issues
        if grammar.error_rate > 2:
            priority.append("🔴 CRITICAL: High error rate - fix grammar and spelling")
        if uniqueness.plagiarism_detected:
            priority.append("🔴 CRITICAL: Plagiarism detected - rewrite content")
        if uniqueness.uniqueness_score < 70:
            priority.append("🔴 CRITICAL: Low uniqueness - add original content")

        # High priority
        if eeat.overall_eeat_score < 40:
            priority.append("🟡 HIGH: Weak E-E-A-T signals - add expertise and sources")
        if readability.flesch_reading_ease < 30:
            priority.append("🟡 HIGH: Very difficult to read - simplify language")

        return priority[:5]

    def _identify_quick_wins(
        self,
        grammar: GrammarAnalysis,
        engagement: EngagementAnalysis,
        depth: ContentDepthAnalysis,
    ) -> list[str]:
        """Identify quick wins."""
        quick_wins = []

        if grammar.total_errors > 0 and grammar.total_errors < 10:
            quick_wins.append(f"Fix {grammar.total_errors} grammar/spelling errors (5 min)")
        if not engagement.call_to_action_present:
            quick_wins.append("Add call-to-action at the end (2 min)")
        if not depth.has_examples:
            quick_wins.append("Add 1-2 practical examples (10 min)")

        return quick_wins[:3]


async def main():
    """Example usage."""
    checker = ContentQualityChecker()

    sample_content = """
    Dental implants are a modern solution for missing teeth. They provide a permanent
    replacement that looks and functions like natural teeth. In my experience working
    with patients for over 15 years, dental implants have transformed countless lives.

    According to recent studies, dental implants have a 95% success rate. This makes
    them one of the most reliable dental procedures available today.

    For example, one of our patients received implants after losing teeth in an accident.
    The results were amazing, and they regained their confidence completely.

    If you're considering dental implants, contact our clinic today for a consultation.
    """

    report = await checker.check(
        url="https://example.com/dental-implants",
        content=sample_content,
        target_keyword="dental implants",
    )

    print(f"Content Quality Report: {report.url}")
    print(f"Overall Score: {report.overall_quality_score}/100 (Grade: {report.quality_grade})")
    print()

    print("Priority Issues:")
    for issue in report.priority_issues:
        print(f"  {issue}")

    print()
    print("Quick Wins:")
    for win in report.quick_wins:
        print(f"  ✅ {win}")


if __name__ == "__main__":
    asyncio.run(main())


# ==============================================================================
# Added by Teacher Agent: quality-checker
# ==============================================================================

import asyncio

async def translate(text: str) -> list[Any]:
    """Return a list of GrammarCheckingTree objects (each GrammarCheckingTree
    object represents a sentence) based on the input text using the benepar library.

    Precondition:
        - text can only contain letters in the English alphabet and basic
        punctuation marks (e.g. ",", ".", "?", "!").
    """
    grammar_trees = []

    doc = nlp(text)
    sentence_trees = list(doc.sents)
    for sentence_tree in sentence_trees:
        grammar_trees.append(_create_grammar_tree(sentence_tree))

    return grammar_trees

# ==============================================================================
# Added by Teacher Agent: quality-checker
# ==============================================================================

async def find(
        self,
        path: Path,
        *,
        command_hash: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> Optional["CloudPath"]:
        """Find the best matching version of a file within the storage,
        or `None` if no match can be found. If both the creation and content hash
        are specified, only exact matches will be returned. Otherwise, the most
        recent matching file is preferred.
        """
        name = self.encode_name(str(path))
        urls = []
        if command_hash is not None and content_hash is not None:
            url = self.url / name / command_hash / content_hash
            urls = [url] if url.exists() else []
        elif command_hash is not None:
            if (self.url / name / command_hash).exists():
                urls = list((self.url / name / command_hash).iterdir())
        else:
            if (self.url / name).exists():
                for sub_dir in (self.url / name).iterdir():
                    urls.extend(sub_dir.iterdir())
                if content_hash is not None:
                    urls = [url for url in urls if url.parts[-1] == content_hash]
        if len(urls) >= 2:
            try:
                urls.sort(key=lambda x: x.stat().st_mtime)
            except Exception:
                msg.warn(
                    "Unable to sort remote files by last modified. The file(s) "
                    "pulled from the cache may not be the most recent."
                )
        return urls[-1] if urls else None