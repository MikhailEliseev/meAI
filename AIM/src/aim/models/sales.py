"""Sales Admin Agent — database models.

Persistent storage for conversations, messages, escalations, and agent activity.
Part of Phase 13: AI Sales Admin Agent.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from aim.storage.models import Base


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ── Conversation ────────────────────────────────────────────────────────────

class SalesConversation(Base):
    """Active or recent conversation on any channel."""

    __tablename__ = "sales_conversations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: _new_id("conv"))
    client_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    lead_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    channel_user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    qualification_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    escalation_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_sales_conv_channel_user", "channel", "channel_user_id"),
        Index("idx_sales_conv_status", "status"),
        Index("idx_sales_conv_lead", "lead_id"),
    )


# ── Message ─────────────────────────────────────────────────────────────────

class SalesMessage(Base):
    """Individual message in a conversation — persisted for audit + training."""

    __tablename__ = "sales_messages"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: _new_id("msg"))
    conversation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("sales_conversations.id"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # incoming / outgoing
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), default="text")
    sender_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_sales_msg_conv", "conversation_id", "created_at"),
    )


# ── Escalation ──────────────────────────────────────────────────────────────

class SalesEscalation(Base):
    """Audit trail for human escalations (required for 152-ФЗ compliance)."""

    __tablename__ = "sales_escalations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: _new_id("esc"))
    conversation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("sales_conversations.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    escalated_to: Mapped[str] = mapped_column(String(50), nullable=True)
    notification_channel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_sales_esc_conv", "conversation_id"),
    )


# ── Agent Activity Log ──────────────────────────────────────────────────────

class SalesAgentActivity(Base):
    """Immutable activity log — everything the agent does."""

    __tablename__ = "sales_agent_activity"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: _new_id("act"))
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    lead_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_sales_act_time", "created_at"),
        Index("idx_sales_act_type", "agent_type", "action"),
    )
