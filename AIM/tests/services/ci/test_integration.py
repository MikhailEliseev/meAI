"""End-to-end integration tests for the LLM CI pipeline.

Covers the full pipeline: models → matrix builder → dialogue manager.
"""

import pytest

from AIM.src.aim.services.ci.comparison_matrix import ComparisonMatrixBuilder
from AIM.src.aim.services.ci.dialogue_manager import DialogueManager
from AIM.src.aim.services.ci.models import (
    CompetitorFull,
    ComparisonMatrix,
    PipelineProgress,
    SeoAuditResult,
    SocialProfile,
    SocialScanResult,
)


class TestEndToEndIntegration:
    """Integration tests covering model roundtrip, matrix building, and dialogue."""

    # ------------------------------------------------------------------
    # 1. Models roundtrip
    # ------------------------------------------------------------------

    def test_models_roundtrip(self):
        """Create SeoAuditResult and verify all fields are accessible."""
        result = SeoAuditResult(
            url="https://example.com",
            score=72,
            issues=["Missing H1 tag", "No meta description"],
            title="Example Clinic - Home",
        )

        assert result.url == "https://example.com"
        assert result.score == 72
        assert len(result.issues) == 2
        assert "Missing H1 tag" in result.issues
        assert result.title == "Example Clinic - Home"

    # ------------------------------------------------------------------
    # 2. Matrix builder with full competitor data
    # ------------------------------------------------------------------

    def test_matrix_builder_with_full_data(self):
        """Build matrix from CompetitorFull with all fields populated.

        Verify financials (latest_revenue uses most recent year key),
        SEO score, website fields, and positioning.
        """
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="ООО Юцковская",
            url="https://yutskovskaya.ru",
            inn="7709123456",
            financials={
                "revenue": {"2023": 150_000_000, "2024": 180_000_000, "2025": 200_000_000},
                "profit": {"2023": 15_000_000, "2024": 20_000_000},
                "trend": "growing",
            },
            seo=SeoAuditResult(
                url="https://yutskovskaya.ru",
                score=68,
                issues=["Missing H1 on 3 pages", "No SSL certificate", "Slow page load"],
            ),
            social=SocialScanResult(
                company_name="ООО Юцковская",
                instagram=SocialProfile(
                    platform="instagram",
                    handle="yutskovskaya_clinic",
                    exists=True,
                    subscribers=15_000,
                    posts_last_month=12,
                ),
                telegram=SocialProfile(
                    platform="telegram",
                    handle="yutskovskaya",
                    exists=True,
                    subscribers=3_000,
                ),
            ),
            website_features=["booking", "chat", "price_list"],
            website_missing=["calculator", "reviews"],
            doctors_count=24,
            directions_claimed=12,
            pricing_visible=True,
            positioning="Premium aesthetic medicine with personalized approach",
        )

        client_features = {"booking": True, "chat": True, "calculator": False}
        matrix = builder.build(
            client_url="https://client-clinic.ru",
            client_features=client_features,
            competitors_full=[comp],
            client_name="ООО КлиентКлиник",
        )

        assert len(matrix.competitors) == 1

        c = matrix.competitors[0]

        # Financials: max(revenue.keys()) = "2025" → 200_000_000
        assert c["financials"]["latest_revenue"] == 200_000_000
        assert c["financials"]["trend"] == "growing"

        # SEO
        assert c["seo"]["score"] == 68
        assert "Missing H1 on 3 pages" in c["seo"]["issues"]

        # Website fields (note: field name is 'doctors_count' from current code)
        assert c["website"]["doctors_count"] == 24
        assert c["website"]["directions_claimed"] == 12
        assert c["website"]["pricing_visible"] is True
        assert "booking" in c["website"]["features"]
        assert "calculator" in c["website"]["missing"]

        # Social
        assert c["social"]["instagram"]["exists"] is True
        assert c["social"]["instagram"]["handle"] == "yutskovskaya_clinic"
        assert c["social"]["telegram"]["exists"] is True

        # Positioning
        assert "Premium aesthetic medicine" in c["positioning"]

    # ------------------------------------------------------------------
    # 3. Dialogue manager builds system prompt
    # ------------------------------------------------------------------

    def test_dialogue_manager_builds_prompt(self):
        """System prompt must contain the three major sections."""
        dm = DialogueManager()
        matrix = ComparisonMatrix(
            client={"url": "https://test.ru", "name": "ТестКлиника"},
            competitors=[],
        )

        prompt = dm.build_system_prompt(matrix)

        assert "ДАННЫЕ КЛИЕНТА" in prompt
        assert "ДАННЫЕ КОНКУРЕНТОВ" in prompt
        assert "ПРАВИЛА" in prompt

    # ------------------------------------------------------------------
    # 4. Dialogue manager fallback
    # ------------------------------------------------------------------

    def test_dialogue_manager_fallback(self):
        """Fallback response must contain competitor name and revenue digits."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="ООО Эрасмиль",
            url="https://erasmile.ru",
            financials={
                "revenue": {"2025": 10_000_000},
                "trend": "stable",
            },
        )

        matrix = builder.build(
            client_url="https://client-clinic.ru",
            client_features={"booking": True},
            competitors_full=[comp],
            client_name="ООО КлиентКлиник",
        )

        dm = DialogueManager()
        text = dm._fallback_response(matrix)

        # Competitor name present
        assert "Эрасмиль" in text
        # Revenue number present (at least the digit "10")
        assert "10" in text

    # ------------------------------------------------------------------
    # 5. PipelineProgress model
    # ------------------------------------------------------------------

    def test_pipeline_progress_model(self):
        """PipelineProgress dataclass stores and returns all fields."""
        progress = PipelineProgress(
            stage="searching",
            message="Ищу конкурентов...",
            competitor_name="",
            details={"query": "косметология москва"},
        )

        assert progress.stage == "searching"
        assert progress.message == "Ищу конкурентов..."
        assert progress.competitor_name == ""
        assert progress.details["query"] == "косметология москва"

    # ------------------------------------------------------------------
    # 6. Matrix JSON compact — fits in LLM context
    # ------------------------------------------------------------------

    def test_matrix_json_compact(self):
        """Three competitors with full data must produce prompt < 10000 chars."""
        builder = ComparisonMatrixBuilder()
        comps = []

        for i in range(3):
            comps.append(
                CompetitorFull(
                    name=f"ООО Конкурент {i} — Медицинский Центр",
                    url=f"https://competitor-{i}.ru",
                    inn=f"770000{i:04d}",
                    financials={
                        "revenue": {
                            "2023": 80_000_000 + i * 20_000_000,
                            "2024": 100_000_000 + i * 30_000_000,
                            "2025": 120_000_000 + i * 40_000_000,
                        },
                        "profit": {"2025": 12_000_000 + i * 5_000_000},
                        "trend": "growing",
                    },
                    seo=SeoAuditResult(
                        url=f"https://competitor-{i}.ru",
                        score=75 - i * 10,
                        issues=[
                            f"Issue {i}-1: Missing meta descriptions",
                            f"Issue {i}-2: No H1 on landing page",
                            f"Issue {i}-3: Slow page load time",
                        ],
                    ),
                    social=SocialScanResult(
                        company_name=f"Конкурент {i}",
                        instagram=SocialProfile(
                            platform="instagram",
                            handle=f"clinic_{i}_insta",
                            exists=True,
                            subscribers=5_000 * (i + 1),
                            posts_last_month=8 + i * 2,
                        ),
                    ),
                    website_features=["booking", "chat", "price_list", "doctors_page"],
                    website_missing=["calculator", "online_consultation"],
                    doctors_count=15 + i * 5,
                    directions_claimed=8 + i * 2,
                    pricing_visible=(i % 2 == 0),
                    positioning=f"Лучшая клиника {'премиум' if i == 0 else 'бизнес' if i == 1 else 'эконом'} класса в Москве с современным оборудованием",
                )
            )

        client_features = {
            "booking": True,
            "chat": True,
            "calculator": True,
            "online_consultation": False,
        }
        matrix = builder.build(
            client_url="https://client-clinic.ru",
            client_features=client_features,
            competitors_full=comps,
            client_name="ООО КлиентКлиник — Современная Стоматология",
        )

        # Build the full system prompt
        dm = DialogueManager()
        prompt = dm.build_system_prompt(matrix)

        assert len(prompt) < 10000, (
            f"System prompt is {len(prompt)} chars, must be < 10000"
        )
