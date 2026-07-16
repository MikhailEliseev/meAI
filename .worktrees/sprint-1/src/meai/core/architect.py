"""
Architect - Strategic Decision Maker

The Architect is the strategic layer that makes high-level decisions
for the AIM Agency system.
"""

import os
import uuid
import subprocess
import tempfile
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

from meai.core.architect_critic import ArchitectCritic, CritiqueVerdict


@dataclass
class StrategicQuestion:
    """A strategic question for the Architect."""
    goal: str
    constraints: list[str] = field(default_factory=list)
    resources: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategicDecision:
    """A strategic decision made by the Architect."""
    decision_id: str
    action: str
    rationale: str
    confidence: float
    alternatives: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Architect:
    """
    Strategic decision maker for the AIM Agency.

    The Architect analyzes strategic questions and provides
    well-reasoned decisions with alternatives and risk assessment.

    Now includes Critic integration for decision validation.
    """

    def __init__(self, db=None, enable_critic: bool = True, obsidian_path: str = "./obsidian"):
        """Initialize Architect.

        Args:
            db: Database connection
            enable_critic: Enable Critic validation (default: True)
            obsidian_path: Path to Obsidian vault
        """
        self.db = db
        self.enable_critic = enable_critic
        self.critic = ArchitectCritic(obsidian_path) if enable_critic else None

    async def make_decision(self, question: StrategicQuestion, max_revisions: int = 2) -> StrategicDecision:
        """
        Make a strategic decision based on the question.

        Now includes Critic validation loop:
        1. Generate initial decision
        2. Critic reviews decision
        3. If CHALLENGE → revise and retry (up to max_revisions)
        4. If APPROVE → return decision
        5. If REJECT → generate new decision

        Args:
            question: The strategic question to answer
            max_revisions: Maximum number of revisions (default: 2)

        Returns:
            StrategicDecision with action, rationale, and alternatives
        """

        revision_count = 0
        critique_history = []

        while revision_count <= max_revisions:
            # Build prompt for Claude
            prompt = self._build_prompt(question, critique_history)

            # Get decision from Claude via subprocess
            response_text = await self._call_claude(prompt)

            # Parse response
            decision = self._parse_response(response_text)

            # If Critic is disabled, return immediately
            if not self.enable_critic:
                if self.db:
                    await self._save_decision(question, decision)
                return decision

            # Critic reviews decision
            decision_dict = {
                "decision_id": decision.decision_id,
                "action": decision.action,
                "rationale": decision.rationale,
                "confidence": decision.confidence,
                "alternatives": decision.alternatives,
                "risks": decision.risks,
            }

            critique = await self.critic.critique_decision(decision_dict)
            critique_history.append(critique)

            # Handle verdict
            if critique.verdict == CritiqueVerdict.APPROVE:
                # Decision approved!
                if self.db:
                    await self._save_decision(question, decision, critique)
                return decision

            elif critique.verdict == CritiqueVerdict.REJECT:
                # Decision rejected - start over
                revision_count = 0
                critique_history = [critique]  # Keep only rejection critique
                continue

            else:  # CHALLENGE
                # Decision challenged - revise
                revision_count += 1
                if revision_count > max_revisions:
                    # Max revisions reached - return best effort
                    if self.db:
                        await self._save_decision(question, decision, critique)
                    return decision
                # Continue loop to revise

        # Should not reach here, but return last decision
        if self.db:
            await self._save_decision(question, decision, critique_history[-1] if critique_history else None)
        return decision

    def _build_prompt(self, question: StrategicQuestion, critique_history: list = None) -> str:
        """Build prompt for Claude.

        Args:
            question: Strategic question
            critique_history: Previous critiques (for revisions)
        """

        prompt = f"""You are the Architect - a strategic advisor for an AI-first medical marketing agency (AIM Agency at iamaim.ru).

Your role is to make strategic decisions that guide the agency's development and operations.

## Strategic Question
{question.goal}

## Context
"""

        if question.constraints:
            prompt += "\n### Constraints\n"
            for constraint in question.constraints:
                prompt += f"- {constraint}\n"

        if question.resources:
            prompt += "\n### Available Resources\n"
            for key, value in question.resources.items():
                prompt += f"- {key}: {value}\n"

        if question.context:
            prompt += "\n### Additional Context\n"
            for key, value in question.context.items():
                prompt += f"- {key}: {value}\n"

        # Add critique history if this is a revision
        if critique_history:
            prompt += "\n## Previous Critique\n"
            latest_critique = critique_history[-1]
            prompt += f"Your previous decision was **{latest_critique.verdict.value.upper()}**.\n\n"

            if latest_critique.key_concerns:
                prompt += "### Key Concerns:\n"
                for concern in latest_critique.key_concerns:
                    prompt += f"- {concern}\n"

            if latest_critique.recommendations:
                prompt += "\n### Recommendations:\n"
                for rec in latest_critique.recommendations:
                    prompt += f"- {rec}\n"

            prompt += "\nPlease revise your decision addressing these concerns.\n"

        prompt += """

## Your Task

Analyze this strategic question and provide:

1. **Recommended Action** - What should we do? (1-2 sentences)
2. **Rationale** - Why is this the best approach? (2-3 paragraphs)
3. **Confidence** - How confident are you? (0.0 to 1.0)
4. **Alternatives** - What other options did you consider? (2-3 alternatives)
5. **Risks** - What could go wrong? (2-3 key risks)

Format your response as:

ACTION:
[Your recommended action]

RATIONALE:
[Your detailed reasoning]

CONFIDENCE:
[0.0 to 1.0]

ALTERNATIVES:
1. [Alternative 1]
2. [Alternative 2]
3. [Alternative 3]

RISKS:
- [Risk 1]
- [Risk 2]
- [Risk 3]
"""

        return prompt

    def _parse_response(self, text: str) -> StrategicDecision:
        """Parse Claude's response into a StrategicDecision."""

        lines = text.strip().split('\n')

        action = ""
        rationale = ""
        confidence = 0.7
        alternatives = []
        risks = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("ACTION:"):
                current_section = "action"
                continue
            elif line.startswith("RATIONALE:"):
                current_section = "rationale"
                continue
            elif line.startswith("CONFIDENCE:"):
                current_section = "confidence"
                continue
            elif line.startswith("ALTERNATIVES:"):
                current_section = "alternatives"
                continue
            elif line.startswith("RISKS:"):
                current_section = "risks"
                continue

            if not line:
                continue

            if current_section == "action":
                action += line + " "
            elif current_section == "rationale":
                rationale += line + " "
            elif current_section == "confidence":
                try:
                    confidence = float(line)
                except ValueError:
                    confidence = 0.7
            elif current_section == "alternatives":
                if line.startswith(("1.", "2.", "3.", "-", "•")):
                    alternatives.append(line[2:].strip())
            elif current_section == "risks":
                if line.startswith(("-", "•")):
                    risks.append(line[1:].strip())

        return StrategicDecision(
            decision_id=str(uuid.uuid4()),
            action=action.strip(),
            rationale=rationale.strip(),
            confidence=confidence,
            alternatives=alternatives,
            risks=risks
        )

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude via subprocess (using system Claude)."""

        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            temp_file = f.name

        try:
            # Call Claude via echo and pipe
            result = subprocess.run(
                f'echo "{prompt}" | claude',
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise RuntimeError(f"Claude call failed: {result.stderr}")

            return result.stdout.strip()

        finally:
            # Cleanup
            Path(temp_file).unlink(missing_ok=True)

    async def _save_decision(self, question: StrategicQuestion, decision: StrategicDecision, critique=None):
        """Save decision to database.

        Args:
            question: Strategic question
            decision: Strategic decision
            critique: Optional critique result
        """
        # TODO: Implement database storage with critique
        pass
