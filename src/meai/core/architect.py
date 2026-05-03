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
    """

    def __init__(self, db=None):
        """Initialize Architect."""
        self.db = db

    async def make_decision(self, question: StrategicQuestion) -> StrategicDecision:
        """
        Make a strategic decision based on the question.

        Args:
            question: The strategic question to answer

        Returns:
            StrategicDecision with action, rationale, and alternatives
        """

        # Build prompt for Claude
        prompt = self._build_prompt(question)

        # Get decision from Claude via subprocess
        response_text = await self._call_claude(prompt)

        # Parse response
        decision = self._parse_response(response_text)

        # Save to database if available
        if self.db:
            await self._save_decision(question, decision)

        return decision

    def _build_prompt(self, question: StrategicQuestion) -> str:
        """Build prompt for Claude."""

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

    async def _save_decision(self, question: StrategicQuestion, decision: StrategicDecision):
        """Save decision to database."""
        # TODO: Implement database storage
        pass
