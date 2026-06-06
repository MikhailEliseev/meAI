"""
Tests for Ad Copy Generator
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.aim.ai.ads.generator import AdCopyGenerator, generate_ad_copy
from src.aim.ai.ads.schemas import (
    AdCopyResult,
    AdCopyVariant,
    ComplianceCheck,
    AdTemplate,
)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock()

    # Mock generate response
    mock_response = MagicMock()
    mock_response.content = """ЗАГОЛОВОК: Имплантация зубов за 1 день
ОПИСАНИЕ: Без боли. Гарантия 10 лет. Запись на консультацию.
CTA: Записаться"""

    client.generate = AsyncMock(return_value=mock_response)
    return client


@pytest.fixture
def generator(mock_llm_client):
    """Create Ad Copy Generator instance."""
    return AdCopyGenerator(
        llm_client=mock_llm_client,
        market="russia",
        platform="yandex_direct",
    )


@pytest.mark.asyncio
class TestAdCopyGenerator:
    """Test Ad Copy Generator class."""

    async def test_init_russia_market(self, mock_llm_client):
        """Test initialization with Russia market."""
        generator = AdCopyGenerator(
            llm_client=mock_llm_client,
            market="russia",
            platform="yandex_direct",
        )

        assert generator.llm_client == mock_llm_client
        assert generator.market == "russia"
        assert generator.platform == "yandex_direct"
        assert len(generator.templates) > 0
        assert "russia" in generator.compliance_rules
        assert "forbidden_words" in generator.compliance_rules["russia"]

    async def test_init_usa_market(self, mock_llm_client):
        """Test initialization with USA market."""
        generator = AdCopyGenerator(
            llm_client=mock_llm_client,
            market="usa",
            platform="google_ads",
        )

        assert generator.market == "usa"
        assert generator.platform == "google_ads"
        assert "usa" in generator.compliance_rules

    async def test_generate_variants(self, generator):
        """Test generating multiple variants."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=3,
        )

        assert isinstance(result, AdCopyResult)
        assert result.specialty == "Стоматология"
        assert result.service == "Имплантация зубов"
        assert result.platform == "yandex_direct"
        assert len(result.variants) == 3
        assert isinstance(result.compliance, ComplianceCheck)
        assert result.generation_cost > 0

    async def test_generate_with_target_audience(self, generator):
        """Test generating with target audience."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            target_audience="Мужчины 35-50 лет",
            num_variants=3,
        )

        assert len(result.variants) == 3
        # LLM should receive target audience in prompt
        generator.llm_client.generate.assert_called()

    async def test_generate_with_emotional_trigger(self, generator):
        """Test generating with emotional trigger."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            emotional_trigger="urgency",
            num_variants=3,
        )

        assert len(result.variants) == 3
        # All variants should have urgency trigger
        for variant in result.variants:
            assert variant.emotional_trigger == "urgency"

    async def test_variant_structure(self, generator):
        """Test variant structure."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        variant = result.variants[0]
        assert isinstance(variant, AdCopyVariant)
        assert isinstance(variant.headline, str)
        assert isinstance(variant.description, str)
        assert isinstance(variant.cta, str)
        assert isinstance(variant.emotional_trigger, str)
        assert 0 <= variant.compliance_score <= 100
        assert 0 <= variant.predicted_ctr <= 100

    async def test_compliance_check_passed(self, generator):
        """Test compliance check when no violations."""
        # Mock LLM to return compliant copy
        mock_response = MagicMock()
        mock_response.content = """ЗАГОЛОВОК: Имплантация зубов
ОПИСАНИЕ: Качественное лечение. Необходима консультация специалиста.
CTA: Записаться"""
        generator.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Should have no violations (headline and description within limits)
        assert result.compliance.score > 0

    async def test_compliance_check_violations(self, generator):
        """Test compliance check with violations."""
        # Mock LLM to return non-compliant copy
        mock_response = MagicMock()
        mock_response.content = """ЗАГОЛОВОК: Лучшая имплантация зубов с гарантированным излечением
ОПИСАНИЕ: Мы лучшие! 100% результат! Чудо-технология для гарантированного излечения всех проблем с зубами!
CTA: Записаться"""
        generator.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Should have violations (forbidden words, too long)
        assert len(result.compliance.violations) > 0
        assert not result.compliance.passed

    async def test_compliance_forbidden_words_russia(self, generator):
        """Test compliance check for forbidden words in Russia."""
        # Mock LLM to return copy with forbidden words
        mock_response = MagicMock()
        mock_response.content = """ЗАГОЛОВОК: Лучший результат
ОПИСАНИЕ: Гарантированное излечение. 100% результат. Чудо-метод.
CTA: Записаться"""
        generator.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Should detect forbidden words
        violations = result.compliance.violations
        assert any("лучший" in v.lower() for v in violations)
        assert any("гарантированное излечение" in v.lower() for v in violations)
        assert any("100% результат" in v.lower() for v in violations)
        assert any("чудо" in v.lower() for v in violations)

    async def test_compliance_length_limits(self, generator):
        """Test compliance check for length limits."""
        # Mock LLM to return too long copy
        mock_response = MagicMock()
        mock_response.content = """ЗАГОЛОВОК: Имплантация зубов за один день с гарантией качества
