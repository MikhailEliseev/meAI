"""
Compliance Checker - Tiered Gates System

Three-stage compliance checking for medical marketing keywords:
1. Pattern matching (<10ms) - Fast local check
2. openFDA lookup (cached 24h) - External validation
3. Risk scoring (1-25) - Action determination

Creates audit trail for regulatory defense.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from AIM.src.aim.subagents.compliance.patterns import ProhibitedPatternLibrary
from AIM.src.aim.subagents.compliance.fda_client import FDAClient
from AIM.src.aim.subagents.compliance.risk_scorer import RiskScorer
from AIM.src.aim.subagents.schemas.compliance import (
    ComplianceCheckResult,
    AuditTrailEntry,
)
from AIM.src.aim.storage.models import AuditTrail


class ComplianceChecker:
    """Tiered compliance checker for keyword research

    Three-stage gate system:
    - Stage 1: Pattern matching (<10ms) - Local prohibited language check
    - Stage 2: openFDA lookup (cached 24h) - FDA enforcement history
    - Stage 3: Risk scoring (1-25) - Likelihood × Severity

    Actions based on risk level:
    - CRITICAL (20-25): Block keyword
    - HIGH (15-19): Reduce priority 50%
    - MEDIUM/LOW (1-14): Pass with documentation

    All checks are logged to audit trail for regulatory defense.

    Args:
        database_url: SQLAlchemy database URL
        agent_id: Agent ID for audit trail
        patterns_file: Path to patterns YAML (optional)
    """

    def __init__(
        self,
        database_url: str = "sqlite+aiosqlite:///./data/aim.db",
        agent_id: str = "keyword-research-agent",
        patterns_file: Optional[str] = None,
    ):
        self.database_url = database_url
        self.agent_id = agent_id

        # Initialize components
        self.pattern_library = ProhibitedPatternLibrary(patterns_file)
        self.fda_client = FDAClient()
        self.risk_scorer = RiskScorer()

        # Database setup
        self.engine = create_async_engine(database_url, echo=False)
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def check_keyword(
        self,
        keyword: str,
        task_id: Optional[str] = None,
    ) -> ComplianceCheckResult:
        """Check keyword through three-stage gate system

        Args:
            keyword: Keyword to check
            task_id: Optional task ID for audit trail

        Returns:
            ComplianceCheckResult with risk assessment and action
        """
        # Stage 1: Pattern matching (<10ms)
        pattern_matches = self.pattern_library.check_keyword(keyword)
        pattern_severity = self.pattern_library.get_max_severity(pattern_matches)

        # Stage 2: openFDA lookup (cached 24h, graceful degradation)
        fda_records = await self.fda_client.search_enforcement(keyword, limit=10)

        # Handle graceful degradation (None = timeout/error)
        if fda_records is None:
            fda_enforcement_found = False
            fda_enforcement_count = 0
            fda_records = []
        else:
            fda_enforcement_found = len(fda_records) > 0
            fda_enforcement_count = len(fda_records)

        # Stage 3: Risk scoring
        scoring_result = self.risk_scorer.score_keyword(
            keyword=keyword,
            pattern_matches=pattern_matches,
            fda_enforcement_count=fda_enforcement_count,
            fda_enforcement_records=fda_records,
        )

        # Build result
        result = ComplianceCheckResult(
            keyword=keyword,
            matched_patterns=pattern_matches,
            pattern_severity=pattern_severity,
            fda_enforcement_found=fda_enforcement_found,
            fda_enforcement_count=fda_enforcement_count,
            fda_enforcement_records=fda_records,
            likelihood_score=scoring_result["likelihood_score"],
            severity_score=scoring_result["severity_score"],
            risk_score=scoring_result["risk_score"],
            risk_level=scoring_result["risk_level"],
            action=scoring_result["action"],
            rationale=scoring_result["rationale"],
            checked_at=datetime.now(timezone.utc),
        )

        # Create audit trail
        await self._create_audit_trail(result, task_id)

        return result

    async def _create_audit_trail(
        self,
        result: ComplianceCheckResult,
        task_id: Optional[str] = None,
    ) -> None:
        """Create audit trail entry in database

        Args:
            result: Compliance check result
            task_id: Optional task ID
        """
        # Serialize pattern matches to JSON
        matched_patterns_json = json.dumps([
            {
                "pattern": match.pattern,
                "category": match.category,
                "severity": match.severity,
                "rationale": match.rationale,
            }
            for match in result.matched_patterns
        ])

        # Serialize FDA records to JSON
        fda_details_json = json.dumps([
            {
                "recall_number": record.recall_number,
                "product_description": record.product_description,
                "reason_for_recall": record.reason_for_recall,
                "classification": record.classification,
                "recall_initiation_date": record.recall_initiation_date,
            }
            for record in result.fda_enforcement_records
        ])

        # Create audit trail record
        audit_record = AuditTrail(
            keyword=result.keyword,
            risk_level=result.risk_level.value,
            action=result.action.value,
            rationale=result.rationale,
            likelihood_score=result.likelihood_score,
            severity_score=result.severity_score,
            risk_score=result.risk_score,
            matched_patterns=matched_patterns_json if result.matched_patterns else None,
            pattern_severity=result.pattern_severity,
            fda_enforcement_found=1 if result.fda_enforcement_found else 0,
            fda_enforcement_count=result.fda_enforcement_count,
            fda_enforcement_details=fda_details_json if result.fda_enforcement_records else None,
            agent_id=self.agent_id,
            task_id=task_id,
            timestamp=result.checked_at,
        )

        # Save to database
        async with self.session_maker() as session:
            session.add(audit_record)
            await session.commit()

    async def get_audit_history(
        self,
        keyword: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditTrail]:
        """Get audit trail history

        Args:
            keyword: Filter by keyword (optional)
            risk_level: Filter by risk level (optional)
            limit: Maximum records to return

        Returns:
            List of audit trail records
        """
        async with self.session_maker() as session:
            query = select(AuditTrail)

            if keyword:
                query = query.where(AuditTrail.keyword == keyword)
            if risk_level:
                query = query.where(AuditTrail.risk_level == risk_level)

            query = query.order_by(AuditTrail.timestamp.desc()).limit(limit)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def close(self) -> None:
        """Close resources"""
        await self.fda_client.close()
        await self.engine.dispose()

    def __repr__(self) -> str:
        """String representation"""
        return f"<ComplianceChecker(agent_id='{self.agent_id}', patterns={self.pattern_library.get_pattern_count()})>"
