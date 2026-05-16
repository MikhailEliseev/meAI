"""Linear Service - Business logic for lead task management

Handles:
- Creating Linear tasks for Hot/Warm leads
- Round-robin assignment to sales team
- Task status synchronization
- Priority mapping and task formatting

Part of: Phase 11 Sprint 2 - Task 2.3
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from AIM.src.aim.ai.lead_scoring.schemas import LeadScore
from AIM.src.aim.integrations.linear.client import LinearClient
from AIM.src.aim.integrations.linear.schemas import LinearIssue, LinearTask
from aim.models.lead import Lead
from AIM.src.aim.utils.encryption import get_encryptor


class LinearService:
    """Linear service for lead task management

    Features:
    - Create tasks for Hot/Warm leads
    - Round-robin assignment
    - Status synchronization
    - Task formatting with lead details
    """

    # Priority mapping: tier -> Linear priority
    PRIORITY_MAP = {
        "Hot": 1,  # Urgent
        "Warm": 2,  # High
        "Cold": 4,  # Low (not created by default)
    }

    # Status mapping: Linear state type -> AIM status
    STATUS_MAP = {
        "backlog": "backlog",
        "unstarted": "backlog",
        "started": "in_progress",
        "completed": "completed",
        "canceled": "canceled",
    }

    def __init__(
        self,
        linear_client: LinearClient,
        db_session: AsyncSession,
        team_id: str,
        hot_label_id: str,
        warm_label_id: str,
        assignees: list[str],
    ):
        """Initialize Linear service

        Args:
            linear_client: Linear API client
            db_session: Database session
            team_id: Linear team ID for sales
            hot_label_id: Label ID for Hot leads
            warm_label_id: Label ID for Warm leads
            assignees: List of assignee user IDs for round-robin
        """
        self.client = linear_client
        self.db = db_session
        self.team_id = team_id
        self.hot_label_id = hot_label_id
        self.warm_label_id = warm_label_id
        self.assignees = assignees
        self._assignee_index = 0
        self.encryptor = get_encryptor()

    async def create_task_for_lead(
        self,
        lead: Lead,
        score_result: LeadScore,
    ) -> LinearTask:
        """Create Linear task for lead

        Args:
            lead: Lead record
            score_result: Lead scoring result

        Returns:
            Created Linear task

        Raises:
            ValueError: If task creation fails
        """
        # Generate task title and description
        title = self._generate_task_title(lead, score_result)
        description = self._generate_task_description(lead, score_result)

        # Get priority and labels
        priority = self.PRIORITY_MAP.get(score_result.tier, 0)
        label_ids = self._get_label_ids(score_result.tier)

        # Get next assignee (round-robin)
        assignee_id = await self._get_next_assignee()

        # Create Linear issue
        issue = await self.client.create_issue(
            team_id=self.team_id,
            title=title,
            description=description,
            priority=priority,
            label_ids=label_ids,
            assignee_id=assignee_id,
        )

        # Create task record in database
        task = LinearTask(
            id=str(uuid.uuid4()),
            lead_id=lead.id,
            linear_issue_id=issue.id,
            linear_url=issue.url,
            status=self.STATUS_MAP.get(issue.state.type, "backlog"),
            assignee_id=assignee_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return task

    async def update_task_status(
        self,
        task_id: str,
        status: str,
    ) -> None:
        """Update task status in database

        Args:
            task_id: Task ID
            status: New status (backlog, in_progress, completed, canceled)
        """
        from AIM.src.aim.models.linear_task import LinearTask as LinearTaskModel

        stmt = select(LinearTaskModel).where(LinearTaskModel.id == task_id)
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            task.status = status
            task.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def sync_task_status(
        self,
        linear_issue_id: str,
    ) -> None:
        """Sync task status from Linear to AIM database

        Args:
            linear_issue_id: Linear issue ID
        """
        from AIM.src.aim.models.linear_task import LinearTask as LinearTaskModel

        # Fetch issue from Linear
        issue = await self.client.get_issue(linear_issue_id)

        # Find task in database
        stmt = select(LinearTaskModel).where(
            LinearTaskModel.linear_issue_id == linear_issue_id
        )
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            # Update status
            new_status = self.STATUS_MAP.get(issue.state.type, "backlog")
            task.status = new_status
            task.updated_at = datetime.now(timezone.utc)

            # Update assignee if changed
            if issue.assignee:
                task.assignee_id = issue.assignee.id

            await self.db.commit()

    async def _get_next_assignee(self) -> str | None:
        """Get next assignee using round-robin

        Returns:
            Assignee user ID or None if no assignees configured
        """
        if not self.assignees:
            return None

        assignee = self.assignees[self._assignee_index]
        self._assignee_index = (self._assignee_index + 1) % len(self.assignees)
        return assignee

    def _get_label_ids(self, tier: str) -> list[str]:
        """Get label IDs for tier

        Args:
            tier: Lead tier (Hot, Warm, Cold)

        Returns:
            List of label IDs
        """
        if tier == "Hot":
            return [self.hot_label_id]
        elif tier == "Warm":
            return [self.warm_label_id]
        else:
            return []

    def _generate_task_title(self, lead: Lead, score_result: LeadScore) -> str:
        """Generate task title

        Args:
            lead: Lead record
            score_result: Lead scoring result

        Returns:
            Task title in format: "[Hot] Plastic Surgery Lead - Score 87"
        """
        specialty = lead.specialty.replace("_", " ").title()
        return f"[{score_result.tier}] {specialty} Lead - Score {score_result.score}"

    def _generate_task_description(
        self,
        lead: Lead,
        score_result: LeadScore,
    ) -> str:
        """Generate task description with lead details

        Args:
            lead: Lead record
            score_result: Lead scoring result

        Returns:
            Task description (markdown)
        """
        # Decrypt sensitive fields
        name = self.encryptor.decrypt(lead.name_encrypted)
        phone = self.encryptor.decrypt(lead.phone_encrypted)
        email = self.encryptor.decrypt(lead.email_encrypted)
        clinic = self.encryptor.decrypt(lead.clinic_name_encrypted)
        message = (
            self.encryptor.decrypt(lead.message_encrypted)
            if lead.message_encrypted
            else "N/A"
        )

        # Format explanation
        explanation = "\n".join(f"- {item}" for item in score_result.explanation)

        # Format timestamp
        submitted_at = lead.created_at.strftime("%Y-%m-%d %H:%M UTC")

        return f"""## Lead Information

**Name:** {name}
**Phone:** {phone}
**Email:** {email}
**Clinic:** {clinic}
**Specialty:** {lead.specialty.replace("_", " ").title()}

## Message

{message}

## Scoring Details

**Score:** {score_result.score}/100
**Tier:** {score_result.tier}

**Why this lead scored high:**
{explanation}

## Source

**Traffic Source:** {lead.source}
**UTM Campaign:** {lead.utm_campaign or "N/A"}
**Submitted:** {submitted_at}

## Next Steps

1. Call within 15 minutes (Hot leads) or 2 hours (Warm leads)
2. Verify specialty and clinic details
3. Schedule consultation
4. Update task status in Linear when contacted
"""
