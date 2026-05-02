#!/usr/bin/env python3
"""
Architect Raw Inbox Monitor

Автоматически мониторит obsidian/architect/raw/ и обрабатывает новые файлы.
Запускается как фоновый процесс или через cron.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import yaml
import hashlib


class ArchitectInboxMonitor:
    """Мониторинг и обработка raw inbox для Architect"""

    def __init__(self, raw_dir: Path, wiki_dir: Path, decisions_dir: Path):
        self.raw_dir = raw_dir
        self.wiki_dir = wiki_dir
        self.decisions_dir = decisions_dir
        self.state_file = raw_dir.parent / ".inbox_state.yaml"
        self.processed_files: Dict[str, str] = {}

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
            # Найти второй разделитель ---
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

    def should_read_raw_or_wiki(self, raw_file: Path) -> tuple[str, Path]:
        """
        Определить, читать raw или wiki

        Returns:
            ("raw", path) или ("wiki", path)
        """
        frontmatter = self.parse_frontmatter(raw_file)

        # Проверяем, обработан ли файл
        if frontmatter.get('status') == 'processed':
            # Ищем output wiki
            output = frontmatter.get('output', '')
            if output:
                # Извлекаем имя файла из [[wiki-file]]
                wiki_name = output.strip('[]').strip()
                wiki_path = self.wiki_dir / f"{wiki_name}.md"

                if wiki_path.exists():
                    return ("wiki", wiki_path)

        return ("raw", raw_file)

    def classify_file(self, file_path: Path) -> str:
        """Классифицировать файл по типу"""
        frontmatter = self.parse_frontmatter(file_path)

        # Если тип уже указан
        if 'type' in frontmatter:
            return frontmatter['type']

        # Анализ по содержимому
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()

        # Простая эвристика
        if any(word in content for word in ['стратегия', 'решение', 'подход']):
            return 'strategy'
        elif any(word in content for word in ['вопрос', '?', 'как', 'почему']):
            return 'question'
        elif any(word in content for word in ['идея', 'можно', 'предлагаю']):
            return 'idea'
        elif any(word in content for word in ['код', 'функция', 'класс', 'api']):
            return 'technical'
        else:
            return 'note'

    def generate_analysis_prompt(self, file_path: Path) -> str:
        """Сгенерировать промпт для Claude для анализа файла"""
        file_type = self.classify_file(file_path)

        prompts = {
            'strategy': f"""
Проанализируй стратегический документ: {file_path.name}

1. Извлеки ключевые стратегические инсайты
2. Определи, требуется ли решение от Architect
3. Создай структурированную заметку в wiki/
4. Если нужно решение - создай в decisions/
5. Обнови метаданные в raw/ файле (status: processed)
6. Залогируй операцию в wiki/log.md
""",
            'question': f"""
Проанализируй вопрос: {file_path.name}

1. Определи тип вопроса (стратегический/тактический/технический)
2. Если стратегический - передай Architect
3. Если тактический - передай Operator
4. Если технический - ответь сам или делегируй агенту
5. Создай заметку с ответом в wiki/
6. Обнови метаданные в raw/ (status: processed)
""",
            'idea': f"""
Проанализируй идею: {file_path.name}

1. Оцени потенциал идеи (high/medium/low)
2. Определи связи с существующими заметками
3. Если идея стратегическая - передай Architect
4. Создай заметку в wiki/ с оценкой
5. Обнови метаданные в raw/ (status: processed)
""",
            'technical': f"""
Проанализируй технический документ: {file_path.name}

1. Извлеки технические инсайты
2. Определи применимость для AIM Agency
3. Создай техническую заметку в wiki/
4. Если нужна имплементация - создай задачу
5. Обнови метаданные в raw/ (status: processed)
""",
            'note': f"""
Проанализируй заметку: {file_path.name}

1. Извлеки ключевую информацию
2. Классифицируй по темам
3. Создай структурированную заметку в wiki/
4. Обнови метаданные в raw/ (status: processed)
"""
        }

        return prompts.get(file_type, prompts['note'])

    async def process_file(self, file_path: Path) -> None:
        """Обработать один файл"""
        print(f"\n🔍 Обрабатываю: {file_path.name}")

        # Проверяем, не обработан ли уже
        if self.is_processed(file_path):
            print(f"✅ Уже обработан: {file_path.name}")
            self.processed_files[file_path.name] = self.get_file_hash(file_path)
            return

        # Умная проверка: читать raw или wiki?
        source_type, source_path = self.should_read_raw_or_wiki(file_path)

        if source_type == "wiki":
            print(f"📚 Файл уже обработан, читаю wiki: {source_path.name}")
            print(f"💡 Используй wiki-документ для анализа, не исходный raw-файл")
        else:
            print(f"📋 Новый файл, анализирую raw")

        # Классифицируем
        file_type = self.classify_file(file_path)
        print(f"📋 Тип: {file_type}")

        # Генерируем промпт для анализа
        prompt = self.generate_analysis_prompt(file_path)

        print(f"\n💡 Промпт для Claude:\n{prompt}")
        print(f"\n⏳ Жду обработки от Claude...")

        # Здесь Claude должен обработать файл
        # В реальности это будет вызов через API или интерактивно

        # Обновляем состояние
        self.processed_files[file_path.name] = self.get_file_hash(file_path)

    async def monitor_loop(self, interval: int = 60) -> None:
        """Основной цикл мониторинга"""
        print(f"🚀 Запущен мониторинг {self.raw_dir}")
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
        print(f"🔍 Однократная проверка {self.raw_dir}")

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

    parser = argparse.ArgumentParser(description='Architect Raw Inbox Monitor')
    parser.add_argument('--once', action='store_true', help='Обработать один раз и выйти')
    parser.add_argument('--interval', type=int, default=60, help='Интервал проверки в секундах')
    args = parser.parse_args()

    # Пути
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / "obsidian" / "architect" / "raw"
    wiki_dir = base_dir / "obsidian" / "architect" / "wiki"
    decisions_dir = base_dir / "obsidian" / "architect" / "decisions"

    # Создаём монитор
    monitor = ArchitectInboxMonitor(raw_dir, wiki_dir, decisions_dir)

    if args.once:
        await monitor.process_once()
    else:
        await monitor.monitor_loop(interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
