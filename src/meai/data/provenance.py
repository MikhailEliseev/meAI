"""
Data Provenance Framework

Система отслеживания происхождения данных для гарантии zero hallucinations.
Каждый факт должен иметь проверяемый источник.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """Типы источников данных."""

    API = "api"  # Данные из API (HH, 2GIS, Yandex, etc)
    SCRAPING = "scraping"  # Web scraping
    MANUAL = "manual"  # Ручной ввод пользователя
    DATABASE = "database"  # Из базы данных
    FILE = "file"  # Из файла (CSV, JSON, etc)
    COMPUTED = "computed"  # Вычислено из других verified данных


class DataQualityLevel(str, Enum):
    """Уровни качества данных."""

    HIGH = "high"  # API, официальные источники
    MEDIUM = "medium"  # Scraping, проверенные сайты
    LOW = "low"  # Ручной ввод, непроверенные источники
    UNKNOWN = "unknown"  # Качество неизвестно


class DataSource(BaseModel):
    """
    Источник данных.

    Каждый факт должен иметь источник для прослеживаемости.
    """

    type: DataSourceType
    name: str  # Название источника (e.g., "hh_api", "2gis_api", "manual_input")
    url: Optional[str] = None  # URL источника (если применимо)
    timestamp: datetime = Field(default_factory=datetime.now)
    quality: DataQualityLevel = DataQualityLevel.UNKNOWN
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        """Человекочитаемое представление источника."""
        parts = [f"{self.type.value}:{self.name}"]
        if self.url:
            parts.append(f"({self.url})")
        return " ".join(parts)


class VerifiedData(BaseModel):
    """
    Данные с проверенным источником.

    Все данные в системе должны быть обёрнуты в VerifiedData.
    """

    value: Any  # Само значение
    source: DataSource  # Источник данных
    verified_at: datetime = Field(default_factory=datetime.now)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)  # Уверенность в данных
    notes: Optional[str] = None  # Дополнительные заметки

    def __str__(self) -> str:
        """Человекочитаемое представление."""
        return f"{self.value} [source: {self.source}]"

    @property
    def is_high_quality(self) -> bool:
        """Проверка высокого качества данных."""
        return self.source.quality == DataQualityLevel.HIGH

    @property
    def is_api_sourced(self) -> bool:
        """Проверка что данные из API."""
        return self.source.type == DataSourceType.API


class ProvenanceChain(BaseModel):
    """
    Цепочка происхождения данных.

    Отслеживает как данные трансформировались от источника до финального значения.
    """

    original_source: DataSource
    transformations: List[Dict[str, Any]] = Field(default_factory=list)
    final_value: Any
    created_at: datetime = Field(default_factory=datetime.now)

    def add_transformation(
        self,
        operation: str,
        input_data: Any,
        output_data: Any,
        agent_id: str
    ) -> None:
        """Добавить трансформацию в цепочку."""
        self.transformations.append({
            "operation": operation,
            "input": input_data,
            "output": output_data,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        })

    def get_full_chain(self) -> List[str]:
        """Получить полную цепочку как список строк."""
        chain = [f"Source: {self.original_source}"]
        for i, t in enumerate(self.transformations, 1):
            chain.append(
                f"Step {i}: {t['operation']} by {t['agent_id']} at {t['timestamp']}"
            )
        return chain


class MissingDataError(Exception):
    """
    Ошибка отсутствия данных.

    Выбрасывается когда данные недоступны из источников.
    НЕ ВЫДУМЫВАТЬ ДАННЫЕ - явно сообщить об отсутствии!
    """

    def __init__(
        self,
        field_name: str,
        reason: str,
        suggestions: Optional[List[str]] = None
    ):
        self.field_name = field_name
        self.reason = reason
        self.suggestions = suggestions or []

        message = f"Missing data for '{field_name}': {reason}"
        if self.suggestions:
            message += f"\n\nSuggestions:\n" + "\n".join(
                f"  - {s}" for s in self.suggestions
            )

        super().__init__(message)


class ProvenanceTracker:
    """
    Трекер происхождения данных.

    Отслеживает все источники данных в системе.
    """

    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.chains: Dict[str, ProvenanceChain] = {}
        self.missing_data: List[Dict[str, Any]] = []

    def register_source(self, source_id: str, source: DataSource) -> None:
        """Зарегистрировать источник данных."""
        self.sources[source_id] = source

    def create_verified_data(
        self,
        value: Any,
        source_id: str,
        confidence: float = 1.0,
        notes: Optional[str] = None
    ) -> VerifiedData:
        """
        Создать проверенные данные.

        Args:
            value: Значение
            source_id: ID зарегистрированного источника
            confidence: Уверенность в данных
            notes: Дополнительные заметки

        Returns:
            VerifiedData с источником

        Raises:
            ValueError: Если источник не зарегистрирован
        """
        if source_id not in self.sources:
            raise ValueError(f"Source '{source_id}' not registered")

        return VerifiedData(
            value=value,
            source=self.sources[source_id],
            confidence=confidence,
            notes=notes
        )

    def start_chain(
        self,
        source_id: str,
        initial_value: Any
    ) -> ProvenanceChain:
        """Начать цепочку происхождения."""
        if source_id not in self.sources:
            raise ValueError(f"Source '{source_id}' not registered")

        return ProvenanceChain(
            original_source=self.sources[source_id],
            final_value=initial_value
        )

    def report_missing_data(
        self,
        field_name: str,
        reason: str,
        suggestions: Optional[List[str]] = None,
        agent_id: Optional[str] = None
    ) -> None:
        """
        Зарегистрировать отсутствующие данные.

        Args:
            field_name: Название поля
            reason: Причина отсутствия
            suggestions: Предложения как получить данные
            agent_id: ID агента, который обнаружил отсутствие
        """
        self.missing_data.append({
            "field_name": field_name,
            "reason": reason,
            "suggestions": suggestions or [],
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        })

    def get_missing_data_report(self) -> Dict[str, Any]:
        """Получить отчёт об отсутствующих данных."""
        return {
            "total_missing": len(self.missing_data),
            "missing_fields": self.missing_data,
            "generated_at": datetime.now().isoformat()
        }

    def get_data_coverage(self) -> Dict[str, Any]:
        """
        Получить статистику покрытия данных.

        Returns:
            Статистика по источникам и качеству
        """
        total_sources = len(self.sources)

        by_type = {}
        by_quality = {}

        for source in self.sources.values():
            # По типу
            type_name = source.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            # По качеству
            quality_name = source.quality.value
            by_quality[quality_name] = by_quality.get(quality_name, 0) + 1

        return {
            "total_sources": total_sources,
            "by_type": by_type,
            "by_quality": by_quality,
            "missing_data_count": len(self.missing_data),
            "high_quality_percent": (
                by_quality.get("high", 0) / total_sources * 100
                if total_sources > 0 else 0
            )
        }


# Глобальный трекер для всей системы
_global_tracker = ProvenanceTracker()


def get_tracker() -> ProvenanceTracker:
    """Получить глобальный трекер."""
    return _global_tracker


def register_api_source(
    source_id: str,
    api_name: str,
    base_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> DataSource:
    """
    Зарегистрировать API источник.

    Args:
        source_id: Уникальный ID источника
        api_name: Название API
        base_url: Базовый URL API
        metadata: Дополнительные метаданные

    Returns:
        DataSource объект
    """
    source = DataSource(
        type=DataSourceType.API,
        name=api_name,
        url=base_url,
        quality=DataQualityLevel.HIGH,
        metadata=metadata or {}
    )

    _global_tracker.register_source(source_id, source)
    return source


def register_manual_source(
    source_id: str,
    author: str,
    reason: str,
    metadata: Optional[Dict[str, Any]] = None
) -> DataSource:
    """
    Зарегистрировать ручной ввод.

    Args:
        source_id: Уникальный ID источника
        author: Кто ввёл данные
        reason: Причина ручного ввода
        metadata: Дополнительные метаданные

    Returns:
        DataSource объект
    """
    meta = metadata or {}
    meta["author"] = author
    meta["reason"] = reason

    source = DataSource(
        type=DataSourceType.MANUAL,
        name=f"manual_input_by_{author}",
        quality=DataQualityLevel.LOW,
        metadata=meta
    )

    _global_tracker.register_source(source_id, source)
    return source


def verify(
    value: Any,
    source_id: str,
    confidence: float = 1.0,
    notes: Optional[str] = None
) -> VerifiedData:
    """
    Быстрый способ создать проверенные данные.

    Args:
        value: Значение
        source_id: ID зарегистрированного источника
        confidence: Уверенность
        notes: Заметки

    Returns:
        VerifiedData
    """
    return _global_tracker.create_verified_data(
        value=value,
        source_id=source_id,
        confidence=confidence,
        notes=notes
    )


def report_missing(
    field_name: str,
    reason: str,
    suggestions: Optional[List[str]] = None,
    agent_id: Optional[str] = None
) -> None:
    """
    Быстрый способ зарегистрировать отсутствующие данные.

    Args:
        field_name: Название поля
        reason: Причина отсутствия
        suggestions: Как получить данные
        agent_id: ID агента
    """
    _global_tracker.report_missing_data(
        field_name=field_name,
        reason=reason,
        suggestions=suggestions,
        agent_id=agent_id
    )
