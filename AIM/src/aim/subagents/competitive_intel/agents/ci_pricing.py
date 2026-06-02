"""
CI Pricing Agent - Pricing Strategy Analysis

Анализирует ценовую стратегию конкурентов:
- Прайс-листы и цены на услуги
- Ценовые сегменты (budget/mid/premium)
- Акции и скидки
- Ценовое позиционирование
- Прозрачность цен
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
import re

import httpx
from bs4 import BeautifulSoup

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIPricingAgent(Agent):
    """CI Pricing - агент анализа ценовой стратегии конкурентов."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-pricing",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-pricing")

        # Price segments
        self.price_segments = {
            "budget": "Бюджетный сегмент",
            "mid": "Средний сегмент",
            "premium": "Премиум сегмент",
            "luxury": "Люкс сегмент"
        }

        # Pricing strategies
        self.pricing_strategies = [
            "penetration",  # Низкие цены для захвата рынка
            "skimming",     # Высокие цены для премиум позиционирования
            "competitive",  # Цены на уровне конкурентов
            "value_based",  # Цены на основе ценности
            "dynamic"       # Динамическое ценообразование
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ ценовой стратегии конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - niche: ниша (опционально)
                - services: список услуг для анализа (опционально)

        Returns:
            TaskResult с анализом цен
        """
        try:
            competitors = task.payload["competitors"]
            niche = task.payload.get("niche", "")
            services = task.payload.get("services", [])

            print(f"[CI Pricing] Начало анализа цен {len(competitors)} конкурентов")

            # Шаг 1: Collect pricing for each competitor
            pricing_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_pricing(competitor, niche, services)
                pricing_profiles.append(profile)

            # Шаг 2: Market pricing analysis
            try:
                market_analysis = await self._analyze_market_pricing(pricing_profiles)
            except Exception as e:
                print(f"[CI Pricing] Ошибка в _analyze_market_pricing: {type(e).__name__}: {e}")
                raise

            # Шаг 3: Identify pricing leaders
            try:
                pricing_leaders = await self._identify_pricing_leaders(pricing_profiles)
            except Exception as e:
                print(f"[CI Pricing] Ошибка в _identify_pricing_leaders: {type(e).__name__}: {e}")
                raise

            # Шаг 4: Price positioning map
            try:
                positioning_map = await self._create_positioning_map(pricing_profiles)
            except Exception as e:
                print(f"[CI Pricing] Ошибка в _create_positioning_map: {type(e).__name__}: {e}")
                raise

            # Шаг 5: Pricing insights
            try:
                insights = await self._generate_pricing_insights(
                    pricing_profiles, market_analysis, pricing_leaders, positioning_map
                )
            except Exception as e:
                print(f"[CI Pricing] Ошибка в _generate_pricing_insights: {type(e).__name__}: {e}")
                raise

            # Шаг 6: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "pricing_profiles": pricing_profiles,
                "market_analysis": market_analysis,
                "pricing_leaders": pricing_leaders,
                "positioning_map": positioning_map,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Pricing] Анализ цен завершён для {len(competitors)} конкурентов")

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
            print(f"[CI Pricing] Ошибка: {e}")
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

    # Russian price patterns
    PRICE_PATTERNS = [
        re.compile(r'(\d[\d\s]{0,7})\s*(?:₽|руб|р\.)', re.IGNORECASE),
        re.compile(r'от\s+(\d[\d\s]{0,7})\s*(?:₽|руб|р\.)', re.IGNORECASE),
        re.compile(r'(\d[\d\s]{0,7})\s*(?:₽|руб|р\.)\s*[-–—]\s*(\d[\d\s]{0,7})', re.IGNORECASE),
    ]

    PRICING_PAGE_PATHS = [
        '/price', '/prices', '/pricing', '/price-list', '/prajs', '/price.html',
        '/prices.html', '/services', '/services/', '/uslugi', '/uslugi/',
        '/stoimost', '/stoimost/', '/tseny', '/tseny/',
        '/cena', '/ceny', '/czeny', '/ceni', '/prajs-list', '/prajs-list/',
        '/price-list/', '/prays', '/prays-list/',
        # Additional Russian medical clinic patterns
        '/nashi-ceny', '/nashi-tseny', '/tseny-na-uslugi',
        '/price-list', '/pricelist', '/skachat-prajs',
        '/stoimost-uslug', '/ceny-na-uslugi', '/price-na-uslugi',
        '/konsultacija', '/priem', '/priyom',
    ]

    PRICING_LINK_KEYWORDS = [
        'цена', 'цены', 'прайс', 'стоимость', 'price', 'pricing',
        'сколько стоит', 'приём', 'прием', 'консультаци',
    ]

    BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    PROMO_KEYWORDS = [
        'скидк', 'акци', 'спецпредложен', 'подар', 'бесплат',
        'рассроч', 'кэшб', 'cashback', 'бонус',
    ]

    async def _find_pricing_url(self, website: str) -> Optional[str]:
        """Найти URL страницы с ценами на сайте конкурента."""
        if not website:
            return None
        base = website if website.startswith('http') else f'https://{website}'
        base = base.rstrip('/')

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                resp = await client.get(base, headers={"User-Agent": self.BROWSER_UA})
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Priority 1: exact path match
                for link in soup.find_all('a', href=True):
                    href = (link.get('href') or '').lower().strip().rstrip('/')
                    if not href or href.startswith('#') or href.startswith('javascript'):
                        continue
                    for path in self.PRICING_PAGE_PATHS:
                        if href == path.lstrip('/') or href.endswith(path.lstrip('/')):
                            return urljoin(base, link['href'])

                # Priority 2: link text contains price keywords
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text().lower()
                    if not href or href.startswith('#') or href.startswith('javascript'):
                        continue
                    if any(kw in text for kw in self.PRICING_LINK_KEYWORDS):
                        return urljoin(base, href)

                # Priority 3: homepage fallback — check if homepage contains prices
                text = soup.get_text()
                raw_numbers = []
                for pattern in self.PRICE_PATTERNS:
                    for match in pattern.finditer(text):
                        try:
                            price = int(match.group(1).replace(' ', ''))
                            if 100 <= price <= 10_000_000:
                                raw_numbers.append(price)
                        except (ValueError, IndexError):
                            continue
                if len(raw_numbers) >= 1:
                    return base

                return None
            except Exception as e:
                print(f"[CI Pricing] Не удалось найти страницу цен для {website}: {e}")
                return None

    async def _scrape_prices_from_page(self, url: str) -> Dict[str, Any]:
        """Собрать цены со страницы."""
        result = {"prices_found": False, "prices": {}, "raw_numbers": [], "promo_detected": False, "promos": []}

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers={"User-Agent": self.BROWSER_UA})
                resp.raise_for_status()
            except Exception as e:
                print(f"[CI Pricing] Ошибка загрузки {url}: {e}")
                return result

        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        # Извлекаем все числа похожие на цены
        raw_numbers = []
        for pattern in self.PRICE_PATTERNS:
            for match in pattern.finditer(text):
                price_str = match.group(1).replace(' ', '')
                try:
                    price = int(price_str)
                    if 100 <= price <= 10_000_000:
                        raw_numbers.append(price)
                except ValueError:
                    continue

        if raw_numbers:
            result["prices_found"] = True
            result["raw_numbers"] = sorted(raw_numbers)

            # Категоризируем цены
            cheap = [p for p in raw_numbers if p <= 3000]
            mid = [p for p in raw_numbers if 3000 < p <= 15000]
            expensive = [p for p in raw_numbers if p > 15000]

            result["prices"] = {
                "min": min(raw_numbers),
                "max": max(raw_numbers),
                "median": sorted(raw_numbers)[len(raw_numbers) // 2],
                "count": len(raw_numbers),
                "budget_range": f"{min(cheap) if cheap else '—'} – {max(cheap) if cheap else '—'}",
                "mid_range": f"{min(mid) if mid else '—'} – {max(mid) if mid else '—'}",
                "premium_range": f"{min(expensive) if expensive else '—'} – {max(expensive) if expensive else '—'}",
            }

        # Ищем акции
        page_lower = text.lower()
        for kw in self.PROMO_KEYWORDS:
            if kw in page_lower:
                result["promo_detected"] = True
                # Ищем конкретные цифры скидок рядом с ключевым словом
                idx = page_lower.find(kw)
                context = text[max(0, idx - 50):idx + 100]
                discount_match = re.search(r'(\d{1,2})\s*%', context)
                if discount_match:
                    result["promos"].append({
                        "keyword": kw,
                        "discount_percent": int(discount_match.group(1)),
                        "context": context.strip()[:120]
                    })
                else:
                    result["promos"].append({"keyword": kw, "discount_percent": None})

        return result

    def _determine_price_segment(self, price_data: Dict[str, Any]) -> Optional[str]:
        """Определить ценовой сегмент на основе реальных цен (логика, не random)."""
        if not price_data.get("prices_found") or not price_data["prices"].get("median"):
            return None

        median = price_data["prices"]["median"]

        # Медицинские бенчмарки (российский рынок)
        if median <= 3000:
            return "budget"
        elif median <= 12000:
            return "mid"
        elif median <= 35000:
            return "premium"
        else:
            return "luxury"

    def _determine_pricing_strategy(self, prices: Dict[str, Any], segment: Optional[str]) -> Optional[str]:
        """Определить ценовую стратегию на основе реальных данных."""
        if not prices.get("prices_found"):
            return None

        raw = prices.get("raw_numbers", [])
        if len(raw) < 3:
            return None

        # Смотрим разброс цен (coefficient of variation)
        mean = sum(raw) / len(raw)
        variance = sum((p - mean) ** 2 for p in raw) / len(raw)
        cv = (variance ** 0.5) / mean if mean > 0 else 0

        if segment == "premium" or segment == "luxury":
            return "skimming"
        elif segment == "budget" and cv < 0.3:
            return "penetration"
        elif cv < 0.25:
            return "competitive"
        elif cv > 0.5:
            return "dynamic"
        else:
            return "value_based"

    async def _analyze_competitor_pricing(
        self,
        competitor: Dict[str, Any],
        niche: str,
        services: List[str]
    ) -> Dict[str, Any]:
        """
        Проанализировать цены одного конкурента через реальный сбор данных.

        Стратегия:
        1. Найти страницу с ценами на сайте конкурента
        2. Загрузить и распарсить цены (Russian price patterns)
        3. Определить ценовой сегмент из реальных цен
        4. Детектировать акции/скидки
        5. Если страница не найдена → structured null
        """
        name = competitor["name"]
        website = competitor.get("website") or competitor.get("url") or competitor.get("site")
        print(f"[CI Pricing] Анализ цен: {name}")

        if not website:
            print(f"[CI Pricing] Нет website для {name}, возвращаю structured null")
            return {
                "name": name,
                "price_segment": None,
                "prices": {},
                "avg_check": None,
                "price_transparency": False,
                "has_promotions": None,
                "promotions": [],
                "pricing_strategy": None,
                "price_competitiveness": None,
                "confidence": 0.0,
                "note": "no website provided"
            }

        # Шаг 1: Найти URL страницы с ценами
        pricing_url = await self._find_pricing_url(website)

        if not pricing_url:
            # Fallback: try scraping the homepage directly
            print(f"[CI Pricing] Страница цен не найдена для {name}, пробую главную")
            pricing_url = website.rstrip('/') if website else None

        if not pricing_url:
            return {
                "name": name,
                "website": website,
                "price_segment": None,
                "prices": {},
                "avg_check": None,
                "price_transparency": False,
                "has_promotions": None,
                "promotions": [],
                "pricing_strategy": None,
                "price_competitiveness": None,
                "confidence": 0.0,
                "note": "no pricing page detected"
            }

        # Шаг 2: Собрать цены со страницы
        price_data = await self._scrape_prices_from_page(pricing_url)

        # Шаг 3: Определить ценовой сегмент (логика)
        price_segment = self._determine_price_segment(price_data)

        # Шаг 4: Ценовая стратегия (логика)
        pricing_strategy = self._determine_pricing_strategy(price_data, price_segment)

        # Шаг 5: Средний чек из реальных данных
        avg_check = price_data["prices"].get("median") if price_data["prices_found"] else None

        # Шаг 6: Прозрачность цен
        price_transparency = price_data["prices_found"]

        profile = {
            "name": name,
            "website": website,
            "pricing_url": pricing_url,
            "price_segment": price_segment,
            "prices": price_data["prices"],
            "raw_prices": price_data.get("raw_numbers", []),
            "avg_check": avg_check,
            "price_transparency": price_transparency,
            "has_promotions": price_data["promo_detected"],
            "promotions": price_data["promos"],
            "pricing_strategy": pricing_strategy,
            "price_competitiveness": self._assess_competitiveness(price_segment) if price_segment else None,
            "confidence": 0.7 if price_data["prices_found"] else 0.0,
            "note": None if price_data["prices_found"] else "no prices extracted from page"
        }

        return profile

    def _assess_competitiveness(self, segment: str) -> str:
        """Оценить конкурентоспособность цен."""
        if segment == "budget":
            return "high"  # Низкие цены = высокая конкурентоспособность
        elif segment == "mid":
            return "medium"
        else:
            return "low"  # Высокие цены = низкая конкурентоспособность

    async def _analyze_market_pricing(
        self,
        pricing_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать ценообразование на рынке.

        Args:
            pricing_profiles: ценовые профили

        Returns:
            Анализ рынка
        """
        print(f"[CI Pricing] Анализ ценообразования рынка")

        # Распределение по сегментам
        segment_distribution = {}
        for profile in pricing_profiles:
            segment = profile["price_segment"]
            segment_distribution[segment] = segment_distribution.get(segment, 0) + 1

        # Средний чек по сегментам (пропускаем None)
        avg_check_by_segment = {}
        for segment in ["budget", "mid", "premium"]:
            segment_profiles = [p for p in pricing_profiles if p["price_segment"] == segment]
            segment_checks = [p["avg_check"] for p in segment_profiles if p["avg_check"] is not None]
            if segment_checks:
                avg_check_by_segment[segment] = round(sum(segment_checks) / len(segment_checks))

        # Прозрачность цен на рынке
        transparent_count = sum(1 for p in pricing_profiles if p["price_transparency"])
        transparency_rate = (transparent_count / len(pricing_profiles)) * 100 if pricing_profiles else 0

        # Использование акций
        promotions_count = sum(1 for p in pricing_profiles if p["has_promotions"])
        promotions_rate = (promotions_count / len(pricing_profiles)) * 100 if pricing_profiles else 0

        # Средний чек по рынку (только где есть цены)
        market_checks = [p["avg_check"] for p in pricing_profiles if p["avg_check"] is not None]
        market_avg_check = sum(market_checks) / len(market_checks) if market_checks else 0

        market_analysis = {
            "segment_distribution": segment_distribution,
            "avg_check_by_segment": avg_check_by_segment,
            "market_avg_check": round(market_avg_check),
            "price_transparency_percent": round(transparency_rate, 1),
            "promotions_usage_percent": round(promotions_rate, 1),
            "dominant_segment": max(segment_distribution.items(), key=lambda x: x[1])[0]
        }

        return market_analysis

    async def _identify_pricing_leaders(
        self,
        pricing_profiles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Определить ценовых лидеров.

        Args:
            pricing_profiles: ценовые профили

        Returns:
            Лидеры по ценам
        """
        print(f"[CI Pricing] Определение ценовых лидеров")

        # Самые дешёвые (None → бесконечность, отбрасываем)
        with_prices = [p for p in pricing_profiles if p["avg_check"] is not None]
        sorted_by_price = sorted(with_prices, key=lambda x: x["avg_check"])
        cheapest = sorted_by_price[:3]

        # Самые дорогие
        most_expensive = sorted_by_price[-3:][::-1] if len(sorted_by_price) >= 3 else sorted_by_price[::-1]

        # Лучшая прозрачность
        transparent = [p for p in pricing_profiles if p["price_transparency"]]
        best_transparency = sorted(transparent, key=lambda x: len(x.get("prices", {})) if isinstance(x.get("prices"), dict) else 0, reverse=True)[:3]

        return {
            "cheapest": [
                {"name": p["name"], "avg_check": p["avg_check"], "segment": p["price_segment"]}
                for p in cheapest
            ],
            "most_expensive": [
                {"name": p["name"], "avg_check": p["avg_check"], "segment": p["price_segment"]}
                for p in most_expensive
            ],
            "best_transparency": [
                {"name": p["name"], "services_count": len(p["prices"])}
                for p in best_transparency
            ]
        }

    async def _create_positioning_map(
        self,
        pricing_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Создать карту ценового позиционирования.

        Args:
            pricing_profiles: ценовые профили

        Returns:
            Карта позиционирования
        """
        print(f"[CI Pricing] Создание карты позиционирования")

        # Группировка по сегментам
        positioning = {
            "budget": [],
            "mid": [],
            "premium": [],
            "luxury": []
        }

        for profile in pricing_profiles:
            segment = profile["price_segment"]
            if segment is None:
                continue  # Skip competitors with no price data
            positioning[segment].append({
                "name": profile["name"],
                "avg_check": profile["avg_check"],
                "transparency": profile["price_transparency"]
            })

        # Ценовые разрывы (gaps) — только где есть цены
        all_checks = sorted([p["avg_check"] for p in pricing_profiles if p["avg_check"] is not None])
        gaps = []
        for i in range(len(all_checks) - 1):
            diff = all_checks[i + 1] - all_checks[i]
            if diff > all_checks[i] * 0.3:  # Разрыв >30%
                gaps.append({
                    "lower": all_checks[i],
                    "upper": all_checks[i + 1],
                    "gap_percent": round((diff / all_checks[i]) * 100, 1)
                })

        return {
            "positioning": positioning,
            "price_gaps": gaps
        }

    async def _generate_pricing_insights(
        self,
        pricing_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        pricing_leaders: Dict[str, Any],
        positioning_map: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Сгенерировать ценовые инсайты.

        Args:
            pricing_profiles: ценовые профили
            market_analysis: анализ рынка
            pricing_leaders: лидеры по ценам
            positioning_map: карта позиционирования

        Returns:
            Инсайты
        """
        print(f"[CI Pricing] Генерация ценовых инсайтов")

        insights = {
            "market_positioning": market_analysis["dominant_segment"],
            "price_transparency_level": "high" if market_analysis["price_transparency_percent"] > 70 else "medium" if market_analysis["price_transparency_percent"] > 40 else "low",
            "competition_intensity": "high" if len(pricing_profiles) > 10 else "medium" if len(pricing_profiles) > 5 else "low",
            "opportunities_count": len(positioning_map["price_gaps"]),
            "key_findings": []
        }

        # Ключевые находки
        if market_analysis["price_transparency_percent"] < 50:
            insights["key_findings"].append("Менее 50% конкурентов публикуют цены на сайте")

        if len(positioning_map["price_gaps"]) > 0:
            insights["key_findings"].append(f"Обнаружено {len(positioning_map['price_gaps'])} ценовых разрывов для позиционирования")

        if market_analysis["promotions_usage_percent"] > 60:
            insights["key_findings"].append("Высокая активность акций и скидок на рынке")

        return insights

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-pricing.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Pricing] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "price_collection",
            "pricing_strategy_analysis",
            "price_positioning",
            "promotion_analysis",
            "price_transparency_analysis",
            "competitive_pricing_analysis"
        ]
