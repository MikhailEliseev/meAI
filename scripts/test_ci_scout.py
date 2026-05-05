"""
Тест CI Scout Agent

Проверяет работу агента поиска и кластеризации конкурентов.
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавить путь к проекту
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.meai.agents.base_agent import Task, TaskStatus

# Импорт CI Scout
ci_scout_path = os.path.join(project_root, 'AIM/src/aim/subagents/competitive_intel/agents/ci_scout.py')
import importlib.util
spec = importlib.util.spec_from_file_location("ci_scout", ci_scout_path)
ci_scout_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_scout_module)
CIScoutAgent = ci_scout_module.CIScoutAgent


async def test_ci_scout():
    """Тест CI Scout Agent."""
    print("=" * 60)
    print("CI Scout Agent Test")
    print("=" * 60)

    # Создать CI Scout Agent (без Event Bus, он создаётся внутри)
    scout = CIScoutAgent(
        agent_id="ci-scout-test",
        database_url="sqlite+aiosqlite:///./data/meai.db"
    )

    # Создать тестовую задачу (используем правильную структуру Task)
    task = Task(
        task_id="test_task_001",
        subtask_id="subtask_001",
        parent_task_id="parent_001",
        action="competitor_discovery",
        description="Найти конкурентов в стоматологии Москвы",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now()
    )

    # Добавим payload как атрибут (для совместимости)
    task.payload = {
        "niche": "стоматология",
        "geo": "Москва",
        "target_audience": "взрослые 25-55",
        "price_segment": "mid"
    }

    print("\n📋 Задача:")
    print(f"  Ниша: {task.payload['niche']}")
    print(f"  Город: {task.payload['geo']}")
    print(f"  ЦА: {task.payload['target_audience']}")
    print(f"  Сегмент: {task.payload['price_segment']}")

    # Выполнить задачу
    print("\n🔄 Выполнение...")
    result = await scout.execute_task(task)

    # Проверить результат
    print("\n✅ Результат:")
    print(f"  Статус: {result.status}")

    if result.status == "success":
        data = result.result
        print(f"  Найдено конкурентов: {data['total_found']}")
        print(f"  Выбрано для анализа: {data['top_selected']}")

        print("\n📊 Кластеры:")
        for cluster, names in data['clusters'].items():
            print(f"  {cluster}: {len(names)} конкурентов")

        print("\n🎯 TOP для анализа:")
        for i, comp in enumerate(data['top_for_analysis'], 1):
            print(f"  {i}. {comp['name']} ({comp['cluster']})")
            print(f"     Причина: {comp['reason']}")

        print("\n💡 Инсайты:")
        insights = data['insights']
        print(f"  Всего игроков: {insights['total_players']}")
        print(f"  Фрагментация: {insights['fragmentation']}")
        print(f"  Доминирующий кластер: {insights['dominant_positioning']}")

        print("\n📁 Результаты сохранены в: AIM/data/ci-competitors.json")

        return True
    else:
        print(f"  ❌ Ошибка: {result.result.get('error')}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ci_scout())

    print("\n" + "=" * 60)
    if success:
        print("✅ Тест пройден!")
    else:
        print("❌ Тест провален!")
    print("=" * 60)

    sys.exit(0 if success else 1)