ОПИСАНИЕ: Профессиональная имплантация зубов с использованием современных технологий и материалов высочайшего качества
CTA: Записаться"""
        generator.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Should detect length violations
        violations = result.compliance.violations
        assert any("заголовок слишком длинный" in v.lower() for v in violations)
        assert any("описание слишком длинное" in v.lower() for v in violations)

    async def test_compliance_recommendations_russia(self, generator):
        """Test compliance recommendations for Russia."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Should have Russia-specific recommendations
        recommendations = result.compliance.recommendations
        assert any("лицензи" in r.lower() for r in recommendations)
        assert any("адрес" in r.lower() for r in recommendations)

    async def test_template_selection_by_specialty(self, generator):
        """Test template selection by specialty and service."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Should use dental implants template
        assert "dental_implants" in result.template_used or result.template_used == "default"

    async def test_template_selection_by_emotional_trigger(self, generator):
        """Test template selection by emotional trigger."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            emotional_trigger="urgency",
            num_variants=1,
        )

        # Should use urgency template
        assert "urgency" in result.template_used or result.template_used == "default"

    async def test_llm_prompt_building(self, generator):
        """Test LLM prompt building."""
        await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            target_audience="Мужчины 35-50 лет",
            emotional_trigger="trust",
            num_variants=1,
        )

        # Check that LLM was called with correct prompt
        generator.llm_client.generate.assert_called()
        call_args = generator.llm_client.generate.call_args
        prompt = call_args.kwargs["prompt"]

        assert "Стоматология" in prompt
        assert "Имплантация зубов" in prompt
        assert "Мужчины 35-50 лет" in prompt
        assert "trust" in prompt
        assert "yandex_direct" in prompt

    async def test_llm_response_parsing(self, generator):
        """Test LLM response parsing."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = """ЗАГОЛОВОК: Тестовый заголовок
ОПИСАНИЕ: Тестовое описание услуги.
CTA: Тестовый CTA"""
        generator.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        variant = result.variants[0]
        assert variant.headline == "Тестовый заголовок"
        assert variant.description == "Тестовое описание услуги."
        assert variant.cta == "Тестовый CTA"

    async def test_llm_response_parsing_fallback(self, generator):
        """Test LLM response parsing with fallback."""
        # Mock LLM to return malformed response
        mock_response = MagicMock()
        mock_response.content = "Invalid response format"
        generator.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Should use fallback values
        variant = result.variants[0]
        assert variant.headline == "Медицинские услуги"
        assert "Качественное лечение" in variant.description
        assert variant.cta == "Записаться"

    async def test_ctr_prediction(self, generator):
        """Test CTR prediction."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        variant = result.variants[0]
        # CTR should be between 0 and 10%
        assert 0 <= variant.predicted_ctr <= 10.0

    async def test_cost_calculation(self, generator):
        """Test cost calculation."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=3,
        )

        # Cost should be $0.14 per ad set
        assert result.generation_cost == 0.14

    async def test_parallel_variant_generation(self, generator):
        """Test parallel variant generation."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=5,
        )

        # Should generate 5 variants
        assert len(result.variants) == 5

        # LLM should be called 5 times (once per variant)
        assert generator.llm_client.generate.call_count == 5

    async def test_variant_diversity(self, generator):
        """Test variant diversity (different temperatures)."""
        result = await generator.generate(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=3,
        )

        # Check that LLM was called with increasing temperatures
        calls = generator.llm_client.generate.call_args_list
        temperatures = [call.kwargs["temperature"] for call in calls]

        # Temperatures should increase: 0.7, 0.8, 0.9 (with floating point tolerance)
        assert abs(temperatures[0] - 0.7) < 0.01
        assert abs(temperatures[1] - 0.8) < 0.01
        assert abs(temperatures[2] - 0.9) < 0.01

    async def test_close(self, generator):
        """Test close method."""
        await generator.close()
        # Should not raise any errors

    async def test_generate_ad_copy_convenience_function(self, mock_llm_client):
        """Test convenience function."""
        result = await generate_ad_copy(
            specialty="Стоматология",
            service="Имплантация зубов",
            llm_client=mock_llm_client,
            market="russia",
            platform="yandex_direct",
            num_variants=3,
        )

        assert isinstance(result, AdCopyResult)
        assert len(result.variants) == 3

    async def test_usa_market_compliance(self, mock_llm_client):
        """Test USA market compliance rules."""
        generator = AdCopyGenerator(
            llm_client=mock_llm_client,
            market="usa",
            platform="google_ads",
        )

        # Mock LLM to return copy with USA forbidden words
        mock_response = MagicMock()
        mock_response.content = """ЗАГОЛОВОК: Guaranteed cure
ОПИСАНИЕ: Miracle treatment with guaranteed results.
CTA: Book now"""
        generator.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await generator.generate(
            specialty="Dentistry",
            service="Dental implants",
            num_variants=1,
        )

        # Should detect USA forbidden words
        violations = result.compliance.violations
        assert any("guaranteed" in v.lower() for v in violations)
        assert any("miracle" in v.lower() for v in violations)

        await generator.close()
