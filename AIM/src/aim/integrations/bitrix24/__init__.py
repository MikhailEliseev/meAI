"""Bitrix24 CRM Integration.

Uses fast_bitrix24 library for REST API calls, with additional resilience
patterns: circuit breaker, exponential backoff, structured logging.
"""

from src.aim.integrations.bitrix24.schemas import Bitrix24Contact, Bitrix24Deal, Bitrix24Lead
from src.aim.integrations.bitrix24.client import Bitrix24Client

__all__ = ["Bitrix24Client", "Bitrix24Lead", "Bitrix24Contact", "Bitrix24Deal"]
