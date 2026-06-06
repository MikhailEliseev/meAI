"""GDPR/FZ-152 Data Subject Rights Endpoints

Right to deletion (ФЗ-152 ст.21) — anonymize PII, keep metadata.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import structlog

from src.aim.database import get_db
from src.aim.models.lead import Lead
from src.aim.models.fz152_audit import FZ152AuditLog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/gdpr", tags=["gdpr"])


@router.delete("/leads/{lead_id}", status_code=status.HTTP_200_OK)
async def gdpr_delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Anonymize lead PII per right-to-deletion request (ФЗ-152 ст.21).

    Does NOT hard-delete. Anonymizes PII fields, preserves metadata.
    """
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.name_encrypted == "DELETED":
        raise HTTPException(status_code=409, detail="Lead already anonymized")

    old_name = lead.name

    lead.name_encrypted = "DELETED"
    lead.phone_encrypted = ""
    lead.email_encrypted = ""
    lead.processed = False

    audit = FZ152AuditLog(
        lead_id=lead_id,
        action="gdpr_deletion_request",
        ip_address="0.0.0.0",
        details={
            "anonymized_at": datetime.now(timezone.utc).isoformat(),
            "fields_anonymized": ["name", "phone", "email"],
            "name_was": f"{old_name[:1]}***" if old_name else "***",
        },
    )
    db.add(audit)
    await db.commit()

    logger.info("gdpr_deletion_completed", lead_id=lead_id)
    return {
        "status": "anonymized",
        "lead_id": lead_id,
        "message": "Personal data anonymized per ФЗ-152 ст.21",
        "anonymized_at": datetime.now(timezone.utc).isoformat(),
    }
