"""Yandex Maps web search — Playwright-based competitor discovery.

Uses headless Chromium to navigate Yandex Maps search results
and extract business cards via JavaScript evaluation.

No API key needed — works via the public web interface.
Replaces the broken Organization Search API (search-maps.yandex.ru/v1)
which returns HTTP 403 for keys that only cover the Geocoder product.

Architecture:
  YandexMapsSearchClient (async, singleton)
    └── Playwright headless Chromium (lazy-init, kept alive)
        └── page.evaluate(_EXTRACT_JS) → list[dict]
"""

import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── JavaScript extraction function ──────────────────────────────────
# Battle-tested on Yandex Maps search results (2026-05-22).
# Queries all <li> elements, filters by "Рейтинг" keyword + length > 30,
# extracts name, rating, reviews count, address, category, working status.
#
# Yandex Maps renders search results as <li> elements containing:
#   <a href="/org/...">Name</a>
#   text: "Рейтинг 4.8 • 250 оценок • ул. Примерная, 10 • Категория • Открыто"

_EXTRACT_JS = """
() => {
  const cards = [];
  const seen = new Set();
  const lis = document.querySelectorAll('li');

  // Service/pricing keywords that mark the end of an address.
  // Yandex textContent concatenates address + service + price without spaces,
  // e.g. "ул. Примерная, 10Консультация стоматолога5000 ₽"
  // Stop address capture at medical services, pricing, and promo keywords.
  // Yandex concatenates text without spaces: "ул. X, 5Имплант Osstem13500 ₽"
  // The boundary list must cover both root words (Имплант) and full forms (Имплантация).
  const SERVICE_BOUNDARY = /(?:Консультация|Приём|Прием|Удаление|Лечение|Имплант|Осмотр|Диагностика|Протезирование|Отбеливание|Чистка|Гигиена|Исправление|Коррекция|Реставрация|Пломбирование|Анестезия|Рентген|Компьютерная|Художественная|Эстетическая|Профессиональная|Керамическая|Циркониевая|Металлокерамическая|Нейлоновая|Бюгельная|Простое|Сложное|Бесплатная|Бесплатный|Платная|Платный|Съёмный|Несъёмный|Временная|Постоянная|Винир|Люминир|Коронка|Вкладка|Наложение|Снятие|Шинирование|Кюретаж|Пародонтология|Эндодонтия|Стоматология|Косметология|Акция|Скидка|Подарок|Рассрочка|Кредит|Онлайн|Запись|Цена|Стоимость|Прайс|Открыто|Закрыто|Круглосуточно|₽)/i;

  lis.forEach(li => {
    const text = li.textContent.replace(/\\s+/g, ' ').trim();
    if (/^\\d+$/.test(text) || text.length < 30) return;
    if (!text.includes('Рейтинг')) return;
    const orgLink = li.querySelector('a[href*="/org/"]');
    if (!orgLink) return;
    const url = orgLink.getAttribute('href') || '';
    if (url.includes('/gallery/') || url.includes('/reviews/')) return;
    const name = orgLink.textContent.trim();
    if (!name || name === 'Фото' || name.length < 2) return;
    if (seen.has(url)) return;
    seen.add(url);

    const ratingMatch = text.match(/Рейтинг\\s*(\\d+[,.]\\d+)/);
    const rating = ratingMatch ? parseFloat(ratingMatch[1].replace(',', '.')) : null;
    const ratingsMatch = text.match(/(\\d{2,5})\\s*оцен/);
    const ratingsCount = ratingsMatch ? parseInt(ratingsMatch[1]) : null;

    // Extract address: match street-type prefix + everything up to a service keyword or price.
    // Captures "ул. Примерная, 10, этаж 1" from "ул. Примерная, 10, этаж 1Консультация..."
    let address = '';
    const addrMatch = text.match(
      /(?:ул\\.|улица|пер\\.|переулок|пр\\.|пр-т|проспект|бульвар|б-р|шоссе|наб\\.|набережная|площадь|пл\\.|проезд|тупик)\\s*[^.]*?\\.?\\s*\\d+[^·]*/i
    );
    if (addrMatch) {
      let raw = addrMatch[0];
      // Truncate at first service/pricing keyword
      const boundaryIdx = raw.search(SERVICE_BOUNDARY);
      if (boundaryIdx > 0) {
        raw = raw.substring(0, boundaryIdx);
      }
      // Remove trailing price: "5000 ₽", "от 5000 ₽"
      raw = raw.replace(/\\d+\\s*₽.*$/, '');
      // Clean trailing punctuation and whitespace
      raw = raw.replace(/[,\\s]+$/, '');
      // If too short (just "ул." with no number), skip
      if (raw.length > 5 && /\\d/.test(raw)) {
        address = raw.trim();
      }
    }

    const catLink = li.querySelector('a[href*="/category/"]');
    const category = catLink ? catLink.textContent.trim() : '';
    const statusMatch = text.match(/(Открыто|Закрыто|Круглосуточно)/);
    const workingStatus = statusMatch ? statusMatch[1] : '';

    // Website: find external link (not yandex /org/, /category/, /gallery/, /reviews/)
    let website = null;
    const allLinks = li.querySelectorAll('a[href]');
    allLinks.forEach(a => {
      if (website) return;  // already found
      const h = a.getAttribute('href') || '';
      if (!h || h.startsWith('/') || h.includes('yandex.ru')) return;
      if (h.includes('/org/') || h.includes('/category/') ||
          h.includes('/gallery/') || h.includes('/reviews/')) return;
      // Must look like a real website (has a TLD)
      if (/^https?:\\/\\/[^\\s]+\\.[a-z]{2,}/.test(h)) {
        website = h;
      }
    });

    // Coordinates: new Yandex Maps uses ID-based URLs (/org/name/123456/),
    // not coordinate-based (/org/name/37.62,55.76). Try both patterns.
    let lat = null, lon = null;
    const coordMatch = url.match(/(\\d{2}\\.\\d{4,}),\\s*(\\d{2}\\.\\d{4,})/);
    if (coordMatch) { lon = parseFloat(coordMatch[1]); lat = parseFloat(coordMatch[2]); }

    cards.push({ name, rating, ratings_count: ratingsCount, address, category,
      working_status: workingStatus,
      url: url.startsWith('/') ? 'https://yandex.ru' + url : url,
      website: website,
      lat, lon,
      source: 'yandex_maps_web' });
  });
  return cards;
}
"""

