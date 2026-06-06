"""CRM Sync Agent — Bitrix24 integration for Sales Admin.

Subscribes to EventBus events, syncs qualified leads to Bitrix24 CRM,
handles incoming webhooks, and performs deduplication before creating entities.

Flow:
    Lead qualified → sales.lead.qualified (EventBus)
        → CrmAgent._on_lead_qualified()
        → decrypt PII → check Bitrix24 for duplicates
        → create/update lead → create contact → create deal
        → log to SalesAgentActivity

    Bitrix24 webhook → sales.crm.updated (EventBus)
        → CrmAgent._on_crm_updated()
        → update AIM lead status
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.database import get_db
from src.aim.integrations.bitrix24.client import Bitrix24Client, create_bitrix24_client
from src.aim.integrations.bitrix24.schemas import (
    Bitrix24Contact,
    Bitrix24Deal,
    Bitrix24Lead,
    Bitrix24Webhook,
    CrmSyncResult,
)
from src.aim.models.lead import Lead
from src.aim.models.sales import SalesAgentActivity, SalesConversation
from src.aim.utils.encryption import FieldEncryption

logger = logging.getLogger(__name__)


class CrmAgent:
    """Autonomous CRM sync agent.

    Bridges AIM's internal lead management with Bitrix24 CRM:
    - Qualified leads → Bitrix24 (lead + contact + deal)
    - Bitrix24 updates → AIM lead status sync
    - Dedup before creation

    Uses FieldEncryption to decrypt PII before sending to Bitrix24.
    This is a security boundary — PII is encrypted at rest in AIM,
    decrypted only when actively syncing to CRM.
    """

    def __init__(
        self,
        event_bus=None,
        encryption: FieldEncryption | None = None,
        client: Bitrix24Client | None = None,
    ) -> None:
        import os

        self._event_bus = event_bus
        self._client = client or create_bitrix24_client()

        if encryption:
            self._encryption = encryption
        else:
            try:
                self._encryption = FieldEncryption()
            except Exception:
                logger.warning("CrmAgent: encryption not configured — PII decryption will fail")
                self._encryption = None

        self._deals_pipeline_id: int = int(os.getenv("BITRIX24_DEAL_PIPELINE_ID", "0") or "0")

        if self._event_bus:
            self._event_bus.subscribe("sales.lead.qualified", self._on_lead_qualified)
            self._event_bus.subscribe("sales.crm.updated", self._on_crm_updated)
            logger.info("CrmAgent subscribed to events")

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def _decrypt_lead(self, lead: Lead) -> dict:
        """Decrypt PII fields from a Lead. Returns dict with plaintext fields."""
        if not self._encryption:
            logger.warning("CrmAgent: cannot decrypt lead — encryption not configured")
            return {"name": None, "phone": None, "email": None, "clinic_name": None}
        return {
            "name": self._encryption.decrypt(lead.name_encrypted) if lead.name_encrypted else None,
            "phone": self._encryption.decrypt(lead.phone_encrypted) if lead.phone_encrypted else None,
            "email": self._encryption.decrypt(lead.email_encrypted) if lead.email_encrypted else None,
            "clinic_name": self._encryption.decrypt(lead.clinic_name_encrypted) if lead.clinic_name_encrypted else None,
        }

    async def _log_activity(
        self,
        agent_type: str,
        action: str,
        lead_id: str | None = None,
        conversation_id: str | None = None,
        duration_ms: int | None = None,
        success: bool | None = None,
        details: dict | None = None,
    ) -> None:
        """Write an entry to SalesAgentActivity log."""
        import uuid

        try:
            db: AsyncSession
            async for db in get_db():
                entry = SalesAgentActivity(
                    id=f"act_{uuid.uuid4().hex[:12]}",
                    agent_type=agent_type,
                    action=action,
                    conversation_id=conversation_id,
                    lead_id=lead_id,
                    duration_ms=duration_ms,
                    success=success,
                    details=details,
                )
                db.add(entry)
                await db.commit()
                break
        except Exception as e:
            logger.warning("CrmAgent: failed to log activity: %s", e)

    # ── Event handlers ────────────────────────────────────────────────────

    async def _on_lead_qualified(self, event) -> None:
        """Handle sales.lead.qualified event.

        Event payload: {lead_id, score, tier, conversation_id}
        Syncs the qualified lead to Bitrix24 CRM.
        """
        if not self.enabled:
            logger.info("CrmAgent: Bitrix24 not configured — skipping lead sync")
            return

        lead_id = event.payload.get("lead_id")
        if not lead_id:
            logger.warning("CrmAgent: lead.qualified event missing lead_id")
            return

        await self.sync_lead_to_crm(lead_id)

    async def _on_crm_updated(self, event) -> None:
        """Handle sales.crm.updated event — Bitrix24 webhook data."""
        webhook_data = event.payload
        logger.info("CrmAgent: received CRM update event=%s", webhook_data.get("event"))
        # Future: update AIM lead status based on CRM changes

    # ── Sync logic ────────────────────────────────────────────────────────

    async def sync_lead_to_crm(self, aim_lead_id: str) -> list[CrmSyncResult]:
        """Full sync: decrypt lead → dedup → create/update in Bitrix24.

        Returns list of CrmSyncResult for each operation (lead, contact, deal).
        """
        if not self.enabled:
            return [CrmSyncResult(success=False, action="sync", error="Bitrix24 not configured")]

        import time
        start = time.monotonic()

        results: list[CrmSyncResult] = []

        try:
            db: AsyncSession
            async for db in get_db():
                result = await db.execute(select(Lead).where(Lead.id == aim_lead_id))
                lead = result.scalar_one_or_none()
                if not lead:
                    logger.warning("CrmAgent: lead not found id=%s", aim_lead_id)
                    results.append(CrmSyncResult(success=False, action="sync", error="Lead not found", aim_lead_id=aim_lead_id))
                    break

                pii = self._decrypt_lead(lead)
                logger.info("CrmAgent: syncing lead id=%s specialty=%s", aim_lead_id, lead.specialty)

                # 1. Dedup: check for existing lead in Bitrix24
                existing = None
                if pii["email"]:
                    existing = await self._client.find_lead_by_email(pii["email"])
                if not existing and pii["phone"]:
                    existing = await self._client.find_lead_by_phone(pii["phone"])

                if existing:
                    # Update existing lead
                    bx_lead = Bitrix24Lead(
                        title=f"{pii['name'] or 'Лид'} — {pii.get('clinic_name') or lead.specialty or 'клиника'}",
                        name=pii["name"],
                        phone=pii["phone"],
                        email=pii["email"],
                        source_description=f"AIM auto-sync (lead={aim_lead_id})",
                        uf_crm_lead_aim_id=aim_lead_id,
                        uf_crm_lead_tier=lead.score_tier,
                    )
                    bitrix24_id = existing.get("ID")
                    result = await self._client.update_lead(bitrix24_id, bx_lead)
                    results.append(result)
                else:
                    # Create new lead
                    bx_lead = Bitrix24Lead(
                        title=f"{pii['name'] or 'Лид'} — {pii.get('clinic_name') or lead.specialty or 'клиника'}",
                        name=pii["name"],
                        phone=pii["phone"],
                        email=pii["email"],
                        source_id="WEB",
                        source_description=f"AIM auto-sync (lead={aim_lead_id})",
                        comments=f"Специализация: {lead.specialty}\nИсточник: {lead.source}",
                        uf_crm_lead_aim_id=aim_lead_id,
                        uf_crm_lead_tier=getattr(lead, 'score_tier', None),
                    )
                    result = await self._client.create_lead(bx_lead)
                    results.append(result)

                if not result.success:
                    break

                bitrix24_id = result.bitrix24_id
                if not bitrix24_id:
                    break

                # 2. Create/update contact
                bx_contact = Bitrix24Contact(
                    name=pii["name"],
                    phone=pii["phone"],
                    email=pii["email"],
                    source_description=f"AIM lead {aim_lead_id}",
                    uf_crm_contact_aim_id=aim_lead_id,
                )
                contact_result = await self._client.create_contact(bx_contact)
                results.append(contact_result)

                # 3. Create deal for qualified leads
                if lead.score_tier in ("hot", "warm"):
                    bx_deal = Bitrix24Deal(
                        title=f"Сделка: {pii['name'] or 'Лид'} — {pii.get('clinic_name') or lead.specialty}",
                        lead_id=bitrix24_id,
                        stage_id="NEW",
                        comments=f"AIM квалификация: {lead.score_tier.upper()} (score={getattr(lead, 'score', 'N/A')})",
                        uf_crm_deal_aim_id=aim_lead_id,
                    )
                    if self._deals_pipeline_id:
                        bx_deal.category_id = self._deals_pipeline_id
                    deal_result = await self._client.create_deal(bx_deal)
                    results.append(deal_result)

                # Update AIM lead with Bitrix24 ID
                await db.execute(
                    update(Lead).where(Lead.id == aim_lead_id).values(
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                await db.commit()

                break

        except Exception as e:
            logger.exception("CrmAgent: sync failed for lead %s: %s", aim_lead_id, e)
            results.append(CrmSyncResult(success=False, action="sync", error=str(e), aim_lead_id=aim_lead_id))

        duration_ms = int((time.monotonic() - start) * 1000)
        await self._log_activity(
            agent_type="crm_agent",
            action="sync_lead",
            lead_id=aim_lead_id,
            duration_ms=duration_ms,
            success=all(r.success for r in results) if results else False,
            details={"results": [r.model_dump() for r in results]},
        )

        return results

    async def handle_webhook(self, webhook: Bitrix24Webhook) -> CrmSyncResult:
        """Process incoming Bitrix24 webhook.

        When a lead/deal is updated in Bitrix24 manually, this syncs
        the changes back to AIM.
        """
        logger.info("CrmAgent: webhook event=%s entity=%s id=%s", webhook.event, webhook.entity_type, webhook.entity_id)

        if not webhook.entity_id:
            return CrmSyncResult(success=False, action="webhook", error="No entity ID in webhook")

        await self._log_activity(
            agent_type="crm_agent",
            action="webhook_received",
            details={
                "event": webhook.event,
                "entity_type": webhook.entity_type,
                "entity_id": webhook.entity_id,
            },
        )

        return CrmSyncResult(
            success=True,
            action="webhook",
            bitrix24_id=int(webhook.entity_id) if webhook.entity_id.isdigit() else None,
            details={"event": webhook.event, "entity_type": webhook.entity_type},
        )

    async def health_check(self) -> dict:
        """Check Bitrix24 connectivity."""
        if not self.enabled:
            return {"status": "disabled", "reason": "Bitrix24 not configured"}
        ok = await self._client.health_check()
        return {"status": "ok" if ok else "error", "bitrix24_connected": ok}

    async def close(self) -> None:
        if self._client:
            await self._client.close()
