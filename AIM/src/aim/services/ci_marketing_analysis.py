"""CI Marketing Analysis — lightweight competitive intelligence for pre-sale.

Combines our real data (DaData financials, Yandex Maps ratings, OKVED codes)
with the marketing analysis methodology from ai-marketing-claude:
  - SWOT analysis (per-competitor + aggregate)
  - Feature comparison matrix
  - Pricing comparison
  - Positioning map (price × specialization breadth)
  - Steal-worthy tactics
  - Top strategic recommendation

Fast (< 12s): parallel scraping of 3 competitor websites + rule-based analysis.
Deterministic: no LLM calls, only heuristics and pattern matching.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .competitor_matcher import _MULTI_SPEC_SIGNALS
from .rusprofile.models import CompetitorMatch

logger = logging.getLogger(__name__)

# ── Data models ──────────────────────────────────────────────────────


@dataclass
class ScrapedPageData:
    url: str = ""
    title: str = ""
    h1_tags: list[str] = field(default_factory=list)
    meta_description: str = ""
    og_title: str = ""
    og_description: str = ""
    ctas: list[str] = field(default_factory=list)
    pricing_indicators: list[str] = field(default_factory=list)
    trust_signals: list[str] = field(default_factory=list)
    social_links: list[str] = field(default_factory=list)
    services_on_page: list[str] = field(default_factory=list)
    visible_phone: bool = False
    has_online_booking: bool = False
    has_price_page: bool = False
    word_count: int = 0
    fetch_error: str = ""


@dataclass
class SwotQuadrant:
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)


@dataclass
class Tactic:
    source_competitor: str
    tactic_description: str
    why_it_works: str
    how_to_implement: str
    estimated_effort: str  # "Low" | "Medium" | "High"
    expected_impact: str   # "Low" | "Medium" | "High"


@dataclass
class CiAnalysisResult:
    chat_summary: str = ""
    feature_matrix: dict = field(default_factory=dict)
    pricing_comparison: dict = field(default_factory=dict)
    positioning_map: dict = field(default_factory=dict)
    swot_per_competitor: list = field(default_factory=list)
    aggregate_swot: Optional[SwotQuadrant] = None
    steal_worthy_tactics: list = field(default_factory=list)
    top_recommendation: str = ""
    scraped_at: str = ""
    analysis_duration_seconds: float = 0.0
    error: str = ""


# ── Competitor page scraper ──────────────────────────────────────────

# Booking-related patterns in Russian
_BOOKING_PATTERNS = [
    "записаться", "запись онлайн", "онлайн-запись", "запись на приём",
    "записаться на прием", "заказать звонок", "обратный звонок",
]

_PRICE_PAGE_PATTERNS = ["/price", "/prices", "/tseny", "/цены", "прайс"]

_TRUST_PATTERNS = [
    "лицензия", "сертификат", "диплом", "награда", "дипломированный",
    "сертифицированный", "стаж", "опыт работы",
]

_PHONE_REGEX = re.compile(
    r'(\+7|8)\s*\(?\d{3}\)?\s*\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'
)

_SOCIAL_DOMAINS = {
    "vk.com", "instagram.com", "youtube.com", "t.me", "telegram.me",
    "whatsapp.com", "wa.me", "dzen.ru", "zen.yandex.ru",
}


class CompetitorPageScraper:
    """Parallel scraper for competitor websites using httpx + BeautifulSoup."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def scrape_all(self, urls: list[str]) -> list[ScrapedPageData]:
        """Scrape multiple URLs in parallel."""
        tasks = [self._scrape_one(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def _scrape_one(self, raw_url: str) -> ScrapedPageData:
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"
        result = ScrapedPageData(url=url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "ru-RU,ru;q=0.9",
                })
                html = resp.text
        except Exception as e:
            result.fetch_error = str(e)
            logger.warning("ci_marketing: fetch failed for %s: %s", url, e)
            return result

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")

        result.title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Meta tags
        for meta in soup.find_all("meta"):
            name = (meta.get("name") or "").lower()
            prop = (meta.get("property") or "").lower()
            content = meta.get("content", "")
            if name == "description":
                result.meta_description = content
            elif prop == "og:title":
                result.og_title = content
            elif prop == "og:description":
                result.og_description = content

        # H1/H2
        for tag in soup.find_all(["h1", "h2"]):
            text = tag.get_text(strip=True)
            if text:
                if tag.name == "h1":
                    result.h1_tags.append(text)
                # Store H2s up to 10
                if tag.name == "h2" and len(result.h1_tags) < 10:
                    pass  # captured in word_count via full text

        # CTAs (buttons + links with action words)
        cta_keywords = {
            "записаться", "запись", "записаться на приём", "записаться на прием",
            "заказать звонок", "позвонить", "связаться", "оставить заявку",
            "консультация", "бесплатная консультация", "получить консультацию",
            "заказать", "купить", "оформить", "узнать", "подробнее",
        }
        for el in soup.find_all(["a", "button"]):
            text = el.get_text(strip=True).lower()
            if any(kw in text for kw in cta_keywords):
                result.ctas.append(el.get_text(strip=True))

        # Pricing indicators
        pricing_re = re.compile(
            r'\d[\d\s]*\s*(?:₽|руб|р\.|rub)|от\s*\d[\d\s]*|цена|стоимость|прайс',
            re.IGNORECASE,
        )
        page_text = soup.get_text()
        for match in pricing_re.finditer(page_text):
            snippet = match.group().strip()
            if len(snippet) > 3 and snippet not in result.pricing_indicators:
                result.pricing_indicators.append(snippet)
                if len(result.pricing_indicators) >= 10:
                    break

        # Trust signals
        for pattern in _TRUST_PATTERNS:
            if pattern in page_text.lower():
                result.trust_signals.append(pattern)

        # Phone numbers
        result.visible_phone = bool(_PHONE_REGEX.search(page_text))

        # Online booking
        page_lower = page_text.lower()
        result.has_online_booking = any(p in page_lower for p in _BOOKING_PATTERNS)

        # Social links
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            for domain in _SOCIAL_DOMAINS:
                if domain in href:
                    result.social_links.append(domain)
                    break

        # Services on page
        all_spec_keywords: set[str] = set()
        for keywords in _MULTI_SPEC_SIGNALS.values():
            all_spec_keywords.update(keywords)
        for kw in all_spec_keywords:
            if kw in page_lower:
                result.services_on_page.append(kw)

        # Word count
        result.word_count = len(page_text.split())

        # Check for price page
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if any(p in href for p in _PRICE_PAGE_PATTERNS):
                result.has_price_page = True
                break

        return result


# ── Feature mapper ───────────────────────────────────────────────────

class FeatureMapper:
    """Build feature comparison matrix from OKVED + services data."""

    FEATURE_DIMENSIONS = [
        "Терапия", "Хирургия", "Ортопедия", "Имплантация", "Ортодонтия",
        "Отбеливание", "Профгигиена", "Детская стоматология", "Рентген",
        "Косметология", "Пластическая хирургия", "Гинекология", "Урология",
        "Офтальмология", "Педиатрия", "Неврология", "Кардиология",
        "Онлайн-запись", "Цены на сайте", "Телефон на сайте",
        "Соцсети", "Лицензия/сертификаты",
    ]

    @staticmethod
    def build_matrix(
        client_services: list[str],
        competitors: list[CompetitorMatch],
        scraped_pages: list[ScrapedPageData],
    ) -> dict[str, dict[str, bool]]:
        """Build {feature: {client: bool, comp1: bool, comp2: bool, ...}} matrix."""
        matrix: dict[str, dict[str, bool]] = {}

        # Client services set
        client_services_lower = {s.lower() for s in client_services}
        client_services_text = " ".join(client_services).lower()

        for feature in FeatureMapper.FEATURE_DIMENSIONS:
            feature_lower = feature.lower()
            row: dict[str, bool] = {}

            # Client
            row["client"] = (
                feature_lower in client_services_text
                or any(feature_lower in s for s in client_services_lower)
            )

            # Competitors
            for i, match in enumerate(competitors):
                comp_name = match.profile.legal_name or f"comp_{i}"
                # Check services list
                comp_services = {s.lower() for s in match.services}
                comp_services_text = " ".join(match.services).lower()

                has_feature = (
                    feature_lower in comp_services_text
                    or any(feature_lower in s for s in comp_services)
                )

                # Augment with scraped data
                if scraped_pages and i < len(scraped_pages) and not has_feature:
                    page = scraped_pages[i]
                    if feature == "Онлайн-запись":
                        has_feature = page.has_online_booking
                    elif feature == "Цены на сайте":
                        has_feature = page.has_price_page or len(page.pricing_indicators) > 0
                    elif feature == "Телефон на сайте":
                        has_feature = page.visible_phone
                    elif feature == "Соцсети":
                        has_feature = len(page.social_links) > 0
                    elif feature == "Лицензия/сертификаты":
                        has_feature = len(page.trust_signals) > 0

                row[comp_name] = has_feature

            # Only include if at least one party has it
            if any(row.values()):
                matrix[feature] = row

        return matrix


# ── Pricing analyzer ─────────────────────────────────────────────────

# Revenue → price tier mapping
def _revenue_to_tier(revenue: Optional[int]) -> tuple[str, int]:
    """Map annual revenue (RUB) to price tier and numeric level (1-10)."""
    if revenue is None:
        return ("неизвестно", 5)
    if revenue < 15_000_000:
        return ("бюджет", 3)
    if revenue < 40_000_000:
        return ("средний", 5)
    if revenue < 100_000_000:
        return ("выше среднего", 7)
    return ("премиум", 9)


class PricingAnalyzer:
    """Build pricing comparison from DaData revenue data + scraped indicators."""

    @staticmethod
    def build_comparison(
        client_revenue: Optional[int],
        competitors: list[CompetitorMatch],
        scraped_pages: list[ScrapedPageData],
    ) -> dict:
        """
        Returns:
            {
                "tiers": {"Клиент": str, "Comp A": str, ...},
                "levels": {"Клиент": int, "Comp A": int, ...},
                "has_public_prices": {"Клиент": bool, ...},
            }
        """
        tiers: dict[str, str] = {}
        levels: dict[str, int] = {}
        has_prices: dict[str, bool] = {}

        tier_name, level = _revenue_to_tier(client_revenue)
        tiers["Клиент"] = tier_name
        levels["Клиент"] = level
        has_prices["Клиент"] = False

        for i, match in enumerate(competitors):
            name = match.profile.legal_name or f"Конкурент {i+1}"
            tier_name, level = _revenue_to_tier(match.profile.revenue_year)
            tiers[name] = tier_name
            levels[name] = level

            if scraped_pages and i < len(scraped_pages):
                page = scraped_pages[i]
                has_prices[name] = page.has_price_page or len(page.pricing_indicators) > 0
            else:
                has_prices[name] = False

        return {"tiers": tiers, "levels": levels, "has_public_prices": has_prices}


# ── Positioning mapper ───────────────────────────────────────────────

class PositioningMapper:
    """Build positioning map: X = price level, Y = specialization breadth."""

    @staticmethod
    def build_map(
        client_services: list[str],
        competitors: list[CompetitorMatch],
        pricing: dict,
    ) -> dict:
        """
        Returns:
            {name: {"x": int, "y": int, "label": str}}
            x: price level (1-10, from PricingAnalyzer)
            y: specialization breadth (number of distinct OKVED categories, 1-10)
        """
        levels = pricing.get("levels", {})
        pos_map: dict[str, dict] = {}

        # Client
        client_breadth = max(1, min(10, len(client_services) // 2))
        pos_map["Клиент"] = {
            "x": levels.get("Клиент", 5),
            "y": client_breadth,
            "label": "Вы",
        }

        for i, match in enumerate(competitors):
            name = match.profile.legal_name or f"Конкурент {i+1}"
            # Breadth from OKVED diversity
            okved_categories = set()
            if match.profile.okved_main:
                okved_categories.add(match.profile.okved_main[:2])
            for code in match.profile.okved_secondary:
                okved_categories.add(code[:2])
            breadth = max(1, min(10, len(okved_categories) + 1))

            pos_map[name] = {
                "x": levels.get(name, 5),
                "y": breadth,
                "label": f"К{i+1}",
            }

        return pos_map


# ── SWOT engine ──────────────────────────────────────────────────────

class SwotEngine:
    """Rule-based SWOT analysis — deterministic, no LLM."""

    @staticmethod
    def for_competitor(
        client_name: str,
        client_services: list[str],
        client_revenue: Optional[int],
        client_rating: Optional[float],
        competitor: CompetitorMatch,
        scraped: Optional[ScrapedPageData] = None,
    ) -> SwotQuadrant:
        comp = competitor.profile
        comp_name = comp.legal_name or "Конкурент"
        client_svc_set = {s.lower() for s in client_services}
        comp_svc_set = {s.lower() for s in competitor.services}

        strengths: list[str] = []
        weaknesses: list[str] = []
        opportunities: list[str] = []
        threats: list[str] = []

        # ── Strengths (client outperforms competitor) ──
        if client_rating and comp.rating and client_rating > comp.rating:
            strengths.append(f"Рейтинг {client_rating} выше чем у {comp_name} ({comp.rating})")
        elif client_rating and not comp.rating:
            strengths.append(f"У вас есть рейтинг {client_rating}, у {comp_name} нет публичного рейтинга")

        extra_svc = client_svc_set - comp_svc_set
        if extra_svc:
            svc_list = ", ".join(sorted(extra_svc)[:4])
            strengths.append(f"У вас больше услуг: {svc_list}")

        if client_revenue and comp.revenue_year and client_revenue > comp.revenue_year:
            strengths.append("Ваш масштаб (выручка) больше — больше возможностей для инвестиций в маркетинг")

        if scraped and scraped.has_online_booking and not comp_svc_set:
            strengths.append(f"У вас есть онлайн-запись — у {comp_name} нет")

        # ── Weaknesses (competitor outperforms client) ──
        if comp.rating and (not client_rating or comp.rating > (client_rating or 0)):
            weaknesses.append(f"У {comp_name} рейтинг {comp.rating} — выше вашего")

        comp_extra = comp_svc_set - client_svc_set
        if comp_extra:
            svc_list = ", ".join(sorted(comp_extra)[:4])
            weaknesses.append(f"{comp_name} предлагает услуги которых у вас нет: {svc_list}")

        if comp.revenue_year and (not client_revenue or comp.revenue_year > (client_revenue or 0)):
            weaknesses.append(f"{comp_name} крупнее — может позволить больше рекламы")

        if scraped and not scraped.fetch_error:
            if scraped.word_count > 2000:
                weaknesses.append(f"У {comp_name} большой сайт ({scraped.word_count}+ слов) — сильный контент")
            if scraped.social_links:
                platforms = ", ".join(scraped.social_links[:3])
                weaknesses.append(f"{comp_name} активен в соцсетях: {platforms}")

        # ── Opportunities (competitor weaknesses to exploit) ──
        if not scraped or scraped.fetch_error:
            opportunities.append(f"Сайт {comp_name} недоступен или нечитаем — займите их позиции в поиске")
        elif not scraped.has_online_booking:
            opportunities.append(f"{comp_name} без онлайн-записи — выделитесь удобством записи")
        if comp.rating is not None and comp.rating < 4.0:
            opportunities.append(f"Низкий рейтинг {comp_name} ({comp.rating}) — ваша точка роста")
        if not (scraped and scraped.has_price_page) and not (scraped and len(scraped.pricing_indicators) > 3):
            opportunities.append(f"{comp_name} скрывает цены — публикуйте свои, это привлекает пациентов")
        if scraped and len(scraped.trust_signals) < 2:
            opportunities.append("Покажите лицензии и сертификаты — у конкурента их не видно")

        # ── Threats (competitor advantages to watch) ──
        if comp.reviews_count and comp.reviews_count > 20:
            threats.append(f"{comp_name} имеет {comp.reviews_count}+ отзывов — сильная репутация")
        if comp.rating and comp.rating >= 4.5:
            threats.append(f"{comp_name} с рейтингом {comp.rating} — трудно превзойти по качеству")
        if scraped and scraped.has_online_booking:
            threats.append(f"{comp_name} уже предлагает онлайн-запись — не отставайте")
        if comp.revenue_year and comp.revenue_year > 80_000_000:
            threats.append(f"{comp_name} — крупный игрок с большим маркетинговым бюджетом")

        # Ensure at least 3 items per quadrant
        _pad_quadrant(strengths, comp_name, "strength")
        _pad_quadrant(weaknesses, comp_name, "weakness")
        _pad_quadrant(opportunities, comp_name, "opportunity")
        _pad_quadrant(threats, comp_name, "threat")

        return SwotQuadrant(
            strengths=strengths[:4],
            weaknesses=weaknesses[:4],
            opportunities=opportunities[:4],
            threats=threats[:4],
        )

    @staticmethod
    def aggregate(
        client_name: str,
        client_services: list[str],
        competitors: list[CompetitorMatch],
        individual_swots: list[SwotQuadrant],
    ) -> SwotQuadrant:
        """Aggregate SWOT across all competitors."""
        all_s = set()
        all_w = set()
        all_o = set()
        all_t = set()

        for swot in individual_swots:
            all_s.update(swot.strengths)
            all_w.update(swot.weaknesses)
            all_o.update(swot.opportunities)
            all_t.update(swot.threats)

        # Deduplicate and trim
        return SwotQuadrant(
            strengths=list(all_s)[:4],
            weaknesses=list(all_w)[:4],
            opportunities=list(all_o)[:4],
            threats=list(all_t)[:4],
        )


def _pad_quadrant(items: list[str], comp_name: str, quad_type: str) -> None:
    """Ensure at least 3 items in a SWOT quadrant."""
    defaults = {
        "strength": [
            f"Ваш сайт может быть лучше оптимизирован чем у {comp_name}",
            f"Вы лучше знаете локальный рынок чем {comp_name}",
            "Индивидуальный подход к пациентам — ваше преимущество",
        ],
        "weakness": [
            f"{comp_name} уже присутствует на рынке — нужно догонять",
            f"Возможно {comp_name} тратит больше на маркетинг",
            "Вам нужно усилить онлайн-присутствие",
        ],
        "opportunity": [
            "Займите нишу с лучшим сервисом",
            "Сделайте сайт быстрее и удобнее чем у конкурентов",
            "Публикуйте кейсы и отзывы — это привлекает пациентов",
        ],
        "threat": [
            f"{comp_name} может снизить цены",
            f"{comp_name} может усилить рекламу",
            "Рынок может измениться — будьте гибкими",
        ],
    }
    needed = 3 - len(items)
    if needed > 0:
        defaults_list = defaults.get(quad_type, [])
        for i in range(min(needed, len(defaults_list))):
            if defaults_list[i] not in items:
                items.append(defaults_list[i])


# ── Tactic extractor ─────────────────────────────────────────────────

class TacticExtractor:
    """Extract steal-worthy tactics from competitor scraped data."""

    @staticmethod
    def extract(
        competitors: list[CompetitorMatch],
        scraped_pages: list[ScrapedPageData],
        client_services: list[str],
    ) -> list[Tactic]:
        tactics: list[Tactic] = []

        for i, (match, page) in enumerate(zip(competitors, scraped_pages)):
            if page.fetch_error:
                continue

            comp_name = match.profile.legal_name or f"Конкурент {i+1}"

            # Tactic: Online booking
            if page.has_online_booking:
                tactics.append(Tactic(
                    source_competitor=comp_name,
                    tactic_description=f"Онлайн-запись как у {comp_name}",
                    why_it_works="Пациенты ценят удобство: запись 24/7 без звонков",
                    how_to_implement="Добавить виджет онлайн-записи (Яндекс.Записи, Dentune, 1С:Медицина)",
                    estimated_effort="Medium",
                    expected_impact="High",
                ))

            # Tactic: Price transparency
            if page.has_price_page:
                tactics.append(Tactic(
                    source_competitor=comp_name,
                    tactic_description=f"Страница с ценами как у {comp_name}",
                    why_it_works="Прозрачные цены = доверие. Пациенты сравнивают цены до визита.",
                    how_to_implement="Создать /prices с основными услугами и диапазоном цен",
                    estimated_effort="Low",
                    expected_impact="High",
                ))

            # Tactic: Content depth
            if page.word_count > 3000:
                tactics.append(Tactic(
                    source_competitor=comp_name,
                    tactic_description=f"Глубокий контент как у {comp_name} ({page.word_count} слов на сайте)",
                    why_it_works="Больше контента = больше позиций в поиске = больше пациентов",
                    how_to_implement="Добавить страницы по каждой услуге (300-500 слов), блог с ответами на вопросы пациентов",
                    estimated_effort="Medium",
                    expected_impact="Medium",
                ))

            # Tactic: Social presence
            if len(page.social_links) >= 2:
                platforms = ", ".join(page.social_links[:3])
                tactics.append(Tactic(
                    source_competitor=comp_name,
                    tactic_description=f"Активность в соцсетях: {platforms}",
                    why_it_works="Соцсети создают доверие и повторные визиты",
                    how_to_implement="Завести страницы в VK и Telegram, публиковать 2-3 раза в неделю",
                    estimated_effort="Low",
                    expected_impact="Medium",
                ))

        # Deduplicate by tactic_description
        seen: set[str] = set()
        uniq: list[Tactic] = []
        for t in tactics:
            key = t.tactic_description.lower()
            if key not in seen:
                seen.add(key)
                uniq.append(t)

        return uniq[:6]


# ── Report formatter ─────────────────────────────────────────────────

class ReportFormatter:
    """Format analysis results for chat display and file storage."""

    @staticmethod
    def chat_summary(result: CiAnalysisResult) -> str:
        """Compact markdown summary for pre-sale bot (6-8 bullet points)."""
        lines = ["## Анализ конкурентов\n"]

        # Key insight
        feature_matrix = result.feature_matrix
        swot_list = result.swot_per_competitor

        lines.append("### Ключевые выводы:\n")

        # Count features where client is unique
        client_only = 0
        for feature, row in feature_matrix.items():
            client_has = row.get("client", False)
            others_have = any(v for k, v in row.items() if k != "client")
            if client_has and not others_have:
                client_only += 1

        if client_only > 0:
            lines.append(f"- У вас есть **{client_only} уникальных преимуществ**, которых нет у конкурентов")

        # Count features where competitors have them but client doesn't
        client_missing = 0
        for feature, row in feature_matrix.items():
            client_has = row.get("client", False)
            others_have = any(v for k, v in row.items() if k != "client")
            if not client_has and others_have:
                client_missing += 1
        if client_missing > 0:
            lines.append(f"- Конкуренты предлагают **{client_missing} услуг/фич**, которых нет у вас — точки роста")

        # SWOT highlights
        if result.aggregate_swot:
            agg = result.aggregate_swot
            if agg.opportunities:
                lines.append(f"- **Главная возможность:** {agg.opportunities[0]}")
            if agg.strengths:
                lines.append(f"- **Ваше преимущество:** {agg.strengths[0]}")

        # Tactics
        if result.steal_worthy_tactics:
            lines.append("\n### Что взять у конкурентов:\n")
            for i, t in enumerate(result.steal_worthy_tactics[:3], 1):
                lines.append(f"{i}. **{t.tactic_description}** — {t.why_it_works}")

        # Top recommendation
        if result.top_recommendation:
            lines.append(f"\n### Главная рекомендация:\n{result.top_recommendation}")

        return "\n".join(lines)

    @staticmethod
    def full_report_dict(result: CiAnalysisResult) -> dict:
        """Full JSON-serializable report for storage."""
        swot_data = []
        for comp_name, swot in result.swot_per_competitor:
            swot_data.append({
                "competitor": comp_name,
                "strengths": swot.strengths,
                "weaknesses": swot.weaknesses,
                "opportunities": swot.opportunities,
                "threats": swot.threats,
            })

        return {
            "chat_summary": result.chat_summary,
            "feature_matrix": result.feature_matrix,
            "pricing_comparison": result.pricing_comparison,
            "positioning_map": result.positioning_map,
            "swot_per_competitor": swot_data,
            "aggregate_swot": {
                "strengths": result.aggregate_swot.strengths if result.aggregate_swot else [],
                "weaknesses": result.aggregate_swot.weaknesses if result.aggregate_swot else [],
                "opportunities": result.aggregate_swot.opportunities if result.aggregate_swot else [],
                "threats": result.aggregate_swot.threats if result.aggregate_swot else [],
            },
            "steal_worthy_tactics": [
                {
                    "source": t.source_competitor,
                    "tactic": t.tactic_description,
                    "why": t.why_it_works,
                    "how": t.how_to_implement,
                    "effort": t.estimated_effort,
                    "impact": t.expected_impact,
                }
                for t in result.steal_worthy_tactics
            ],
            "top_recommendation": result.top_recommendation,
            "scraped_at": result.scraped_at,
            "duration_seconds": result.analysis_duration_seconds,
        }

    @staticmethod
    def top_recommendation(result: CiAnalysisResult) -> str:
        """Generate single most actionable recommendation."""
        # Priority: tactic with high impact + low effort
        for t in result.steal_worthy_tactics:
            if t.expected_impact == "High" and t.estimated_effort in ("Low", "Medium"):
                return f"Сделайте {t.tactic_description.split(' как')[0].lower()} — {t.why_it_works}"

        # Fallback: first opportunity from aggregate SWOT
        if result.aggregate_swot and result.aggregate_swot.opportunities:
            return result.aggregate_swot.opportunities[0]

        return "Усильте онлайн-присутствие: добавьте онлайн-запись и прозрачные цены на сайт"


# ── Main analyzer ────────────────────────────────────────────────────


class CiMarketingAnalyzer:
    """Orchestrates the full CI marketing analysis pipeline."""

    def __init__(self, timeout: float = 10.0):
        self.scraper = CompetitorPageScraper(timeout=timeout)
        self.feature_mapper = FeatureMapper()
        self.pricing_analyzer = PricingAnalyzer()
        self.positioning_mapper = PositioningMapper()
        self.swot_engine = SwotEngine()
        self.tactic_extractor = TacticExtractor()
        self.formatter = ReportFormatter()

    async def analyze(
        self,
        url: str,
        specialization: str,
        city: str,
        services: list[str],
        competitors: list[CompetitorMatch],
        client_revenue: Optional[int] = None,
        client_rating: Optional[float] = None,
    ) -> CiAnalysisResult:
        """Run full CI marketing analysis.

        Args:
            url: Client clinic website URL
            specialization: Client specialization (e.g. "стоматология")
            city: Client city
            services: Client services list
            competitors: 3 confirmed CompetitorMatch objects
            client_revenue: Estimated client annual revenue
            client_rating: Client rating (if known)
        """
        t0 = time.monotonic()

        # 1. Scrape competitor websites (parallel)
        scrape_urls = [m.website or f"https://{m.profile.legal_name.lower().replace(' ', '-')}.ru"
                       for m in competitors]
        scraped = await self.scraper.scrape_all(scrape_urls)

        # Build competitor name → website map for display
        for i, match in enumerate(competitors):
            if i < len(scraped) and not scraped[i].url:
                scraped[i].url = match.website or ""

        # 2. Feature matrix
        feature_matrix = self.feature_mapper.build_matrix(services, competitors, scraped)

        # 3. Pricing comparison
        pricing = self.pricing_analyzer.build_comparison(client_revenue, competitors, scraped)

        # 4. Positioning map
        pos_map = self.positioning_mapper.build_map(services, competitors, pricing)

        # 5. SWOT per competitor
        swot_per_competitor: list[tuple[str, SwotQuadrant]] = []
        for i, match in enumerate(competitors):
            comp_name = match.profile.legal_name or f"Конкурент {i+1}"
            page = scraped[i] if i < len(scraped) else None
            swot = self.swot_engine.for_competitor(
                client_name=specialization or "Клиент",
                client_services=services,
                client_revenue=client_revenue,
                client_rating=client_rating,
                competitor=match,
                scraped=page,
            )
            swot_per_competitor.append((comp_name, swot))

        # 6. Aggregate SWOT
        aggregate_swot = self.swot_engine.aggregate(
            specialization, services, competitors,
            [s for _, s in swot_per_competitor],
        )

        # 7. Steal-worthy tactics
        tactics = self.tactic_extractor.extract(competitors, scraped, services)

        # 8. Build result
        result = CiAnalysisResult(
            feature_matrix=feature_matrix,
            pricing_comparison=pricing,
            positioning_map=pos_map,
            swot_per_competitor=swot_per_competitor,
            aggregate_swot=aggregate_swot,
            steal_worthy_tactics=tactics,
            scraped_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            analysis_duration_seconds=time.monotonic() - t0,
        )

        # 9. Generate recommendations
        result.top_recommendation = self.formatter.top_recommendation(result)
        result.chat_summary = self.formatter.chat_summary(result)

        logger.info(
            "ci_marketing_analysis: done in %.1fs, %d tactics, %d features",
            result.analysis_duration_seconds,
            len(tactics),
            len(feature_matrix),
        )

        return result
