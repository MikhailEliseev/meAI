"""
DEPRECATED: Use ci_content_improved.py instead.

Kept for reference. Orchestrator uses CIContentAgentImproved from ci_content_improved.
This module contains mock/random data and is no longer wired into the CI pipeline.
"""

# fmt: off
_OLD_DOC = """
CI Content Agent - Content Strategy Analysis

Анализирует контент-стратегию конкурентов:
- Типы контента (блог, видео, кейсы, FAQ)
- Частота публикаций
- Качество и глубина контента
- SEO-оптимизация контента
- Контент-маркетинг стратегия

DEPRECATED: Use ci_content_improved.py instead.
Kept for reference. Orchestrator uses CIContentAgentImproved from ci_content_improved.
"""

from typing import Any, Dict, List
from datetime import datetime
import json
import random

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIContentAgent(Agent):
    """CI Content - агент анализа контент-стратегии конкурентов."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-content",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-content")

        # Content types
        self.content_types = {
            "blog": "Блог/статьи",
            "video": "Видео",
            "cases": "Кейсы/портфолио",
            "faq": "FAQ/вопросы-ответы",
            "guides": "Гайды/инструкции",
            "news": "Новости",
            "reviews": "Отзывы"
        }

        # Content quality indicators
        self.quality_indicators = [
            "word_count",
            "readability",
            "seo_optimization",
            "multimedia",
            "expertise",
            "freshness"
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ контент-стратегии конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - niche: ниша (опционально)

        Returns:
            TaskResult с анализом контента
        """
        try:
            competitors = task.payload["competitors"]
            niche = task.payload.get("niche", "")

            print(f"[CI Content] Начало анализа контента {len(competitors)} конкурентов")

            # Шаг 1: Analyze content for each competitor
            content_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_content(competitor, niche)
                content_profiles.append(profile)

            # Шаг 2: Market content analysis
            market_analysis = await self._analyze_market_content(content_profiles)

            # Шаг 3: Identify content leaders
            content_leaders = await self._identify_content_leaders(content_profiles)

            # Шаг 4: Content gaps analysis
            content_gaps = await self._analyze_content_gaps(content_profiles, niche)

            # Шаг 5: Content insights
            insights = await self._generate_content_insights(
                content_profiles, market_analysis, content_leaders, content_gaps
            )

            # Шаг 6: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "content_profiles": content_profiles,
                "market_analysis": market_analysis,
                "content_leaders": content_leaders,
                "content_gaps": content_gaps,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Content] Анализ контента завершён для {len(competitors)} конкурентов")

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
            print(f"[CI Content] Ошибка: {e}")
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

    async def _analyze_competitor_content(
        self,
        competitor: Dict[str, Any],
        niche: str
    ) -> Dict[str, Any]:
        """
        Проанализировать контент одного конкурента.

        Args:
            competitor: данные конкурента
            niche: ниша

        Returns:
            Контент-профиль конкурента
        """
        name = competitor["name"]
        print(f"[CI Content] Анализ контента: {name}")

        # TODO: Реальный анализ через краулинг + NLP
        # Пока генерируем реалистичные данные

        # Количество контента по типам
        content_by_type = {}
        for content_type in ["blog", "video", "cases", "faq", "guides"]:
            count = random.randint(0, 50) if random.random() > 0.3 else 0
            if count > 0:
                content_by_type[content_type] = count

        # Частота публикаций
        if content_by_type.get("blog", 0) > 20:
            frequency = "high"  # >2 раза в неделю
        elif content_by_type.get("blog", 0) > 10:
            frequency = "medium"  # 1-2 раза в неделю
        elif content_by_type.get("blog", 0) > 0:
            frequency = "low"  # <1 раза в неделю
        else:
            frequency = "none"

        # Качество контента (0-100)
        quality_score = random.randint(40, 95)

        # SEO-оптимизация
        seo_score = random.randint(30, 90)

        # Контент-маркетинг активность
        has_content_strategy = len(content_by_type) >= 3

        profile = {
            "name": name,
            "content_by_type": content_by_type,
            "total_content_pieces": sum(content_by_type.values()),
            "publishing_frequency": frequency,
            "quality_score": quality_score,
            "seo_score": seo_score,
            "has_content_strategy": has_content_strategy,
            "content_maturity": self._assess_content_maturity(
                len(content_by_type),
                sum(content_by_type.values()),
                quality_score
            )
        }

        return profile

    def _assess_content_maturity(
        self,
        types_count: int,
        total_pieces: int,
        quality: int
    ) -> str:
        """Оценить зрелость контент-стратегии."""
        score = 0

        # Разнообразие типов контента
        if types_count >= 4:
            score += 3
        elif types_count >= 2:
            score += 2
        elif types_count >= 1:
            score += 1

        # Объём контента
        if total_pieces >= 30:
            score += 3
        elif total_pieces >= 15:
            score += 2
        elif total_pieces >= 5:
            score += 1

        # Качество
        if quality >= 80:
            score += 3
        elif quality >= 60:
            score += 2
        elif quality >= 40:
            score += 1

        # Итоговая оценка
        if score >= 7:
            return "advanced"
        elif score >= 4:
            return "intermediate"
        elif score >= 2:
            return "basic"
        else:
            return "minimal"

    async def _analyze_market_content(
        self,
        content_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать контент-активность рынка.

        Args:
            content_profiles: контент-профили конкурентов

        Returns:
            Анализ рынка
        """
        print(f"[CI Content] Анализ контент-активности рынка")

        # Средние показатели
        avg_content_pieces = sum(p["total_content_pieces"] for p in content_profiles) / len(content_profiles)
        avg_quality = sum(p["quality_score"] for p in content_profiles) / len(content_profiles)
        avg_seo = sum(p["seo_score"] for p in content_profiles) / len(content_profiles)

        # Компании с контент-стратегией
        with_strategy = sum(1 for p in content_profiles if p["has_content_strategy"])
        strategy_adoption = (with_strategy / len(content_profiles)) * 100

        # Самые популярные типы контента
        content_type_usage = {}
        for profile in content_profiles:
            for content_type in profile["content_by_type"].keys():
                content_type_usage[content_type] = content_type_usage.get(content_type, 0) + 1

        most_popular = sorted(content_type_usage.items(), key=lambda x: x[1], reverse=True)[:3]

        market_analysis = {
            "avg_content_pieces": round(avg_content_pieces, 1),
            "avg_quality_score": round(avg_quality, 1),
            "avg_seo_score": round(avg_seo, 1),
            "strategy_adoption_percent": round(strategy_adoption, 1),
            "most_popular_content_types": [
                {"type": ct, "usage_count": count} for ct, count in most_popular
            ]
        }

        return market_analysis

    async def _identify_content_leaders(
        self,
        content_profiles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Определить лидеров по контенту.

        Args:
            content_profiles: контент-профили

        Returns:
            Лидеры по контенту
        """
        print(f"[CI Content] Определение контент-лидеров")

        # Сортировка по объёму контента
        sorted_by_volume = sorted(
            content_profiles,
            key=lambda x: x["total_content_pieces"],
            reverse=True
        )

        # Сортировка по качеству
        sorted_by_quality = sorted(
            content_profiles,
            key=lambda x: x["quality_score"],
            reverse=True
        )

        # TOP-3 по объёму
        volume_leaders = sorted_by_volume[:3]

        # TOP-3 по качеству
        quality_leaders = sorted_by_quality[:3]

        return {
            "volume_leaders": [
                {
                    "name": p["name"],
                    "content_pieces": p["total_content_pieces"],
                    "maturity": p["content_maturity"]
                }
                for p in volume_leaders if p["total_content_pieces"] > 0
            ],
            "quality_leaders": [
                {
                    "name": p["name"],
                    "quality_score": p["quality_score"],
                    "seo_score": p["seo_score"]
                }
                for p in quality_leaders
            ]
        }

    async def _analyze_content_gaps(
        self,
        content_profiles: List[Dict[str, Any]],
        niche: str
    ) -> List[Dict[str, Any]]:
        """
        Проанализировать пробелы в контенте.

        Args:
            content_profiles: контент-профили
            niche: ниша

        Returns:
            Пробелы в контенте
        """
        print(f"[CI Content] Анализ пробелов в контенте")

        gaps = []

        # Проверка покрытия типов контента
        all_types = set(self.content_types.keys())
        used_types = set()

        for profile in content_profiles:
            used_types.update(profile["content_by_type"].keys())

        missing_types = all_types - used_types

        for content_type in missing_types:
            gaps.append({
                "type": "missing_content_type",
                "content_type": content_type,
                "description": f"Никто не использует {self.content_types[content_type]}",
                "opportunity": "high"
            })

        # Низкое качество контента
        low_quality_count = sum(1 for p in content_profiles if p["quality_score"] < 60)
        if low_quality_count > len(content_profiles) / 2:
            gaps.append({
                "type": "quality_gap",
                "description": "Большинство конкурентов имеют низкое качество контента",
                "opportunity": "high"
            })

        # Низкая SEO-оптимизация
        low_seo_count = sum(1 for p in content_profiles if p["seo_score"] < 60)
        if low_seo_count > len(content_profiles) / 2:
            gaps.append({
                "type": "seo_gap",
                "description": "Большинство конкурентов плохо оптимизируют контент для SEO",
                "opportunity": "medium"
            })

        return gaps

    async def _generate_content_insights(
        self,
        content_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        content_leaders: Dict[str, Any],
        content_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать контент-инсайты.

        Args:
            content_profiles: контент-профили
            market_analysis: анализ рынка
            content_leaders: лидеры по контенту
            content_gaps: пробелы в контенте

        Returns:
            Инсайты
        """
        print(f"[CI Content] Генерация контент-инсайтов")

        insights = {
            "content_maturity_level": self._assess_market_maturity(content_profiles),
            "content_competition": "high" if market_analysis["avg_content_pieces"] > 20 else "medium" if market_analysis["avg_content_pieces"] > 10 else "low",
            "opportunities_count": len([g for g in content_gaps if g.get("opportunity") == "high"]),
            "key_findings": []
        }

        # Ключевые находки
        if market_analysis["strategy_adoption_percent"] < 50:
            insights["key_findings"].append("Менее 50% конкурентов имеют контент-стратегию")

        if market_analysis["avg_quality_score"] < 70:
            insights["key_findings"].append(f"Средний уровень качества контента: {market_analysis['avg_quality_score']:.0f}/100")

        if len(content_gaps) > 0:
            insights["key_findings"].append(f"Обнаружено {len(content_gaps)} возможностей для дифференциации")

        return insights

    def _assess_market_maturity(self, profiles: List[Dict[str, Any]]) -> str:
        """Оценить зрелость контент-маркетинга на рынке."""
        maturity_scores = {
            "minimal": 1,
            "basic": 2,
            "intermediate": 3,
            "advanced": 4
        }

        avg_score = sum(maturity_scores.get(p["content_maturity"], 1) for p in profiles) / len(profiles)

        if avg_score >= 3.5:
            return "advanced"
        elif avg_score >= 2.5:
            return "intermediate"
        elif avg_score >= 1.5:
            return "basic"
        else:
            return "minimal"

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-content.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Content] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "content_analysis",
            "blog_analysis",
            "content_quality_assessment",
            "seo_content_analysis",
            "content_strategy_analysis",
            "content_gap_analysis"
        ]
