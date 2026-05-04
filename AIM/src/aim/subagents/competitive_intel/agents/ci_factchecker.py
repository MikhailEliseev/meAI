"""
CI Factchecker Agent - Data Validation and Fact Checking

Проверяет достоверность данных от всех CI агентов:
- Кросс-проверка данных из разных источников
- Выявление противоречий
- Оценка надёжности источников
- Валидация метрик и цифр
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIFactcheckerAgent(Agent):
    """
    CI Factchecker - агент проверки фактов и данных.

    Фаза 6 CI pipeline:
    - Кросс-проверка данных из разных источников
    - Выявление противоречий и несоответствий
    - Оценка надёжности источников
    - Валидация метрик, цифр и утверждений
    - Присвоение confidence scores
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-factchecker",
            database_url=database_url,
            vault_path=vault_path
        )
        # Переопределяем vault на специфичный для CI Factchecker
        self.vault = ObsidianVault("AIM/obsidian/ci-factchecker")

        # Source reliability tiers
        self.source_reliability = {
            "tier1": {
                "name": "Высоконадёжные",
                "sources": ["yandex_maps", "2gis", "official_website"],
                "confidence": 0.95
            },
            "tier2": {
                "name": "Надёжные",
                "sources": ["prodoctorov", "zoon", "napopravku"],
                "confidence": 0.85
            },
            "tier3": {
                "name": "Средненадёжные",
                "sources": ["social_media", "forums", "blogs"],
                "confidence": 0.70
            },
            "tier4": {
                "name": "Низконадёжные",
                "sources": ["anonymous_reviews", "unverified_sources"],
                "confidence": 0.50
            }
        }

        # Validation rules
        self.validation_rules = {
            "rating": {
                "min": 1.0,
                "max": 5.0,
                "type": "float"
            },
            "review_count": {
                "min": 0,
                "max": 10000,
                "type": "int"
            },
            "price": {
                "min": 0,
                "max": 1000000,
                "type": "int"
            },
            "score": {
                "min": 0,
                "max": 100,
                "type": "float"
            }
        }

        # Contradiction types
        self.contradiction_types = {
            "rating_mismatch": "Несоответствие рейтингов из разных источников",
            "count_mismatch": "Несоответствие количества отзывов",
            "data_conflict": "Конфликт данных",
            "temporal_inconsistency": "Временная несогласованность"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить проверку фактов.

        Args:
            task: Задача с payload:
                - previous_results: результаты от предыдущих агентов (обязательно)

        Returns:
            TaskResult с результатами проверки
        """
        try:
            previous_results = task.payload.get("previous_results", {})

            # Логирование начала
            print(f"[CI Factchecker] Начало проверки фактов")

            # Шаг 1: Extract all facts and data points
            facts = await self._extract_facts(previous_results)

            # Шаг 2: Cross-validate data from different sources
            validation_results = await self._cross_validate(facts)

            # Шаг 3: Identify contradictions
            contradictions = await self._identify_contradictions(facts, validation_results)

            # Шаг 4: Assess source reliability
            reliability_scores = await self._assess_reliability(facts)

            # Шаг 5: Calculate confidence scores
            confidence_scores = await self._calculate_confidence(
                facts, validation_results, reliability_scores
            )

            # Шаг 6: Generate validation report
            report = await self._generate_report(
                facts, validation_results, contradictions, reliability_scores, confidence_scores
            )

            # Шаг 7: Save results
            results = {
                "validation_date": datetime.now().isoformat(),
                "total_facts_checked": len(facts),
                "validation_results": validation_results,
                "contradictions": contradictions,
                "reliability_scores": reliability_scores,
                "confidence_scores": confidence_scores,
                "report": report
            }

            await self._save_results(results)

            # Логирование завершения
            print(f"[CI Factchecker] Проверка фактов завершена: {len(facts)} фактов, {len(contradictions)} противоречий")

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
            print(f"[CI Factchecker] Ошибка: {e}")
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

    async def _extract_facts(
        self,
        previous_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Извлечь все факты и данные из результатов предыдущих фаз.

        Args:
            previous_results: результаты от Scout, Auditor, Reputation и др.

        Returns:
            Список фактов для проверки
        """
        print(f"[CI Factchecker] Извлечение фактов из {len(previous_results)} фаз")

        facts = []

        # Извлечь факты из Scout (Phase 1)
        if "phase_1" in previous_results:
            scout_data = previous_results["phase_1"]

            # Факты о конкурентах
            for competitor in scout_data.get("competitors", []):
                facts.append({
                    "type": "competitor_profile",
                    "source": "scout",
                    "phase": 1,
                    "competitor": competitor.get("name"),
                    "data": {
                        "name": competitor.get("name"),
                        "cluster": competitor.get("cluster"),
                        "price_segment": competitor.get("price_segment")
                    }
                })

        # Извлечь факты из Auditor (Phase 2-3)
        if "phase_2" in previous_results:
            auditor_data = previous_results["phase_2"]

            for audit in auditor_data.get("audits", []):
                facts.append({
                    "type": "audit_score",
                    "source": "auditor",
                    "phase": 2,
                    "competitor": audit.get("name"),
                    "data": {
                        "total_score": audit.get("total_score"),
                        "grade": audit.get("grade"),
                        "dimension_scores": audit.get("dimension_scores", {})
                    }
                })

        # Извлечь факты из Reputation (Phase 4)
        if "phase_4" in previous_results:
            reputation_data = previous_results["phase_4"]

            for review_data in reputation_data.get("reviews_data", []):
                facts.append({
                    "type": "reputation_data",
                    "source": "reputation",
                    "phase": 4,
                    "competitor": review_data.get("name"),
                    "data": {
                        "total_reviews": review_data.get("total_reviews"),
                        "avg_rating": review_data.get("avg_rating"),
                        "sources": review_data.get("sources", {})
                    }
                })

        return facts

    async def _cross_validate(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Кросс-проверка данных из разных источников.

        Args:
            facts: список фактов

        Returns:
            Результаты валидации
        """
        print(f"[CI Factchecker] Кросс-проверка {len(facts)} фактов")

        validation_results = {
            "validated": [],
            "failed": [],
            "warnings": []
        }

        for fact in facts:
            # Валидация по типу факта
            if fact["type"] == "audit_score":
                result = self._validate_score(fact)
            elif fact["type"] == "reputation_data":
                result = self._validate_reputation(fact)
            elif fact["type"] == "competitor_profile":
                result = self._validate_profile(fact)
            else:
                result = {"status": "skipped", "reason": "unknown type"}

            if result["status"] == "valid":
                validation_results["validated"].append({
                    "fact": fact,
                    "result": result
                })
            elif result["status"] == "invalid":
                validation_results["failed"].append({
                    "fact": fact,
                    "result": result
                })
            elif result["status"] == "warning":
                validation_results["warnings"].append({
                    "fact": fact,
                    "result": result
                })

        print(f"[CI Factchecker] Валидация: {len(validation_results['validated'])} OK, "
              f"{len(validation_results['failed'])} failed, {len(validation_results['warnings'])} warnings")

        return validation_results

    def _validate_score(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация score данных."""
        data = fact["data"]
        total_score = data.get("total_score", 0)

        # Проверка диапазона
        if not (0 <= total_score <= 100):
            return {
                "status": "invalid",
                "reason": f"Score {total_score} вне диапазона [0, 100]"
            }

        # Проверка согласованности с grade
        grade = data.get("grade")
        expected_grade = self._score_to_grade(total_score)

        if grade != expected_grade:
            return {
                "status": "warning",
                "reason": f"Grade {grade} не соответствует score {total_score} (ожидается {expected_grade})"
            }

        return {"status": "valid"}

    def _score_to_grade(self, score: float) -> str:
        """Конвертировать score в grade."""
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        else:
            return "D"

    def _validate_reputation(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация reputation данных."""
        data = fact["data"]
        avg_rating = data.get("avg_rating", 0)
        total_reviews = data.get("total_reviews", 0)

        # Проверка рейтинга
        if not (1.0 <= avg_rating <= 5.0):
            return {
                "status": "invalid",
                "reason": f"Rating {avg_rating} вне диапазона [1.0, 5.0]"
            }

        # Проверка количества отзывов
        if total_reviews < 0:
            return {
                "status": "invalid",
                "reason": f"Negative review count: {total_reviews}"
            }

        # Проверка согласованности с источниками
        sources = data.get("sources", {})
        calculated_total = sum(s.get("count", 0) for s in sources.values())

        if abs(calculated_total - total_reviews) > 5:  # Допуск 5 отзывов
            return {
                "status": "warning",
                "reason": f"Total reviews {total_reviews} не соответствует сумме по источникам {calculated_total}"
            }

        return {"status": "valid"}

    def _validate_profile(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация profile данных."""
        data = fact["data"]
        name = data.get("name")
        cluster = data.get("cluster")
        price_segment = data.get("price_segment")

        # Проверка обязательных полей
        if not name:
            return {
                "status": "invalid",
                "reason": "Missing competitor name"
            }

        # Проверка допустимых значений
        valid_clusters = ["direct", "indirect", "leader", "niche", "emerging"]
        if cluster not in valid_clusters:
            return {
                "status": "warning",
                "reason": f"Unknown cluster: {cluster}"
            }

        valid_segments = ["budget", "mid", "premium"]
        if price_segment not in valid_segments:
            return {
                "status": "warning",
                "reason": f"Unknown price segment: {price_segment}"
            }

        return {"status": "valid"}

    async def _identify_contradictions(
        self,
        facts: List[Dict[str, Any]],
        validation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Выявить противоречия в данных.

        Args:
            facts: список фактов
            validation_results: результаты валидации

        Returns:
            Список противоречий
        """
        print(f"[CI Factchecker] Поиск противоречий")

        contradictions = []

        # Группировать факты по конкурентам
        facts_by_competitor = {}
        for fact in facts:
            competitor = fact.get("competitor")
            if competitor:
                if competitor not in facts_by_competitor:
                    facts_by_competitor[competitor] = []
                facts_by_competitor[competitor].append(fact)

        # Проверить противоречия для каждого конкурента
        for competitor, competitor_facts in facts_by_competitor.items():
            # Проверить рейтинги из разных источников
            ratings = []
            for fact in competitor_facts:
                if fact["type"] == "reputation_data":
                    sources = fact["data"].get("sources", {})
                    for source_name, source_data in sources.items():
                        ratings.append({
                            "source": source_name,
                            "rating": source_data.get("avg_rating", 0)
                        })

            # Если разброс рейтингов > 0.5, это противоречие
            if len(ratings) >= 2:
                rating_values = [r["rating"] for r in ratings]
                rating_spread = max(rating_values) - min(rating_values)

                if rating_spread > 0.5:
                    contradictions.append({
                        "type": "rating_mismatch",
                        "competitor": competitor,
                        "description": f"Разброс рейтингов {rating_spread:.1f} (от {min(rating_values):.1f} до {max(rating_values):.1f})",
                        "severity": "medium" if rating_spread < 1.0 else "high",
                        "sources": [r["source"] for r in ratings]
                    })

        print(f"[CI Factchecker] Найдено {len(contradictions)} противоречий")

        return contradictions

    async def _assess_reliability(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Оценить надёжность источников.

        Args:
            facts: список фактов

        Returns:
            Reliability scores по источникам
        """
        print(f"[CI Factchecker] Оценка надёжности источников")

        reliability_scores = {}

        for fact in facts:
            source = fact.get("source")

            # Определить tier источника
            tier = self._get_source_tier(source)
            confidence = self.source_reliability[tier]["confidence"]

            if source not in reliability_scores:
                reliability_scores[source] = confidence

        return reliability_scores

    def _get_source_tier(self, source: str) -> str:
        """Определить tier источника."""
        for tier, tier_data in self.source_reliability.items():
            if source in tier_data["sources"]:
                return tier

        # По умолчанию tier3
        return "tier3"

    async def _calculate_confidence(
        self,
        facts: List[Dict[str, Any]],
        validation_results: Dict[str, Any],
        reliability_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Рассчитать confidence scores для данных.

        Args:
            facts: список фактов
            validation_results: результаты валидации
            reliability_scores: надёжность источников

        Returns:
            Confidence scores
        """
        print(f"[CI Factchecker] Расчёт confidence scores")

        confidence_scores = {}

        # Группировать по конкурентам
        for fact in facts:
            competitor = fact.get("competitor")
            if not competitor:
                continue

            source = fact.get("source")
            source_reliability = reliability_scores.get(source, 0.7)

            # Базовая confidence = надёжность источника
            confidence = source_reliability

            # Снизить confidence если есть warnings
            for warning in validation_results.get("warnings", []):
                if warning["fact"].get("competitor") == competitor:
                    confidence *= 0.9

            # Снизить confidence если есть failed validations
            for failed in validation_results.get("failed", []):
                if failed["fact"].get("competitor") == competitor:
                    confidence *= 0.7

            # Сохранить максимальную confidence для конкурента
            if competitor not in confidence_scores or confidence > confidence_scores[competitor]:
                confidence_scores[competitor] = round(confidence, 2)

        return confidence_scores

    async def _generate_report(
        self,
        facts: List[Dict[str, Any]],
        validation_results: Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        reliability_scores: Dict[str, float],
        confidence_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Сгенерировать отчёт о проверке.

        Args:
            facts: список фактов
            validation_results: результаты валидации
            contradictions: противоречия
            reliability_scores: надёжность источников
            confidence_scores: confidence scores

        Returns:
            Отчёт
        """
        print(f"[CI Factchecker] Генерация отчёта")

        report = {
            "summary": {
                "total_facts": len(facts),
                "validated": len(validation_results["validated"]),
                "failed": len(validation_results["failed"]),
                "warnings": len(validation_results["warnings"]),
                "contradictions": len(contradictions)
            },
            "data_quality": self._assess_data_quality(validation_results, contradictions),
            "reliability_assessment": {
                "sources": reliability_scores,
                "avg_reliability": round(sum(reliability_scores.values()) / len(reliability_scores), 2) if reliability_scores else 0
            },
            "confidence_assessment": {
                "competitors": confidence_scores,
                "avg_confidence": round(sum(confidence_scores.values()) / len(confidence_scores), 2) if confidence_scores else 0
            },
            "recommendations": self._generate_recommendations(validation_results, contradictions)
        }

        return report

    def _assess_data_quality(
        self,
        validation_results: Dict[str, Any],
        contradictions: List[Dict[str, Any]]
    ) -> str:
        """Оценить качество данных."""
        total = len(validation_results["validated"]) + len(validation_results["failed"]) + len(validation_results["warnings"])

        if total == 0:
            return "unknown"

        valid_pct = len(validation_results["validated"]) / total * 100

        if valid_pct >= 95 and len(contradictions) == 0:
            return "excellent"
        elif valid_pct >= 85 and len(contradictions) <= 2:
            return "good"
        elif valid_pct >= 70:
            return "acceptable"
        else:
            return "poor"

    def _generate_recommendations(
        self,
        validation_results: Dict[str, Any],
        contradictions: List[Dict[str, Any]]
    ) -> List[str]:
        """Сгенерировать рекомендации."""
        recommendations = []

        if len(validation_results["failed"]) > 0:
            recommendations.append("Пересобрать данные для фактов с failed validation")

        if len(contradictions) > 0:
            recommendations.append("Разрешить противоречия через дополнительные источники")

        if len(validation_results["warnings"]) > 5:
            recommendations.append("Проверить качество сбора данных")

        if not recommendations:
            recommendations.append("Данные прошли проверку, можно использовать для анализа")

        return recommendations

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-factcheck.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Factchecker] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "fact_extraction",
            "cross_validation",
            "contradiction_detection",
            "source_reliability_assessment",
            "confidence_scoring",
            "data_quality_assessment"
        ]
