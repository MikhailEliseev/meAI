import json
from datetime import datetime, timezone

import pytest

from AIM.src.aim.services.ci.comparison_matrix import ComparisonMatrixBuilder
from AIM.src.aim.services.ci.models import CompetitorFull, SeoAuditResult, SocialScanResult, SocialProfile


class TestComparisonMatrixBuilder:
    def test_build_empty(self):
        builder = ComparisonMatrixBuilder()
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={"booking": True, "chat": False},
            competitors_full=[],
        )
        assert len(matrix.competitors) == 0
        assert matrix.client["url"] == "https://client.ru"

    def test_build_with_one_competitor(self):
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="TestClinic",
            url="https://test.ru",
            inn="1234567890",
            financials={"revenue": {"2025": 10000000}},
            seo=SeoAuditResult(url="https://test.ru", score=65, issues=["Missing H1"]),
            scraped_at="2026-05-26T10:00:00+00:00",
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={"booking": True},
            competitors_full=[comp],
        )
        assert len(matrix.competitors) == 1
        assert matrix.competitors[0]["name"] == "TestClinic"
        assert matrix.competitors[0]["seo"]["score"] == 65
        assert "Missing H1" in matrix.competitors[0]["seo"]["issues"]

    def test_build_compact_json_fits_token_budget(self):
        builder = ComparisonMatrixBuilder()
        comps = []
        for i in range(5):
            comps.append(CompetitorFull(
                name=f"Competitor {i}",
                url=f"https://comp{i}.ru",
                inn=f"{i}" * 10,
                financials={"revenue": {"2025": 1000000 * (i + 1)}, "trend": "growing"},
                seo=SeoAuditResult(
                    url=f"https://comp{i}.ru",
                    score=70 - i * 10,
                    issues=[f"Issue {j}" for j in range(3)],
                ),
            ))
        matrix = builder.build("https://client.ru", {"booking": True}, comps)
        json_str = builder.to_llm_context(matrix)
        assert len(json_str) < 8000  # Under 8K chars as compact JSON

    def test_to_llm_context_returns_compact_json(self):
        """to_llm_context() should return valid, compact JSON."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="TestClinic",
            url="https://test.ru",
            inn="1234567890",
            scraped_at="2026-05-26T10:00:00+00:00",
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={"booking": True},
            competitors_full=[comp],
        )
        ctx = builder.to_llm_context(matrix)
        parsed = json.loads(ctx)
        assert "client" in parsed
        assert "competitors" in parsed
        assert parsed["competitors"][0]["name"] == "TestClinic"
        # Should use compact separators (no extra spaces)
        assert ": " not in ctx

    def test_competitor_has_id_and_scraped_at(self):
        """Each competitor must have 'id' and 'scraped_at' fields."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="ClinicA",
            url="https://a.ru",
            inn="111",
            scraped_at="2026-01-01T00:00:00+00:00",
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[comp],
        )
        c = matrix.competitors[0]
        assert c["id"] == 1
        assert c["scraped_at"] == "2026-01-01T00:00:00+00:00"

    def test_competitor_scraped_at_fallback(self):
        """When CompetitorFull.scraped_at is empty, fall back to current time."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="NoTime",
            url="https://notime.ru",
            inn="222",
            scraped_at="",  # empty string
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[comp],
        )
        c = matrix.competitors[0]
        # Should be a non-empty ISO datetime string
        assert c["scraped_at"]
        assert "T" in c["scraped_at"]

    def test_competitor_ids_are_sequential(self):
        """Multiple competitors should get sequential IDs starting from 1."""
        builder = ComparisonMatrixBuilder()
        comps = [
            CompetitorFull(name=f"Comp{i}", url=f"https://c{i}.ru", inn=f"{i}")
            for i in range(3)
        ]
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=comps,
        )
        ids = [c["id"] for c in matrix.competitors]
        assert ids == [1, 2, 3]

    def test_positioning_is_top_level_not_inside_website(self):
        """positioning must be at competitor top level, not nested inside website."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="PosClinic",
            url="https://pos.ru",
            inn="333",
            positioning="Premium clinic for VIP patients with personalized approach and advanced technology",
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[comp],
        )
        c = matrix.competitors[0]
        assert "positioning" in c
        assert "positioning" not in c["website"]
        assert c["positioning"] == "Premium clinic for VIP patients with personalized approach and advanced technology"

    def test_positioning_truncated_to_120_chars(self):
        """positioning should be truncated to 120 characters."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="LongPos",
            url="https://long.ru",
            inn="444",
            positioning="A" * 200,
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[comp],
        )
        assert len(matrix.competitors[0]["positioning"]) == 120

    def test_website_has_doctors_count_and_directions_claimed(self):
        """Website dict must use 'doctors_count' and 'directions_claimed' keys."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="FieldTest",
            url="https://field.ru",
            inn="555",
            doctors_count=42,
            directions_claimed=7,
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[comp],
        )
        w = matrix.competitors[0]["website"]
        assert "doctors_count" in w
        assert "directions_claimed" in w
        assert "doctors" not in w
        assert "directions" not in w
        assert w["doctors_count"] == 42
        assert w["directions_claimed"] == 7

    def test_client_includes_name_when_provided(self):
        builder = ComparisonMatrixBuilder()
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={"booking": True},
            competitors_full=[],
            client_name="Client Clinic Name",
        )
        assert matrix.client["name"] == "Client Clinic Name"

    def test_client_name_not_present_when_empty(self):
        builder = ComparisonMatrixBuilder()
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[],
        )
        assert "name" not in matrix.client

    def test_client_includes_seo_when_provided(self):
        builder = ComparisonMatrixBuilder()
        seo = SeoAuditResult(url="https://client.ru", score=80, issues=["Slow load"])
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[],
            client_seo=seo,
        )
        assert "seo" in matrix.client
        assert matrix.client["seo"]["score"] == 80
        assert "Slow load" in matrix.client["seo"]["issues"]

    def test_client_seo_not_present_when_none(self):
        builder = ComparisonMatrixBuilder()
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[],
        )
        assert "seo" not in matrix.client

    def test_client_includes_social_when_provided(self):
        builder = ComparisonMatrixBuilder()
        social = SocialScanResult(
            company_name="Test",
            instagram=SocialProfile(platform="instagram", handle="test_ig", exists=True, subscribers=500),
        )
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[],
            client_social=social,
        )
        assert "social" in matrix.client
        assert matrix.client["social"]["instagram"]["exists"] is True
        assert matrix.client["social"]["instagram"]["handle"] == "test_ig"

    def test_client_social_not_present_when_none(self):
        builder = ComparisonMatrixBuilder()
        matrix = builder.build(
            client_url="https://client.ru",
            client_features={},
            competitors_full=[],
        )
        assert "social" not in matrix.client
