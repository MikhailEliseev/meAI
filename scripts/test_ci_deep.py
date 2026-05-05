"""
Test CI Deep Analyzer - Deep Competitor Analysis

Глубокий анализ конкурента:
- Sitemap parsing
- Smart crawling
- Page classification
- Deep page analysis
- Aggregation
- Detailed reporting

Quality Over Speed: 10-30 минут на конкурента
"""

import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.subagents.competitive_intel.agents.ci_deep_analyzer import CIDeepAnalyzer
from meai.agents.base_agent import Task


async def test_ci_deep_analyzer():
    """Test CI Deep Analyzer with real URL"""

    print("=" * 80)
    print("CI Deep Analyzer - Deep Competitor Analysis Test")
    print("=" * 80)
    print()

    # Initialize agent
    agent = CIDeepAnalyzer(
        agent_id="ci-deep-test",
        database_url="sqlite+aiosqlite:///./AIM/data/test.db",
        vault_path="./AIM/obsidian/ci-deep",
        max_pages=50,  # Analyze up to 50 pages
        delay_between_requests=2.0  # 2 seconds between requests
    )

    print("✓ Agent initialized")
    print(f"  Max pages: {agent.max_pages}")
    print(f"  Delay: {agent.delay}s between requests")
    print()

    # Ask user for URL
    print("Введите URL сайта для глубокого анализа (или нажмите Enter для примера):")
    url = input("> ").strip()

    if not url:
        url = "https://toriclinic.ru/"
        print(f"Используем пример: {url}")

    print()
    print(f"🔍 Глубокий анализ: {url}")
    print("-" * 80)
    print()
    print("⏱️  Ожидаемое время: 10-30 минут")
    print("💡 Quality Over Speed: анализируем по молекулам!")
    print()

    # Create task
    task = Task(
        task_id="test-task-1",
        subtask_id="test-subtask-1",
        parent_task_id="test-parent-1",
        action="deep_competitor_analysis",
        description=f"Deep analysis for {url}",
        priority=2,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )

    # Add payload manually
    task.payload = {
        "competitors": [
            {
                "name": "Test Competitor",
                "url": url
            }
        ]
    }

    # Execute task
    result = await agent.execute_task(task)

    print()
    print("=" * 80)
    print("РЕЗУЛЬТАТЫ ГЛУБОКОГО АНАЛИЗА")
    print("=" * 80)
    print()

    if result.status == "success":
        data = result.result

        print(f"✓ Глубокий анализ завершён успешно")
        print(f"  Время выполнения: {result.duration_seconds:.1f}s ({result.duration_seconds/60:.1f} минут)")
        print()

        # Deep profiles
        if data.get("deep_profiles"):
            profile = data["deep_profiles"][0]

            print("📊 ГЛУБОКИЙ ПРОФИЛЬ КОНКУРЕНТА:")
            print(f"  Название: {profile.get('name')}")
            print(f"  URL: {profile.get('url')}")
            print(f"  Всего найдено страниц: {profile.get('total_pages_found')}")
            print(f"  Проанализировано страниц: {profile.get('pages_analyzed')}")
            print()

            # Page types
            page_types = profile.get("page_types", {})
            if page_types:
                print("📑 ТИПЫ СТРАНИЦ:")
                for page_type, urls in page_types.items():
                    if urls:
                        print(f"  {page_type}: {len(urls)} страниц")
                print()

            # Deep analysis
            deep = profile.get("deep_analysis", {})
            if deep:
                print("🔬 ГЛУБОКИЙ АНАЛИЗ:")
                print(f"  Всего страниц: {deep.get('total_pages')}")

                page_type_counts = deep.get("page_types", {})
                if page_type_counts:
                    print(f"  Распределение по типам:")
                    for ptype, count in page_type_counts.items():
                        print(f"    - {ptype}: {count}")

                seo_cov = deep.get("seo_coverage", {})
                if seo_cov:
                    print(f"  SEO покрытие:")
                    print(f"    - Title: {seo_cov.get('title')}")
                    print(f"    - Description: {seo_cov.get('description')}")
                    print(f"    - H1: {seo_cov.get('h1')}")

                print(f"  Schema.org покрытие: {deep.get('schema_coverage')}")
                print(f"  Качество: {deep.get('quality_score', 0):.1f}/100")
                print()

        # Market insights
        insights = data.get("market_insights", {})
        if insights:
            print("💡 РЫНОЧНЫЕ ИНСАЙТЫ:")
            print(f"  Конкурентов проанализировано: {insights.get('total_competitors')}")
            print(f"  Средняя глубина анализа: {insights.get('avg_pages_analyzed', 0):.0f} страниц")
            print(f"  Уровень анализа: {insights.get('analysis_depth')}")
            print()

        # Results file
        print(f"📁 Результаты сохранены в: AIM/data/ci-deep/")
        print()

    else:
        print(f"✗ Анализ завершился с ошибкой")
        print(f"  Ошибка: {result.error}")
        print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(test_ci_deep_analyzer())
