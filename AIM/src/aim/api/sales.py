"""Sales API Endpoints

Dashboard for the Sales Admin Agent — pipeline view, conversations,
activity log, manual qualification and escalation triggers.

Part of Phase 13: AI Sales Admin Agent — Sub-Phase 5.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.database import get_db
from src.aim.models.sales import SalesAgentActivity, SalesConversation, SalesEscalation, SalesMessage
from src.aim.subagents.sales.knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sales", tags=["sales"])


# ── Request/Response schemas ──────────────────────────────────────────────


class PipelineStats(BaseModel):
    stage: str
    count: int


class PipelineResponse(BaseModel):
    total: int
    by_status: list[PipelineStats]
    by_tier: list[PipelineStats]


class ConversationSummary(BaseModel):
    id: str
    channel: str
    status: str
    messages_count: int
    qualification_tier: Optional[str] = None
    qualification_score: Optional[int] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime


class ConversationList(BaseModel):
    conversations: list[ConversationSummary]
    total: int


class ActivityEntry(BaseModel):
    id: str
    agent_type: str
    action: str
    conversation_id: Optional[str] = None
    lead_id: Optional[str] = None
    duration_ms: Optional[int] = None
    success: Optional[bool] = None
    created_at: datetime


class ActivityList(BaseModel):
    activities: list[ActivityEntry]
    total: int


class ManualEscalateRequest(BaseModel):
    conversation_id: str
    reason: str = "manual"
    severity: str = "urgent"
    notes: str = ""


class ManualQualifyRequest(BaseModel):
    conversation_id: str
    score: int = Field(ge=0, le=100)
    tier: str = Field(pattern=r"^(hot|warm|cold)$")
    notes: str = ""


class KnowledgeSyncRequest(BaseModel):
    client_id: str


class KnowledgeUpdateRequest(BaseModel):
    client_id: str
    filename: str = Field(pattern=r"^(services|faq|tone_of_voice|escalation_rules|qualification)\.md$")
    content: str = Field(min_length=1)


# ── Pipeline endpoints ────────────────────────────────────────────────────


@router.get("/pipeline", response_model=PipelineResponse)
async def get_pipeline(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PipelineResponse:
    """Sales pipeline overview — conversations by status and qualification tier."""
    base_q = select(SalesConversation)
    if project_id:
        base_q = base_q.where(SalesConversation.project_id == project_id)

    # Total
    total_result = await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )
    total = total_result.scalar() or 0

    # By status
    status_result = await db.execute(
        select(SalesConversation.status, func.count())
        .where(SalesConversation.project_id == project_id if project_id else True)
        .group_by(SalesConversation.status)
    )
    by_status = [
        PipelineStats(stage=row[0], count=row[1])
        for row in status_result.all()
    ]

    # By qualification tier (extracted from JSONB)
    # SQLite doesn't support jsonb path extraction cleanly, so we'll use raw strings
    tier_result = await db.execute(
        select(SalesConversation.qualification_result).where(
            SalesConversation.qualification_result.isnot(None)
        )
    )
    tiers: dict[str, int] = {}
    for (qr,) in tier_result.all():
        if isinstance(qr, dict):
            tier = qr.get("tier", "unknown")
            tiers[tier] = tiers.get(tier, 0) + 1

    by_tier = [PipelineStats(stage=k, count=v) for k, v in tiers.items()]

    return PipelineResponse(total=total, by_status=by_status, by_tier=by_tier)


@router.get("/conversations", response_model=ConversationList)
async def list_conversations(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ConversationList:
    """List conversations, optionally filtered by status."""
    q = select(SalesConversation).order_by(desc(SalesConversation.last_message_at))
    if status_filter:
        q = q.where(SalesConversation.status == status_filter)

    total_result = await db.execute(
        select(func.count()).select_from(q.subquery())
    )
    total = total_result.scalar() or 0

    result = await db.execute(q.limit(limit).offset(offset))
    convs = result.scalars().all()

    summaries = [
        ConversationSummary(
            id=c.id,
            channel=c.channel,
            status=c.status,
            messages_count=c.messages_count,
            qualification_tier=c.qualification_result.get("tier") if c.qualification_result else None,
            qualification_score=c.qualification_result.get("score") if c.qualification_result else None,
            last_message_at=c.last_message_at,
            created_at=c.created_at,
        )
        for c in convs
    ]

    return ConversationList(conversations=summaries, total=total)


@router.get("/activity", response_model=ActivityList)
async def list_activity(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> ActivityList:
    """Recent agent activity log."""
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    q = (
        select(SalesAgentActivity)
        .where(SalesAgentActivity.created_at >= since)
        .order_by(desc(SalesAgentActivity.created_at))
    )

    total_result = await db.execute(
        select(func.count()).select_from(q.subquery())
    )
    total = total_result.scalar() or 0

    result = await db.execute(q.limit(limit))
    activities = result.scalars().all()

    return ActivityList(
        activities=[
            ActivityEntry(
                id=a.id,
                agent_type=a.agent_type,
                action=a.action,
                conversation_id=a.conversation_id,
                lead_id=a.lead_id,
                duration_ms=a.duration_ms,
                success=a.success,
                created_at=a.created_at,
            )
            for a in activities
        ],
        total=total,
    )


# ── Manual actions ────────────────────────────────────────────────────────


@router.post("/qualify", status_code=status.HTTP_200_OK)
async def manual_qualify(
    body: ManualQualifyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually set qualification for a conversation."""
    result = await db.execute(
        select(SalesConversation).where(SalesConversation.id == body.conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.qualification_result = {
        "score": body.score,
        "tier": body.tier,
        "manual": True,
        "notes": body.notes,
        "qualified_at": datetime.now(timezone.utc).isoformat(),
    }
    db.add(conv)
    await db.commit()

    logger.info(f"Manual qualification: {body.conversation_id} → {body.tier} ({body.score})")
    return {"status": "ok", "conversation_id": body.conversation_id, "tier": body.tier}


@router.post("/escalate", status_code=status.HTTP_200_OK)
async def manual_escalate(
    body: ManualEscalateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually escalate a conversation to a human manager."""
    result = await db.execute(
        select(SalesConversation).where(SalesConversation.id == body.conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = "escalated"
    conv.escalation_count = (conv.escalation_count or 0) + 1
    db.add(conv)

    esc = SalesEscalation(
        conversation_id=body.conversation_id,
        reason=body.reason,
        severity=body.severity,
        context_snapshot={"manual": True, "notes": body.notes},
    )
    db.add(esc)
    await db.commit()

    logger.info(f"Manual escalation: {body.conversation_id} reason={body.reason}")
    return {"status": "ok", "conversation_id": body.conversation_id}


# ── Knowledge management ──────────────────────────────────────────────────


_knowledge = KnowledgeManager()


@router.post("/knowledge/sync", status_code=status.HTTP_200_OK)
async def sync_knowledge(body: KnowledgeSyncRequest) -> dict:
    """Trigger knowledge sync for a client — reload vault from disk."""
    _knowledge.invalidate_cache(body.client_id)
    vault = _knowledge.load_vault(body.client_id, use_cache=False)
    return {
        "status": "ok",
        "client_id": body.client_id,
        "files": list(vault.keys()),
    }


@router.put("/knowledge/update", status_code=status.HTTP_200_OK)
async def update_knowledge(body: KnowledgeUpdateRequest) -> dict:
    """Update a single vault file for a client."""
    _knowledge.update_file(body.client_id, body.filename, body.content)
    return {
        "status": "ok",
        "client_id": body.client_id,
        "filename": body.filename,
    }


@router.get("/knowledge/{client_id}", status_code=status.HTTP_200_OK)
async def get_knowledge(client_id: str) -> dict:
    """Get all vault files for a client."""
    vault = _knowledge.load_vault(client_id)
    return {
        "client_id": client_id,
        "files": list(vault.keys()),
        "content": vault,
    }
