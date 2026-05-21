"""Email Template model for email automation.

Stores reusable email templates for different tiers and steps.
Templates support Jinja2 variables and AI content generation.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON

from aim.storage.models import Base


class EmailTemplate(Base):
    """Email template for automated campaigns.

    Stores reusable templates for different lead tiers and workflow steps.
    Supports Jinja2 templating with dynamic variables.
    Can include AI prompts for content personalization.

    Attributes:
        id: Template identifier (e.g., 'hot_instant', 'warm_day0')
        name: Human-readable template name
        tier: Lead tier (hot, warm, cold)
        step: Step in workflow sequence (0-indexed)
        subject_template: Email subject with Jinja2 variables
        html_template: HTML email body with Jinja2 variables
        text_template: Plain text email body with Jinja2 variables
        ai_prompt: Optional prompt for AI content generation
        variables: JSON schema of required template variables
        created_at: When template was created
        updated_at: When template was last modified

    Template Variables:
        Common variables available in all templates:
        - {name}: Lead name
        - {email}: Lead email
        - {specialty}: Lead specialty (стоматология, etc.)
        - {service}: Service of interest
        - {manager_name}: Assigned manager name
        - {manager_phone}: Manager phone
        - {unsubscribe_url}: Unsubscribe link (required by law)

    AI Personalization:
        If ai_prompt is set, the template renderer will:
        1. Generate personalized content using AI
        2. Inject generated content into template variables
        3. Render final email with Jinja2

    Example:
        Template with AI personalization:
        ```
        subject_template: "Ваш запрос на {service} получен"
        html_template: "<p>Здравствуйте, {name}!</p><p>{ai_intro}</p>"
        ai_prompt: "Write personalized intro for {specialty} doctor interested in {service}"
        ```
    """

    __tablename__ = "email_templates"

    id = Column(String(50), primary_key=True)  # e.g., 'hot_instant', 'warm_day0'
    name = Column(String(255), nullable=False)
    tier = Column(String(10), nullable=False)  # hot, warm, cold
    step = Column(Integer, nullable=False)  # 0-indexed step in sequence
    subject_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=False)
    text_template = Column(Text, nullable=False)
    ai_prompt = Column(Text, nullable=True)  # Optional AI content generation prompt
    variables = Column(JSON, nullable=True)  # JSON schema of required variables
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<EmailTemplate(id={self.id}, tier={self.tier}, step={self.step}, name={self.name})>"
