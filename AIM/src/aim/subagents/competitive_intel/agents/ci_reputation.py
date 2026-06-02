"""
CI Reputation Agent - Competitor Reputation Analysis

Анализирует репутацию конкурентов через:
- Отзывы (Яндекс.Карты, 2GIS, Prodoctorov, Zoon)
- Brave Search (fallback when SerpAPI unavailable)
- Sentiment analysis
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

import httpx

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIReputationAgent(Agent):
    """
    CI Reputation - агент анализа репутации конкурентов.

    Фаза 4 CI pipeline:
    - Сбор отзывов из всех источников (SerpAPI → Brave → прямой скрапинг)
    - Sentiment analysis
    - Topic analysis
    - Репутационные риски и возможности
    """

    def __init__(
        self,
        agent_id: str,
        serpapi_key: str | None = None,
        brave_api_key: str | None = None,
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
        self.brave_api_key = brave_api_key or os.getenv("BRAVE_API_KEY")
        self.serpapi_base_url = "https://serpapi.com/search"
        self.brave_base_url = "https://api.search.brave.com/res/v1/web/search"

        # Rotating SerpAPI client (auto-failover on 429)
        self._serpapi_client = None
        try:
            from aim.subagents.competitive_intel.serpapi_client import get_serpapi_client
            self._serpapi_client = get_serpapi_client()
        except Exception:
            pass

        # Review sources with platform-specific scraping URLs
        self.sources = {
            "yandex_maps": {
                "name": "Яндекс.Карты",
                "weight": 0.30,
                "search_query": "яндекс карты отзывы",
            },
            "2gis": {
                "name": "2GIS",
                "weight": 0.25,
                "search_query": "2гис отзывы",
            },
            "prodoctorov": {
                "name": "ПроДокторов",
                "weight": 0.20,
                "search_query": "prodoctorov отзывы",
            },
            "zoon": {
                "name": "Zoon",
                "weight": 0.15,
                "search_query": "zoon отзывы",
            },
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

        # Topic keywords for matching
        self._topic_keywords = {
            "service": ["обслуживание", "сервис", "вежлив", "хам", "груб", "отношение", "администрат"],
            "doctors": ["врач", "доктор", "специалист", "медсестр", "персонал", "хирург", "терапевт"],
            "price": ["цен", "дорог", "дешёв", "дешев", "стоим", "рубл", "прайс", "скидк"],
            "equipment": ["оборудован", "аппарат", "томограф", "узи", "рентген", "оснащен"],
            "cleanliness": ["чистот", "чист", "грязн", "стерильн", "уборк", "поряд"],
            "waiting_time": ["очеред", "ждать", "ожидан", "быстр", "долг", "задержк", "минут"],
            "results": ["результат", "лечени", "помог", "эффект", "вылечил", "толк"],
            "communication": ["объяснил", "рассказал", "поговори", "обсуди", "ответил", "звонк", "сообщил"],
        }

        # Sentiment keywords for text-based analysis
        self._positive_words = [
            "отлично", "прекрасно", "замечательно", "профессионально", "рекомендую",
            "понравилось", "доволен", "довольна", "лучший", "лучшая", "лучшие",
            "спасибо", "благодарен", "благодарна", "вежливый", "вежливая", "вежливые",
            "чисто", "уютно", "комфортно", "качественно", "внимательный", "внимательная",
            "помогли", "помог", "вылечили", "эффективно", "грамотный", "грамотная",
            "приятно", "быстро", "аккуратно", "всё хорошо", "все хорошо", "супер",
            "идеально", "порядочный", "доброжелательный", "отзывчивый",
        ]
        self._negative_words = [
            "ужасно", "отвратительно", "хамят", "хамство", "нахамили", "обманули",
            "развод", "развели", "деньги дерут", "выкачивают", "плохо", "не советую",
            "не рекомендую", "пожалел", "пожалела", "зря", "бесполезно", "больно",
            "больнее", "грязно", "не помогло", "не помогли", "не помог", "ошибка",
            "осложнение", "стало хуже", "испортили", "навредили", "грубый", "грубая",
            "наплевательски", "равнодушно", "не ответили", "пропали", "кинули",
            "дорого", "завышены", "обдираловка", "навязывают", "втюхивают",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        try:
            competitors = task.payload["competitors"]
            sources = task.payload.get("sources", list(self.sources.keys()))

            print(f"[CI Reputation] Начало анализа репутации {len(competitors)} конкурентов")

            # Collect reviews — all competitors in parallel
            reviews_data = await asyncio.gather(*[
                self._collect_reviews(competitor, sources)
                for competitor in competitors
            ])

            # Sentiment analysis
            sentiment_data = await self._analyze_sentiment(reviews_data)

            # Topic analysis
            topic_data = await self._analyze_topics(reviews_data)

            # Calculate reputation scores
            reputation_scores = await self._calculate_reputation_scores(
                reviews_data, sentiment_data, topic_data
            )

            # Identify risks and opportunities
            risks_opportunities = await self._identify_risks_opportunities(
                reputation_scores, sentiment_data, topic_data
            )

            # Generate insights
            insights = await self._generate_insights(
                reputation_scores, sentiment_data, topic_data
            )

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
        """Собрать отзывы конкурента из всех источников параллельно."""
        name = competitor["name"]
        print(f"[CI Reputation] Сбор отзывов: {name}")

        # All sources in parallel for this competitor
        source_tasks = []
        for source in sources:
            if source in self.sources:
                source_tasks.append(self._collect_from_source(competitor, source))

        source_results = await asyncio.gather(*source_tasks)

        reviews = {
            "name": name,
            "sources": {},
            "total_reviews": 0,
            "avg_rating": 0.0
        }

        total_rating = 0.0
        total_count = 0

        for result in source_results:
            source_key = result["source"]
            reviews["sources"][source_key] = result

            if result["count"] and isinstance(result.get("avg_rating"), (int, float)) and result["count"] > 0:
                total_rating += result["avg_rating"] * result["count"]
                total_count += result["count"]

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

        Порядок методов:
        1. SerpAPI (если ключ доступен)
        2. Brave Search (если ключ доступен)
        3. Прямой поиск на платформе
        """
        name = competitor["name"]
        source_info = self.sources[source]

        empty_result = {
            "source": source,
            "source_name": source_info["name"],
            "count": 0,
            "avg_rating": None,
            "sentiment_distribution": None,
            "recent_reviews": [],
            "data_source": "unavailable",
        }

        # Method 1: SerpAPI (rotating client preferred, fallback to direct key)
        if self._serpapi_client or self.serpapi_key:
            result = await self._search_serpapi(name, source_info)
            if result is not None and (result.get("count") or isinstance(result.get("avg_rating"), (int, float))):
                return result

        # Method 2: Brave Search
        if self.brave_api_key:
            result = await self._search_brave(name, source_info)
            if result is not None and (result.get("count") or isinstance(result.get("avg_rating"), (int, float))):
                return result

        # Method 3: DuckDuckGo Lite (free, no API key)
        result = await self._search_duckduckgo(name, source_info)
        if result is not None and (result.get("count") or isinstance(result.get("avg_rating"), (int, float))):
            return result

        # Method 4: Direct platform scraping
        result = await self._scrape_direct(name, source_info, source)
        if result is not None:
            return result

        return empty_result

    async def _search_serpapi(
        self, name: str, source_info: dict
    ) -> Dict[str, Any] | None:
        """Search via SerpAPI with key rotation."""
        query = f"{name} отзывы {source_info['search_query']}"

        # Try rotating client first (handles 429 across keys)
        if self._serpapi_client:
            try:
                results = await self._serpapi_client.search(query)
                if results:
                    return self._extract_rating_from_search(
                        {"organic_results": results}, source_info
                    )
            except Exception as e:
                print(f"[CI Reputation] Rotating SerpAPI error for {name}: {e}")

        # Fallback: direct SerpAPI call with single key
        if self.serpapi_key:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
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
                    return self._extract_rating_from_search(data, source_info)
            except Exception as e:
                print(f"[CI Reputation] SerpAPI error for {name}: {e}")

        return None

    async def _search_brave(
        self, name: str, source_info: dict
    ) -> Dict[str, Any] | None:
        """Search via Brave Search API (free tier, 2000 queries/month)."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                query = f"{name} отзывы рейтинг {source_info['search_query']}"
                headers = {
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self.brave_api_key,
                }
                params = {"q": query, "count": 10, "search_lang": "ru", "country": "RU"}
                resp = await client.get(
                    self.brave_base_url, params=params, headers=headers
                )
                resp.raise_for_status()
                data = resp.json()

                return self._extract_rating_from_brave(data, source_info)
        except Exception as e:
            print(f"[CI Reputation] Brave Search error for {name}: {e}")
            return None

    async def _search_duckduckgo(
        self, name: str, source_info: dict
    ) -> Dict[str, Any] | None:
        """Search via DuckDuckGo Lite — free, no API key, plain HTML."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                query = f"{name} отзывы рейтинг"
                params = {"q": query}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                }
                resp = await client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params=params, headers=headers
                )
                if resp.status_code != 200:
                    return None

                html = resp.text

                # DDG Lite returns results in simple HTML tables:
                # <tr class="result-snippet"><td>snippet</td></tr>
                # <tr class="result-link"><td><a href="url">title</a></td></tr>
                snippets = []
                rating = None
                count = None

                # Extract result snippets
                snippet_matches = re.findall(
                    r'<tr[^>]*class="result-snippet"[^>]*>.*?<td[^>]*>(.*?)</td>.*?</tr>',
                    html, re.DOTALL | re.IGNORECASE
                )
                for s in snippet_matches[:5]:
                    clean = re.sub(r'<[^>]+>', '', s).strip()
                    if clean and len(clean) > 20:
                        snippets.append({"text": clean[:300], "source": "duckduckgo", "date": None})

                # Extract rating from all text (snippets + titles)
                link_matches = re.findall(
                    r'<tr[^>]*class="result-link"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</tr>',
                    html, re.DOTALL | re.IGNORECASE
                )
                all_text = " ".join(s["text"] for s in snippets)
                for _, title in link_matches[:10]:
                    all_text += " " + re.sub(r'<[^>]+>', '', title)

                # Extract rating
                rating_match = re.search(
                    r'(?:рейтинг|rating|оценка)\s*(\d+[.,]\d+)', all_text, re.IGNORECASE
                )
                if not rating_match:
                    rating_match = re.search(
                        r'(\d+[.,]\d+)\s*(?:из\s*5|/5|★)', all_text
                    )
                if rating_match:
                    rating = float(rating_match.group(1).replace(",", "."))

                # Extract review count
                count_match = re.search(
                    r'(\d+)\s*(?:отзыв|отзыва|отзывов|review)', all_text, re.IGNORECASE
                )
                if count_match:
                    count = int(count_match.group(1))

                if rating or count or snippets:
                    # Try text-based sentiment first, fall back to rating estimate
                    text_sentiment = self._analyze_text_sentiment(snippets)
                    if text_sentiment:
                        sentiment_dist = text_sentiment
                    elif rating and isinstance(rating, (int, float)):
                        sentiment_dist = self._estimate_sentiment_from_rating(rating)
                    else:
                        sentiment_dist = None

                    return {
                        "source": source_info["name"],
                        "source_name": source_info["name"],
                        "count": count,
                        "avg_rating": round(rating, 1) if isinstance(rating, (int, float)) else None,
                        "sentiment_distribution": sentiment_dist,
                        "recent_reviews": snippets,
                        "data_source": "duckduckgo_lite",
                    }

                return None

        except Exception as e:
            print(f"[CI Reputation] DuckDuckGo error for {name}: {e}")
            return None

    async def _scrape_direct(
        self, name: str, source_info: dict, source_key: str
    ) -> Dict[str, Any] | None:
        """Direct platform scraping as last resort."""
        if source_key == "yandex_maps":
            return await self._scrape_yandex_maps(name, source_info)
        elif source_key == "prodoctorov":
            return await self._scrape_prodoctorov(name, source_info)
        elif source_key == "2gis":
            return await self._scrape_2gis(name, source_info)
        return None

    async def _scrape_yandex_maps(
        self, name: str, source_info: dict
    ) -> Dict[str, Any] | None:
        """Search Yandex.Maps directly for org rating."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                # Use Yandex search to find the Maps page
                query = f"{name} яндекс карты"
                url = "https://yandex.ru/search/"
                params = {"text": query, "lr": 213}  # Moscow region
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                }
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    return None

                html = resp.text

                # Extract rating from search snippets (Yandex shows Maps rating in SERP)
                # Pattern: "Рейтинг 4.8" or "★ 4.8" or "4,8 ★"
                rating_match = re.search(
                    r'(?:Рейтинг|рейтинг)\s*(\d+[.,]\d+)', html
                )
                if not rating_match:
                    rating_match = re.search(
                        r'(\d+[.,]\d+)\s*★|★\s*(\d+[.,]\d+)', html
                    )
                if not rating_match:
                    rating_match = re.search(
                        r'"ratingValue"\s*:\s*"(\d+[.,]\d+)"', html
                    )

                rating = None
                if rating_match:
                    rating_str = rating_match.group(1) or rating_match.group(2)
                    if rating_str:
                        rating = float(rating_str.replace(",", "."))

                # Extract review count
                count_match = re.search(
                    r'(\d+)\s*(?:отзыв|отзыва|отзывов)', html
                )
                count = int(count_match.group(1)) if count_match else None

                # Extract review snippets
                snippets = []
                for snippet_match in re.finditer(
                    r'(?:отзыв|отзывы)[^.]*?["«]([^"»]{20,200})["»]',
                    html, re.IGNORECASE
                ):
                    snippets.append({
                        "text": snippet_match.group(1)[:300],
                        "source": "yandex.ru/search",
                        "date": None,
                    })

                if rating or count:
                    sentiment_dist = None
                    if rating and isinstance(rating, (int, float)):
                        if rating >= 4.0:
                            sentiment_dist = {"positive": 70, "negative": 15, "neutral": 15}
                        elif rating >= 3.0:
                            sentiment_dist = {"positive": 40, "negative": 30, "neutral": 30}
                        else:
                            sentiment_dist = {"positive": 20, "negative": 60, "neutral": 20}

                    return {
                        "source": "yandex_maps",
                        "source_name": source_info["name"],
                        "count": count,
                        "avg_rating": round(rating, 1) if rating else None,
                        "sentiment_distribution": sentiment_dist,
                        "recent_reviews": snippets[:5],
                        "data_source": "yandex_search",
                    }

                return None

        except Exception as e:
            print(f"[CI Reputation] Yandex Maps scrape error for {name}: {e}")
            return None

    async def _scrape_prodoctorov(
        self, name: str, source_info: dict
    ) -> Dict[str, Any] | None:
        """Search Prodoctorov directly."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                url = "https://prodoctorov.ru/search/"
                params = {"q": name}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                }
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    return None

                html = resp.text

                # Extract rating from search results
                # Prodoctorov shows rating like "4.5" or "4,5" near clinic name
                rating_match = re.search(
                    r'(?:rating|рейтинг)[^\d]*(\d+[.,]\d+)', html, re.IGNORECASE
                )
                if not rating_match:
                    rating_match = re.search(
                        r'"rating"[^"]*"[^"]*"[^"]*"(\d+[.,]\d+)"', html
                    )

                rating = None
                if rating_match:
                    rating_str = rating_match.group(1)
                    rating = float(rating_str.replace(",", "."))

                count_match = re.search(
                    r'(\d+)\s*(?:отзыв|отзыва|отзывов)', html
                )
                count = int(count_match.group(1)) if count_match else None

                if rating:
                    sentiment_dist = {"positive": 65, "negative": 15, "neutral": 20} if rating >= 4.0 else {"positive": 35, "negative": 35, "neutral": 30}
                    return {
                        "source": "prodoctorov",
                        "source_name": source_info["name"],
                        "count": count,
                        "avg_rating": round(rating, 1),
                        "sentiment_distribution": sentiment_dist,
                        "recent_reviews": [],
                        "data_source": "prodoctorov_search",
                    }

                return None

        except Exception as e:
            print(f"[CI Reputation] Prodoctorov scrape error for {name}: {e}")
            return None

    async def _scrape_2gis(
        self, name: str, source_info: dict
    ) -> Dict[str, Any] | None:
        """Search 2GIS directly."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                url = "https://2gis.ru/moscow/search/"
                params = {"q": name}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                }
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    return None

                html = resp.text

                # 2GIS uses JSON-LD or inline data for ratings
                rating_match = re.search(
                    r'"rating"\s*:\s*(\d+[.,]\d+)', html
                )
                if not rating_match:
                    rating_match = re.search(
                        r'"averageRating"\s*:\s*(\d+[.,]\d+)', html
                    )

                rating = None
                if rating_match:
                    rating_str = rating_match.group(1)
                    rating = float(rating_str.replace(",", "."))

                count_match = re.search(
                    r'"reviewCount"\s*:\s*(\d+)', html
                )
                if not count_match:
                    count_match = re.search(
                        r'(\d+)\s*(?:отзыв|отзыва|отзывов)', html
                    )
                count = int(count_match.group(1)) if count_match else None

                if rating:
                    sentiment_dist = {"positive": 65, "negative": 20, "neutral": 15} if rating >= 4.0 else {"positive": 30, "negative": 40, "neutral": 30}
                    return {
                        "source": "2gis",
                        "source_name": source_info["name"],
                        "count": count,
                        "avg_rating": round(rating, 1),
                        "sentiment_distribution": sentiment_dist,
                        "recent_reviews": [],
                        "data_source": "2gis_search",
                    }

                return None

        except Exception as e:
            print(f"[CI Reputation] 2GIS scrape error for {name}: {e}")
            return None

    def _extract_rating_from_search(
        self, data: dict, source_info: dict
    ) -> Dict[str, Any] | None:
        """Extract rating and review data from SerpAPI response."""
        rating = None
        count = None
        snippets = []

        # Try knowledge graph first (Google's structured data)
        kg = data.get("knowledge_graph", {})
        if kg:
            rating = kg.get("rating")
            count = kg.get("reviews_count") or kg.get("rating_count")

        # Extract snippets from organic results
        for result in data.get("organic_results", [])[:5]:
            snippet = result.get("snippet", "")
            if snippet:
                snippets.append({
                    "text": snippet[:300],
                    "source": result.get("link", ""),
                    "date": None,
                })

        # Try to extract rating from snippets if not in KG
        if rating is None and snippets:
            for s in snippets:
                rating_match = re.search(
                    r'(?:рейтинг|rating|оценка)\s*(\d+[.,]\d+)', s["text"], re.IGNORECASE
                )
                if rating_match:
                    rating = float(rating_match.group(1).replace(",", "."))
                    break

        if rating is None and count is None and not snippets:
            return None

        # Try text-based sentiment first, fall back to rating estimate
        text_sentiment = self._analyze_text_sentiment(snippets)
        if text_sentiment:
            sentiment_dist = text_sentiment
        elif rating and isinstance(rating, (int, float)):
            sentiment_dist = self._estimate_sentiment_from_rating(rating)
        else:
            sentiment_dist = None

        return {
            "source": "serpapi",
            "source_name": source_info["name"],
            "count": count,
            "avg_rating": round(rating, 1) if isinstance(rating, (int, float)) else None,
            "sentiment_distribution": sentiment_dist,
            "recent_reviews": snippets,
            "data_source": "serpapi",
        }

    def _extract_rating_from_brave(
        self, data: dict, source_info: dict
    ) -> Dict[str, Any] | None:
        """Extract rating and review data from Brave Search response."""
        rating = None
        count = None
        snippets = []

        web_results = data.get("web", {}).get("results", [])
        for result in web_results[:10]:
            description = result.get("description", "")
            if description:
                snippets.append({
                    "text": description[:300],
                    "source": result.get("url", ""),
                    "date": None,
                })

                # Try to extract rating from description
                if rating is None:
                    rating_match = re.search(
                        r'(?:рейтинг|rating|оценка)\s*(\d+[.,]\d+)',
                        description, re.IGNORECASE
                    )
                    if rating_match:
                        rating = float(rating_match.group(1).replace(",", "."))

                # Try to extract review count
                if count is None:
                    count_match = re.search(
                        r'(\d+)\s*(?:отзыв|отзыва|отзывов|review|reviews)',
                        description, re.IGNORECASE
                    )
                    if count_match:
                        count = int(count_match.group(1))

        if not snippets:
            return None

        # Try text-based sentiment first, fall back to rating estimate
        text_sentiment = self._analyze_text_sentiment(snippets)
        if text_sentiment:
            sentiment_dist = text_sentiment
        elif rating and isinstance(rating, (int, float)):
            sentiment_dist = self._estimate_sentiment_from_rating(rating)
        else:
            sentiment_dist = None

        return {
            "source": source_info["name"],
            "source_name": source_info["name"],
            "count": count,
            "avg_rating": round(rating, 1) if isinstance(rating, (int, float)) else None,
            "sentiment_distribution": sentiment_dist,
            "recent_reviews": snippets[:5],
            "data_source": "brave_search",
        }

    def _analyze_text_sentiment(self, snippets: list[dict]) -> dict | None:
        """Analyze sentiment from actual review text snippets using keyword matching.

        Returns sentiment_distribution dict or None if insufficient text.
        """
        if not snippets:
            return None

        all_text = " ".join(s.get("text", "") for s in snippets).lower()
        if len(all_text) < 50:
            return None

        positive_count = sum(1 for w in self._positive_words if w in all_text)
        negative_count = sum(1 for w in self._negative_words if w in all_text)

        total_signals = positive_count + negative_count
        if total_signals == 0:
            return None  # No clear sentiment signals

        # Calculate percentages with slight neutral buffer
        positive_pct = round((positive_count / max(total_signals, 1)) * 100)
        negative_pct = round((negative_count / max(total_signals, 1)) * 100)

        # Clamp and distribute remainder to neutral
        neutral_pct = max(5, 100 - positive_pct - negative_pct)

        # Adjust so totals sum to 100
        if positive_pct + negative_pct + neutral_pct > 100:
            excess = positive_pct + negative_pct + neutral_pct - 100
            if positive_pct >= negative_pct:
                positive_pct -= excess
            else:
                negative_pct -= excess

        return {
            "positive": max(positive_pct, 0),
            "negative": max(negative_pct, 0),
            "neutral": max(neutral_pct, 0),
        }

    def _estimate_sentiment_from_rating(self, rating: float) -> dict:
        """Fallback: estimate sentiment distribution from rating with deterministic jitter."""
        # Base distribution by rating bracket
        if rating >= 4.5:
            base_pos, base_neg, base_neu = 75, 10, 15
        elif rating >= 4.0:
            base_pos, base_neg, base_neu = 60, 20, 20
        elif rating >= 3.5:
            base_pos, base_neg, base_neu = 45, 30, 25
        elif rating >= 3.0:
            base_pos, base_neg, base_neu = 35, 40, 25
        elif rating >= 2.0:
            base_pos, base_neg, base_neu = 20, 55, 25
        else:
            base_pos, base_neg, base_neu = 10, 70, 20

        # Deterministic jitter from rating (avoids identical scores, no random import)
        jitter_pos = (hash(str(rating) + "pos") % 17) - 8
        jitter_neg = (hash(str(rating) + "neg") % 17) - 8

        pos = max(5, min(90, base_pos + jitter_pos))
        neg = max(5, min(90, base_neg + jitter_neg))
        neu = max(5, 100 - pos - neg)

        return {"positive": pos, "negative": neg, "neutral": neu}

    async def _analyze_sentiment(
        self,
        reviews_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Провести sentiment analysis для всех конкурентов.

        Uses text-based analysis on real review snippets when available.
        Falls back to rating-based estimation with jitter.
        """
        sentiment_data = []

        for competitor_reviews in reviews_data:
            total_positive = 0.0
            total_negative = 0.0
            total_neutral = 0.0
            total_count = 0
            used_text_analysis = False

            for source_data in competitor_reviews["sources"].values():
                count = source_data.get("count") or 0
                if count == 0:
                    continue

                # Try text-based sentiment first
                recent = source_data.get("recent_reviews", [])
                text_sentiment = self._analyze_text_sentiment(recent) if recent else None

                if text_sentiment:
                    dist = text_sentiment
                    used_text_analysis = True
                else:
                    # Fall back to stored distribution or rating-based estimate
                    dist = source_data.get("sentiment_distribution")
                    if not dist:
                        avg_r = source_data.get("avg_rating")
                        if isinstance(avg_r, (int, float)) and avg_r > 0:
                            dist = self._estimate_sentiment_from_rating(avg_r)

                if not dist:
                    continue

                total_positive += (dist["positive"] / 100) * count
                total_negative += (dist["negative"] / 100) * count
                total_neutral += (dist["neutral"] / 100) * count
                total_count += count

            sentiment_data.append({
                "name": competitor_reviews["name"],
                "total_reviews": int(total_count),
                "sentiment": {
                    "positive": round((total_positive / total_count) * 100, 1) if total_count > 0 else 0,
                    "negative": round((total_negative / total_count) * 100, 1) if total_count > 0 else 0,
                    "neutral": round((total_neutral / total_count) * 100, 1) if total_count > 0 else 0
                },
                "sentiment_score": round((total_positive - total_negative) / total_count, 2) if total_count > 0 else 0,
                "text_analyzed": used_text_analysis,
            })

        print(f"[CI Reputation] Sentiment analysis завершён для {len(sentiment_data)} конкурентов")
        return sentiment_data

    async def _analyze_topics(
        self,
        reviews_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Провести topic analysis через keyword matching."""
        topic_data = []

        for competitor_reviews in reviews_data:
            topics = {}
            all_snippets: List[str] = []

            for source_data in competitor_reviews["sources"].values():
                for review in source_data.get("recent_reviews", []):
                    text = review.get("text", "")
                    if text:
                        all_snippets.append(text.lower())

            for topic_key, topic_name in self.review_topics.items():
                mentions = 0
                for snippet in all_snippets:
                    if self._text_matches_topic(snippet, topic_key):
                        mentions += 1

                topics[topic_key] = {
                    "name": topic_name,
                    "mentions": mentions,
                    "sentiment": None,
                    "confidence": 0.5 if mentions > 0 else 0.0,
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
        keywords = self._topic_keywords.get(topic_key, [])
        return any(kw in text for kw in keywords)

    async def _calculate_reputation_scores(
        self,
        reviews_data: List[Dict[str, Any]],
        sentiment_data: List[Dict[str, Any]],
        topic_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Рассчитать reputation scores для конкурентов."""
        reputation_scores = []

        for i, competitor_reviews in enumerate(reviews_data):
            sentiment = sentiment_data[i]
            avg_rating = competitor_reviews["avg_rating"]
            sentiment_score = sentiment["sentiment_score"]

            # Формула: (avg_rating / 5) * 50 + (sentiment_score + 1) / 2 * 50
            # Use rating if available, otherwise rely solely on sentiment
            if isinstance(avg_rating, (int, float)) and avg_rating > 0:
                reputation_score = round(
                    (avg_rating / 5) * 50 + ((sentiment_score + 1) / 2) * 50,
                    1
                )
            else:
                # No rating data — use sentiment only (score in [-1, 1], map to [0, 100])
                reputation_score = round(((sentiment_score + 1) / 2) * 100, 1)

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
        """Определить репутационные риски и возможности."""
        risks = []
        opportunities = []

        for i, score_data in enumerate(reputation_scores):
            sentiment = sentiment_data[i]
            sentiment_negative = sentiment["sentiment"]["negative"]
            sentiment_total = sentiment["total_reviews"]

            if sentiment_total > 0 and sentiment_negative > 20:
                risks.append({
                    "type": "high_negative_sentiment",
                    "competitor": score_data["name"],
                    "negative_pct": sentiment_negative,
                    "description": f"{score_data['name']} имеет {sentiment_negative}% негативных отзывов"
                })

            # Opportunities from topic weaknesses
            topics = topic_data[i]["topics"]
            for topic_key, topic_item in topics.items():
                if topic_item.get("sentiment") is None:
                    continue
                if topic_item["sentiment"].get("negative", 0) > 30:
                    opportunities.append({
                        "type": "competitor_weakness",
                        "competitor": score_data["name"],
                        "topic": topic_item["name"],
                        "negative_pct": topic_item["sentiment"]["negative"],
                        "description": f"{score_data['name']} получает критику по '{topic_item['name']}' ({topic_item['sentiment']['negative']}% негатива)"
                    })

        print(f"[CI Reputation] Найдено {len(risks)} рисков и {len(opportunities)} возможностей")
        return {"risks": risks, "opportunities": opportunities}

    async def _generate_insights(
        self,
        reputation_scores: List[Dict[str, Any]],
        sentiment_data: List[Dict[str, Any]],
        topic_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Сгенерировать инсайты о репутации рынка."""
        if not reputation_scores:
            return {
                "market_avg_reputation": 0,
                "market_avg_sentiment": {"positive": 0, "negative": 0},
                "best_reputation": None,
                "worst_reputation": None,
                "reputation_spread": 0
            }

        avg_reputation = round(
            sum(s["reputation_score"] for s in reputation_scores) / len(reputation_scores), 1
        )
        avg_positive = round(
            sum(s["sentiment"]["positive"] for s in sentiment_data) / len(sentiment_data), 1
        )
        avg_negative = round(
            sum(s["sentiment"]["negative"] for s in sentiment_data) / len(sentiment_data), 1
        )

        best = max(reputation_scores, key=lambda x: x["reputation_score"])
        worst = min(reputation_scores, key=lambda x: x["reputation_score"])

        return {
            "market_avg_reputation": avg_reputation,
            "market_avg_sentiment": {"positive": avg_positive, "negative": avg_negative},
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

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        import os as _os
        _os.makedirs("AIM/data", exist_ok=True)
        output_file = "AIM/data/ci-reputation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"[CI Reputation] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        return [
            "review_collection",
            "sentiment_analysis",
            "topic_analysis",
            "reputation_scoring",
            "risk_identification",
            "opportunity_identification"
        ]
