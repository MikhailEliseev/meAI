"""
Conversational Search Optimizer

Optimizes content for AI-powered search engines:
- Google AI Overviews
- ChatGPT Search
- Perplexity AI

Focuses on citability, answer-box readiness, and conversational queries.
"""

import re
from typing import List, Dict, Any, Optional
from collections import Counter

from ..llm.client import LLMClient
from ..llm.schemas import LLMRequest
from .schemas import ConversationalOptimization


class ConversationalOptimizer:
    """
    Conversational search optimization analyzer.

    Features:
    - AI Overviews readiness scoring
    - ChatGPT citability analysis
    - Perplexity optimization
    - Conversational query generation
    - Answer box readiness check
    - FAQ suggestions
    - Citation score calculation
    """

    # Citation signals
    CITATION_SIGNALS = {
        "structured_data": 15,  # Schema.org markup
        "clear_answers": 20,    # Direct answers to questions
        "authoritative": 15,    # Author credentials, sources
        "recent": 10,           # Publication date, freshness
        "comprehensive": 15,    # Depth and breadth
        "readable": 10,         # Clear, concise language
        "multimedia": 10,       # Images, videos, diagrams
        "sources": 5,           # External citations
    }

    def __init__(self, llm_client: LLMClient):
        """
        Initialize conversational optimizer.

        Args:
            llm_client: LLM client for query generation
        """
        self.llm_client = llm_client

    async def analyze(
        self,
        content: str,
        url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationalOptimization:
        """
        Analyze conversational search optimization.

        Args:
            content: HTML content
            url: Page URL
            metadata: Optional metadata

        Returns:
            ConversationalOptimization with scores and suggestions
        """
        # Extract text
        text = self._extract_text(content)

        # Calculate AI Overviews score
        ai_overviews_score = self._score_ai_overviews(text, content, metadata)

        # Calculate ChatGPT score
        chatgpt_score = self._score_chatgpt(text, content, metadata)

        # Calculate Perplexity score
        perplexity_score = self._score_perplexity(text, content, metadata)

        # Generate conversational queries
        conversational_queries = await self._generate_conversational_queries(text, metadata)

        # Check answer box readiness
        answer_box_ready = self._check_answer_box_readiness(text, content)

        # Generate FAQ suggestions
        faq_suggestions = await self._generate_faq_suggestions(text, metadata)

        # Calculate citation score
        citation_score = self._calculate_citation_score(content, metadata)

        return ConversationalOptimization(
            ai_overviews_score=ai_overviews_score,
            chatgpt_score=chatgpt_score,
            perplexity_score=perplexity_score,
            conversational_queries=conversational_queries,
            answer_box_ready=answer_box_ready,
            faq_suggestions=faq_suggestions,
            citation_score=citation_score,
        )

    def _extract_text(self, html: str) -> str:
        """Extract clean text from HTML."""
        # Remove script and style tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&quot;", '"')
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")

        # Clean whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _score_ai_overviews(
        self,
        text: str,
        content: str,
        metadata: Optional[Dict[str, Any]],
    ) -> float:
        """
        Score for Google AI Overviews.

        Criteria:
        - Structured data (schema.org)
        - Clear, direct answers
        - Authoritative signals
        - Recent content
        - Comprehensive coverage

        Args:
            text: Clean text
            content: HTML content
            metadata: Optional metadata

        Returns:
            Score 0-100
        """
        score = 0.0

        # Structured data (20 points)
        if 'application/ld+json' in content or 'itemscope' in content:
            score += 20

        # Direct answers (20 points)
        # Check for question-answer patterns
        qa_patterns = [
            r"что такое .{5,50}\?",
            r"как .{5,50}\?",
            r"почему .{5,50}\?",
            r"когда .{5,50}\?",
            r"где .{5,50}\?",
        ]
        has_questions = any(re.search(pattern, text, re.IGNORECASE) for pattern in qa_patterns)
        if has_questions:
            score += 10

        # Check for answer patterns (lists, definitions)
        if re.search(r"^\d+\.", text, re.MULTILINE) or re.search(r"^[-•]", text, re.MULTILINE):
            score += 10

        # Authoritative signals (15 points)
        auth_signals = ["автор:", "источник:", "исследование", "данные", "статистика"]
        auth_count = sum(1 for signal in auth_signals if signal in text.lower())
        score += min(auth_count * 3, 15)

        # Recent content (10 points)
        if metadata:
            pub_date = metadata.get("published_date")
            if pub_date:
                score += 10

        # Comprehensive coverage (15 points)
        word_count = len(text.split())
        if word_count > 1500:
            score += 15
        elif word_count > 1000:
            score += 10
        elif word_count > 500:
            score += 5

        # Readability (10 points)
        avg_sentence_length = self._calculate_avg_sentence_length(text)
        if 10 <= avg_sentence_length <= 20:
            score += 10
        elif 8 <= avg_sentence_length <= 25:
            score += 5

        # Multimedia (10 points)
        if '<img' in content:
            score += 5
        if '<video' in content or 'youtube.com' in content:
            score += 5

        return min(score, 100.0)

    def _score_chatgpt(
        self,
        text: str,
        content: str,
        metadata: Optional[Dict[str, Any]],
    ) -> float:
        """
        Score for ChatGPT citability.

        Criteria:
        - Clear, quotable statements
        - Factual accuracy signals
        - Source attribution
        - Structured information
        - Conversational tone

        Args:
            text: Clean text
            content: HTML content
            metadata: Optional metadata

        Returns:
            Score 0-100
        """
        score = 0.0

        # Clear statements (25 points)
        # Check for declarative sentences
        sentences = re.split(r'[.!?]+', text)
        clear_sentences = [s for s in sentences if 10 <= len(s.split()) <= 30]
        if len(clear_sentences) > 10:
            score += 25
        elif len(clear_sentences) > 5:
            score += 15

        # Factual signals (20 points)
        fact_signals = ["согласно", "исследование показало", "данные", "статистика", "процент"]
        fact_count = sum(1 for signal in fact_signals if signal in text.lower())
        score += min(fact_count * 4, 20)

        # Source attribution (15 points)
        if "источник:" in text.lower() or "по данным" in text.lower():
            score += 15

        # Structured information (20 points)
        if re.search(r"^\d+\.", text, re.MULTILINE):
            score += 10
        if '<table' in content or '<ul' in content or '<ol' in content:
            score += 10

        # Conversational tone (20 points)
        conversational_markers = ["вы можете", "рекомендуем", "важно знать", "обратите внимание"]
        conv_count = sum(1 for marker in conversational_markers if marker in text.lower())
        score += min(conv_count * 5, 20)

        return min(score, 100.0)

    def _score_perplexity(
        self,
        text: str,
        content: str,
        metadata: Optional[Dict[str, Any]],
    ) -> float:
        """
        Score for Perplexity AI optimization.

        Criteria:
        - Comprehensive answers
        - Multiple perspectives
        - Recent information
        - Source diversity
        - Technical depth

        Args:
            text: Clean text
            content: HTML content
            metadata: Optional metadata

        Returns:
            Score 0-100
        """
        score = 0.0

        # Comprehensive answers (30 points)
        word_count = len(text.split())
        if word_count > 2000:
            score += 30
        elif word_count > 1500:
            score += 20
        elif word_count > 1000:
            score += 10

        # Multiple perspectives (20 points)
        perspective_markers = ["с одной стороны", "с другой стороны", "однако", "в то же время"]
        persp_count = sum(1 for marker in perspective_markers if marker in text.lower())
        score += min(persp_count * 5, 20)

        # Recent information (15 points)
        if metadata and metadata.get("published_date"):
            score += 15

        # Source diversity (20 points)
        if "источник:" in text.lower():
            source_count = text.lower().count("источник:")
            score += min(source_count * 5, 20)

        # Technical depth (15 points)
        technical_markers = ["механизм", "процесс", "алгоритм", "метод", "технология"]
        tech_count = sum(1 for marker in technical_markers if marker in text.lower())
        score += min(tech_count * 3, 15)

        return min(score, 100.0)

    async def _generate_conversational_queries(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[str]:
        """
        Generate conversational queries using LLM.

        Args:
            text: Content text
            metadata: Optional metadata

        Returns:
            List of conversational queries
        """
        # Extract topic from metadata or text
        topic = metadata.get("title", "") if metadata else ""
        if not topic:
            # Use first sentence as topic
            sentences = re.split(r'[.!?]+', text)
            topic = sentences[0] if sentences else text[:100]

        prompt = f"""Сгенерируй 5 разговорных поисковых запросов для темы: "{topic}"

Требования:
- Естественный разговорный язык (как люди спрашивают голосом)
- Вопросительная форма
- Длина 5-15 слов
- Разные типы вопросов (что, как, почему, когда, где)

Примеры:
- "Как выбрать стоматологическую клинику в Москве"
- "Что такое имплантация зубов и сколько это стоит"
- "Почему болит зуб после лечения канала"

Верни только список запросов, по одному на строку."""

        try:
            response = await self.llm_client.generate(
                LLMRequest(
                    prompt=prompt,
                    model="claude-haiku-4",  # Fast model for simple task
                    max_tokens=500,
                    temperature=0.8,
                )
            )

            # Parse queries from response
            queries = [
                line.strip().lstrip("-•").strip()
                for line in response.content.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

            return queries[:5]

        except Exception:
            # Fallback to template-based generation
            return [
                f"Что такое {topic}",
                f"Как работает {topic}",
                f"Почему важно {topic}",
                f"Где найти {topic}",
                f"Когда нужно {topic}",
            ]

    def _check_answer_box_readiness(self, text: str, content: str) -> bool:
        """
        Check if content is ready for answer boxes.

        Criteria:
        - Has clear question-answer structure
        - Has structured data (FAQ schema)
        - Has concise answers (50-300 chars)
        - Has proper formatting (lists, paragraphs)

        Args:
            text: Clean text
            content: HTML content

        Returns:
            True if ready for answer boxes
        """
        # Check for FAQ schema
        has_faq_schema = 'FAQPage' in content or 'Question' in content

        # Check for question patterns
        qa_patterns = [
            r"что такое .{5,50}\?",
            r"как .{5,50}\?",
            r"почему .{5,50}\?",
        ]
        has_questions = any(re.search(pattern, text, re.IGNORECASE) for pattern in qa_patterns)

        # Check for structured formatting
        has_structure = '<ul' in content or '<ol' in content or re.search(r"^\d+\.", text, re.MULTILINE)

        # Check for concise answers
        sentences = re.split(r'[.!?]+', text)
        concise_sentences = [s for s in sentences if 50 <= len(s) <= 300]
        has_concise = len(concise_sentences) >= 3

        # Ready if at least 3 criteria met
        criteria_met = sum([has_faq_schema, has_questions, has_structure, has_concise])
        return criteria_met >= 3

    async def _generate_faq_suggestions(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        Generate FAQ suggestions using LLM.

        Args:
            text: Content text
            metadata: Optional metadata

        Returns:
            List of FAQ items (question + answer)
        """
        # Extract topic
        topic = metadata.get("title", "") if metadata else ""
        if not topic:
            sentences = re.split(r'[.!?]+', text)
            topic = sentences[0] if sentences else text[:100]

        prompt = f"""Сгенерируй 3 FAQ вопроса-ответа для темы: "{topic}"

Требования:
- Вопросы должны быть частыми и релевантными
- Ответы краткие (2-3 предложения, 100-200 символов)
- Формат: Q: вопрос\nA: ответ

Пример:
Q: Сколько стоит имплантация зуба?
A: Стоимость имплантации зуба в Москве варьируется от 30 000 до 80 000 рублей. Цена зависит от производителя имплантата, сложности случая и клиники.

Верни 3 пары вопрос-ответ."""

        try:
            response = await self.llm_client.generate(
                LLMRequest(
                    prompt=prompt,
                    model="claude-haiku-4",
                    max_tokens=800,
                    temperature=0.7,
                )
            )

            # Parse FAQ items
            faq_items = []
            lines = response.content.split("\n")
            current_q = None

            for line in lines:
                line = line.strip()
                if line.startswith("Q:"):
                    current_q = line[2:].strip()
                elif line.startswith("A:") and current_q:
                    answer = line[2:].strip()
                    faq_items.append({"question": current_q, "answer": answer})
                    current_q = None

            return faq_items[:3]

        except Exception:
            # Return empty list on error
            return []

    def _calculate_citation_score(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]],
    ) -> float:
        """
        Calculate citation score (0-100).

        Based on signals that make content citable by AI.

        Args:
            content: HTML content
            metadata: Optional metadata

        Returns:
            Citation score 0-100
        """
        score = 0.0

        # Structured data (15 points)
        if 'application/ld+json' in content or 'itemscope' in content:
            score += self.CITATION_SIGNALS["structured_data"]

        # Clear answers (20 points)
        if re.search(r"что такое|как |почему ", content, re.IGNORECASE):
            score += self.CITATION_SIGNALS["clear_answers"]

        # Authoritative (15 points)
        if "автор:" in content.lower() or "источник:" in content.lower():
            score += self.CITATION_SIGNALS["authoritative"]

        # Recent (10 points)
        if metadata and metadata.get("published_date"):
            score += self.CITATION_SIGNALS["recent"]

        # Comprehensive (15 points)
        word_count = len(content.split())
        if word_count > 1500:
            score += self.CITATION_SIGNALS["comprehensive"]

        # Readable (10 points)
        text = self._extract_text(content)
        avg_sentence_length = self._calculate_avg_sentence_length(text)
        if 10 <= avg_sentence_length <= 20:
            score += self.CITATION_SIGNALS["readable"]

        # Multimedia (10 points)
        if '<img' in content or '<video' in content:
            score += self.CITATION_SIGNALS["multimedia"]

        # Sources (5 points)
        if content.lower().count("источник:") > 0:
            score += self.CITATION_SIGNALS["sources"]

        return min(score, 100.0)

    def _calculate_avg_sentence_length(self, text: str) -> float:
        """Calculate average sentence length in words."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        total_words = sum(len(s.split()) for s in sentences)
        return total_words / len(sentences)
