"""Review collector for Russian platforms: Yandex Maps, ProDoctorov.

Uses Playwright (headless Chromium) because both platforms are JS-rendered
SPAs that block plain HTTP requests with CSRF/challenge mechanisms.

Aggregates ratings and review counts from platforms where Russian
patients actually leave reviews. Google Maps reviews are only ~20-30%
of total reviews for Russian medical clinics.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class PlatformReviews:
    """Review data from a single platform."""
    platform: str  # "yandex_maps" | "prodoctorov"
    url: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    error: str = ""


@dataclass
class AggregatedReviews:
    """Reviews aggregated across all platforms."""
    company_name: str
    platforms: list[PlatformReviews] = field(default_factory=list)
    total_reviews: int = 0
    avg_rating: float = 0.0

    def best_platform(self) -> Optional[PlatformReviews]:
        """Platform with the most reviews (most representative)."""
        if not self.platforms:
            return None
        return max(self.platforms, key=lambda p: p.reviews_count)


# ---------------------------------------------------------------------------
# Review collector (Playwright-based)
# ---------------------------------------------------------------------------


class ReviewCollector:
    """Collects reviews from Russian platforms for a given company.

    Uses Playwright headless Chromium because Yandex Maps and ProDoctorov
    are JS-rendered SPAs with CSRF protection that block plain HTTP.

    Usage::

        collector = ReviewCollector()
        await collector.start()
        result = await collector.collect("Юцковская", "Москва")
        print(f"Total reviews: {result.total_reviews}")
        await collector.close()
    """

    _YANDEX_SEARCH_URL = "https://yandex.ru/maps/213/moscow/?text={query}"
    _PRODOCTOROV_SEARCH_URL = "https://prodoctorov.ru/{city}/lpu/?search={query}"

    def __init__(self, timeout: float = 15.0, headless: bool = True) -> None:
        self._timeout = timeout
        self._headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._started = False

    async def start(self) -> None:
        """Launch browser (call once, reuse across multiple collect() calls)."""
        if self._started:
            return
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )
        self._started = True

    async def close(self) -> None:
        """Close browser and clean up resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._started = False

    async def _ensure_started(self) -> None:
        if not self._started:
            await self.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect(self, company_name: str, city: str = "Москва") -> AggregatedReviews:
        """Collect reviews from all platforms for a company."""
        await self._ensure_started()

        yandex_result, prodoctors_result = await asyncio.gather(
            self._search_yandex(company_name, city),
            self._search_prodoctorov(company_name, city),
            return_exceptions=True,
        )

        platforms: list[PlatformReviews] = []
        if isinstance(yandex_result, PlatformReviews):
            platforms.append(yandex_result)
        elif isinstance(yandex_result, Exception):
            platforms.append(PlatformReviews(platform="yandex_maps", error=str(yandex_result)[:200]))
        # None = not found, silently skip

        if isinstance(prodoctors_result, PlatformReviews):
            platforms.append(prodoctors_result)
        elif isinstance(prodoctors_result, Exception):
            platforms.append(PlatformReviews(platform="prodoctorov", error=str(prodoctors_result)[:200]))
        # None = not found, silently skip

        total = sum(p.reviews_count for p in platforms)
        ratings = [p.rating for p in platforms if p.rating > 0]
        avg = sum(ratings) / len(ratings) if ratings else 0.0

        return AggregatedReviews(
            company_name=company_name,
            platforms=platforms,
            total_reviews=total,
            avg_rating=round(avg, 1),
        )

    # ------------------------------------------------------------------
    # Yandex Maps (Playwright)
    # ------------------------------------------------------------------

    async def _search_yandex(
        self, company_name: str, city: str
    ) -> Optional[PlatformReviews]:
        """Search Yandex Maps via Playwright and extract rating/reviews."""
        from urllib.parse import quote

        query = quote(f"{company_name} {city}")
        url = self._YANDEX_SEARCH_URL.format(query=query)

        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self._timeout * 1000)

            # Wait for search results — the sidebar with organization card
            try:
                await page.wait_for_selector(
                    ".search-business-card-view__title, .card-title-view__title, "
                    ".business-card-view__title, [class*='business-card']",
                    timeout=10000,
                )
            except Exception:
                # Results might be in a different format or not found
                pass

            # Give JS a moment to render
            await asyncio.sleep(2)

            # Verify a real organization card is present (not just ads/sidebar noise)
            has_card = await page.query_selector(
                "[class*='business-card'], [class*='business-summary-rating']"
            )
            if not has_card:
                return None

            # Extract rating and review count from the page
            rating = await self._extract_yandex_rating(page)
            reviews_count = await self._extract_yandex_reviews(page)
            name = await self._extract_yandex_name(page)
            ymap_url = page.url

            if not name and not rating:
                return None

            return PlatformReviews(
                platform="yandex_maps",
                url=ymap_url,
                rating=rating,
                reviews_count=reviews_count,
            )
        except Exception as e:
            logger.warning("Yandex Maps search failed for %s: %s", company_name, e)
            return PlatformReviews(platform="yandex_maps", error=str(e)[:200])
        finally:
            await page.close()

    async def _extract_yandex_rating(self, page) -> float:
        """Extract rating from Yandex Maps organization card.

        Rating text format: "Рейтинг 5,0" inside .business-rating-badge-view__rating
        """
        try:
            el = await page.query_selector(".business-rating-badge-view__rating")
            if el:
                text = await el.text_content()
                if text:
                    num = re.search(r"(\d+[.,]\d+)", text)
                    if num:
                        return float(num.group(1).replace(",", "."))
        except Exception:
            pass
        return 0.0

    async def _extract_yandex_reviews(self, page) -> int:
        """Extract review count from Yandex Maps organization card.

        Yandex has two metrics:
        1. "N оценок" — total ratings (stars, no text)
        2. "N отзывов" — text reviews (more valuable)

        We prefer text reviews count. Falls back to ratings count.
        """
        try:
            # Priority 1: Text reviews count from ".business-reviews-card-view__title"
            # Format: "426 отзывов"
            for selector in [
                ".business-reviews-card-view__title",
                "[class*='reviews-card'] [class*='title']",
                "a[href*='reviews'] [class*='title']",
            ]:
                el = await page.query_selector(selector)
                if el:
                    text = await el.text_content()
                    if text:
                        nums = re.findall(r"\d+", text.replace(" ", "").replace(" ", ""))
                        if nums:
                            return int(nums[0])

            # Priority 2: "N оценок" from the rating badge
            el = await page.query_selector(
                ".business-summary-rating-badge-view__rating-and-stars"
            )
            if el:
                text = await el.text_content()
                if text:
                    # Format: "Рейтинг 5,0735 оценок"
                    match = re.search(r"(\d+)\s*оцен", text)
                    if match:
                        return int(match.group(1))
        except Exception:
            pass
        return 0

    async def _extract_yandex_name(self, page) -> str:
        """Extract organization name from Yandex Maps card."""
        try:
            for selector in [
                ".business-card-view__title",
                ".card-title-view__title",
                "h1",
                "[class*='business-card'] h1",
                "[class*='org-name']",
            ]:
                el = await page.query_selector(selector)
                if el:
                    text = await el.text_content()
                    if text and text.strip():
                        return text.strip()
        except Exception:
            pass
        return ""

    # ------------------------------------------------------------------
    # ProDoctorov (Playwright)
    # ------------------------------------------------------------------

    async def _search_prodoctorov(
        self, company_name: str, city: str = "Москва"
    ) -> Optional[PlatformReviews]:
        """Search ProDoctorov via Playwright with search box interaction."""
        city_map = {
            "москва": "moskva",
            "санкт-петербург": "sankt-peterburg",
            "спб": "sankt-peterburg",
            "казань": "kazan",
            "екатеринбург": "ekaterinburg",
            "новосибирск": "novosibirsk",
            "краснодар": "krasnodar",
            "нижний новгород": "nijniy-novgorod",
            "ростов-на-дону": "rostov-na-donu",
        }
        city_slug = city_map.get(city.lower(), "moskva")

        page = await self._context.new_page()
        try:
            # Step 1: Navigate to city listing page
            await page.goto(
                f"https://prodoctorov.ru/{city_slug}/lpu/",
                wait_until="domcontentloaded",
                timeout=self._timeout * 1000,
            )

            # Step 2: Type company name into search box (JS-rendered filtering)
            search_input = await page.query_selector(
                "input[type='search'], input[name*='search'], "
                "input[placeholder*='поиск'], input[placeholder*='Поиск'], "
                "input[class*='search']"
            )
            if search_input:
                await search_input.fill(company_name)
                await asyncio.sleep(2)
            else:
                logger.warning("ProDoctorov: search input not found for %s", company_name)
                return None

            # Step 3: Wait for filtered results
            await asyncio.sleep(2)

            # Step 4: Find clinic link matching company name
            company_lower = company_name.lower()
            clinic_url = None

            links = await page.query_selector_all("a[href*='/lpu/']")
            for link in links:
                text = (await link.text_content()).strip().lower()
                href = await link.get_attribute("href")
                if not text or not href:
                    continue
                if len(text) < 5 or text.isdigit():
                    continue
                if "отзыв" in text or "цен" in text or "₽" in text:
                    continue
                if company_lower in text:
                    clinic_url = f"https://prodoctorov.ru{href.split('#')[0]}"
                    break

            if not clinic_url:
                return None

            # Step 5: Navigate to clinic page to extract rating
            await page.goto(clinic_url, wait_until="domcontentloaded", timeout=self._timeout * 1000)
            await asyncio.sleep(2)

            rating = await self._extract_pd_rating(page)
            reviews_count = await self._extract_pd_reviews(page)

            return PlatformReviews(
                platform="prodoctorov",
                url=clinic_url,
                rating=rating,
                reviews_count=reviews_count,
            )
        except Exception as e:
            logger.warning("ProDoctorov search failed for %s: %s", company_name, e)
            return PlatformReviews(platform="prodoctorov", error=str(e)[:200])
        finally:
            await page.close()

    async def _extract_pd_rating(self, page) -> float:
        """Extract rating from ProDoctorov clinic page.

        ProDoctorov uses a 0-100 scale in meta[itemprop='ratingValue'].
        Display rating is value/20 (e.g. 86/20 = 4.3).
        Also available in .b-common-rating__header as "Рейтинг 4.3".
        """
        try:
            # Method 1: meta itemprop rating (0-100 scale)
            meta_rating = await page.query_selector("meta[itemprop='ratingValue']")
            if meta_rating:
                content = await meta_rating.get_attribute("content")
                if content:
                    val = float(content)
                    # If value > 10, it's on a 0-100 scale
                    if val > 10:
                        return round(val / 20, 1)
                    return val

            # Method 2: .b-common-rating__header "Рейтинг 4.3"
            header = await page.query_selector(".b-common-rating__header")
            if header:
                text = await header.text_content()
                if text:
                    num = re.search(r"(\d+[.,]\d+)", text)
                    if num:
                        return float(num.group(1).replace(",", "."))
        except Exception:
            pass
        return 0.0

    async def _extract_pd_reviews(self, page) -> int:
        """Extract review count from ProDoctorov clinic page.

        Uses meta[itemprop='ratingCount'] as primary source.
        Falls back to text pattern matching.
        """
        try:
            # Method 1: meta itemprop ratingCount
            meta_count = await page.query_selector("meta[itemprop='ratingCount']")
            if meta_count:
                content = await meta_count.get_attribute("content")
                if content and content.isdigit():
                    return int(content)

            # Method 2: "N отзыва(ов)" in body text
            # Look for the largest number next to "отзыв" — likely total
            body_text = await page.text_content("body")
            if body_text:
                matches = re.findall(r"(\d+)\s*отзыв", body_text, re.I)
                if matches:
                    return max(int(m) for m in matches)
        except Exception:
            pass
        return 0


# ---------------------------------------------------------------------------
# Sync wrapper for use with asyncio.to_thread
# ---------------------------------------------------------------------------


class SyncReviewCollector:
    """Synchronous wrapper for ReviewCollector — used in PipelineRunner.

    Creates its own browser instance per collect() call since
    PipelineRunner runs collectors via asyncio.to_thread() which
    can't share the same event loop.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout
        self._collector: Optional[ReviewCollector] = None

    async def _ensure_collector(self) -> ReviewCollector:
        if self._collector is None:
            self._collector = ReviewCollector(timeout=self._timeout)
            await self._collector.start()
        return self._collector

    async def collect(self, company_name: str, city: str = "Москва") -> AggregatedReviews:
        c = await self._ensure_collector()
        return await c.collect(company_name, city)

    async def close(self) -> None:
        if self._collector is not None:
            await self._collector.close()
            self._collector = None
