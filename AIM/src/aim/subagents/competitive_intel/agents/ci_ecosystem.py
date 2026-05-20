"""
CI Ecosystem Agent - Partner & Integration Ecosystem Analysis

Анализирует экосистему партнёров и интеграций конкурентов:
- Партнёры и поставщики
- Интеграции с сервисами
- Экосистема продуктов
- Стратегические альянсы
- Каналы дистрибуции
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
import re

import httpx
from bs4 import BeautifulSoup

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIEcosystemAgent(Agent):
    """CI Ecosystem - агент анализа экосистемы партнёров и интеграций."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-ecosystem",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-ecosystem")

        # Partner types
        self.partner_types = {
            "technology": "Технологические партнёры",
            "distribution": "Дистрибуция",
            "marketing": "Маркетинговые партнёры",
            "suppliers": "Поставщики",
            "strategic": "Стратегические альянсы",
            "integration": "Интеграционные партнёры"
        }

        # Integration categories
        self.integration_categories = {
            "crm": "CRM системы",
            "payment": "Платёжные системы",
            "analytics": "Аналитика",
            "communication": "Коммуникации",
            "booking": "Онлайн-запись",
            "marketing": "Маркетинг автоматизация"
        }

        # HTML-сигналы для детекшна интеграций (российский рынок)
        self.crm_signals = {
            "amoCRM": ["amocrm", "amo_social", "amoforms", "amocrm.ru/js"],
            "Bitrix24": ["bitrix24", "bitrix.info", "bx24", "b24form"],
            "Salesforce": ["salesforce", "force.com"],
            "RetailCRM": ["retailcrm", "retailrocket"],
        }

        self.payment_signals = {
            "YooKassa": ["yookassa", "yoomoney", "yandex.checkout", "ЮKassa"],
            "CloudPayments": ["cloudpayments", "cloudpayments.ru"],
            "Sberbank": ["sberbank.ru/acquiring", "sberbank.*платеж", "sber.acquiring"],
            "Tinkoff": ["tinkoff.ru/acquiring", "tinkoff.*kassa", "tinkoff.ru/payment"],
            "Robokassa": ["robokassa", "roboxchange"],
        }

        self.analytics_signals = {
            "Yandex.Metrika": ["mc.yandex.ru/metrika", "metrika", "yandex_metrika", "ym("],
            "Google Analytics": ["googletagmanager", "gtag", "analytics.js", "ga\(", "gtm.start"],
            "VK Pixel": ["vk.com/js/api", "vk_pixel", "VK.Retargeting", "vk_retargeting"],
            "MyTarget": ["top-fwz1.mail.ru", "mytarget", "top.mail.ru/js"],
        }

        self.booking_signals = {
            "Yclients": ["yclients", "yclients.com"],
            "DIKIDI": ["dikidi", "dikidi.ru"],
            "Altegio": ["altegio", "altegio.com"],
            "MedFlex": ["medflex", "medflex.ru"],
            "Prodoctorov": ["prodoctorov.ru", "prodoctorov"],
            "1C-Medicine": ["1c-med", "1c.*медицин"],
        }

        self.communication_signals = {
            "JivoSite": ["jivosite", "jivosite.ru/js", "jivo_chat"],
            "CallbackHunter": ["callbackhunter", "callbackhunter.ru"],
            "LiveTex": ["livetex", "livetex.ru"],
            "Talk-Me": ["talk-me", "talkme"],
            "WhatsApp": ["api.whatsapp", "whatsapp://", "wa.me/", "chat.whatsapp"],
            "Telegram": ["t.me/", "telegram.me/", "telegram.org/js"],
        }

        self.aggregator_signals = {
            "Prodoctorov": ["prodoctorov.ru", "prodoctorov"],
            "2GIS": ["2gis.ru", "2gis.com", "2gis.*отзыв"],
            "Yandex.Maps": ["yandex.ru/maps", "yandex.*карт", "yandex.ru/profile"],
            "Google Maps": ["google.com/maps", "maps.google", "google.*maps"],
            "Zoon": ["zoon.ru", "zoon"],
            "Yell": ["yell.ru", "yell"],
        }

        self.social_domains = {
            "VK": ["vk.com", "vk.ru", "vkontakte.ru"],
            "Telegram": ["t.me", "telegram.me", "tg.me"],
            "YouTube": ["youtube.com", "youtu.be", "youtube.ru"],
            "Instagram": ["instagram.com"],
            "Odnoklassniki": ["ok.ru", "odnoklassniki.ru"],
            "Yandex.Zen": ["dzen.ru", "zen.yandex.ru"],
            "Rutube": ["rutube.ru"],
        }

        self.partner_link_keywords = [
            "partner", "партнёр", "партнер", "сотрудничеств",
            "франшиз", "franchise", "franchisee",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ экосистемы конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - niche: ниша (опционально)

        Returns:
            TaskResult с анализом экосистемы
        """
        try:
            competitors = task.payload["competitors"]
            niche = task.payload.get("niche", "")

            print(f"[CI Ecosystem] Начало анализа экосистемы {len(competitors)} конкурентов")

            # Шаг 1: Analyze ecosystem for each competitor
            ecosystem_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_ecosystem(competitor, niche)
                ecosystem_profiles.append(profile)

            # Шаг 2: Market ecosystem analysis
            market_analysis = await self._analyze_market_ecosystem(ecosystem_profiles)

            # Шаг 3: Identify ecosystem leaders
            ecosystem_leaders = await self._identify_ecosystem_leaders(ecosystem_profiles)

            # Шаг 4: Integration opportunities
            integration_opportunities = await self._identify_integration_opportunities(
                ecosystem_profiles, niche
            )

            # Шаг 5: Ecosystem insights
            insights = await self._generate_ecosystem_insights(
                ecosystem_profiles, market_analysis, ecosystem_leaders, integration_opportunities
            )

            # Шаг 6: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "ecosystem_profiles": ecosystem_profiles,
                "market_analysis": market_analysis,
                "ecosystem_leaders": ecosystem_leaders,
                "integration_opportunities": integration_opportunities,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Ecosystem] Анализ экосистемы завершён для {len(competitors)} конкурентов")

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
            print(f"[CI Ecosystem] Ошибка: {e}")
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

    async def _analyze_competitor_ecosystem(
        self,
        competitor: Dict[str, Any],
        niche: str
    ) -> Dict[str, Any]:
        """
        Проанализировать экосистему конкурента через реальный HTML-анализ сайта.

        Детектирует: CRM, платёжные системы, аналитику, онлайн-запись,
        соцсети, мессенджеры, виджеты, партнёрские интеграции.

        Если сайт недоступен → structured null.
        """
        name = competitor["name"]
        website = competitor.get("website") or competitor.get("url") or competitor.get("site")
        print(f"[CI Ecosystem] Анализ экосистемы: {name}")

        if not website:
            print(f"[CI Ecosystem] Нет website для {name}, возвращаю structured null")
            return {
                "name": name,
                "partners_by_type": {},
                "total_partners": 0,
                "integrations": {},
                "integration_count": 0,
                "distribution_channels": [],
                "strategic_alliances": [],
                "has_strategic_alliances": False,
                "ecosystem_maturity": "unknown",
                "confidence": 0.0,
                "note": "no website provided"
            }

        signals = await self._scan_website_ecosystem(website)

        if signals is None:
            return {
                "name": name,
                "website": website,
                "partners_by_type": {},
                "total_partners": 0,
                "integrations": {},
                "integration_count": 0,
                "distribution_channels": [],
                "strategic_alliances": [],
                "has_strategic_alliances": False,
                "ecosystem_maturity": "unknown",
                "confidence": 0.0,
                "note": "website unreachable"
            }

        # Построение профиля из детектированных сигналов
        partners_by_type = {}
        integrations = {}
        distribution_channels = []
        strategic_alliances = []

        if signals["crm"]:
            for crm in signals["crm"]:
                integrations[f"crm:{crm}"] = crm
            partners_by_type["technology"] = partners_by_type.get("technology", 0) + len(signals["crm"])

        if signals["payment"]:
            for pay in signals["payment"]:
                integrations[f"payment:{pay}"] = pay
            partners_by_type["suppliers"] = partners_by_type.get("suppliers", 0) + len(signals["payment"])

        if signals["analytics"]:
            for an in signals["analytics"]:
                integrations[f"analytics:{an}"] = an
            partners_by_type["technology"] = partners_by_type.get("technology", 0) + len(signals["analytics"])

        if signals["booking"]:
            for book in signals["booking"]:
                integrations[f"booking:{book}"] = book
            partners_by_type["integration"] = partners_by_type.get("integration", 0) + len(signals["booking"])

        if signals["communication"]:
            for comm in signals["communication"]:
                integrations[f"communication:{comm}"] = comm
            partners_by_type["technology"] = partners_by_type.get("technology", 0) + len(signals["communication"])

        if signals["social_links"]:
            partners_by_type["marketing"] = partners_by_type.get("marketing", 0) + len(signals["social_links"])

        if signals["aggregators"]:
            for agg in signals["aggregators"]:
                distribution_channels.append(agg)
            partners_by_type["distribution"] = partners_by_type.get("distribution", 0) + len(signals["aggregators"])

        if signals["partner_links"]:
            partners_by_type["strategic"] = partners_by_type.get("strategic", 0) + len(signals["partner_links"])
            for pl in signals["partner_links"]:
                strategic_alliances.append({"type": "detected_partner_link", "url": pl})

        ecosystem_maturity = self._assess_ecosystem_maturity(
            len(partners_by_type),
            len(integrations),
            len(distribution_channels),
            len(strategic_alliances) > 0
        )

        profile = {
            "name": name,
            "website": website,
            "partners_by_type": partners_by_type,
            "total_partners": sum(partners_by_type.values()),
            "integrations": integrations,
            "integration_count": len(integrations),
            "distribution_channels": distribution_channels,
            "strategic_alliances": strategic_alliances,
            "has_strategic_alliances": len(strategic_alliances) > 0,
            "ecosystem_maturity": ecosystem_maturity,
            "detected_signals": signals,
            "confidence": 0.7 if signals["page_loaded"] else 0.0
        }

        return profile

    async def _scan_website_ecosystem(self, website: str) -> Optional[Dict[str, Any]]:
        """Сканировать сайт на наличие экосистемных сигналов."""
        url = website if website.startswith('http') else f'https://{website}'

        result = {
            "page_loaded": False,
            "crm": [],
            "payment": [],
            "analytics": [],
            "booking": [],
            "communication": [],
            "social_links": [],
            "aggregators": [],
            "partner_links": [],
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers={"User-Agent": "AIM-CI-Ecosystem/1.0"})
                resp.raise_for_status()
            except Exception as e:
                print(f"[CI Ecosystem] Ошибка загрузки {url}: {e}")
                return None

        result["page_loaded"] = True
        html = resp.text
        html_lower = html.lower()
        soup = BeautifulSoup(html, 'html.parser')

        # Детектим CRM по скриптам, iframe, формам
        for name, patterns in self.crm_signals.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    result["crm"].append(name)
                    break

        # Детектим платёжные системы
        for name, patterns in self.payment_signals.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    result["payment"].append(name)
                    break

        # Детектим аналитику (скрипты, счётчики, пиксели)
        for name, patterns in self.analytics_signals.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    result["analytics"].append(name)
                    break

        # Детектим системы онлайн-записи
        for name, patterns in self.booking_signals.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    result["booking"].append(name)
                    break

        # Детектим коммуникационные виджеты
        for name, patterns in self.communication_signals.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    result["communication"].append(name)
                    break

        # Детектим соцсети по ссылкам
        for platform, domains in self.social_domains.items():
            for domain in domains:
                if domain in html_lower:
                    result["social_links"].append(platform)
                    break

        # Детектим агрегаторы по ссылкам
        for name, patterns in self.aggregator_signals.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    result["aggregators"].append(name)
                    break

        # Детектим партнёрские ссылки
        for link in soup.find_all('a', href=True):
            href = (link.get('href') or '').lower()
            link_text = (link.get_text() or '').lower().strip()
            for kw in self.partner_link_keywords:
                if kw in href or kw in link_text:
                    result["partner_links"].append(link.get('href'))
                    break

        # Дедупликация partner_links
        result["partner_links"] = list(set(result["partner_links"]))

        return result

    def _assess_ecosystem_maturity(
        self,
        partner_types: int,
        integrations: int,
        channels: int,
        has_alliances: bool
    ) -> str:
        """Оценить зрелость экосистемы."""
        score = 0

        # Разнообразие партнёров
        if partner_types >= 3:
            score += 3
        elif partner_types >= 2:
            score += 2
        elif partner_types >= 1:
            score += 1

        # Интеграции
        if integrations >= 4:
            score += 3
        elif integrations >= 2:
            score += 2
        elif integrations >= 1:
            score += 1

        # Каналы дистрибуции
        if channels >= 3:
            score += 2
        elif channels >= 2:
            score += 1

        # Стратегические альянсы
        if has_alliances:
            score += 2

        # Итоговая оценка
        if score >= 8:
            return "advanced"
        elif score >= 5:
            return "intermediate"
        elif score >= 2:
            return "basic"
        else:
            return "minimal"

    async def _analyze_market_ecosystem(
        self,
        ecosystem_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать экосистему рынка.

        Args:
            ecosystem_profiles: профили экосистем

        Returns:
            Анализ рынка
        """
        print(f"[CI Ecosystem] Анализ экосистемы рынка")

        # Средние показатели
        avg_partners = sum(p["total_partners"] for p in ecosystem_profiles) / len(ecosystem_profiles)
        avg_integrations = sum(p["integration_count"] for p in ecosystem_profiles) / len(ecosystem_profiles)

        # Популярные интеграции
        integration_usage = {}
        for profile in ecosystem_profiles:
            for key, service in profile["integrations"].items():
                integration_usage[key] = integration_usage.get(key, 0) + 1

        most_popular_integrations = sorted(
            integration_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Использование каналов дистрибуции
        channel_usage = {}
        for profile in ecosystem_profiles:
            for channel in profile["distribution_channels"]:
                channel_usage[channel] = channel_usage.get(channel, 0) + 1

        # Компании со стратегическими альянсами
        with_alliances = sum(1 for p in ecosystem_profiles if p["has_strategic_alliances"])
        alliances_rate = (with_alliances / len(ecosystem_profiles)) * 100

        market_analysis = {
            "avg_partners": round(avg_partners, 1),
            "avg_integrations": round(avg_integrations, 1),
            "most_popular_integrations": [
                {"integration": integ, "usage_count": count}
                for integ, count in most_popular_integrations
            ],
            "channel_usage": channel_usage,
            "strategic_alliances_percent": round(alliances_rate, 1)
        }

        return market_analysis

    async def _identify_ecosystem_leaders(
        self,
        ecosystem_profiles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Определить лидеров по экосистеме.

        Args:
            ecosystem_profiles: профили экосистем

        Returns:
            Лидеры по экосистеме
        """
        print(f"[CI Ecosystem] Определение лидеров экосистемы")

        # Сортировка по количеству партнёров
        sorted_by_partners = sorted(
            ecosystem_profiles,
            key=lambda x: x["total_partners"],
            reverse=True
        )

        # Сортировка по интеграциям
        sorted_by_integrations = sorted(
            ecosystem_profiles,
            key=lambda x: x["integration_count"],
            reverse=True
        )

        # Сортировка по зрелости
        maturity_scores = {"minimal": 1, "basic": 2, "intermediate": 3, "advanced": 4}
        sorted_by_maturity = sorted(
            ecosystem_profiles,
            key=lambda x: maturity_scores.get(x["ecosystem_maturity"], 1),
            reverse=True
        )

        return {
            "partner_leaders": [
                {
                    "name": p["name"],
                    "partners_count": p["total_partners"],
                    "maturity": p["ecosystem_maturity"]
                }
                for p in sorted_by_partners[:3] if p["total_partners"] > 0
            ],
            "integration_leaders": [
                {
                    "name": p["name"],
                    "integrations_count": p["integration_count"],
                    "integrations": list(p["integrations"].keys())
                }
                for p in sorted_by_integrations[:3] if p["integration_count"] > 0
            ],
            "maturity_leaders": [
                {
                    "name": p["name"],
                    "maturity": p["ecosystem_maturity"]
                }
                for p in sorted_by_maturity[:3]
            ]
        }

    async def _identify_integration_opportunities(
        self,
        ecosystem_profiles: List[Dict[str, Any]],
        niche: str
    ) -> List[Dict[str, Any]]:
        """
        Определить возможности для интеграций.

        Args:
            ecosystem_profiles: профили экосистем
            niche: ниша

        Returns:
            Возможности для интеграций
        """
        print(f"[CI Ecosystem] Определение возможностей для интеграций")

        opportunities = []

        # Проверка покрытия категорий интеграций
        all_categories = set(self.integration_categories.keys())
        used_categories = set()

        for profile in ecosystem_profiles:
            for key in profile["integrations"].keys():
                category = key.split(":")[0]
                used_categories.add(category)

        missing_categories = all_categories - used_categories

        for category in missing_categories:
            opportunities.append({
                "type": "missing_integration",
                "category": category,
                "description": f"Никто не интегрирован с {self.integration_categories[category]}",
                "priority": "high"
            })

        # Низкое использование партнёрств
        low_partnership = sum(1 for p in ecosystem_profiles if p["total_partners"] < 2)
        if low_partnership > len(ecosystem_profiles) / 2:
            opportunities.append({
                "type": "partnership_gap",
                "description": "Большинство конкурентов имеют мало партнёров",
                "priority": "medium"
            })

        # Отсутствие стратегических альянсов
        no_alliances = sum(1 for p in ecosystem_profiles if not p["has_strategic_alliances"])
        if no_alliances > len(ecosystem_profiles) / 2:
            opportunities.append({
                "type": "alliance_gap",
                "description": "Большинство конкурентов не имеют стратегических альянсов",
                "priority": "high"
            })

        return opportunities

    async def _generate_ecosystem_insights(
        self,
        ecosystem_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        ecosystem_leaders: Dict[str, Any],
        integration_opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать инсайты по экосистеме.

        Args:
            ecosystem_profiles: профили экосистем
            market_analysis: анализ рынка
            ecosystem_leaders: лидеры экосистемы
            integration_opportunities: возможности интеграций

        Returns:
            Инсайты
        """
        print(f"[CI Ecosystem] Генерация инсайтов по экосистеме")

        # Оценка зрелости рынка
        maturity_scores = {"minimal": 1, "basic": 2, "intermediate": 3, "advanced": 4}
        avg_maturity = sum(
            maturity_scores.get(p["ecosystem_maturity"], 1) for p in ecosystem_profiles
        ) / len(ecosystem_profiles)

        if avg_maturity >= 3:
            market_maturity = "advanced"
        elif avg_maturity >= 2:
            market_maturity = "intermediate"
        else:
            market_maturity = "basic"

        insights = {
            "ecosystem_maturity": market_maturity,
            "integration_level": "high" if market_analysis["avg_integrations"] > 3 else "medium" if market_analysis["avg_integrations"] > 1 else "low",
            "partnership_activity": "high" if market_analysis["avg_partners"] > 3 else "medium" if market_analysis["avg_partners"] > 1 else "low",
            "opportunities_count": len([o for o in integration_opportunities if o.get("priority") == "high"]),
            "key_findings": []
        }

        # Ключевые находки
        if market_analysis["strategic_alliances_percent"] < 30:
            insights["key_findings"].append("Менее 30% конкурентов имеют стратегические альянсы")

        if market_analysis["avg_integrations"] < 2:
            insights["key_findings"].append("Низкий уровень интеграций на рынке")

        if len(integration_opportunities) > 0:
            insights["key_findings"].append(f"Обнаружено {len(integration_opportunities)} возможностей для построения экосистемы")

        if market_analysis.get("most_popular_integrations"):
            top_integration = market_analysis["most_popular_integrations"][0]
            insights["key_findings"].append(f"Самая популярная интеграция: {top_integration['integration']}")

        return insights

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-ecosystem.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Ecosystem] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "partner_analysis",
            "integration_analysis",
            "ecosystem_mapping",
            "strategic_alliance_analysis",
            "distribution_channel_analysis",
            "ecosystem_maturity_assessment"
        ]
