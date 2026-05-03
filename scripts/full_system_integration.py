#!/usr/bin/env python3
"""
Full System Integration

Запускает полную систему:
- Architect Monitor (raw → wiki)
- Teacher Agent (wiki → magisters)
- All Magister Monitors (raw → wiki)

Полный цикл обучения от Architect до Magisters.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.meai.events.event_bus import EventBus
from scripts.architect_inbox_monitor import ArchitectInboxMonitor
from scripts.teacher_agent import TeacherAgent
from scripts.magister_monitor import MagisterMonitor


async def main():
    """Запуск полной системы"""

    print("=" * 70)
    print("🚀 Full System Integration")
    print("=" * 70)
    print("\nАрхитектура:")
    print("  Architect (raw/) → Monitor → Architect (wiki/)")
    print("       ↓")
    print("  Teacher Agent (EventBus)")
    print("       ↓")
    print("  Magisters (raw/) → Monitors → Magisters (wiki/)")
    print("=" * 70)

    # Пути
    base_dir = Path(__file__).parent.parent

    # Architect
    architect_raw = base_dir / "obsidian" / "architect" / "raw"
    architect_wiki = base_dir / "obsidian" / "architect" / "wiki"
    architect_decisions = base_dir / "obsidian" / "architect" / "decisions"

    # Teacher
    teacher_vault = base_dir / "obsidian" / "teacher"
    magisters_dir = base_dir / "obsidian" / "magisters"

    # Event Bus
    event_bus = EventBus()
    await event_bus.initialize()
    print("\n✅ Event Bus инициализирован")

    # Создаём Teacher Agent
    teacher = TeacherAgent(
        teacher_vault,
        magisters_dir,
        architect_wiki,
        event_bus
    )
    await teacher.start()
    print("✅ Teacher Agent запущен")

    # Создаём Architect Monitor
    architect_monitor = ArchitectInboxMonitor(
        architect_raw,
        architect_wiki,
        architect_decisions,
        use_gatekeeper=True,
        event_bus=event_bus
    )
    print("✅ Architect Monitor создан")

    # Создаём Magister Monitors
    magisters = ["seo-magister", "content-magister", "ads-magister", "ai-magister"]
    magister_monitors = {}

    for magister_name in magisters:
        magister_vault = magisters_dir / magister_name
        if magister_vault.exists():
            monitor = MagisterMonitor(magister_name, magister_vault, event_bus)
            magister_monitors[magister_name] = monitor
            print(f"✅ {magister_name} Monitor создан")

    print("\n" + "=" * 70)
    print("🎯 Система готова к работе!")
    print("=" * 70)
    print("\nПолный цикл:")
    print("  1. Architect Monitor обнаруживает новые файлы")
    print("  2. Gatekeeper проверяет качество")
    print("  3. Создаётся wiki в Architect")
    print("  4. Teacher получает событие через EventBus")
    print("  5. Teacher распределяет знания магистрам")
    print("  6. Magister Monitors обрабатывают raw → wiki")
    print("  7. Знания адаптируются 'на пальцах' для субагентов")
    print("\n" + "=" * 70)

    # Однократная проверка всех компонентов
    print("\n🔍 Запускаю однократную проверку всех компонентов...\n")

    # 1. Architect Monitor
    print("\n📋 Architect Monitor:")
    await architect_monitor.process_once()

    # 2. Magister Monitors
    for magister_name, monitor in magister_monitors.items():
        print(f"\n📋 {magister_name} Monitor:")
        await monitor.process_once()

    print("\n" + "=" * 70)
    print("✅ Полная проверка завершена")
    print("=" * 70)

    # Статистика
    print("\n📊 Статистика системы:")
    print(f"   Магистров: {len(teacher.magister_manager.magisters)}")
    for name, magister in teacher.magister_manager.magisters.items():
        print(f"   - {name}: {magister['status']}")

    # Закрываем Event Bus
    await event_bus.close()


if __name__ == "__main__":
    asyncio.run(main())
