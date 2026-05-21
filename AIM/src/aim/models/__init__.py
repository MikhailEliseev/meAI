"""
AIM Models Package

Data models for AIM Agency.
"""

from aim.storage.models import Base
from aim.models.analytics_models import (
    DomainMetrics,
    AggregatedMetrics,
    Correlation,
    StrategicInsight,
    CrossDomainMetrics,
    AnalyticsAlert,
)
from aim.models.lead import Lead
from aim.models.linear_task import LinearTask
from aim.models.email_workflow import EmailWorkflow
from aim.models.scheduled_email import ScheduledEmail
from aim.models.email_event import EmailEvent
from aim.models.email_template import EmailTemplate
from aim.models.payment import Payment
from aim.models.document import Document
from aim.models.fz152_audit import FZ152AuditLog
from aim.models.sales import (
    SalesConversation,
    SalesMessage,
    SalesEscalation,
    SalesAgentActivity,
)

__all__ = [
    "Base",
    "DomainMetrics",
    "AggregatedMetrics",
    "Correlation",
    "StrategicInsight",
    "CrossDomainMetrics",
    "AnalyticsAlert",
    "Lead",
    "LinearTask",
    "EmailWorkflow",
    "ScheduledEmail",
    "EmailEvent",
    "EmailTemplate",
    "Payment",
    "Document",
    "FZ152AuditLog",
    "SalesConversation",
    "SalesMessage",
    "SalesEscalation",
    "SalesAgentActivity",
]
