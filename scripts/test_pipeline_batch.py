"""Batch test: find_competitors pipeline for 10 random clinic URLs."""
import json
import time
import httpx
import asyncio

URLS = [
    "https://yutskovskaya.ru",
    "https://drsheikh.ru",
    "https://linline.ru",
    "https://dklinika.ru",
    "https://artdent.ru",
    "https://dentalway.ru",
    "https://vse-svoi.ru",
    "https://innova-stom.ru",
    "https://mendeleev-dental.ru",
    "https://estet-clinic.ru",
]

API = "http://app:8000"
TIMEOUT = 200  # full pipeline up to 180s


async def test_one(client: httpx.AsyncClient, url: str) -> dict:
    t0 = time.monotonic()
    result = {"url": url, "ok": False, "elapsed_s": 0, "competitors": 0, "error": None, "details": None}

    try:
        resp = await client.post(
            f"{API}/api/competitors/find",
            json={"url": url, "count": 5},
            timeout=TIMEOUT,
        )
        elapsed = time.monotonic() - t0
        result["elapsed_s"] = round(elapsed, 1)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                comps = data.get("competitors", [])
                result["ok"] = True
                result["competitors"] = len(comps)
                result["details"] = {
                    c.get("legal_name", "?"): {
                        "revenue": c.get("revenue_year"),
                        "score": c.get("total_score"),
                        "source": c.get("data_source"),
                        "inn": c.get("inn"),
                        "brand": c.get("brand_name", "")[:40],
                    }
                    for c in comps[:5]
                }
                print(f"  ✅ {url}: {len(comps)} competitors in {elapsed:.1f}s")
                for c in comps[:5]:
                    inn = c.get('inn', '') or '-'
                    brand = (c.get('brand_name', '') or '')[:30]
                    print(f"     - {c.get('legal_name', '?')[:50]} | INN={inn} | revenue={c.get('revenue_year')} | score={c.get('total_score')}")
            else:
                result["error"] = data.get("error", "unknown")
                print(f"  ❌ {url}: API error — {result['error']}")
        else:
            result["error"] = f"HTTP {resp.status_code}"
            print(f"  ❌ {url}: HTTP {resp.status_code}")

    except httpx.TimeoutException:
        result["elapsed_s"] = round(time.monotonic() - t0, 1)
        result["error"] = "timeout"
        print(f"  ⏱️  {url}: timeout after {result['elapsed_s']}s")
    except Exception as e:
        result["elapsed_s"] = round(time.monotonic() - t0, 1)
        result["error"] = str(e)
        print(f"  💥 {url}: {e}")

    return result


async def main():
    print(f"🚀 Testing {len(URLS)} URLs...\n")
    t0 = time.monotonic()

    async with httpx.AsyncClient() as client:
        # Run sequentially to avoid overloading Apify/DaData
        results = []
        for i, url in enumerate(URLS, 1):
            print(f"[{i}/{len(URLS)}] {url}")
            result = await test_one(client, url)
            results.append(result)
            print()

    total = time.monotonic() - t0

    # Summary
    ok = [r for r in results if r["ok"]]
    fail = [r for r in results if not r["ok"]]

    print("=" * 60)
    print(f"SUMMARY ({len(URLS)} URLs, {total:.0f}s total)")
    print(f"  ✅ Success: {len(ok)}")
    print(f"  ❌ Failed:  {len(fail)}")
    if ok:
        avg_time = sum(r["elapsed_s"] for r in ok) / len(ok)
        total_comps = sum(r["competitors"] for r in ok)
        print(f"  ⏱️  Avg time: {avg_time:.1f}s")
        print(f"  🏢 Total competitors found: {total_comps}")
    if fail:
        for r in fail:
            print(f"  ❌ {r['url']}: {r['error']}")

    # Save detailed log
    log = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_s": round(total, 1),
        "results": results,
    }
    with open("/tmp/pipeline_test_results.json", "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\n📄 Full log: /tmp/pipeline_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
