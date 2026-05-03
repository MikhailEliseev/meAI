#!/usr/bin/env python3
"""
Subagent Distributor

Распределяет знания от Magisters к Subagents.
Magister создаёт адаптированные wiki-документы, которые затем распределяются субагентам.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import yaml


class SubagentDistributor:
    """Распределяет знания от Magister к его субагентам"""

    def __init__(self, magister_vault: Path, magister_name: str):
        self.magister_vault = magister_vault
        self.magister_name = magister_name
        self.wiki_dir = magister_vault / "wiki"
        self.subagents_dir = magister_vault / "subagents"

        # Загружаем список субагентов
        self.subagents = self._load_subagents()

    def _load_subagents(self) -> Dict[str, Dict[str, Any]]:
        """Загрузить список субагентов из директории"""
        subagents = {}

        if not self.subagents_dir.exists():
            return subagents

        for subagent_dir in self.subagents_dir.iterdir():
            if not subagent_dir.is_dir():
                continue

            schema_file = subagent_dir / "SCHEMA.md"
            if not schema_file.exists():
                continue

            # Парсим SCHEMA
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if content.startswith('---'):
                try:
                    end_idx = content.find('---', 3)
                    if end_idx != -1:
                        frontmatter_text = content[3:end_idx].strip()
                        schema = yaml.safe_load(frontmatter_text) or {}

                        subagents[subagent_dir.name] = {
                            'name': schema.get('name', subagent_dir.name),
                            'specialization': schema.get('specialization', ''),
                            'path': subagent_dir,
                            'schema': schema
                        }
                except Exception as e:
                    print(f"⚠️  Ошибка загрузки субагента {subagent_dir.name}: {e}")

        return subagents

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

    def determine_relevant_subagents(self, wiki_doc: Path) -> List[str]:
        """
        Определить, каким субагентам релевантно знание

        Анализирует:
        - Теги в frontmatter
        - Поле for_subagents (если есть)
        - Категорию документа
        """
        frontmatter = self.parse_frontmatter(wiki_doc)

        # 1. Проверяем явное указание субагентов
        if 'for_subagents' in frontmatter:
            return frontmatter['for_subagents']

        # 2. Анализируем по категории и тегам
        relevant = []
        category = frontmatter.get('category', '')
        tags = frontmatter.get('tags', [])

        # Маппинг категорий/тегов на субагентов
        mappings = {
            'positions': ['positions', 'ranking', 'monitoring', 'serp'],
            'content': ['content', 'copywriting', 'keywords', 'optimization'],
            'links': ['links', 'backlinks', 'linkbuilding', 'outreach'],
            'technical': ['technical', 'performance', 'crawl', 'schema']
        }

        # Проверяем категорию
        for subagent, keywords in mappings.items():
            if category in keywords:
                relevant.append(subagent)

        # Проверяем теги
        for subagent, keywords in mappings.items():
            for tag in tags:
                if tag.lower() in keywords:
                    if subagent not in relevant:
                        relevant.append(subagent)

        # Если не нашли релевантных - отправляем всем
        if not relevant:
            relevant = list(self.subagents.keys())

        return relevant

    async def distribute_to_subagent(self, subagent_name: str, wiki_doc: Path) -> bool:
        """Отправить знание субагенту"""

        if subagent_name not in self.subagents:
            print(f"⚠️  Субагент не найден: {subagent_name}")
            return False

        try:
            subagent = self.subagents[subagent_name]
            subagent_raw = subagent['path'] / "raw"

            # Читаем wiki-документ
            with open(wiki_doc, 'r', encoding='utf-8') as f:
                wiki_content = f.read()

            # Создаём файл в raw/ субагента
            timestamp = datetime.now().strftime('%Y%m%d-%H%M')
            raw_filename = f"{timestamp}-{wiki_doc.stem}.md"
            raw_file = subagent_raw / raw_filename

            # Frontmatter для субагента
            frontmatter = self.parse_frontmatter(wiki_doc)
            subagent_frontmatter = f"""---
title: "{frontmatter.get('title', wiki_doc.stem)}"
source: "magister-wiki"
source_file: "{wiki_doc.name}"
magister: "{self.magister_name}"
received_at: "{datetime.now().isoformat()}"
status: raw
tags: {frontmatter.get('tags', [])}
---

# Knowledge from {self.magister_name.upper()}

**Source:** [[{wiki_doc.stem}]]
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**For:** {subagent['name']}

---

{wiki_content}
"""

            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(subagent_frontmatter)

            print(f"   📄 Создан файл для {subagent_name}: {raw_filename}")

            # Логируем в wiki/log.md субагента
            await self._log_to_subagent(subagent, wiki_doc)

            return True

        except Exception as e:
            print(f"   ❌ Ошибка отправки {subagent_name}: {e}")
            return False

    async def _log_to_subagent(self, subagent: Dict[str, Any], wiki_doc: Path):
        """Залогировать получение знания в лог субагента"""

        log_file = subagent['path'] / "wiki" / "log.md"

        log_entry = f"""
## [{datetime.now().strftime('%Y-%m-%d %H:%M')}] receive | {wiki_doc.name}

- Source: {self.magister_name} wiki
- File: {wiki_doc.name}
- Status: Received, ready for processing
"""

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    async def distribute_wiki_document(self, wiki_doc: Path) -> List[str]:
        """
        Распределить wiki-документ релевантным субагентам

        Returns:
            List субагентов, которым отправлено знание
        """
        print(f"\n📚 Распределяю знание: {wiki_doc.name}")

        # Определяем релевантных субагентов
        relevant_subagents = self.determine_relevant_subagents(wiki_doc)
        print(f"   👥 Релевантные субагенты: {relevant_subagents}")

        # Отправляем знание субагентам
        distributed = []
        for subagent_name in relevant_subagents:
            success = await self.distribute_to_subagent(subagent_name, wiki_doc)
            if success:
                distributed.append(subagent_name)

        print(f"   ✅ Распределено {len(distributed)} субагентам")

        return distributed


async def main():
    """Тестирование SubagentDistributor"""
    import argparse

    parser = argparse.ArgumentParser(description='Subagent Distributor')
    parser.add_argument('magister', help='Имя магистра (seo-magister, etc.)')
    parser.add_argument('wiki_doc', help='Путь к wiki-документу для распределения')
    args = parser.parse_args()

    # Пути
    base_dir = Path(__file__).parent.parent
    magister_vault = base_dir / "obsidian" / "magisters" / args.magister

    if not magister_vault.exists():
        print(f"❌ Магистр не найден: {args.magister}")
        return

    wiki_doc = Path(args.wiki_doc)
    if not wiki_doc.exists():
        print(f"❌ Wiki-документ не найден: {args.wiki_doc}")
        return

    # Создаём дистрибьютор
    distributor = SubagentDistributor(magister_vault, args.magister)

    print(f"\n🎯 Subagent Distributor")
    print(f"   Магистр: {args.magister}")
    print(f"   Субагентов: {len(distributor.subagents)}")
    for name, info in distributor.subagents.items():
        print(f"   - {name}: {info['specialization']}")

    # Распределяем знание
    await distributor.distribute_wiki_document(wiki_doc)


if __name__ == "__main__":
    asyncio.run(main())
