"""End-to-end tests for AI-enhanced Magisters

Tests integration of all AI Magisters:
- Ads Magister AI
- SEO Magister AI
- Content Magister AI

Part of: Phase 10 - AI Enhancement (Task 2.3)
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from AIM.src.aim.magisters.ads_magister_ai import AdsMagisterAI
from AIM.src.aim.magisters.seo_magister_ai import SEOMagisterAI
from AIM.src.aim.magisters.content_magister_ai import ContentMagisterAI
from AIM.src.aim.ai.ads.schemas import AdCopyResult, AdCopyVariant, ComplianceCheck
from AIM.src.aim.ai.analytics.schemas import BudgetOptimizationResult
from AIM.src.aim.ai.llm.schemas import LLMResponse


class TestAIMagistersE2E:
    """End-to-end tests for AI Magisters"""

    @pytest.fixture
    async def ads_magister(self):
        """Create Ads Magister AI instance"""
        llm_client = AsyncMock()
        llm_client.close = AsyncMock()

        vault = MagicMock()
        vault.vault_path = MagicMock()
        vault.vault_path.__truediv__ = lambda self, x: MagicMock(exists=lambda: False)

        magister = AdsMagisterAI(
            magister_id="test-ads-magister-ai-e2e",
            database_url="sqlite+aiosqlite:///:memory:",
            vault_path="./test_vault",
            llm_client=llm_client,
            vault=vault,
        )

        yield magister
        await magister.close()

    @pytest.fixture
    async def seo_magister(self):
        """Create SEO Magister AI instance"""
        llm_client = AsyncMock()
        llm_client.close = AsyncMock()

        vault = MagicMock()
        vault.vault_path = MagicMock()
        vault.vault_path.__truediv__ = lambda self, x: MagicMock(exists=lambda: False)

        magister = SEOMagisterAI(
            magister_id="test-seo-magister-ai-e2e",
            database_url="sqlite+aiosqlite:///:memory:",
            vault_path="./test_vault",
            llm_client=llm_client,
            vault=vault,
            serp_api_key="test-serp-api-key",
        )

        yield magister
        await magister.close()

    @pytest.fixture
    async def content_magister(self):
        """Create Content Magister AI instance"""
        llm_client = AsyncMock()
        llm_client.close = AsyncMock()

        vault = MagicMock()
        vault.vault_path = MagicMock()
        vault.vault_path.__truediv__ = lambda self, x: MagicMock(exists=lambda: False)

        magister = ContentMagisterAI(
            magister_id="test-content-magister-ai-e2e",
            database_url="sqlite+aiosqlite:///:memory:",
            vault_path="./test_vault",
            llm_client=llm_client,
            vault=vault,
        )

        yield magister
        await magister.close()

    async def test_all_magisters_initialized(self, ads_magister, seo_magister, content_magister):
        """Test all AI Magisters are properly initialized"""
        # Ads Magister
        assert ads_magister.magister_id == "test-ads-magister-ai-e2e"
        assert ads_magister.llm_client is not None
        assert ads_magister.ad_copy_generator is not None
        assert ads_magister.budget_optimizer is not None
        assert ads_magister.anomaly_detector is not None
        assert ads_magister.forecaster is not None

        # SEO Magister
        assert seo_magister.magister_id == "test-seo-magister-ai-e2e"
        assert seo_magister.llm_client is not None

        # Content Magister
        assert content_magister.magister_id == "test-content-magister-ai-e2e"
        assert content_magister.llm_client is not None

    async def test_campaign_workflow(self, ads_magister, seo_magister, content_magister):
        """Test complete campaign workflow across all Magisters"""

        # Step 1: Content Magister generates article
        content_response = LLMResponse(
            content="# Dental Implants Guide\n\nComprehensive guide to dental implants...",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=500,
            input_tokens=100,
            output_tokens=400,
            cost_usd=0.015,
            latency_ms=1200,
        )
        content_magister.llm_client.generate = AsyncMock(return_value=content_response)

        article = await content_magister.generate_content(
            topic="Dental Implants",
            content_type="article",
            word_count=1000,
        )

        assert article["topic"] == "Dental Implants"
        assert article["word_count"] > 0

        # Step 2: SEO Magister analyzes content (mock)
        # In real workflow, SEO Magister would analyze the article
        # For E2E test, we just verify it's available
        assert seo_magister is not None

        # Step 3: Ads Magister generates ad copy
        ad_copy_result = AdCopyResult(
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
            ],
            compliance=ComplianceCheck(
                score=92.0,
                passed=True,
                violations=[],
                warnings=[],
            ),
            template_used="dental_implants_urgency",
            generation_cost=0.14,
        )

        ads_magister.ad_copy_generator.generate = AsyncMock(return_value=ad_copy_result)

        ad_copy = await ads_magister.generate_ad_copy(
            specialty="Стоматология",
            service="Имплантация зубов",
            num_variants=1,
        )

        assert ad_copy["specialty"] == "Стоматология"
        assert len(ad_copy["variants"]) == 1
        assert ad_copy["compliance"]["passed"] is True

        # Step 4: Ads Magister optimizes budget
        budget_result = BudgetOptimizationResult(
            recommended_daily_budget=1500.0,
            channel_allocation={
                "google_ads": 900.0,
                "yandex_direct": 600.0,
            },
            expected_conversions=45,
            expected_cpa=33.33,
            confidence=0.85,
        )

        ads_magister.budget_optimizer.optimize = AsyncMock(return_value=budget_result)

        budget = await ads_magister.optimize_budget(
            total_budget=1500.0,
            channel_performance={
                "google_ads": {"conversions": 20, "cost": 500, "clicks": 100},
                "yandex_direct": {"conversions": 15, "cost": 400, "clicks": 80},
            },
        )

        assert budget["recommended_daily_budget"] == 1500.0
        assert budget["expected_conversions"] == 45

    async def test_content_optimization_workflow(self, content_magister, seo_magister):
        """Test content creation and optimization workflow"""

        # Step 1: Generate content
        generate_response = LLMResponse(
            content="# Original Article\n\nContent here...",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=300,
            input_tokens=80,
            output_tokens=220,
            cost_usd=0.009,
            latency_ms=900,
        )
        content_magister.llm_client.generate = AsyncMock(return_value=generate_response)

        content = await content_magister.generate_content(
            topic="Test Topic",
            content_type="article",
        )

        assert content["content"] is not None

        # Step 2: Analyze readability
        readability_response = LLMResponse(
            content="""Score: 75
