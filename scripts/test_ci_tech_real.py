"""
Test CI Tech Agent - Real Technology Stack Analysis

Простой тест для проверки CI Tech Agent с реальным URL.
"""

import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.subagents.competitive_intel.agents.ci_tech_real import CITechAgent
from meai.agents.base_agent import Task


async def test_ci_tech_agent():
    """Test CI Tech Agent with real URL"""

    print("=" * 80)
    print("CI Tech Agent - Real Technology Stack Analysis Test")
    print("=" * 80)
    print()

    # Initialize agent
    agent = CITechAgent(
        agent_id="ci-tech-test",
        database_url="sqlite+aiosqlite:///./AIM/data/test.db",
        vault_path="./AIM/obsidian/ci-tech"
    )

    print("✓ Agent initialized")
    print()

    # Ask user for URL
    print("Введите URL сайта для анализа (или нажмите Enter для примера):")
    url = input("> ").strip()

    if not url:
        url = "https://example.com"
        print(f"Используем пример: {url}")

    print()
    print(f"Анализируем: {url}")
    print("-" * 80)
    print()

    # Create task
    task = Task(
        task_id="test-task-1",
        subtask_id="test-subtask-1",
        parent_task_id="test-parent-1",
        action="analyze_tech_stack",
        description=f"Analyze tech stack for {url}",
        priority=2,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )

    # Add payload manually (Task doesn't have payload field)
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
    print("РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("=" * 80)
    print()

    if result.status == "success":
        data = result.result

        print(f"✓ Анализ завершён успешно")
        print(f"  Время выполнения: {result.duration_seconds:.2f}s")
        print()

        # Tech profiles
        if data.get("tech_profiles"):
            profile = data["tech_profiles"][0]

            print("📊 ТЕХНОЛОГИЧЕСКИЙ ПРОФИЛЬ:")
            print(f"  Название: {profile.get('name')}")
            print(f"  URL: {profile.get('url')}")
            print(f"  CMS: {profile.get('cms', 'Unknown')}")
            print()

            # Technologies
            technologies = profile.get("technologies", [])
            if technologies:
                print(f"  Технологии ({len(technologies)}):")
                for tech in technologies:
                    print(f"    - {tech}")
                print()

            # SEO
            seo = profile.get("seo_optimization", {})
            if seo:
                print(f"  SEO Оптимизация:")
                print(f"    Балл: {seo.get('score', 0)}/100")
                if seo.get('issues'):
                    print(f"    Проблемы:")
                    for issue in seo['issues']:
                        print(f"      - {issue}")
                print()

            # GEO
            geo = profile.get("geo_optimization", {})
            if geo:
                print(f"  GEO/AI Оптимизация:")
                print(f"    Балл: {geo.get('ai_ready_score', 0)}/100")
                if geo.get('recommendations'):
                    print(f"    Рекомендации:")
                    for rec in geo['recommendations']:
                        print(f"      - {rec}")
                print()

            # Performance
            perf = profile.get("performance", {})
            if perf:
                print(f"  Производительность:")
                print(f"    Балл: {perf.get('score', 0)}/100")
                print(f"    Размер HTML: {perf.get('html_size_kb', 0):.1f} KB")
                if perf.get('issues'):
                    print(f"    Проблемы:")
                    for issue in perf['issues']:
                        print(f"      - {issue}")
                print()

        # Market analysis
        market = data.get("market_tech", {})
        if market:
            print("📈 РЫНОЧНЫЙ АНАЛИЗ:")
            print(f"  Популярная CMS: {market.get('most_popular_cms', 'Unknown')}")
            print(f"  Средний SEO балл: {market.get('avg_seo_score', 0)}/100")
            print(f"  Средний GEO балл: {market.get('avg_geo_score', 0)}/100")
            print()

        # Insights
        insights = data.get("insights", {})
        if insights:
            print("💡 ИНСАЙТЫ:")

            findings = insights.get("key_findings", [])
            if findings:
                print("  Ключевые находки:")
                for finding in findings:
                    print(f"    - {finding}")
                print()

            opportunities = insights.get("opportunities", [])
            if opportunities:
                print("  Возможности:")
                for opp in opportunities:
                    print(f"    - {opp}")
                print()

        # Results file
        print(f"📁 Результаты сохранены в: AIM/data/ci-tech/")
        print()

    else:
        print(f"✗ Анализ завершился с ошибкой")
        print(f"  Ошибка: {result.error}")
        print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(test_ci_tech_agent())
