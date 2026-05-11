"""
SQLAlchemy Database Models for AIM Agency

Models for compliance tracking, user feedback, and audit trails.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class AuditTrail(Base):
    """Audit trail for compliance tracking

    Stores all compliance checks for regulatory defense.
    Immutable record of what was checked, when, and why.
    """
    __tablename__ = "audit_trail"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Keyword and compliance data
    keyword: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # blocked, reduced, passed
    rationale: Mapped[str] = mapped_column(Text, nullable=False)  # Why this decision was made

    # Risk scoring details
    likelihood_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    severity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-25

    # Pattern matching results
    matched_patterns: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of matched patterns
    pattern_severity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Max severity from patterns

    # FDA enforcement data
    fda_enforcement_found: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True)  # 0 or 1 (SQLite boolean)
    fda_enforcement_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fda_enforcement_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Metadata
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_keyword_timestamp', 'keyword', 'timestamp'),
        Index('idx_risk_level_timestamp', 'risk_level', 'timestamp'),
        Index('idx_action_timestamp', 'action', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<AuditTrail(id={self.id}, keyword='{self.keyword}', risk_level='{self.risk_level}', action='{self.action}')>"


class UserFeedbackRecord(Base):
    """User feedback on keyword priority accuracy

    Stores user corrections to priority scores for learning and improvement.
    Used to tune the priority scoring algorithm over time.
    """
    __tablename__ = "user_feedback"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Keyword and original analysis
    keyword: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    original_priority_score: Mapped[float] = mapped_column(Float, nullable=False)

    # User feedback
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    user_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # User's corrected score
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Free-form feedback
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # too_high, too_low, accurate

    # Original analysis data (for learning)
    original_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    original_difficulty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    original_cpc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_keyword_feedback_type', 'keyword', 'feedback_type'),
        Index('idx_feedback_type_timestamp', 'feedback_type', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<UserFeedbackRecord(id={self.id}, keyword='{self.keyword}', feedback_type='{self.feedback_type}')>"
