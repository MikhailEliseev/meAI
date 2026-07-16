"""
Unit tests for AI Content Detector.

Tests linguistic feature extraction and AI detection accuracy.
"""

import pytest

from AIM.src.aim.subagents.utils.ai_content_detector import AIContentDetector


class TestAIContentDetector:
    """Test AI Content Detector functionality."""

    def test_initialization_default(self):
        """Test default initialization."""
        detector = AIContentDetector()

        assert detector.ai_threshold == 0.6
        assert detector.min_words == 50

    def test_initialization_custom(self):
        """Test custom initialization."""
        detector = AIContentDetector(ai_threshold=0.7, min_words=100)

        assert detector.ai_threshold == 0.7
        assert detector.min_words == 100

    def test_detect_short_text(self):
        """Test detection with text below minimum word count."""
        detector = AIContentDetector(min_words=50)
        text = "This is a very short text."

        result = detector.detect(text)

        assert result["is_ai_generated"] is None
        assert result["confidence"] == 0.0
        assert result["warning"] is not None
        assert "too short" in result["warning"].lower()

    def test_detect_human_text(self):
        """Test detection with human-written text."""
        detector = AIContentDetector(ai_threshold=0.6)

        # Human-written text with natural variation
        text = """
        The medical field has undergone tremendous changes over the past decade.
        Innovations in technology have revolutionized patient care, diagnostics, and treatment.
        However, these advancements come with their own set of challenges.
        Healthcare professionals must constantly adapt to new tools and methodologies.
        Patient privacy concerns have become increasingly important in the digital age.
        Balancing technological progress with ethical considerations remains a critical issue.
        The future of medicine will likely involve even more sophisticated AI systems.
        Yet, the human element in healthcare cannot be replaced by machines.
        Empathy, intuition, and personal connection are irreplaceable aspects of medical care.
        As we move forward, finding the right balance will be essential.
        """

        result = detector.detect(text)

        assert result["is_ai_generated"] is not None
        assert "features" in result
        assert result["features"]["word_count"] >= 50
        assert 0.0 <= result["confidence"] <= 1.0
        assert 0.0 <= result["prob_ai"] <= 1.0
        assert 0.0 <= result["prob_human"] <= 1.0
        assert result["prob_ai"] + result["prob_human"] == pytest.approx(1.0)

    def test_detect_ai_text(self):
        """Test detection with AI-generated text."""
        detector = AIContentDetector(ai_threshold=0.6)

        # AI-generated text (more uniform, predictable)
        text = """
        Medical technology has advanced significantly in recent years.
        These advancements have improved patient outcomes and treatment options.
        Healthcare providers now have access to sophisticated diagnostic tools.
        Digital health records have streamlined information management.
        Telemedicine has expanded access to healthcare services.
        Artificial intelligence assists in diagnosis and treatment planning.
        Robotic surgery has enhanced precision in complex procedures.
        Wearable devices monitor patient health in real-time.
        Personalized medicine tailors treatments to individual patients.
        The integration of technology continues to transform healthcare delivery.
        """

        result = detector.detect(text)

        assert result["is_ai_generated"] is not None
        assert "features" in result
        assert result["features"]["word_count"] >= 50

    def test_feature_extraction_vocabulary_richness(self):
        """Test vocabulary richness features (TTR, hapax ratio)."""
        detector = AIContentDetector()

        # Text with high vocabulary diversity
        text = "unique different various diverse distinct separate individual particular specific special"
        features = detector._extract_features(text)

        assert "ttr" in features
        assert "hapax_ratio" in features
        assert 0.0 <= features["ttr"] <= 1.0
        assert 0.0 <= features["hapax_ratio"] <= 1.0
        # High TTR (all unique words)
        assert features["ttr"] == 1.0

    def test_feature_extraction_sentence_stats(self):
        """Test sentence statistics extraction."""
        detector = AIContentDetector()

        text = "Short sentence. This is a longer sentence with more words. Brief."
        features = detector._extract_features(text)

        assert "sent_len_mean" in features
        assert "sent_len_std" in features
        assert "num_sentences" in features
        assert features["num_sentences"] == 3
        assert features["sent_len_mean"] > 0

    def test_feature_extraction_readability(self):
        """Test readability scores (Flesch Reading Ease, Flesch-Kincaid)."""
        detector = AIContentDetector()

        text = """
        The quick brown fox jumps over the lazy dog.
        This sentence is simple and easy to read.
        Short words make text more accessible.
        """
        features = detector._extract_features(text)

        assert "flesch_reading_ease" in features
        assert "flesch_kincaid_grade" in features
        # Flesch Reading Ease: higher = easier (0-100)
        assert 0 <= features["flesch_reading_ease"] <= 100
        # Flesch-Kincaid Grade: grade level (0-18+)
        assert features["flesch_kincaid_grade"] >= 0

    def test_feature_extraction_punctuation(self):
        """Test punctuation pattern features."""
        detector = AIContentDetector()

        text = "Hello, world! How are you? I am fine, thank you."
        features = detector._extract_features(text)

        assert "comma_rate" in features
        assert "period_rate" in features
        assert "question_rate" in features
        assert "exclamation_rate" in features
        assert features["comma_rate"] > 0
        assert features["period_rate"] > 0
        assert features["question_rate"] > 0
        assert features["exclamation_rate"] > 0

    def test_feature_extraction_word_length(self):
        """Test word length statistics."""
        detector = AIContentDetector()

        text = "short tiny big large enormous gigantic"
        features = detector._extract_features(text)

        assert "word_len_mean" in features
        assert "word_len_std" in features
        assert "long_word_ratio" in features
        assert features["word_len_mean"] > 0
        assert 0.0 <= features["long_word_ratio"] <= 1.0

    def test_feature_extraction_entropy(self):
        """Test Shannon entropy calculation."""
        detector = AIContentDetector()

        # High entropy (diverse words)
        text_diverse = "apple banana cherry date elderberry fig grape"
        features_diverse = detector._extract_features(text_diverse)

        # Low entropy (repetitive words)
        text_repetitive = "apple apple apple banana banana cherry"
        features_repetitive = detector._extract_features(text_repetitive)

        assert "word_entropy" in features_diverse
        assert "word_entropy" in features_repetitive
        # Diverse text should have higher entropy
        assert features_diverse["word_entropy"] > features_repetitive["word_entropy"]

    def test_feature_extraction_perplexity_burstiness(self):
        """Test perplexity and burstiness calculation."""
        detector = AIContentDetector()

        text = "the quick brown fox jumps over the lazy dog the fox is quick"
        features = detector._extract_features(text)

        assert "perplexity" in features
        assert "burstiness" in features
        assert features["perplexity"] > 0
        assert 0.0 <= features["burstiness"] <= 1.0

    def test_empty_text(self):
        """Test handling of empty text."""
        detector = AIContentDetector()

        result = detector.detect("")

        assert result["is_ai_generated"] is None
        assert result["features"]["word_count"] == 0
        assert result["warning"] is not None

    def test_syllable_count(self):
        """Test syllable counting heuristic."""
        detector = AIContentDetector()

        assert detector._syllable_count("cat") == 1
        assert detector._syllable_count("hello") == 2
        assert detector._syllable_count("beautiful") == 3
        assert detector._syllable_count("education") == 4

    def test_ai_probability_calculation(self):
        """Test AI probability calculation from features."""
        detector = AIContentDetector()

        # Features typical of AI text (low entropy, low perplexity, low burstiness)
        ai_features = {
            "word_entropy": 4.5,  # Low
            "perplexity": 40.0,  # Low
            "burstiness": 0.2,  # Low
            "ttr": 0.35,  # Low
            "flesch_reading_ease": 75.0,  # High
        }

        prob_ai = detector._calculate_ai_probability(ai_features)
        assert 0.0 <= prob_ai <= 1.0
        # Should be high probability of AI
        assert prob_ai > 0.5

        # Features typical of human text (high entropy, high perplexity, high burstiness)
        human_features = {
            "word_entropy": 7.5,  # High
            "perplexity": 120.0,  # High
            "burstiness": 0.6,  # High
            "ttr": 0.7,  # High
            "flesch_reading_ease": 45.0,  # Moderate
        }

        prob_ai_human = detector._calculate_ai_probability(human_features)
        assert 0.0 <= prob_ai_human <= 1.0
        # Should be low probability of AI
        assert prob_ai_human < 0.5

    def test_confidence_score(self):
        """Test confidence score calculation."""
        detector = AIContentDetector(ai_threshold=0.6)

        text = """
        Medical advancements have transformed healthcare delivery systems worldwide.
        Innovative technologies enable precise diagnostics and personalized treatment plans.
        Healthcare professionals utilize sophisticated tools for patient care optimization.
        Digital health records facilitate seamless information sharing across providers.
        Telemedicine platforms expand access to medical expertise in remote areas.
        """

        result = detector.detect(text)

        # Confidence should be the probability of the predicted class
        if result["is_ai_generated"]:
            assert result["confidence"] == result["prob_ai"]
        else:
            assert result["confidence"] == result["prob_human"]

        assert 0.0 <= result["confidence"] <= 1.0
