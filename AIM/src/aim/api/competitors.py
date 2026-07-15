"""Competitor Discovery API Endpoints

POST /api/competitors/find    — find top-3 competitors for a clinic URL
POST /api/competitors/save    — save competitor selection to pre-sale folder
POST /api/competitors/analyze — CI marketing analysis (SWOT, features, pricing, tactics)
"""

import asyncio
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.aim.services.competitor_matcher import CompetitorMatcher
from src.aim.services.pre_sale_folder import PreSaleFolder
from src.aim.services.rusprofile.models import CompetitorMatch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


# ── Request/Response models ────────────────────────────────────────

class FindCompetitorsRequest(BaseModel):
    url: str = Field(..., description="Client clinic website URL")
    count: int = Field(default=5, ge=1, le=10, description="Number of competitors to return")
    strategy: str = Field(
        default="v2",
        description="Discovery strategy: 'v2' (Perplexity+SearXNG+ФНС) or 'v1' (Google Maps)",
    )
    named_competitors: Optional[list[str]] = Field(
        default=None,
        description="Optional list of competitor names or URLs to look up directly",
    )
    client_revenue: Optional[int] = Field(
        default=None,
        description="Estimated client annual revenue (RUB) for gap-scoring",
    )


class CompetitorJson(BaseModel):
    inn: str = ""
    legal_name: str = ""
    brand_name: Optional[str] = None
    revenue_year: Optional[int] = None
    profit_year: Optional[int] = None
    financial_year: Optional[int] = None
    revenue_trend: Optional[str] = None
    revenue_source: str = "none"
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
    rating: Optional[float] = None
    reviews_count: Optional[int] = None

    # Multi-entity support
    inns: list[str] = []
    licenses: list[dict] = []
    is_multi_entity: bool = False
    social_links: dict[str, str] = {}

    # V2 enrichment fields
    surgeons_count: Optional[int] = None
    instagram_followers: Optional[int] = None
    instagram_handle: Optional[str] = None
    instagram_posts: Optional[int] = None

    # Deep ФНС + Firecrawl enrichment
    registration_date: Optional[str] = None
    revenue_change_3yr: Optional[float] = None
    website_cms: Optional[str] = None
    website_pages: Optional[int] = None
    website_size_kb: Optional[float] = None


class FindCompetitorsResponse(BaseModel):
    success: bool = True
    url: str
    competitors: list[CompetitorJson]
    is_megalopolis: bool = False
    client_revenue: Optional[int] = None
    client_profit: Optional[int] = None
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
    tier: str = Field("quick", description="Analysis tier: quick or deep")
    target_audience: str = Field("", description="Target audience description")
    price_segment: str = Field("mid", description="Price segment: economy, mid, premium")
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
    competitor_details: list[dict] = []


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/find", response_model=FindCompetitorsResponse, status_code=status.HTTP_200_OK)
async def find_competitors(body: FindCompetitorsRequest) -> FindCompetitorsResponse:
    """Find top-N competitors for a clinic website.

    Strategy v2 (default): Perplexity + SearXNG → bo.nalog brand→INN → ФНС financials.
    Strategy v1 (legacy):  Google Maps (Apify) → DaData → scoring.
    """
    # Select matcher by strategy
    if body.strategy == "v2":
        from src.aim.services.competitor_matcher_v2 import CompetitorMatcherV2
        matcher = CompetitorMatcherV2()
    else:
        matcher = CompetitorMatcher()

    try:
        matches = await matcher.find_competitors(
            url=body.url, count=body.count, named_competitors=body.named_competitors,
            client_revenue=body.client_revenue,
        )

        competitors = [_competitor_to_json(m) for m in matches]

        logger.info(
            "competitors_found: url=%s strategy=%s count=%d megalopolis=%s",
            body.url, body.strategy, len(competitors), getattr(matcher, "last_is_megalopolis", False),
        )

        return FindCompetitorsResponse(
            success=True,
            url=body.url,
            competitors=competitors,
            is_megalopolis=getattr(matcher, "last_is_megalopolis", False),
            client_revenue=getattr(matcher, "last_client_revenue", None),
            client_profit=getattr(matcher, "last_client_profit", None),
        )

    except Exception as e:
        logger.exception("find_competitors_failed: strategy=%s", body.strategy)
        return FindCompetitorsResponse(
            success=False,
            url=body.url,
            competitors=[],
            error=str(e),
        )
    finally:
        if hasattr(matcher, "close"):
            close_result = matcher.close()
            if asyncio.iscoroutine(close_result):
                await close_result


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


