"""
SEMrush API Client для CI Research Agent

Функции:
- Competitor discovery (Domain Overview, Competitors)
- Keyword research (Keyword Magic Tool)
- Backlink analysis
- Traffic analytics
"""

from typing import List, Dict, Any, Optional
import structlog
from .omni_router import OmniRouter

logger = structlog.get_logger()


class SEMrushClient:
    """
    SEMrush API Client

    API Documentation: https://www.semrush.com/api-documentation/
    """

    def __init__(self, omni_router: OmniRouter):
        self.router = omni_router
        self.provider_name = "semrush"

    async def discover_competitors(
        self,
        domain: str,
        database: str = "ru",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Найти конкурентов домена

        API: /analytics/v1/
        Endpoint: domain_competitors
        Cost: 10 API units per request

        Args:
            domain: Домен для анализа (например, "stomatologia.ru")
            database: База данных (ru, us, uk, etc.)
            limit: Количество конкурентов (max 100)

        Returns:
            List of competitors with metrics:
            - domain: Домен конкурента
            - common_keywords: Количество общих ключевых слов
            - se_keywords: Количество ключевых слов конкурента
            - competition_level: Уровень конкуренции (0-1)
            - organic_traffic: Органический трафик
            - organic_cost: Стоимость органического трафика
        """
        logger.info(
            "discovering_competitors",
            domain=domain,
            database=database,
            limit=limit,
        )

        try:
            response = await self.router.request(
                method="GET",
                endpoint="/analytics/v1/",
                params={
                    "type": "domain_competitors",
                    "key": "API_KEY_PLACEHOLDER",  # Omni-Router подставит из headers
                    "domain": domain,
                    "database": database,
                    "display_limit": limit,
                    "export_columns": "Dn,Cr,Np,Or,Ot,Oc",
                },
                preferred_provider=self.provider_name,
            )

            competitors = []
            for row in response.get("data", []):
                competitors.append({
                    "domain": row.get("Dn"),
                    "common_keywords": int(row.get("Cr", 0)),
                    "se_keywords": int(row.get("Np", 0)),
                    "competition_level": float(row.get("Or", 0)),
                    "organic_traffic": int(row.get("Ot", 0)),
                    "organic_cost": float(row.get("Oc", 0)),
                })

            logger.info(
                "competitors_discovered",
                domain=domain,
                count=len(competitors),
            )

            return competitors

        except Exception as e:
            logger.error(
                "competitor_discovery_failed",
                domain=domain,
                error=str(e),
            )
            raise

    async def get_domain_overview(
        self,
        domain: str,
        database: str = "ru",
    ) -> Dict[str, Any]:
        """
        Получить обзор домена

        API: /analytics/v1/
        Endpoint: domain_overview
        Cost: 10 API units per request

        Args:
            domain: Домен для анализа
            database: База данных

        Returns:
            Domain metrics:
            - organic_keywords: Количество органических ключевых слов
            - organic_traffic: Органический трафик
            - organic_cost: Стоимость органического трафика
            - adwords_keywords: Количество платных ключевых слов
            - adwords_traffic: Платный трафик
            - adwords_cost: Стоимость платного трафика
        """
        logger.info("fetching_domain_overview", domain=domain, database=database)

        try:
            response = await self.router.request(
                method="GET",
                endpoint="/analytics/v1/",
                params={
                    "type": "domain_overview",
                    "key": "API_KEY_PLACEHOLDER",
                    "domain": domain,
                    "database": database,
                    "export_columns": "Dn,Rk,Or,Ot,Oc,Ad,At,Ac",
                },
                preferred_provider=self.provider_name,
            )

            data = response.get("data", [{}])[0]
            overview = {
                "domain": data.get("Dn"),
                "rank": int(data.get("Rk", 0)),
                "organic_keywords": int(data.get("Or", 0)),
                "organic_traffic": int(data.get("Ot", 0)),
                "organic_cost": float(data.get("Oc", 0)),
                "adwords_keywords": int(data.get("Ad", 0)),
                "adwords_traffic": int(data.get("At", 0)),
                "adwords_cost": float(data.get("Ac", 0)),
            }

            logger.info("domain_overview_fetched", domain=domain, rank=overview["rank"])
            return overview

        except Exception as e:
            logger.error("domain_overview_failed", domain=domain, error=str(e))
            raise

    async def get_backlinks(
        self,
        domain: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Получить обратные ссылки домена

        API: /analytics/v1/
        Endpoint: backlinks
        Cost: 10 API units per request

        Args:
            domain: Домен для анализа
            limit: Количество ссылок (max 1000)

        Returns:
            List of backlinks:
            - source_url: URL источника
            - target_url: URL цели
            - anchor: Анкор ссылки
            - external_links: Количество внешних ссылок на странице
            - internal_links: Количество внутренних ссылок
            - source_title: Заголовок страницы источника
        """
        logger.info("fetching_backlinks", domain=domain, limit=limit)

        try:
            response = await self.router.request(
                method="GET",
                endpoint="/analytics/v1/",
                params={
                    "type": "backlinks",
                    "key": "API_KEY_PLACEHOLDER",
                    "target": domain,
                    "target_type": "root_domain",
                    "display_limit": limit,
                    "export_columns": "source_url,target_url,anchor,external_num,internal_num,source_title",
                },
                preferred_provider=self.provider_name,
            )

            backlinks = []
            for row in response.get("data", []):
                backlinks.append({
                    "source_url": row.get("source_url"),
                    "target_url": row.get("target_url"),
                    "anchor": row.get("anchor"),
                    "external_links": int(row.get("external_num", 0)),
                    "internal_links": int(row.get("internal_num", 0)),
                    "source_title": row.get("source_title"),
                })

            logger.info("backlinks_fetched", domain=domain, count=len(backlinks))
            return backlinks

        except Exception as e:
            logger.error("backlinks_fetch_failed", domain=domain, error=str(e))
            raise

    async def get_organic_keywords(
        self,
        domain: str,
        database: str = "ru",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Получить органические ключевые слова домена

        API: /analytics/v1/
        Endpoint: domain_organic
        Cost: 10 API units per request

        Args:
            domain: Домен для анализа
            database: База данных
            limit: Количество ключевых слов (max 10000)

        Returns:
            List of keywords:
            - keyword: Ключевое слово
            - position: Позиция в выдаче
            - search_volume: Объём поиска
            - cpc: Цена за клик
            - competition: Конкуренция (0-1)
            - traffic_percent: Процент трафика от этого слова
            - url: URL страницы в выдаче
        """
        logger.info(
            "fetching_organic_keywords",
            domain=domain,
            database=database,
            limit=limit,
        )

        try:
            response = await self.router.request(
                method="GET",
                endpoint="/analytics/v1/",
                params={
                    "type": "domain_organic",
                    "key": "API_KEY_PLACEHOLDER",
                    "domain": domain,
                    "database": database,
                    "display_limit": limit,
                    "export_columns": "Ph,Po,Nq,Cp,Co,Tr,Ur",
                },
                preferred_provider=self.provider_name,
            )

            keywords = []
            for row in response.get("data", []):
                keywords.append({
                    "keyword": row.get("Ph"),
                    "position": int(row.get("Po", 0)),
                    "search_volume": int(row.get("Nq", 0)),
                    "cpc": float(row.get("Cp", 0)),
                    "competition": float(row.get("Co", 0)),
                    "traffic_percent": float(row.get("Tr", 0)),
                    "url": row.get("Ur"),
                })

            logger.info(
                "organic_keywords_fetched",
                domain=domain,
                count=len(keywords),
            )
            return keywords

        except Exception as e:
            logger.error(
                "organic_keywords_fetch_failed",
                domain=domain,
                error=str(e),
            )
            raise
