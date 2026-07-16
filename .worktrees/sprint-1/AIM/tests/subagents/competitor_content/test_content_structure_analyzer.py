"""
Unit tests for Content Structure Analyzer.

Tests content structure analysis, readability scoring, and quality metrics.
"""

import pytest

from AIM.src.aim.subagents.competitor_content.content_structure_analyzer import (
    ContentStructureAnalyzer,
)


class TestContentStructureAnalyzer:
    """Test Content Structure Analyzer functionality."""

    def test_initialization_default(self):
        """Test default initialization."""
        analyzer = ContentStructureAnalyzer()

        assert analyzer.min_word_count == 300
        assert analyzer.ideal_paragraph_length == 100
        assert analyzer.ideal_sentence_length == 20

    def test_initialization_custom(self):
        """Test custom initialization."""
        analyzer = ContentStructureAnalyzer(
            min_word_count=500, ideal_paragraph_length=150, ideal_sentence_length=25
        )

        assert analyzer.min_word_count == 500
        assert analyzer.ideal_paragraph_length == 150
        assert analyzer.ideal_sentence_length == 25

    def test_analyze_basic_structure(self):
        """Test basic analysis structure."""
        analyzer = ContentStructureAnalyzer()

        html = "<html><body><h1>Title</h1><p>Content here.</p></body></html>"
        text = "Content here."

        result = analyzer.analyze(html, text)

        assert "readability" in result
        assert "heading_hierarchy" in result
        assert "content_length" in result
        assert "paragraph_analysis" in result
        assert "sentence_analysis" in result
        assert "visual_elements" in result
        assert "quality_score" in result
        assert "quality_level" in result

    def test_readability_calculation(self):
        """Test Flesch Reading Ease calculation."""
        analyzer = ContentStructureAnalyzer()

        # Simple text (high readability)
        simple_text = "The cat sat on the mat. The dog ran in the park. The sun is bright."
        simple_score = analyzer._calculate_readability(simple_text)

        # Complex text (lower readability)
        complex_text = "The implementation of sophisticated algorithms necessitates comprehensive understanding of computational complexity theory and advanced mathematical principles."
        complex_score = analyzer._calculate_readability(complex_text)

        assert 0 <= simple_score <= 100
        assert 0 <= complex_score <= 100
        assert simple_score > complex_score  # Simple text should be more readable

    def test_syllable_counting(self):
        """Test syllable counting heuristic."""
        analyzer = ContentStructureAnalyzer()

        assert analyzer._count_syllables("cat") == 1
        assert analyzer._count_syllables("hello") == 2
        assert analyzer._count_syllables("beautiful") == 3
        assert analyzer._count_syllables("education") == 4

    def test_heading_extraction(self):
        """Test heading extraction from HTML."""
        analyzer = ContentStructureAnalyzer()

        html = """
        <html>
        <body>
            <h1>Main Title</h1>
            <h2>Section 1</h2>
            <h3>Subsection 1.1</h3>
            <h2>Section 2</h2>
        </body>
        </html>
        """

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        headings = analyzer._extract_headings(soup)

        assert headings["h1"] == 1
        assert headings["h2"] == 2
        assert headings["h3"] == 1

    def test_heading_hierarchy_scoring_good(self):
        """Test heading hierarchy scoring with good structure."""
        analyzer = ContentStructureAnalyzer()

        # Good hierarchy: 1 H1, multiple H2, some H3
        good_headings = {"h1": 1, "h2": 3, "h3": 2}
        score = analyzer._score_heading_hierarchy(good_headings)

        assert score >= 70  # Should be high score

    def test_heading_hierarchy_scoring_bad(self):
        """Test heading hierarchy scoring with bad structure."""
        analyzer = ContentStructureAnalyzer()

        # Bad hierarchy: no H1, H4 without H3
        bad_headings = {"h2": 2, "h4": 1}
        score = analyzer._score_heading_hierarchy(bad_headings)

        assert score < 50  # Should be low score

    def test_content_length_analysis(self):
        """Test content length analysis."""
        analyzer = ContentStructureAnalyzer(min_word_count=100)

        html = "<html><body><p>Short content.</p></body></html>"
        text = "Short content."

        result = analyzer.analyze(html, text)

        assert result["content_length"]["word_count"] == 2
        assert result["content_length"]["meets_minimum"] is False

    def test_paragraph_analysis(self):
        """Test paragraph analysis."""
        analyzer = ContentStructureAnalyzer()

        html = "<html><body><p>Paragraph 1</p><p>Paragraph 2</p></body></html>"
        text = "Paragraph 1 with some words.\n\nParagraph 2 with more words here."

        result = analyzer.analyze(html, text)

        assert result["paragraph_analysis"]["count"] == 2
        assert result["paragraph_analysis"]["avg_length"] > 0

    def test_sentence_analysis(self):
        """Test sentence analysis."""
        analyzer = ContentStructureAnalyzer()

        html = "<html><body><p>First sentence. Second sentence. Third sentence.</p></body></html>"
        text = "First sentence. Second sentence. Third sentence."

        result = analyzer.analyze(html, text)

        assert result["sentence_analysis"]["count"] == 3
        assert result["sentence_analysis"]["avg_length"] > 0

    def test_visual_elements_detection(self):
        """Test visual elements detection."""
        analyzer = ContentStructureAnalyzer()

        html = """
        <html>
        <body>
            <ul><li>Item 1</li></ul>
            <ol><li>Item 2</li></ol>
            <table><tr><td>Cell</td></tr></table>
            <img src="image.jpg" alt="Image">
        </body>
        </html>
        """
        text = "Content with visual elements."

        result = analyzer.analyze(html, text)

        assert result["visual_elements"]["lists"] == 2
        assert result["visual_elements"]["tables"] == 1
        assert result["visual_elements"]["images"] == 1

    def test_quality_score_calculation(self):
        """Test overall quality score calculation."""
        analyzer = ContentStructureAnalyzer()

        # High quality content
        high_quality_html = """
        <html>
        <body>
            <h1>Main Title</h1>
            <h2>Section 1</h2>
            <p>This is a well-structured paragraph with good length. It contains multiple sentences that are easy to read. The content is clear and concise.</p>
            <ul><li>Point 1</li><li>Point 2</li></ul>
            <h2>Section 2</h2>
            <p>Another paragraph with similar quality. It maintains good readability and structure throughout the content.</p>
            <img src="image.jpg" alt="Relevant image">
        </body>
        </html>
        """
        high_quality_text = """Main Title. Section 1. This is a well-structured paragraph with good length. It contains multiple sentences that are easy to read. The content is clear and concise. Point 1. Point 2. Section 2. Another paragraph with similar quality. It maintains good readability and structure throughout the content."""

        result = analyzer.analyze(high_quality_html, high_quality_text)

        assert result["quality_score"] > 0
        assert result["quality_level"] in ["excellent", "good", "fair", "poor"]

    def test_readability_level_classification(self):
        """Test readability level classification."""
        analyzer = ContentStructureAnalyzer()

        assert analyzer._get_readability_level(95) == "very_easy"
        assert analyzer._get_readability_level(85) == "easy"
        assert analyzer._get_readability_level(75) == "fairly_easy"
        assert analyzer._get_readability_level(65) == "standard"
        assert analyzer._get_readability_level(55) == "fairly_difficult"
        assert analyzer._get_readability_level(40) == "difficult"
        assert analyzer._get_readability_level(20) == "very_difficult"

    def test_quality_level_classification(self):
        """Test quality level classification."""
        analyzer = ContentStructureAnalyzer()

        assert analyzer._get_quality_level(85) == "excellent"
        assert analyzer._get_quality_level(70) == "good"
        assert analyzer._get_quality_level(50) == "fair"
        assert analyzer._get_quality_level(30) == "poor"

    def test_empty_content(self):
        """Test handling of empty content."""
        analyzer = ContentStructureAnalyzer()

        html = "<html><body></body></html>"
        text = ""

        result = analyzer.analyze(html, text)

        assert result["readability"]["score"] == 0.0
        assert result["content_length"]["word_count"] == 0
        assert result["paragraph_analysis"]["count"] == 0
        assert result["sentence_analysis"]["count"] == 0

    def test_medical_content_structure(self):
        """Test analysis of medical content structure."""
        analyzer = ContentStructureAnalyzer()

        html = """
        <html>
        <body>
            <h1>Dental Implants Guide</h1>
            <h2>What are Dental Implants?</h2>
            <p>Dental implants are artificial tooth roots. They provide a strong foundation for fixed or removable replacement teeth.</p>
            <h2>Benefits of Dental Implants</h2>
            <ul>
                <li>Improved appearance</li>
                <li>Improved speech</li>
                <li>Improved comfort</li>
            </ul>
            <h2>Procedure Overview</h2>
            <p>The dental implant procedure involves several steps. First, the implant is placed into the jawbone. Then, a healing period allows osseointegration to occur.</p>
            <img src="implant-diagram.jpg" alt="Dental implant diagram">
            <h3>Recovery Time</h3>
            <p>Recovery typically takes 3-6 months. During this time, the implant fuses with the bone.</p>
        </body>
        </html>
        """
        text = """Dental Implants Guide. What are Dental Implants? Dental implants are artificial tooth roots. They provide a strong foundation for fixed or removable replacement teeth. Benefits of Dental Implants. Improved appearance. Improved speech. Improved comfort. Procedure Overview. The dental implant procedure involves several steps. First, the implant is placed into the jawbone. Then, a healing period allows osseointegration to occur. Recovery Time. Recovery typically takes 3-6 months. During this time, the implant fuses with the bone."""

        result = analyzer.analyze(html, text)

        # Should have good structure
        assert result["heading_hierarchy"]["headings"]["h1"] == 1
        assert result["heading_hierarchy"]["headings"]["h2"] == 3
        assert result["heading_hierarchy"]["headings"]["h3"] == 1
        assert result["visual_elements"]["lists"] == 1
        assert result["visual_elements"]["images"] == 1
        assert result["quality_score"] > 40  # Should be at least fair quality
