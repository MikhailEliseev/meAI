"""Test CI pipeline with named competitor URLs (bypasses DaData)."""
import asyncio
import logging
import sys
import time

sys.path.insert(0, "/Users/mikhaileliseev/Desktop/Dev/meAI")
sys.path.insert(0, "/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from aim.services.ci.pipeline_runner import PipelineRunner


async def main():
    url = "https://yutskovskaya.ru"
    competitors = [
        "https://iphik.ru",
        "https://linline.ru",
        "https://yutskovskaya.ru",
    ]

    print(f"\n{'='*60}")
    print(f"Testing CI Pipeline with URL-based competitors")
    print(f"Client: {url}")
    print(f"Competitors: {competitors}")
    print(f"{'='*60}\n")

    async def on_progress(progress):
        print(f"  [{progress.stage}] {progress.message}")

    runner = PipelineRunner(on_progress=on_progress, timeout=60.0)
    t0 = time.monotonic()

    try:
        collected = await runner.run(
            client_url=url,
            named_competitors=competitors,
        )
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    elapsed = time.monotonic() - t0
    print(f"\n{'='*60}")
    print(f"Results ({len(collected)} competitors, {elapsed:.1f}s)")
    print(f"{'='*60}")
    for c in collected:
        print(f"\n--- {c.name} ---")
        print(f"  URL: {c.url}")
        print(f"  Features: {c.website_features}")
        print(f"  Missing: {c.website_missing}")
        print(f"  Doctors: {c.doctors_count}")
        print(f"  Directions: {c.directions_claimed}")
        print(f"  Pricing: {c.pricing_visible}")
        print(f"  Positioning: {c.positioning[:100] if c.positioning else 'N/A'}")
        if c.seo:
            print(f"  SEO score: {c.seo.score}, Issues: {len(c.seo.issues)}")
        if c.social:
            print(f"  Social platforms: {c.social.total_platforms_found}")
        if c.financials:
            print(f"  Financials: {bool(c.financials.get('revenue'))}")

    print(f"\nDone! {elapsed:.1f}s total")


if __name__ == "__main__":
    asyncio.run(main())