def _extract_named_urls(competitors: list) -> list[str]:
    """Extract URL strings from a mix of CompetitorMatch, dict, or str objects."""
    named_urls = []
    for c in (competitors or []):
        if isinstance(c, str):
            named_urls.append(c)
        elif hasattr(c, 'url'):
            named_urls.append(c.url)
        elif hasattr(c, 'website'):
            named_urls.append(c.website)
        elif isinstance(c, dict):
            named_urls.append(c.get("url", c.get("website", "")))
        else:
            named_urls.append(str(c))
    return [u for u in named_urls if u]


@router.post("/analyze", response_model=AnalyzeCompetitorsResponse, status_code=status.HTTP_200_OK)
async def analyze_competitors(body: AnalyzeCompetitorsRequest) -> AnalyzeCompetitorsResponse:
    """Run CI marketing analysis on confirmed competitors via shared CIOrchestrator.

    Reuses the SEO API's singleton CIOrchestrator via _get_orchestrator().
    """
    try:
        from src.aim.api.seo import _get_orchestrator

        matches = [_json_to_match(c) for c in body.competitors]
        named_urls = _extract_named_urls(matches)

        # Build rich competitor objects preserving find_competitors data
        # (ratings, names, revenue) for the orchestrator
        import re as _re
        rich_competitors = []
        for i, c in enumerate(body.competitors):
            # Extract star rating from match_reason (e.g. "рейтинг 4.7, 52 отзыва")
            star_rating = None
            if c.match_reason:
                rm = _re.search(r'рейтинг\s+(\d+\.?\d*)', c.match_reason)
                if rm:
                    try:
                        star_rating = float(rm.group(1))
                    except ValueError:
                        pass
            comp = {
                "name": c.brand_name or c.legal_name or f"competitor_{i}",
                "brand_name": c.brand_name,
                "legal_name": c.legal_name,
                "url": c.website or "",
                "website": c.website or "",
                "rating": c.rating or star_rating,
                "reviews_count": c.reviews_count or 0,
                "revenue_year": c.revenue_year,
                "profit_year": c.profit_year,
                "revenue_trend": c.revenue_trend,
                "employee_count": c.employee_count,
                "revenue_source": c.revenue_source,
                "total_score": c.total_score,
                "match_reason": c.match_reason,
                "services": c.services,
                "social_links": c.social_links,
            }
            rich_competitors.append(comp)

        orchestrator = await _get_orchestrator()
        result = await orchestrator.execute_ci_analysis({
            "task_id": f"analyze-{uuid.uuid4().hex[:12]}",
            "url": body.url,
            "competitors": rich_competitors,
            "niche": body.specialization,
            "geo": body.city,
            "tier": body.tier,
            "target_audience": body.target_audience or "",
            "price_segment": body.price_segment or "mid",
            "client_revenue": body.client_revenue,
            "client_rating": body.client_rating,
        })

        # Map dict result to backwards-compatible response fields.
        # execute_ci_analysis returns {findings, reports, errors, ...}
        # — fields like chat_summary, feature_matrix are extracted from
        # findings or default to empty if not produced by the current tier.
        tactics_list = result.get("steal_worthy_tactics", [])
        if not tactics_list:
            # Backward-compat: if steal_worthy_tactics not at top level,
            # try to extract from phase findings.
            findings = result.get("findings", {})
            tactics_list = findings.get("steal_worthy_tactics", [])

        tactics_json = []
        for t in tactics_list:
            if isinstance(t, dict):
                tactics_json.append({
                    "source": t.get("source_competitor", t.get("source", "")),
                    "tactic": t.get("tactic_description", t.get("tactic", "")),
                    "why": t.get("why_it_works", t.get("why", "")),
                    "how": t.get("how_to_implement", t.get("how", "")),
                    "effort": t.get("estimated_effort", t.get("effort", "medium")),
                    "impact": t.get("expected_impact", t.get("impact", "medium")),
                })

        feature_matrix = result.get("feature_matrix", {})
        findings = result.get("findings", {})
        if not feature_matrix and "phase_2" in findings:
            # Try to extract feature_matrix from phase_2 (ci-auditor)
            phase2 = findings["phase_2"]
            if isinstance(phase2, dict):
                fm = phase2.get("result", phase2).get("feature_matrix", {})
                if fm:
                    feature_matrix = fm

        duration = result.get("execution_time_seconds", 0)

        logger.info(
            "ci_analysis_complete: url=%s duration=%ds tactics=%d features=%d",
            body.url, duration,
            len(tactics_json), len(feature_matrix),
        )

        return JSONResponse(
            content=AnalyzeCompetitorsResponse(
                success=True,
                chat_summary=result.get("chat_summary", ""),
                feature_matrix=feature_matrix,
                pricing_comparison=result.get("pricing_comparison", {}),
                positioning_map=result.get("positioning_map", {}),
                steal_worthy_tactics=tactics_json,
                top_recommendation=result.get("top_recommendation", ""),
                duration_seconds=duration,
                competitor_details=result.get("competitor_details", []),
            ).model_dump(),
            headers={
                "X-Deprecated-API": "true",
                "Migration": "/api/seo/audit (POST with tier=quick)",
            },
        )

    except Exception as e:
        logger.exception("analyze_competitors_failed")
        return JSONResponse(
            content=AnalyzeCompetitorsResponse(
                success=False,
                error=str(e),
            ).model_dump(),
            headers={
                "X-Deprecated-API": "true",
                "Migration": "/api/seo/audit (POST with tier=quick)",
            },
        )


