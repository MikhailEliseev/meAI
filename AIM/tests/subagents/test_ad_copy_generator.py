"""Tests for Ad Copy Generator."""

import pytest

from AIM.src.aim.subagents.ads.ad_copy_generator import (
    AdCopyGenerator,
    AdCopySet,
    AdHeadline,
    AdDescription,
    CallToAction,
    ComplianceCheck,
    AdCopyVariant,
)


@pytest.fixture
def generator():
    """Create Ad Copy Generator instance."""
    return AdCopyGenerator()


@pytest.mark.asyncio
async def test_generate_ad_copy_set(generator):
    """Test complete ad copy set generation."""
    ad_copy_set = await generator.generate(
        target_keyword="зубные имплантаты",
        product_name="Имплантаты Nobel",
        benefits=["Пожизненная гарантия", "Установка за 1 день"],
        platform="both",
    )

    assert isinstance(ad_copy_set, AdCopySet)
    assert ad_copy_set.target_keyword == "зубные имплантаты"
    assert ad_copy_set.total_variants > 0
    assert ad_copy_set.total_headlines > 0
    assert ad_copy_set.total_descriptions > 0
    assert ad_copy_set.total_ctas > 0
    assert len(ad_copy_set.yandex_variants) > 0
    assert len(ad_copy_set.google_variants) > 0


@pytest.mark.asyncio
async def test_generate_yandex_only(generator):
    """Test Yandex-only ad copy generation."""
    ad_copy_set = await generator.generate(
        target_keyword="стоматология",
        product_name="Клиника Дента",
        benefits=["Опытные врачи"],
        platform="yandex",
    )

    assert len(ad_copy_set.yandex_variants) > 0
    assert len(ad_copy_set.google_variants) == 0
    assert all(v.platform == "yandex" for v in ad_copy_set.variants)


@pytest.mark.asyncio
async def test_generate_google_only(generator):
    """Test Google-only ad copy generation."""
    ad_copy_set = await generator.generate(
        target_keyword="стоматология",
        product_name="Клиника Дента",
        benefits=["Опытные врачи"],
        platform="google",
    )

    assert len(ad_copy_set.google_variants) > 0
    assert len(ad_copy_set.yandex_variants) == 0
    assert all(v.platform == "google" for v in ad_copy_set.variants)


def test_generate_headlines(generator):
    """Test headline generation."""
    headlines = generator._generate_headlines(
        keyword="имплантаты",
        product="Nobel Biocare",
        benefits=["Пожизненная гарантия", "Установка за 1 день"],
    )

    assert len(headlines) > 0
    assert all(isinstance(h, AdHeadline) for h in headlines)
    assert all(h.length <= 56 for h in headlines)  # Yandex limit
    assert any(h.variant_type == "benefit" for h in headlines)
    assert any(h.variant_type == "question" for h in headlines)


def test_generate_descriptions(generator):
    """Test description generation."""
    descriptions = generator._generate_descriptions(
        keyword="имплантаты",
        product="Nobel Biocare",
        benefits=["Пожизненная гарантия", "Установка за 1 день"],
    )

    assert len(descriptions) > 0
    assert all(isinstance(d, AdDescription) for d in descriptions)
    assert all(d.length <= 81 for d in descriptions)  # Yandex limit
    assert any(d.includes_cta for d in descriptions)


def test_generate_ctas(generator):
    """Test CTA generation."""
    ctas = generator._generate_ctas()

    assert len(ctas) > 0
    assert all(isinstance(c, CallToAction) for c in ctas)
    assert any(c.urgency_level == "high" for c in ctas)
    assert any(c.urgency_level == "medium" for c in ctas)
    assert any(c.urgency_level == "low" for c in ctas)
    assert any(c.action_type == "buy" for c in ctas)
    assert any(c.action_type == "learn" for c in ctas)


def test_create_variants(generator):
    """Test variant creation."""
    headlines = [
        AdHeadline(text="Test Headline", length=12, variant_type="benefit"),
    ]
    descriptions = [
        AdDescription(text="Test Description", length=16, includes_cta=True, cta_text="Learn"),
    ]
    ctas = [
        CallToAction(text="Learn More", urgency_level="low", action_type="learn"),
    ]

    variants = generator._create_variants(headlines, descriptions, ctas, "both")

    assert len(variants) > 0
    assert all(isinstance(v, AdCopyVariant) for v in variants)
    assert any(v.platform == "yandex" for v in variants)
    assert any(v.platform == "google" for v in variants)


def test_check_compliance_valid(generator):
    """Test compliance check for valid ad copy."""
    compliance = generator._check_compliance(
        headline="Имплантаты Nobel Biocare",
        description="Пожизненная гарантия. Установка за 1 день.",
        platform="yandex",
    )

    assert isinstance(compliance, ComplianceCheck)
    assert compliance.platform == "yandex"
    assert compliance.is_compliant is True
    assert len(compliance.violations) == 0


def test_check_compliance_forbidden_words(generator):
    """Test compliance check with forbidden words."""
    compliance = generator._check_compliance(
        headline="Лучший имплантат",
        description="100% гарантия качества",
        platform="yandex",
    )

    assert compliance.is_compliant is False
    assert len(compliance.violations) > 0
    assert any("лучший" in v.lower() for v in compliance.violations)


def test_check_compliance_length_limit(generator):
    """Test compliance check with length violations."""
    long_headline = "A" * 60  # Exceeds Yandex limit (56)
    compliance = generator._check_compliance(
        headline=long_headline,
        description="Test",
        platform="yandex",
    )

    assert compliance.is_compliant is False
    assert any("превышает лимит" in v for v in compliance.violations)


def test_check_compliance_warnings(generator):
    """Test compliance check warnings."""
    compliance = generator._check_compliance(
        headline="ИМПЛАНТАТЫ!!!",
        description="Купите сейчас!!!",
        platform="yandex",
    )

    assert len(compliance.warnings) > 0
    assert any("верхнем регистре" in w for w in compliance.warnings)
    assert any("восклицательных знаков" in w for w in compliance.warnings)


def test_platform_limits(generator):
    """Test platform-specific limits."""
    assert generator.limits["yandex"]["headline_max"] == 56
    assert generator.limits["yandex"]["description_max"] == 81
    assert generator.limits["google"]["headline_max"] == 30
    assert generator.limits["google"]["description_max"] == 90


def test_forbidden_words_list(generator):
    """Test forbidden words list."""
    assert len(generator.forbidden_words) > 0
    assert "лучший" in generator.forbidden_words
    assert "100%" in generator.forbidden_words
    assert "бесплатно" in generator.forbidden_words
