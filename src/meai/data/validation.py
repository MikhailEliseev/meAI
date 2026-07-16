"""
Data Validation Layer

Проверка данных перед использованием и сохранением.
Гарантирует что все данные имеют источники.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from meai.data.provenance import (
    VerifiedData,
    DataSource,
    MissingDataError,
    ProvenanceTracker,
    DataQualityLevel,
    get_tracker
)


class ValidationResult:
    """Результат валидации данных."""

    def __init__(self):
        self.passed: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.missing_fields: List[str] = []
        self.coverage_percent: float = 0.0

    def add_error(self, message: str) -> None:
        """Добавить ошибку."""
        self.errors.append(message)
        self.passed = False

    def add_warning(self, message: str) -> None:
        """Добавить предупреждение."""
        self.warnings.append(message)

    def add_missing_field(self, field_name: str) -> None:
        """Добавить отсутствующее поле."""
        self.missing_fields.append(field_name)

    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь."""
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "missing_fields": self.missing_fields,
            "coverage_percent": self.coverage_percent
        }


class DataValidator:
    """
    Валидатор данных.

    Проверяет что все данные имеют источники и соответствуют требованиям.
    """

    def __init__(
        self,
        strict_mode: bool = True,
        min_coverage: float = 0.8,
        tracker: Optional[ProvenanceTracker] = None
    ):
        """
        Инициализация валидатора.

        Args:
            strict_mode: Строгий режим (ошибки вместо warnings)
            min_coverage: Минимальное покрытие данных (0.0-1.0)
            tracker: Трекер происхождения (по умолчанию глобальный)
        """
        self.strict_mode = strict_mode
        self.min_coverage = min_coverage
        self.tracker = tracker or get_tracker()

    def validate_data(
        self,
        data: Dict[str, Any],
        required_fields: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Валидировать данные.

        Args:
            data: Данные для проверки
            required_fields: Обязательные поля

        Returns:
            ValidationResult
        """
        result = ValidationResult()
        required_fields = required_fields or []

        # Проверка обязательных полей
        for field in required_fields:
            if field not in data:
                result.add_missing_field(field)
                msg = f"Required field '{field}' is missing"
                if self.strict_mode:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

        # Проверка что все значения - VerifiedData
        total_fields = len(data)
        verified_fields = 0

        for key, value in data.items():
            if isinstance(value, VerifiedData):
                verified_fields += 1

                # Проверка качества источника
                if value.source.quality == DataQualityLevel.UNKNOWN:
                    result.add_warning(
                        f"Field '{key}' has unknown quality source"
                    )
            else:
                msg = f"Field '{key}' is not VerifiedData (no source)"
                if self.strict_mode:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

        # Расчёт покрытия
        if total_fields > 0:
            result.coverage_percent = (verified_fields / total_fields) * 100
        else:
            result.coverage_percent = 0.0

        # Проверка минимального покрытия
        if result.coverage_percent < (self.min_coverage * 100):
            msg = (
                f"Data coverage {result.coverage_percent:.1f}% "
                f"is below minimum {self.min_coverage * 100}%"
            )
            if self.strict_mode:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        return result

    def validate_json_file(
        self,
        file_path: str,
        required_fields: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Валидировать JSON файл.

        Args:
            file_path: Путь к файлу
            required_fields: Обязательные поля

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Проверка структуры
            if not isinstance(data, dict):
                result.add_error("JSON file must contain an object")
                return result

            # Валидация данных
            return self.validate_data(data, required_fields)

        except FileNotFoundError:
            result.add_error(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")
        except Exception as e:
            result.add_error(f"Validation error: {e}")

        return result

    def validate_agent_output(
        self,
        agent_id: str,
        output: Dict[str, Any],
        expected_fields: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Валидировать выход агента.

        Args:
            agent_id: ID агента
            output: Выходные данные
            expected_fields: Ожидаемые поля

        Returns:
            ValidationResult
        """
        result = self.validate_data(output, expected_fields)

        # Добавить информацию об агенте
        if not result.passed:
            result.add_error(f"Agent '{agent_id}' produced invalid output")

        return result


class DataQualityScore:
    """
    Оценка качества данных.

    Рассчитывает score на основе источников и покрытия.
    """

    @staticmethod
    def calculate_score(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рассчитать score качества данных.

        Args:
            data: Данные для оценки

        Returns:
            Словарь со score и деталями
        """
        total_fields = len(data)
        if total_fields == 0:
            return {
                "score": 0.0,
                "total_fields": 0,
                "verified_fields": 0,
                "by_quality": {},
                "by_source_type": {}
            }

        verified_fields = 0
        by_quality = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "unknown": 0
        }
        by_source_type = {}

        for value in data.values():
            if isinstance(value, VerifiedData):
                verified_fields += 1

                # По качеству
                quality = value.source.quality.value
                by_quality[quality] = by_quality.get(quality, 0) + 1

                # По типу источника
                source_type = value.source.type.value
                by_source_type[source_type] = by_source_type.get(source_type, 0) + 1

        # Расчёт score (0.0 - 1.0)
        coverage = verified_fields / total_fields

        # Вес по качеству
        quality_weight = (
            by_quality["high"] * 1.0 +
            by_quality["medium"] * 0.7 +
            by_quality["low"] * 0.4 +
            by_quality["unknown"] * 0.2
        ) / verified_fields if verified_fields > 0 else 0

        # Итоговый score
        score = coverage * quality_weight

        return {
            "score": round(score, 2),
            "total_fields": total_fields,
            "verified_fields": verified_fields,
            "coverage_percent": round(coverage * 100, 1),
            "by_quality": by_quality,
            "by_source_type": by_source_type
        }


class ValidationLayer:
    """
    Слой валидации для всей системы.

    Проверяет данные на каждом этапе pipeline.
    """

    def __init__(
        self,
        strict_mode: bool = True,
        min_coverage: float = 0.8,
        output_dir: str = "AIM/data/validation"
    ):
        """
        Инициализация слоя валидации.

        Args:
            strict_mode: Строгий режим
            min_coverage: Минимальное покрытие
            output_dir: Директория для отчётов
        """
        self.validator = DataValidator(strict_mode, min_coverage)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # История валидаций
        self.validation_history: List[Dict[str, Any]] = []

    def validate_phase_output(
        self,
        phase_number: int,
        agent_id: str,
        output: Dict[str, Any],
        required_fields: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Валидировать выход фазы.

        Args:
            phase_number: Номер фазы
            agent_id: ID агента
            output: Выходные данные
            required_fields: Обязательные поля

        Returns:
            ValidationResult
        """
        result = self.validator.validate_agent_output(
            agent_id=agent_id,
            output=output,
            expected_fields=required_fields
        )

        # Сохранить в историю
        self.validation_history.append({
            "phase": phase_number,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "result": result.to_dict()
        })

        # Сохранить отчёт
        self._save_validation_report(phase_number, agent_id, result)

        return result

    def _save_validation_report(
        self,
        phase_number: int,
        agent_id: str,
        result: ValidationResult
    ) -> None:
        """Сохранить отчёт валидации."""
        report_file = (
            self.output_dir /
            f"phase-{phase_number}-{agent_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )

        report = {
            "phase": phase_number,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "validation": result.to_dict()
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def get_pipeline_coverage(self) -> Dict[str, Any]:
        """
        Получить покрытие данных для всего pipeline.

        Returns:
            Статистика покрытия
        """
        if not self.validation_history:
            return {
                "total_phases": 0,
                "avg_coverage": 0.0,
                "phases": []
            }

        phases_coverage = []
        total_coverage = 0.0

        for validation in self.validation_history:
            coverage = validation["result"]["coverage_percent"]
            phases_coverage.append({
                "phase": validation["phase"],
                "agent_id": validation["agent_id"],
                "coverage": coverage
            })
            total_coverage += coverage

        avg_coverage = total_coverage / len(self.validation_history)

        return {
            "total_phases": len(self.validation_history),
            "avg_coverage": round(avg_coverage, 1),
            "phases": phases_coverage
        }

    def generate_missing_data_report(self) -> Dict[str, Any]:
        """
        Сгенерировать отчёт об отсутствующих данных.

        Returns:
            Отчёт с рекомендациями
        """
        tracker = get_tracker()
        missing_data = tracker.get_missing_data_report()

        # Группировка по агентам
        by_agent: Dict[str, List[Dict[str, Any]]] = {}
        for item in missing_data["missing_fields"]:
            agent_id = item.get("agent_id", "unknown")
            if agent_id not in by_agent:
                by_agent[agent_id] = []
            by_agent[agent_id].append(item)

        # Приоритизация
        high_priority = []
        medium_priority = []
        low_priority = []

        for item in missing_data["missing_fields"]:
            if item.get("suggestions"):
                high_priority.append(item)
            elif item.get("agent_id"):
                medium_priority.append(item)
            else:
                low_priority.append(item)

        return {
            "total_missing": missing_data["total_missing"],
            "by_agent": by_agent,
            "prioritized": {
                "high": high_priority,
                "medium": medium_priority,
                "low": low_priority
            },
            "generated_at": missing_data["generated_at"]
        }
