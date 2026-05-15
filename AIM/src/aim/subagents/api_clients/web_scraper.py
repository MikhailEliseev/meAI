"""
Web Scraper для сбора первичных источников

Функции:
- Извлечение контента с веб-страниц
- Поиск founder interviews, case studies, operator posts
- Извлечение структурированных данных
- Обработка JavaScript-rendered страниц
"""

from typing import Dict, Any, List, Optional
import asyncio
import structlog
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import trafilatura
from datetime import datetime

logger = structlog.get_logger()


class WebScraper:
    """
    Web Scraper для CI Research

    Использует:
    - Playwright для JavaScript-rendered страниц
    - Trafilatura для извлечения основного контента
    - BeautifulSoup для парсинга HTML
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Инициализация браузера"""
        if self._initialized:
            return

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self._initialized = True
        logger.info("web_scraper_initialized")

    async def close(self) -> None:
        """Закрытие браузера"""
        if self.browser:
            await self.browser.close()
        logger.info("web_scraper_closed")

    async def scrape_page(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        timeout: int = 30000,
    ) -> Dict[str, Any]:
        """
        Извлечь контент со страницы

        Args:
            url: URL страницы
            wait_for_selector: CSS селектор для ожидания загрузки
            timeout: Таймаут в миллисекундах

        Returns:
            Extracted content:
            - url: URL страницы
            - title: Заголовок
            - content: Основной текст (cleaned)
            - html: Полный HTML
            - metadata: Метаданные (author, date, etc.)
            - links: Список ссылок
            - images: Список изображений
        """
        if not self._initialized:
            await self.initialize()

        logger.info("scraping_page", url=url)

        try:
            page = await self.browser.new_page()

            # Загрузить страницу
            await page.goto(url, timeout=timeout, wait_until="networkidle")

            # Ждать загрузки контента
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout)

            # Получить HTML
            html = await page.content()
            await page.close()

            # Извлечь основной контент через trafilatura
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=False,
            )

            # Парсинг через BeautifulSoup для метаданных
            soup = BeautifulSoup(html, "html.parser")

            # Заголовок
            title = None
            if soup.title:
                title = soup.title.string
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)

            # Метаданные
            metadata = self._extract_metadata(soup)

            # Ссылки
            links = [
                {
                    "url": a.get("href"),
                    "text": a.get_text(strip=True),
                }
                for a in soup.find_all("a", href=True)
                if a.get("href").startswith("http")
            ]

            # Изображения
            images = [
                {
                    "url": img.get("src"),
                    "alt": img.get("alt", ""),
                }
                for img in soup.find_all("img", src=True)
                if img.get("src").startswith("http")
            ]

            result = {
                "url": url,
                "title": title,
                "content": content,
                "html": html,
                "metadata": metadata,
                "links": links[:50],  # Первые 50 ссылок
                "images": images[:20],  # Первые 20 изображений
                "scraped_at": datetime.now().isoformat(),
            }

            logger.info(
                "page_scraped",
                url=url,
                title=title,
                content_length=len(content) if content else 0,
            )

            return result

        except Exception as e:
            logger.error("scraping_failed", url=url, error=str(e))
            raise

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлечь метаданные из HTML"""
        metadata = {}

        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        # Автор
        author = None
        if "author" in metadata:
            author = metadata["author"]
        elif soup.find("span", class_="author"):
            author = soup.find("span", class_="author").get_text(strip=True)

        # Дата публикации
        published_date = None
        if "article:published_time" in metadata:
            published_date = metadata["article:published_time"]
        elif soup.find("time"):
            published_date = soup.find("time").get("datetime")

        return {
            "author": author,
            "published_date": published_date,
            "description": metadata.get("description"),
            "keywords": metadata.get("keywords"),
            "og_title": metadata.get("og:title"),
            "og_description": metadata.get("og:description"),
            "og_image": metadata.get("og:image"),
        }

    async def search_google(
        self,
        query: str,
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Поиск в Google

        Args:
            query: Поисковый запрос
            num_results: Количество результатов

        Returns:
            List of search results:
            - title: Заголовок
            - url: URL
            - snippet: Сниппет
        """
        if not self._initialized:
            await self.initialize()

        logger.info("searching_google", query=query, num_results=num_results)

        try:
            page = await self.browser.new_page()

            # Google Search
            search_url = f"https://www.google.com/search?q={query}&num={num_results}"
            await page.goto(search_url, wait_until="networkidle")

            # Парсинг результатов
            html = await page.content()
            await page.close()

            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Извлечь результаты поиска
            for g in soup.find_all("div", class_="g"):
                title_elem = g.find("h3")
                link_elem = g.find("a")
                snippet_elem = g.find("div", class_="VwiC3b")

                if title_elem and link_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": link_elem.get("href"),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                    })

            logger.info("google_search_completed", query=query, count=len(results))
            return results

        except Exception as e:
            logger.error("google_search_failed", query=query, error=str(e))
            raise

    async def search_linkedin(
        self,
        company_name: str,
        search_type: str = "posts",
    ) -> List[Dict[str, Any]]:
        """
        Поиск в LinkedIn

        Args:
            company_name: Название компании
            search_type: Тип поиска (posts, people, company)

        Returns:
            List of LinkedIn results
        """
        if not self._initialized:
            await self.initialize()

        logger.info(
            "searching_linkedin",
            company_name=company_name,
            search_type=search_type,
        )

        try:
            page = await self.browser.new_page()

            # LinkedIn Search
            if search_type == "posts":
                search_url = f"https://www.linkedin.com/search/results/content/?keywords={company_name}"
            elif search_type == "people":
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={company_name}"
            else:
                search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"

            await page.goto(search_url, wait_until="networkidle")

            # Парсинг результатов
            html = await page.content()
            await page.close()

            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Извлечь результаты (структура зависит от типа поиска)
            # TODO: Реализовать парсинг для каждого типа

            logger.info(
                "linkedin_search_completed",
                company_name=company_name,
                count=len(results),
            )
            return results

        except Exception as e:
            logger.error(
                "linkedin_search_failed",
                company_name=company_name,
                error=str(e),
            )
            raise

    async def extract_case_study(self, url: str) -> Dict[str, Any]:
        """
        Извлечь структурированные данные из case study

        Args:
            url: URL case study

        Returns:
            Structured case study data:
            - company: Название компании
            - challenge: Проблема
            - solution: Решение
            - results: Результаты (метрики)
            - quotes: Цитаты
        """
        page_data = await self.scrape_page(url)

        # TODO: Использовать LLM для извлечения структурированных данных
        # Пока возвращаем сырые данные

        return {
            "url": url,
            "title": page_data["title"],
            "content": page_data["content"],
            "metadata": page_data["metadata"],
            "extracted_at": datetime.now().isoformat(),
        }
