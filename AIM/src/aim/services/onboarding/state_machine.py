"""Onboarding State Machine

Manages onboarding workflow state transitions and validation.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class OnboardingState(str, Enum):
    """Onboarding workflow states."""

    LEAD_CREATED = "LEAD_CREATED"
    DOCUMENTS_PENDING = "DOCUMENTS_PENDING"
    DOCUMENTS_UPLOADED = "DOCUMENTS_UPLOADED"
    DOCUMENTS_VALIDATED = "DOCUMENTS_VALIDATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    ONBOARDING_COMPLETE = "ONBOARDING_COMPLETE"
    ONBOARDING_FAILED = "ONBOARDING_FAILED"


class OnboardingEvent(str, Enum):
    """Onboarding workflow events."""

    START = "START"
    UPLOAD_DOCUMENT = "UPLOAD_DOCUMENT"
    VALIDATE_DOCUMENTS = "VALIDATE_DOCUMENTS"
    REQUEST_PAYMENT = "REQUEST_PAYMENT"
    PROCESS_PAYMENT = "PROCESS_PAYMENT"
    COMPLETE_PAYMENT = "COMPLETE_PAYMENT"
    COMPLETE_ONBOARDING = "COMPLETE_ONBOARDING"
    FAIL = "FAIL"
    RETRY = "RETRY"


class OnboardingStateMachine:
    """State machine for onboarding workflow.

    Manages state transitions and validates workflow logic.
    """

    # Valid state transitions
    TRANSITIONS = {
        OnboardingState.LEAD_CREATED: {
            OnboardingEvent.START: OnboardingState.DOCUMENTS_PENDING,
        },
        OnboardingState.DOCUMENTS_PENDING: {
            OnboardingEvent.UPLOAD_DOCUMENT: OnboardingState.DOCUMENTS_PENDING,
            OnboardingEvent.VALIDATE_DOCUMENTS: OnboardingState.DOCUMENTS_UPLOADED,
            OnboardingEvent.FAIL: OnboardingState.ONBOARDING_FAILED,
        },
        OnboardingState.DOCUMENTS_UPLOADED: {
            OnboardingEvent.VALIDATE_DOCUMENTS: OnboardingState.DOCUMENTS_VALIDATED,
            OnboardingEvent.FAIL: OnboardingState.ONBOARDING_FAILED,
        },
        OnboardingState.DOCUMENTS_VALIDATED: {
            OnboardingEvent.REQUEST_PAYMENT: OnboardingState.PAYMENT_PENDING,
            OnboardingEvent.FAIL: OnboardingState.ONBOARDING_FAILED,
        },
        OnboardingState.PAYMENT_PENDING: {
            OnboardingEvent.PROCESS_PAYMENT: OnboardingState.PAYMENT_PROCESSING,
            OnboardingEvent.FAIL: OnboardingState.ONBOARDING_FAILED,
        },
        OnboardingState.PAYMENT_PROCESSING: {
            OnboardingEvent.COMPLETE_PAYMENT: OnboardingState.PAYMENT_COMPLETED,
            OnboardingEvent.FAIL: OnboardingState.ONBOARDING_FAILED,
        },
        OnboardingState.PAYMENT_COMPLETED: {
            OnboardingEvent.COMPLETE_ONBOARDING: OnboardingState.ONBOARDING_COMPLETE,
            OnboardingEvent.FAIL: OnboardingState.ONBOARDING_FAILED,
        },
        OnboardingState.ONBOARDING_FAILED: {
            OnboardingEvent.RETRY: OnboardingState.DOCUMENTS_PENDING,
        },
    }

    def __init__(self, current_state: str):
        """Initialize state machine.

        Args:
            current_state: Current state string
        """
        self.current_state = OnboardingState(current_state)

    def can_transition(self, event: OnboardingEvent) -> bool:
        """Check if transition is allowed.

        Args:
            event: Event to trigger

        Returns:
            True if transition allowed
        """
        allowed_events = self.TRANSITIONS.get(self.current_state, {})
        return event in allowed_events

    def transition(self, event: OnboardingEvent) -> OnboardingState:
        """Execute state transition.

        Args:
            event: Event to trigger

        Returns:
            New state

        Raises:
            ValueError: If transition not allowed
        """
        if not self.can_transition(event):
            raise ValueError(
                f"Transition not allowed: {self.current_state} -> {event}"
            )

        new_state = self.TRANSITIONS[self.current_state][event]
        logger.info(
            f"State transition: {self.current_state} -> {new_state} (event: {event})"
        )

        self.current_state = new_state
        return new_state

    def get_next_steps(self) -> list[dict]:
        """Get required next steps for current state.

        Returns:
            List of next step descriptions
        """
        steps_map = {
            OnboardingState.LEAD_CREATED: [
                {
                    "step": "start_onboarding",
                    "description": "Начать процесс онбординга",
                    "required": True,
                }
            ],
            OnboardingState.DOCUMENTS_PENDING: [
                {
                    "step": "upload_license",
                    "description": "Загрузить медицинскую лицензию",
                    "required": True,
                },
                {
                    "step": "upload_inn",
                    "description": "Загрузить свидетельство ИНН",
                    "required": True,
                },
                {
                    "step": "upload_ogrn",
                    "description": "Загрузить свидетельство ОГРН",
                    "required": True,
                },
                {
                    "step": "upload_contract",
                    "description": "Загрузить договор",
                    "required": True,
                },
            ],
            OnboardingState.DOCUMENTS_UPLOADED: [
                {
                    "step": "validate_documents",
                    "description": "Дождаться валидации документов",
                    "required": True,
                }
            ],
            OnboardingState.DOCUMENTS_VALIDATED: [
                {
                    "step": "process_payment",
                    "description": "Оплатить онбординг (50,000 ₽)",
                    "required": True,
                }
            ],
            OnboardingState.PAYMENT_PENDING: [
                {
                    "step": "complete_payment",
                    "description": "Завершить оплату",
                    "required": True,
                }
            ],
            OnboardingState.PAYMENT_PROCESSING: [
                {
                    "step": "wait_payment",
                    "description": "Дождаться обработки платежа",
                    "required": True,
                }
            ],
            OnboardingState.PAYMENT_COMPLETED: [
                {
                    "step": "complete_onboarding",
                    "description": "Завершить онбординг",
                    "required": True,
                }
            ],
            OnboardingState.ONBOARDING_COMPLETE: [
                {
                    "step": "none",
                    "description": "Онбординг завершён",
                    "required": False,
                }
            ],
            OnboardingState.ONBOARDING_FAILED: [
                {
                    "step": "retry",
                    "description": "Повторить неудавшийся шаг",
                    "required": True,
                }
            ],
        }

        return steps_map.get(self.current_state, [])

    def get_progress_percentage(self) -> int:
        """Get progress percentage for current state.

        Returns:
            Progress percentage (0-100)
        """
        progress_map = {
            OnboardingState.LEAD_CREATED: 10,
            OnboardingState.DOCUMENTS_PENDING: 20,
            OnboardingState.DOCUMENTS_UPLOADED: 40,
            OnboardingState.DOCUMENTS_VALIDATED: 60,
            OnboardingState.PAYMENT_PENDING: 70,
            OnboardingState.PAYMENT_PROCESSING: 80,
            OnboardingState.PAYMENT_COMPLETED: 90,
            OnboardingState.ONBOARDING_COMPLETE: 100,
            OnboardingState.ONBOARDING_FAILED: 0,
        }

        return progress_map.get(self.current_state, 0)

    def is_terminal_state(self) -> bool:
        """Check if current state is terminal.

        Returns:
            True if terminal state
        """
        return self.current_state in (
            OnboardingState.ONBOARDING_COMPLETE,
            OnboardingState.ONBOARDING_FAILED,
        )

    def get_allowed_events(self) -> list[OnboardingEvent]:
        """Get list of allowed events for current state.

        Returns:
            List of allowed events
        """
        return list(self.TRANSITIONS.get(self.current_state, {}).keys())
