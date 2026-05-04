"""
CI Reputation Agent - Competitor Reputation Analysis

Анализирует репутацию конкурентов через:
- Отзывы (Яндекс.Карты, 2GIS, Prodoctorov, Zoon)
- Социальные сети (VK, Telegram, Instagram)
- Упоминания в медиа и блогах
- Sentiment analysis
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIReputationAgent(Agent):
    """
    CI Reputation - агент анализа репутации конкурентов.

    Фаза 4 CI pipeline:
    - Сбор отзывов из всех источников
    - Sentiment analysis (позитив/негатив/нейтрал)
    - Анализ тем отзывов (что хвалят/ругают)
    - Репутационные риски и возможности
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-reputation",
            database_url=database_url,
            vault_path=vault_path
        )
        # Переопределяем vault на специфичный для CI Reputation
        self.vault = ObsidianVault("AIM/obsidian/ci-reputation")

        # Review sources
        self.sources = {
            "yandex_maps": {
                "name": "Яндекс.Карты",
                "weight": 0.30,
                "url_pattern": "https://yandex.ru/maps/org/{org_id}/reviews/"
            },
            "2gis": {
                "name": "2GIS",
                "weight": 0.25,
                "url_pattern": "https://2gis.ru/{city}/firm/{firm_id}/reviews"
            },
            "prodoctorov": {
                "name": "ПроДокторов",
                "weight": 0.20,
                "url_pattern": "https://prodoctorov.ru/{city}/lpu/{clinic_id}/otzyvy/"
            },
            "zoon": {
                "name": "Zoon",
                "weight": 0.15,
                "url_pattern": "https://zoon.ru/{city}/{niche}/{clinic_slug}/reviews/"
            },
            "napopravku": {
                "name": "НаПоправку",
                "weight": 0.10,
                "url_pattern": "https://napopravku.ru/{city}/clinic/{clinic_id}/reviews/"
            }
        }

        # Sentiment categories
        self.sentiment_categories = {
            "positive": "Позитивные отзывы",
            "negative": "Негативные отзывы",
            "neutral": "Нейтральные отзывы"
        }

        # Review topics (что обсуждают в отзывах)
        self.review_topics = {
            "service": "Качество обслуживания",
            "doctors": "Врачи и персонал",
            "price": "Цены",
            "equipment": "Оборудование",
            "cleanliness": "Чистота",
            "waiting_time": "Время ожидания",
            "results": "Результаты лечения",
            "communication": "Коммуникация"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ репутации конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов для анализа (обязательно)
                - sources: источники отзывов (опционально, default: все)

        Returns:
            TaskResult с результатами анализа репутации
        """
        try:
            competitors = task.payload["competitors"]
            sources = task.payload.get("sources", list(self.sources.keys()))

            # Логирование начала
            print(f"[CI Reputation] Начало анализа репутации {len(competitors)} конкурентов")

            # Шаг 1: Collect reviews from all sources
            reviews_data = []
            for competitor in competitors:
                competitor_reviews = await self._collect_reviews(competitor, sources)
                reviews_data.append(competitor_reviews)

            # Шаг 2: Sentiment analysis
            sentiment_data = await self._analyze_sentiment(reviews_data)

            # Шаг 3: Topic analysis
            topic_data = await self._analyze_topics(reviews_data)

            # Шаг 4: Calculate reputation scores
            reputation_scores = await self._calculate_reputation_scores(
                reviews_data, sentiment_data, topic_data
            )

            # Шаг 5: Identify reputation risks and opportunities
            risks_opportunities = await self._identify_risks_opportunities(
                reputation_scores, sentiment_data, topic_data
            )

            # Шаг 6: Generate insights
            insights = await self._generate_insights(
                reputation_scores, sentiment_data, topic_data
            )

            # Шаг 7: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "sources_used": sources,
                "reviews_data": reviews_data,
                "sentiment_data": sentiment_data,
                "topic_data": topic_data,
                "reputation_scores": reputation_scores,
                "risks_opportunities": risks_opportunities,
                "insights": insights
            }

            await self._save_results(results)

            # Логирование завершения
            print(f"[CI Reputation] Завершён анализ репутации {len(competitors)} конкурентов")

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
            print(f"[CI Reputation] Ошибка: {e}")
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

    async def _collect_reviews(
        self,
        competitor: Dict[str, Any],
        sources: List[str]
    ) -> Dict[str, Any]:
        """
        Собрать отзывы конкурента из всех источников.

        Args:
            competitor: данные конкурента
            sources: список источников

        Returns:
            Данные отзывов конкурента
        """
        name = competitor["name"]
        print(f"[CI Reputation] Сбор отзывов: {name}")

        reviews = {
            "name": name,
            "sources": {},
            "total_reviews": 0,
            "avg_rating": 0.0
        }

        total_rating = 0.0
        total_count = 0

        # Собрать отзывы из каждого источника
        for source in sources:
            if source in self.sources:
                source_reviews = await self._collect_from_source(competitor, source)
                reviews["sources"][source] = source_reviews

                total_rating += source_reviews["avg_rating"] * source_reviews["count"]
                total_count += source_reviews["count"]

        reviews["total_reviews"] = total_count
        reviews["avg_rating"] = round(total_rating / total_count, 2) if total_count > 0 else 0.0

        return reviews

    async def _collect_from_source(
        self,
        competitor: Dict[str, Any],
        source: str
    ) -> Dict[str, Any]:
        """
        Собрать отзывы из одного источника.

        Args:
            competitor: данные конкурента
            source: источник отзывов

        Returns:
            Данные отзывов из источника
        """
        # TODO: Реальный сбор через WebFetch
        # Пока генерируем реалистичные тестовые данные

        import random

        count = random.randint(20, 200)
        avg_rating = round(random.uniform(3.8, 4.9), 1)

        # Генерировать распределение по sentiment
        positive_pct = random.randint(60, 85)
        negative_pct = random.randint(5, 20)
        neutral_pct = 100 - positive_pct - negative_pct

        return {
            "source": source,
            "source_name": self.sources[source]["name"],
            "count": count,
            "avg_rating": avg_rating,
            "sentiment_distribution": {
                "positive": positive_pct,
                "negative": negative_pct,
                "neutral": neutral_pct
            },
            "recent_reviews": self._generate_sample_reviews(count, avg_rating)
        }

    def _generate_sample_reviews(self, count: int, avg_rating: float) -> List[Dict[str, Any]]:
        """Генерировать примеры отзывов."""
        import random

        samples = []
        num_samples = min(5, count)

        for _ in range(num_samples):
            rating = round(random.gauss(avg_rating, 0.5), 1)
            rating = max(1.0, min(5.0, rating))

            sentiment = "positive" if rating >= 4.0 else "negative" if rating < 3.0 else "neutral"

            samples.append({
                "rating": rating,
                "sentiment": sentiment,
                "text": self._generate_review_text(sentiment),
                "date": "2026-04-15"  # Примерная дата
            })

        return samples

    def _generate_review_text(self, sentiment: str) -> str:
        """Генерировать текст отзыва."""
        positive_texts = [
            "Отличная клиника, профессиональные врачи",
            "Очень довольна результатом, рекомендую",
            "Современное оборудование, вежливый персонал",
            "Быстро записали, качественно обслужили"
        ]

        negative_texts = [
            "Долго ждали приёма, не понравилось",
            "Завышенные цены, результат не оправдал ожиданий",
            "Грубый персонал, не рекомендую",
            "Обещали одно, сделали другое"
        ]

        neutral_texts = [
            "Обычная клиника, ничего особенного",
            "Нормально, но есть куда расти",
            "Средний уровень обслуживания",
            "Приемлемо, но не более"
        ]

        import random

        if sentiment == "positive":
            return random.choice(positive_texts)
        elif sentiment == "negative":
            return random.choice(negative_texts)
        else:
            return random.choice(neutral_texts)

    async def _analyze_sentiment(
        self,
        reviews_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Провести sentiment analysis для всех конкурентов.

        Args:
            reviews_data: данные отзывов

        Returns:
            Результаты sentiment analysis
        """
        sentiment_data = []

        for competitor_reviews in reviews_data:
            # Агрегировать sentiment по всем источникам
            total_positive = 0
            total_negative = 0
            total_neutral = 0
            total_count = 0

            for source_data in competitor_reviews["sources"].values():
                dist = source_data["sentiment_distribution"]
                count = source_data["count"]

                total_positive += (dist["positive"] / 100) * count
                total_negative += (dist["negative"] / 100) * count
                total_neutral += (dist["neutral"] / 100) * count
                total_count += count

            sentiment_data.append({
                "name": competitor_reviews["name"],
                "total_reviews": total_count,
                "sentiment": {
                    "positive": round((total_positive / total_count) * 100, 1) if total_count > 0 else 0,
                    "negative": round((total_negative / total_count) * 100, 1) if total_count > 0 else 0,
                    "neutral": round((total_neutral / total_count) * 100, 1) if total_count > 0 else 0
                },
                "sentiment_score": round((total_positive - total_negative) / total_count, 2) if total_count > 0 else 0
            })

        print(f"[CI Reputation] Sentiment analysis завершён для {len(sentiment_data)} конкурентов")

        return sentiment_data

    async def _analyze_topics(
        self,
        reviews_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Провести topic analysis (что обсуждают в отзывах).

        Args:
            reviews_data: данные отзывов

        Returns:
            Результаты topic analysis
        """
        # TODO: Реальный NLP анализ тем
        # Пока генерируем реалистичные данные

        import random

        topic_data = []

        for competitor_reviews in reviews_data:
            topics = {}

            for topic_key, topic_name in self.review_topics.items():
                # Генерировать упоминания темы
                mentions = random.randint(10, 100)

                # Генерировать sentiment для темы
                positive_pct = random.randint(50, 90)
                negative_pct = random.randint(5, 30)
                neutral_pct = 100 - positive_pct - negative_pct

                topics[topic_key] = {
                    "name": topic_name,
                    "mentions": mentions,
                    "sentiment": {
                        "positive": positive_pct,
                        "negative": negative_pct,
                        "neutral": neutral_pct
                    }
                }

            topic_data.append({
                "name": competitor_reviews["name"],
                "topics": topics
            })

        print(f"[CI Reputation] Topic analysis завершён для {len(topic_data)} конкурентов")

        return topic_data

    async def _calculate_reputation_scores(
        self,
        reviews_data: List[Dict[str, Any]],
        sentiment_data: List[Dict[str, Any]],
        topic_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Рассчитать reputation scores для конкурентов.

        Args:
            reviews_data: данные отзывов
            sentiment_data: данные sentiment
            topic_data: данные тем

        Returns:
            Reputation scores
        """
        reputation_scores = []

        for i, competitor_reviews in enumerate(reviews_data):
            sentiment = sentiment_data[i]

            # Рассчитать reputation score (0-100)
            # Формула: (avg_rating / 5) * 50 + (sentiment_score + 1) / 2 * 50
            avg_rating = competitor_reviews["avg_rating"]
            sentiment_score = sentiment["sentiment_score"]

            reputation_score = round(
                (avg_rating / 5) * 50 + ((sentiment_score + 1) / 2) * 50,
                1
            )

            # Определить grade
            if reputation_score >= 85:
                grade = "A"
            elif reputation_score >= 70:
                grade = "B"
            elif reputation_score >= 55:
                grade = "C"
            else:
                grade = "D"

            reputation_scores.append({
                "name": competitor_reviews["name"],
                "reputation_score": reputation_score,
                "grade": grade,
                "avg_rating": avg_rating,
                "total_reviews": competitor_reviews["total_reviews"],
                "sentiment_score": sentiment_score
            })

        print(f"[CI Reputation] Reputation scores рассчитаны для {len(reputation_scores)} конкурентов")

        return reputation_scores

    async def _identify_risks_opportunities(
        self,
        reputation_scores: List[Dict[str, Any]],
        sentiment_data: List[Dict[str, Any]],
        topic_data: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Определить репутационные риски и возможности.

        Args:
            reputation_scores: reputation scores
            sentiment_data: данные sentiment
            topic_data: данные тем

        Returns:
            Риски и возможности
        """
        risks = []
        opportunities = []

        for i, score_data in enumerate(reputation_scores):
            sentiment = sentiment_data[i]
            topics = topic_data[i]["topics"]

            # Риски: высокий негатив
            if sentiment["sentiment"]["negative"] > 20:
                risks.append({
                    "type": "high_negative_sentiment",
                    "competitor": score_data["name"],
                    "negative_pct": sentiment["sentiment"]["negative"],
                    "description": f"{score_data['name']} имеет {sentiment['sentiment']['negative']}% негативных отзывов"
                })

            # Возможности: слабые темы у конкурентов
            for topic_key, topic_data_item in topics.items():
                if topic_data_item["sentiment"]["negative"] > 30:
                    opportunities.append({
                        "type": "competitor_weakness",
                        "competitor": score_data["name"],
                        "topic": topic_data_item["name"],
                        "negative_pct": topic_data_item["sentiment"]["negative"],
                        "description": f"{score_data['name']} получает критику по теме '{topic_data_item['name']}' ({topic_data_item['sentiment']['negative']}% негатива)"
                    })

        print(f"[CI Reputation] Найдено {len(risks)} рисков и {len(opportunities)} возможностей")

        return {
            "risks": risks,
            "opportunities": opportunities
        }

    async def _generate_insights(
        self,
        reputation_scores: List[Dict[str, Any]],
        sentiment_data: List[Dict[str, Any]],
        topic_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать инсайты о репутации рынка.

        Args:
            reputation_scores: reputation scores
            sentiment_data: данные sentiment
            topic_data: данные тем

        Returns:
            Инсайты
        """
        # Средняя репутация рынка
        avg_reputation = round(
            sum(s["reputation_score"] for s in reputation_scores) / len(reputation_scores),
            1
        )

        # Средний sentiment
        avg_positive = round(
            sum(s["sentiment"]["positive"] for s in sentiment_data) / len(sentiment_data),
            1
        )
        avg_negative = round(
            sum(s["sentiment"]["negative"] for s in sentiment_data) / len(sentiment_data),
            1
        )

        # Лучший и худший по репутации
        best = max(reputation_scores, key=lambda x: x["reputation_score"])
        worst = min(reputation_scores, key=lambda x: x["reputation_score"])

        insights = {
            "market_avg_reputation": avg_reputation,
            "market_avg_sentiment": {
                "positive": avg_positive,
                "negative": avg_negative
            },
            "best_reputation": {
                "name": best["name"],
                "score": best["reputation_score"],
                "grade": best["grade"]
            },
            "worst_reputation": {
                "name": worst["name"],
                "score": worst["reputation_score"],
                "grade": worst["grade"]
            },
            "reputation_spread": round(best["reputation_score"] - worst["reputation_score"], 1)
        }

        print(f"[CI Reputation] Средняя репутация рынка: {avg_reputation}")

        return insights

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-reputation.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Reputation] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "review_collection",
            "sentiment_analysis",
            "topic_analysis",
            "reputation_scoring",
            "risk_identification",
            "opportunity_identification"
        ]
