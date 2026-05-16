"""Analytics API Endpoints

FastAPI routes for analytics metrics and reports.

Part of: Phase 11 Sprint 2 - Task 2.5
"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from aim.database import get_db
from aim.schemas.analytics import (
    AnalyticsExportRequest,
    AnalyticsExportResponse,
    ConversionFunnel,
    EmailMetrics,
    LeadMetrics,
    RealTimeStats,
)
from aim.services.analytics import AnalyticsService
from aim.services.analytics.report_generator import ReportGenerator

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    """Dependency injection for AnalyticsService."""
    return AnalyticsService(db)


@router.get("/leads", response_model=LeadMetrics)
async def get_lead_analytics(
    start_date: datetime = Query(..., description="Start date for metrics"),
    end_date: datetime = Query(..., description="End date for metrics"),
    tier: Optional[str] = Query(None, description="Filter by tier (hot/warm/cold)"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> LeadMetrics:
    """
    Get lead acquisition and scoring metrics.

    **Parameters:**
    - **start_date**: Start date for metrics period
    - **end_date**: End date for metrics period
    - **tier**: Optional tier filter (hot/warm/cold)

    **Returns:**
    - Lead metrics including totals, averages, rates, and time series
    """
    try:
        # Validate date range
        if end_date < start_date:
            raise HTTPException(
                status_code=422,
                detail="end_date must be after start_date",
            )

        # Validate tier
        if tier and tier not in ["hot", "warm", "cold"]:
            raise HTTPException(
                status_code=422,
                detail="tier must be one of: hot, warm, cold",
            )

        metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
            tier=tier,
        )
        return metrics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get lead metrics: {str(e)}",
        )


@router.get("/emails", response_model=EmailMetrics)
async def get_email_analytics(
    start_date: datetime = Query(..., description="Start date for metrics"),
    end_date: datetime = Query(..., description="End date for metrics"),
    tier: Optional[str] = Query(None, description="Filter by workflow tier (hot/warm/cold)"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> EmailMetrics:
    """
    Get email campaign performance metrics.

    **Parameters:**
    - **start_date**: Start date for metrics period
    - **end_date**: End date for metrics period
    - **tier**: Optional workflow tier filter (hot/warm/cold)

    **Returns:**
    - Email metrics including delivery, open, click rates, and time series
    """
    try:
        # Validate date range
        if end_date < start_date:
            raise HTTPException(
                status_code=422,
                detail="end_date must be after start_date",
            )

        # Validate tier
        if tier and tier not in ["hot", "warm", "cold"]:
            raise HTTPException(
                status_code=422,
                detail="tier must be one of: hot, warm, cold",
            )

        metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
            tier=tier,
        )
        return metrics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get email metrics: {str(e)}",
        )


@router.get("/funnel", response_model=ConversionFunnel)
async def get_conversion_funnel(
    start_date: datetime = Query(..., description="Start date for metrics"),
    end_date: datetime = Query(..., description="End date for metrics"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> ConversionFunnel:
    """
    Get lead conversion funnel metrics.

    **Parameters:**
    - **start_date**: Start date for metrics period
    - **end_date**: End date for metrics period

    **Returns:**
    - Conversion funnel showing lead journey from capture to engagement
    """
    try:
        # Validate date range
        if end_date < start_date:
            raise HTTPException(
                status_code=422,
                detail="end_date must be after start_date",
            )

        funnel = await service.get_conversion_funnel(
            start_date=start_date,
            end_date=end_date,
        )
        return funnel

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversion funnel: {str(e)}",
        )


@router.get("/realtime", response_model=RealTimeStats)
async def get_realtime_stats(
    service: AnalyticsService = Depends(get_analytics_service),
) -> RealTimeStats:
    """
    Get real-time statistics for current day.

    **Returns:**
    - Real-time stats including today's counts and active workflows
    """
    try:
        stats = await service.get_real_time_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get real-time stats: {str(e)}",
        )


@router.get("/export", response_model=AnalyticsExportResponse)
async def export_report(
    start_date: datetime = Query(..., description="Start date for export"),
    end_date: datetime = Query(..., description="End date for export"),
    format: str = Query("csv", regex="^(csv|json|pdf)$", description="Export format"),
    include_charts: bool = Query(False, description="Include charts in PDF export"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsExportResponse:
    """
    Export analytics report in specified format.

    **Parameters:**
    - **start_date**: Start date for export period
    - **end_date**: End date for export period
    - **format**: Export format (csv, json, pdf)
    - **include_charts**: Include charts in PDF export (PDF only)

    **Returns:**
    - Export response with file path and metadata
    """
    try:
        # Validate date range
        if end_date < start_date:
            raise HTTPException(
                status_code=422,
                detail="end_date must be after start_date",
            )

        # Get all metrics
        lead_metrics = await service.get_lead_metrics(
            start_date=start_date,
            end_date=end_date,
        )
        email_metrics = await service.get_email_metrics(
            start_date=start_date,
            end_date=end_date,
        )
        funnel = await service.get_conversion_funnel(
            start_date=start_date,
            end_date=end_date,
        )

        # Generate report
        generator = ReportGenerator()

        if format == "csv":
            file_path = generator.generate_csv_report(
                lead_metrics=lead_metrics,
                email_metrics=email_metrics,
                funnel=funnel,
            )
        elif format == "json":
            realtime_stats = await service.get_real_time_stats()
            file_path = generator.generate_json_report(
                lead_metrics=lead_metrics,
                email_metrics=email_metrics,
                funnel=funnel,
                realtime_stats=realtime_stats,
            )
        elif format == "pdf":
            file_path = generator.generate_pdf_report(
                lead_metrics=lead_metrics,
                email_metrics=email_metrics,
                funnel=funnel,
                include_charts=include_charts,
            )
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported format: {format}",
            )

        # Get file size
        import os
        file_size = os.path.getsize(file_path)

        return AnalyticsExportResponse(
            file_path=file_path,
            file_size=file_size,
            format=format,
            generated_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export report: {str(e)}",
        )


@router.websocket("/ws")
async def analytics_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analytics updates.

    Sends real-time statistics every 5 seconds.

    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/analytics/ws');
    ws.onmessage = (event) => {
        const stats = JSON.parse(event.data);
        console.log('Real-time stats:', stats);
    };
    ```
    """
    await websocket.accept()

    try:
        # Get database session for this WebSocket connection
        async for db in get_db():
            service = AnalyticsService(db)

            while True:
                try:
                    # Get real-time stats
                    stats = await service.get_real_time_stats()

                    # Send to client
                    await websocket.send_json(stats.model_dump())

                    # Wait 5 seconds before next update
                    await asyncio.sleep(5)

                except Exception as e:
                    # Log error but continue
                    print(f"Error sending real-time stats: {e}")
                    await asyncio.sleep(5)

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Close WebSocket connection
        try:
            await websocket.close()
        except Exception:
            pass
