#!/usr/bin/env python3
"""
Ask Architect - Simple wrapper for Claude Code integration

Usage in Claude Code:
    Just ask: "Architect, какую нишу выбрать первой?"

This script is called by Claude Code to get strategic decisions.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.core.architect import Architect, StrategicQuestion
import asyncio


async def ask(question: str) -> dict:
    """Ask Architect and return structured response."""

    architect = Architect()

    strategic_q = StrategicQuestion(
        goal=question,
        constraints=[],
        resources={},
        context={}
    )

    decision = await architect.make_decision(strategic_q)

    # Save to Obsidian
    await save_to_obsidian(question, decision)

    return {
        "action": decision.action,
        "rationale": decision.rationale,
        "confidence": decision.confidence,
        "alternatives": decision.alternatives,
        "risks": decision.risks,
    }


async def save_to_obsidian(question: str, decision):
    """Save decision to Obsidian."""
    from datetime import datetime, timezone

    vault_path = Path("obsidian/architect")
    decisions_dir = vault_path / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    filename = f"{timestamp}-decision.md"
    filepath = decisions_dir / filename

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
- **Saved to:** `{filepath.name}`

---

*This decision was made by Architect via Claude Code.*
"""

    filepath.write_text(content)
    print(f"\n✅ Decision saved to: {filepath.name}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ask_architect.py \"Your question\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    result = asyncio.run(ask(question))

    # Print formatted output
    print(f"\n💡 РЕШЕНИЕ ARCHITECT\n")
    print(f"{result['action']}\n")
    print(f"**Уверенность:** {result['confidence']:.0%}\n")
    print(f"**Обоснование:**\n{result['rationale']}\n")

    if result['alternatives']:
        print(f"**Альтернативы:**")
        for i, alt in enumerate(result['alternatives'], 1):
            print(f"{i}. {alt}")
        print()

    if result['risks']:
        print(f"**Риски:**")
        for risk in result['risks']:
            print(f"⚠️  {risk}")


if __name__ == "__main__":
    main()
