"""
Test CI Deep Analyzer - Multiple Competitors Analysis

Анализ пула конкурентов из косметологии:
1. Tori Clinic (toriclinic.ru)
2. Professional Clinic
3. CIDK (Центральный институт дерматокосметологии)
4. Frau-Clinic
5. Клиника Юлии Щербатовой
"""

import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.subagents.competitive_intel.agents.ci_deep_analyzer import CIDeepAnalyzer
from meai.agents.base_agent import Task


async def test_multiple_competitors():
    """Test CI Deep Analyzer with multiple competitors"""

    print("=" * 80)
    print("CI Deep Analyzer - Multiple Competitors Analysis")
    print("=" * 80)
    print()

    # Initialize agent
    agent = CIDeepAnalyzer(
        agent_id="ci-deep-multi",
        database_url="sqlite+aiosqlite:///./AIM/data/test.db",
        vault_path="./AIM/obsidian/ci-deep",
        max_pages=50,
        delay_between_requests=2.0
    )

    print("✓ Agent initialized")
    print()

    # Competitors pool
    competitors = [
        {
            "name": "Tori Clinic",
            "url": "https://toriclinic.ru/"
        },
        {
            "name": "Professional Clinic",
            "url": "https://profclinic.ru/"
        },
        {
            "name": "CIDK",
            "url": "https://cidk.ru/"
        },
        {
            "name": "Frau Clinic",
            "url": "https://frauklinik.ru/"
        },
        {
            "name": "Клиника Юлии Щербатовой",
            "url": "https://doctor-shcherbatova.ru/"
        }
    ]

    print(f"🎯 Анализируем {len(competitors)} конкурентов:")
    for i, comp in enumerate(competitors, 1):
        print(f"  {i}. {comp['name']} - {comp['url']}")
    print()
    print("⏱️  Ожидаемое время: 10-30 минут на конкурента")
    print("⏱️  Общее время: ~50-150 минут (Quality Over Speed!)")
    print()

    # Create task
    task = Task(
        task_id="test-multi-1",
        subtask_id="test-multi-sub-1",
        parent_task_id="test-multi-parent-1",
        action="deep_competitor_analysis",
        description=f"Deep analysis of {len(competitors)} competitors",
        priority=2,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )

    task.payload = {
        "competitors": competitors
    }

    # Execute task
    print("🚀 Запускаем глубокий анализ...")
    print()

    result = await agent.execute_task(task)

    print()
    print("=" * 80)
    print("СВОДНЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 80)
    print()

    if result.status == "success":
        data = result.result

        print(f"✓ Анализ завершён успешно")
        print(f"  Время выполнения: {result.duration_seconds:.1f}s ({result.duration_seconds/60:.1f} минут)")
        print()

        # Summary table
        print("📊 СВОДНАЯ ТАБЛИЦА:")
        print()
        print(f"{'Конкурент':<30} {'Страниц':<10} {'SEO':<10} {'Schema':<10} {'Качество':<10}")
        print("-" * 80)

        for profile in data.get("deep_profiles", []):
            name = profile.get("name", "Unknown")[:28]
            pages = profile.get("pages_analyzed", 0)

            deep = profile.get("deep_analysis", {})
            seo_cov = deep.get("seo_coverage", {})
            schema_cov = deep.get("schema_coverage", "0/0")
            quality = deep.get("quality_score", 0)

            # Parse SEO coverage
            title_cov = seo_cov.get("title", "0/0")
            desc_cov = seo_cov.get("description", "0/0")

            print(f"{name:<30} {pages:<10} {desc_cov:<10} {schema_cov:<10} {quality:<10.1f}")

        print()

        # Market insights
        insights = data.get("market_insights", {})
        if insights:
            print("💡 РЫНОЧНЫЕ ИНСАЙТЫ:")
            print(f"  Конкурентов проанализировано: {insights.get('total_competitors')}")
            print(f"  Средняя глубина анализа: {insights.get('avg_pages_analyzed', 0):.0f} страниц")
            print()

        print(f"📁 Детальные результаты: AIM/data/ci-deep/")
        print()

    else:
        print(f"✗ Анализ завершился с ошибкой")
        print(f"  Ошибка: {result.error}")
        print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(test_multiple_competitors())
