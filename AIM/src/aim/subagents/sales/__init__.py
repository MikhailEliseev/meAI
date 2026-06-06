"""Sales Admin Agent — channel monitors and subagents.

Part of Phase 13: AI Sales Admin Agent.
"""

from src.aim.subagents.sales.channel_monitor_base import BaseChannelMonitor, ChannelMessage
from src.aim.subagents.sales.crm_agent import CrmAgent
from src.aim.subagents.sales.knowledge_manager import KnowledgeManager, knowledge_manager
from src.aim.subagents.sales.telegram_monitor import TelegramMonitor

__all__ = [
    "BaseChannelMonitor",
    "ChannelMessage",
    "CrmAgent",
    "KnowledgeManager",
    "knowledge_manager",
    "TelegramMonitor",
]
