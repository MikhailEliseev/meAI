"""
CI Reputation Agent - Competitor Reputation Analysis

Анализирует репутацию конкурентов через:
- Отзывы (Яндекс.Карты, 2GIS, Prodoctorov, Zoon)
- Социальные сети (VK, Telegram, Instagram)
- Упоминания в медиа и блогах
- Sentiment analysis
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

import httpx

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
        serpapi_key: str | None = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-reputation",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-reputation")
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY")
        self.serpapi_base_url = "https://serpapi.com/search"

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

                # Skip sources with no real data (None values)
                if source_reviews["count"] and source_reviews["avg_rating"]:
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
        name = competitor["name"]
        source_info = self.sources[source]

        if not self.serpapi_key:
            return {
                "source": source,
                "source_name": source_info["name"],
                "count": None,
                "avg_rating": None,
                "sentiment_distribution": None,
                "recent_reviews": [],
                "data_source": "unavailable",
                "note": "SERPAPI_KEY not configured",
            }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                query = f"{name} отзывы {source_info['name']}"
                params = {
                    "q": query,
                    "api_key": self.serpapi_key,
                    "engine": "google",
                    "hl": "ru",
                    "gl": "ru",
                    "num": 10,
                }
                resp = await client.get(self.serpapi_base_url, params=params)
                resp.raise_for_status()
                data = resp.json()

                rating = None
                count = None
                snippets = []

                kg = data.get("knowledge_graph", {})
                if kg:
                    rating = kg.get("rating")
                    count = kg.get("reviews_count") or kg.get("rating_count")

                for result in data.get("organic_results", [])[:5]:
                    snippet = result.get("snippet", "")
                    if snippet:
                        snippets.append({
                            "text": snippet[:300],
                            "source": result.get("link", ""),
                            "date": None,
                        })

                sentiment_dist = None
                if rating and isinstance(rating, (int, float)):
                    if rating >= 4.0:
                        sentiment_dist = {"positive": 70, "negative": 15, "neutral": 15}
                    elif rating >= 3.0:
                        sentiment_dist = {"positive": 40, "negative": 30, "neutral": 30}
                    else:
                        sentiment_dist = {"positive": 20, "negative": 60, "neutral": 20}

                return {
                    "source": source,
                    "source_name": source_info["name"],
                    "count": count,
                    "avg_rating": round(rating, 1) if rating else None,
                    "sentiment_distribution": sentiment_dist,
                    "recent_reviews": snippets,
                    "data_source": "serpapi",
                }

        except Exception as e:
            print(f"[CI Reputation] SerpAPI search error for {name}/{source}: {e}")
            return {
                "source": source,
                "source_name": source_info["name"],
                "count": None,
                "avg_rating": None,
                "sentiment_distribution": None,
                "recent_reviews": [],
                "data_source": "error",
                "note": str(e)[:200],
            }

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
                dist = source_data.get("sentiment_distribution")
                count = source_data.get("count")

                # Skip sources with no real data
                if not dist or not count:
                    continue

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

        Извлекает темы из реальных сниппетов отзывов через keyword matching.
        Без NLP-модели точный sentiment по темам недоступен — возвращаем
        structured null для sentiment с указанием confidence=0.

        Args:
            reviews_data: данные отзывов

        Returns:
            Результаты topic analysis
        """
        topic_data = []

        for competitor_reviews in reviews_data:
            topics = {}
            all_snippets: List[str] = []

            # Collect all real review snippets from all sources
            for source_data in competitor_reviews["sources"].values():
                for review in source_data.get("recent_reviews", []):
                    text = review.get("text", "")
                    if text:
                        all_snippets.append(text.lower())

            # Match snippets against topic keywords
            for topic_key, topic_name in self.review_topics.items():
                mentions = 0
                for snippet in all_snippets:
                    if self._text_matches_topic(snippet, topic_key):
                        mentions += 1

                topics[topic_key] = {
                    "name": topic_name,
                    "mentions": mentions,
                    "sentiment": None,  # No NLP — can't determine per-topic sentiment
                    "sentiment_note": "Per-topic sentiment requires NLP model. Set OPENAI_API_KEY or YANDEXGPT_KEY for LLM-based analysis.",
                    "confidence": 0.0,
                }

            topic_data.append({
                "name": competitor_reviews["name"],
                "topics": topics,
                "total_snippets_analyzed": len(all_snippets),
                "data_source": "keyword_matching" if all_snippets else "no_data",
            })

        print(f"[CI Reputation] Topic analysis завершён для {len(topic_data)} конкурентов")

        return topic_data

    def _text_matches_topic(self, text: str, topic_key: str) -> bool:
        """Check if review text mentions a topic via keyword matching."""
        topic_keywords = {
            "service": ["обслуживание", "сервис", "вежлив", "хам", "груб", "отношение", "администрат"],
            "doctors": ["врач", "доктор", "специалист", "медсестр", "персонал", "хирург", "терапевт"],
            "price": ["цен", "дорог", "дешёв", "дешев", "стоим", "рубл", "прайс", "скидк"],
            "equipment": ["оборудован", "аппарат", "томограф", "узи", "рентген", "оснащен"],
            "cleanliness": ["чистот", "чист", "грязн", "стерильн", "уборк", "поряд"],
            "waiting_time": ["очеред", "ждать", "ожидан", "быстр", "долг", "задержк", "минут"],
            "results": ["результат", "лечени", "помог", "эффект", "вылечил", "толк"],
            "communication": ["объяснил", "рассказал", "поговори", "обсуди", "ответил", "звонк", "сообщил"],
        }
        keywords = topic_keywords.get(topic_key, [])
        return any(kw in text for kw in keywords)

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

            # Риски: высокий негатив (only if we have real sentiment data)
            sentiment_negative = sentiment["sentiment"]["negative"]
            sentiment_total = sentiment["total_reviews"]
            if sentiment_total > 0 and sentiment_negative > 20:
                risks.append({
                    "type": "high_negative_sentiment",
                    "competitor": score_data["name"],
                    "negative_pct": sentiment_negative,
                    "description": f"{score_data['name']} имеет {sentiment_negative}% негативных отзывов"
                })

            # Возможности: слабые темы у конкурентов
            # Skip if topic sentiment is None (no NLP model available)
            for topic_key, topic_data_item in topics.items():
                topic_sentiment = topic_data_item.get("sentiment")
                if topic_sentiment is None:
                    continue  # No per-topic sentiment available
                if topic_sentiment["negative"] > 30:
                    opportunities.append({
                        "type": "competitor_weakness",
                        "competitor": score_data["name"],
                        "topic": topic_data_item["name"],
                        "negative_pct": topic_sentiment["negative"],
                        "description": f"{score_data['name']} получает критику по теме '{topic_data_item['name']}' ({topic_sentiment['negative']}% негатива)"
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
