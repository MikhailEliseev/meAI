"""Tests for ФЗ-38 medical advertising compliance."""
import pytest
from aim.subagents.ads.ad_copy_generator import AdCopyGenerator, ComplianceCheck


DISCLAIMER = "ИМЕЮТСЯ ПРОТИВОПОКАЗАНИЯ, НЕОБХОДИМА КОНСУЛЬТАЦИЯ СПЕЦИАЛИСТА"


@pytest.fixture
def generator():
    return AdCopyGenerator()


def test_medical_disclaimer_required(generator):
    """Medical ad without disclaimer → violation."""
    result = generator._check_compliance(
        headline="Имплантация зубов",
        description="Установка имплантов. Запишитесь сегодня.",
        platform="yandex",
    )
    assert not result.is_compliant
    assert any("ФЗ-38" in v and "отсутствует" in v for v in result.violations), (
        f"Expected ФЗ-38 disclaimer violation, got: {result.violations}"
    )


def test_medical_disclaimer_present_passes(generator):
    """Medical ad WITH disclaimer → compliant (description within Yandex 81-char limit)."""
    result = generator._check_compliance(
        headline="Имплантация зубов",
        description=DISCLAIMER,
        platform="yandex",
    )
    assert result.is_compliant


def test_non_medical_ad_no_disclaimer_needed(generator):
    """Non-medical ad without disclaimer → still compliant."""
    result = generator._check_compliance(
        headline="Маркетинговое агентство AIM",
        description="Продвижение бизнеса. Узнайте больше.",
        platform="yandex",
    )
    fz38_violations = [v for v in result.violations if "ФЗ-38" in v]
    assert len(fz38_violations) == 0


def test_prohibited_efficacy_claim(generator):
    """Medical ad with 'гарантированный результат' → violation."""
    result = generator._check_compliance(
        headline="Лечение зубов — гарантированный результат",
        description=DISCLAIMER,
        platform="yandex",
    )
    assert any("запрещённое утверждение" in v for v in result.violations), (
        f"Expected prohibited claim violation, got: {result.violations}"
    )
    # Disclaimer is present, so no disclaimer violation
    assert not any("отсутствует" in v for v in result.violations)


def test_age_restriction_warning_16plus(generator):
    """Medical ad with 16+ → warning (should be 18+)."""
    result = generator._check_compliance(
        headline="Стоматология 16+",
        description=DISCLAIMER,
        platform="yandex",
    )
    assert any("18+" in w for w in result.warnings), (
        f"Expected 18+ age warning, got: {result.warnings}"
    )


def test_age_restriction_18plus_ok(generator):
    """Medical ad with 18+ → no age violation warning."""
    result = generator._check_compliance(
        headline="Стоматология 18+",
        description=DISCLAIMER,
        platform="yandex",
    )
    age_violation_warnings = [w for w in result.warnings if "18+" in w and "рекомендуется" not in w]
    assert len(age_violation_warnings) == 0


def test_erir_warning(generator):
    """Medical ad without ЕРИР token → warning."""
    result = generator._check_compliance(
        headline="Лечение зубов 18+",
        description=DISCLAIMER,
        platform="yandex",
    )
    assert any("ЕРИР" in w for w in result.warnings), (
        f"Expected ЕРИР warning, got: {result.warnings}"
    )
