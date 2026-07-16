#!/usr/bin/env python3
"""
Subagent Monitor - Universal monitor for all subagents

Мониторит raw/ каждого субагента и обрабатывает знания от Magister.
Создаёт специализированные wiki-документы для конкретных задач субагента.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import yaml
import hashlib

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))


class SubagentMonitor:
    """Универсальный монитор для субагентов"""

    def __init__(self, magister_name: str, subagent_name: str, subagent_path: Path):
        self.magister_name = magister_name
        self.subagent_name = subagent_name
        self.subagent_path = subagent_path
        self.raw_dir = subagent_path / "raw"
        self.wiki_dir = subagent_path / "wiki"
        self.state_file = subagent_path / f".{subagent_name}_state.yaml"
        self.processed_files: Dict[str, str] = {}

        # Загружаем SCHEMA для понимания специализации
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Загрузить SCHEMA.md субагента"""
        schema_file = self.subagent_path / "SCHEMA.md"

        if not schema_file.exists():
            return {}

        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Парсим frontmatter
        if content.startswith('---'):
            try:
                end_idx = content.find('---', 3)
                if end_idx != -1:
                    frontmatter_text = content[3:end_idx].strip()
                    return yaml.safe_load(frontmatter_text) or {}
            except Exception as e:
                print(f"⚠️  Ошибка парсинга SCHEMA: {e}")

        return {}

    def load_state(self) -> None:
        """Загрузить состояние обработанных файлов"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.processed_files = data.get('processed', {})

    def save_state(self) -> None:
        """Сохранить состояние обработанных файлов"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            yaml.dump({
                'processed': self.processed_files,
                'last_check': datetime.now().isoformat()
            }, f)

    def get_file_hash(self, file_path: Path) -> str:
        """Получить хеш файла для отслеживания изменений"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def get_new_files(self) -> List[Path]:
        """Найти новые или изменённые файлы в raw/"""
        new_files = []

        if not self.raw_dir.exists():
            return new_files

        for file_path in self.raw_dir.glob("*.md"):
            file_hash = self.get_file_hash(file_path)
            file_name = file_path.name

            # Проверяем, новый файл или изменённый
            if file_name not in self.processed_files:
                new_files.append(file_path)
                print(f"📥 Новый файл: {file_name}")
            elif self.processed_files[file_name] != file_hash:
                new_files.append(file_path)
                print(f"📝 Изменённый файл: {file_name}")

        return new_files

    def parse_frontmatter(self, file_path: Path) -> Dict[str, Any]:
        """Извлечь frontmatter из markdown файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return {}

        try:
            end_idx = content.find('---', 3)
            if end_idx == -1:
                return {}

            frontmatter_text = content[3:end_idx].strip()
            return yaml.safe_load(frontmatter_text) or {}
        except Exception as e:
            print(f"⚠️  Ошибка парсинга frontmatter в {file_path.name}: {e}")
            return {}

    def is_processed(self, file_path: Path) -> bool:
        """Проверить, обработан ли файл"""
        frontmatter = self.parse_frontmatter(file_path)
        return frontmatter.get('status') == 'processed'

    def generate_processing_prompt(self, file_path: Path) -> str:
        """
        Сгенерировать промпт для обработки знания субагентом

        Субагент должен:
        1. Извлечь релевантную информацию для своей специализации
        2. Создать actionable инструкции
        3. Определить конкретные задачи
        4. Указать инструменты и метрики
        """
        frontmatter = self.parse_frontmatter(file_path)
        source_file = frontmatter.get('source_file', 'unknown')

        subagent_role = self.schema.get('role', self.subagent_name)
        specialization = self.schema.get('specialization', '')

        prompt = f"""
Ты — {subagent_role}.

Твоя специализация: {specialization}

Получено новое знание от {self.magister_name}: {source_file}

Твоя задача — извлечь релевантную информацию для ТВОЕЙ специализации и создать actionable план.

Что нужно сделать:

1. **Извлеки релевантную информацию**
   - Что из этого знания относится к твоей специализации?
   - Какие конкретные задачи ты можешь выполнить?
   - Какие инструменты использовать?

2. **Создай actionable план**
   - Конкретные шаги (что делать?)
   - Инструменты (чем делать?)
   - Метрики (как измерять?)
   - Сроки (когда делать?)

3. **Определи приоритеты**
   - Что сделать в первую очередь?
   - Что можно автоматизировать?
   - Что требует ручной работы?

4. **Создай чеклист**
   - [ ] Задача 1
   - [ ] Задача 2
   - [ ] Задача 3

Создай wiki-документ в соответствующей категории:
- workflows/ - для процессов работы
- strategies/ - для стратегий
- technologies/ - для инструментов

Обнови метаданные в raw/ файле:
- status: processed
- output: [[wiki-doc-name]]
- processed_at: timestamp

Залогируй операцию в wiki/log.md
"""

        return prompt

    async def process_file(self, file_path: Path) -> None:
        """Обработать один файл"""
        print(f"\n🔍 Обрабатываю: {file_path.name}")

        # Проверяем, не обработан ли уже
        if self.is_processed(file_path):
            print(f"✅ Уже обработан: {file_path.name}")
            self.processed_files[file_path.name] = self.get_file_hash(file_path)
            return

        # Генерируем промпт для обработки
        prompt = self.generate_processing_prompt(file_path)

        print(f"\n💡 Промпт для {self.subagent_name}:\n{prompt}")
        print(f"\n⏳ Жду обработки от Claude...")

        # TODO: Здесь должна быть автоматическая обработка через Claude API
        # Пока что Monitor только обнаруживает и генерирует промпт
        # Фактическая обработка (создание wiki) делается вручную через Claude Code

        print(f"\n📋 Файл готов к обработке:")
        print(f"   Субагент: {self.subagent_name}")
        print(f"   Специализация: {self.schema.get('specialization', 'N/A')}")
        print(f"   Путь: {file_path}")
        print(f"   Следующий шаг: создать wiki-документ с actionable планом")

        # Обновляем состояние
        self.processed_files[file_path.name] = self.get_file_hash(file_path)

    async def monitor_loop(self, interval: int = 60) -> None:
        """Основной цикл мониторинга"""
        print(f"🚀 Запущен мониторинг {self.subagent_name}")
        print(f"📂 Raw: {self.raw_dir}")
        print(f"⏱️  Интервал проверки: {interval} секунд")

        while True:
            try:
                # Загружаем состояние
                self.load_state()

                # Ищем новые файлы
                new_files = self.get_new_files()

                if new_files:
                    print(f"\n📦 Найдено новых файлов: {len(new_files)}")

                    for file_path in new_files:
                        await self.process_file(file_path)

                    # Сохраняем состояние
                    self.save_state()
                    print(f"\n💾 Состояние сохранено")
                else:
                    print(f"✨ Нет новых файлов ({datetime.now().strftime('%H:%M:%S')})")

                # Ждём следующей проверки
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                print("\n\n👋 Остановка мониторинга...")
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
                await asyncio.sleep(interval)

    async def process_once(self) -> None:
        """Обработать все файлы один раз (без цикла)"""
        print(f"🔍 Однократная проверка {self.subagent_name}")

        self.load_state()
        new_files = self.get_new_files()

        if not new_files:
            print("✨ Нет новых файлов для обработки")
            return

        print(f"\n📦 Найдено новых файлов: {len(new_files)}")

        for file_path in new_files:
            await self.process_file(file_path)

        self.save_state()
        print(f"\n💾 Состояние сохранено")


async def main():
    """Точка входа"""
    import argparse

    parser = argparse.ArgumentParser(description='Subagent Monitor')
    parser.add_argument('magister', help='Имя магистра (seo-magister, etc.)')
    parser.add_argument('subagent', help='Имя субагента (positions, content, etc.)')
    parser.add_argument('--once', action='store_true', help='Обработать один раз и выйти')
    parser.add_argument('--interval', type=int, default=60, help='Интервал проверки в секундах')
    args = parser.parse_args()

    # Пути
    base_dir = Path(__file__).parent.parent
    subagent_path = base_dir / "obsidian" / "magisters" / args.magister / "subagents" / args.subagent

    if not subagent_path.exists():
        print(f"❌ Субагент не найден: {args.magister}/{args.subagent}")
        print(f"   Путь: {subagent_path}")
        return

    # Создаём монитор
    monitor = SubagentMonitor(args.magister, args.subagent, subagent_path)

    if args.once:
        await monitor.process_once()
    else:
        await monitor.monitor_loop(interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
