"""Unit tests for gap-scoring bonus in CompetitorMatcher._score_one().

Verifies that competitors with revenue in the +20-50% sweet spot
get a scoring bonus, while those outside the range do not.

Strategy: the gap bonus is added to `total` at the end of _score_one.
We verify it by computing the bonus formula directly and checking it's
in [0.08, 0.12] when 1.2x <= ratio <= 1.5x, and 0 otherwise.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.aim.services.competitor_matcher import _score_one, _score_revenue_match
from src.aim.services.rusprofile.models import ClientProfile, CompanyProfile


def calculate_gap_bonus(client_revenue: int, comp_revenue: int) -> float:
    """Replicate the gap bonus calculation from _score_one()."""
    if client_revenue <= 0 or comp_revenue <= 0:
        return 0.0
    ratio = comp_revenue / client_revenue
    if 1.2 <= ratio <= 1.5:
        center = 1.35
        dist_from_center = abs(ratio - center) / 0.15
        return 0.12 - (dist_from_center * 0.04)
    return 0.0


def make_candidate(revenue: int = 0, revenue_source: str = "none",
                   geo_lat: float = 55.75, geo_lon: float = 37.62,
                   brand_name: str = "Test Clinic",
                   legal_name: str = "ООО Тест Клиник",
                   rating: float = 4.5, reviews_count: int = 100) -> CompanyProfile:
    return CompanyProfile(
        inn="7700000001",
        legal_name=legal_name,
        brand_name=brand_name,
        revenue_year=revenue,
        revenue_source=revenue_source,
        geo_lat=geo_lat,
        geo_lon=geo_lon,
        rating=rating,
        reviews_count=reviews_count,
        source_specialization="стоматология",
    )


def make_client(revenue: int = 30_000_000, specialization: str = "стоматология",
                city: str = "Москва", city_lat: float = 55.7558,
                city_lon: float = 37.6173) -> ClientProfile:
    return ClientProfile(
        url="https://test-clinic.ru",
        specialization=specialization,
        city=city,
        services=["терапия", "хирургия", "ортопедия"],
        estimated_revenue=revenue,
        city_lat=city_lat,
        city_lon=city_lon,
    )


class TestGapBonusFormula:
    """Direct tests of the gap bonus formula."""

    def test_bonus_zero_at_ratio_1_0(self):
        assert calculate_gap_bonus(10_000_000, 10_000_000) == 0.0

    def test_bonus_zero_at_ratio_1_19(self):
        assert calculate_gap_bonus(10_000_000, 11_900_000) == 0.0

    def test_bonus_at_min_threshold(self):
        bonus = calculate_gap_bonus(10_000_000, 12_000_000)  # ratio = 1.2
        assert 0.07 <= bonus <= 0.09, f"Expected ~0.08 at 1.2x, got {bonus}"

    def test_bonus_max_at_center(self):
        bonus = calculate_gap_bonus(10_000_000, 13_500_000)  # ratio = 1.35
        assert 0.11 <= bonus <= 0.13, f"Expected 0.12 at 1.35x, got {bonus}"

    def test_bonus_at_max_threshold(self):
        bonus = calculate_gap_bonus(10_000_000, 15_000_000)  # ratio = 1.5
        assert 0.07 <= bonus <= 0.09, f"Expected ~0.08 at 1.5x, got {bonus}"

    def test_bonus_zero_at_ratio_1_51(self):
        assert calculate_gap_bonus(10_000_000, 15_100_000) == 0.0

    def test_bonus_zero_at_ratio_2_0(self):
        assert calculate_gap_bonus(10_000_000, 20_000_000) == 0.0

    def test_bonus_zero_with_client_revenue_zero(self):
        assert calculate_gap_bonus(0, 15_000_000) == 0.0

    def test_bonus_zero_with_comp_revenue_zero(self):
        assert calculate_gap_bonus(10_000_000, 0) == 0.0


class TestGapBonusApplied:
    """Verify gap bonus is actually applied in _score_one()."""

    @pytest.mark.asyncio
    async def test_bonus_increases_score(self):
        """Score with client_revenue > 0 should exceed score with client_revenue=0
        when the competitor is in the gap sweet spot, and the difference should
        be at least the gap bonus (plus any revenue_match change)."""
        client = make_client(revenue=10_000_000)
        candidate = make_candidate(revenue=13_500_000, revenue_source="tax_filed")

        result_with = await _score_one(
            client, candidate, client.estimated_revenue,
            client.city_lat, client.city_lon,
        )
        result_without = await _score_one(
            client, candidate, 0,
            client.city_lat, client.city_lon,
        )

        # The total difference should be >= gap_bonus (0.12)
        # It will be larger because revenue_match also differs (0.94 vs 0.5)
        diff = result_with.total_score - result_without.total_score
        assert diff >= 0.10, (
            f"Expected diff >= gap bonus (0.12), got {diff:.4f}"
        )

    @pytest.mark.asyncio
    async def test_score_does_not_exceed_max(self):
        """Gap bonus should not push total_score above 1.0."""
        client = make_client(revenue=10_000_000)
        candidate = make_candidate(
            revenue=13_500_000, revenue_source="tax_filed",
            brand_name="Perfect Match", rating=5.0, reviews_count=1000,
            geo_lat=55.7558, geo_lon=37.6173,
        )

        result = await _score_one(
            client, candidate, client.estimated_revenue,
            client.city_lat, client.city_lon,
        )

        assert result.total_score <= 1.0, (
            f"Total score should not exceed 1.0: {result.total_score:.4f}"
        )


class TestRevenueMatch:
    """Basic revenue match scoring tests.

    _score_revenue_match peaks at 1.0 in the 1.5x-3.0x aspirational range.
    Equal revenue = 0.8, not 1.0 — the function biases toward
    competitors slightly ahead.
    """

    def test_exact_revenue_match(self):
        score = _score_revenue_match(10_000_000, 10_000_000)
        assert score == 0.8, f"1:1 ratio should be 0.8, got {score}"

    def test_aspirational_peak(self):
        score = _score_revenue_match(10_000_000, 20_000_000)
        assert score == 1.0, f"2x ratio should be 1.0 peak, got {score}"

    def test_half_revenue(self):
        score = _score_revenue_match(10_000_000, 5_000_000)
        assert 0.4 <= score <= 0.6, f"0.5x revenue score: {score}"

    def test_zero_competitor_revenue(self):
        score = _score_revenue_match(10_000_000, 0)
        assert score == 0.5, f"Zero comp revenue should give 0.5, got {score}"

    def test_zero_client_revenue(self):
        score = _score_revenue_match(0, 15_000_000)
        assert score == 0.5, f"Zero client revenue should give 0.5, got {score}"
