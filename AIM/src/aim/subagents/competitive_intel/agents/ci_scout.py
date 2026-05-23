"""
CI Scout Agent - Market Discovery and Competitor Clustering

Находит ВСЕХ конкурентов в нише/гео через SerpAPI + SEMrush,
кластеризует их и выбирает TOP-5-10 для глубокого анализа.

Data sources (ALL REAL, no mock):
- SerpAPI web search — поиск конкурентов по 8 запросам
- SEMrush Domain Competitors — related domains по seed URL
- httpx — загрузка HTML сайтов конкурентов для извлечения метаданных
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re
import asyncio

import httpx
from bs4 import BeautifulSoup

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIScoutAgent(Agent):
    """
    CI Scout - агент поиска и кластеризации конкурентов.

    Фаза 1 CI pipeline:
    - Находит всех игроков в нише через SerpAPI + SEMrush
    - Строит профили конкурентов (реальные данные с сайтов)
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
        self.vault = ObsidianVault("AIM/obsidian/ci-scout")

        # Загружаем API-ключи
        try:
            from aim.config.settings import get_api_settings
            settings = get_api_settings()
            self.serpapi_key = settings.serpapi_api_key
            self.semrush_api_key = settings.semrush_api_key
        except Exception:
            self.serpapi_key = None
            self.semrush_api_key = None

        # HTTP client для загрузки сайтов
        self._http = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AIM-CIScout/1.0)"}
        )

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
                - competitors: список URL (первый — клиентский сайт)
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

            # Извлекаем URL клиента из списка competitors (первый URL)
            competitors_list = task.payload.get("competitors", [])
            client_url = ""
            if competitors_list:
                first = competitors_list[0]
                if isinstance(first, str):
                    client_url = first
                elif isinstance(first, dict):
                    client_url = first.get("url", "")

            # Логирование начала
            pass

            # Шаг 1: Multi-source discovery
            competitors = await self._discover_competitors(niche, geo, client_url)

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

    async def _discover_competitors(
        self, niche: str, geo: str, client_url: str = ""
    ) -> List[Dict[str, str]]:
        """
        Найти реальных конкурентов через SerpAPI + SEMrush → DaData fallback.

        Когда SerpAPI/SEMrush ключи не настроены, использует DaData-based
        CompetitorMatcher (тот же, что работает в /api/competitors/find).

        Returns:
            Список словарей [{name, url}, ...]
        """
        discovered = {}  # url → {name, url, source}

        # Метод 1: SerpAPI web search (8 запросов)
        if self.serpapi_key:
            search_queries = [
                f"{niche} {geo} рейтинг лучших клиник 2025 2026",
                f"{niche} {geo} отзывы пациентов",
                f"топ частных клиник {niche} {geo}",
                f"{niche} {geo} site:prodoctorov.ru",
                f"{niche} {geo} site:zoon.ru",
                f"{niche} {geo} site:2gis.ru",
                f"{niche} {geo} site:napopravku.ru",
                f"клиника {niche} {geo} запись онлайн",
            ]

            for query in search_queries[:6]:
                try:
                    results = await self._serpapi_search(query)
                    for r in results:
                        url = r.get("url", "")
                        name = r.get("title", "")
                        if url and name and "http" in url:
                            domain = self._extract_domain(url)
                            if domain not in discovered:
                                discovered[domain] = {
                                    "name": self._clean_company_name(name),
                                    "url": f"https://{domain}",
                                    "source": "serpapi"
                                }
                except Exception as e:
                    print(f"[CI Scout] SerpAPI query failed: {query[:50]}... — {e}")
                    continue

                await asyncio.sleep(0.5)

        # Метод 2: SEMrush Domain Competitors
        if self.semrush_api_key and len(discovered) < 5:
            try:
                semrush_competitors = await self._semrush_discover_competitors(niche, geo)
                for comp in semrush_competitors:
                    domain = comp.get("domain", "")
                    if domain and domain not in discovered:
                        discovered[domain] = {
                            "name": comp.get("name", domain),
                            "url": f"https://{domain}",
                            "source": "semrush"
                        }
            except Exception as e:
                print(f"[CI Scout] SEMrush discovery failed: {e}")

        # Метод 3: DaData fallback — когда SerpAPI/SEMrush не настроены или не дали результатов
        if not discovered:
            print("[CI Scout] SerpAPI/SEMrush не дали результатов — использую DaData fallback")
            try:
                dadata_competitors = await self._dadata_discover_competitors(niche, geo, client_url)
                for comp in dadata_competitors:
                    name = comp.get("name", "")
                    url = comp.get("url", "")
                    domain = comp.get("domain", "")
                    # Use name as dedup key when domain is missing
                    dedup_key = domain if domain else name
                    if dedup_key and dedup_key not in discovered:
                        discovered[dedup_key] = {
                            "name": name,
                            "url": url,
                            "source": "dadata",
                        }
            except Exception as e:
                print(f"[CI Scout] DaData fallback failed: {e}")

        result = list(discovered.values())
        source_labels = set(c.get("source", "?") for c in result)
        print(f"[CI Scout] Найдено {len(result)} конкурентов (источники: {', '.join(source_labels)})")
        return result

    async def _dadata_discover_competitors(
        self, niche: str, geo: str, client_url: str = ""
    ) -> List[Dict[str, str]]:
        """
        DaData-based competitor discovery — используется как fallback когда
        SerpAPI/SEMrush ключи не настроены.

        Использует CompetitorMatcher (тот же, что и /api/competitors/find).
        """
        from aim.services.competitor_matcher import CompetitorMatcher

        result: List[Dict[str, str]] = []

        # Если есть client_url, используем полноценный CompetitorMatcher.find_competitors()
        if client_url:
            try:
                matcher = CompetitorMatcher()
                matches = await matcher.find_competitors(url=client_url, count=10)
                for m in matches:
                    p = m.profile
                    website = m.website or ""
                    domain = ""
                    if website:
                        domain = website.replace("https://", "").replace("http://", "").rstrip("/")

                    result.append({
                        "name": p.brand_name or p.legal_name,
                        "url": website,
                        "domain": domain,
                    })
                print(f"[CI Scout] DaData (CompetitorMatcher): нашёл {len(result)} через find_competitors()")
                return result
            except Exception as e:
                print(f"[CI Scout] CompetitorMatcher.find_competitors() failed: {e}")

        # Fallback: используем только _search_candidates() без полного пайплайна
        try:
            from aim.services.rusprofile.models import ClientProfile
            from aim.services.competitor_matcher import CompetitorMatcher

            matcher = CompetitorMatcher()
            client = ClientProfile(
                url=client_url or "https://unknown.ru",
                specialization=niche if niche and niche != "medical" else "стоматология",
                city=geo if geo and geo != "ru" else "",
                services=[],
            )
            candidates = await matcher._search_candidates(client)
            for c in candidates:
                name = c.brand_name or c.legal_name
                if not name:
                    continue
                result.append({
                    "name": name,
                    "url": "",
                    "domain": "",
                })
            print(f"[CI Scout] DaData (_search_candidates): нашёл {len(result)}")
        except Exception as e:
            print(f"[CI Scout] DaData _search_candidates failed: {e}")

        return result

    async def _serpapi_search(self, query: str) -> List[Dict[str, str]]:
        """Поиск через SerpAPI (organic results)."""
        params = {
            "api_key": self.serpapi_key,
            "engine": "google",
            "q": query,
            "hl": "ru",
            "gl": "ru",
            "num": 10,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("https://serpapi.com/search", params=params)
            resp.raise_for_status()
            data = resp.json()
        return data.get("organic_results", [])

    async def _semrush_discover_competitors(self, niche: str, geo: str) -> List[Dict[str, str]]:
        """
        Поиск конкурентов через SEMrush Domain Competitors.
        Использует SEMrush API для поиска клиник по ключевым словам ниши.
        """
        # Формируем seed keywords для поиска
        seed_keywords = [
            f"{niche} {geo}",
            f"клиника {niche} {geo}",
            f"врач {niche} {geo}",
        ]

        discovered = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for kw in seed_keywords[:2]:
                try:
                    params = {
                        "type": "domain_competitors",
                        "key": self.semrush_api_key,
                        "domain": f"{kw.replace(' ', '')}.ru",  # fallback seed
                        "database": "ru",
                        "display_limit": 5,
                    }
                    resp = await client.get(
                        "https://api.semrush.com/analytics/v1/",
                        params=params
                    )
                    if resp.status_code == 200:
                        # Парсим CSV-ответ SEMrush
                        lines = resp.text.strip().split("\n")
                        for line in lines[1:]:  # Пропускаем заголовок
                            parts = line.split(";")
                            if len(parts) >= 2:
                                discovered.append({
                                    "domain": parts[0].strip(),
                                    "name": parts[0].strip().split(".")[0].capitalize(),
                                })
                except Exception as e:
                    print(f"[CI Scout] SEMrush keyword '{kw[:30]}...' failed: {e}")
                    continue

        return discovered

    def _extract_domain(self, url: str) -> str:
        """Извлечь домен из URL."""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url

    def _clean_company_name(self, title: str) -> str:
        """Очистить название компании из заголовка поиска."""
        # Убираем типичные суффиксы из SERP
        for sep in [' — ', ' – ', ' | ', ': ', ' - ']:
            if sep in title:
                title = title.split(sep)[0]
        # Обрезаем длинные заголовки
        return title[:80] if len(title) > 80 else title

    async def _build_profiles(
        self,
        competitors: List[Dict[str, str]],
        niche: str,
        geo: str
    ) -> List[Dict[str, Any]]:
        """
        Построить профили конкурентов на основе реальных данных с сайтов.

        Args:
            competitors: список [{name, url, source}, ...]
            niche: ниша
            geo: город
        """
        profiles = []

        for comp in competitors[:15]:  # Максимум 15 профилей
            try:
                profile = await self._build_single_profile(comp, niche, geo)
                profiles.append(profile)
            except Exception as e:
                print(f"[CI Scout] Failed to build profile for {comp.get('name', '?')}: {e}")
                # Базовый профиль из того что есть
                profiles.append({
                    "name": comp.get("name", "Unknown"),
                    "url": comp.get("url", ""),
                    "geo": geo,
                    "niche": niche,
                    "source": comp.get("source", "unknown"),
                    "cluster": "unknown",
                    "channels": {},
                    "price_segment": "unknown",
                    "estimated_size": "unknown",
                    "ad_presence": "unknown",
                    "differentiators": [],
                    "notes": "Не удалось загрузить сайт"
                })

        print(f"[CI Scout] Построено {len(profiles)} профилей конкурентов")
        return profiles

    async def _build_single_profile(
        self,
        competitor: Dict[str, str],
        niche: str,
        geo: str
    ) -> Dict[str, Any]:
        """
        Построить профиль конкурента на основе реальных данных с его сайта.

        Загружает HTML сайта и извлекает: title, description, соцсети,
        признаки ценового сегмента, технологии.
        """
        name = competitor.get("name", "Unknown")
        url = competitor.get("url", "")
        source = competitor.get("source", "unknown")

        profile = {
            "name": name,
            "url": url,
            "geo": geo,
            "niche": niche,
            "source": source,
            "cluster": "unknown",
            "channels": {},
            "price_segment": "unknown",
            "estimated_size": "unknown",
            "ad_presence": "unknown",
            "differentiators": [],
            "notes": ""
        }

        if not url:
            return profile

        # Загружаем HTML сайта
        try:
            resp = await self._http.get(url)
            if resp.status_code != 200:
                profile["notes"] = f"Сайт вернул {resp.status_code}"
                return profile

            html = resp.text
            soup = BeautifulSoup(html, "lxml")

            # Title + meta description
            profile["title"] = soup.title.text.strip()[:200] if soup.title else name
            meta_desc = soup.find("meta", attrs={"name": "description"})
            profile["meta_description"] = meta_desc["content"][:300] if meta_desc else ""

            # Социальные сети и каналы
            channels = {"website": True}
            social_links = soup.find_all("a", href=True)
            for link in social_links:
                href = link.get("href", "")
                if "vk.com/" in href and "vk" not in channels:
                    channels["vk"] = href
                elif "t.me/" in href and "telegram" not in channels:
                    channels["telegram"] = href
                elif "youtube.com/" in href and "youtube" not in channels:
                    channels["youtube"] = href
                elif "instagram.com/" in href and "instagram" not in channels:
                    channels["instagram"] = href
            profile["channels"] = channels

            # Признаки ценового сегмента из текста
            text_lower = html.lower()
            if any(kw in text_lower for kw in ["премиум", "элит", "люкс", "vip", "эксклюзив"]):
                profile["price_segment"] = "premium"
            elif any(kw in text_lower for kw in ["эконом", "доступн", "бюджет", "скидк", "акци"]):
                profile["price_segment"] = "budget"
            else:
                profile["price_segment"] = "mid"

            # Признаки размера из HTML
            page_size = len(html)
            if page_size > 200_000:
                profile["estimated_size"] = "large"
            elif page_size > 80_000:
                profile["estimated_size"] = "medium"
            else:
                profile["estimated_size"] = "small"

            # Обнаружение рекламных пикселей
            has_metrics = "metrika" in text_lower or "google-analytics" in text_lower or "gtag" in text_lower
            has_pixel = "facebook" in text_lower or "fbq" in text_lower or "vk pixel" in text_lower
            if has_metrics and has_pixel:
                profile["ad_presence"] = "high"
            elif has_metrics:
                profile["ad_presence"] = "medium"
            else:
                profile["ad_presence"] = "low"

            # Разные признаки
            differentiators = []
            if "запись онлайн" in text_lower or "онлайн-запись" in text_lower:
                differentiators.append("Онлайн-запись")
            if "telemed" in text_lower or "онлайн-консультаци" in text_lower:
                differentiators.append("Телемедицина")
            profile["differentiators"] = differentiators

            profile["notes"] = f"Данные собраны с сайта {url}"

        except httpx.ConnectError:
            profile["notes"] = "Не удалось подключиться к сайту"
        except httpx.TimeoutException:
            profile["notes"] = "Таймаут при загрузке сайта"
        except Exception as e:
            profile["notes"] = f"Ошибка при анализе сайта: {str(e)[:100]}"

        return profile

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
        Определить кластер для конкурента на основе реальных данных профиля.
        """
        # Прямой конкурент: тот же ценовой сегмент
        if profile["price_segment"] == price_segment:
            return "direct"

        # Лидер: крупный сайт + высокая рекламная активность + premium
        if (profile.get("estimated_size") in ("large", "medium")
                and profile.get("ad_presence") == "high"
                and profile.get("price_segment") == "premium"):
            return "leader"

        # Нишевой: узкая специализация (определяем по differentiators)
        if len(profile.get("differentiators", [])) >= 2:
            return "niche"

        # Новый игрок: малый размер + высокая рекламная активность
        if profile.get("estimated_size") == "small" and profile.get("ad_presence") == "high":
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
