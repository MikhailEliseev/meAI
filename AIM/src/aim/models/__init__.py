"""
AIM Models Package

Data models for AIM Agency.
"""

from src.aim.storage.models import Base
from src.aim.models.analytics_models import (
    DomainMetrics,
    AggregatedMetrics,
    Correlation,
    StrategicInsight,
    CrossDomainMetrics,
    AnalyticsAlert,
)
from src.aim.models.lead import Lead
from src.aim.models.linear_task import LinearTask
from src.aim.models.email_workflow import EmailWorkflow
from src.aim.models.scheduled_email import ScheduledEmail
from src.aim.models.email_event import EmailEvent
from src.aim.models.email_template import EmailTemplate
from src.aim.models.payment import Payment
from src.aim.models.document import Document
from src.aim.models.fz152_audit import FZ152AuditLog
from src.aim.models.sales import (
    SalesConversation,
    SalesMessage,
    SalesEscalation,
    SalesAgentActivity,
)
from src.aim.models.company_profile import CompanyProfileModel

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
    "CompanyProfileModel",
]
