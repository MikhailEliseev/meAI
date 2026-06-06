"""Tests for AI-enhanced Content Magister

Tests integration of AI components with Content Magister:
- Content Generator integration
- Content Optimizer integration
- Readability Analyzer integration
- SEO Content Analyzer integration

Part of: Phase 10 - AI Enhancement (Task 2.3)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.aim.magisters.content_magister_ai import ContentMagisterAI
from src.aim.ai.llm.schemas import LLMResponse


class TestContentMagisterAI:
    """Test AI-enhanced Content Magister"""

    @pytest.fixture
    async def magister(self):
        """Create AI-enhanced Content Magister instance"""
        # Mock LLM client
        llm_client = AsyncMock()
        llm_client.close = AsyncMock()

        # Mock vault
        vault = MagicMock()
        vault.vault_path = MagicMock()
        vault.vault_path.__truediv__ = lambda self, x: MagicMock(exists=lambda: False)

        magister = ContentMagisterAI(
            magister_id="test-content-magister-ai",
            database_url="sqlite+aiosqlite:///:memory:",
            vault_path="./test_vault",
            llm_client=llm_client,
            vault=vault,
        )

        yield magister

        await magister.close()

    async def test_initialization(self, magister):
        """Test AI-enhanced Content Magister initialization"""
        assert magister.magister_id == "test-content-magister-ai"
        assert magister.llm_client is not None

    async def test_generate_content(self, magister):
        """Test content generation"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""# Dental Implants: Complete Guide

## Introduction
Dental implants are a modern solution for missing teeth...

## Benefits
- Permanent solution
- Natural appearance
- Improved function

## Procedure
The implant procedure involves several steps...""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=500,
            input_tokens=100,
            output_tokens=400,
            cost_usd=0.015,
            latency_ms=1200,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Generate content
        result = await magister.generate_content(
            topic="Dental Implants",
            content_type="article",
            target_audience="Patients considering dental implants",
            tone="professional",
            word_count=1000,
        )

        # Verify result
        assert result["topic"] == "Dental Implants"
        assert result["content_type"] == "article"
        assert "Dental implants" in result["content"]
        assert result["word_count"] > 0
        assert result["generation_cost"] == 0.015
        assert result["metadata"]["target_audience"] == "Patients considering dental implants"
        assert result["metadata"]["tone"] == "professional"

    async def test_optimize_content(self, magister):
        """Test content optimization"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""## Optimized Content
# Dental Implants: Your Complete Guide

## What Are Dental Implants?
Dental implants offer a permanent solution for missing teeth. They look natural and function like real teeth.

## Key Benefits
- Long-lasting results
- Natural appearance
- Better chewing ability

## The Procedure
Getting dental implants involves a simple, proven process...

## Improvements Made
- Simplified language for better readability
- Added clear headings for structure
- Shortened sentences for clarity
- Added patient-friendly terminology""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=400,
            input_tokens=150,
            output_tokens=250,
            cost_usd=0.012,
            latency_ms=1000,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Optimize content
        original_content = "Dental implants are titanium posts surgically positioned..."
        result = await magister.optimize_content(
            content=original_content,
            optimization_goals=["readability", "engagement"],
        )

        # Verify result
        assert result["original_content"] == original_content
        assert "Dental Implants" in result["optimized_content"]
        assert len(result["improvements"]) > 0
        assert "readability" in result["optimization_goals"]
        assert result["optimization_cost"] == 0.012

    async def test_analyze_readability(self, magister):
        """Test readability analysis"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""Score: 75
