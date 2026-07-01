"""
Test script: PRESALE pipeline end-to-end test for 3 clinics.
Runs find_competitors + analyze and logs all results for pattern analysis.
"""
import json
import sys
import time
import traceback
from datetime import datetime

import httpx

AIM_API_BASE = "http://localhost:8000"
TIMEOUT = 120  # seconds per call

CLINICS = [
    {
        "name": "Delight Lancette",
        "url": "https://delight-lancette.ru",
        "specialization": "косметология",
        "city": "Москва",
    },
    {
        "name": "Dental Clinic SPb",
        "url": "https://dentalclinic-spb.ru",
        "specialization": "стоматология",
        "city": "Санкт-Петербург",
    },
    {
        "name": "MED4YOU",
        "url": "https://med4you.ru",
        "specialization": "многопрофильная клиника",
        "city": "Москва",
    },
]


def analyze_result(clinic_name: str, stage: str, data: dict) -> list[str]:
    """Analyze API response and return list of issues found."""
    issues = []
    prefix = f"[{clinic_name}] [{stage}]"

    if not data:
        issues.append(f"{prefix} EMPTY response")
        return issues

    if data.get("error"):
        issues.append(f"{prefix} ERROR: {data.get('error')} — {data.get('detail', '')}")
        return issues

    if stage == "find_competitors":
        competitors = data.get("competitors", [])
        if not competitors:
            issues.append(f"{prefix} 0 competitors found")
        else:
            for i, c in enumerate(competitors):
                cname = c.get("brand_name") or c.get("legal_name") or f"#{i+1}"
                if not c.get("revenue_year"):
                    issues.append(f"{prefix} competitor '{cname}': revenue_year = None")
                if not c.get("profit_year"):
                    issues.append(f"{prefix} competitor '{cname}': profit_year = None")
                if not c.get("website"):
                    issues.append(f"{prefix} competitor '{cname}': website = None")
                if not c.get("services"):
                    issues.append(f"{prefix} competitor '{cname}': services = [] (empty)")
                if c.get("total_score", 0) == 0:
                    issues.append(f"{prefix} competitor '{cname}': total_score = 0")
                if c.get("revenue_source") == "none":
                    issues.append(f"{prefix} competitor '{cname}': revenue_source = 'none' (no financial data)")

    elif stage == "analyze":
        if not data.get("chat_summary"):
            issues.append(f"{prefix} chat_summary is empty")
        if not data.get("feature_matrix"):
            issues.append(f"{prefix} feature_matrix is empty")
        if not data.get("pricing_comparison"):
            issues.append(f"{prefix} pricing_comparison is empty")
        if not data.get("steal_worthy_tactics"):
            issues.append(f"{prefix} steal_worthy_tactics = [] (0 tactics)")
        else:
            tactics = data["steal_worthy_tactics"]
            issues.append(f"{prefix} steal_worthy_tactics count = {len(tactics)}")
        if data.get("duration_seconds", 0) < 1:
            issues.append(f"{prefix} duration_seconds < 1s (probably failed fast)")
        if data.get("top_recommendation") in (None, "", "Нет данных"):
            issues.append(f"{prefix} top_recommendation is empty or 'Нет данных'")

    return issues


async def test_clinic(client: httpx.AsyncClient, clinic: dict) -> dict:
    """Run full pipeline for one clinic."""
    result = {
        "clinic": clinic["name"],
        "url": clinic["url"],
        "timestamp": datetime.now().isoformat(),
        "stages": {},
        "issues": [],
    }

    # Stage 1: find_competitors
    t0 = time.monotonic()
    try:
        r = await client.post(
            f"{AIM_API_BASE}/api/competitors/find",
            json={"url": clinic["url"], "count": 3},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        find_data = r.json()
    except Exception as e:
        find_data = {"error": str(e), "detail": traceback.format_exc()}
    t1 = time.monotonic()
    result["stages"]["find_competitors"] = {
        "duration_s": round(t1 - t0, 1),
        "response": find_data,
    }
    result["issues"] += analyze_result(clinic["name"], "find_competitors", find_data)

    # Stage 2: analyze competitors (if we have competitors)
    competitors = find_data.get("competitors", []) if isinstance(find_data, dict) else []
    if competitors and not find_data.get("error"):
        t0 = time.monotonic()
        try:
            r = await client.post(
                f"{AIM_API_BASE}/api/competitors/analyze",
                json={
                    "url": clinic["url"],
                    "specialization": clinic["specialization"],
                    "city": clinic["city"],
                    "services": [],
                    "competitors": competitors,
                    "tier": "quick",
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            analyze_data = r.json()
        except Exception as e:
            analyze_data = {"error": str(e), "detail": traceback.format_exc()}
        t1 = time.monotonic()
        result["stages"]["analyze"] = {
            "duration_s": round(t1 - t0, 1),
            "response": analyze_data,
        }
        result["issues"] += analyze_result(clinic["name"], "analyze", analyze_data)
    else:
        result["stages"]["analyze"] = {
            "duration_s": 0,
            "skipped": True,
            "reason": "no competitors to analyze" if not competitors else f"find_competitors error: {find_data.get('error')}",
        }

    return result


async def main():
    all_results = []
    all_issues = []

    async with httpx.AsyncClient() as client:
        for clinic in CLINICS:
            print(f"\n{'='*60}")
            print(f"Testing: {clinic['name']} ({clinic['url']})")
            print(f"{'='*60}")
            result = await test_clinic(client, clinic)
            all_results.append(result)
            all_issues += result["issues"]

            # Print stage results
            for stage_name, stage_data in result["stages"].items():
                if stage_data.get("skipped"):
                    print(f"  {stage_name}: SKIPPED — {stage_data.get('reason')}")
                elif "error" in stage_data.get("response", {}):
                    print(f"  {stage_name}: ERROR in {stage_data['duration_s']}s — {stage_data['response']['error']}")
                else:
                    print(f"  {stage_name}: OK in {stage_data['duration_s']}s")

            # Print issues for this clinic
            clinic_issues = result["issues"]
            if clinic_issues:
                print(f"  ISSUES ({len(clinic_issues)}):")
                for issue in clinic_issues:
                    print(f"    - {issue}")

    # Final summary
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Total issues: {len(all_issues)}")
    if all_issues:
        print(f"\nAll issues:")
        for issue in all_issues:
            print(f"  - {issue}")

    # Save full dump
    dump_path = "/tmp/presale_test_dump.json"
    with open(dump_path, "w") as f:
        json.dump({"results": all_results, "issues": all_issues}, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nFull dump saved to: {dump_path}")
    print(f"Size: {len(json.dumps(all_results, ensure_ascii=False, default=str))} chars")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
