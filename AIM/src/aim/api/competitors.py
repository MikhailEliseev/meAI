"""Competitor Discovery API Endpoints

POST /api/competitors/find  — find top-3 competitors for a clinic URL
POST /api/competitors/save  — save competitor selection to pre-sale folder
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aim.services.competitor_matcher import CompetitorMatcher
from aim.services.pre_sale_folder import PreSaleFolder
from aim.services.rusprofile.models import CompetitorMatch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


# ── Request/Response models ────────────────────────────────────────

class FindCompetitorsRequest(BaseModel):
    url: str = Field(..., description="Client clinic website URL")
    count: int = Field(default=3, ge=1, le=5, description="Number of competitors to return")


class CompetitorJson(BaseModel):
    inn: str
    legal_name: str
    brand_name: Optional[str] = None
    revenue_year: Optional[int] = None
    profit_year: Optional[int] = None
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
    data_quality: float = 0.7
    total_score: float = 0.0
    match_reason: str = ""
    services: list[str] = []
    website: Optional[str] = None


class FindCompetitorsResponse(BaseModel):
    success: bool = True
    url: str
    competitors: list[CompetitorJson]
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


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/find", response_model=FindCompetitorsResponse, status_code=status.HTTP_200_OK)
async def find_competitors(body: FindCompetitorsRequest) -> FindCompetitorsResponse:
    """Find top-N competitors for a clinic website.

    Runs service extractor → DaData search → scoring → top-3.
    Returns competitor profiles with match scores and reasons.
    """
    try:
        matcher = CompetitorMatcher()
        matches = await matcher.find_competitors(url=body.url, count=body.count)

        competitors = [_competitor_to_json(m) for m in matches]

        logger.info("competitors_found: url=%s count=%d", body.url, len(competitors))

        return FindCompetitorsResponse(
            success=True,
            url=body.url,
            competitors=competitors,
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
        data_quality=m.data_quality,
        total_score=m.total_score,
        match_reason=m.match_reason,
        services=m.services,
        website=m.website,
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
        revenue_trend=j.revenue_trend,
        employee_count=j.employee_count,
        okved_main=j.okved_main,
        okved_secondary=j.okved_secondary,
        legal_address=j.legal_address,
        geo_lat=j.geo_lat,
        geo_lon=j.geo_lon,
        data_source=j.data_source,
        confidence=j.confidence,
    )
    return CompetitorMatch(
        profile=profile,
        website=j.website,
        services=j.services,
        revenue_match=j.revenue_match,
        location_score=j.location_score,
        service_overlap=j.service_overlap,
        data_quality=j.data_quality,
        total_score=j.total_score,
        match_reason=j.match_reason,
    )
