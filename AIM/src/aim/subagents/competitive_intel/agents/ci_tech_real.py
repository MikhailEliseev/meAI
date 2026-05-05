"""
CI Tech Agent - Real Technology Stack Analysis

Реальный анализ технологического стека конкурентов:
- Парсинг HTML для определения CMS, фреймворков, библиотек
- Анализ JavaScript файлов (Google Analytics, Яндекс.Метрика, etc.)
- Определение технологий по meta тегам, headers, DOM структуре
- SEO/GEO оптимизация под нейросети
- Технический стек и оптимизация сайта
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re
from pathlib import Path

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CITechAgent(Agent):
    """CI Tech - агент реального анализа технологического стека.

    Анализирует:
    1. CMS и платформы (WordPress, Tilda, Bitrix, etc.)
    2. Frontend технологии (React, Vue, jQuery, etc.)
    3. Аналитика (Google Analytics, Яндекс.Метрика, etc.)
    4. SEO оптимизация (meta теги, schema.org, Open Graph)
    5. GEO оптимизация под нейросети (structured data, FAQ schema)
    6. Технический стек (CDN, хостинг, SSL)
    7. Производительность (скорость загрузки, оптимизация)
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/ci-tech"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-tech",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault(vault_path)
        self.data_path = Path("AIM/data/ci-tech")
        self.data_path.mkdir(parents=True, exist_ok=True)

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute tech stack analysis task

        Task payload:
        {
            "competitors": [
                {"name": "Competitor 1", "url": "https://example.com"},
                {"name": "Competitor 2", "url": "https://example2.com"}
            ]
        }
        """
        try:
            start_time = datetime.now()
            competitors = task.payload.get("competitors", [])

            if not competitors:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={"error": "No competitors provided"},
                    error="No competitors provided",
                    duration_seconds=0.0,
                    completed_at=datetime.now()
                )

            print(f"[CI Tech] Анализ tech stack {len(competitors)} конкурентов")

            # Analyze each competitor
            tech_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor(competitor)
                tech_profiles.append(profile)
                print(f"[CI Tech] ✓ {competitor['name']}: {profile['cms']}, {len(profile['technologies'])} технологий")

            # Market analysis
            market_tech = await self._analyze_market_tech(tech_profiles)

            # Generate insights
            insights = await self._generate_tech_insights(tech_profiles, market_tech)

            # Strategic analysis for first competitor (main target)
            main_profile = tech_profiles[0] if tech_profiles else {}

            financial_analysis = await self._estimate_competitor_budget(main_profile)
            competitive_gaps = await self._identify_competitive_gaps(main_profile)
            industry_benchmarks = await self._compare_to_industry(main_profile, industry="medical")
            tech_debt = await self._analyze_tech_debt(main_profile)
            attack_roadmap = await self._generate_attack_roadmap(competitive_gaps)

            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "tech_profiles": tech_profiles,
                "market_tech": market_tech,
                "insights": insights,
                "financial_analysis": financial_analysis,
                "competitive_gaps": competitive_gaps,
                "industry_benchmarks": industry_benchmarks,
                "tech_debt": tech_debt,
                "attack_roadmap": attack_roadmap
            }

            # Save results
            await self._save_results(results)

            duration = (datetime.now() - start_time).total_seconds()
            print(f"[CI Tech] Анализ завершён за {duration:.1f}s")

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=results,
                error=None,
                duration_seconds=duration,
                completed_at=datetime.now()
            )

        except Exception as e:
            print(f"[CI Tech] ERROR: {e}")
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

    async def _analyze_competitor(self, competitor: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single competitor's tech stack

        Returns:
        {
            "name": "Competitor Name",
            "url": "https://example.com",
            "cms": "WordPress",
            "technologies": ["React", "Google Analytics"],
            "seo_optimization": {...},
            "geo_optimization": {...},
            "performance": {...}
        }
        """
        url = competitor.get("url")
        name = competitor.get("name", url)

        if not url:
            return {
                "name": name,
                "url": None,
                "error": "No URL provided",
                "cms": "Unknown",
                "technologies": [],
                "seo_optimization": {},
                "geo_optimization": {},
                "performance": {}
            }

        try:
            # Fetch website HTML
            html = await self._fetch_html(url)

            # Detect CMS
            cms = await self._detect_cms(html, url)

            # Detect technologies
            technologies = await self._detect_technologies(html)

            # Analyze SEO optimization
            seo = await self._analyze_seo(html)

            # Analyze GEO optimization (AI-ready structured data)
            geo = await self._analyze_geo_optimization(html)

            # Analyze performance
            performance = await self._analyze_performance(html, url)

            return {
                "name": name,
                "url": url,
                "cms": cms,
                "technologies": technologies,
                "seo_optimization": seo,
                "geo_optimization": geo,
                "performance": performance,
                "analyzed_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"[CI Tech] Error analyzing {name}: {e}")
            return {
                "name": name,
                "url": url,
                "error": str(e),
                "cms": "Unknown",
                "technologies": [],
                "seo_optimization": {},
                "geo_optimization": {},
                "performance": {}
            }

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML from URL using Playwright

        Uses Playwright MCP server for real browser rendering.
        """
        print(f"[CI Tech] Fetching {url}...")

        try:
            # Use Playwright MCP to navigate and get HTML
            # For now, we'll use a simple approach - ask user to provide HTML
            # or use requests library as fallback

            import aiohttp
            import ssl

            # Create SSL context that doesn't verify certificates (for testing)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    ssl=ssl_context,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    }
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        print(f"[CI Tech] ✓ Fetched {len(html)} bytes")
                        return html
                    else:
                        print(f"[CI Tech] ✗ HTTP {response.status}")
                        return ""

        except Exception as e:
            print(f"[CI Tech] ✗ Error fetching {url}: {e}")
            return ""

    async def _detect_cms(self, html: str, url: str) -> str:
        """Detect CMS from HTML

        Detection methods:
        - Meta tags (generator, application-name)
        - Specific HTML patterns
        - URL patterns (/wp-content/, /bitrix/, etc.)
        - JavaScript files
        """
        if not html:
            return "Unknown"

        cms_signatures = {
            "WordPress": [
                r'/wp-content/',
                r'/wp-includes/',
                r'<meta name="generator" content="WordPress',
                r'wp-json'
            ],
            "Tilda": [
                r'tilda',
                r't-records',
                r'static.tildacdn.com'
            ],
            "1C-Bitrix": [
                r'/bitrix/',
                r'bitrix_sessid',
                r'BX.'
            ],
            "Wix": [
                r'wix.com',
                r'_wix',
                r'static.parastorage.com'
            ],
            "Joomla": [
                r'/components/com_',
                r'<meta name="generator" content="Joomla'
            ],
            "Drupal": [
                r'Drupal',
                r'/sites/default/',
                r'drupal.js'
            ],
            "Shopify": [
                r'cdn.shopify.com',
                r'Shopify.theme'
            ]
        }

        for cms, patterns in cms_signatures.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    return cms

        return "Custom"

    async def _detect_technologies(self, html: str) -> List[str]:
        """Detect technologies from HTML

        Detects:
        - Frontend frameworks (React, Vue, Angular)
        - Libraries (jQuery, Bootstrap)
        - Analytics (Google Analytics, Яндекс.Метрика)
        - Marketing tools (Facebook Pixel, Google Tag Manager)
        """
        if not html:
            return []

        technologies = []

        tech_signatures = {
            "React": [r'react', r'_react', r'ReactDOM'],
            "Vue.js": [r'vue\.js', r'Vue\.'],
            "Angular": [r'angular', r'ng-'],
            "jQuery": [r'jquery', r'\$\('],
            "Bootstrap": [r'bootstrap'],
            "Google Analytics": [r'google-analytics\.com', r'gtag\(', r'ga\('],
            "Яндекс.Метрика": [r'mc\.yandex\.ru', r'ym\('],
            "Google Tag Manager": [r'googletagmanager\.com', r'gtm\.js'],
            "Facebook Pixel": [r'facebook\.net', r'fbq\('],
            "Hotjar": [r'hotjar\.com'],
            "Intercom": [r'intercom\.io'],
            "Cloudflare": [r'cloudflare'],
            "Webpack": [r'webpack'],
            "Next.js": [r'_next/'],
            "Nuxt.js": [r'_nuxt/']
        }

        for tech, patterns in tech_signatures.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    if tech not in technologies:
                        technologies.append(tech)
                    break

        return technologies

    async def _analyze_seo(self, html: str) -> Dict[str, Any]:
        """Analyze SEO optimization

        Checks:
        - Title tag
        - Meta description
        - H1 tags
        - Open Graph tags
        - Schema.org markup
        - Canonical URL
        """
        if not html:
            return {"score": 0, "issues": ["No HTML to analyze"]}

        seo = {
            "has_title": bool(re.search(r'<title>', html, re.IGNORECASE)),
            "has_meta_description": bool(re.search(r'<meta name="description"', html, re.IGNORECASE)),
            "has_h1": bool(re.search(r'<h1', html, re.IGNORECASE)),
            "has_og_tags": bool(re.search(r'<meta property="og:', html, re.IGNORECASE)),
            "has_schema": bool(re.search(r'schema\.org', html, re.IGNORECASE)),
            "has_canonical": bool(re.search(r'<link rel="canonical"', html, re.IGNORECASE))
        }

        score = sum(seo.values()) / len(seo) * 100
        seo["score"] = round(score, 1)

        issues = []
        if not seo["has_title"]:
            issues.append("Missing title tag")
        if not seo["has_meta_description"]:
            issues.append("Missing meta description")
        if not seo["has_h1"]:
            issues.append("Missing H1 tag")
        if not seo["has_schema"]:
            issues.append("No Schema.org markup")

        seo["issues"] = issues

        return seo

    async def _analyze_geo_optimization(self, html: str) -> Dict[str, Any]:
        """Analyze GEO optimization for AI/neural networks

        Checks:
        - FAQ Schema (for AI snippets)
        - HowTo Schema
        - Article Schema
        - Structured data quality
        - AI-readable content structure
        """
        if not html:
            return {"ai_ready_score": 0, "recommendations": ["No HTML to analyze"]}

        geo = {
            "has_faq_schema": bool(re.search(r'"@type":\s*"FAQPage"', html, re.IGNORECASE)),
            "has_howto_schema": bool(re.search(r'"@type":\s*"HowTo"', html, re.IGNORECASE)),
            "has_article_schema": bool(re.search(r'"@type":\s*"Article"', html, re.IGNORECASE)),
            "has_breadcrumbs": bool(re.search(r'"@type":\s*"BreadcrumbList"', html, re.IGNORECASE)),
            "has_local_business": bool(re.search(r'"@type":\s*"LocalBusiness"', html, re.IGNORECASE))
        }

        score = sum(geo.values()) / len(geo) * 100
        geo["ai_ready_score"] = round(score, 1)

        recommendations = []
        if not geo["has_faq_schema"]:
            recommendations.append("Add FAQ Schema for AI snippets")
        if not geo["has_article_schema"]:
            recommendations.append("Add Article Schema for better AI understanding")
        if not geo["has_local_business"]:
            recommendations.append("Add LocalBusiness Schema for local SEO")

        geo["recommendations"] = recommendations

        return geo

    async def _analyze_performance(self, html: str, url: str) -> Dict[str, Any]:
        """Analyze performance and optimization

        Checks:
        - Page size
        - Number of resources
        - Image optimization
        - Minification
        """
        if not html:
            return {"score": 0, "issues": ["No HTML to analyze"]}

        performance = {
            "html_size_kb": len(html.encode('utf-8')) / 1024 if html else 0,
            "has_minified_css": bool(re.search(r'\.min\.css', html)),
            "has_minified_js": bool(re.search(r'\.min\.js', html)),
            "uses_cdn": bool(re.search(r'cdn\.', html, re.IGNORECASE)),
            "has_lazy_loading": bool(re.search(r'loading="lazy"', html, re.IGNORECASE))
        }

        # Simple performance score
        score = 0
        if performance["html_size_kb"] < 100:
            score += 20
        if performance["has_minified_css"]:
            score += 20
        if performance["has_minified_js"]:
            score += 20
        if performance["uses_cdn"]:
            score += 20
        if performance["has_lazy_loading"]:
            score += 20

        performance["score"] = score

        issues = []
        if performance["html_size_kb"] > 200:
            issues.append("Large HTML size")
        if not performance["has_minified_css"]:
            issues.append("CSS not minified")
        if not performance["has_minified_js"]:
            issues.append("JavaScript not minified")

        performance["issues"] = issues

        return performance

    async def _analyze_market_tech(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market technology trends"""
        if not profiles:
            return {}

        # CMS distribution
        cms_usage = {}
        for p in profiles:
            cms = p.get("cms", "Unknown")
            cms_usage[cms] = cms_usage.get(cms, 0) + 1

        # Technology adoption
        all_technologies = []
        for p in profiles:
            all_technologies.extend(p.get("technologies", []))

        tech_usage = {}
        for tech in all_technologies:
            tech_usage[tech] = tech_usage.get(tech, 0) + 1

        # SEO scores
        seo_scores = [p.get("seo_optimization", {}).get("score", 0) for p in profiles]
        avg_seo_score = sum(seo_scores) / len(seo_scores) if seo_scores else 0

        # GEO scores
        geo_scores = [p.get("geo_optimization", {}).get("ai_ready_score", 0) for p in profiles]
        avg_geo_score = sum(geo_scores) / len(geo_scores) if geo_scores else 0

        return {
            "most_popular_cms": max(cms_usage.items(), key=lambda x: x[1])[0] if cms_usage else "Unknown",
            "cms_distribution": cms_usage,
            "top_technologies": sorted(tech_usage.items(), key=lambda x: x[1], reverse=True)[:10],
            "avg_seo_score": round(avg_seo_score, 1),
            "avg_geo_score": round(avg_geo_score, 1)
        }

    async def _generate_tech_insights(
        self,
        profiles: List[Dict[str, Any]],
        market: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate actionable tech insights with financial analysis and gap analysis"""
        insights = []

        # CMS insights
        popular_cms = market.get("most_popular_cms", "Unknown")
        insights.append(f"Самая популярная CMS: {popular_cms}")

        # SEO insights
        avg_seo = market.get("avg_seo_score", 0)
        if avg_seo < 50:
            insights.append(f"Низкий уровень SEO оптимизации (средний балл: {avg_seo:.0f}/100)")
        elif avg_seo < 75:
            insights.append(f"Средний уровень SEO оптимизации (средний балл: {avg_seo:.0f}/100)")
        else:
            insights.append(f"Высокий уровень SEO оптимизации (средний балл: {avg_seo:.0f}/100)")

        # GEO insights
        avg_geo = market.get("avg_geo_score", 0)
        if avg_geo < 30:
            insights.append(f"Низкая готовность к AI/GEO (средний балл: {avg_geo:.0f}/100) - возможность для конкурентного преимущества!")
        elif avg_geo < 60:
            insights.append(f"Средняя готовность к AI/GEO (средний балл: {avg_geo:.0f}/100)")
        else:
            insights.append(f"Высокая готовность к AI/GEO (средний балл: {avg_geo:.0f}/100)")

        # Technology insights
        top_tech = market.get("top_technologies", [])
        if top_tech:
            top_3 = [tech[0] for tech in top_tech[:3]]
            insights.append(f"Популярные технологии: {', '.join(top_3)}")

        # NEW: Financial analysis for each competitor
        financial_analysis = []
        for profile in profiles:
            budget = await self._estimate_competitor_budget(profile)
            financial_analysis.append({
                "competitor": profile.get("name"),
                "budget": budget
            })

        # NEW: Gap analysis for each competitor
        gap_analysis = []
        for profile in profiles:
            gaps = await self._identify_competitive_gaps(profile)
            gap_analysis.append({
                "competitor": profile.get("name"),
                "gaps": gaps
            })

        # NEW: Industry benchmarks comparison
        industry_comparison = []
        for profile in profiles:
            comparison = await self._compare_to_industry(profile, industry="medical")
            industry_comparison.append({
                "competitor": profile.get("name"),
                "comparison": comparison
            })

        # NEW: Tech debt analysis
        tech_debt_analysis = []
        for profile in profiles:
            debt = await self._analyze_tech_debt(profile)
            tech_debt_analysis.append({
                "competitor": profile.get("name"),
                "tech_debt": debt
            })

        # NEW: Attack roadmap
        roadmap = await self._generate_attack_roadmap(gap_analysis)

        return {
            "key_findings": insights,
            "opportunities": self._identify_opportunities(profiles, market),
            "financial_analysis": financial_analysis,
            "gap_analysis": gap_analysis,
            "industry_comparison": industry_comparison,
            "tech_debt": tech_debt_analysis,
            "attack_roadmap": roadmap
        }

    async def _estimate_competitor_budget(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate competitor's monthly tech budget

        Analyzes tech stack to estimate how much competitor spends on technology.
        """
        cms = profile.get("cms", "Unknown")
        technologies = profile.get("technologies", [])
        performance = profile.get("performance", {})

        budget_signals = []
        total_min = 0
        total_max = 0

        # CMS costs
        cms_costs = {
            "WordPress": {"min": 500, "max": 2000, "signal": "Низкий бюджет - популярное решение"},
            "Custom": {"min": 5000, "max": 20000, "signal": "Высокий бюджет - custom разработка"},
            "Tilda": {"min": 100, "max": 500, "signal": "Минимальный бюджет - конструктор"},
            "1C-Bitrix": {"min": 2000, "max": 8000, "signal": "Средний бюджет - корпоративное решение"},
            "Wix": {"min": 50, "max": 300, "signal": "Минимальный бюджет - конструктор"},
            "Shopify": {"min": 1000, "max": 5000, "signal": "Средний бюджет - e-commerce платформа"}
        }

        if cms in cms_costs:
            cost = cms_costs[cms]
            budget_signals.append({
                "category": "CMS",
                "item": cms,
                "min": cost["min"],
                "max": cost["max"],
                "signal": cost["signal"]
            })
            total_min += cost["min"]
            total_max += cost["max"]

        # Frontend framework costs (indicates developer salary)
        if "React" in technologies or "Vue.js" in technologies or "Angular" in technologies:
            budget_signals.append({
                "category": "Frontend Development",
                "item": "Modern framework",
                "min": 3000,
                "max": 10000,
                "signal": "Есть frontend разработчик"
            })
            total_min += 3000
            total_max += 10000

        # Infrastructure costs
        if performance.get("uses_cdn"):
            budget_signals.append({
                "category": "Infrastructure",
                "item": "CDN",
                "min": 500,
                "max": 2000,
                "signal": "Инвестируют в производительность"
            })
            total_min += 500
            total_max += 2000

        # Analytics costs (indicates marketing maturity)
        has_analytics = "Google Analytics" in technologies or "Яндекс.Метрика" in technologies
        if has_analytics:
            budget_signals.append({
                "category": "Marketing",
                "item": "Analytics",
                "min": 0,
                "max": 500,
                "signal": "Есть маркетолог или аналитик"
            })
            total_max += 500

        # Determine budget level
        if total_min > 5000:
            budget_level = "high"
            maturity = "Зрелая компания с хорошим финансированием"
        elif total_min > 1000:
            budget_level = "medium"
            maturity = "Средняя компания, стандартный бюджет"
        else:
            budget_level = "low"
            maturity = "Стартап или малый бизнес, минимальный бюджет"

        return {
            "estimated_monthly_min": total_min,
            "estimated_monthly_max": total_max,
            "budget_level": budget_level,
            "maturity": maturity,
            "signals": budget_signals,
            "interpretation": f"Конкурент тратит ${total_min:,}-${total_max:,}/мес на технологии"
        }

    async def _identify_competitive_gaps(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify competitive gaps = our opportunities

        Finds what competitor is NOT doing, prioritized by Impact/Effort matrix.
        """
        gaps = []

        seo = profile.get("seo_optimization", {})
        geo = profile.get("geo_optimization", {})
        performance = profile.get("performance", {})
        technologies = profile.get("technologies", [])

        # SEO gaps
        if not seo.get("has_schema"):
            gaps.append({
                "gap": "No Schema.org markup",
                "opportunity": "Захватить AI трафик (Google AI Overviews, ChatGPT)",
                "action": "Добавить Schema.org разметку (Organization, LocalBusiness, Service)",
                "impact": 9,  # 1-10
                "effort": 2,  # 1-10
                "priority": "CRITICAL",
                "time_to_implement": "1 день",
                "competitive_advantage_months": 12,
                "why_critical": "Google AI Overviews используют Schema.org для ответов. Кто первый добавит - получит весь AI трафик."
            })

        if not seo.get("has_meta_description"):
            gaps.append({
                "gap": "No meta description",
                "opportunity": "Лучшие сниппеты в поиске → выше CTR",
                "action": "Написать уникальные meta descriptions для всех страниц",
                "impact": 6,
                "effort": 1,
                "priority": "HIGH",
                "time_to_implement": "2 часа",
                "competitive_advantage_months": 3
            })

        # GEO gaps (AI optimization)
        if not geo.get("has_faq_schema"):
            gaps.append({
                "gap": "No FAQ Schema",
                "opportunity": "Появляться в AI ответах на вопросы пользователей",
                "action": "Создать FAQ страницу с Schema.org разметкой",
                "impact": 10,
                "effort": 1,
                "priority": "CRITICAL",
                "time_to_implement": "2 часа",
                "competitive_advantage_months": 12,
                "why_critical": "ChatGPT, Perplexity, Google AI берут ответы из FAQ Schema. Это новый канал трафика!"
            })

        if not geo.get("has_local_business"):
            gaps.append({
                "gap": "No LocalBusiness Schema",
                "opportunity": "Локальное SEO + карты Google",
                "action": "Добавить LocalBusiness Schema с адресом, телефоном, часами работы",
                "impact": 8,
                "effort": 2,
                "priority": "HIGH",
                "time_to_implement": "3 часа",
                "competitive_advantage_months": 6
            })

        # Performance gaps
        if not performance.get("uses_cdn"):
            gaps.append({
                "gap": "No CDN",
                "opportunity": "Быстрее загружаться → меньше bounce rate",
                "action": "Подключить Cloudflare или другой CDN",
                "impact": 7,
                "effort": 3,
                "priority": "MEDIUM",
                "time_to_implement": "1 день",
                "competitive_advantage_months": 6
            })

        if not performance.get("has_minified_css") or not performance.get("has_minified_js"):
            gaps.append({
                "gap": "No minification",
                "opportunity": "Быстрее загружаться → лучше Core Web Vitals",
                "action": "Настроить минификацию CSS/JS в build процессе",
                "impact": 5,
                "effort": 2,
                "priority": "MEDIUM",
                "time_to_implement": "4 часа",
                "competitive_advantage_months": 3
            })

        # Analytics gaps
        has_analytics = "Google Analytics" in technologies or "Яндекс.Метрика" in technologies
        if not has_analytics:
            gaps.append({
                "gap": "No analytics",
                "opportunity": "Data-driven решения vs слепые решения конкурента",
                "action": "Установить Google Analytics и Яндекс.Метрику",
                "impact": 9,
                "effort": 1,
                "priority": "CRITICAL",
                "time_to_implement": "1 час",
                "competitive_advantage_months": 999,  # Постоянное преимущество
                "why_critical": "Конкурент работает вслепую - не знает откуда клиенты, что работает, что нет"
            })

        # Sort by priority score (impact / effort)
        for gap in gaps:
            gap["priority_score"] = gap["impact"] / gap["effort"]

        gaps.sort(key=lambda x: x["priority_score"], reverse=True)

        return gaps

    async def _compare_to_industry(self, profile: Dict[str, Any], industry: str = "medical") -> Dict[str, Any]:
        """Compare competitor to industry benchmarks

        Shows if competitor is above or below average in their industry.
        """
        # Industry benchmarks (medical/dental clinics)
        benchmarks = {
            "medical": {
                "avg_seo_score": 45,
                "avg_geo_score": 15,
                "schema_adoption": 10,  # Only 10% have Schema.org
                "online_booking_adoption": 40,  # 40% have online booking
                "analytics_adoption": 60,  # 60% have analytics
                "cdn_adoption": 30  # 30% use CDN
            }
        }

        bench = benchmarks.get(industry, benchmarks["medical"])

        seo_score = profile.get("seo_optimization", {}).get("score", 0)
        geo_score = profile.get("geo_optimization", {}).get("ai_ready_score", 0)

        seo_diff = seo_score - bench["avg_seo_score"]
        geo_diff = geo_score - bench["avg_geo_score"]

        # Determine position
        if seo_diff < -20:
            seo_position = "Значительно ниже среднего"
            seo_verdict = "Легко обойти"
        elif seo_diff < 0:
            seo_position = "Ниже среднего"
            seo_verdict = "Можно обойти"
        elif seo_diff < 20:
            seo_position = "Выше среднего"
            seo_verdict = "Нужны усилия"
        else:
            seo_position = "Значительно выше среднего"
            seo_verdict = "Сильный конкурент"

        if geo_diff < -10:
            geo_position = "Значительно ниже среднего"
            geo_verdict = "Огромная возможность в AI/GEO"
        elif geo_diff < 0:
            geo_position = "Ниже среднего"
            geo_verdict = "Хорошая возможность в AI/GEO"
        else:
            geo_position = "Выше среднего"
            geo_verdict = "Конкурент готов к AI"

        return {
            "industry": industry,
            "seo": {
                "competitor_score": seo_score,
                "industry_avg": bench["avg_seo_score"],
                "difference": seo_diff,
                "position": seo_position,
                "verdict": seo_verdict
            },
            "geo": {
                "competitor_score": geo_score,
                "industry_avg": bench["avg_geo_score"],
                "difference": geo_diff,
                "position": geo_position,
                "verdict": geo_verdict
            },
            "benchmarks": bench,
            "overall_verdict": f"{seo_verdict} по SEO, {geo_verdict}"
        }

    async def _analyze_tech_debt(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitor's technical debt

        Identifies problems that will slow down competitor in the future.
        """
        technologies = profile.get("technologies", [])
        performance = profile.get("performance", {})

        debt_items = []

        # Old libraries
        if "jQuery" in technologies:
            debt_items.append({
                "issue": "jQuery detected",
                "problem": "Устаревшая библиотека (2006)",
                "impact": "Сложно нанять разработчиков, медленная разработка",
                "severity": "medium"
            })

        # No modern framework
        has_modern_framework = any(fw in technologies for fw in ["React", "Vue.js", "Angular", "Next.js", "Nuxt.js"])
        if not has_modern_framework and technologies:
            debt_items.append({
                "issue": "No modern frontend framework",
                "problem": "Vanilla JS или старые подходы",
                "impact": "Сложно масштабировать, медленная разработка новых фич",
                "severity": "high"
            })

        # Performance debt
        if not performance.get("has_minified_css"):
            debt_items.append({
                "issue": "CSS not minified",
                "problem": "Нет build процесса",
                "impact": "Медленная загрузка, плохой DX",
                "severity": "low"
            })

        if not performance.get("uses_cdn"):
            debt_items.append({
                "issue": "No CDN",
                "problem": "Все файлы с одного сервера",
                "impact": "Медленно в регионах, высокая нагрузка на сервер",
                "severity": "medium"
            })

        # Calculate total debt score
        severity_scores = {"low": 1, "medium": 3, "high": 5}
        total_debt_score = sum(severity_scores[item["severity"]] for item in debt_items)

        if total_debt_score > 10:
            debt_level = "high"
            interpretation = "Высокий технический долг - конкурент будет медленно развиваться"
        elif total_debt_score > 5:
            debt_level = "medium"
            interpretation = "Средний технический долг - есть проблемы"
        else:
            debt_level = "low"
            interpretation = "Низкий технический долг - конкурент в хорошей форме"

        return {
            "debt_items": debt_items,
            "total_debt_score": total_debt_score,
            "debt_level": debt_level,
            "interpretation": interpretation
        }

    async def _generate_attack_roadmap(self, gap_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate step-by-step roadmap to outcompete competitors

        Prioritizes actions by Impact/Effort and creates timeline.
        """
        # gap_analysis is already a list of gaps
        sorted_gaps = sorted(gap_analysis, key=lambda x: x.get("impact", 0) / max(x.get("effort", 1), 1), reverse=True)

        # Build roadmap
        week_1_actions = []
        week_2_actions = []
        month_1_actions = []

        for gap in sorted_gaps:
            time = gap.get("time_to_implement", "")
            priority = gap.get("priority", "")

            action = f"{gap.get('action', gap.get('opportunity', 'Unknown'))}"

            # Distribute by time
            if "час" in time or priority == "CRITICAL":
                week_1_actions.append(action)
            elif "день" in time or priority == "HIGH":
                week_2_actions.append(action)
            else:
                month_1_actions.append(action)

        return {
            "week_1": {
                "focus": "Quick Wins (критические возможности)",
                "actions": week_1_actions[:3],  # Top 3
                "expected_impact": "Захват AI трафика, базовая аналитика"
            },
            "week_2": {
                "focus": "Техническая оптимизация",
                "actions": week_2_actions[:3],  # Top 3
                "expected_impact": "Производительность, SEO улучшения"
            },
            "month_1": {
                "focus": "Долгосрочные преимущества",
                "actions": month_1_actions[:3],  # Top 3
                "expected_impact": "Устойчивое конкурентное преимущество"
            },
            "total_opportunities": len(sorted_gaps),
            "critical_count": len([g for g in sorted_gaps if g.get("priority") == "CRITICAL"]),
            "high_count": len([g for g in sorted_gaps if g.get("priority") == "HIGH"])
        }

    def _identify_opportunities(
        self,
        profiles: List[Dict[str, Any]],
        market: Dict[str, Any]
    ) -> List[str]:
        """Identify competitive opportunities"""
        opportunities = []

        avg_seo = market.get("avg_seo_score", 0)
        avg_geo = market.get("avg_geo_score", 0)

        if avg_seo < 60:
            opportunities.append("Возможность обойти конкурентов по SEO оптимизации")

        if avg_geo < 40:
            opportunities.append("Большая возможность в AI/GEO оптимизации - конкуренты не готовы")

        # Check for missing technologies
        analytics_count = sum(1 for p in profiles if "Google Analytics" in p.get("technologies", []) or "Яндекс.Метрика" in p.get("technologies", []))
        if analytics_count < len(profiles) * 0.5:
            opportunities.append("Многие конкуренты не используют аналитику - возможность для data-driven подхода")

        return opportunities

    async def _save_results(self, results: Dict[str, Any]) -> None:
        """Save results to JSON and Obsidian"""
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = self.data_path / f"tech_analysis_{timestamp}.json"

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Tech] Results saved to {json_file}")

        # Save to Obsidian vault
        # TODO: Format and save to vault

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return [
            "tech_stack_analysis",
            "cms_detection",
            "technology_detection",
            "seo_analysis",
            "geo_optimization_analysis",
            "performance_analysis",
            "market_tech_analysis"
        ]
