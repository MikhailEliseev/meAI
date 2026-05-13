"""
Analytics Service - Campaign performance tracking and ROI calculation.

Collects real metrics from Google Ads API and provides business intelligence.
"""

from typing import Any, Dict, List, Optional
import structlog
from datetime import datetime, timedelta

from AIM.src.aim.subagents.ads.api_clients.google_ads_client import GoogleAdsClient
from AIM.src.aim.subagents.ads.config.settings import AdsSettings

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """
    Campaign analytics and reporting service.
    
    Provides:
    - Real-time metrics collection
    - Performance tracking over time
    - ROI calculation
    - Trend analysis
    - Custom reporting
    """
    
    def __init__(
        self,
        settings: Optional[AdsSettings] = None,
        client: Optional[GoogleAdsClient] = None,
    ):
        """
        Initialize analytics service.
        
        Args:
            settings: Configuration settings
            client: Pre-initialized GoogleAdsClient (optional)
        """
        self.settings = settings or AdsSettings()
        self.client = client or GoogleAdsClient(settings=self.settings)
        
        logger.info("analytics_service_initialized")
    
    async def get_campaign_performance(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> Dict[str, Any]:
        """
        Get comprehensive campaign performance metrics.
        
        Args:
            campaign_id: Campaign ID
            date_range: Date range for metrics
        
        Returns:
            Performance metrics with calculations
        """
        logger.info(
            "fetching_campaign_performance",
            campaign_id=campaign_id,
            date_range=date_range,
        )
        
        # Get real metrics from API
        metrics_data = await self.client.get_campaign_metrics(
            campaign_id=campaign_id,
            date_range=date_range,
        )
        
        metrics = metrics_data["metrics"]
        
        # Calculate derived metrics
        clicks = metrics["clicks"]
        impressions = metrics["impressions"]
        cost_usd = metrics["cost_usd"]
        conversions = metrics["conversions"]
        conversions_value = metrics["conversions_value"]
        
        # CTR (already in metrics, but recalculate for verification)
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        
        # Conversion rate
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        
        # Cost per conversion
        cost_per_conversion = (cost_usd / conversions) if conversions > 0 else 0
        
        # ROI calculation
        roi = ((conversions_value - cost_usd) / cost_usd * 100) if cost_usd > 0 else 0
        
        # ROAS (Return on Ad Spend)
        roas = (conversions_value / cost_usd) if cost_usd > 0 else 0
        
        logger.info(
            "campaign_performance_calculated",
            campaign_id=campaign_id,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            roi=roi,
            roas=roas,
        )
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": metrics_data["campaign_name"],
            "date_range": date_range,
            "raw_metrics": {
                "impressions": impressions,
                "clicks": clicks,
                "cost_usd": cost_usd,
                "conversions": conversions,
                "conversions_value": conversions_value,
            },
            "calculated_metrics": {
                "ctr": round(ctr, 2),
                "conversion_rate": round(conversion_rate, 2),
                "avg_cpc": metrics["average_cpc"],
                "avg_cpm": metrics["average_cpm"],
                "cost_per_conversion": round(cost_per_conversion, 2),
            },
            "business_metrics": {
                "roi": round(roi, 2),
                "roas": round(roas, 2),
                "profit": round(conversions_value - cost_usd, 2),
            }
        }
    
    async def get_multi_campaign_performance(
        self,
        campaign_ids: List[str],
        date_range: str = "LAST_30_DAYS",
    ) -> Dict[str, Any]:
        """
        Get performance for multiple campaigns.
        
        Args:
            campaign_ids: List of campaign IDs
            date_range: Date range for metrics
        
        Returns:
            Aggregated performance across campaigns
        """
        logger.info(
            "fetching_multi_campaign_performance",
            campaign_count=len(campaign_ids),
            date_range=date_range,
        )
        
        campaigns_performance = []
        total_metrics = {
            "impressions": 0,
            "clicks": 0,
            "cost_usd": 0,
            "conversions": 0,
            "conversions_value": 0,
        }
        
        # Fetch performance for each campaign
        for campaign_id in campaign_ids:
            try:
                performance = await self.get_campaign_performance(
                    campaign_id=campaign_id,
                    date_range=date_range,
                )
                
                campaigns_performance.append(performance)
                
                # Aggregate totals
                raw = performance["raw_metrics"]
                total_metrics["impressions"] += raw["impressions"]
                total_metrics["clicks"] += raw["clicks"]
                total_metrics["cost_usd"] += raw["cost_usd"]
                total_metrics["conversions"] += raw["conversions"]
                total_metrics["conversions_value"] += raw["conversions_value"]
                
            except Exception as e:
                logger.error(
                    "campaign_performance_fetch_failed",
                    campaign_id=campaign_id,
                    error=str(e),
                )
        
        # Calculate aggregated metrics
        total_ctr = (total_metrics["clicks"] / total_metrics["impressions"] * 100) if total_metrics["impressions"] > 0 else 0
        total_conversion_rate = (total_metrics["conversions"] / total_metrics["clicks"] * 100) if total_metrics["clicks"] > 0 else 0
        total_roi = ((total_metrics["conversions_value"] - total_metrics["cost_usd"]) / total_metrics["cost_usd"] * 100) if total_metrics["cost_usd"] > 0 else 0
        total_roas = (total_metrics["conversions_value"] / total_metrics["cost_usd"]) if total_metrics["cost_usd"] > 0 else 0
        
        logger.info(
            "multi_campaign_performance_calculated",
            campaign_count=len(campaigns_performance),
            total_cost=total_metrics["cost_usd"],
            total_conversions=total_metrics["conversions"],
            total_roi=total_roi,
        )
        
        return {
            "date_range": date_range,
            "campaigns_count": len(campaigns_performance),
            "campaigns": campaigns_performance,
            "totals": {
                "raw_metrics": total_metrics,
                "calculated_metrics": {
                    "ctr": round(total_ctr, 2),
                    "conversion_rate": round(total_conversion_rate, 2),
                    "avg_cpc": round(total_metrics["cost_usd"] / total_metrics["clicks"], 2) if total_metrics["clicks"] > 0 else 0,
                },
                "business_metrics": {
                    "roi": round(total_roi, 2),
                    "roas": round(total_roas, 2),
                    "profit": round(total_metrics["conversions_value"] - total_metrics["cost_usd"], 2),
                }
            }
        }
    
    async def track_performance_trend(
        self,
        campaign_id: str,
        periods: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Track performance trend over multiple periods.
        
        Args:
            campaign_id: Campaign ID
            periods: List of date ranges (default: last 7, 14, 30 days)
        
        Returns:
            Trend analysis with period-over-period comparison
        """
        if periods is None:
            periods = ["LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS"]
        
        logger.info(
            "tracking_performance_trend",
            campaign_id=campaign_id,
            periods=periods,
        )
        
        trend_data = []
        
        for period in periods:
            try:
                performance = await self.get_campaign_performance(
                    campaign_id=campaign_id,
                    date_range=period,
                )
                
                trend_data.append({
                    "period": period,
                    "metrics": performance["calculated_metrics"],
                    "business_metrics": performance["business_metrics"],
                })
                
            except Exception as e:
                logger.error(
                    "trend_period_fetch_failed",
                    campaign_id=campaign_id,
                    period=period,
                    error=str(e),
                )
        
        # Calculate trends (period-over-period changes)
        trends = []
        for i in range(1, len(trend_data)):
            current = trend_data[i]
            previous = trend_data[i-1]
            
            ctr_change = current["metrics"]["ctr"] - previous["metrics"]["ctr"]
            roi_change = current["business_metrics"]["roi"] - previous["business_metrics"]["roi"]
            
            trends.append({
                "from_period": previous["period"],
                "to_period": current["period"],
                "changes": {
                    "ctr": round(ctr_change, 2),
                    "roi": round(roi_change, 2),
                    "ctr_direction": "up" if ctr_change > 0 else "down" if ctr_change < 0 else "stable",
                    "roi_direction": "up" if roi_change > 0 else "down" if roi_change < 0 else "stable",
                }
            })
        
        logger.info(
            "performance_trend_calculated",
            campaign_id=campaign_id,
            periods_analyzed=len(trend_data),
        )
        
        return {
            "campaign_id": campaign_id,
            "periods": trend_data,
            "trends": trends,
        }
    
    async def calculate_roi(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
        revenue_per_conversion: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate detailed ROI analysis.
        
        Args:
            campaign_id: Campaign ID
            date_range: Date range for calculation
            revenue_per_conversion: Override revenue per conversion (if not tracked in API)
        
        Returns:
            Detailed ROI breakdown
        """
        logger.info(
            "calculating_roi",
            campaign_id=campaign_id,
            date_range=date_range,
        )
        
        # Get metrics
        metrics_data = await self.client.get_campaign_metrics(
            campaign_id=campaign_id,
            date_range=date_range,
        )
        
        metrics = metrics_data["metrics"]
        cost_usd = metrics["cost_usd"]
        conversions = metrics["conversions"]
        conversions_value = metrics["conversions_value"]
        
        # Use provided revenue or API value
        if revenue_per_conversion is not None:
            total_revenue = conversions * revenue_per_conversion
        else:
            total_revenue = conversions_value
        
        # Calculate ROI components
        total_cost = cost_usd
        total_profit = total_revenue - total_cost
        roi_percentage = (total_profit / total_cost * 100) if total_cost > 0 else 0
        roas = (total_revenue / total_cost) if total_cost > 0 else 0
        
        # Break-even analysis
        break_even_conversions = total_cost / (revenue_per_conversion or (conversions_value / conversions if conversions > 0 else 0))
        conversions_to_break_even = max(0, break_even_conversions - conversions)
        
        logger.info(
            "roi_calculated",
            campaign_id=campaign_id,
            roi_percentage=roi_percentage,
            roas=roas,
            profit=total_profit,
        )
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": metrics_data["campaign_name"],
            "date_range": date_range,
            "financial_summary": {
                "total_cost": round(total_cost, 2),
                "total_revenue": round(total_revenue, 2),
                "total_profit": round(total_profit, 2),
                "roi_percentage": round(roi_percentage, 2),
                "roas": round(roas, 2),
            },
            "conversion_economics": {
                "conversions": conversions,
                "revenue_per_conversion": round(total_revenue / conversions, 2) if conversions > 0 else 0,
                "cost_per_conversion": round(total_cost / conversions, 2) if conversions > 0 else 0,
                "profit_per_conversion": round(total_profit / conversions, 2) if conversions > 0 else 0,
            },
            "break_even_analysis": {
                "break_even_conversions": round(break_even_conversions, 2),
                "conversions_to_break_even": round(conversions_to_break_even, 2),
                "is_profitable": total_profit > 0,
            }
        }
    
    async def generate_performance_report(
        self,
        campaign_ids: List[str],
        date_range: str = "LAST_30_DAYS",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            campaign_ids: List of campaign IDs
            date_range: Date range for report
        
        Returns:
            Full performance report with insights
        """
        logger.info(
            "generating_performance_report",
            campaign_count=len(campaign_ids),
            date_range=date_range,
        )
        
        # Get multi-campaign performance
        performance = await self.get_multi_campaign_performance(
            campaign_ids=campaign_ids,
            date_range=date_range,
        )
        
        # Identify top performers
        campaigns = performance["campaigns"]
        top_roi = max(campaigns, key=lambda x: x["business_metrics"]["roi"]) if campaigns else None
        top_roas = max(campaigns, key=lambda x: x["business_metrics"]["roas"]) if campaigns else None
        top_conversions = max(campaigns, key=lambda x: x["raw_metrics"]["conversions"]) if campaigns else None
        
        # Generate insights
        insights = []
        
        totals = performance["totals"]
        if totals["business_metrics"]["roi"] < 0:
            insights.append({
                "type": "warning",
                "message": f"Overall ROI is negative ({totals['business_metrics']['roi']}%). Review campaign targeting and landing pages.",
            })
        
        if totals["calculated_metrics"]["ctr"] < 2.0:
            insights.append({
                "type": "improvement",
                "message": f"Overall CTR ({totals['calculated_metrics']['ctr']}%) is below industry average. Consider improving ad copy.",
            })
        
        if top_roi:
            insights.append({
                "type": "success",
                "message": f"Top performing campaign by ROI: {top_roi['campaign_name']} ({top_roi['business_metrics']['roi']}%)",
            })
        
        logger.info(
            "performance_report_generated",
            campaign_count=len(campaigns),
            insights_count=len(insights),
        )
        
        return {
            "report_date": datetime.now().isoformat(),
            "date_range": date_range,
            "summary": performance["totals"],
            "campaigns": campaigns,
            "top_performers": {
                "by_roi": {
                    "campaign_id": top_roi["campaign_id"] if top_roi else None,
                    "campaign_name": top_roi["campaign_name"] if top_roi else None,
                    "roi": top_roi["business_metrics"]["roi"] if top_roi else None,
                } if top_roi else None,
                "by_roas": {
                    "campaign_id": top_roas["campaign_id"] if top_roas else None,
                    "campaign_name": top_roas["campaign_name"] if top_roas else None,
                    "roas": top_roas["business_metrics"]["roas"] if top_roas else None,
                } if top_roas else None,
                "by_conversions": {
                    "campaign_id": top_conversions["campaign_id"] if top_conversions else None,
                    "campaign_name": top_conversions["campaign_name"] if top_conversions else None,
                    "conversions": top_conversions["raw_metrics"]["conversions"] if top_conversions else None,
                } if top_conversions else None,
            },
            "insights": insights,
        }
    
    def close(self) -> None:
        """Close service and cleanup resources."""
        self.client.close()
        logger.info("analytics_service_closed")
