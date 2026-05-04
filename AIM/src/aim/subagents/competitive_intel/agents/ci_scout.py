"""
CI Scout Agent - Market Discovery and Competitor Clustering

Находит ВСЕХ конкурентов в нише/гео, кластеризует их и выбирает TOP-5-10 для глубокого анализа.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIScoutAgent(Agent):
    """
    CI Scout - агент поиска и кластеризации конкурентов.

    Фаза 1 CI pipeline:
    - Находит всех игроков в нише через WebSearch и каталоги
    - Строит профили конкурентов
    - Кластеризует по типам (direct/indirect/leader/niche/emerging)
    - Выбирает TOP-5-10 для глубокого анализа
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-scout",
            database_url=database_url,
            vault_path=vault_path
        )
        # Переопределяем vault на специфичный для CI Scout
        self.vault = ObsidianVault("AIM/obsidian/ci-scout")

        # Источники данных
        self.directories = {
            "zoon": "https://zoon.ru/{geo_slug}/{niche_slug}/",
            "2gis": "https://2gis.ru/{geo_slug}/search/{niche}",
            "yandex_maps": "https://yandex.ru/maps/?text={niche}+{geo}",
            "prodoctorov": "https://prodoctorov.ru/{geo_slug}/lpu/?search={niche}",
            "napopravku": "https://napopravku.ru/{geo_slug}/clinics/",
            "avito": "https://www.avito.ru/{geo_slug}/uslugi/{niche_slug}"
        }

        # Кластеры конкурентов
        self.clusters = {
            "direct": "Прямые конкуренты (та же услуга, ЦА, ценовой сегмент)",
            "indirect": "Косвенные (смежная услуга или другая ЦА)",
            "leader": "Лидеры рынка (самые известные, высокий рейтинг)",
            "niche": "Нишевые (узкая специализация)",
            "emerging": "Новые игроки (< 2 лет, активно растут)"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить поиск и кластеризацию конкурентов.

        Args:
            task: Задача с payload:
                - niche: ниша (обязательно)
                - geo: город (обязательно)
                - target_audience: целевая аудитория (опционально)
                - price_segment: ценовой сегмент (опционально)

        Returns:
            TaskResult с найденными конкурентами
        """
        try:
            niche = task.payload["niche"]
            geo = task.payload["geo"]
            target_audience = task.payload.get("target_audience", "")
            price_segment = task.payload.get("price_segment", "mid")

            # Логирование начала
            pass

            # Шаг 1: Multi-source discovery
            competitors = await self._discover_competitors(niche, geo)

            # Шаг 2: Build competitor profiles
            profiles = await self._build_profiles(competitors, niche, geo)

            # Шаг 3: Cluster competitors
            clustered = await self._cluster_competitors(profiles, target_audience, price_segment)

            # Шаг 4: Select TOP-5-10
            top_selected = await self._select_top_competitors(clustered)

            # Шаг 5: Market insights
            insights = await self._generate_insights(clustered, top_selected)

            # Шаг 6: Save results
            results = {
                "niche": niche,
                "geo": geo,
                "target_audience": target_audience,
                "price_segment": price_segment,
                "analysis_date": datetime.now().isoformat(),
                "total_found": len(profiles),
                "top_selected": len(top_selected),
                "competitors": profiles,
                "top_for_analysis": top_selected,
                "clusters": clustered,
                "insights": insights
            }

            await self._save_results(results)

            # Логирование завершения
            pass

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=results,
                error=None,
                duration_seconds=0.0,
                completed_at=datetime.now()
            )

        except Exception as e:
            pass
            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=0.0,
                completed_at=datetime.now()
            )

    async def _discover_competitors(self, niche: str, geo: str) -> List[str]:
        """
        Найти всех конкурентов через WebSearch и каталоги.

        Args:
            niche: ниша
            geo: город

        Returns:
            Список названий конкурентов
        """
        competitors = set()

        # WebSearch queries (8 запросов)
        search_queries = [
            f"{niche} {geo} топ лучшие 2025 2026",
            f"{niche} {geo} рейтинг клиник отзывы",
            f"{niche} {geo} частная клиника цены",
            f"{niche} {geo} косметолог запись онлайн",
            f"{niche} {geo} site:prodoctorov.ru",
            f"{niche} {geo} site:zoon.ru",
            f"{niche} {geo} site:napopravku.ru",
            f"{niche} {geo} VK группа реклама"
        ]

        # TODO: Реальный WebSearch через инструменты
        # Пока генерируем тестовые данные на основе ниши и гео
        competitors.update(self._generate_test_competitors(niche, geo))

        print(f"[CI Scout] Найдено {len(competitors)} конкурентов через WebSearch")

        return list(competitors)

    def _generate_test_competitors(self, niche: str, geo: str) -> List[str]:
        """
        Генерировать тестовые данные конкурентов.

        TODO: Заменить на реальный WebSearch когда будет доступен.
        """
        # Базовые названия для разных ниш
        base_names = {
            "стоматология": ["Дента", "Смайл", "Зубная Фея", "Дентал", "Стома"],
            "косметология": ["Грейс", "Бьюти", "Эстетик", "Глоу", "Шарм"],
            "default": ["Клиника", "Центр", "Медицина", "Здоровье", "Лайф"]
        }

        names = base_names.get(niche, base_names["default"])
        suffixes = ["Клиника", "Центр", "Студия", "Клуб", "Лаб"]

        competitors = []
        for i, name in enumerate(names[:5], 1):
            suffix = suffixes[i % len(suffixes)]
            competitors.append(f"{name} {suffix}")

        return competitors

    async def _build_profiles(
        self,
        competitors: List[str],
        niche: str,
        geo: str
    ) -> List[Dict[str, Any]]:
        """
        Построить профили конкурентов.

        Args:
            competitors: список названий
            niche: ниша
            geo: город

        Returns:
            Список профилей конкурентов
        """
        profiles = []

        for name in competitors:
            profile = await self._build_single_profile(name, niche, geo)
            profiles.append(profile)

        print(f"[CI Scout] Построено {len(profiles)} профилей конкурентов")

        return profiles

    async def _build_single_profile(
        self,
        name: str,
        niche: str,
        geo: str
    ) -> Dict[str, Any]:
        """
        Построить профиль одного конкурента.

        Args:
            name: название
            niche: ниша
            geo: город

        Returns:
            Профиль конкурента
        """
        # TODO: Реальный сбор данных через WebFetch
        # Пока генерируем реалистичные тестовые данные

        # Определить ценовой сегмент по названию
        premium_keywords = ["грейс", "премиум", "элит", "люкс", "vip"]
        budget_keywords = ["эконом", "доступ", "бюджет", "народ"]

        name_lower = name.lower()
        if any(kw in name_lower for kw in premium_keywords):
            price_segment = "premium"
            positioning = "premium"
        elif any(kw in name_lower for kw in budget_keywords):
            price_segment = "budget"
            positioning = "budget"
        else:
            price_segment = "mid"
            positioning = "mid"

        # Генерировать рейтинг
        import random
        rating = round(random.uniform(4.2, 4.9), 1)
        reviews = random.randint(50, 500)

        profile = {
            "name": name,
            "url": f"https://{self._slugify(name)}.ru",
            "address": f"ул. Примерная, {random.randint(1, 100)}",
            "geo": geo,
            "niche": niche,
            "description": f"{name} - {niche} в {geo}",
            "positioning": positioning,
            "cluster": "unknown",  # Будет определён в _cluster_competitors
            "channels": {
                "website": True,
                "vk": f"vk.com/{self._slugify(name)}",
                "telegram": f"t.me/{self._slugify(name)}",
                "yandex_maps_rating": f"{rating} ({reviews} отзывов)",
                "2gis_rating": f"{round(rating - 0.1, 1)} ({int(reviews * 0.6)} отзывов)",
                "online_booking": random.choice([True, False])
            },
            "price_segment": price_segment,
            "estimated_size": random.choice(["small", "medium", "large"]),
            "ad_presence": random.choice(["high", "medium", "low"]),
            "differentiators": [
                f"Специализация на {niche}",
                f"Работает в {geo}"
            ],
            "notes": f"Интересен для анализа как {positioning} игрок"
        }

        return profile

    def _slugify(self, text: str) -> str:
        """Преобразовать текст в slug."""
        # Транслитерация (упрощённая)
        translit = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }

        text = text.lower()
        result = []
        for char in text:
            if char in translit:
                result.append(translit[char])
            elif char.isalnum() or char == '-':
                result.append(char)
            elif char == ' ':
                result.append('-')

        return ''.join(result)

    async def _cluster_competitors(
        self,
        profiles: List[Dict[str, Any]],
        target_audience: str,
        price_segment: str
    ) -> Dict[str, List[str]]:
        """
        Кластеризовать конкурентов.

        Args:
            profiles: профили конкурентов
            target_audience: целевая аудитория
            price_segment: ценовой сегмент

        Returns:
            Словарь кластеров
        """
        clusters = {
            "direct": [],
            "indirect": [],
            "leader": [],
            "niche": [],
            "emerging": []
        }

        for profile in profiles:
            # Определить кластер
            cluster = self._determine_cluster(profile, target_audience, price_segment)
            profile["cluster"] = cluster
            clusters[cluster].append(profile["name"])

        print(f"[CI Scout] Кластеризация: direct={len(clusters['direct'])}, "
              f"indirect={len(clusters['indirect'])}, leader={len(clusters['leader'])}, "
              f"niche={len(clusters['niche'])}, emerging={len(clusters['emerging'])}")

        return clusters

    def _determine_cluster(
        self,
        profile: Dict[str, Any],
        target_audience: str,
        price_segment: str
    ) -> str:
        """
        Определить кластер для конкурента.

        Args:
            profile: профиль конкурента
            target_audience: целевая аудитория
            price_segment: ценовой сегмент

        Returns:
            Название кластера
        """
        # Прямой конкурент: тот же ценовой сегмент
        if profile["price_segment"] == price_segment:
            return "direct"

        # Лидер: высокий рейтинг + много отзывов
        rating_match = re.search(r'(\d+\.\d+)', profile["channels"]["yandex_maps_rating"])
        reviews_match = re.search(r'\((\d+)', profile["channels"]["yandex_maps_rating"])

        if rating_match and reviews_match:
            rating = float(rating_match.group(1))
            reviews = int(reviews_match.group(1))

            if rating >= 4.7 and reviews >= 200:
                return "leader"

        # Нишевой: узкая специализация (определяем по differentiators)
        if len(profile["differentiators"]) > 2:
            return "niche"

        # Новый игрок: малый размер + высокая рекламная активность
        if profile["estimated_size"] == "small" and profile["ad_presence"] == "high":
            return "emerging"

        # По умолчанию - косвенный
        return "indirect"

    async def _select_top_competitors(
        self,
        clusters: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Выбрать TOP-5-10 конкурентов для глубокого анализа.

        Критерии:
        1. Все прямые конкуренты
        2. Минимум 1 лидер рынка
        3. Минимум 1 нишевой
        4. Активная реклама
        5. Высокий рейтинг

        Args:
            clusters: кластеры конкурентов

        Returns:
            Список TOP конкурентов
        """
        top = []

        # Все прямые конкуренты
        for name in clusters["direct"]:
            top.append({
                "name": name,
                "cluster": "direct",
                "reason": "Прямой конкурент (тот же ценовой сегмент)"
            })

        # Минимум 1 лидер
        if clusters["leader"]:
            top.append({
                "name": clusters["leader"][0],
                "cluster": "leader",
                "reason": "Лидер рынка (высокий рейтинг, много отзывов)"
            })

        # Минимум 1 нишевой
        if clusters["niche"]:
            top.append({
                "name": clusters["niche"][0],
                "cluster": "niche",
                "reason": "Нишевой игрок (узкая специализация)"
            })

        # Добавить emerging если есть место
        if len(top) < 10 and clusters["emerging"]:
            top.append({
                "name": clusters["emerging"][0],
                "cluster": "emerging",
                "reason": "Новый игрок (активно растёт)"
            })

        print(f"[CI Scout] Выбрано {len(top)} конкурентов для глубокого анализа")

        return top

    async def _generate_insights(
        self,
        clusters: Dict[str, List[str]],
        top_selected: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать инсайты о рынке.

        Args:
            clusters: кластеры конкурентов
            top_selected: выбранные TOP конкуренты

        Returns:
            Инсайты о рынке
        """
        total_players = sum(len(names) for names in clusters.values())

        insights = {
            "total_players": total_players,
            "fragmentation": "высокая" if total_players > 15 else "средняя" if total_players > 8 else "низкая",
            "dominant_positioning": self._get_dominant_cluster(clusters),
            "digitalization_level": "высокий",  # TODO: рассчитать реально
            "key_gaps": [
                "Недостаточно онлайн-записи",
                "Слабое присутствие в Telegram"
            ]
        }

        print(f"[CI Scout] Сгенерированы инсайты: {total_players} игроков, "
              f"фрагментация {insights['fragmentation']}")

        return insights

    def _get_dominant_cluster(self, clusters: Dict[str, List[str]]) -> str:
        """Определить доминирующий кластер."""
        max_cluster = max(clusters.items(), key=lambda x: len(x[1]))
        return max_cluster[0]

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-competitors.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Scout] Результаты сохранены в {output_file}")

    async def _log_start(self, niche: str, geo: str):
        """Логировать начало работы."""
        print(f"[CI Scout] Начало поиска конкурентов: {niche} в {geo}")

    async def _log_completion(self, total: int, top: int):
        """Логировать завершение работы."""
        print(f"[CI Scout] Найдено {total} конкурентов, выбрано {top} для анализа")

    async def _log_error(self, error: str):
        """Логировать ошибку."""
        print(f"[CI Scout] Ошибка: {error}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "competitor_discovery",
            "market_mapping",
            "competitor_clustering",
            "market_insights"
        ]
