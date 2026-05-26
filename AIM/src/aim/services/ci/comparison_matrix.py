# AIM/src/aim/services/ci/comparison_matrix.py
"""ComparisonMatrix — build compact matrix from collector outputs for LLM context."""

import json
from datetime import datetime, timezone

from .models import CompetitorFull, ComparisonMatrix


class ComparisonMatrixBuilder:
    """Builds ComparisonMatrix from CompetitorFull data.

    The matrix is designed to fit in ~5000 tokens when serialized,
    with 3-5 competitors each having 20+ parameters.
    """

    def build(
        self,
        client_url: str,
        client_features: dict,
        competitors_full: list[CompetitorFull],
    ) -> ComparisonMatrix:
        client = {
            "url": client_url,
            "features": [k for k, v in client_features.items() if v] if client_features else [],
            "missing": [k for k, v in client_features.items() if not v] if client_features else [],
        }

        competitors = []
        for cf in competitors_full:
            comp = {
                "name": cf.name,
                "url": cf.url,
                "financials": self._compact_financials(cf),
                "seo": self._compact_seo(cf),
                "social": self._compact_social(cf),
                "website": {
                    "features": cf.website_features,
                    "missing": cf.website_missing,
                    "doctors": cf.doctors_count,
                    "directions": cf.directions_claimed,
                    "pricing_visible": cf.pricing_visible,
                    "positioning": cf.positioning[:120] if cf.positioning else "",
                },
            }
            competitors.append(comp)

        return ComparisonMatrix(
            client=client,
            competitors=competitors,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_llm_context(self, matrix: ComparisonMatrix) -> str:
        """Convert matrix to compact JSON string for LLM system prompt."""
        return json.dumps(
            {"client": matrix.client, "competitors": matrix.competitors},
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _compact_financials(self, cf: CompetitorFull) -> dict:
        fin = cf.financials
        revenue = fin.get("revenue", {})
        return {
            "latest_revenue": max(revenue.values()) if revenue else None,
            "latest_profit": max(fin.get("profit", {}).values()) if fin.get("profit") else None,
            "trend": fin.get("trend", ""),
        }

    def _compact_seo(self, cf: CompetitorFull) -> dict:
        if cf.seo is None:
            return {"score": None, "issues": [], "error": "No data"}
        return {
            "score": cf.seo.score,
            "issues": cf.seo.issues[:8],  # cap at 8 issues
        }

    def _compact_social(self, cf: CompetitorFull) -> dict:
        if cf.social is None:
            return {
                "instagram": {"exists": False},
                "telegram": {"exists": False},
                "vk": {"exists": False},
                "tiktok": {"exists": False},
            }
        return cf.social.as_dict()