@router.post("/analyze/stream")
async def analyze_competitors_stream(body: AnalyzeCompetitorsRequest):
    """SSE streaming alias for /api/seo/audit?tier=quick.

    Reuses the SEO API's singleton CIOrchestrator via _get_orchestrator().
    Emits progress events during analysis and a final result event.
    """

    async def generate():
        from src.aim.api.seo import _get_orchestrator
        import asyncio as _asyncio

        matches = [_json_to_match(c) for c in body.competitors]
        named_urls = _extract_named_urls(matches)

        queue: _asyncio.Queue = _asyncio.Queue()

        async def progress_callback(phase_num: int, status: str, message: str):
            """Bridge CIOrchestrator progress -> SSE events."""
            await queue.put({
                "type": "progress",
                "stage": status,
                "message": f"[Phase {phase_num}] {message}",
                "phase": phase_num,
                "competitor": "",
            })

        async def run_analysis():
            try:
                orchestrator = await _get_orchestrator()

                task_data = {
                    "task_id": f"stream-{id(body)}",
                    "url": body.url,
                    "competitors": named_urls,
                    "niche": body.specialization,
                    "geo": body.city,
                    "tier": "quick",
                    "target_audience": "",
                    "price_segment": "mid",
                }

                result = await orchestrator.execute_ci_analysis(
                    task_data,
                    progress_callback=progress_callback,
                )

                # Extract tactics with backward-compat dict handling
                tactics_list = result.get("steal_worthy_tactics", [])
                if not tactics_list:
                    findings_inner = result.get("findings", {})
                    tactics_list = findings_inner.get("steal_worthy_tactics", [])

                tactics_json = []
                for t in tactics_list:
                    if isinstance(t, dict):
                        tactics_json.append({
                            "source": t.get("source_competitor", t.get("source", "")),
                            "tactic": t.get("tactic_description", t.get("tactic", "")),
                            "why": t.get("why_it_works", t.get("why", "")),
                            "how": t.get("how_to_implement", t.get("how", "")),
                            "effort": t.get("estimated_effort", t.get("effort", "medium")),
                            "impact": t.get("expected_impact", t.get("impact", "medium")),
                        })

                # Extract feature_matrix from findings if not at top level
                feature_matrix = result.get("feature_matrix", {})
                findings_inner = result.get("findings", {})
                if not feature_matrix and "phase_2" in findings_inner:
                    phase2 = findings_inner["phase_2"]
                    if isinstance(phase2, dict):
                        fm = phase2.get("result", phase2).get("feature_matrix", {})
                        if fm:
                            feature_matrix = fm

                await queue.put({
                    "type": "result",
                    "data": {
                        "success": True,
                        "chat_summary": result.get("chat_summary", ""),
                        "feature_matrix": feature_matrix,
                        "pricing_comparison": result.get("pricing_comparison", {}),
                        "positioning_map": result.get("positioning_map", {}),
                        "steal_worthy_tactics": tactics_json,
                        "top_recommendation": result.get("top_recommendation", ""),
                        "duration_seconds": result.get("execution_time_seconds", 0),
                        "tier": result.get("tier", "quick"),
                    },
                })
            except Exception as e:
                logger.exception("analyze_competitors_stream_failed")
                await queue.put({"type": "error", "message": str(e)})

        task = _asyncio.create_task(run_analysis())

        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event["type"] in ("result", "error"):
                break

        await task

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Deprecated-API": "true",
            "Migration": "/api/seo/audit (POST with tier=quick)",
        },
    )


