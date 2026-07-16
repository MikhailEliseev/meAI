"""
Comprehensive Test for Phase 5 CI Agents

Тестирует все 7 параллельных агентов Phase 5:
- CI Finance
- CI Vacancies
- CI Tech
- CI Site Crawler
- CI Content
- CI Pricing
- CI Ecosystem
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.subagents.competitive_intel.agents.ci_finance import CIFinanceAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_vacancies import CIVacanciesAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_tech import CITechAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_site_crawler import CISiteCrawlerAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_content import CIContentAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_pricing import CIPricingAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_ecosystem import CIEcosystemAgent
from meai.agents.base_agent import Task


async def test_phase5_agents():
    """Тест всех агентов Phase 5."""

    print("=" * 80)
    print("🧪 ТЕСТ PHASE 5 CI AGENTS")
    print("=" * 80)
    print()

    # Тестовые данные конкурентов (из Phase 1)
    test_competitors = [
        {
            "name": "Клиника А",
            "website": "https://clinic-a.ru",
            "estimated_size": "medium",
            "price_segment": "mid"
        },
        {
            "name": "Клиника Б",
            "website": "https://clinic-b.ru",
            "estimated_size": "large",
            "price_segment": "premium"
        },
        {
            "name": "Клиника В",
            "website": "https://clinic-c.ru",
            "estimated_size": "small",
            "price_segment": "budget"
        },
        {
            "name": "Клиника Г",
            "website": "https://clinic-d.ru",
            "estimated_size": "medium",
            "price_segment": "mid"
        },
        {
            "name": "Клиника Д",
            "website": "https://clinic-e.ru",
            "estimated_size": "large",
            "price_segment": "premium"
        }
    ]

    niche = "стоматология"
    geo = "Москва"

    # Создаём агентов
    agents = {
        "CI Finance": CIFinanceAgent("ci-finance"),
        "CI Vacancies": CIVacanciesAgent("ci-vacancies"),
        "CI Tech": CITechAgent("ci-tech"),
        "CI Site Crawler": CISiteCrawlerAgent("ci-site-crawler"),
        "CI Content": CIContentAgent("ci-content"),
        "CI Pricing": CIPricingAgent("ci-pricing"),
        "CI Ecosystem": CIEcosystemAgent("ci-ecosystem")
    }

    print(f"📋 Тестовые данные:")
    print(f"   Ниша: {niche}")
    print(f"   Гео: {geo}")
    print(f"   Конкурентов: {len(test_competitors)}")
    print()

    # Запускаем агентов параллельно
    print("🚀 Запуск 7 агентов параллельно...")
    print()

    tasks = []
    for agent_name, agent in agents.items():
        task = Task(
            task_id=f"test_{agent.agent_id}",
            subtask_id=f"test_{agent.agent_id}_sub",
            parent_task_id="test_phase5",
            action="ci_analysis",
            description=f"Test {agent_name}",
            priority=1,
            status="received",
            created_at=datetime.now(),
            received_at=datetime.now()
        )
        # Добавляем payload как атрибут
        task.payload = {
            "competitors": test_competitors,
            "niche": niche,
            "geo": geo
        }
        tasks.append((agent_name, agent.execute_task(task)))

    # Выполняем параллельно
    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

    # Анализируем результаты
    print("=" * 80)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    print()

    success_count = 0
    failed_count = 0

    for (agent_name, _), result in zip(tasks, results):
        if isinstance(result, Exception):
            print(f"❌ {agent_name}: FAILED")
            print(f"   Ошибка: {result}")
            failed_count += 1
        elif result.status == "success":
            print(f"✅ {agent_name}: SUCCESS")

            # Выводим ключевые метрики
            if agent_name == "CI Finance":
                insights = result.result.get("insights", {})
                print(f"   Размер рынка: {insights.get('market_size', 'N/A')}")
                print(f"   Прибыльность: {insights.get('profitability', 'N/A')}")

            elif agent_name == "CI Vacancies":
                market = result.result.get("market_analysis", {})
                print(f"   Открытых вакансий: {market.get('total_open_vacancies', 0)}")
                print(f"   Средний размер команды: {market.get('avg_team_size', 0)}")

            elif agent_name == "CI Tech":
                market = result.result.get("market_tech", {})
                print(f"   Популярная CMS: {market.get('most_popular_cms', 'N/A')}")
                print(f"   Онлайн-запись: {market.get('online_booking_adoption', 0):.0f}%")

            elif agent_name == "CI Site Crawler":
                structure = result.result.get("structure_analysis", {})
                print(f"   Средний размер сайта: {structure.get('avg_pages', 0):.0f} страниц")
                print(f"   Мобильная адаптация: {structure.get('mobile_adoption_percent', 0):.0f}%")

            elif agent_name == "CI Content":
                market = result.result.get("market_analysis", {})
                print(f"   Среднее кол-во контента: {market.get('avg_content_pieces', 0):.0f}")
                print(f"   Средний качество: {market.get('avg_quality_score', 0):.0f}/100")

            elif agent_name == "CI Pricing":
                market = result.result.get("market_analysis", {})
                print(f"   Средний чек: {market.get('market_avg_check', 0):,.0f} руб")
                print(f"   Прозрачность цен: {market.get('price_transparency_percent', 0):.0f}%")

            elif agent_name == "CI Ecosystem":
                market = result.result.get("market_analysis", {})
                print(f"   Среднее партнёров: {market.get('avg_partners', 0):.1f}")
                print(f"   Среднее интеграций: {market.get('avg_integrations', 0):.1f}")

            success_count += 1
        else:
            print(f"❌ {agent_name}: FAILED")
            print(f"   Статус: {result.status}")
            print(f"   Ошибка: {result.error}")
            failed_count += 1

        print()

    # Итоговая статистика
    print("=" * 80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    print()
    print(f"✅ Успешно: {success_count}/7")
    print(f"❌ Ошибок: {failed_count}/7")
    print()

    if success_count == 7:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Phase 5 агенты работают корректно.")
    elif success_count > 0:
        print("⚠️  ЧАСТИЧНЫЙ УСПЕХ")
        print(f"{success_count} агентов работают, {failed_count} требуют исправления.")
    else:
        print("❌ ВСЕ ТЕСТЫ ПРОВАЛЕНЫ")
        print("Требуется отладка агентов.")

    print()
    print("=" * 80)

    # Проверяем созданные файлы
    print()
    print("📁 Проверка созданных файлов:")
    print()

    expected_files = [
        "AIM/data/ci-finance.json",
        "AIM/data/ci-vacancies.json",
        "AIM/data/ci-tech.json",
        "AIM/data/ci-site-crawler.json",
        "AIM/data/ci-content.json",
        "AIM/data/ci-pricing.json",
        "AIM/data/ci-ecosystem.json"
    ]

    files_created = 0
    for file_path in expected_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            files_created += 1
        else:
            print(f"❌ {file_path} - НЕ СОЗДАН")

    print()
    print(f"Создано файлов: {files_created}/{len(expected_files)}")
    print()

    return success_count == 7


if __name__ == "__main__":
    success = asyncio.run(test_phase5_agents())
    sys.exit(0 if success else 1)
