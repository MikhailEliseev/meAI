"""End-to-end test: full CI pipeline + Hermes API."""

import asyncio
import sys
import time

sys.path.insert(0, "/Users/mikhaileliseev/Desktop/Dev/meAI")
sys.path.insert(0, "/Users/mikhaileliseev/Desktop/Dev/meAI/AIM")

from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner
from AIM.src.aim.services.ci.models import CompetitorFull


async def progress_handler(progress):
    """Print pipeline progress updates."""
    icon = {
        "searching": "🔍",
        "collecting": "📊",
        "seo": "🔎",
        "social": "📱",
        "financials": "💰",
        "scraping": "🌐",
        "matrix": "📈",
        "done": "✅",
    }.get(progress.stage, "⚙️")
    name = f" [{progress.competitor_name}]" if progress.competitor_name else ""
    print(f"  {icon} {progress.message}{name}")


async def main():
    print("=" * 70)
    print("FULL CI PIPELINE TEST — Юцковская, косметология, Москва")
    print("  (расширенный полигон 278×133 км)")
    print("=" * 70)
    print()

    runner = PipelineRunner(
        on_progress=progress_handler,
        timeout=180.0,
    )

    t0 = time.monotonic()
    results = await runner.run(
        client_url="https://yutskovskaya.ru",
        client_inn="9717023304",
    )
    elapsed = time.monotonic() - t0

    print(f"\n{'=' * 70}")
    print(f"РЕЗУЛЬТАТЫ (за {elapsed:.0f} сек)")
    print(f"{'=' * 70}")

    if not results:
        print("❌ Конкуренты не найдены!")
        return 1

    for i, c in enumerate(results):
        print(f"\n── #{i+1} {c.name} ──")
        print(f"  URL: {c.url}")
        print(f"  Positioning: {c.positioning[:120] if c.positioning else '—'}")
        if c.financials:
            rev = c.financials.get("revenue", {})
            profit = c.financials.get("profit", {})
            trend = c.financials.get("trend", "")
            latest_rev = max(rev.values()) if rev else 0
            latest_profit = max(profit.values()) if profit else 0
            print(f"  💰 Выручка: {latest_rev:,.0f} ₽ (trend: {trend})")
            print(f"  💰 Прибыль: {latest_profit:,.0f} ₽")
        else:
            print("  💰 Финансы: не найдены (нет ИНН?)")
        if c.seo:
            print(f"  🔎 SEO score: {c.seo.score}")
        if c.social:
            print(f"  📱 Соцсети: {c.social.total_platforms_found} платформ")
        if c.website_features:
            print(f"  🌐 Фичи: {', '.join(c.website_features)}")
        if c.doctors_count > 0:
            print(f"  🩺 Врачей на сайте: {c.doctors_count}")

    print(f"\n{'=' * 70}")
    print(f"ИТОГО: {len(results)} конкурентов за {elapsed:.0f} сек")
    print(f"{'=' * 70}")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
