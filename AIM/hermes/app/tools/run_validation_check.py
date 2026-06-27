"""
run_validation_check — Hermes tool: Cross-Source Data Validation

Performs quality control by cross-referencing data collected from
different sources during competitor analysis. Identifies:
- Internal contradictions (e.g., "200 patients/day" but revenue = 50M ₽)
- Confidence scores per data dimension
- Missing data that should have been found
- Recommendations for manual verification

No external API calls — purely analytical. The LLM passes collected data
from previous tool calls, and this tool structures it for consistency checking.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

from tools.registry import registry

logger = logging.getLogger(__name__)


async def handle_run_validation_check(
    company_name=None,
    website=None,
    revenue_data=None,
    seo_data=None,
    review_data=None,
    ad_data=None,
    competitor_data=None,
    **kwargs,
) -> str:
    """Cross-validate data collected from multiple sources about a competitor.

    Takes all the data Hermes has collected so far (from prescan, CI analysis,
    SEO audits, review scans, ad intelligence) and structures it for LLM-driven
    consistency checking.

    The LLM should examine the returned data and look for:
    - Revenue vs patient volume contradictions
    - SEO score vs content volume mismatches
    - Review rating vs review count anomalies
    - Ad spend vs revenue plausibility
    - Missing critical dimensions

    Args:
        company_name: Company being validated
        website: Company website URL
        revenue_data: Financial data from run_prescan or find_company_financials
        seo_data: SEO metrics from run_prescan or run_seo_audit
        review_data: Review aggregation from run_review_platforms or run_prescan
        ad_data: Advertising intelligence from run_ads_intelligence
        competitor_data: Competitor analysis from run_ci_analysis

    Returns:
        JSON with structured data dimensions, consistency flags, and verification checklist.
    """
    if isinstance(company_name, dict):
        d = company_name
        company_name = d.get("company_name", "")
        if website is None:
            website = d.get("website", "")
        if revenue_data is None:
            revenue_data = d.get("revenue_data")
        if seo_data is None:
            seo_data = d.get("seo_data")
        if review_data is None:
            review_data = d.get("review_data")
        if ad_data is None:
            ad_data = d.get("ad_data")
        if competitor_data is None:
            competitor_data = d.get("competitor_data")

    if not company_name:
        try:
            cached = Path("/tmp/hermes_last_company.txt").read_text().strip()
            if cached:
                logger.info("Using cached company name: %s", cached)
                company_name = cached
        except Exception:
            pass

    if not company_name:
        return json.dumps({"error": "company_name is required"})

    logger.info("Validation check for: %s", company_name)

    from app.main import push_tool_progress

    push_tool_progress("validation", f"Проверяю консистентность данных по «{company_name}»…")

    # Build structured dimensions for LLM analysis
    dimensions = {}

    # Financial dimension
    if revenue_data:
        dim = {"present": True, "source": "prescan/navod"}
        if isinstance(revenue_data, dict):
            dim["revenue"] = revenue_data.get("revenue_year")
            dim["profit"] = revenue_data.get("profit_year")
            dim["employees"] = revenue_data.get("employees_count")
            dim["year"] = revenue_data.get("financial_year")
            dim["trend"] = revenue_data.get("revenue_trend")

            # Quick sanity: revenue per employee
            rev = dim.get("revenue")
            emp = dim.get("employees")
            if rev and emp and emp > 0:
                rev_per_emp = rev / emp
                dim["revenue_per_employee"] = int(rev_per_emp)
                if rev_per_emp < 500_000:
                    dim["_flag"] = "Выручка на сотрудника подозрительно низкая (< 500 тыс ₽) — проверь данные"
                elif rev_per_emp > 20_000_000:
                    dim["_flag"] = "Выручка на сотрудника нереалистично высокая (> 20 млн ₽) — возможно, неполные данные"
        dimensions["financial"] = dim
    else:
        dimensions["financial"] = {"present": False, "_missing": "Нет финансовых данных — пропущена фаза prescan или nalog.ru"}

    # SEO dimension
    if seo_data:
        dim = {"present": True, "source": "prescan/seo-audit"}
        if isinstance(seo_data, dict):
            dim["seo_score"] = seo_data.get("seo_score")
            dim["performance_score"] = seo_data.get("performance_score")
            dim["core_web_vitals"] = seo_data.get("core_web_vitals")
            dim["pages_found"] = seo_data.get("pages_found")
            dim["has_schema"] = seo_data.get("has_schema_org")
            dim["has_ssl"] = seo_data.get("has_ssl")
            dim["cms"] = seo_data.get("cms")
        dimensions["seo"] = dim
    else:
        dimensions["seo"] = {"present": False, "_missing": "Нет SEO-данных"}

    # Review dimension
    if review_data:
        dim = {"present": True, "source": "review-platforms/prescan"}
        if isinstance(review_data, dict):
            dim["avg_rating"] = review_data.get("avg_rating")
            dim["total_reviews"] = review_data.get("total_review_count")
            dim["platforms_found"] = review_data.get("platforms_with_reviews")
            dim["reputation"] = review_data.get("reputation")

            # Quick sanity: rating vs review count
            rating = dim.get("avg_rating")
            count = dim.get("total_reviews", 0)
            if rating and count and count < 5 and float(rating) >= 4.9:
                dim["_flag"] = "Идеальный рейтинг при малом количестве отзывов — возможна накрутка"
        dimensions["reviews"] = dim
    else:
        dimensions["reviews"] = {"present": False, "_missing": "Нет данных об отзывах"}

    # Advertising dimension
    if ad_data:
        dim = {"present": True, "source": "ads-intelligence"}
        if isinstance(ad_data, dict):
            dim["total_ads"] = ad_data.get("total_active_ads")
            dim["ad_intensity"] = ad_data.get("ad_intensity")

            # Correlation: revenue vs ad intensity
            rev = dimensions.get("financial", {}).get("revenue")
            ad_intensity = dim.get("ad_intensity", "")
            if rev and "агрессивная" in str(ad_intensity) and rev < 50_000_000:
                dim["_flag"] = "Агрессивная реклама при низкой выручке — проверь окупаемость рекламы"
        dimensions["advertising"] = dim
    else:
        dimensions["advertising"] = {"present": False, "_missing": "Нет данных о рекламе"}

    # Competitor dimension
    if competitor_data:
        dim = {"present": True, "source": "ci-analysis"}
        dimensions["competitors"] = dim
    else:
        dimensions["competitors"] = {"present": False, "_missing": "Нет анализа конкурентов"}

    # Build the validation report
    present_dims = [k for k, v in dimensions.items() if v.get("present")]
    missing_dims = [k for k, v in dimensions.items() if not v.get("present")]

    flags = []
    for dim_name, dim_data in dimensions.items():
        flag = dim_data.pop("_flag", None)
        if flag:
            flags.append({"dimension": dim_name, "issue": flag})

    # Confidence assessment
    if len(present_dims) >= 4 and not flags:
        confidence = "высокая — данные консистентны по 4+ измерениям"
    elif len(present_dims) >= 3:
        confidence = "средняя — достаточно данных, есть мелкие расхождения"
    elif len(present_dims) >= 2:
        confidence = "низкая — мало измерений, возможны слепые зоны"
    else:
        confidence = "критически низкая — недостаточно данных для выводов"

    push_tool_progress(
        "validation",
        f"✅ Валидация: {len(present_dims)}/{len(dimensions)} измерений, "
        f"{len(flags)} флагов — достоверность: {confidence}",
    )

    return json.dumps({
        "company_name": company_name,
        "website": website,
        "dimensions_present": len(present_dims),
        "dimensions_total": len(dimensions),
        "dimensions_missing": missing_dims,
        "consistency_flags": flags,
        "total_flags": len(flags),
        "overall_confidence": confidence,
        "dimensions": dimensions,
        "verification_checklist": [
            "Сравни revenue_per_employee со средним по рынку (2-5 млн ₽/чел для клиник)",
            "Проверь, что SEO-скора соответствует реальной видимости сайта в поиске",
            "Сравни рейтинг и количество отзывов — идеальный рейтинг при <10 отзывов = подозрительно",
            "Проверь, что данные из prescan не противоречат данным из внешних источников",
            "Если есть aggressive-реклама, проверь окупаемость: revenue / ad_impressions",
        ],
    }, ensure_ascii=False, indent=2)


registry.register(
    name="run_validation_check",
    toolset="aim-operations",
    schema={
            "name": "run_validation_check",
            "description": (
                "Cross-validate all collected data about a competitor for internal consistency. "
                "Takes data from prescan, CI analysis, SEO audits, review scans, and ad intelligence "
                "and structures it for LLM-driven consistency checking. "
                "The LLM receives organized dimensions (financial, SEO, reviews, advertising, competitors) "
                "with pre-computed sanity flags (e.g., revenue-per-employee anomalies, "
                "perfect rating with too few reviews = possible manipulation). "
                "Also generates a verification checklist of things to manually check. "
                "Use this as the FINAL quality-control step before presenting findings to the client — "
                "never present unvalidated data to a potential client."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "[REQUIRED] Company being validated",
                    },
                    "website": {
                        "type": "string",
                        "description": "Company website URL",
                    },
                    "revenue_data": {
                        "type": "object",
                        "description": "Financial data from run_prescan or find_company_financials (revenue_year, profit_year, employees_count, etc.)",
                    },
                    "seo_data": {
                        "type": "object",
                        "description": "SEO metrics from run_prescan or run_seo_audit (seo_score, performance_score, core_web_vitals, etc.)",
                    },
                    "review_data": {
                        "type": "object",
                        "description": "Review aggregation from run_review_platforms or run_prescan (avg_rating, total_reviews, reputation)",
                    },
                    "ad_data": {
                        "type": "object",
                        "description": "Advertising intelligence from run_ads_intelligence (total_active_ads, ad_intensity)",
                    },
                    "competitor_data": {
                        "type": "object",
                        "description": "Competitor analysis results from run_ci_analysis",
                    },
                },
                "required": ["company_name"],
            },
        },
    handler=handle_run_validation_check,
    check_fn=lambda: True,
    is_async=True,
    description="Cross-validate all collected competitor data — sanity checks, contradictions, confidence score, QC checklist",
    emoji="🔍",
)
