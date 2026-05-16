"""Ads Magister AI Integration

Integrates AI components with Ads Magister:
- Ad Copy Generator (Task 2.1)
- Predictive Analytics (Task 2.2)
- Budget Optimizer
- Anomaly Detector

Part of: Phase 10 - AI Enhancement (Task 2.3)
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
import structlog

from aim.magisters.ads_magister import AdsMagister
from aim.ai.ads.generator import AdCopyGenerator
from aim.ai.analytics.budget_optimizer import BudgetOptimizer
from aim.ai.analytics.anomaly_detector import AnomalyDetector
from aim.ai.analytics.forecaster import PerformanceForecaster
from aim.ai.llm.client import LLMClient

logger = structlog.get_logger(__name__)


class AdsMagisterAI(AdsMagister):
    """Ads Magister with AI Enhancement

    Extends base Ads Magister with AI capabilities:
    - AI-powered ad copy generation
    - Predictive analytics for performance forecasting
    - Budget optimization with Thompson Sampling
    - Anomaly detection for performance issues

    Target Improvements:
    - Campaign setup time: -60%
    - Compliance violations: <1%
    - Performance prediction accuracy: >75%
    - Budget efficiency: +25%
    """

    def __init__(
        self,
        magister_id: str = "ads-magister-ai",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/ads-magister",
        event_bus: Any | None = None,
        vault: Any | None = None,
        llm_client: LLMClient | None = None,
    ):
        """Initialize AI-enhanced Ads Magister

        Args:
            magister_id: Unique Magister ID
            database_url: Database connection URL
            vault_path: Path to Ads Magister's Obsidian vault
            event_bus: Optional EventBus instance (for testing)
            vault: Optional ObsidianVault instance (for testing)
            llm_client: Optional LLM client (for testing)
        """
        super().__init__(
            magister_id=magister_id,
            database_url=database_url,
            vault_path=vault_path,
            event_bus=event_bus,
            vault=vault,
        )

        # Initialize AI components
        self.llm_client = llm_client or LLMClient()
        self.ad_copy_generator = AdCopyGenerator(
            llm_client=self.llm_client,
            market="russia",
            platform="yandex_direct",
        )
        self.budget_optimizer = BudgetOptimizer(
            kp=0.5,
            ki=0.1,
            kd=0.2,
            exploration_rate=0.1,
        )
        self.anomaly_detector = AnomalyDetector()
        self.forecaster = PerformanceForecaster()

        logger.info(
            "ads_magister_ai_initialized",
            magister_id=magister_id,
            ai_components=["ad_copy_generator", "budget_optimizer", "anomaly_detector", "forecaster"],
        )

    async def generate_ad_copy(
        self,
        specialty: str,
        service: str,
        target_audience: str | None = None,
        emotional_trigger: str | None = None,
        num_variants: int = 3,
    ) -> Dict[str, Any]:
        """Generate AI-powered ad copy with compliance checking

        Args:
            specialty: Medical specialty (e.g., "Стоматология")
            service: Specific service (e.g., "Имплантация зубов")
            target_audience: Target audience description
            emotional_trigger: Preferred emotional trigger (urgency, trust, fear, social_proof)
            num_variants: Number of variants to generate (3-5)

        Returns:
            Ad copy result with variants and compliance check
        """
        logger.info(
            "generating_ad_copy",
            specialty=specialty,
            service=service,
            num_variants=num_variants,
        )

        # Generate ad copy
        result = await self.ad_copy_generator.generate(
            specialty=specialty,
            service=service,
            target_audience=target_audience,
            emotional_trigger=emotional_trigger,
            num_variants=num_variants,
        )

        # Log to Obsidian
        await self._log_operation(
            "generate_ad_copy",
            f"Generated {len(result.variants)} variants for {specialty} - {service}. "
            f"Compliance: {result.compliance.score:.1f}%, Cost: ${result.generation_cost:.4f}"
        )

        logger.info(
            "ad_copy_generated",
            specialty=specialty,
            service=service,
            variants_count=len(result.variants),
            compliance_score=result.compliance.score,
            generation_cost=result.generation_cost,
        )

        return {
            "specialty": result.specialty,
            "service": result.service,
            "platform": result.platform,
            "variants": [
                {
                    "headline": v.headline,
                    "description": v.description,
                    "cta": v.cta,
                    "emotional_trigger": v.emotional_trigger,
                    "predicted_ctr": v.predicted_ctr,
                }
                for v in result.variants
            ],
            "compliance": {
                "score": result.compliance.score,
                "passed": result.compliance.passed,
                "violations": result.compliance.violations,
                "warnings": result.compliance.warnings,
            },
            "generation_cost": result.generation_cost,
        }

    async def optimize_budget(
        self,
        total_budget: float,
        channel_performance: Dict[str, Dict[str, float]],
        constraints: Dict[str, Dict[str, float]] | None = None,
    ) -> Dict[str, Any]:
        """Optimize budget allocation across channels

        Args:
            total_budget: Total daily budget to allocate
            channel_performance: Performance data by channel
                {
                    "google_ads": {"conversions": 20, "cost": 500, "clicks": 100},
                    "yandex_direct": {"conversions": 15, "cost": 400, "clicks": 80},
                }
            constraints: Optional min/max budget constraints by channel

        Returns:
            Budget optimization result with recommended allocation
        """
        logger.info(
            "optimizing_budget",
            total_budget=total_budget,
            channels=list(channel_performance.keys()),
        )

        # Optimize budget
        result = await self.budget_optimizer.optimize(
            total_budget=total_budget,
            channel_performance=channel_performance,
            constraints=constraints,
        )

        # Log to Obsidian
        await self._log_operation(
            "optimize_budget",
            f"Optimized ${total_budget:.2f} across {len(result.channel_allocation)} channels. "
            f"Expected: {result.expected_conversions} conversions, ${result.expected_cpa:.2f} CPA"
        )

        logger.info(
            "budget_optimized",
            total_budget=total_budget,
            expected_conversions=result.expected_conversions,
            expected_cpa=result.expected_cpa,
            confidence=result.confidence,
        )

        return {
            "recommended_daily_budget": result.recommended_daily_budget,
            "channel_allocation": result.channel_allocation,
            "expected_conversions": result.expected_conversions,
            "expected_cpa": result.expected_cpa,
            "confidence": result.confidence,
        }

    async def detect_anomalies(
        self,
        current_data: Any,
        historical_data: Any,
        budget_plan: float,
    ) -> List[Dict[str, Any]]:
        """Detect performance anomalies

        Args:
            current_data: Current performance data (pandas DataFrame)
            historical_data: Historical performance data (pandas DataFrame)
            budget_plan: Planned budget for comparison

        Returns:
            List of anomaly alerts with severity and recommendations
        """
        logger.info(
            "detecting_anomalies",
            budget_plan=budget_plan,
        )

        # Detect anomalies
        alerts = await self.anomaly_detector.detect(
            current_data=current_data,
            historical_data=historical_data,
            budget_plan=budget_plan,
        )

        # Log to Obsidian
        if alerts:
            await self._log_operation(
                "detect_anomalies",
                f"Detected {len(alerts)} anomalies. "
                f"Critical: {sum(1 for a in alerts if a.severity == 'critical')}, "
                f"High: {sum(1 for a in alerts if a.severity == 'high')}"
            )

        logger.info(
            "anomalies_detected",
            alerts_count=len(alerts),
            critical_count=sum(1 for a in alerts if a.severity == "critical"),
        )

        return [
            {
                "type": alert.type,
                "severity": alert.severity,
                "description": alert.description,
                "recommended_action": alert.recommended_action,
                "detected_at": alert.detected_at.isoformat(),
            }
            for alert in alerts
        ]

    async def forecast_performance(
        self,
        historical_data: Any,
        metric: str,
        horizon_days: int = 30,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """Forecast campaign performance

        Args:
            historical_data: Historical performance data (pandas DataFrame)
            metric: Metric to forecast (clicks, conversions, cost, revenue)
            horizon_days: Forecast horizon in days
            confidence_level: Confidence level for intervals (0.5-0.99)

        Returns:
            Forecast result with predictions and confidence intervals
        """
        logger.info(
            "forecasting_performance",
            metric=metric,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
        )

        # Create forecast request
        from aim.ai.analytics.schemas import ForecastRequest

        request = ForecastRequest(
            metric=metric,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
        )

        # Forecast performance
        result = await self.forecaster.forecast(historical_data, request)

        # Log to Obsidian
        await self._log_operation(
            "forecast_performance",
            f"Forecasted {metric} for {horizon_days} days. "
            f"Accuracy: {result.accuracy_score:.1%}, "
            f"Seasonality: {'detected' if result.seasonality_detected else 'not detected'}"
        )

        logger.info(
            "performance_forecasted",
            metric=metric,
            horizon_days=horizon_days,
            accuracy_score=result.accuracy_score,
            seasonality_detected=result.seasonality_detected,
        )

        return {
            "metric": metric,
            "horizon_days": horizon_days,
            "predictions": result.predictions,
            "lower_bound": result.lower_bound,
            "upper_bound": result.upper_bound,
            "accuracy_score": result.accuracy_score,
            "seasonality_detected": result.seasonality_detected,
        }

    async def close(self):
        """Close AI components and base magister"""
        # Close AI components
        await self.llm_client.close()
        await self.budget_optimizer.close()
        await self.anomaly_detector.close()
        await self.forecaster.close()
