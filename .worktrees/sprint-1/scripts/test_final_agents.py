"""
Comprehensive Test for Phase 9, 10, 16 CI Agents

Тестирует финальные агенты:
- Phase 9: CI Prioritizer
- Phase 10: CI Marketing Strategy
- Phase 16: CI Offer Generator
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.subagents.competitive_intel.agents.ci_prioritizer import CIPrioritizerAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_marketing_strategy import CIMarketingStrategyAgent
from AIM.src.aim.subagents.competitive_intel.agents.ci_offer_generator import CIOfferGeneratorAgent
from meai.agents.base_agent import Task


async def test_final_agents():
    """Тест финальных агентов."""

    print("=" * 80)
    print("🧪 ТЕСТ FINAL CI AGENTS (Phase 9, 10, 16)")
    print("=" * 80)
    print()

    # Мок данных из предыдущих фаз
    mock_previous_results = {
        "phase_1": {
            "competitors": [
                {"name": "Клиника А", "cluster": "direct"},
                {"name": "Клиника Б", "cluster": "direct"},
                {"name": "Клиника В", "cluster": "indirect"}
            ],
            "insights": [
                {"type": "market_opportunity", "title": "Низкая цифровизация", "description": "40% конкурентов без онлайн-записи", "value": 8}
            ]
        },
        "phase_2": {
            "insights": [
                {"title": "Слабое SEO", "description": "Средний балл: 60/100", "value": 7}
            ]
        },
        "phase_4": {
            "insights": [
                {"title": "Репутация", "description": "Средний рейтинг: 4.2/5", "value": 6}
            ]
        },
        "phase_5": {
            "results": {
                "ci-finance": {
                    "insights": {
                        "market_size": "large",
                        "profitability": "medium"
                    }
                }
            }
        },
        "phase_7": {
            "competitive_landscape": "moderate",
            "positioning": {
                "statement": "Современная клиника с цифровым подходом"
            },
            "recommendations": [
                {"title": "Внедрить онлайн-запись", "description": "Быстрая победа", "priority": "high"}
            ]
        }
    }

    niche = "стоматология"
    client_name = "Тестовая Клиника"

    print(f"📋 Тестовые данные:")
    print(f"   Ниша: {niche}")
    print(f"   Клиент: {client_name}")
    print()

    # Создаём агентов
    agents = {
        "CI Prioritizer": CIPrioritizerAgent("ci-prioritizer"),
        "CI Marketing Strategy": CIMarketingStrategyAgent("ci-marketing-strategy"),
        "CI Offer Generator": CIOfferGeneratorAgent("ci-offer-generator")
    }

    print("🚀 Запуск 3 агентов последовательно...")
    print()

    results = {}
    success_count = 0
    failed_count = 0

    # Phase 9: Prioritizer
    print("=" * 80)
    print("Phase 9: CI Prioritizer")
    print("=" * 80)

    task = Task(
        task_id="test_prioritizer",
        subtask_id="test_prioritizer_sub",
        parent_task_id="test_final",
        action="prioritize",
        description="Test Prioritizer",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    task.payload = {
        "previous_results": mock_previous_results,
        "business_goals": ["увеличить поток клиентов", "улучшить репутацию"]
    }

    result = await agents["CI Prioritizer"].execute_task(task)
    results["phase_9"] = result.result if result.status == "success" else {}

    if result.status == "success":
        print(f"✅ CI Prioritizer: SUCCESS")
        print(f"   Инсайтов собрано: {result.result.get('total_insights', 0)}")
        print(f"   Quick wins: {len(result.result.get('quick_wins', []))}")
        print(f"   Action items: {len(result.result.get('action_plan', []))}")
        success_count += 1
    else:
        print(f"❌ CI Prioritizer: FAILED")
        print(f"   Ошибка: {result.error}")
        failed_count += 1

    print()

    # Phase 10: Marketing Strategy
    print("=" * 80)
    print("Phase 10: CI Marketing Strategy")
    print("=" * 80)

    # Добавляем результаты Phase 9
    mock_previous_results["phase_9"] = results.get("phase_9", {})

    task = Task(
        task_id="test_marketing_strategy",
        subtask_id="test_marketing_strategy_sub",
        parent_task_id="test_final",
        action="create_strategy",
        description="Test Marketing Strategy",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    task.payload = {
        "previous_results": mock_previous_results,
        "budget": 500000,
        "timeline": "3 месяца"
    }

    result = await agents["CI Marketing Strategy"].execute_task(task)
    results["phase_10"] = result.result if result.status == "success" else {}

    if result.status == "success":
        print(f"✅ CI Marketing Strategy: SUCCESS")
        print(f"   Бюджет: {result.result.get('budget', 0):,} руб")
        print(f"   Каналов: {len(result.result.get('channel_strategy', []))}")
        print(f"   Целевых сегментов: {result.result.get('target_audience', {}).get('total_segments', 0)}")
        success_count += 1
    else:
        print(f"❌ CI Marketing Strategy: FAILED")
        print(f"   Ошибка: {result.error}")
        failed_count += 1

    print()

    # Phase 16: Offer Generator
    print("=" * 80)
    print("Phase 16: CI Offer Generator")
    print("=" * 80)

    # Добавляем результаты Phase 10
    mock_previous_results["phase_10"] = results.get("phase_10", {})

    task = Task(
        task_id="test_offer_generator",
        subtask_id="test_offer_generator_sub",
        parent_task_id="test_final",
        action="generate_offer",
        description="Test Offer Generator",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    task.payload = {
        "previous_results": mock_previous_results,
        "client_name": client_name,
        "niche": niche
    }

    result = await agents["CI Offer Generator"].execute_task(task)

    if result.status == "success":
        print(f"✅ CI Offer Generator: SUCCESS")
        offer = result.result.get('offer', {})
        print(f"   Инсайтов: {len(offer.get('key_insights', []))}")
        print(f"   Действий: {len(offer.get('action_plan', []))}")
        print(f"   Markdown сгенерирован: {'markdown' in result.result}")
        success_count += 1
    else:
        print(f"❌ CI Offer Generator: FAILED")
        print(f"   Ошибка: {result.error}")
        failed_count += 1

    print()

    # Итоговая статистика
    print("=" * 80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    print()
    print(f"✅ Успешно: {success_count}/3")
    print(f"❌ Ошибок: {failed_count}/3")
    print()

    if success_count == 3:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Финальные агенты работают корректно.")
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
        "AIM/data/ci-prioritizer.json",
        "AIM/data/ci-marketing-strategy.json",
        "AIM/data/ci-offer.json"
    ]

    files_created = 0
    for file_path in expected_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            files_created += 1
        else:
            print(f"❌ {file_path} - НЕ СОЗДАН")

    # Проверяем markdown
    md_file = f"AIM/data/ci-offer-{client_name.lower().replace(' ', '-')}.md"
    if Path(md_file).exists():
        print(f"✅ {md_file}")
        files_created += 1
    else:
        print(f"❌ {md_file} - НЕ СОЗДАН")

    print()
    print(f"Создано файлов: {files_created}/{len(expected_files) + 1}")
    print()

    return success_count == 3


if __name__ == "__main__":
    success = asyncio.run(test_final_agents())
    sys.exit(0 if success else 1)
