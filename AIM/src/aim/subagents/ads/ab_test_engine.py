"""
A/B Test Engine — Statistical Experiment Design & Analysis.

Uses scipy.stats for chi-square significance testing and sample size
calculation. Designed for landing page and ad copy split tests.
"""

from dataclasses import dataclass
from enum import Enum

import structlog
from scipy import stats


class ExperimentStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"


@dataclass
class ExperimentConfig:
    """Configuration for an A/B test experiment."""
    name: str
    description: str
    variant_a_name: str
    variant_b_name: str
    metric_name: str
    baseline_rate: float
    minimum_detectable_effect: float
    confidence_level: float = 0.95
    statistical_power: float = 0.80


@dataclass
class ExperimentResult:
    """Result of an A/B test analysis."""
    variant_a: str
    variant_b: str
    conversions_a: int
    visitors_a: int
    conversions_b: int
    visitors_b: int
    p_value: float
    confidence: float
    relative_lift: float
    winner: str | None
    status: ExperimentStatus
    recommendation: str = ""


class ABTestEngine:
    """Statistical A/B test analysis using scipy.stats."""

    MIN_SAMPLE_SIZE = 100
    CONFIDENCE_THRESHOLD = 0.95

    def __init__(self):
        self.logger = structlog.get_logger()

    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.80,
        alpha: float = 0.05,
    ) -> int:
        from scipy.stats import norm

        if not (0 < baseline_rate < 1):
            raise ValueError(f"baseline_rate must be between 0 and 1, got {baseline_rate}")
        if minimum_detectable_effect <= 0:
            raise ValueError("minimum_detectable_effect must be positive")

        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)

        p1 = baseline_rate
        p2 = baseline_rate + minimum_detectable_effect
        p_pooled = (p1 + p2) / 2

        n = (
            (z_alpha * (2 * p_pooled * (1 - p_pooled)) ** 0.5
             + z_beta * (p1 * (1 - p1) + p2 * (1 - p2)) ** 0.5) ** 2
            / (p2 - p1) ** 2
        )

        result = int(n) + 1
        self.logger.info(
            "sample_size_calculated",
            baseline_rate=baseline_rate,
            mde=minimum_detectable_effect,
            required_per_variant=result,
        )
        return result

    def analyze_results(
        self,
        variant_a: str,
        variant_b: str,
        conversions_a: int,
        visitors_a: int,
        conversions_b: int,
        visitors_b: int,
    ) -> ExperimentResult:
        for val, name in [(conversions_a, "conversions_a"), (conversions_b, "conversions_b")]:
            if val < 0:
                raise ValueError(f"{name} must be >= 0, got {val}")
        for val, name in [(visitors_a, "visitors_a"), (visitors_b, "visitors_b")]:
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}")

        rate_a = conversions_a / visitors_a
        rate_b = conversions_b / visitors_b

        relative_lift = (rate_b - rate_a) / rate_a if rate_a > 0 else 0.0

        contingency = [
            [conversions_a, visitors_a - conversions_a],
            [conversions_b, visitors_b - conversions_b],
        ]
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        confidence = round((1 - p_value) * 100, 1)

        if p_value < (1 - self.CONFIDENCE_THRESHOLD):
            winner = 'B' if rate_b > rate_a else 'A'
            status_ = ExperimentStatus.COMPLETED
            rec = (
                f"Variant '{variant_b if winner == 'B' else variant_a}' wins "
                f"with {confidence:.1f}% confidence "
                f"(p={p_value:.4f}, lift={relative_lift:.1%})"
            )
        elif visitors_a < self.MIN_SAMPLE_SIZE or visitors_b < self.MIN_SAMPLE_SIZE:
            winner = None
            status_ = ExperimentStatus.RUNNING
            rec = (
                f"Collect more data: minimum {self.MIN_SAMPLE_SIZE} visitors "
                f"per variant required (current: A={visitors_a}, B={visitors_b})"
            )
        else:
            winner = None
            status_ = ExperimentStatus.INCONCLUSIVE
            rec = (
                f"No statistically significant difference detected "
                f"(p={p_value:.4f}, confidence={confidence:.1f}%)"
            )

        result = ExperimentResult(
            variant_a=variant_a,
            variant_b=variant_b,
            conversions_a=conversions_a,
            visitors_a=visitors_a,
            conversions_b=conversions_b,
            visitors_b=visitors_b,
            p_value=round(p_value, 4),
            confidence=confidence,
            relative_lift=round(relative_lift, 4),
            winner=winner,
            status=status_,
            recommendation=rec,
        )

        self.logger.info(
            "ab_test_analyzed",
            winner=winner,
            p_value=result.p_value,
            status=status_.value,
        )
        return result
