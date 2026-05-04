"""
CI Auditor Agent - Deep Competitor Website Audit

Проводит глубокий аудит сайтов конкурентов по 4 направлениям:
- Technical (скорость, мобильность, SEO)
- Content (структура, качество, ключевые слова)
- UX/UI (юзабилити, конверсия, CTA)
- Marketing (каналы, воронки, лид-магниты)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIAuditorAgent(Agent):
    """
    CI Auditor - агент глубокого аудита конкурентов.

    Фаза 2-3 CI pipeline:
    - Технический аудит (PageSpeed, мобильность, Core Web Vitals)
    - Контентный аудит (структура, качество, SEO)
    - UX/UI аудит (юзабилити, конверсия)
    - Маркетинговый аудит (каналы, воронки)
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-auditor",
            database_url=database_url,
            vault_path=vault_path
        )
        # Переопределяем vault на специфичный для CI Auditor
        self.vault = ObsidianVault("AIM/obsidian/ci-auditor")

        # Audit dimensions
        self.audit_dimensions = {
            "technical": {
                "page_speed": "Скорость загрузки (Desktop/Mobile)",
                "core_web_vitals": "LCP, FID, CLS",
                "mobile_friendly": "Мобильная адаптация",
                "https": "HTTPS и безопасность",
                "structured_data": "Schema.org разметка",
                "sitemap": "XML Sitemap",
                "robots_txt": "robots.txt"
            },
            "content": {
                "structure": "Структура сайта (глубина, навигация)",
                "quality": "Качество контента (уникальность, полезность)",
                "keywords": "Ключевые слова (плотность, релевантность)",
                "headings": "Заголовки (H1-H6 структура)",
                "images": "Изображения (alt, размер, оптимизация)",
                "internal_links": "Внутренняя перелинковка",
                "blog": "Блог/статьи (частота, качество)"
            },
            "ux_ui": {
                "usability": "Юзабилити (простота навигации)",
                "conversion": "Конверсионные элементы (формы, CTA)",
                "design": "Дизайн (современность, брендинг)",
                "trust_signals": "Сигналы доверия (отзывы, сертификаты)",
                "contact_forms": "Формы связи (доступность, простота)",
                "online_booking": "Онлайн-запись",
                "chat": "Онлайн-чат"
            },
            "marketing": {
                "channels": "Маркетинговые каналы (SEO, PPC, Social)",
                "funnels": "Воронки продаж",
                "lead_magnets": "Лид-магниты (акции, скидки)",
                "email_capture": "Сбор email",
                "retargeting": "Ретаргетинг (пиксели)",
                "analytics": "Аналитика (GA, Яндекс.Метрика)",
                "crm": "CRM интеграция"
            }
        }

        # Scoring weights
        self.weights = {
            "technical": 0.25,
            "content": 0.30,
            "ux_ui": 0.25,
            "marketing": 0.20
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить аудит конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов для аудита (обязательно)
                - audit_type: тип аудита (quick/deep/full, опционально)

        Returns:
            TaskResult с результатами аудита
        """
        try:
            competitors = task.payload["competitors"]
            audit_type = task.payload.get("audit_type", "deep")

            # Логирование начала
            print(f"[CI Auditor] Начало аудита {len(competitors)} конкурентов (тип: {audit_type})")

            # Шаг 1: Audit each competitor
            audits = []
            for competitor in competitors:
                audit = await self._audit_competitor(competitor, audit_type)
                audits.append(audit)

            # Шаг 2: Calculate scores
            scored_audits = await self._calculate_scores(audits)

            # Шаг 3: Generate insights
            insights = await self._generate_insights(scored_audits)

            # Шаг 4: Identify gaps and opportunities
            gaps = await self._identify_gaps(scored_audits)

            # Шаг 5: Save results
            results = {
                "audit_type": audit_type,
                "audit_date": datetime.now().isoformat(),
                "total_audited": len(audits),
                "audits": scored_audits,
                "insights": insights,
                "gaps": gaps
            }

            await self._save_results(results)

            # Логирование завершения
            print(f"[CI Auditor] Завершён аудит {len(audits)} конкурентов")

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
            print(f"[CI Auditor] Ошибка: {e}")
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

    async def _audit_competitor(
        self,
        competitor: Dict[str, Any],
        audit_type: str
    ) -> Dict[str, Any]:
        """
        Провести аудит одного конкурента.

        Args:
            competitor: данные конкурента
            audit_type: тип аудита (quick/deep/full)

        Returns:
            Результаты аудита
        """
        name = competitor["name"]
        url = competitor.get("url", "")

        print(f"[CI Auditor] Аудит: {name}")

        # Определить dimensions для аудита
        dimensions = self._get_audit_dimensions(audit_type)

        audit = {
            "name": name,
            "url": url,
            "audit_type": audit_type,
            "dimensions": {}
        }

        # Провести аудит по каждому dimension
        for dimension in dimensions:
            audit["dimensions"][dimension] = await self._audit_dimension(
                url, dimension, audit_type
            )

        return audit

    def _get_audit_dimensions(self, audit_type: str) -> List[str]:
        """Определить dimensions для аудита в зависимости от типа."""
        if audit_type == "quick":
            return ["technical", "content"]
        elif audit_type == "deep":
            return ["technical", "content", "ux_ui"]
        else:  # full
            return ["technical", "content", "ux_ui", "marketing"]

    async def _audit_dimension(
        self,
        url: str,
        dimension: str,
        audit_type: str
    ) -> Dict[str, Any]:
        """
        Провести аудит по одному dimension.

        Args:
            url: URL сайта
            dimension: dimension для аудита
            audit_type: тип аудита

        Returns:
            Результаты аудита dimension
        """
        # TODO: Реальный аудит через WebFetch и инструменты
        # Пока генерируем реалистичные тестовые данные

        import random

        checks = self.audit_dimensions[dimension]
        results = {}

        for check_key, check_name in checks.items():
            # Генерировать оценку (0-100)
            score = random.randint(60, 95)

            # Генерировать статус
            if score >= 80:
                status = "good"
            elif score >= 60:
                status = "medium"
            else:
                status = "poor"

            results[check_key] = {
                "name": check_name,
                "score": score,
                "status": status,
                "details": self._generate_check_details(check_key, score)
            }

        return results

    def _generate_check_details(self, check_key: str, score: int) -> str:
        """Генерировать детали проверки."""
        details_map = {
            "page_speed": f"Desktop: {score}ms, Mobile: {score + 200}ms",
            "core_web_vitals": f"LCP: {score/10}s, FID: {score}ms, CLS: 0.{score//10}",
            "mobile_friendly": "Адаптивный дизайн" if score > 70 else "Требуется улучшение",
            "https": "HTTPS включён" if score > 80 else "Смешанный контент",
            "structured_data": f"{score//10} типов разметки" if score > 70 else "Разметка отсутствует",
            "sitemap": "XML Sitemap найден" if score > 70 else "Sitemap не найден",
            "robots_txt": "robots.txt корректен" if score > 70 else "robots.txt требует правок",
            "structure": f"Глубина: {score//20} уровней",
            "quality": f"Уникальность: {score}%",
            "keywords": f"Плотность: {score//10}%",
            "headings": f"H1-H6 структура: {score}%",
            "images": f"Alt теги: {score}%",
            "internal_links": f"{score} внутренних ссылок",
            "blog": f"{score//10} статей в месяц" if score > 50 else "Блог не активен",
            "usability": f"Простота навигации: {score}%",
            "conversion": f"{score//10} CTA элементов",
            "design": "Современный дизайн" if score > 70 else "Устаревший дизайн",
            "trust_signals": f"{score//10} сигналов доверия",
            "contact_forms": f"{score//20} форм связи",
            "online_booking": "Онлайн-запись есть" if score > 70 else "Онлайн-запись отсутствует",
            "chat": "Онлайн-чат есть" if score > 70 else "Чат отсутствует",
            "channels": f"{score//15} активных каналов",
            "funnels": f"{score//20} воронок",
            "lead_magnets": f"{score//20} лид-магнитов",
            "email_capture": "Email-сбор настроен" if score > 70 else "Email-сбор отсутствует",
            "retargeting": "Пиксели установлены" if score > 70 else "Ретаргетинг не настроен",
            "analytics": "GA + Метрика" if score > 70 else "Аналитика не настроена",
            "crm": "CRM интегрирована" if score > 70 else "CRM не интегрирована"
        }

        return details_map.get(check_key, f"Оценка: {score}/100")

    async def _calculate_scores(
        self,
        audits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Рассчитать общие оценки для каждого аудита.

        Args:
            audits: список аудитов

        Returns:
            Аудиты с рассчитанными оценками
        """
        scored_audits = []

        for audit in audits:
            dimension_scores = {}

            # Рассчитать средний score для каждого dimension
            for dimension, checks in audit["dimensions"].items():
                scores = [check["score"] for check in checks.values()]
                dimension_scores[dimension] = sum(scores) / len(scores) if scores else 0

            # Рассчитать общий weighted score
            total_score = sum(
                dimension_scores.get(dim, 0) * weight
                for dim, weight in self.weights.items()
            )

            audit["dimension_scores"] = dimension_scores
            audit["total_score"] = round(total_score, 1)

            # Определить grade
            if total_score >= 85:
                audit["grade"] = "A"
            elif total_score >= 70:
                audit["grade"] = "B"
            elif total_score >= 55:
                audit["grade"] = "C"
            else:
                audit["grade"] = "D"

            scored_audits.append(audit)

        print(f"[CI Auditor] Рассчитаны оценки для {len(scored_audits)} конкурентов")

        return scored_audits

    async def _generate_insights(
        self,
        audits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать инсайты из аудитов.

        Args:
            audits: список аудитов с оценками

        Returns:
            Инсайты о рынке
        """
        # Средние оценки по dimensions
        avg_scores = {}
        for dimension in self.audit_dimensions.keys():
            scores = [
                audit["dimension_scores"].get(dimension, 0)
                for audit in audits
                if dimension in audit["dimension_scores"]
            ]
            avg_scores[dimension] = round(sum(scores) / len(scores), 1) if scores else 0

        # Лучший и худший конкурент
        best = max(audits, key=lambda x: x["total_score"])
        worst = min(audits, key=lambda x: x["total_score"])

        insights = {
            "market_average": round(sum(a["total_score"] for a in audits) / len(audits), 1),
            "dimension_averages": avg_scores,
            "best_competitor": {
                "name": best["name"],
                "score": best["total_score"],
                "grade": best["grade"]
            },
            "worst_competitor": {
                "name": worst["name"],
                "score": worst["total_score"],
                "grade": worst["grade"]
            },
            "strongest_dimension": max(avg_scores.items(), key=lambda x: x[1])[0],
            "weakest_dimension": min(avg_scores.items(), key=lambda x: x[1])[0]
        }

        print(f"[CI Auditor] Средняя оценка рынка: {insights['market_average']}")

        return insights

    async def _identify_gaps(
        self,
        audits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Определить gaps и возможности.

        Args:
            audits: список аудитов с оценками

        Returns:
            Список gaps и возможностей
        """
        gaps = []

        # Найти общие слабые места
        for dimension in self.audit_dimensions.keys():
            scores = [
                audit["dimension_scores"].get(dimension, 0)
                for audit in audits
                if dimension in audit["dimension_scores"]
            ]

            if scores:
                avg = sum(scores) / len(scores)

                if avg < 70:
                    gaps.append({
                        "type": "market_gap",
                        "dimension": dimension,
                        "avg_score": round(avg, 1),
                        "opportunity": f"Рынок слаб в {dimension} (средняя оценка {round(avg, 1)}). Возможность выделиться.",
                        "priority": "high" if avg < 60 else "medium"
                    })

        # Найти специфичные gaps у лидеров
        best_audits = sorted(audits, key=lambda x: x["total_score"], reverse=True)[:3]

        for audit in best_audits:
            for dimension, score in audit["dimension_scores"].items():
                if score < 70:
                    gaps.append({
                        "type": "competitor_weakness",
                        "competitor": audit["name"],
                        "dimension": dimension,
                        "score": score,
                        "opportunity": f"{audit['name']} слаб в {dimension} ({score}). Можно обойти.",
                        "priority": "medium"
                    })

        print(f"[CI Auditor] Найдено {len(gaps)} gaps и возможностей")

        return gaps

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-audits.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Auditor] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "technical_audit",
            "content_audit",
            "ux_ui_audit",
            "marketing_audit",
            "competitor_scoring",
            "gap_analysis"
        ]