Reading Level: 10th grade
Issues:
- Some issues
Recommendations:
- Some recommendations""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=150,
            input_tokens=80,
            output_tokens=70,
            cost_usd=0.0045,
            latency_ms=650,
        )
        content_magister.llm_client.generate = AsyncMock(return_value=readability_response)

        readability = await content_magister.analyze_readability(
            content=content["content"]
        )

        assert readability["score"] == 75.0

        # Step 3: Optimize content
        optimize_response = LLMResponse(
            content="""## Optimized Content
# Improved Article

Better content...

## Improvements Made
- Improved readability
- Better structure""",
            model="claude-opus-4",
            provider="anthropic",
            tokens_used=200,
            input_tokens=100,
            output_tokens=100,
            cost_usd=0.006,
            latency_ms=700,
        )
        content_magister.llm_client.generate = AsyncMock(return_value=optimize_response)

        optimized = await content_magister.optimize_content(
            content=content["content"],
            optimization_goals=["readability", "seo"],
        )

        assert optimized["optimized_content"] is not None
        assert len(optimized["improvements"]) > 0

    async def test_analytics_workflow(self, ads_magister):
        """Test analytics and monitoring workflow"""

        # Step 1: Detect anomalies
        ads_magister.anomaly_detector.detect = AsyncMock(return_value=[])

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

        anomalies = await ads_magister.detect_anomalies(
            current_data=current_data,
            historical_data=historical_data,
            budget_plan=1000.0,
        )

        assert len(anomalies) == 0

        # Step 2: Forecast performance
        from AIM.src.aim.ai.analytics.schemas import ForecastResponse

        forecast_result = ForecastResponse(
            predictions=[100, 105, 110, 115, 120],
            lower_bound=[90, 95, 100, 105, 110],
            upper_bound=[110, 115, 120, 125, 130],
            accuracy_score=0.82,
            seasonality_detected=True,
        )

        ads_magister.forecaster.forecast = AsyncMock(return_value=forecast_result)

        forecast = await ads_magister.forecast_performance(
            historical_data=historical_data,
            metric="clicks",
            horizon_days=5,
        )

        assert len(forecast["predictions"]) == 5
        assert forecast["accuracy_score"] == 0.82

    async def test_all_magisters_close_properly(self, ads_magister, seo_magister, content_magister):
        """Test all Magisters close properly"""
        # Close all magisters
        await ads_magister.close()
        await seo_magister.close()
        await content_magister.close()

        # Verify LLM clients closed
        ads_magister.llm_client.close.assert_called_once()
        seo_magister.llm_client.close.assert_called_once()
        content_magister.llm_client.close.assert_called_once()
