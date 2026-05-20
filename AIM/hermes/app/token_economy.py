"""TokenEconomy — LLM cost controller for AI Sales chat.

Prevents budget overruns by gating expensive AI tiers behind lead quality
and enforcing per-lead spending caps.

Tiers:
  TIER 0 — Qualification (free, always allowed)
  TIER 1 — Basic audit (WARM leads, lead_score >= 40)
  TIER 2 — Deep audit (HOT leads, lead_score >= 70 + explicit consent)
  MAX    — $0.15 per lead (hard cap)
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LeadBudget:
    lead_id: str
    total_cost: float = 0.0
    tier_0_count: int = 0
    tier_1_count: int = 0
    tier_2_count: int = 0


class TokenEconomy:
    """Budget guard for AI Sales chat conversations.

    Usage:
        econ = TokenEconomy()
        if econ.can_run_tier("TIER_1", lead_score=55):
            econ.track_cost(lead_id, 0.015)
            # run the audit
    """

    TIER_0_MAX_COST = 0.003   # Qualification (Haiku)
    TIER_1_MAX_COST = 0.02    # Basic audit (Sonnet)
    TIER_2_MAX_COST = 0.12    # Deep audit (Opus)
    MAX_COST_PER_LEAD = 0.15  # Hard cap

    # Lead score thresholds
    WARM_THRESHOLD = 40  # TIER 1: lead_score >= 40
    HOT_THRESHOLD = 70   # TIER 2: lead_score >= 70

    def __init__(self):
        self._ledgers: dict[str, LeadBudget] = {}
        self._lock = threading.Lock()

    def can_run_tier(self, tier: str, lead_score: int, has_consent: bool = False) -> bool:
        """Check if a tier can run based on lead score and consent.

        Args:
            tier: "TIER_0", "TIER_1", or "TIER_2"
            lead_score: 0-100 lead score
            has_consent: explicit user consent for deep audit (TIER_2)

        Returns:
            True if the tier is allowed for this lead quality.
        """
        if tier == "TIER_0":
            return True  # Always free

        if tier == "TIER_1":
            return lead_score >= self.WARM_THRESHOLD

        if tier == "TIER_2":
            return lead_score >= self.HOT_THRESHOLD and has_consent

        logger.warning("Unknown tier: %s", tier)
        return False

    def get_remaining_budget(self, lead_id: str) -> float:
        """Return remaining budget for a lead."""
        with self._lock:
            ledger = self._ledgers.get(lead_id)
            if ledger is None:
                return self.MAX_COST_PER_LEAD
            return max(0.0, self.MAX_COST_PER_LEAD - ledger.total_cost)

    def track_cost(self, lead_id: str, amount: float) -> None:
        """Record token cost for a lead. Does NOT enforce budget — use can_run_tier first."""
        with self._lock:
            if lead_id not in self._ledgers:
                self._ledgers[lead_id] = LeadBudget(lead_id=lead_id)
            ledger = self._ledgers[lead_id]
            ledger.total_cost += amount

            # Classify which tier this cost belongs to (best-effort)
            if amount <= self.TIER_0_MAX_COST:
                ledger.tier_0_count += 1
            elif amount <= self.TIER_1_MAX_COST:
                ledger.tier_1_count += 1
            else:
                ledger.tier_2_count += 1

            logger.info(
                "Tracked $%.4f for lead %s (total: $%.4f, remaining: $%.4f)",
                amount, lead_id, ledger.total_cost,
                self.get_remaining_budget(lead_id),
            )

    def get_lead_cost(self, lead_id: str) -> float:
        """Return total cost for a lead."""
        with self._lock:
            ledger = self._ledgers.get(lead_id)
            return ledger.total_cost if ledger else 0.0

    def get_status(self, lead_id: str) -> dict:
        """Return full budget status for a lead."""
        with self._lock:
            ledger = self._ledgers.get(lead_id)
            if ledger is None:
                return {
                    "lead_id": lead_id,
                    "total_cost": 0.0,
                    "remaining": self.MAX_COST_PER_LEAD,
                    "tier_0_count": 0,
                    "tier_1_count": 0,
                    "tier_2_count": 0,
                    "max_budget": self.MAX_COST_PER_LEAD,
                }
            return {
                "lead_id": lead_id,
                "total_cost": round(ledger.total_cost, 4),
                "remaining": round(self.get_remaining_budget(lead_id), 4),
                "tier_0_count": ledger.tier_0_count,
                "tier_1_count": ledger.tier_1_count,
                "tier_2_count": ledger.tier_2_count,
                "max_budget": self.MAX_COST_PER_LEAD,
            }

    def reset_lead(self, lead_id: str) -> None:
        """Reset budget tracking for a lead (e.g., when lead becomes ACTIVE client)."""
        with self._lock:
            self._ledgers.pop(lead_id, None)
            logger.info("Reset budget for lead %s", lead_id)


# Global singleton for Hermes app
token_economy = TokenEconomy()
