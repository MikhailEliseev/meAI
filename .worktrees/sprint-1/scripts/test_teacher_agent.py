#!/usr/bin/env python3
"""
Test Teacher Agent

Тестирование Teacher Agent без запуска полного Event Bus.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.teacher_agent import KnowledgeDistributor, MagisterManager, TeacherAgent
from src.meai.events.event_bus import EventBus, Event
from src.meai.memory.obsidian import ObsidianVault


async def test_knowledge_distributor():
    """Тест KnowledgeDistributor"""

    print("\n" + "="*60)
    print("TEST 1: KnowledgeDistributor")
    print("="*60)

    # Пути
    base_dir = Path(__file__).parent.parent
    architect_wiki = base_dir / "obsidian" / "architect" / "wiki"
    teacher_vault_path = base_dir / "obsidian" / "teacher"

    # Event Bus
    event_bus = EventBus()

    # Teacher vault
    teacher_vault = ObsidianVault(teacher_vault_path)

    # KnowledgeDistributor
    distributor = KnowledgeDistributor(architect_wiki, teacher_vault, event_bus)

    # Тестовый wiki-документ (BlackHat SEO)
    test_doc = architect_wiki / "sources" / "2026-05-02-blackhat-seo.md"

    if not test_doc.exists():
        print(f"❌ Тестовый документ не найден: {test_doc}")
        return False

    print(f"\n📄 Тестовый документ: {test_doc.name}")

    # Распределяем знание
    magisters = await distributor.distribute_new_knowledge(test_doc)

    if magisters:
        print(f"\n✅ Знание распределено {len(magisters)} магистрам: {magisters}")
        return True
    else:
        print(f"\n❌ Знание не распределено")
        return False


async def test_magister_manager():
    """Тест MagisterManager"""

    print("\n" + "="*60)
    print("TEST 2: MagisterManager")
    print("="*60)

    # Пути
    base_dir = Path(__file__).parent.parent
    magisters_dir = base_dir / "obsidian" / "magisters"

    # Event Bus
    event_bus = EventBus()

    # MagisterManager
    manager = MagisterManager(magisters_dir, event_bus)

    print(f"\n📊 Загружено магистров: {len(manager.magisters)}")

    for name, magister in manager.magisters.items():
        print(f"   - {name}: {magister['status']}")

    if len(manager.magisters) > 0:
        print(f"\n✅ MagisterManager работает")
        return True
    else:
        print(f"\n❌ Магистры не загружены")
        return False


async def test_feedback_processing():
    """Тест обработки feedback"""

    print("\n" + "="*60)
    print("TEST 3: Feedback Processing")
    print("="*60)

    # Пути
    base_dir = Path(__file__).parent.parent
    magisters_dir = base_dir / "obsidian" / "magisters"

    # Event Bus
    event_bus = EventBus()

    # MagisterManager
    manager = MagisterManager(magisters_dir, event_bus)

    # Тестовый feedback
    test_feedback = {
        "type": "missing_knowledge",
        "topic": "Google алгоритмы 2026",
        "urgency": "high"
    }

    print(f"\n📬 Тестовый feedback:")
    print(f"   Тип: {test_feedback['type']}")
    print(f"   Тема: {test_feedback['topic']}")
    print(f"   Срочность: {test_feedback['urgency']}")

    # Обрабатываем feedback
    await manager.process_magister_feedback("seo-magister", test_feedback)

    print(f"\n✅ Feedback обработан")
    return True


async def test_teacher_agent_init():
    """Тест инициализации Teacher Agent"""

    print("\n" + "="*60)
    print("TEST 4: Teacher Agent Initialization")
    print("="*60)

    # Пути
    base_dir = Path(__file__).parent.parent
    teacher_vault_path = base_dir / "obsidian" / "teacher"
    magisters_dir = base_dir / "obsidian" / "magisters"
    architect_wiki_path = base_dir / "obsidian" / "architect" / "wiki"

    # Event Bus
    event_bus = EventBus()

    # Teacher Agent
    teacher = TeacherAgent(
        teacher_vault_path,
        magisters_dir,
        architect_wiki_path,
        event_bus
    )

    print(f"\n✅ Teacher Agent инициализирован")
    print(f"   - KnowledgeDistributor: готов")
    print(f"   - MagisterManager: готов")
    print(f"   - Event Bus: готов")

    return True


async def run_all_tests():
    """Запустить все тесты"""

    print("\n" + "="*60)
    print("🧪 TEACHER AGENT - TEST SUITE")
    print("="*60)

    results = []

    # Test 1: KnowledgeDistributor
    try:
        result = await test_knowledge_distributor()
        results.append(("KnowledgeDistributor", result))
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        results.append(("KnowledgeDistributor", False))

    # Test 2: MagisterManager
    try:
        result = await test_magister_manager()
        results.append(("MagisterManager", result))
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        results.append(("MagisterManager", False))

    # Test 3: Feedback Processing
    try:
        result = await test_feedback_processing()
        results.append(("Feedback Processing", result))
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        results.append(("Feedback Processing", False))

    # Test 4: Teacher Agent Init
    try:
        result = await test_teacher_agent_init()
        results.append(("Teacher Agent Init", result))
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        results.append(("Teacher Agent Init", False))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "="*60)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*60)

    if failed == 0:
        print("\n🎉 Все тесты пройдены!")
    else:
        print(f"\n⚠️  {failed} тест(ов) не прошли")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
