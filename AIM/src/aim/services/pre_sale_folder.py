"""Pre-Sale folder service — manages per-lead pre-sale/ directory.

Creates and maintains the folder structure for competitor discovery sessions:
  pre-sale/
  ├── session.json              # Session metadata
  ├── full_chat_log.md          # Full chat transcript
  ├── competitors/
  │   ├── system_suggested.json # AI-suggested competitors
  │   ├── client_suggested.json # Client-provided competitors
  │   ├── approved_final.json   # Final agreed list
  │   └── research/
  │       └── {inn}.json        # Per-competitor deep profile
  └── decisions/
      └── approval_log.json     # Chronological log: shown → decision

Public API is fire-and-forget: methods never raise, only log warnings.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .rusprofile.models import CompetitorMatch

logger = logging.getLogger(__name__)

DEFAULT_LEADS_BASE = os.getenv("LEADS_BASE_DIR", "/opt/data/leads")


def _leads_base() -> Path:
    return Path(DEFAULT_LEADS_BASE)


class PreSaleFolder:
    """Manages the pre-sale/ folder for a single lead."""

    def __init__(self, lead_id: str):
        self.lead_id = lead_id
        self.base = _leads_base() / lead_id / "pre-sale"

    # ── Create ─────────────────────────────────────────────────────

    def ensure(self) -> None:
        """Create full pre-sale/ folder tree if it doesn't exist."""
        try:
            self.base.mkdir(parents=True, exist_ok=True)
            (self.base / "competitors" / "research").mkdir(parents=True, exist_ok=True)
            (self.base / "decisions").mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning("pre_sale: cannot create folder tree for %s: %s", self.lead_id, e)

    # ── Session ────────────────────────────────────────────────────

    def save_session(self, *, url: str, specialization: str = "",
                     city: str = "", services: list[str] | None = None,
                     company_name: str | None = None) -> None:
        """Save session metadata (created when pre-sale flow starts)."""
        self.ensure()
        record = {
            "lead_id": self.lead_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "client_url": url,
            "company_name": company_name,
            "specialization": specialization,
            "city": city,
            "services": services or [],
            "phase": "competitor_discovery",
        }
        self._write("session.json", record)

    def update_phase(self, phase: str) -> None:
        """Update the current phase of the session."""
        record = self._read("session.json") or {}
        record["phase"] = phase
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write("session.json", record)

    # ── Chat log ───────────────────────────────────────────────────

    def append_chat(self, role: str, text: str) -> None:
        """Append a message to full_chat_log.md."""
        self.ensure()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"**{ts} — {role}:** {text}\n\n"
        try:
            with open(self.base / "full_chat_log.md", "a", encoding="utf-8") as f:
                f.write(line)
        except OSError as e:
            logger.warning("pre_sale: cannot write chat log for %s: %s", self.lead_id, e)

    # ── Competitors ────────────────────────────────────────────────

    def save_system_suggested(self, competitors: list[CompetitorMatch]) -> None:
        """Save AI-suggested competitors."""
        self.ensure()
        self._write("competitors/system_suggested.json", {
            "suggested_at": datetime.now(timezone.utc).isoformat(),
            "competitors": [_match_to_dict(m) for m in competitors],
        })

    def save_client_suggested(self, urls: list[str]) -> None:
        """Save client-provided competitor URLs."""
        self.ensure()
        self._write("competitors/client_suggested.json", {
            "suggested_at": datetime.now(timezone.utc).isoformat(),
            "urls": urls,
        })

    def save_approved_final(self, competitors: list[CompetitorMatch]) -> None:
        """Save final approved competitor list."""
        self.ensure()
        self._write("competitors/approved_final.json", {
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "competitors": [_match_to_dict(m) for m in competitors],
        })

    def save_competitor_research(self, inn: str, profile: dict) -> None:
        """Save deep research profile for a single competitor."""
        self.ensure()
        self._write(f"competitors/research/{inn}.json", profile)

    # ── Decisions ──────────────────────────────────────────────────

    def log_approval_event(self, event: str, detail: dict | None = None) -> None:
        """Log an approval workflow event.

        Args:
            event: Event type, e.g. 'shown', 'client_approved', 'client_rejected',
                   'client_reroll', 'client_suggested_own', 'finalized'
            detail: Optional detail dict
        """
        self.ensure()
        log_path = self.base / "decisions" / "approval_log.json"
        entries: list = []
        try:
            if log_path.exists():
                entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

        entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "detail": detail or {},
        })
        self._write("decisions/approval_log.json", entries)

    # ── Helpers ────────────────────────────────────────────────────

    def _write(self, rel_path: str, data) -> None:
        path = self.base / rel_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning("pre_sale: cannot write %s for lead %s: %s",
                           rel_path, self.lead_id, e)

    def _read(self, rel_path: str) -> Optional[dict]:
        path = self.base / rel_path
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("pre_sale: cannot read %s for lead %s: %s",
                           rel_path, self.lead_id, e)
        return None


def _match_to_dict(m: CompetitorMatch) -> dict:
    """Convert CompetitorMatch to JSON-serializable dict."""
    p = m.profile
    return {
        "inn": p.inn,
        "legal_name": p.legal_name,
        "brand_name": p.brand_name,
        "revenue_year": p.revenue_year,
        "profit_year": p.profit_year,
        "revenue_trend": p.revenue_trend,
        "financial_year": p.financial_year,
        "employee_count": p.employee_count,
        "okved_main": p.okved_main,
        "okved_secondary": p.okved_secondary,
        "legal_address": p.legal_address,
        "actual_addresses": p.actual_addresses,
        "geo_lat": p.geo_lat,
        "geo_lon": p.geo_lon,
        "data_source": p.data_source,
        "confidence": p.confidence,
        "website": m.website,
        "services": m.services,
        "revenue_match": m.revenue_match,
        "location_score": m.location_score,
        "service_overlap": m.service_overlap,
        "data_quality": m.data_quality,
        "total_score": m.total_score,
        "match_reason": m.match_reason,
    }
