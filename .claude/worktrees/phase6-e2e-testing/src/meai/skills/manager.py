"""Claude skills manager for discovering and executing skills."""

import subprocess
from typing import Optional


class SkillsManager:
    """Manages Claude Code skills discovery and execution."""

    def __init__(self):
        self.available_skills = self._discover_skills()

    def _discover_skills(self) -> dict[str, str]:
        """Discover available Claude skills."""
        # This would parse the skills list from Claude Code
        # For now, return a static list of key skills
        return {
            "gsd-new-project": "Initialize new project with deep context",
            "gsd-plan-phase": "Create detailed phase plan",
            "gsd-execute-phase": "Execute phase plans",
            "deep-research": "Multi-source research with citations",
            "document-manager": "Document operations (PDF, DOCX, etc)",
            "git-master": "Expert Git operations",
            "superflow": "Full development workflow",
        }

    def execute_skill(self, skill_name: str, args: Optional[str] = None) -> dict:
        """Execute a Claude skill via CLI."""
        cmd = ["claude", "--skill", skill_name]
        if args:
            cmd.extend(args.split())

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Skill execution timed out",
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
            }

    def list_skills(self) -> list[str]:
        """List all available skills."""
        return list(self.available_skills.keys())

    def get_skill_info(self, skill_name: str) -> Optional[str]:
        """Get description of a skill."""
        return self.available_skills.get(skill_name)