# ── Serialization helpers ──────────────────────────────────────────

def _safe_int(val) -> int | None:
    """Безопасное преобразование в int (от corrupt данных скраперов)."""
    if not val:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError, OverflowError):
        return None


def _safe_float(val) -> float | None:
    """Безопасное преобразование в float."""
    if not val:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


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
        revenue_source=p.revenue_source,
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
        rating=p.rating,
        reviews_count=p.reviews_count,
        social_links=m.social_links or p.social_links or {},
        inns=p.inns,
        licenses=p.licenses,
        is_multi_entity=p.is_multi_entity,
        surgeons_count=p.employee_count,
        instagram_handle=p.social_links.get("instagram"),
        instagram_followers=_safe_int(p.social_links.get("instagram_followers")),
        instagram_posts=_safe_int(p.social_links.get("instagram_posts")),
        registration_date=p.registration_date,
        website_cms=p.social_links.get("website_cms"),
        website_pages=_safe_int(p.social_links.get("website_pages")),
        website_size_kb=_safe_float(p.social_links.get("website_size_kb")),
    )


def _json_to_match(j: CompetitorJson) -> CompetitorMatch:
    """Convert API model back to CompetitorMatch for storage."""
    import hashlib
    from src.aim.services.rusprofile.models import CompanyProfile

    inn = j.inn if j.inn else f"manual-{hashlib.md5((j.website or j.brand_name or 'unknown').encode()).hexdigest()[:10]}"
    legal_name = j.legal_name if j.legal_name else (j.brand_name or j.website or "Неизвестный конкурент")

    profile = CompanyProfile(
        inn=inn,
        legal_name=legal_name,
        brand_name=j.brand_name,
        revenue_year=j.revenue_year,
        profit_year=j.profit_year,
        financial_year=j.financial_year,
        revenue_trend=j.revenue_trend,
        revenue_source=j.revenue_source,
        employee_count=j.employee_count,
        okved_main=j.okved_main,
        okved_secondary=j.okved_secondary,
        legal_address=j.legal_address,
        geo_lat=j.geo_lat,
        geo_lon=j.geo_lon,
        data_source=j.data_source,
        confidence=j.confidence,
        website=j.website,
        rating=j.rating,
        reviews_count=j.reviews_count,
        social_links=j.social_links,
        inns=j.inns,
        licenses=j.licenses,
        is_multi_entity=j.is_multi_entity,
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
