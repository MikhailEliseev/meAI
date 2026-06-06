"""Email Services

Email automation components for AIM agency.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from src.aim.services.email.email_sender import EmailSender
from src.aim.services.email.scheduler import (
    EmailScheduler,
    get_scheduler,
    init_scheduler,
    start_scheduler,
    stop_scheduler,
)
from src.aim.services.email.template_renderer import TemplateRenderer
from src.aim.services.email.webhook_handler import WebhookHandler
from src.aim.services.email.workflow_engine import WorkflowEngine
from src.aim.services.email.workflow_state_manager import WorkflowStateManager

__all__ = [
    "TemplateRenderer",
    "WorkflowEngine",
    "WorkflowStateManager",
    "EmailScheduler",
    "EmailSender",
    "WebhookHandler",
    "get_scheduler",
    "init_scheduler",
    "start_scheduler",
    "stop_scheduler",
]
