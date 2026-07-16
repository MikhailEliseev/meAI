"""Restore original nachalo competitors with financial data from DaData."""
import asyncio, json, httpx
from pathlib import Path

ARCHIVE = Path("/opt/data/sessions-archive/nachalo-clinica")
ORIGINAL_COMPETITORS = [
    {"name": "Медицинский центр «Семья» на Буденновском", "url": "https://semya-clinic.ru"},
    {"name": "«Семейный медицинский центр»", "url": "https://semeynaya.ru"},
    {"name": "Медицинский центр «Люди» на Тельмана", "url": "https://lydi-clinic.ru"},
    {"name": "«Наш доктор», семейная клиника", "url": "https://nashdoctor.ru"},
]


async def main():
    prescan = json.loads((ARCHIVE / "prescan-data.json").read_text())
    url = prescan["url"]
    city = prescan.get("city", "Ростов-на-Дону")

    fin = prescan.get("stage_1_financials", prescan.get("financials", {}))
    specialization = fin.get("main_activity", "медицинская клиника")
    services = fin.get("services", []) or []

    # Step 1: Look up original competitors by name
    named = [c["name"] for c in ORIGINAL_COMPETITORS]
    print(f"Looking up original competitors: {named}")

    async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=30)) as client:
        find_resp = await client.post(
            "http://app:8000/api/competitors/find",
            json={
                "url": url,
                "count": 4,
                "named_competitors": named,
            },
        )
        find_data = find_resp.json()
        print(f"Find success: {find_data.get('success')}, found: {len(find_data.get('competitors', []))}")

        competitors = find_data.get("competitors", [])
        for c in competitors:
            sl = c.get("social_links", {}) or {}
            insta = sl.get("instagram", "") if isinstance(sl, dict) else ""
            print(
                f"  {c.get('brand_name') or c.get('legal_name')}: "
                f"rev={c.get('revenue_year')}, trend={c.get('revenue_trend')}, "
                f"emp={c.get('employee_count')}, insta={insta}"
            )

        if not competitors:
            print("No competitors found via named_competitors. Falling back to direct analyze with original URLs.")
            # Build minimal competitor objects for the analyze API
            competitors = [
                {
                    "brand_name": c["name"],
                    "legal_name": c["name"],
                    "website": c["url"],
                }
                for c in ORIGINAL_COMPETITORS
            ]

        # Step 2: Run CI analysis with these competitors
        print("\nRunning CI analysis...")
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
        print(f"Analysis success: {analyze_data.get('success')}")
        print(f"Duration: {analyze_data.get('duration_seconds', 0)}s")

        if analyze_data.get("success"):
            enriched = analyze_data.get("competitors", [])
            for c in enriched:
                print(
                    f"  {c.get('name')}: rev={c.get('revenue')}, "
                    f"trend={c.get('revenue_trend')}, docs={c.get('doctors')}, "
                    f"insta={c.get('instagram')}"
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
