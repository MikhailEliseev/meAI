"""Linear Integration Mixin for Magisters

Provides Linear task tracking capabilities to Magisters.
"""

from typing import Any, Optional

try:
    import sys
    from pathlib import Path
    scripts_path = Path(__file__).parent.parent.parent.parent.parent / "scripts"
    if str(scripts_path) not in sys.path:
        sys.path.insert(0, str(scripts_path))
    from linear_cli import LinearClient
    LINEAR_AVAILABLE = True
except ImportError:
    LINEAR_AVAILABLE = False
    LinearClient = None


class LinearMixin:
    """Mixin to add Linear integration to Magisters.

    Usage:
        class SEOMagisterV2(LinearMixin):
            def __init__(self, linear_client=None, linear_enabled=False):
                self.setup_linear(linear_client, linear_enabled)
    """

    def setup_linear(
        self,
        linear_client: Optional["LinearClient"] = None,
        linear_enabled: bool = False,
    ) -> None:
        self.linear_client = linear_client
        self.linear_enabled = linear_enabled and linear_client is not None
        self.linear_task_id: Optional[str] = None
        self.linear_team_id: Optional[str] = None

    def set_linear_task_id(self, task_id: str, team_id: str | None = None) -> None:
        self.linear_task_id = task_id
        if team_id:
            self.linear_team_id = team_id

    def sync_linear_from_message(self, payload: dict) -> None:
        """Extract Linear info from Operator's delegation message."""
        if not self.linear_enabled:
            return
        task_id = payload.get("linear_task_id")
        team_id = payload.get("linear_team_id")
        if task_id:
            self.set_linear_task_id(task_id, team_id)

    def update_linear_status(self, status: str) -> bool:
        """Update Linear task status via API.

        Args:
            status: "in_progress", "completed", or "failed"

        Returns:
            True if updated successfully
        """
        if not self.linear_enabled or not self.linear_task_id:
            return False
        if not self.linear_client:
            return False

        try:
            state_name = {
                "in_progress": "In Progress",
                "completed": "Done",
                "failed": "Canceled",
            }.get(status, "Todo")

            team_id = self.linear_team_id
            if not team_id:
                return False

            states = self.linear_client.list_states(team_id)
            state_id = None
            for s in states:
                if s.get("name") == state_name:
                    state_id = s.get("id")
                    break

            if not state_id:
                return False

            self.linear_client.update_issue(self.linear_task_id, state_id=state_id)
            return True
        except Exception:
            return False

    def add_linear_comment(self, comment: str) -> bool:
        """Add comment to Linear task.

        Args:
            comment: Comment text

        Returns:
            True if added successfully
        """
        if not self.linear_enabled or not self.linear_task_id or not self.linear_client:
            return False

        try:
            self.linear_client.add_comment(self.linear_task_id, comment)
            return True
        except Exception:
            return False

    def add_linear_progress_update(self, phase: str, status: str, details: str = "") -> bool:
        """Add progress update comment to Linear task.

        Args:
            phase: Phase name (e.g., "Keyword Research")
            status: Status (e.g., "completed", "in_progress", "failed")
            details: Optional details

        Returns:
            True if added successfully
        """
        if not self.linear_enabled:
            return False

        emoji_map = {
            "completed": "✅",
            "in_progress": "🔄",
            "failed": "❌",
            "started": "▶️",
        }

        emoji = emoji_map.get(status, "📝")
        comment = f"{emoji} **{phase}**: {status}"

        if details:
            comment += f"\n\n{details}"

        return self.add_linear_comment(comment)
