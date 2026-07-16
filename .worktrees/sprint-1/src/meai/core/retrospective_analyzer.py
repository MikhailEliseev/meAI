"""Retrospective Analyzer - анализ прошлых решений

Сравнивает predicted vs actual outcomes.
Извлекает уроки из успехов и ошибок.
Улучшает процесс принятия решений.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import text

from meai.storage.database import Database


class OutcomeType(str, Enum):
    """Тип результата"""

    SUCCESS = "success"  # Всё прошло как планировалось
    PARTIAL = "partial"  # Частичный успех
    FAILURE = "failure"  # Провал


class LessonType(str, Enum):
    """Тип урока"""

    WHAT_WORKED = "what_worked"  # Что сработало
    WHAT_FAILED = "what_failed"  # Что не сработало
    MISSED_SIGNAL = "missed_signal"  # Пропущенный сигнал
    WRONG_ASSUMPTION = "wrong_assumption"  # Неверное предположение
    UNEXPECTED_BENEFIT = "unexpected_benefit"  # Неожиданная польза
    UNEXPECTED_COST = "unexpected_cost"  # Неожиданная цена


class Lesson(BaseModel):
    """Урок из прошлого опыта"""

    lesson_type: LessonType
    description: str
    evidence: list[str] = Field(default_factory=list)
    impact: str  # Какое влияние это оказало
    recommendation: str  # Что делать в следующий раз


class RetrospectiveReport(BaseModel):
    """Ретроспективный отчёт"""

    report_id: str
    decision_id: str
    outcome_type: OutcomeType
    predicted_outcome: dict[str, Any]
    actual_outcome: dict[str, Any]
    delta_analysis: dict[str, Any]  # Что отличается
    lessons_learned: list[Lesson]
    recommendations: list[str]
    confidence_calibration: dict[str, Any]  # Насколько точна была уверенность
    created_at: datetime


class RetrospectiveAnalyzer:
    """Анализирует прошлые решения и извлекает уроки

    Workflow:
    1. Получить решение и его фактический результат
    2. Сравнить predicted vs actual
    3. Выявить расхождения
    4. Извлечь уроки
    5. Сгенерировать рекомендации
    6. Обновить Decision Maker
    """

    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/meai.db"):
        """Initialize Retrospective Analyzer

        Args:
            database_url: Database URL
        """
        self.db = Database(database_url)

    async def initialize(self) -> None:
        """Initialize analyzer"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown analyzer"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create retrospective tables"""
        async with self.db.session() as session:
            # Retrospective reports
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS retrospective_reports (
                    id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    outcome_type TEXT NOT NULL,
                    predicted_outcome TEXT NOT NULL,
                    actual_outcome TEXT NOT NULL,
                    delta_analysis TEXT NOT NULL,
                    lessons_learned TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    confidence_calibration TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
                """)
            )

            # Lessons learned (denormalized for quick access)
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS lessons_learned (
                    id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    decision_id TEXT NOT NULL,
                    lesson_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
                """)
            )

            await session.commit()

    async def analyze_decision_outcome(
        self,
        decision_id: str,
        decision: dict[str, Any],
        actual_outcome: dict[str, Any],
    ) -> RetrospectiveReport:
        """Анализирует результат решения

        Args:
            decision_id: ID решения
            decision: Оригинальное решение
            actual_outcome: Фактический результат

        Returns:
            Ретроспективный отчёт
        """
        report_id = f"retro-{uuid4().hex[:8]}"

        # Определяем тип результата
        outcome_type = self._determine_outcome_type(decision, actual_outcome)

        # Извлекаем predicted outcome
        predicted_outcome = self._extract_predicted_outcome(decision)

        # Анализируем расхождения
        delta_analysis = self._analyze_delta(predicted_outcome, actual_outcome)

        # Извлекаем уроки
        lessons_learned = self._extract_lessons(
            decision,
            predicted_outcome,
            actual_outcome,
            delta_analysis,
            outcome_type,
        )

        # Генерируем рекомендации
        recommendations = self._generate_recommendations(lessons_learned)

        # Анализируем калибровку уверенности
        confidence_calibration = self._analyze_confidence_calibration(
            decision,
            outcome_type,
        )

        report = RetrospectiveReport(
            report_id=report_id,
            decision_id=decision_id,
            outcome_type=outcome_type,
            predicted_outcome=predicted_outcome,
            actual_outcome=actual_outcome,
            delta_analysis=delta_analysis,
            lessons_learned=lessons_learned,
            recommendations=recommendations,
            confidence_calibration=confidence_calibration,
            created_at=datetime.now(timezone.utc),
        )

        # Сохраняем в базу
        await self._save_report(report)

        return report

    def _determine_outcome_type(
        self,
        decision: dict[str, Any],
        actual_outcome: dict[str, Any],
    ) -> OutcomeType:
        """Определить тип результата

        Args:
            decision: Решение
            actual_outcome: Фактический результат

        Returns:
            Тип результата
        """
        # Проверяем явное указание
        if "outcome_type" in actual_outcome:
            return OutcomeType(actual_outcome["outcome_type"])

        # Проверяем success flag
        if "success" in actual_outcome:
            if actual_outcome["success"] is True:
                return OutcomeType.SUCCESS
            elif actual_outcome["success"] is False:
                return OutcomeType.FAILURE

        # Проверяем score
        if "score" in actual_outcome:
            score = actual_outcome["score"]
            if score >= 0.8:
                return OutcomeType.SUCCESS
            elif score >= 0.5:
                return OutcomeType.PARTIAL
            else:
                return OutcomeType.FAILURE

        # По умолчанию - partial
        return OutcomeType.PARTIAL

    def _extract_predicted_outcome(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Извлечь предсказанный результат

        Args:
            decision: Решение

        Returns:
            Предсказанный результат
        """
        predicted = {}

        # Извлекаем из rationale
        if "rationale" in decision:
            predicted["rationale"] = decision["rationale"]

        # Извлекаем ожидаемые результаты
        if "expected_results" in decision:
            predicted["expected_results"] = decision["expected_results"]

        # Извлекаем confidence
        if "confidence" in decision:
            predicted["confidence"] = decision["confidence"]

        # Извлекаем risks
        if "risks" in decision:
            predicted["risks"] = decision["risks"]

        return predicted

    def _analyze_delta(
        self,
        predicted: dict[str, Any],
        actual: dict[str, Any],
    ) -> dict[str, Any]:
        """Анализировать расхождения

        Args:
            predicted: Предсказанный результат
            actual: Фактический результат

        Returns:
            Анализ расхождений
        """
        delta = {
            "differences": [],
            "surprises": [],
            "confirmations": [],
        }

        # Сравниваем ключи
        predicted_keys = set(predicted.keys())
        actual_keys = set(actual.keys())

        # Неожиданные ключи
        unexpected_keys = actual_keys - predicted_keys
        if unexpected_keys:
            delta["surprises"].append({
                "type": "unexpected_keys",
                "keys": list(unexpected_keys),
                "description": "Появились неожиданные аспекты результата",
            })

        # Отсутствующие ключи
        missing_keys = predicted_keys - actual_keys
        if missing_keys:
            delta["differences"].append({
                "type": "missing_keys",
                "keys": list(missing_keys),
                "description": "Некоторые ожидаемые аспекты не реализовались",
            })

        # Сравниваем значения
        for key in predicted_keys & actual_keys:
            pred_val = predicted[key]
            actual_val = actual[key]

            if pred_val != actual_val:
                delta["differences"].append({
                    "key": key,
                    "predicted": pred_val,
                    "actual": actual_val,
                    "description": f"{key}: ожидали {pred_val}, получили {actual_val}",
                })
            else:
                delta["confirmations"].append({
                    "key": key,
                    "value": pred_val,
                    "description": f"{key}: совпало с ожиданиями",
                })

        return delta

    def _extract_lessons(
        self,
        decision: dict[str, Any],
        predicted: dict[str, Any],
        actual: dict[str, Any],
        delta: dict[str, Any],
        outcome_type: OutcomeType,
    ) -> list[Lesson]:
        """Извлечь уроки

        Args:
            decision: Решение
            predicted: Предсказанный результат
            actual: Фактический результат
            delta: Анализ расхождений
            outcome_type: Тип результата

        Returns:
            Список уроков
        """
        lessons = []

        # Урок 1: Что сработало (если успех)
        if outcome_type == OutcomeType.SUCCESS:
            lessons.append(Lesson(
                lesson_type=LessonType.WHAT_WORKED,
                description=f"Решение '{decision.get('action', 'N/A')}' сработало как ожидалось",
                evidence=[
                    f"Outcome type: {outcome_type.value}",
                    f"Confirmations: {len(delta['confirmations'])}",
                ],
                impact="Положительный - цель достигнута",
                recommendation="Использовать этот подход в похожих ситуациях",
            ))

        # Урок 2: Что не сработало (если провал)
        if outcome_type == OutcomeType.FAILURE:
            lessons.append(Lesson(
                lesson_type=LessonType.WHAT_FAILED,
                description=f"Решение '{decision.get('action', 'N/A')}' не сработало",
                evidence=[
                    f"Outcome type: {outcome_type.value}",
                    f"Differences: {len(delta['differences'])}",
                ],
                impact="Негативный - цель не достигнута",
                recommendation="Избегать этого подхода в будущем",
            ))

        # Урок 3: Пропущенные сигналы
        if delta["surprises"]:
            for surprise in delta["surprises"]:
                lessons.append(Lesson(
                    lesson_type=LessonType.MISSED_SIGNAL,
                    description=f"Не предвидели: {surprise['description']}",
                    evidence=[str(surprise)],
                    impact="Неожиданный результат",
                    recommendation="Учитывать этот аспект в будущих решениях",
                ))

        # Урок 4: Неверные предположения
        for diff in delta["differences"]:
            if "predicted" in diff and "actual" in diff:
                lessons.append(Lesson(
                    lesson_type=LessonType.WRONG_ASSUMPTION,
                    description=f"Неверное предположение о {diff['key']}",
                    evidence=[
                        f"Ожидали: {diff['predicted']}",
                        f"Получили: {diff['actual']}",
                    ],
                    impact="Расхождение с ожиданиями",
                    recommendation=f"Пересмотреть предположения о {diff['key']}",
                ))

        # Урок 5: Калибровка уверенности
        confidence = decision.get("confidence", 0)
        if outcome_type == OutcomeType.SUCCESS and confidence < 0.7:
            lessons.append(Lesson(
                lesson_type=LessonType.UNEXPECTED_BENEFIT,
                description="Успех при низкой уверенности",
                evidence=[
                    f"Confidence: {confidence * 100}%",
                    f"Outcome: {outcome_type.value}",
                ],
                impact="Недооценили вероятность успеха",
                recommendation="Повысить уверенность в похожих ситуациях",
            ))

        if outcome_type == OutcomeType.FAILURE and confidence > 0.8:
            lessons.append(Lesson(
                lesson_type=LessonType.UNEXPECTED_COST,
                description="Провал при высокой уверенности",
                evidence=[
                    f"Confidence: {confidence * 100}%",
                    f"Outcome: {outcome_type.value}",
                ],
                impact="Переоценили вероятность успеха",
                recommendation="Быть более осторожным в оценке уверенности",
            ))

        return lessons

    def _generate_recommendations(self, lessons: list[Lesson]) -> list[str]:
        """Сгенерировать рекомендации

        Args:
            lessons: Уроки

        Returns:
            Список рекомендаций
        """
        recommendations = []

        # Группируем уроки по типам
        lessons_by_type: dict[LessonType, list[Lesson]] = {}
        for lesson in lessons:
            if lesson.lesson_type not in lessons_by_type:
                lessons_by_type[lesson.lesson_type] = []
            lessons_by_type[lesson.lesson_type].append(lesson)

        # Генерируем рекомендации по типам
        if LessonType.WHAT_WORKED in lessons_by_type:
            recommendations.append(
                "Повторить успешный подход в похожих ситуациях"
            )

        if LessonType.WHAT_FAILED in lessons_by_type:
            recommendations.append(
                "Избегать неудачного подхода в будущем"
            )

        if LessonType.MISSED_SIGNAL in lessons_by_type:
            recommendations.append(
                f"Учитывать {len(lessons_by_type[LessonType.MISSED_SIGNAL])} пропущенных сигналов"
            )

        if LessonType.WRONG_ASSUMPTION in lessons_by_type:
            recommendations.append(
                f"Пересмотреть {len(lessons_by_type[LessonType.WRONG_ASSUMPTION])} неверных предположений"
            )

        if LessonType.UNEXPECTED_BENEFIT in lessons_by_type:
            recommendations.append(
                "Повысить уверенность в похожих ситуациях"
            )

        if LessonType.UNEXPECTED_COST in lessons_by_type:
            recommendations.append(
                "Быть более осторожным в оценке рисков"
            )

        return recommendations

    def _analyze_confidence_calibration(
        self,
        decision: dict[str, Any],
        outcome_type: OutcomeType,
    ) -> dict[str, Any]:
        """Анализировать калибровку уверенности

        Args:
            decision: Решение
            outcome_type: Тип результата

        Returns:
            Анализ калибровки
        """
        confidence = decision.get("confidence", 0)

        # Определяем правильность калибровки
        if outcome_type == OutcomeType.SUCCESS:
            expected_confidence = 0.8  # Успех → высокая уверенность
        elif outcome_type == OutcomeType.PARTIAL:
            expected_confidence = 0.6  # Частичный → средняя уверенность
        else:
            expected_confidence = 0.4  # Провал → низкая уверенность

        delta = confidence - expected_confidence
        calibration_error = abs(delta)

        if calibration_error < 0.1:
            calibration_quality = "excellent"
        elif calibration_error < 0.2:
            calibration_quality = "good"
        elif calibration_error < 0.3:
            calibration_quality = "fair"
        else:
            calibration_quality = "poor"

        return {
            "predicted_confidence": confidence,
            "expected_confidence": expected_confidence,
            "delta": delta,
            "calibration_error": calibration_error,
            "calibration_quality": calibration_quality,
            "interpretation": self._interpret_calibration(delta, outcome_type),
        }

    def _interpret_calibration(
        self,
        delta: float,
        outcome_type: OutcomeType,
    ) -> str:
        """Интерпретировать калибровку

        Args:
            delta: Разница между predicted и expected confidence
            outcome_type: Тип результата

        Returns:
            Интерпретация
        """
        if abs(delta) < 0.1:
            return "Уверенность хорошо откалибрована"

        if delta > 0:
            # Overconfident
            if outcome_type == OutcomeType.FAILURE:
                return "Излишняя уверенность привела к провалу"
            else:
                return "Уверенность была выше необходимой"
        else:
            # Underconfident
            if outcome_type == OutcomeType.SUCCESS:
                return "Недооценили вероятность успеха"
            else:
                return "Уверенность была ниже необходимой"

    async def _save_report(self, report: RetrospectiveReport) -> None:
        """Сохранить отчёт в базу

        Args:
            report: Отчёт
        """
        import json

        async with self.db.session() as session:
            # Сохраняем отчёт
            await session.execute(
                text("""
                INSERT INTO retrospective_reports
                (id, decision_id, outcome_type, predicted_outcome, actual_outcome,
                 delta_analysis, lessons_learned, recommendations,
                 confidence_calibration, created_at)
                VALUES (:id, :decision_id, :outcome_type, :predicted_outcome,
                        :actual_outcome, :delta_analysis, :lessons_learned,
                        :recommendations, :confidence_calibration, :created_at)
                """),
                {
                    "id": report.report_id,
                    "decision_id": report.decision_id,
                    "outcome_type": report.outcome_type.value,
                    "predicted_outcome": json.dumps(report.predicted_outcome),
                    "actual_outcome": json.dumps(report.actual_outcome),
                    "delta_analysis": json.dumps(report.delta_analysis),
                    "lessons_learned": json.dumps([
                        lesson.model_dump() for lesson in report.lessons_learned
                    ]),
                    "recommendations": json.dumps(report.recommendations),
                    "confidence_calibration": json.dumps(report.confidence_calibration),
                    "created_at": report.created_at,
                },
            )

            # Сохраняем уроки (denormalized)
            for lesson in report.lessons_learned:
                lesson_id = f"lesson-{uuid4().hex[:8]}"
                await session.execute(
                    text("""
                    INSERT INTO lessons_learned
                    (id, report_id, decision_id, lesson_type, description,
                     evidence, impact, recommendation, created_at)
                    VALUES (:id, :report_id, :decision_id, :lesson_type,
                            :description, :evidence, :impact, :recommendation,
                            :created_at)
                    """),
                    {
                        "id": lesson_id,
                        "report_id": report.report_id,
                        "decision_id": report.decision_id,
                        "lesson_type": lesson.lesson_type.value,
                        "description": lesson.description,
                        "evidence": json.dumps(lesson.evidence),
                        "impact": lesson.impact,
                        "recommendation": lesson.recommendation,
                        "created_at": report.created_at,
                    },
                )

            await session.commit()

    async def get_lessons_for_similar_decisions(
        self,
        decision: dict[str, Any],
        limit: int = 10,
    ) -> list[Lesson]:
        """Получить уроки из похожих решений

        Args:
            decision: Текущее решение
            limit: Максимум уроков

        Returns:
            Список уроков
        """
        import json

        # TODO: Реализовать similarity search
        # Пока просто возвращаем последние уроки

        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT id, report_id, decision_id, lesson_type, description,
                       evidence, impact, recommendation, created_at
                FROM lessons_learned
                ORDER BY created_at DESC
                LIMIT :limit
                """),
                {"limit": limit},
            )
            rows = result.fetchall()

        lessons = []
        for row in rows:
            lessons.append(Lesson(
                lesson_type=LessonType(row[3]),
                description=row[4],
                evidence=json.loads(row[5]),
                impact=row[6],
                recommendation=row[7],
            ))

        return lessons

    async def get_calibration_stats(self) -> dict[str, Any]:
        """Получить статистику калибровки

        Returns:
            Статистика калибровки
        """
        import json

        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT confidence_calibration
                FROM retrospective_reports
                ORDER BY created_at DESC
                """)
            )
            rows = result.fetchall()

        if not rows:
            return {
                "total_reports": 0,
                "average_calibration_error": 0.0,
                "calibration_quality_distribution": {},
            }

        calibrations = [json.loads(row[0]) for row in rows]

        total_error = sum(cal["calibration_error"] for cal in calibrations)
        avg_error = total_error / len(calibrations)

        quality_dist = {}
        for cal in calibrations:
            quality = cal["calibration_quality"]
            quality_dist[quality] = quality_dist.get(quality, 0) + 1

        return {
            "total_reports": len(calibrations),
            "average_calibration_error": avg_error,
            "calibration_quality_distribution": quality_dist,
        }
