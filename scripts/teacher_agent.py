#!/usr/bin/env python3
"""
Teacher Agent - Hierarchical Learning System

Центр обучающей системы агентства.
Распределяет знания магистрам, обрабатывает обратную связь, улучшает стратегию обучения.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import yaml

from src.meai.events.event_bus import EventBus, Event
from src.meai.memory.obsidian import ObsidianVault


class KnowledgeDistributor:
    """Распределяет знания из Architect wiki магистрам"""

    def __init__(self, architect_wiki: Path, teacher_vault: ObsidianVault, event_bus: EventBus):
        self.architect_wiki = architect_wiki
        self.teacher_vault = teacher_vault
        self.event_bus = event_bus

        # Маппинг тегов на магистров
        self.tag_to_magister = {
            "seo": "seo-magister",
            "search": "seo-magister",
            "ranking": "seo-magister",
            "content": "content-magister",
            "copywriting": "content-magister",
            "articles": "content-magister",
            "ads": "ads-magister",
            "advertising": "ads-magister",
            "ppc": "ads-magister",
            "ai": "ai-magister",
            "automation": "ai-magister",
            "agents": "ai-magister"
        }

    async def distribute_new_knowledge(self, wiki_doc: Path) -> List[str]:
        """
        Определить, каким магистрам релевантно новое знание

        Args:
            wiki_doc: Путь к wiki-документу из Architect

        Returns:
            List магистров, которым передано знание
        """
        # 1. Читаем wiki-документ
        frontmatter = self._parse_frontmatter(wiki_doc)
        tags = frontmatter.get("tags", [])

        print(f"\n📚 Новое знание: {wiki_doc.name}")
        print(f"   Теги: {tags}")

        # 2. Определяем релевантных магистров
        relevant_magisters = set()

        for tag in tags:
            if tag in self.tag_to_magister:
                relevant_magisters.add(self.tag_to_magister[tag])

        if not relevant_magisters:
            print(f"   ⚠️  Нет релевантных магистров для тегов: {tags}")
            return []

        print(f"   👥 Релевантные магистры: {relevant_magisters}")

        # 3. Отправляем знание магистрам
        distributed = []
        for magister in relevant_magisters:
            success = await self.send_knowledge_to_magister(magister, wiki_doc)
            if success:
                distributed.append(magister)

        # 4. Логируем
        await self._log_distribution(wiki_doc, distributed)

        return distributed

    async def send_knowledge_to_magister(self, magister: str, wiki_doc: Path) -> bool:
        """Отправить знание магистру"""

        try:
            # Создаём событие для магистра
            event = Event(
                event_type="knowledge_update",
                payload={
                    "magister": magister,
                    "source": str(wiki_doc),
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Публикуем через Event Bus
            await self.event_bus.publish(event)

            print(f"   ✅ Отправлено {magister}")
            return True

        except Exception as e:
            print(f"   ❌ Ошибка отправки {magister}: {e}")
            return False

    def _parse_frontmatter(self, file_path: Path) -> Dict[str, Any]:
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

    async def _log_distribution(self, wiki_doc: Path, magisters: List[str]):
        """Залогировать распределение знаний"""

        log_entry = f"""
## [{datetime.now().strftime('%Y-%m-%d %H:%M')}] distribute | {wiki_doc.name}

- Source: {wiki_doc}
- Magisters: {', '.join(magisters)}
- Status: Distributed
"""

        log_file = self.teacher_vault.vault_path / "wiki" / "log.md"

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)


class MagisterManager:
    """Управляет магистрами и их базами знаний"""

    def __init__(self, magisters_dir: Path, event_bus: EventBus):
        self.magisters_dir = magisters_dir
        self.event_bus = event_bus
        self.magisters: Dict[str, Dict] = {}

        self._load_magisters()

    def _load_magisters(self):
        """Загрузить всех магистров"""

        for magister_dir in self.magisters_dir.iterdir():
            if magister_dir.is_dir():
                config_file = magister_dir / "SCHEMA.md"
                if config_file.exists():
                    self.magisters[magister_dir.name] = {
                        "name": magister_dir.name,
                        "path": magister_dir,
                        "status": "active"
                    }

        print(f"\n👥 Загружено магистров: {len(self.magisters)}")
        for name in self.magisters:
            print(f"   - {name}")

    async def create_magister(self, name: str, domain: str, description: str) -> Dict:
        """Создать нового магистра"""

        magister_dir = self.magisters_dir / name
        magister_dir.mkdir(exist_ok=True)

        # Создаём структуру
        (magister_dir / "raw").mkdir(exist_ok=True)
        (magister_dir / "wiki").mkdir(exist_ok=True)
        (magister_dir / "subagents").mkdir(exist_ok=True)

        # Создаём файлы
        (magister_dir / "wiki" / "index.md").touch()
        (magister_dir / "wiki" / "log.md").touch()
        (magister_dir / "wiki" / "knowledge-base.md").touch()
        (magister_dir / "wiki" / "sources.md").touch()
        (magister_dir / "wiki" / "improvements.md").touch()
        (magister_dir / "wiki" / "problems.md").touch()

        magister = {
            "name": name,
            "domain": domain,
            "description": description,
            "path": magister_dir,
            "status": "active",
            "created": datetime.now().isoformat()
        }

        self.magisters[name] = magister

        print(f"\n✅ Создан магистр: {name} ({domain})")

        return magister

    async def update_magister_knowledge(self, magister_name: str, knowledge: Dict):
        """Обновить базу знаний магистра"""

        if magister_name not in self.magisters:
            print(f"⚠️  Магистр не найден: {magister_name}")
            return

        magister = self.magisters[magister_name]
        knowledge_file = magister["path"] / "wiki" / "knowledge-base.md"

        # Добавляем новое знание
        entry = f"""
