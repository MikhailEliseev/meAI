"""
Onboarding Database Models

SQLAlchemy models for onboarding workflow state persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid

from aim.storage.database import Base


class OnboardingSession(Base):
    """Onboarding session state"""

    __tablename__ = "onboarding_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(255), nullable=False, index=True)

    # Current stage
    stage = Column(String(50), nullable=False, index=True)

    # Session data (JSON)
    data = Column(JSON, nullable=False, default=dict)

    # State transition history
    history = Column(JSON, nullable=False, default=list)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<OnboardingSession(id={self.id}, client_id={self.client_id}, stage={self.stage})>"


class OnboardingState(Base):
    """Onboarding state snapshots for audit"""

    __tablename__ = "onboarding_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # State snapshot
    stage = Column(String(50), nullable=False)
    event = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False, default=dict)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<OnboardingState(session_id={self.session_id}, stage={self.stage}, event={self.event})>"