Reading Level: 10th grade
Issues:
- Some sentences are too long (>25 words)
- Technical jargon not explained
- Passive voice used frequently
Recommendations:
- Break long sentences into shorter ones
- Add definitions for technical terms
- Use more active voice
- Add transition words for flow""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=200,
            input_tokens=100,
            output_tokens=100,
            cost_usd=0.006,
            latency_ms=800,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Analyze readability
        content = "The osseointegration process of dental implants..."
        result = await magister.analyze_readability(content=content)

        # Verify result
        assert result["score"] == 75.0
        assert result["reading_level"] == "10th grade"
        assert len(result["issues"]) == 3
        assert len(result["recommendations"]) == 4
        assert result["analysis_cost"] == 0.006

    async def test_analyze_seo_content(self, magister):
        """Test SEO content analysis"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""Score: 82
Keyword Usage:
- dental implants: Good frequency (5 times), natural placement in headings and body
- tooth replacement: Underused (1 time), needs more mentions
- implant procedure: Well-placed (3 times), good context
Issues:
- Missing meta description optimization
- Keyword density too low for "tooth replacement"
- No internal linking suggestions
Recommendations:
- Add "tooth replacement" 2-3 more times naturally
- Include keyword in first paragraph
- Add related keywords (dental surgery, permanent teeth)
- Optimize headings with target keywords""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=300,
            input_tokens=150,
            output_tokens=150,
            cost_usd=0.009,
            latency_ms=900,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Analyze SEO
        content = "Dental implants are the best solution for missing teeth..."
        result = await magister.analyze_seo_content(
            content=content,
            target_keywords=["dental implants", "tooth replacement", "implant procedure"],
        )

        # Verify result
        assert result["score"] == 82.0
        assert len(result["target_keywords"]) == 3
        assert "dental implants" in result["keyword_usage"]
        assert len(result["issues"]) == 3
        assert len(result["recommendations"]) == 4
        assert result["analysis_cost"] == 0.009

    async def test_generate_content_minimal_params(self, magister):
        """Test content generation with minimal parameters"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="# Simple Article\n\nContent here...",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=100,
            input_tokens=50,
            output_tokens=50,
            cost_usd=0.003,
            latency_ms=600,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Generate content with minimal params
        result = await magister.generate_content(
            topic="Test Topic",
            content_type="blog_post",
        )

        # Verify result
        assert result["topic"] == "Test Topic"
        assert result["content_type"] == "blog_post"
        assert result["metadata"]["target_audience"] is None
        assert result["metadata"]["tone"] is None

    async def test_optimize_content_multiple_goals(self, magister):
        """Test content optimization with multiple goals"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""## Optimized Content
Optimized text here...

## Improvements Made
- Improved readability
- Enhanced SEO
- Better engagement
- Clearer structure""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=200,
            input_tokens=100,
            output_tokens=100,
            cost_usd=0.006,
            latency_ms=700,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Optimize with multiple goals
        result = await magister.optimize_content(
            content="Original content",
            optimization_goals=["readability", "seo", "engagement", "clarity"],
        )

        # Verify result
        assert len(result["optimization_goals"]) == 4
        assert len(result["improvements"]) == 4

    async def test_analyze_readability_low_score(self, magister):
        """Test readability analysis with low score"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""Score: 45
Reading Level: Graduate
Issues:
- Very complex sentences
- Heavy use of jargon
- Poor structure
Recommendations:
- Simplify language
- Add examples
- Break into sections""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=150,
            input_tokens=80,
            output_tokens=70,
            cost_usd=0.0045,
            latency_ms=650,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Analyze readability
        result = await magister.analyze_readability(content="Complex content...")

        # Verify low score
        assert result["score"] == 45.0
        assert result["reading_level"] == "Graduate"
        assert len(result["issues"]) > 0

    async def test_analyze_seo_content_multiple_keywords(self, magister):
        """Test SEO analysis with multiple keywords"""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""Score: 88
Keyword Usage:
- keyword1: Excellent
- keyword2: Good
- keyword3: Fair
- keyword4: Poor
- keyword5: Excellent
Issues:
- keyword4 underused
Recommendations:
- Add more keyword4 mentions""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=250,
            input_tokens=120,
            output_tokens=130,
            cost_usd=0.0075,
            latency_ms=850,
        )

        magister.llm_client.generate = AsyncMock(return_value=mock_response)

        # Analyze with 5 keywords
        result = await magister.analyze_seo_content(
            content="Content with keywords...",
            target_keywords=["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
        )

        # Verify result
        assert result["score"] == 88.0
        assert len(result["target_keywords"]) == 5
        assert len(result["keyword_usage"]) == 5

    async def test_close_cleanup(self, magister):
        """Test proper cleanup on close"""
        # Close magister
        await magister.close()

        # Verify LLM client closed
        magister.llm_client.close.assert_called_once()
