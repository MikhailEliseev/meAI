# AIM/tests/services/ci/test_comparison_matrix.py
import pytest
import json
from AIM.src.aim.services.ci.comparison_matrix import ComparisonMatrixBuilder
from AIM.src.aim.services.ci.models import CompetitorFull, SeoAuditResult, SocialScanResult


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
        json_str = json.dumps(matrix.competitors, ensure_ascii=False)
        assert len(json_str) < 8000  # Under 8K chars even as JSON string
