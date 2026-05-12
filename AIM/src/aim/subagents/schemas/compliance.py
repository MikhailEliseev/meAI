"""
Compliance Data Schemas

Pydantic models for compliance checking, risk assessment, and audit trails.
Used by Keyword Research Agent compliance integration.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class RiskLevel(str, Enum):
    """Risk level classification for compliance checks

    Based on Likelihood × Severity scoring (1-25 scale):
    - CRITICAL: 20-25 (block keyword)
    - HIGH: 15-19 (reduce priority 50%)
    - MEDIUM: 8-14 (pass with documentation)
    - LOW: 1-7 (pass with documentation)
    """
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ComplianceAction(str, Enum):
    """Action to take based on risk level"""
    BLOCKED = "blocked"  # CRITICAL risk - keyword blocked
    REDUCED = "reduced"  # HIGH risk - priority reduced 50%
    PASSED = "passed"    # MEDIUM/LOW risk - passed with documentation


class PatternMatch(BaseModel):
    """Single pattern match result"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pattern": "cure.*cancer",
                "category": "cure_claims",
                "severity": 5,
                "rationale": "FDA prohibits cure claims for cancer without approval"
            }
        }
    )

    pattern: str = Field(..., description="Matched pattern text")
    category: str = Field(..., description="Pattern category (e.g., 'cure_claims', 'guarantees')")
    severity: int = Field(..., ge=1, le=5, description="Pattern severity (1-5)")
    rationale: str = Field(..., description="Why this pattern is prohibited")


class FDAEnforcementRecord(BaseModel):
    """FDA enforcement action record"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recall_number": "F-1234-2026",
                "product_description": "Dietary supplement claiming to cure diabetes",
                "reason_for_recall": "Unapproved drug claims",
                "classification": "Class II",
                "recall_initiation_date": "2026-03-15"
            }
        }
    )

    recall_number: str = Field(..., description="FDA recall number")
    product_description: str = Field(..., description="Product description")
    reason_for_recall: str = Field(..., description="Reason for recall")
    classification: str = Field(..., description="FDA classification (Class I, II, III)")
    recall_initiation_date: Optional[str] = Field(None, description="Recall date")


class ComplianceCheckResult(BaseModel):
    """Result of compliance check for a keyword

    Contains all compliance data: pattern matches, FDA enforcement,
    risk scoring, and recommended action.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keyword": "cure diabetes naturally",
                "matched_patterns": [
                    {
                        "pattern": "cure.*diabetes",
                        "category": "cure_claims",
                        "severity": 5,
                        "rationale": "FDA prohibits cure claims for diabetes"
                    }
                ],
                "pattern_severity": 5,
                "fda_enforcement_found": True,
                "fda_enforcement_count": 2,
                "fda_enforcement_records": [],
                "likelihood_score": 5,
                "severity_score": 5,
                "risk_score": 25,
                "risk_level": "CRITICAL",
                "action": "blocked",
                "rationale": "CRITICAL risk: Cure claims for diabetes + FDA enforcement history. Likelihood=5 (pattern match + FDA history), Severity=5 (serious disease). Risk=25. Action: BLOCK keyword.",
                "checked_at": "2026-05-11T21:35:00Z"
            }
        }
    )

    keyword: str = Field(..., description="Keyword that was checked")

    # Stage 1: Pattern matching
    matched_patterns: List[PatternMatch] = Field(
        default_factory=list,
        description="Prohibited patterns found in keyword"
    )
    pattern_severity: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Maximum severity from matched patterns"
    )

    # Stage 2: FDA enforcement
    fda_enforcement_found: bool = Field(
        default=False,
        description="Whether FDA enforcement actions were found"
    )
    fda_enforcement_count: int = Field(
        default=0,
        description="Number of FDA enforcement actions found"
    )
    fda_enforcement_records: List[FDAEnforcementRecord] = Field(
        default_factory=list,
        description="FDA enforcement action details"
    )

    # Stage 3: Risk scoring
    likelihood_score: int = Field(..., ge=1, le=5, description="Likelihood of regulatory action (1-5)")
    severity_score: int = Field(..., ge=1, le=5, description="Severity of consequences (1-5)")
    risk_score: int = Field(..., ge=1, le=25, description="Total risk score (Likelihood × Severity)")
    risk_level: RiskLevel = Field(..., description="Risk level classification")

    # Action and rationale
    action: ComplianceAction = Field(..., description="Recommended action")
    rationale: str = Field(..., description="Detailed rationale for the decision")

    # Metadata
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp")


class AuditTrailEntry(BaseModel):
    """Audit trail entry for regulatory defense

    Immutable record of compliance check for legal/regulatory purposes.
    Stored in database for long-term retention.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keyword": "cure diabetes naturally",
                "risk_level": "CRITICAL",
                "action": "blocked",
                "rationale": "CRITICAL risk: Cure claims for diabetes + FDA enforcement history",
                "likelihood_score": 5,
                "severity_score": 5,
                "risk_score": 25,
                "matched_patterns": '[{"pattern": "cure.*diabetes", "severity": 5}]',
                "pattern_severity": 5,
                "fda_enforcement_found": True,
                "fda_enforcement_count": 2,
                "fda_enforcement_details": '[{"recall_number": "F-1234-2026"}]',
                "agent_id": "keyword-research-agent",
                "task_id": "task-123",
                "timestamp": "2026-05-11T21:35:00Z"
            }
        }
    )

    keyword: str = Field(..., description="Keyword that was checked")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    action: ComplianceAction = Field(..., description="Action taken")
    rationale: str = Field(..., description="Detailed rationale")

    # Risk scoring
    likelihood_score: int = Field(..., ge=1, le=5, description="Likelihood score")
    severity_score: int = Field(..., ge=1, le=5, description="Severity score")
    risk_score: int = Field(..., ge=1, le=25, description="Total risk score")

    # Pattern matching
    matched_patterns: Optional[str] = Field(None, description="JSON array of matched patterns")
    pattern_severity: Optional[int] = Field(None, ge=1, le=5, description="Max pattern severity")

    # FDA enforcement
    fda_enforcement_found: bool = Field(default=False, description="FDA enforcement found")
    fda_enforcement_count: int = Field(default=0, description="Number of FDA actions")
    fda_enforcement_details: Optional[str] = Field(None, description="JSON array of FDA records")

    # Metadata
    agent_id: str = Field(..., description="Agent that performed check")
    task_id: Optional[str] = Field(None, description="Task ID if applicable")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp")
