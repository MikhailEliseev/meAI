#!/usr/bin/env python3
"""
Simple CLI to talk to Architect.

Usage:
    python scripts/talk_to_architect.py "Your strategic question here"

Example:
    python scripts/talk_to_architect.py "Should we launch iamaim.ru with MVP or full product?"
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.core.architect import Architect, StrategicQuestion
from meai.storage.database import Database


async def ask_architect(question: str):
    """Ask Architect a strategic question."""

    # Initialize (Architect doesn't need DB for now)
    architect = Architect()

    # Create strategic question
    strategic_q = StrategicQuestion(
        goal=question,
        constraints=[],
        resources={},
        context={}
    )

    print(f"\n{'='*60}")
    print(f"🤔 ASKING ARCHITECT")
    print(f"{'='*60}")
    print(f"\nQuestion: {question}\n")
    print("Thinking...\n")

    # Get decision
    decision = await architect.make_decision(strategic_q)

    # Display result
    print(f"{'='*60}")
    print(f"💡 ARCHITECT'S DECISION")
    print(f"{'='*60}\n")

    print(f"Action: {decision.action}\n")
    print(f"Rationale:\n{decision.rationale}\n")
    print(f"Confidence: {decision.confidence:.0%}\n")

    if decision.alternatives:
        print(f"Alternatives considered:")
        for i, alt in enumerate(decision.alternatives, 1):
            print(f"  {i}. {alt}")
        print()

    if decision.risks:
        print(f"Risks:")
        for risk in decision.risks:
            print(f"  ⚠️  {risk}")
        print()

    print(f"{'='*60}\n")

    # Save to Obsidian
    await save_to_obsidian(question, decision)

    return decision


async def save_to_obsidian(question: str, decision):
    """Save decision to Architect's vault."""

    vault_path = Path("obsidian/architect")
    decisions_dir = vault_path / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    # Create filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    filename = f"{timestamp}-decision.md"
    filepath = decisions_dir / filename

    # Create content
    content = f"""---
title: "Strategic Decision: {question[:50]}..."
type: strategic-decision
created: {datetime.now(timezone.utc).isoformat()}
confidence: {decision.confidence}
status: active
tags: [decision, strategic]
---

# Strategic Decision

## Question
{question}

## Decision
{decision.action}

## Rationale
{decision.rationale}

## Confidence
{decision.confidence:.0%}

## Alternatives Considered
"""

    if decision.alternatives:
        for i, alt in enumerate(decision.alternatives, 1):
            content += f"{i}. {alt}\n"
    else:
        content += "None\n"

    content += "\n## Risks\n"

    if decision.risks:
        for risk in decision.risks:
            content += f"- {risk}\n"
    else:
        content += "None identified\n"

    content += f"""
## Metadata
- **Decision ID:** {decision.decision_id}
- **Timestamp:** {decision.timestamp.isoformat()}
- **Saved to:** `{filepath.relative_to(vault_path)}`

---

*This decision was made by Architect and saved automatically.*
"""

    # Write file
    filepath.write_text(content)

    print(f"✅ Decision saved to: {filepath}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/talk_to_architect.py \"Your question here\"")
        print("\nExample:")
        print('  python scripts/talk_to_architect.py "Should we launch with MVP or full product?"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    asyncio.run(ask_architect(question))


if __name__ == "__main__":
    main()
