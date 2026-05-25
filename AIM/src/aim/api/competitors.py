"""Competitor Discovery API Endpoints

POST /api/competitors/find    — find top-3 competitors for a clinic URL
POST /api/competitors/save    — save competitor selection to pre-sale folder
POST /api/competitors/analyze — CI marketing analysis (SWOT, features, pricing, tactics)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aim.services.ci_marketing_analysis import CiMarketingAnalyzer
from aim.services.competitor_matcher import CompetitorMatcher
from aim.services.pre_sale_folder import PreSaleFolder
from aim.services.rusprofile.models import CompetitorMatch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


# ── Request/Response models ────────────────────────────────────────

class FindCompetitorsRequest(BaseModel):
    url: str = Field(..., description="Client clinic website URL")
    count: int = Field(default=3, ge=1, le=5, description="Number of competitors to return")
    named_competitors: Optional[list[str]] = Field(
        default=None,
        description="Optional list of competitor names or URLs to look up directly via DaData",
    )


class CompetitorJson(BaseModel):
    inn: str
    legal_name: str
    brand_name: Optional[str] = None
    revenue_year: Optional[int] = None
    profit_year: Optional[int] = None
    financial_year: Optional[int] = None
    revenue_trend: Optional[str] = None
    employee_count: Optional[int] = None
    okved_main: Optional[str] = None
    okved_secondary: list[str] = []
    legal_address: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    data_source: str = "dadata"
    confidence: float = 0.7

    # Scoring
    revenue_match: float = 0.0
    location_score: float = 0.0
    service_overlap: float = 0.0
    specialization_purity: float = 0.0
    data_quality: float = 0.7
    popularity_score: float = 0.0
    visibility_score: float = 0.0
    total_score: float = 0.0
    match_reason: str = ""
    services: list[str] = []
    website: Optional[str] = None
    social_links: dict[str, str] = {}


class FindCompetitorsResponse(BaseModel):
    success: bool = True
    url: str
    competitors: list[CompetitorJson]
    is_megalopolis: bool = False
    error: Optional[str] = None


class SaveCompetitorsRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID for pre-sale folder")
    status: str = Field(default="approved", pattern=r"^(approved|client_suggested)$")
    competitors: list[CompetitorJson] = Field(default_factory=list)
    client_urls: list[str] = Field(default_factory=list, description="Client-provided URLs (status=client_suggested)")


class SaveCompetitorsResponse(BaseModel):
    success: bool = True
    lead_id: str
    saved_to: str
    count: int


class AnalyzeCompetitorsRequest(BaseModel):
    url: str = Field(..., description="Client clinic website URL")
    specialization: str = Field(..., description="Client specialization (e.g. 'стоматология')")
    city: str = Field(..., description="Client city")
    services: list[str] = Field(..., description="Client services list")
    competitors: list[CompetitorJson] = Field(..., description="3 confirmed competitors")
    client_revenue: Optional[int] = Field(None, description="Estimated client annual revenue (RUB)")
    client_rating: Optional[float] = Field(None, description="Client rating if known")


class AnalyzeCompetitorsResponse(BaseModel):
    success: bool = True
    chat_summary: str = ""
    feature_matrix: dict = {}
    pricing_comparison: dict = {}
    positioning_map: dict = {}
    steal_worthy_tactics: list[dict] = []
    top_recommendation: str = ""
    duration_seconds: float = 0.0
    error: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/find", response_model=FindCompetitorsResponse, status_code=status.HTTP_200_OK)
async def find_competitors(body: FindCompetitorsRequest) -> FindCompetitorsResponse:
    """Find top-N competitors for a clinic website.

    Runs service extractor → DaData search → scoring → top-3.
    Returns competitor profiles with match scores and reasons.
    """
    try:
        matcher = CompetitorMatcher()
        matches = await matcher.find_competitors(
            url=body.url, count=body.count, named_competitors=body.named_competitors,
        )

        competitors = [_competitor_to_json(m) for m in matches]

        logger.info("competitors_found: url=%s count=%d megalopolis=%s", body.url, len(competitors), matcher.last_is_megalopolis)

        return FindCompetitorsResponse(
            success=True,
            url=body.url,
            competitors=competitors,
            is_megalopolis=matcher.last_is_megalopolis,
        )

    except Exception as e:
        logger.exception("find_competitors_failed")
        return FindCompetitorsResponse(
            success=False,
            url=body.url,
            competitors=[],
            error=str(e),
        )


@router.post("/save", response_model=SaveCompetitorsResponse, status_code=status.HTTP_200_OK)
async def save_competitors(body: SaveCompetitorsRequest) -> SaveCompetitorsResponse:
    """Save competitor selection to the lead's pre-sale/ folder.

    Handles two flows:
    - status=approved: client accepted system-suggested competitors
    - status=client_suggested: client provided their own URLs
    """
    folder = PreSaleFolder(body.lead_id)
    folder.ensure()

    if body.status == "approved":
        matches = [_json_to_match(c) for c in body.competitors]
        folder.save_approved_final(matches)
        folder.log_approval_event("finalized", {
            "status": "approved",
            "competitor_count": len(matches),
        })
        count = len(matches)
    else:
        folder.save_client_suggested(body.client_urls)
        folder.log_approval_event("client_suggested_own", {
            "urls": body.client_urls,
        })
        count = len(body.client_urls)

    logger.info("competitors_saved: lead_id=%s status=%s count=%d", body.lead_id, body.status, count)

    return SaveCompetitorsResponse(
        success=True,
        lead_id=body.lead_id,
        saved_to=f"pre-sale/competitors/",
        count=count,
    )


@router.post("/analyze", response_model=AnalyzeCompetitorsResponse, status_code=status.HTTP_200_OK)
async def analyze_competitors(body: AnalyzeCompetitorsRequest) -> AnalyzeCompetitorsResponse:
    """Run CI marketing analysis on confirmed competitors.

    Takes client info + 3 confirmed competitors, scrapes their websites,
    and produces SWOT, feature matrix, pricing comparison, positioning map,
    and steal-worthy tactics. Fast (<12s), deterministic, no LLM.
    """
    try:
        matches = [_json_to_match(c) for c in body.competitors]

        analyzer = CiMarketingAnalyzer(timeout=10.0)
        result = await analyzer.analyze(
            url=body.url,
            specialization=body.specialization,
            city=body.city,
            services=body.services,
            competitors=matches,
            client_revenue=body.client_revenue,
            client_rating=body.client_rating,
        )

        tactics_json = [
            {
                "source": t.source_competitor,
                "tactic": t.tactic_description,
                "why": t.why_it_works,
                "how": t.how_to_implement,
                "effort": t.estimated_effort,
                "impact": t.expected_impact,
            }
            for t in result.steal_worthy_tactics
        ]

        logger.info(
            "ci_analysis_complete: url=%s duration=%.1fs tactics=%d features=%d",
            body.url, result.analysis_duration_seconds,
            len(tactics_json), len(result.feature_matrix),
        )

        return AnalyzeCompetitorsResponse(
            success=True,
            chat_summary=result.chat_summary,
            feature_matrix=result.feature_matrix,
            pricing_comparison=result.pricing_comparison,
            positioning_map=result.positioning_map,
            steal_worthy_tactics=tactics_json,
            top_recommendation=result.top_recommendation,
            duration_seconds=result.analysis_duration_seconds,
        )

    except Exception as e:
        logger.exception("analyze_competitors_failed")
        return AnalyzeCompetitorsResponse(
            success=False,
            error=str(e),
        )


# ── Serialization helpers ──────────────────────────────────────────

def _competitor_to_json(m: CompetitorMatch) -> CompetitorJson:
    """Convert CompetitorMatch to API response model."""
    p = m.profile
    return CompetitorJson(
        inn=p.inn,
        legal_name=p.legal_name,
        brand_name=p.brand_name,
        revenue_year=p.revenue_year,
        profit_year=p.profit_year,
        financial_year=p.financial_year,
        revenue_trend=p.revenue_trend,
        employee_count=p.employee_count,
        okved_main=p.okved_main,
        okved_secondary=p.okved_secondary,
        legal_address=p.legal_address,
        geo_lat=p.geo_lat,
        geo_lon=p.geo_lon,
        data_source=p.data_source,
        confidence=p.confidence,
        revenue_match=m.revenue_match,
        location_score=m.location_score,
        service_overlap=m.service_overlap,
        specialization_purity=m.specialization_purity,
        data_quality=m.data_quality,
        popularity_score=m.popularity_score,
        visibility_score=m.visibility_score,
        total_score=m.total_score,
        match_reason=m.match_reason,
        services=m.services,
        website=m.website,
        social_links=m.social_links or p.social_links,
    )


def _json_to_match(j: CompetitorJson) -> CompetitorMatch:
    """Convert API model back to CompetitorMatch for storage."""
    from aim.services.rusprofile.models import CompanyProfile

    profile = CompanyProfile(
        inn=j.inn,
        legal_name=j.legal_name,
        brand_name=j.brand_name,
        revenue_year=j.revenue_year,
        profit_year=j.profit_year,
        financial_year=j.financial_year,
        revenue_trend=j.revenue_trend,
        employee_count=j.employee_count,
        okved_main=j.okved_main,
        okved_secondary=j.okved_secondary,
        legal_address=j.legal_address,
        geo_lat=j.geo_lat,
        geo_lon=j.geo_lon,
        data_source=j.data_source,
        confidence=j.confidence,
        website=j.website,
        social_links=j.social_links,
    )
    return CompetitorMatch(
        profile=profile,
        website=j.website,
        social_links=j.social_links,
        services=j.services,
        revenue_match=j.revenue_match,
        location_score=j.location_score,
        service_overlap=j.service_overlap,
        specialization_purity=j.specialization_purity,
        popularity_score=j.popularity_score,
        visibility_score=j.visibility_score,
        data_quality=j.data_quality,
        total_score=j.total_score,
        match_reason=j.match_reason,
    )
