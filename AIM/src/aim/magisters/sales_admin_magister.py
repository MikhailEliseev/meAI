"""Sales Admin Agent — autonomous virtual clinic administrator 24/7.

Monitors communication channels, responds to patients, qualifies leads,
and escalates complex cases to human managers.

Architecture:
    TelegramMonitor → EventBus (sales.message.received)
                   → SalesAdminMagister.process_message()
                   → [qualification check + escalation check]
                   → Hermes (auto-reply) OR human escalation
                   → TelegramMonitor.send_message()

Part of Phase 13: AI Sales Admin Agent.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any

from aim.magisters.sales_admin_base import (
    DEFAULT_ESCALATION_RULES,
    ConversationStatus,
)
from aim.models.sales import (
    SalesAgentActivity,
    SalesConversation,
    SalesEscalation,
    SalesMessage,
)
from aim.services.sales.escalation_service import EscalationService
from aim.services.sales.qualification_service import QualificationService
from aim.subagents.sales.telegram_monitor import TelegramMonitor

logger = logging.getLogger(__name__)

# How often the magister polls EventBus for new messages (seconds)
POLL_INTERVAL_SECONDS = float(os.getenv("SALES_POLL_INTERVAL", "2.0"))


class SalesAdminMagister:
    """Autonomous sales administrator — monitors channels and responds 24/7.

    Capabilities:
    - monitor_channels: poll EventBus for incoming messages
    - qualify_lead: evaluate lead quality (Sub-Phase 2)
    - escalate_to_manager: escalate to human when needed
    - respond_to_patient: auto-reply via Hermes
    - sync_to_crm: push leads to Bitrix24 (Sub-Phase 4)
    """

    def __init__(self, event_bus=None, call_hermes=None) -> None:
        self._event_bus = event_bus
        self._call_hermes = call_hermes  # async callable: (mode, message, session_id) -> dict
        self._running = False
        self._monitors: dict[str, Any] = {}
        self._poll_task: asyncio.Task | None = None
        self._escalation = EscalationService()
        self._qualification = QualificationService()

    @staticmethod
    def _db():
        """Lazy import of async_session_maker — avoids triggering engine
        creation at module import time."""
        from aim.database import async_session_maker

        return async_session_maker

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self, event_bus) -> None:
        """Start the Sales Admin Magister.

        Args:
            event_bus: EventBus instance for pub/sub communication.
        """
        if self._running:
            return

        self._event_bus = event_bus

        # Initialise channel monitors
        self._monitors["telegram"] = TelegramMonitor(event_bus=event_bus)
        await self._monitors["telegram"].start()

        # Subscribe to incoming messages
        if self._event_bus:
            self._event_bus.subscribe("sales.message.received", self._on_message_received)
            self._event_bus.subscribe("sales.message.send", self._on_message_send)

        # Start background poll loop
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())

        logger.info("SalesAdminMagister started — monitoring channels")

    async def stop(self) -> None:
        """Stop the magister and all channel monitors."""
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        for monitor in self._monitors.values():
            await monitor.stop()
        self._monitors.clear()

        logger.info("SalesAdminMagister stopped")

    # ── Background poll loop ───────────────────────────────────────────────

    async def _poll_loop(self) -> None:
        """Poll EventBus for sales.message.received events.

        Events are delivered via subscriber callbacks (_on_message_received),
        but we also poll here as a fallback for messages that arrived before
        the subscriber was registered.
        """
        while self._running:
            try:
                if self._event_bus:
                    events = await self._event_bus.get_events(
                        event_type="sales.message.received",
                        status="pending",
                        limit=10,
                    )
                    for event in events:
                        await self._process_event(event)
                        await self._event_bus.mark_processed(str(event.id))
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in SalesAdminMagister poll loop")

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    # ── Event handlers ─────────────────────────────────────────────────────

    async def _on_message_received(self, event) -> None:
        """Subscriber callback for sales.message.received events."""
        await self._process_event(event)

    async def _on_message_send(self, event) -> None:
        """Subscriber callback for sales.message.send — deliver response to channel."""
        payload = event.payload if hasattr(event, "payload") else event.get("payload", {})
        channel = payload.get("channel", "telegram")
        channel_user_id = str(payload.get("channel_user_id", ""))
        text = payload.get("text", "")

        monitor = self._monitors.get(channel)
        if monitor and channel_user_id and text:
            ok = await monitor.send_message(channel_user_id, text)
            if ok:
                logger.info(f"Response delivered via {channel} to {channel_user_id}")
            else:
                logger.error(f"Failed to deliver response via {channel}")

    # ── Core message processing ────────────────────────────────────────────

    async def _process_event(self, event) -> None:
        """Process a sales.message.received event through the full pipeline."""
        payload = event.payload if hasattr(event, "payload") else {}

        channel = payload.get("channel", "telegram")
        channel_user_id = str(payload.get("channel_user_id", ""))
        text = (payload.get("text") or "").strip()
        metadata = payload.get("metadata", {})

        if not text or not channel_user_id:
            return

        t_start = datetime.now(timezone.utc)

        # 1. Find or create conversation
        conv = await self._get_or_create_conversation(
            channel=channel,
            channel_user_id=channel_user_id,
        )

        # 2. Store incoming message
        await self._store_message(
            conversation_id=conv.id,
            direction="incoming",
            content=text,
            sender_id=channel_user_id,
            ai_generated=False,
        )

        # 3. Check escalation triggers
        escalation = await self._check_escalation(conv, text)
        if escalation:
            await self._handle_escalation(conv, escalation, text)
            await self._log_activity(
                agent_type="sales_admin",
                action="escalated",
                conversation_id=conv.id,
                details={"reason": escalation["reason"], "severity": escalation["severity"]},
                success=True,
            )
            return

        # 4. Auto-reply via Hermes
        reply = await self._call_hermes_sales(conv, text)
        if reply:
            await self._store_message(
                conversation_id=conv.id,
                direction="outgoing",
                content=reply,
                ai_generated=True,
            )
            # Publish send event for channel monitor to deliver
            await self._publish_send(channel, channel_user_id, reply)

        # 5. Update conversation
        await self._touch_conversation(conv.id)

        # 6. Qualify lead (async, non-blocking)
        await self._qualify_conversation(conv)

        duration_ms = int((datetime.now(timezone.utc) - t_start).total_seconds() * 1000)
        await self._log_activity(
            agent_type="sales_admin",
            action="auto_reply",
            conversation_id=conv.id,
            duration_ms=duration_ms,
            success=True,
        )

    # ── Conversation management ─────────────────────────────────────────────

    async def _get_or_create_conversation(
        self, channel: str, channel_user_id: str
    ) -> SalesConversation:
        """Find existing active conversation or create a new one."""
        async with self._db()() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(SalesConversation).where(
                    SalesConversation.channel == channel,
                    SalesConversation.channel_user_id == channel_user_id,
                    SalesConversation.status == ConversationStatus.active.value,
                )
            )
            conv = result.scalar_one_or_none()
            if conv:
                return conv

            conv = SalesConversation(
                channel=channel,
                channel_user_id=channel_user_id,
                status=ConversationStatus.active.value,
            )
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
            logger.info(f"New conversation: {conv.id} ({channel}/{channel_user_id})")
            return conv

    async def _touch_conversation(self, conversation_id: str) -> None:
        """Update last_message_at and increment messages_count."""
        async with self._db()() as session:
            from sqlalchemy import update

            await session.execute(
                update(SalesConversation)
                .where(SalesConversation.id == conversation_id)
                .values(
                    last_message_at=datetime.now(timezone.utc),
                    messages_count=SalesConversation.messages_count + 1,
                )
            )
            await session.commit()

    # ── Message persistence ─────────────────────────────────────────────────

    async def _store_message(
        self,
        conversation_id: str,
        direction: str,
        content: str,
        sender_id: str | None = None,
        ai_generated: bool = False,
    ) -> SalesMessage:
        """Persist a message to the database."""
        async with self._db()() as session:
            msg = SalesMessage(
                conversation_id=conversation_id,
                direction=direction,
                content=content,
                sender_id=sender_id,
                ai_generated=ai_generated,
            )
            session.add(msg)
            await session.commit()
            await session.refresh(msg)
            return msg

    # ── Escalation (Sub-Phase 1 — keyword-based, expanded in Sub-Phase 2) ──

    async def _check_escalation(
        self, conv: SalesConversation, text: str
    ) -> dict | None:
        """Check if the message triggers any escalation rules.

        Uses the multi-layered EscalationService (5 categories, regex patterns)
        with fallback to DEFAULT_ESCALATION_RULES keyword matching.
        """
        # Primary: EscalationService with 5 categories + regex patterns
        result = await self._escalation.check(
            text=text,
            conversation_messages=None,
            conversation_errors=0,
        )
        if result:
            return {
                "reason": result.reason,
                "severity": result.severity,
                "auto_escalate": result.auto_escalate,
                "response_template": result.response_template,
                "matched_keyword": result.matched_trigger,
                "context": result.context,
            }

        # Fallback: DEFAULT_ESCALATION_RULES keyword matching
        text_lower = text.lower()
        for rule in DEFAULT_ESCALATION_RULES:
            for keyword in rule.trigger_keywords:
                if keyword.lower() in text_lower:
                    return {
                        "reason": rule.reason.value,
                        "severity": rule.severity.value,
                        "auto_escalate": rule.auto_escalate,
                        "response_template": rule.response_template,
                        "matched_keyword": keyword,
                        "context": {},
                    }
        return None

    async def _handle_escalation(
        self, conv: SalesConversation, escalation: dict, trigger_text: str
    ) -> None:
        """Process an escalation — store record, notify, send template response."""
        context_snapshot = {
            "trigger_text": trigger_text[:500],
            "matched_keyword": escalation.get("matched_keyword", ""),
            "messages_count": conv.messages_count,
        }
        if escalation.get("context"):
            context_snapshot.update(escalation["context"])

        async with self._db()() as session:
            esc = SalesEscalation(
                conversation_id=conv.id,
                reason=escalation["reason"],
                severity=escalation["severity"],
                context_snapshot=context_snapshot,
            )
            session.add(esc)

            # Update conversation status
            conv.status = ConversationStatus.escalated.value
            conv.escalation_count = (conv.escalation_count or 0) + 1
            session.add(conv)
            await session.commit()

        # Send template response to patient
        template = escalation.get("response_template")
        if template:
            await self._store_message(
                conversation_id=conv.id,
                direction="outgoing",
                content=template,
                ai_generated=True,
            )
            await self._publish_send("telegram", conv.channel_user_id, template)

        # Notify human manager
        await self._notify_manager(conv, escalation)

        logger.warning(
            f"Escalation: conv={conv.id} reason={escalation['reason']} "
            f"severity={escalation['severity']}"
        )

    async def _qualify_conversation(self, conv: SalesConversation) -> None:
        """Run qualification on the conversation and persist the result.

        Only qualifies every 3rd message to avoid unnecessary LLM calls.
        """
        if conv.messages_count % 3 != 0:
            return

        try:
            async with self._db()() as session:
                from sqlalchemy import select

                result = await session.execute(
                    select(SalesMessage)
                    .where(SalesMessage.conversation_id == conv.id)
                    .order_by(SalesMessage.created_at.desc())
                    .limit(10)
                )
                messages = result.scalars().all()
                message_texts = [m.content for m in reversed(messages)]

            if len(message_texts) < 2:
                return

            qual = await self._qualification.qualify(
                messages=message_texts,
                config=None,
                specialty=None,
            )

            async with self._db()() as session:
                conv.qualification_result = {
                    "score": qual.score,
                    "tier": qual.tier,
                    "recommended_action": qual.recommended_action,
                    "signals": qual.signals,
                    "concerns": qual.concerns,
                    "urgency": qual.urgency,
                    "specialty_match": qual.specialty_match,
                    "budget_indicated": qual.budget_indicated,
                    "reasoning": qual.reasoning,
                    "qualified_at": qual.qualified_at.isoformat(),
                }
                session.add(conv)
                await session.commit()

            logger.info(
                f"Qualification: conv={conv.id} score={qual.score} "
                f"tier={qual.tier} action={qual.recommended_action}"
            )
        except Exception:
            logger.exception("Qualification failed for conversation %s", conv.id)

    async def _notify_manager(
        self, conv: SalesConversation, escalation: dict
    ) -> None:
        """Send escalation notification to the human manager via Telegram."""
        manager_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
        if not manager_chat_id:
            logger.warning("TELEGRAM_ADMIN_CHAT_ID not set — cannot notify manager")
            return

        message = (
            f"🚨 <b>Эскалация #{conv.escalation_count}</b>\n"
            f"Причина: <b>{escalation['reason']}</b>\n"
            f"Серьёзность: <b>{escalation['severity']}</b>\n"
            f"Канал: {conv.channel}\n"
            f"Диалог: <code>{conv.id}</code>\n"
            f"Сообщений: {conv.messages_count}\n"
        )
        await self._publish_send("telegram", manager_chat_id, message)

    # ── Hermes integration ─────────────────────────────────────────────────

    async def _call_hermes_sales(self, conv: SalesConversation, user_message: str) -> str:
        """Call Hermes AIAgent in PRESALE mode for auto-reply.

        Uses the injected call_hermes callable so this module stays decoupled
        from the hermes package (which lives outside PYTHONPATH).
        """
        if self._call_hermes is None:
            logger.error("call_hermes not injected — cannot auto-reply")
            return "Извините, произошла техническая ошибка. Администратор свяжется с вами."

        try:
            result = await self._call_hermes(
                mode="PRESALE",
                message=user_message,
                session_id=f"sales:{conv.id}",
            )
            reply = result.get("reply", "") if isinstance(result, dict) else str(result)
            if isinstance(reply, dict):
                reply = reply.get("response", reply.get("content", str(reply)))
            return str(reply)
        except Exception:
            logger.exception("Hermes call failed for conversation %s", conv.id)
            return (
                "Извините, я сейчас не могу обработать ваш запрос. "
                "Пожалуйста, подождите немного, и администратор свяжется с вами."
            )

    # ── Event publishing helpers ───────────────────────────────────────────

    async def _publish_send(self, channel: str, channel_user_id: str, text: str) -> None:
        """Publish a sales.message.send event for the channel monitor."""
        if not self._event_bus:
            return

        from meai.events.event_bus import Event

        event = Event(
            event_type="sales.message.send",
            payload={
                "channel": channel,
                "channel_user_id": channel_user_id,
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        await self._event_bus.publish(event)

    # ── Activity log ───────────────────────────────────────────────────────

    async def _log_activity(
        self,
        agent_type: str,
        action: str,
        conversation_id: str | None = None,
        lead_id: str | None = None,
        details: dict | None = None,
        duration_ms: int | None = None,
        success: bool | None = None,
        error_message: str | None = None,
    ) -> None:
        """Write an immutable entry to the sales_agent_activity log."""
        async with self._db()() as session:
            entry = SalesAgentActivity(
                agent_type=agent_type,
                action=action,
                conversation_id=conversation_id,
                lead_id=lead_id,
                details=details,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
            )
            session.add(entry)
            await session.commit()

    # ── Capabilities (for Operator discovery) ───────────────────────────────

    def get_capabilities(self) -> list[str]:
        return [
            "monitor_channels",
            "qualify_lead",
            "escalate_to_manager",
            "respond_to_patient",
            "sync_to_crm",
        ]
