#!/usr/bin/env python3
"""
Integration: Monitor + Teacher Agent

Запускает Monitor и Teacher Agent вместе для автоматического распределения знаний.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.teacher_agent import TeacherAgent
from scripts.architect_inbox_monitor import ArchitectInboxMonitor
from src.meai.events.event_bus import EventBus


async def main():
    """Точка входа"""

    print("\n" + "="*60)
    print("🚀 Monitor + Teacher Agent Integration")
    print("="*60)

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

    print("\n✅ Teacher Agent запущен")

    # Создаём Monitor с EventBus
    monitor = ArchitectInboxMonitor(
        architect_raw,
        architect_wiki,
        architect_decisions,
        use_gatekeeper=True,
        event_bus=event_bus
    )

    print("\n✅ Monitor запущен")

    # Интеграция: Monitor → Teacher
    print("\n🔗 Интеграция Monitor → Teacher:")
    print("   1. Monitor обнаруживает новые файлы в raw/")
    print("   2. Gatekeeper проверяет качество")
    print("   3. Если файл обработан → wiki создан")
    print("   4. Monitor уведомляет Teacher о новом wiki")
    print("   5. Teacher распределяет знания магистрам")

    print("\n" + "="*60)
    print("🎯 Система готова к работе!")
    print("="*60)

    # Однократная проверка
    print("\n🔍 Проверяю новые файлы...")
    await monitor.process_once()

    print("\n✅ Проверка завершена")

    # Закрываем Event Bus
    await event_bus.close()


if __name__ == "__main__":
    asyncio.run(main())
