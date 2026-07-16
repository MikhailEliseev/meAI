"""Core assistant orchestration logic."""

from typing import Optional
from meai.memory.obsidian import ObsidianMemory
from meai.skills.manager import SkillsManager


class Assistant:
    """Main assistant orchestrator."""

    def __init__(self, vault_path: str = "./obsidian"):
        self.memory = ObsidianMemory(vault_path)
        self.skills = SkillsManager()

    async def process_request(self, request: str) -> dict:
        """Process a user request."""
        # Log to daily note
        daily_note = self.memory.create_daily_note()
        self.memory.append_to_note(daily_note, f"\n## Request: {request}\n")

        # Analyze request and determine action
        response = await self._analyze_and_act(request)

        # Save response to memory
        self.memory.append_to_note(daily_note, f"\n**Response:** {response['message']}\n")

        return response

    async def _analyze_and_act(self, request: str) -> dict:
        """Analyze request and take appropriate action."""
        # Simple keyword-based routing for now
        request_lower = request.lower()

        if "skill" in request_lower or "помощь" in request_lower:
            skills = self.skills.list_skills()
            return {
                "message": f"Available skills: {', '.join(skills)}",
                "action": "list_skills",
            }

        if "aim" in request_lower or "агентство" in request_lower:
            # Load AIM context
            aim_context = self.memory.read_note("AIM/context.md")
            return {
                "message": "Loading AIM agency context...",
                "context": aim_context,
                "action": "load_context",
            }

        return {
            "message": "Request received. How can I help?",
            "action": "general",
        }

    def save_learning(self, topic: str, content: str) -> None:
        """Save a learning to the vault."""
        self.memory.write_note(
            f"learnings/{topic}.md",
            content,
            frontmatter={"topic": topic, "type": "learning"},
        )

    def save_decision(self, title: str, content: str) -> None:
        """Save an architecture decision."""
        self.memory.write_note(
            f"decisions/{title}.md",
            content,
            frontmatter={"title": title, "type": "decision"},
        )
