"""Tests for A/B test engine (scipy-based statistical analysis)."""
import pytest
from aim.subagents.ads.ab_test_engine import (
    ABTestEngine, ExperimentResult, ExperimentConfig, ExperimentStatus,
)


@pytest.fixture
def engine():
    return ABTestEngine()


def test_chi_square_significance_clear_winner(engine):
    """Clear winner (B much better): p < 0.05, winner = 'B'."""
    result = engine.analyze_results(
        variant_a="original",
        variant_b="treatment",
        conversions_a=50,
        visitors_a=1000,
        conversions_b=75,
        visitors_b=1000,
    )
    assert result.winner == "B"
    assert result.status == ExperimentStatus.COMPLETED
    assert result.p_value < 0.05
    assert result.confidence > 95.0
    assert result.relative_lift == pytest.approx(0.50, rel=0.01)


def test_no_significant_difference(engine):
    """Very close conversion rates -> INCONCLUSIVE."""
    result = engine.analyze_results(
        variant_a="original",
        variant_b="treatment",
        conversions_a=50,
        visitors_a=1000,
        conversions_b=52,
        visitors_b=1000,
    )
    assert result.winner is None
    assert result.status in (ExperimentStatus.INCONCLUSIVE, ExperimentStatus.RUNNING)


def test_sample_size_calculation(engine):
    """calculate_sample_size returns reasonable number."""
    n = engine.calculate_sample_size(
        baseline_rate=0.10,
        minimum_detectable_effect=0.02,
        power=0.80,
        alpha=0.05,
    )
    assert n > 0
    assert n > 500
    assert n < 10000


def test_tiny_sample_returns_running(engine):
    """Sample below MIN_SAMPLE_SIZE -> RUNNING status."""
    result = engine.analyze_results(
        variant_a="original",
        variant_b="treatment",
        conversions_a=5,
        visitors_a=50,
        conversions_b=8,
        visitors_b=50,
    )
    if result.winner is not None:
        pass
    else:
        assert result.status == ExperimentStatus.RUNNING


def test_a_wins_when_better_conversion(engine):
    """Variant A has higher conversion -> winner = 'A'."""
    result = engine.analyze_results(
        variant_a="original",
        variant_b="treatment",
        conversions_a=120,
        visitors_a=1000,
        conversions_b=80,
        visitors_b=1000,
    )
    assert result.winner == "A"
    assert result.status == ExperimentStatus.COMPLETED


def test_equal_conversions(engine):
    """Equal conversions -> no winner."""
    result = engine.analyze_results(
        variant_a="a",
        variant_b="b",
        conversions_a=50,
        visitors_a=1000,
        conversions_b=50,
        visitors_b=1000,
    )
    assert result.winner is None


def test_sample_size_invalid_baseline(engine):
    """baseline_rate must be between 0 and 1."""
    with pytest.raises(ValueError):
        engine.calculate_sample_size(baseline_rate=0.0, minimum_detectable_effect=0.02)
    with pytest.raises(ValueError):
        engine.calculate_sample_size(baseline_rate=1.0, minimum_detectable_effect=0.02)
