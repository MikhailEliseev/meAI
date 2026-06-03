"""ServiceCategorizer — автоматическая категоризация услуг на основе prescan.

Правила из categorization_rules.md. Вход: prescan data → Выход: ServiceItem[].
Используется Hermes при подготовке КП (блоки 5 и 10).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

CategoryType = Literal["base", "recommended", "optional", "next_stage"]


@dataclass
class ServiceItem:
    id: str
    name: str
    category: CategoryType
    price: int
    price_note: str | None = None
    deferred_reason: str | None = None
    selected: bool = True
    locked: bool = False


# Стандартный набор услуг со стандартными ценами
DEFAULT_SERVICES: list[ServiceItem] = [
    ServiceItem(
        id="audit",
        name="Аудит + стратегия",
        category="base",
        price=50000,
        price_note="единоразово",
        locked=True,
    ),
    ServiceItem(
        id="seo_rebuild",
        name="Пересборка сайта (Geo+SEO)",
        category="recommended",
        price=80000,
        selected=True,
        locked=False,
    ),
    ServiceItem(
        id="yandex_direct",
        name="Яндекс.Директ",
        category="recommended",
        price=100000,
        price_note="+ бюджет Директа отдельно",
        selected=True,
        locked=False,
    ),
    ServiceItem(
        id="content_blog",
        name="Блог и контент-маркетинг",
        category="optional",
        price=60000,
        selected=False,
        locked=False,
    ),
    ServiceItem(
        id="social_media",
        name="Соцсети (VK + Telegram)",
        category="next_stage",
        price=40000,
        selected=False,
        locked=True,
        deferred_reason=(
            "Сначала закрываем поиск — соцсети усилят результат на этапе 2"
        ),
    ),
]


class ServiceCategorizer:
    """Категоризирует услуги на основе данных prescan."""

    def categorize(self, prescan_data: dict) -> list[ServiceItem]:
        """Принимает prescan-данные, возвращает список ServiceItem с назначенными категориями.

        Правила применяются последовательно:
        seo → ads → content → social → revenue.
        """
        services = deepcopy(DEFAULT_SERVICES)

        self._apply_seo_rules(services, prescan_data)
        self._apply_ads_rules(services, prescan_data)
        self._apply_content_rules(services, prescan_data)
        self._apply_social_rules(services, prescan_data)
        self._apply_revenue_rules(services, prescan_data)

        return services

    def _find(self, services: list[ServiceItem], service_id: str) -> ServiceItem:
        """Find a service by id. Raises ValueError if not found."""
        for s in services:
            if s.id == service_id:
                return s
        raise ValueError(f"Service {service_id!r} not found in DEFAULT_SERVICES")

    def _apply_seo_rules(
        self, services: list[ServiceItem], data: dict
    ) -> None:
        """Apply SEO-based categorization rules.

        - seo_score < 40 OR no sitemap OR no structured_data → recommended
        - seo_score >= 60 → optional
        - 40-59 → recommended
        """
        s = self._find(services, "seo_rebuild")
        seo_score = data.get("seo_score", 0)
        has_sitemap = data.get("has_sitemap", True)
        has_structured_data = data.get("has_structured_data", True)

        if seo_score < 40 or not has_sitemap or not has_structured_data:
            s.category = "recommended"
            s.selected = True
        elif seo_score >= 60:
            s.category = "optional"
            s.selected = False
        else:
            # 40-59
            s.category = "recommended"
            s.selected = True

    def _apply_ads_rules(
        self, services: list[ServiceItem], data: dict
    ) -> None:
        """Apply ads-based categorization rules.

        - No ad campaigns → recommended
        - Has ad campaigns → optional
        """
        s = self._find(services, "yandex_direct")
        has_ads = data.get("has_ads", True)

        if not has_ads:
            s.category = "recommended"
            s.selected = True
        else:
            s.category = "optional"
            s.selected = False

    def _apply_content_rules(
        self, services: list[ServiceItem], data: dict
    ) -> None:
        """Apply content-based categorization rules.

        - total_pages < 10 → optional, not selected (little content)
        - total_pages >= 10 → optional, selected (has base — blog amplifies)
        """
        s = self._find(services, "content_blog")
        total_pages = data.get("total_pages", 0)

        if total_pages < 10:
            s.category = "optional"
            s.selected = False
        else:
            s.category = "optional"
            s.selected = True

    def _apply_social_rules(
        self, services: list[ServiceItem], data: dict
    ) -> None:
        """Apply social media categorization rules.

        - social_links empty or all None → next_stage, locked
        - Active social links → optional, not selected
        """
        s = self._find(services, "social_media")
        social_links = data.get("social_links", {})

        # Check if social_links has any active entries
        has_active_social = bool(social_links) and any(
            v for v in social_links.values() if v
        )

        if not has_active_social:
            s.category = "next_stage"
            s.locked = True
            s.deferred_reason = (
                "Соцсети не ведутся. Сначала закрываем поиск — "
                "соцсети на этапе 2."
            )
        else:
            s.category = "optional"
            s.locked = False
            s.selected = False

    def _apply_revenue_rules(
        self, services: list[ServiceItem], data: dict
    ) -> None:
        """Apply revenue-gap amplification rules.

        If revenue_year < competitor_avg_revenue by >= 20% → all recommended
        services are set to selected=True with deferred_reason annotation.

        Does NOT change categories — only amplifies selection for recommended.
        """
        revenue_year = data.get("revenue_year")
        competitor_avg_revenue = data.get("competitor_avg_revenue")

        if revenue_year is None or competitor_avg_revenue is None:
            return

        if revenue_year <= 0:
            return

        gap = (competitor_avg_revenue - revenue_year) / revenue_year

        if gap >= 0.2:
            gap_pct = gap * 100
            for s in services:
                if s.category == "recommended":
                    s.selected = True
                    existing_reason = s.deferred_reason or ""
                    gap_note = (
                        f"Разрыв с конкурентами: {gap_pct:.0f}% — "
                        f"рекомендуется усилить"
                    )
                    if existing_reason:
                        s.deferred_reason = f"{existing_reason}. {gap_note}"
                    else:
                        s.deferred_reason = gap_note
