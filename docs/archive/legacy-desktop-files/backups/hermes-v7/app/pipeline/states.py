"""Hermes v7 — State Machine Data Models.

Модели данных без поведения. Используются PipelineEngine и phases.py.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PhaseStatus(Enum):
    """Статус фазы пайплайна."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_DATA = "no_data"              # Легитимный исход: данных нет
    TOOL_FAILED = "tool_failed"      # Инструмент упал, но можно retry
    PERMANENT_FAILURE = "permanent_failure"  # Фаза провалена без восстановления
    SKIPPED = "skipped"              # Пропущена (например, нет URL)
    TIMED_OUT = "timed_out"          # Превышен таймаут


@dataclass
class PhaseContract:
    """Контракт фазы — определяет поведение при ошибках.

    Attributes:
        max_retries: Максимальное количество повторных попыток.
        retry_on_key_exhaustion: Ротировать API-ключи и пробовать снова.
        allow_no_data: NO_DATA = легитимный исход, не ошибка.
        timeout: Таймаут фазы в секундах.
        on_permanent_failure: Что делать при необратимом провале:
            "skip" — пропустить и идти дальше
            "abort" — остановить весь пайплайн
    """
    max_retries: int = 0
    retry_on_key_exhaustion: bool = False
    allow_no_data: bool = False
    timeout: int = 120
    on_permanent_failure: str = "skip"  # "skip" | "abort"


@dataclass
class PhaseResult:
    """Результат выполнения одной фазы.

    Attributes:
        phase_id: Идентификатор фазы (0, 1, 2, ...).
        status: Финальный статус (PhaseStatus).
        data: Данные, собранные фазой (словарь или None).
        error_message: Сообщение об ошибке (если была).
        duration_seconds: Длительность выполнения в секундах.
        tool_calls_made: Список инструментов, которые были вызваны.
        llm_interpretation: LLM-интерпретация данных фазы (текст).
    """
    phase_id: int
    status: PhaseStatus
    data: Optional[dict] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    tool_calls_made: list[str] = field(default_factory=list)
    llm_interpretation: Optional[str] = None


@dataclass
class PipelineState:
    """Полное состояние пайплайна для одной сессии.

    Attributes:
        session_id: ID сессии чата.
        client_url: URL сайта клиента.
        client_name: Название клиники (заполняется из prescan).
        current_phase: Индекс текущей фазы (0-based).
        phases: Словарь {phase_id: PhaseResult} результатов всех фаз.
        retry_counts: Словарь {phase_id: int} счётчиков ретраев.
        accumulated_data: Накопленные данные из всех фаз.
        started_at: Время старта пайплайна (ISO формат).
        mode: Режим работы ("ONBOARDING" / "ADMIN").
    """
    session_id: str
    client_url: str
    client_name: str = ""
    client_city: str = ""  # Определяется из /contacts страницы
    client_specialization: str = ""  # Определяется из главной страницы сайта (до PERPLEXITY)
    client_inn: str = ""  # ИНН клиники (из /contacts или /rekvizity, до FINANCE)
    current_phase: int = 0
    phases: dict[int, PhaseResult] = field(default_factory=dict)
    retry_counts: dict[int, int] = field(default_factory=dict)
    accumulated_data: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    mode: str = "ONBOARDING"