# ── Yandex Maps URL format ──────────────────────────────────────────
# https://yandex.ru/maps/{city_id}/{city_slug}/search/{query}/
YANDEX_MAPS_SEARCH_URL = "https://yandex.ru/maps/{city_id}/{city_slug}/search/{query}/"

# City ID → Yandex Maps internal city ID
# Used to construct proper search URLs with correct region context.
CITY_IDS: dict[str, int] = {
    "москва": 213,
    "санкт-петербург": 2,
    "новосибирск": 65,
    "екатеринбург": 54,
    "казань": 43,
    "нижний новгород": 47,
    "челябинск": 56,
    "самара": 51,
    "омск": 66,
    "ростов-на-дону": 39,
    "уфа": 45,
    "красноярск": 62,
    "пермь": 53,
    "воронеж": 193,
    "волгоград": 38,
    "краснодар": 35,
    "сочи": 239,
    "тюмень": 55,
    "саратов": 194,
    "ижевск": 44,
    "барнаул": 197,
    "ульяновск": 195,
    "иркутск": 63,
    "хабаровск": 76,
    "ярославль": 16,
    "владивосток": 75,
    "махачкала": 28,
    "томск": 67,
    "оренбург": 48,
    "кемерово": 64,
    "новокузнецк": 237,
    "рязань": 11,
    "астрахань": 37,
    "пенза": 49,
    "липецк": 9,
    "тула": 15,
    "киров": 46,
    "чебоксары": 45,  # shares region with уфа, close enough
    "калининград": 22,
    "брянск": 191,
    "курск": 8,
    "тверь": 14,
    "ставрополь": 36,
    "белгород": 4,
    "архангельск": 20,
    "вологда": 21,
    "смоленск": 12,
    "калуга": 6,
    "саранск": 42,
    "владикавказ": 33,
    "грозный": 32,
    "йошкар-ола": 41,
    "мурманск": 23,
    "петрозаводск": 18,
    "сыктывкар": 19,
    "чита": 219,
    "якутск": 74,
}

# Default: Moscow (213)
DEFAULT_CITY_ID = 213


def _get_city_id(city: str) -> int:
    """Map a Russian city name to Yandex Maps internal city ID.

    Handles common variations: "Москва", "москва", "г. Москва".
    Returns DEFAULT_CITY_ID (213 = Moscow) for unknown cities.
    """
    if not city:
        return DEFAULT_CITY_ID

    clean = city.lower().strip()
    # Remove "г." or "г " prefix
    clean = re.sub(r"^г\.?\s*", "", clean)

    if clean in CITY_IDS:
        return CITY_IDS[clean]

    # Partial match: "нижний" → "нижний новгород"
    for known, cid in CITY_IDS.items():
        if clean in known or known in clean:
            return cid

    return DEFAULT_CITY_ID


def _city_to_slug(city: str) -> str:
    """Convert city name to Yandex Maps URL slug.

    "Санкт-Петербург" → "санкт-петербург"
    "Нижний Новгород" → "нижний-новгород"
    "Ростов-на-Дону" → "ростов-на-дону"
    """
    if not city:
        return "moskva"
    clean = re.sub(r"^г\.?\s*", "", city).strip()
    return clean.lower().replace(" ", "-")


# ── YandexMapsSearchClient ──────────────────────────────────────────

