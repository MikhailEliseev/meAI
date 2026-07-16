"""Get financial data for nachalo competitors and save to ci-analysis.json."""
import asyncio, json, httpx
from pathlib import Path

ARCHIVE = Path("/opt/data/sessions-archive/nachalo-clinica")


async def main():
    prescan = json.loads((ARCHIVE / "prescan-data.json").read_text())
    url = prescan["url"]
    city = prescan.get("city", "Ростов-на-Дону")

    fin = prescan.get("stage_1_financials", prescan.get("financials", {}))
    specialization = fin.get("main_activity", "медицинская клиника")
    services = fin.get("services", []) or []

    print(f"URL: {url}, City: {city}, Spec: {specialization}")

    # Call find_competitors with long timeout
    async with httpx.AsyncClient(timeout=httpx.Timeout(600, connect=30)) as client:
        print("Finding competitors (may take 3-5 min)...")
        find_resp = await client.post(
            "http://app:8000/api/competitors/find",
            json={"url": url, "count": 4},
        )
        find_data = find_resp.json()
        if not find_data.get("success"):
            error_msg = find_data.get("error", "unknown")
            print(f"Find error: {error_msg}")
            return

        competitors = find_data["competitors"]
        print(f"Found {len(competitors)} competitors:")
        for c in competitors:
            sl = c.get("social_links", {}) or {}
            insta = sl.get("instagram", "") if isinstance(sl, dict) else ""
            print(
                f"  {c.get('brand_name') or c.get('legal_name')}: "
                f"rev={c.get('revenue_year')}, trend={c.get('revenue_trend')}, "
                f"emp={c.get('employee_count')}, insta={insta}"
            )

        # Now call analyze with enriched competitors
        print("\nRunning CI analysis (deep tier, ~5 min)...")
        analyze_resp = await client.post(
            "http://app:8000/api/competitors/analyze",
            json={
                "url": url,
                "specialization": specialization,
                "city": city,
                "services": services,
                "competitors": competitors,
                "tier": "deep",
            },
            timeout=600,
        )
        analyze_data = analyze_resp.json()

        if analyze_data.get("success"):
            enriched = analyze_data.get("competitors", [])
            print(f"\nEnriched competitors: {len(enriched)}")
            for c in enriched:
                print(
                    f"  {c.get('name')}: rev={c.get('revenue')}, "
                    f"trend={c.get('revenue_trend')}, "
                    f"docs={c.get('doctors')}, insta={c.get('instagram')}"
                )

            output = {
                "chat_summary": analyze_data.get("chat_summary", ""),
                "feature_matrix": analyze_data.get("feature_matrix", {}),
                "pricing_comparison": analyze_data.get("pricing_comparison", {}),
                "positioning_map": analyze_data.get("positioning_map", {}),
                "steal_worthy_tactics": analyze_data.get("steal_worthy_tactics", []),
                "top_recommendation": analyze_data.get("top_recommendation", ""),
                "competitors": enriched,
                "duration_seconds": analyze_data.get("duration_seconds", 0),
            }
            out_path = ARCHIVE / "ci-analysis.json"
            out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
            print(f"\nSaved ci-analysis.json ({len(json.dumps(output))} bytes)")
        else:
            print(f"Analysis error: {analyze_data.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