## [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {knowledge.get('title', 'Untitled')}

{knowledge.get('content', '')}

**Source:** {knowledge.get('source', 'Unknown')}
**Tags:** {', '.join(knowledge.get('tags', []))}

---
"""

        with open(knowledge_file, 'a', encoding='utf-8') as f:
            f.write(entry)

        print(f"✅ Обновлена база знаний: {magister_name}")

    async def process_magister_feedback(self, magister_name: str, feedback: Dict):
        """Обработать обратную связь от магистра"""

        feedback_type = feedback.get("type")

        print(f"\n📬 Feedback от {magister_name}: {feedback_type}")

        if feedback_type == "missing_knowledge":
            await self._handle_missing_knowledge(magister_name, feedback)

        elif feedback_type == "outdated_info":
            await self._handle_outdated_info(magister_name, feedback)

        elif feedback_type == "system_improvement":
            await self._handle_system_improvement(magister_name, feedback)

        elif feedback_type == "escalation":
            await self._escalate_to_operator(magister_name, feedback)

    async def _handle_missing_knowledge(self, magister: str, feedback: Dict):
        """Обработать запрос на недостающие знания"""

        topic = feedback.get("topic")
        urgency = feedback.get("urgency", "medium")

        print(f"   🔍 Ищу знания по теме: {topic}")

        # TODO: Интеграция с Monitor для поиска знаний
        # Пока просто логируем

        print(f"   ⏳ Создана задача на поиск знаний")

    async def _handle_outdated_info(self, magister: str, feedback: Dict):
        """Обработать сообщение об устаревшей информации"""

        wiki_doc = feedback.get("wiki_doc")
        reason = feedback.get("reason")

        print(f"   ⚠️  Устаревшая информация: {wiki_doc}")
        print(f"   Причина: {reason}")

        # TODO: Создать задачу на обновление

    async def _handle_system_improvement(self, magister: str, feedback: Dict):
        """Обработать предложение улучшения системы"""

        improvement = feedback.get("improvement")
        impact = feedback.get("impact", "medium")

        print(f"   💡 Предложение улучшения: {improvement}")
        print(f"   Impact: {impact}")

        # Если impact высокий - эскалируем
        if impact == "high":
            await self._escalate_to_operator(magister, feedback)

    async def _escalate_to_operator(self, magister: str, feedback: Dict):
        """Эскалировать проблему к Operator"""

        print(f"   🚨 Эскалация к Operator")

        # Создаём событие для Operator
        event = Event(
            event_type="escalation",
            payload={
                "from_magister": magister,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat(),
                "priority": "P0"  # Высокий приоритет для эскалаций
            }
        )

        await self.event_bus.publish(event)


class TeacherAgent:
    """Teacher Agent - центр обучающей системы"""

    def __init__(
        self,
        teacher_vault_path: Path,
        magisters_dir: Path,
        architect_wiki_path: Path,
        event_bus: EventBus
    ):
        self.teacher_vault = ObsidianVault(teacher_vault_path)
        self.magisters_dir = magisters_dir
        self.architect_wiki = architect_wiki_path
        self.event_bus = event_bus

        # Компоненты
        self.knowledge_distributor = KnowledgeDistributor(
            architect_wiki_path,
            self.teacher_vault,
            event_bus
        )

        self.magister_manager = MagisterManager(
            magisters_dir,
            event_bus
        )

    async def start(self):
        """Запустить Teacher Agent"""

        print("\n" + "="*50)
        print("🎓 Teacher Agent - Hierarchical Learning System")
        print("="*50)

        # Подписываемся на события
        await self._subscribe_to_events()

        print("\n✅ Teacher Agent запущен")
        print("   Ожидаю новых знаний из Architect wiki...")

    async def _subscribe_to_events(self):
        """Подписаться на события"""

        # Подписываемся на новые wiki-документы из Architect
        await self.event_bus.subscribe(
            "architect.wiki.new_document",
            self._handle_new_knowledge
        )

        # Подписываемся на feedback от магистров
        await self.event_bus.subscribe(
            "magister.feedback",
            self._handle_magister_feedback
        )

    async def _handle_new_knowledge(self, event: Event):
        """Обработать новое знание из Architect wiki"""

        wiki_doc = Path(event.payload["wiki_doc"])

        # Распределяем знание магистрам
        magisters = await self.knowledge_distributor.distribute_new_knowledge(wiki_doc)

        print(f"\n✅ Знание распределено {len(magisters)} магистрам")

    async def _handle_magister_feedback(self, event: Event):
        """Обработать feedback от магистра"""

        magister = event.payload["magister"]
        feedback = event.payload["feedback"]

        await self.magister_manager.process_magister_feedback(magister, feedback)


async def main():
    """Точка входа"""

    # Пути
    base_dir = Path(__file__).parent.parent
    teacher_vault = base_dir / "obsidian" / "teacher"
    magisters_dir = base_dir / "obsidian" / "magisters"
    architect_wiki = base_dir / "obsidian" / "architect" / "wiki"

    # Event Bus
    event_bus = EventBus()

    # Создаём Teacher Agent
    teacher = TeacherAgent(
        teacher_vault,
        magisters_dir,
        architect_wiki,
        event_bus
    )

    # Запускаем
    await teacher.start()

    # Держим запущенным
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Остановка Teacher Agent...")


if __name__ == "__main__":
    asyncio.run(main())
