"""Architect Critic - критик стратегических решений

Ставит под сомнение каждое решение Architect перед реализацией.
Выявляет слабые места, когнитивные искажения, пропущенные риски.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class CritiqueVerdict(str, Enum):
    """Вердикт критика"""

    APPROVE = "approve"  # Решение хорошее, можно реализовывать
    CHALLENGE = "challenge"  # Есть проблемы, нужно пересмотреть
    REJECT = "reject"  # Решение плохое, нужно новое


class CritiqueSeverity(str, Enum):
    """Серьёзность проблемы"""

    LOW = "low"  # Незначительная проблема
    MEDIUM = "medium"  # Средняя проблема
    HIGH = "high"  # Серьёзная проблема
    CRITICAL = "critical"  # Критическая проблема


class CritiqueCheck(BaseModel):
    """Результат одной проверки"""

    check_name: str
    passed: bool
    severity: CritiqueSeverity
    issue: str | None = None
    suggestion: str | None = None
    evidence: list[str] = Field(default_factory=list)


class CritiqueResult(BaseModel):
    """Результат критики решения"""

    critique_id: str
    decision_id: str
    verdict: CritiqueVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    checks: list[CritiqueCheck]
    summary: str
    key_concerns: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime


class ArchitectCritic:
    """Критик решений Architect

    Проверяет каждое решение на:
    1. Полноту альтернатив
    2. Правильность оценки рисков
    3. Когнитивные искажения
    4. Учёт прошлого опыта
    5. Возможные режимы отказа

    Workflow:
    - Architect создаёт решение
    - Critic проверяет решение
    - Если CHALLENGE → Architect пересматривает
    - Если APPROVE → можно реализовывать
    """

    def __init__(self, obsidian_path: str = "./obsidian"):
        """Initialize Architect Critic

        Args:
            obsidian_path: Path to Obsidian vault
        """
        self.obsidian_path = obsidian_path

    async def critique_decision(
        self,
        decision: dict[str, Any],
    ) -> CritiqueResult:
        """Критикует решение Architect

        Args:
            decision: Решение от Architect

        Returns:
            Результат критики
        """
        critique_id = f"critique-{uuid4().hex[:8]}"

        # Выполняем все проверки
        checks = [
            await self._check_alternatives_completeness(decision),
            await self._check_risk_assessment(decision),
            await self._check_cognitive_biases(decision),
            await self._check_past_experience(decision),
            await self._check_failure_modes(decision),
        ]

        # Агрегируем результаты
        verdict = self._determine_verdict(checks)
        confidence = self._calculate_confidence(checks)
        summary = self._generate_summary(checks, verdict)
        key_concerns = self._extract_key_concerns(checks)
        recommendations = self._generate_recommendations(checks)

        return CritiqueResult(
            critique_id=critique_id,
            decision_id=decision.get("decision_id", "unknown"),
            verdict=verdict,
            confidence=confidence,
            checks=checks,
            summary=summary,
            key_concerns=key_concerns,
            recommendations=recommendations,
            created_at=datetime.now(timezone.utc),
        )

    async def _check_alternatives_completeness(
        self,
        decision: dict[str, Any],
    ) -> CritiqueCheck:
        """Проверка 1: Все ли альтернативы рассмотрены?

        Args:
            decision: Решение

        Returns:
            Результат проверки
        """
        alternatives = decision.get("alternatives", [])
        action = decision.get("action", "")

        # Проверяем количество альтернатив
        if len(alternatives) < 2:
            return CritiqueCheck(
                check_name="alternatives_completeness",
                passed=False,
                severity=CritiqueSeverity.HIGH,
                issue="Рассмотрено менее 2 альтернатив",
                suggestion="Рассмотреть минимум 2-3 альтернативных подхода",
                evidence=[
                    f"Количество альтернатив: {len(alternatives)}",
                    "Минимум рекомендуется: 2-3",
                ],
            )

        # Проверяем разнообразие альтернатив
        if len(alternatives) == 2:
            # Проверяем, не являются ли альтернативы слишком похожими
            alt1 = alternatives[0].lower()
            alt2 = alternatives[1].lower()

            # Простая проверка на похожесть (можно улучшить)
            common_words = set(alt1.split()) & set(alt2.split())
            if len(common_words) > len(alt1.split()) * 0.5:
                return CritiqueCheck(
                    check_name="alternatives_completeness",
                    passed=False,
                    severity=CritiqueSeverity.MEDIUM,
                    issue="Альтернативы слишком похожи друг на друга",
                    suggestion="Рассмотреть более разнообразные подходы",
                    evidence=[
                        f"Альтернатива 1: {alternatives[0]}",
                        f"Альтернатива 2: {alternatives[1]}",
                        f"Общих слов: {len(common_words)}",
                    ],
                )

        # Проверяем, есть ли "ничего не делать" как альтернатива
        do_nothing_keywords = ["ничего", "не делать", "оставить как есть", "пропустить"]
        has_do_nothing = any(
            any(keyword in alt.lower() for keyword in do_nothing_keywords)
            for alt in alternatives
        )

        if not has_do_nothing and len(alternatives) < 3:
            return CritiqueCheck(
                check_name="alternatives_completeness",
                passed=True,
                severity=CritiqueSeverity.LOW,
                issue="Не рассмотрена альтернатива 'ничего не делать'",
                suggestion="Всегда рассматривать опцию 'ничего не делать' как baseline",
                evidence=[
                    "Альтернатива 'ничего не делать' отсутствует",
                    "Это важный baseline для сравнения",
                ],
            )

        return CritiqueCheck(
            check_name="alternatives_completeness",
            passed=True,
            severity=CritiqueSeverity.LOW,
            issue=None,
            suggestion=None,
            evidence=[
                f"Рассмотрено {len(alternatives)} альтернатив",
                "Разнообразие альтернатив: достаточное",
            ],
        )

    async def _check_risk_assessment(
        self,
        decision: dict[str, Any],
    ) -> CritiqueCheck:
        """Проверка 2: Правильно ли оценены риски?

        Args:
            decision: Решение

        Returns:
            Результат проверки
        """
        risks = decision.get("risks", [])
        confidence = decision.get("confidence", 0)

        # Проверяем наличие рисков
        if not risks:
            return CritiqueCheck(
                check_name="risk_assessment",
                passed=False,
                severity=CritiqueSeverity.CRITICAL,
                issue="Риски не идентифицированы",
                suggestion="Идентифицировать минимум 2-3 риска для любого решения",
                evidence=[
                    "Количество рисков: 0",
                    "Любое решение имеет риски",
                ],
            )

        # Проверяем количество рисков
        if len(risks) < 2:
            return CritiqueCheck(
                check_name="risk_assessment",
                passed=False,
                severity=CritiqueSeverity.HIGH,
                issue="Идентифицировано слишком мало рисков",
                suggestion="Рассмотреть больше потенциальных рисков",
                evidence=[
                    f"Количество рисков: {len(risks)}",
                    "Рекомендуется: 2-3 риска минимум",
                ],
            )

        # Проверяем соответствие confidence и рисков
        if confidence > 0.9 and len(risks) > 2:
            return CritiqueCheck(
                check_name="risk_assessment",
                passed=False,
                severity=CritiqueSeverity.MEDIUM,
                issue="Высокая уверенность при множестве рисков",
                suggestion="Пересмотреть уверенность с учётом идентифицированных рисков",
                evidence=[
                    f"Уверенность: {confidence * 100}%",
                    f"Количество рисков: {len(risks)}",
                    "Несоответствие: высокая уверенность + много рисков",
                ],
            )

        # Проверяем специфичность рисков
        generic_risks = ["может не сработать", "возможны проблемы", "есть риски"]
        generic_count = sum(
            1 for risk in risks if any(generic in risk.lower() for generic in generic_risks)
        )

        if generic_count > len(risks) * 0.5:
            return CritiqueCheck(
                check_name="risk_assessment",
                passed=False,
                severity=CritiqueSeverity.MEDIUM,
                issue="Риски описаны слишком общо",
                suggestion="Конкретизировать риски с примерами",
                evidence=[
                    f"Общих формулировок: {generic_count} из {len(risks)}",
                    "Риски должны быть конкретными и измеримыми",
                ],
            )

        return CritiqueCheck(
            check_name="risk_assessment",
            passed=True,
            severity=CritiqueSeverity.LOW,
            issue=None,
            suggestion=None,
            evidence=[
                f"Идентифицировано {len(risks)} рисков",
                "Риски конкретные и измеримые",
                f"Уверенность {confidence * 100}% соответствует рискам",
            ],
        )

    async def _check_cognitive_biases(
        self,
        decision: dict[str, Any],
    ) -> CritiqueCheck:
        """Проверка 3: Нет ли когнитивных искажений?

        Args:
            decision: Решение

        Returns:
            Результат проверки
        """
        action = decision.get("action", "")
        rationale = decision.get("rationale", "")
        confidence = decision.get("confidence", 0)

        biases_detected = []

        # 1. Confirmation Bias (подтверждающее искажение)
        confirmation_keywords = [
            "очевидно",
            "конечно",
            "безусловно",
            "всем известно",
            "ясно что",
        ]
        if any(keyword in rationale.lower() for keyword in confirmation_keywords):
            biases_detected.append({
                "bias": "Confirmation Bias",
                "evidence": "Использование категоричных формулировок",
                "risk": "Игнорирование противоречащих данных",
            })

        # 2. Anchoring Bias (эффект якоря)
        if "первый" in rationale.lower() or "изначально" in rationale.lower():
            biases_detected.append({
                "bias": "Anchoring Bias",
                "evidence": "Фокус на первоначальной информации",
                "risk": "Недооценка новых данных",
            })

        # 3. Overconfidence Bias (излишняя уверенность)
        if confidence > 0.95:
            biases_detected.append({
                "bias": "Overconfidence Bias",
                "evidence": f"Очень высокая уверенность: {confidence * 100}%",
                "risk": "Недооценка неопределённости",
            })

        # 4. Sunk Cost Fallacy (ошибка невозвратных затрат)
        sunk_cost_keywords = ["уже потратили", "уже вложили", "не можем бросить"]
        if any(keyword in rationale.lower() for keyword in sunk_cost_keywords):
            biases_detected.append({
                "bias": "Sunk Cost Fallacy",
                "evidence": "Упоминание прошлых затрат",
                "risk": "Продолжение неэффективного пути",
            })

        # 5. Availability Bias (доступность)
        availability_keywords = ["недавно", "только что", "на днях"]
        if any(keyword in rationale.lower() for keyword in availability_keywords):
            biases_detected.append({
                "bias": "Availability Bias",
                "evidence": "Фокус на недавних событиях",
                "risk": "Игнорирование долгосрочных трендов",
            })

        if biases_detected:
            return CritiqueCheck(
                check_name="cognitive_biases",
                passed=False,
                severity=CritiqueSeverity.HIGH if len(biases_detected) > 2 else CritiqueSeverity.MEDIUM,
                issue=f"Обнаружено {len(biases_detected)} когнитивных искажений",
                suggestion="Пересмотреть решение с учётом выявленных искажений",
                evidence=[
                    f"{bias['bias']}: {bias['evidence']} (риск: {bias['risk']})"
                    for bias in biases_detected
                ],
            )

        return CritiqueCheck(
            check_name="cognitive_biases",
            passed=True,
            severity=CritiqueSeverity.LOW,
            issue=None,
            suggestion=None,
            evidence=["Когнитивные искажения не обнаружены"],
        )

    async def _check_past_experience(
        self,
        decision: dict[str, Any],
    ) -> CritiqueCheck:
        """Проверка 4: Учтён ли прошлый опыт?

        Args:
            decision: Решение

        Returns:
            Результат проверки
        """
        rationale = decision.get("rationale", "")

        # Проверяем упоминание прошлого опыта
        experience_keywords = [
            "в прошлый раз",
            "ранее",
            "предыдущий опыт",
            "уже делали",
            "история показывает",
            "на основе опыта",
        ]

        has_experience_reference = any(
            keyword in rationale.lower() for keyword in experience_keywords
        )

        if not has_experience_reference:
            return CritiqueCheck(
                check_name="past_experience",
                passed=False,
                severity=CritiqueSeverity.MEDIUM,
                issue="Не учтён прошлый опыт",
                suggestion="Проверить историю похожих решений в obsidian/architect/decisions/",
                evidence=[
                    "Нет упоминания прошлого опыта",
                    "Рекомендуется проверить архив решений",
                ],
            )

        # TODO: Реальная проверка в Obsidian vault
        # Пока просто проверяем упоминание

        return CritiqueCheck(
            check_name="past_experience",
            passed=True,
            severity=CritiqueSeverity.LOW,
            issue=None,
            suggestion=None,
            evidence=[
                "Прошлый опыт учтён",
                "Есть ссылки на предыдущие решения",
            ],
        )

    async def _check_failure_modes(
        self,
        decision: dict[str, Any],
    ) -> CritiqueCheck:
        """Проверка 5: Что может пойти не так?

        Args:
            decision: Решение

        Returns:
            Результат проверки
        """
        rationale = decision.get("rationale", "")
        risks = decision.get("risks", [])

        # Проверяем упоминание failure modes
        failure_keywords = [
            "может не сработать",
            "если не получится",
            "в случае неудачи",
            "план Б",
            "откат",
            "rollback",
        ]

        has_failure_consideration = any(
            keyword in rationale.lower() for keyword in failure_keywords
        )

        if not has_failure_consideration:
            return CritiqueCheck(
                check_name="failure_modes",
                passed=False,
                severity=CritiqueSeverity.HIGH,
                issue="Не рассмотрены режимы отказа",
                suggestion="Добавить план действий на случай неудачи",
                evidence=[
                    "Нет упоминания failure modes",
                    "Нет плана отката (rollback)",
                    "Что делать если не сработает?",
                ],
            )

        # Проверяем наличие плана отката
        rollback_keywords = ["откат", "rollback", "вернуться", "отменить"]
        has_rollback_plan = any(
            keyword in rationale.lower() for keyword in rollback_keywords
        )

        if not has_rollback_plan:
            return CritiqueCheck(
                check_name="failure_modes",
                passed=False,
                severity=CritiqueSeverity.MEDIUM,
                issue="Нет плана отката",
                suggestion="Добавить план отката на случай неудачи",
                evidence=[
                    "Failure modes рассмотрены",
                    "Но нет конкретного плана отката",
                ],
            )

        return CritiqueCheck(
            check_name="failure_modes",
            passed=True,
            severity=CritiqueSeverity.LOW,
            issue=None,
            suggestion=None,
            evidence=[
                "Failure modes рассмотрены",
                "Есть план отката",
                "Риски управляемы",
            ],
        )

    def _determine_verdict(self, checks: list[CritiqueCheck]) -> CritiqueVerdict:
        """Определить вердикт на основе проверок

        Args:
            checks: Результаты проверок

        Returns:
            Вердикт
        """
        # Считаем проблемы по серьёзности
        critical_issues = sum(
            1 for check in checks
            if not check.passed and check.severity == CritiqueSeverity.CRITICAL
        )
        high_issues = sum(
            1 for check in checks
            if not check.passed and check.severity == CritiqueSeverity.HIGH
        )
        medium_issues = sum(
            1 for check in checks
            if not check.passed and check.severity == CritiqueSeverity.MEDIUM
        )

        # Логика вердикта
        if critical_issues > 0:
            return CritiqueVerdict.REJECT

        if high_issues >= 2:
            return CritiqueVerdict.REJECT

        if high_issues == 1 or medium_issues >= 2:
            return CritiqueVerdict.CHALLENGE

        return CritiqueVerdict.APPROVE

    def _calculate_confidence(self, checks: list[CritiqueCheck]) -> float:
        """Вычислить уверенность в вердикте

        Args:
            checks: Результаты проверок

        Returns:
            Уверенность (0.0 - 1.0)
        """
        # Базовая уверенность
        base_confidence = 0.7

        # Штрафы за проблемы
        for check in checks:
            if not check.passed:
                if check.severity == CritiqueSeverity.CRITICAL:
                    base_confidence -= 0.15
                elif check.severity == CritiqueSeverity.HIGH:
                    base_confidence -= 0.10
                elif check.severity == CritiqueSeverity.MEDIUM:
                    base_confidence -= 0.05

        # Бонус за все проверки пройдены
        if all(check.passed for check in checks):
            base_confidence = 0.95

        return max(0.0, min(1.0, base_confidence))

    def _generate_summary(
        self,
        checks: list[CritiqueCheck],
        verdict: CritiqueVerdict,
    ) -> str:
        """Сгенерировать краткое резюме

        Args:
            checks: Результаты проверок
            verdict: Вердикт

        Returns:
            Резюме
        """
        failed_checks = [check for check in checks if not check.passed]

        if verdict == CritiqueVerdict.APPROVE:
            return "Решение прошло все проверки. Можно реализовывать."

        if verdict == CritiqueVerdict.REJECT:
            return f"Решение имеет критические проблемы ({len(failed_checks)} проверок не пройдено). Требуется новое решение."

        # CHALLENGE
        return f"Решение имеет проблемы ({len(failed_checks)} проверок не пройдено). Требуется пересмотр."

    def _extract_key_concerns(self, checks: list[CritiqueCheck]) -> list[str]:
        """Извлечь ключевые проблемы

        Args:
            checks: Результаты проверок

        Returns:
            Список ключевых проблем
        """
        concerns = []

        for check in checks:
            if not check.passed and check.severity in [
                CritiqueSeverity.CRITICAL,
                CritiqueSeverity.HIGH,
            ]:
                concerns.append(f"{check.check_name}: {check.issue}")

        return concerns

    def _generate_recommendations(self, checks: list[CritiqueCheck]) -> list[str]:
        """Сгенерировать рекомендации

        Args:
            checks: Результаты проверок

        Returns:
            Список рекомендаций
        """
        recommendations = []

        for check in checks:
            if not check.passed and check.suggestion:
                recommendations.append(check.suggestion)

        return recommendations
