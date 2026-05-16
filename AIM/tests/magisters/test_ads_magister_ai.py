"""Tests for AI-enhanced Ads Magister

Tests integration of AI components with Ads Magister:
- Ad Copy Generator integration
- Budget Optimizer integration
- Anomaly Detector integration
- Performance Forecaster integration

Part of: Phase 10 - AI Enhancement (Task 2.3)
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from AIM.src.aim.magisters.ads_magister_ai import AdsMagisterAI
from AIM.src.aim.ai.ads.schemas import AdCopyResult, AdCopyVariant, ComplianceCheck
from AIM.src.aim.ai.analytics.schemas import (
    BudgetOptimizationResult,
    AnomalyAlert,
    ForecastResponse,
)


class TestAdsMagisterAI:
    """Test AI-enhanced Ads Magister"""

    @pytest.fixture
    async def magister(self):
        """Create AI-enhanced Ads Magister instance"""
        # Mock LLM client
        llm_client = AsyncMock()
        llm_client.close = AsyncMock()

        # Mock vault
        vault = MagicMock()
        vault.vault_path = MagicMock()
        vault.vault_path.__truediv__ = lambda self, x: MagicMock(exists=lambda: False)

        magister = AdsMagisterAI(
            magister_id="test-ads-magister-ai",
            database_url="sqlite+aiosqlite:///:memory:",
            vault_path="./test_vault",
            llm_client=llm_client,
            vault=vault,
        )

        yield magister

        await magister.close()

    async def test_initialization(self, magister):
        """Test AI-enhanced Ads Magister initialization"""
        assert magister.magister_id == "test-ads-magister-ai"
        assert magister.llm_client is not None
        assert magister.ad_copy_generator is not None
        assert magister.budget_optimizer is not None
        assert magister.anomaly_detector is not None
        assert magister.forecaster is not None

    async def test_generate_ad_copy(self, magister):
        """Test ad copy generation"""
        # Mock ad copy generator
        mock_result = AdCopyResult(
            specialty="Стоматология",
            service="Имплантация зубов",
            platform="yandex_direct",
            variants=[
                AdCopyVariant(
                    headline="Имплантация зубов под ключ",
                    description="Установка имплантов за 1 день. Гарантия 10 лет.",
                    cta="Записаться на консультацию",
                    emotional_trigger="urgency",
                    compliance_score=92.0,
                    predicted_ctr=3.5,
                ),
                AdCopyVariant(
                    headline="Надёжные зубные импланты",
                    description="Европейские импланты. Опытные врачи. Без боли.",
                    cta="Узнать цену",
                    emotional_trigger="trust",
                    compliance_score=90.0,
                    predicted_ctr=3.2,
                ),
            ],
            compliance=ComplianceCheck(
                score=92.0,
                passed=True,
                violations=[],
                warnings=["Рекомендуется добавить лицензию клиники"],
            ),
            generation_cost=0.14,
            generated_at=datetime.now(timezone.utc),
        )

        magister.ad_copy_generator.generate = AsyncMock(return_value=mock_result)

        # Generate ad copy
        result = await magister.generate_ad_copy(
            specialty="Стоматология",
            service="Имплантация зубов",
            target_audience="Мужчины 35-55 лет",
            emotional_trigger="urgency",
            num_variants=2,
        )

        # Verify result
        assert result["specialty"] == "Стоматология"
        assert result["service"] == "Имплантация зубов"
        assert result["platform"] == "yandex_direct"
        assert len(result["variants"]) == 2
        assert result["variants"][0]["headline"] == "Имплантация зубов под ключ"
        assert result["variants"][0]["predicted_ctr"] == 3.5
        assert result["compliance"]["score"] == 92.0
        assert result["compliance"]["passed"] is True
        assert result["generation_cost"] == 0.14

    async def test_optimize_budget(self, magister):
        """Test budget optimization"""
        # Mock budget optimizer
        mock_result = BudgetOptimizationResult(
            recommended_daily_budget=1500.0,
            channel_allocation={
                "google_ads": 900.0,
                "yandex_direct": 600.0,
            },
            expected_conversions=45,
            expected_cpa=33.33,
            confidence=0.85,
        )

        magister.budget_optimizer.optimize = AsyncMock(return_value=mock_result)

        # Optimize budget
        result = await magister.optimize_budget(
            total_budget=1500.0,
            channel_performance={
                "google_ads": {"conversions": 20, "cost": 500, "clicks": 100},
                "yandex_direct": {"conversions": 15, "cost": 400, "clicks": 80},
            },
        )

        # Verify result
        assert result["recommended_daily_budget"] == 1500.0
        assert result["channel_allocation"]["google_ads"] == 900.0
        assert result["channel_allocation"]["yandex_direct"] == 600.0
        assert result["expected_conversions"] == 45
        assert result["expected_cpa"] == 33.33
        assert result["confidence"] == 0.85

    async def test_detect_anomalies(self, magister):
        """Test anomaly detection"""
        # Mock anomaly detector
        mock_alerts = [
            AnomalyAlert(
                type="performance_drop",
                severity="high",
                description="CTR dropped by 45% compared to baseline",
                metric_name="ctr",
                current_value=1.2,
                expected_value=2.2,
                deviation_pct=45.5,
                recommended_action="Review ad copy and targeting settings",
                detected_at=datetime.now(timezone.utc),
            ),
            AnomalyAlert(
                type="budget_overspend",
                severity="medium",
                description="Budget variance: 25% over plan",
                metric_name="cost",
                current_value=1250.0,
                expected_value=1000.0,
                deviation_pct=25.0,
                recommended_action="Reduce bids or pause low-performing campaigns",
                detected_at=datetime.now(timezone.utc),
            ),
        ]

        magister.anomaly_detector.detect = AsyncMock(return_value=mock_alerts)

        # Create mock data
        current_data = pd.DataFrame({
            "date": [datetime.now(timezone.utc)],
            "clicks": [100],
            "impressions": [8333],
            "conversions": [5],
            "cost": [1250.0],
        })

        historical_data = pd.DataFrame({
            "date": [datetime.now(timezone.utc) - timedelta(days=i) for i in range(30)],
            "clicks": [100] * 30,
            "impressions": [4545] * 30,
            "conversions": [5] * 30,
            "cost": [1000.0] * 30,
        })

        # Detect anomalies
        result = await magister.detect_anomalies(
            current_data=current_data,
            historical_data=historical_data,
            budget_plan=1000.0,
        )

        # Verify result
        assert len(result) == 2
        assert result[0]["type"] == "performance_drop"
        assert result[0]["severity"] == "high"
        assert result[0]["metric_name"] == "ctr"
        assert result[0]["deviation_pct"] == 45.5
        assert result[1]["type"] == "budget_overspend"
        assert result[1]["severity"] == "medium"

    async def test_forecast_performance(self, magister):
        """Test performance forecasting"""
        # Mock forecaster
        mock_result = ForecastResponse(
            predictions=[100, 105, 110, 115, 120],
            lower_bound=[90, 95, 100, 105, 110],
            upper_bound=[110, 115, 120, 125, 130],
            accuracy_score=0.82,
            seasonality_detected=True,
        )

        magister.forecaster.forecast = AsyncMock(return_value=mock_result)

        # Create mock historical data
        historical_data = pd.DataFrame({
            "date": [datetime.now(timezone.utc) - timedelta(days=i) for i in range(90)],
            "clicks": [100 + i for i in range(90)],
        })

        # Forecast performance
        result = await magister.forecast_performance(
            historical_data=historical_data,
            metric="clicks",
            horizon_days=5,
            confidence_level=0.95,
        )

        # Verify result
        assert result["metric"] == "clicks"
        assert result["horizon_days"] == 5
        assert len(result["predictions"]) == 5
        assert result["predictions"] == [100, 105, 110, 115, 120]
        assert result["accuracy_score"] == 0.82
        assert result["seasonality_detected"] is True

    async def test_generate_ad_copy_with_compliance_violations(self, magister):
        """Test ad copy generation with compliance violations"""
        # Mock ad copy generator with violations
        mock_result = AdCopyResult(
            specialty="Стоматология",
            service="Имплантация зубов",
            platform="yandex_direct",
            variants=[
                AdCopyVariant(
                    headline="100% гарантия результата",
                    description="Лучшие импланты в городе!",
                    cta="Записаться",
                    emotional_trigger="urgency",
                    predicted_ctr=2.5,
                ),
            ],
            compliance=ComplianceCheck(
                score=45.0,
                passed=False,
                violations=[
                    "Запрещено: абсолютные гарантии результата",
                    "Запрещено: превосходная степень без подтверждения",
                ],
                warnings=[],
            ),
            generation_cost=0.14,
            generated_at=datetime.now(timezone.utc),
        )

        magister.ad_copy_generator.generate = AsyncMock(return_value=mock_result)

        # Generate ad copy
        result = await magister.generate_ad_copy(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        # Verify compliance violations
        assert result["compliance"]["passed"] is False
        assert result["compliance"]["score"] == 45.0
        assert len(result["compliance"]["violations"]) == 2
        assert "абсолютные гарантии" in result["compliance"]["violations"][0]

    async def test_optimize_budget_with_constraints(self, magister):
        """Test budget optimization with constraints"""
        # Mock budget optimizer
        mock_result = BudgetOptimizationResult(
            recommended_daily_budget=1500.0,
            channel_allocation={
                "google_ads": 1000.0,  # Max constraint
                "yandex_direct": 500.0,  # Min constraint
            },
            expected_conversions=40,
            expected_cpa=37.50,
            confidence=0.80,
        )

        magister.budget_optimizer.optimize = AsyncMock(return_value=mock_result)

        # Optimize budget with constraints
        result = await magister.optimize_budget(
            total_budget=1500.0,
            channel_performance={
                "google_ads": {"conversions": 25, "cost": 600, "clicks": 120},
                "yandex_direct": {"conversions": 10, "cost": 300, "clicks": 60},
            },
            constraints={
                "google_ads": {"min": 600, "max": 1000},
                "yandex_direct": {"min": 500, "max": 800},
            },
        )

        # Verify constraints applied
        assert result["channel_allocation"]["google_ads"] == 1000.0  # Hit max
        assert result["channel_allocation"]["yandex_direct"] == 500.0  # Hit min

    async def test_detect_no_anomalies(self, magister):
        """Test anomaly detection with no anomalies"""
        # Mock anomaly detector with no alerts
        magister.anomaly_detector.detect = AsyncMock(return_value=[])

        # Create mock data (normal performance)
        current_data = pd.DataFrame({
            "date": [datetime.now(timezone.utc)],
            "clicks": [100],
            "impressions": [4545],
            "conversions": [5],
            "cost": [1000.0],
        })

        historical_data = pd.DataFrame({
            "date": [datetime.now(timezone.utc) - timedelta(days=i) for i in range(30)],
            "clicks": [100] * 30,
            "impressions": [4545] * 30,
            "conversions": [5] * 30,
            "cost": [1000.0] * 30,
        })

        # Detect anomalies
        result = await magister.detect_anomalies(
            current_data=current_data,
            historical_data=historical_data,
            budget_plan=1000.0,
        )

        # Verify no anomalies
        assert len(result) == 0

    async def test_forecast_performance_no_seasonality(self, magister):
        """Test performance forecasting without seasonality"""
        # Mock forecaster without seasonality
        mock_result = ForecastResponse(
            predictions=[100, 100, 100, 100, 100],
            lower_bound=[95, 95, 95, 95, 95],
            upper_bound=[105, 105, 105, 105, 105],
            accuracy_score=0.75,
            seasonality_detected=False,
        )

        magister.forecaster.forecast = AsyncMock(return_value=mock_result)

        # Create mock historical data (flat trend)
        historical_data = pd.DataFrame({
            "date": [datetime.now(timezone.utc) - timedelta(days=i) for i in range(30)],
            "clicks": [100] * 30,
        })

        # Forecast performance
        result = await magister.forecast_performance(
            historical_data=historical_data,
            metric="clicks",
            horizon_days=5,
        )

        # Verify no seasonality
        assert result["seasonality_detected"] is False
        assert all(p == 100 for p in result["predictions"])

    async def test_multiple_ai_operations_sequence(self, magister):
        """Test sequence of AI operations"""
        # Mock all AI components
        magister.ad_copy_generator.generate = AsyncMock(
            return_value=AdCopyResult(
                specialty="Стоматология",
                service="Имплантация",
                platform="yandex_direct",
                variants=[],
                compliance=ComplianceCheck(score=90.0, passed=True, violations=[], warnings=[]),
                generation_cost=0.14,
                generated_at=datetime.now(timezone.utc),
            )
        )

        magister.budget_optimizer.optimize = AsyncMock(
            return_value=BudgetOptimizationResult(
                recommended_daily_budget=1000.0,
                channel_allocation={"google_ads": 1000.0},
                expected_conversions=30,
                expected_cpa=33.33,
                confidence=0.85,
            )
        )

        magister.anomaly_detector.detect = AsyncMock(return_value=[])

        # Execute sequence
        ad_result = await magister.generate_ad_copy(
            specialty="Стоматология",
            service="Имплантация",
        )

        budget_result = await magister.optimize_budget(
            total_budget=1000.0,
            channel_performance={"google_ads": {"conversions": 30, "cost": 1000, "clicks": 100}},
        )

        anomaly_result = await magister.detect_anomalies(
            current_data=pd.DataFrame(),
            historical_data=pd.DataFrame(),
            budget_plan=1000.0,
        )

        # Verify all operations completed
        assert ad_result["compliance"]["passed"] is True
        assert budget_result["expected_conversions"] == 30
        assert len(anomaly_result) == 0

    async def test_close_cleanup(self, magister):
        """Test proper cleanup on close"""
        # Close magister
        await magister.close()

        # Verify LLM client closed
        magister.llm_client.close.assert_called_once()
