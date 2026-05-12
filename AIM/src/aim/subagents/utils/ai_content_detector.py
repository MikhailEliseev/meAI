"""
AI content detection using linguistic features and statistical analysis.

Adapted from NLP-Final-Project-Detecting-AI-Generated-Text
(https://github.com/Fahad-Ali-Khan-ca/NLP-Final-Project-Detecting-AI-Generated-Text)

Production-tested approach combining:
- Linguistic feature extraction (readability, vocabulary richness, entropy)
- Statistical analysis (perplexity, burstiness)
- Ensemble detection with confidence scores
"""

import math
import re
from collections import Counter
from typing import Optional

import numpy as np


class AIContentDetector:
    """
    Detect AI-generated content using linguistic features.

    Based on production implementation from Fahad Ali Khan's AI text detector.
    Uses statistical patterns and stylometric analysis without requiring ML models.
    """

    # Sentence and word regex patterns
    _SENT_RE = re.compile(r"(?<=[.!?])\s+")
    _WORD_RE = re.compile(r"\b[a-zA-Z]+\b")

    def __init__(
        self,
        ai_threshold: float = 0.6,
        min_words: int = 50,
    ):
        """
        Initialize AI content detector.

        Args:
            ai_threshold: Confidence threshold for AI classification (0.0-1.0)
            min_words: Minimum word count for reliable detection
        """
        self.ai_threshold = ai_threshold
        self.min_words = min_words

    def detect(self, text: str) -> dict:
        """
        Detect if text is AI-generated.

        Args:
            text: Text content to analyze

        Returns:
            Dictionary with detection results:
            - is_ai_generated: bool
            - confidence: float (0.0-1.0)
            - prob_ai: float
            - prob_human: float
            - features: dict of linguistic features
            - warning: str if text too short
        """
        # Extract features
        features = self._extract_features(text)

        # Check minimum length
        if features["word_count"] < self.min_words:
            return {
                "is_ai_generated": None,
                "confidence": 0.0,
                "prob_ai": 0.0,
                "prob_human": 0.0,
                "features": features,
                "warning": f"Text too short ({features['word_count']} words, minimum {self.min_words})",
            }

        # Calculate AI probability based on features
        prob_ai = self._calculate_ai_probability(features)
        prob_human = 1.0 - prob_ai

        is_ai = prob_ai >= self.ai_threshold
        confidence = prob_ai if is_ai else prob_human

        return {
            "is_ai_generated": is_ai,
            "confidence": confidence,
            "prob_ai": prob_ai,
            "prob_human": prob_human,
            "features": features,
            "warning": None,
        }

    def _extract_features(self, text: str) -> dict:
        """Extract linguistic and stylometric features."""
        words = self._words(text)
        sentences = self._sentences(text)

        features = {}
        features["char_count"] = len(text)
        features["word_count"] = len(words)

        # Vocabulary richness
        features.update(self._vocabulary_richness(words))

        # Sentence statistics
        features.update(self._sentence_stats(sentences))

        # Readability scores
        features.update(self._readability_scores(text, words, sentences))

        # Punctuation patterns
        features.update(self._punctuation_features(text))

        # Word length statistics
        features.update(self._word_length_features(words))

        # Entropy (key AI indicator)
        features["word_entropy"] = self._entropy(words)

        # Perplexity and burstiness (AI detection signals)
        features.update(self._perplexity_burstiness(words))

        return features

    def _calculate_ai_probability(self, features: dict) -> float:
        """
        Calculate probability of AI generation based on features.

        AI-generated text typically has:
        - Lower entropy (more predictable word patterns)
        - Lower perplexity (more uniform distribution)
        - Lower burstiness (less variation in word usage)
        - Higher readability scores (more formulaic)
        - Lower TTR (less vocabulary diversity)
        """
        signals = []

        # Entropy signal (AI: 3-5, Human: 6-9)
        if features["word_entropy"] < 5.0:
            signals.append(0.8)
        elif features["word_entropy"] < 6.5:
            signals.append(0.5)
        else:
            signals.append(0.2)

        # Perplexity signal (AI: low, Human: high)
        if features["perplexity"] < 50:
            signals.append(0.7)
        elif features["perplexity"] < 100:
            signals.append(0.4)
        else:
            signals.append(0.1)

        # Burstiness signal (AI: low, Human: high)
        if features["burstiness"] < 0.3:
            signals.append(0.7)
        elif features["burstiness"] < 0.5:
            signals.append(0.4)
        else:
            signals.append(0.1)

        # TTR signal (AI: low, Human: high)
        if features["ttr"] < 0.4:
            signals.append(0.6)
        elif features["ttr"] < 0.6:
            signals.append(0.3)
        else:
            signals.append(0.1)

        # Readability signal (AI: very high, Human: moderate)
        if features["flesch_reading_ease"] > 70:
            signals.append(0.6)
        elif features["flesch_reading_ease"] > 50:
            signals.append(0.3)
        else:
            signals.append(0.1)

        # Average all signals
        return float(np.mean(signals))

    # -------------------------------------------------------------------------
    # Feature extraction helpers
    # -------------------------------------------------------------------------

    def _sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        return [s.strip() for s in self._SENT_RE.split(text) if s.strip()]

    def _words(self, text: str) -> list[str]:
        """Extract words from text."""
        return self._WORD_RE.findall(text.lower())

    def _syllable_count(self, word: str) -> int:
        """Rough syllable count using vowel-group heuristic."""
        word = word.lower().rstrip("e")
        count = len(re.findall(r"[aeiouy]+", word))
        return max(count, 1)

    def _vocabulary_richness(self, words: list[str]) -> dict:
        """Type-token ratio and hapax legomena ratio."""
        n = len(words)
        if n == 0:
            return {"ttr": 0.0, "hapax_ratio": 0.0}

        types = set(words)
        hapax = sum(1 for w in types if words.count(w) == 1)

        return {
            "ttr": len(types) / n,
            "hapax_ratio": hapax / n,
        }

    def _sentence_stats(self, sentences: list[str]) -> dict:
        """Mean / std of sentence lengths (in words)."""
        lens = [len(s.split()) for s in sentences]
        if not lens:
            return {"sent_len_mean": 0.0, "sent_len_std": 0.0, "num_sentences": 0}

        return {
            "sent_len_mean": float(np.mean(lens)),
            "sent_len_std": float(np.std(lens)),
            "num_sentences": len(lens),
        }

    def _readability_scores(
        self, text: str, words: list[str], sentences: list[str]
    ) -> dict:
        """Flesch Reading Ease and Flesch-Kincaid Grade Level."""
        n_words = len(words)
        n_sents = max(len(sentences), 1)
        n_syllables = sum(self._syllable_count(w) for w in words) if words else 0

        if n_words == 0:
            return {"flesch_reading_ease": 0.0, "flesch_kincaid_grade": 0.0}

        asl = n_words / n_sents  # average sentence length
        asw = n_syllables / n_words  # average syllables per word

        fre = 206.835 - 1.015 * asl - 84.6 * asw
        fkg = 0.39 * asl + 11.8 * asw - 15.59

        return {
            "flesch_reading_ease": round(fre, 2),
            "flesch_kincaid_grade": round(fkg, 2),
        }

    def _punctuation_features(self, text: str) -> dict:
        """Normalized counts for punctuation patterns."""
        n = max(len(text), 1)
        return {
            "comma_rate": text.count(",") / n,
            "period_rate": text.count(".") / n,
            "question_rate": text.count("?") / n,
            "exclamation_rate": text.count("!") / n,
        }

    def _word_length_features(self, words: list[str]) -> dict:
        """Statistics on word lengths."""
        if not words:
            return {"word_len_mean": 0.0, "word_len_std": 0.0, "long_word_ratio": 0.0}

        lens = [len(w) for w in words]
        return {
            "word_len_mean": float(np.mean(lens)),
            "word_len_std": float(np.std(lens)),
            "long_word_ratio": sum(1 for l in lens if l > 6) / len(lens),
        }

    def _entropy(self, words: list[str]) -> float:
        """Shannon entropy of the word distribution."""
        if not words:
            return 0.0

        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1

        n = len(words)
        return -sum((c / n) * math.log2(c / n) for c in freq.values())

    def _perplexity_burstiness(self, words: list[str]) -> dict:
        """
        Calculate perplexity and burstiness.

        Perplexity: Measure of how predictable the text is
        Burstiness: Measure of variation in word usage (Gini coefficient)

        AI text typically has lower perplexity and lower burstiness.
        """
        if not words:
            return {"perplexity": 0.0, "burstiness": 0.0}

        # Word frequency distribution
        freq = Counter(words)
        n = len(words)

        # Perplexity (based on entropy)
        entropy = self._entropy(words)
        perplexity = 2**entropy if entropy > 0 else 0.0

        # Burstiness (Gini coefficient of word frequencies)
        sorted_freqs = sorted(freq.values())
        n_unique = len(sorted_freqs)

        if n_unique == 0:
            burstiness = 0.0
        else:
            # Gini coefficient
            cumsum = np.cumsum(sorted_freqs)
            burstiness = (
                2 * sum((i + 1) * f for i, f in enumerate(sorted_freqs))
            ) / (n_unique * sum(sorted_freqs)) - (n_unique + 1) / n_unique

        return {
            "perplexity": round(perplexity, 2),
            "burstiness": round(burstiness, 3),
        }
