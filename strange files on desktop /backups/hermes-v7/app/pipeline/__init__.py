"""Hermes v7 — State Machine Pipeline.

Python-стейт-машина для онбординга клиентов.
LLM — интерпретатор данных, НЕ оркестратор.

Exports:
    PipelineEngine — главный движок
    PhaseStatus, PhaseContract, PhaseResult, PipelineState — модели данных
    get_toolsets_for_mode, is_tool_allowed — mode gate
    is_write_allowed, protect_config — file guard
    PHASES — список из 15 фаз
"""

from .engine import PipelineEngine, store_pipeline_state, get_pipeline_state
from .states import PhaseStatus, PhaseContract, PhaseResult, PipelineState
from .mode_gate import get_toolsets_for_mode, is_tool_allowed
from .file_guard import is_write_allowed, protect_config, set_current_mode, set_key_rotator
from .phases import PHASES

__all__ = [
    "PipelineEngine",
    "PhaseStatus",
    "PhaseContract",
    "PhaseResult",
    "PipelineState",
    "get_toolsets_for_mode",
    "is_tool_allowed",
    "is_write_allowed",
    "protect_config",
    "set_current_mode",
    "set_key_rotator",
    "store_pipeline_state",
    "get_pipeline_state",
    "PHASES",
]