class YandexMapsSearchClient:
    """Async Playwright-based client for Yandex Maps web search.

    Uses headless Chromium to navigate to Yandex Maps search results
    and extract business cards from the JS-rendered DOM.

    Usage:
        client = YandexMapsSearchClient()
        orgs = await client.search_organizations(
            query="стоматология",
            city="Москва",
        )
        await client.close()
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        """Lazy-init Playwright + headless Chromium.

        Browser is kept alive between searches — startup takes ~2-3s,
        so we pay this cost once, not per query.
        """
        if self._browser is not None:
            return self._browser

        async with self._lock:
            if self._browser is not None:
                return self._browser

            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            logger.info("YandexMapsSearch: Playwright browser launched")
            return self._browser

    async def close(self):
        """Close browser and stop Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.info("YandexMapsSearch: Playwright browser closed")

    async def search_organizations(
        self,
        query: str,
        city: str = "",
        results: int = 30,
    ) -> list[dict]:
        """Search Yandex Maps for organizations via the public web interface.

        Navigates to https://yandex.ru/maps/{city_id}/{slug}/search/{query}/
        and extracts business cards from the JS-rendered search results.

        Args:
            query: Search query (e.g. "стоматология")
            city: City name in Russian (e.g. "Москва")
            results: Max number of results to return

        Returns:
            List of dicts with keys:
              name, rating, ratings_count, address, category,
              working_status, url, lat, lon, source
        """
        city_id = _get_city_id(city)
        city_slug = _city_to_slug(city) if city else "moskva"
        query_encoded = query.replace(" ", "%20")

        url = YANDEX_MAPS_SEARCH_URL.format(
            city_id=city_id,
            city_slug=city_slug,
            query=query_encoded,
        )

        try:
            browser = await self._ensure_browser()
            page = await browser.new_page()

            try:
                logger.debug("YandexMapsSearch: navigating to %s", url)

                # Use domcontentloaded instead of networkidle — faster and less
                # likely to hang on slow/blocked resources (analytics, maps tiles)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Wait for search results to appear. Yandex Maps can be slow
                # for smaller cities or when under load. Try multiple selectors.
                loaded = False
                for selector in [
                    "li",                              # generic list items
                    ".search-snippet-view",            # old Yandex Maps
                    ".business-card-view",             # new Yandex Maps
                    "[data-testid='snippet']",         # fallback
                ]:
                    try:
                        await page.wait_for_selector(selector, timeout=10000)
                        loaded = True
                        break
                    except Exception:
                        continue

                if not loaded:
                    # Last resort: just wait and hope JS rendered
                    await asyncio.sleep(5)

                # Extra wait for JS hydration
                await asyncio.sleep(2)

                cards = await page.evaluate(_EXTRACT_JS)

                logger.info(
                    "YandexMapsSearch: %d results for '%s' in %s",
                    len(cards), query, city or "default",
                )
                return cards[:results]

            finally:
                await page.close()

        except Exception as e:
            logger.error("YandexMapsSearch failed for query=%s city=%s: %s", query, city, e)
            return []

    async def find_medical_orgs(
        self,
        specialization: str,
        city: str,
    ) -> list[dict]:
        """Find medical organizations for a given specialization and city.

        Uses multiple search terms for broader coverage, same pattern
        as the HTTP API version.
        """
        MEDICAL_SEARCH_TERMS = {
            "стоматология": [
                "стоматология",
                "стоматологическая клиника",
                "стоматологический центр",
            ],
            "косметология": [
                "косметология",
                "косметологический центр",
                "косметологическая клиника",
            ],
            "многопрофильная клиника": [
                "медицинский центр",
                "многопрофильная клиника",
            ],
            "пластическая хирургия": [
                "пластическая хирургия",
                "хирургическая клиника",
            ],
            "офтальмология": [
                "офтальмологическая клиника",
                "офтальмологический центр",
            ],
            "диагностический центр": [
                "диагностический центр",
            ],
            "педиатрия": [
                "детская клиника",
                "педиатрия",
                "детский медицинский центр",
            ],
        }

        terms = MEDICAL_SEARCH_TERMS.get(specialization, ["медицинский центр"])

        all_orgs: list[dict] = []
        seen: set[str] = set()

        for term in terms[:3]:
            batch = await self.search_organizations(query=term, city=city, results=20)
            for org in batch:
                key = org["name"].lower()
                if key not in seen:
                    seen.add(key)
                    all_orgs.append(org)

        return all_orgs


# ── Singleton ────────────────────────────────────────────────────────

_yandex_search: YandexMapsSearchClient | None = None


def get_yandex_search_client() -> YandexMapsSearchClient:
    """Get or create the singleton YandexMapsSearchClient.

    Browser is lazy-initialized on first search, so creating the client
    is cheap — the cost is paid on first search_organizations() call.
    """
    global _yandex_search
    if _yandex_search is None:
        _yandex_search = YandexMapsSearchClient()
    return _yandex_search
