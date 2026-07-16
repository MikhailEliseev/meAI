"""
Agent Learning System - Learn from failures and apply lessons automatically

Provides mechanisms for agents to:
1. Record failures and successes
2. Read lessons learned from Obsidian
3. Apply prevention rules automatically
4. Track learning metrics
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json
import re


class AgentLearning:
    """
    Agent Learning System - enables agents to learn from past mistakes.

    Usage:
        learning = AgentLearning(agent_id="ci-deep-analyzer")

        # Before task
        lessons = await learning.get_lessons(tags=["validation", "ci-system"])
        rules = learning.extract_prevention_rules(lessons)

        # During task
        try:
            result = await agent.execute_task(task)
        except Exception as e:
            await learning.record_failure(task, e, context={...})

        # After task
        await learning.record_success(task, result, metrics={...})
    """

    def __init__(
        self,
        agent_id: str,
        lessons_path: str = "obsidian/architect/wiki/lessons",
        learning_data_path: str = "AIM/data/learning"
    ):
        self.agent_id = agent_id
        self.lessons_path = Path(lessons_path)
        self.learning_data_path = Path(learning_data_path)
        self.learning_data_path.mkdir(parents=True, exist_ok=True)

        # Load agent's learning history
        self.history_file = self.learning_data_path / f"{agent_id}_history.json"
        self.history = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        """Load agent's learning history from disk."""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "agent_id": self.agent_id,
            "created_at": datetime.now().isoformat(),
            "total_tasks": 0,
            "total_failures": 0,
            "total_successes": 0,
            "lessons_applied": [],
            "failures": [],
            "successes": []
        }

    def _save_history(self):
        """Save agent's learning history to disk."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    async def get_lessons(
        self,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        Get relevant lessons from Obsidian.

        Args:
            tags: Filter by tags (e.g., ["validation", "ci-system"])
            category: Filter by category (e.g., "bug", "architecture")
            severity: Filter by severity (e.g., "critical", "high")
            status: Filter by status (default: "active")

        Returns:
            List of lessons with metadata and content
        """
        lessons = []

        if not self.lessons_path.exists():
            return lessons

        # Read all lesson files
        for lesson_file in self.lessons_path.glob("*.md"):
            if lesson_file.name in ["TEMPLATE.md", "INDEX.md"]:
                continue

            lesson = self._parse_lesson_file(lesson_file)

            # Apply filters
            if status and lesson.get("status") != status:
                continue

            if category and lesson.get("category") != category:
                continue

            if severity and lesson.get("severity") != severity:
                continue

            if tags:
                lesson_tags = lesson.get("tags", [])
                if not any(tag in lesson_tags for tag in tags):
                    continue

            lessons.append(lesson)

        return lessons

    def _parse_lesson_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse lesson markdown file and extract metadata + content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        frontmatter = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                for line in frontmatter_text.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip().strip('"')

                        # Parse tags as list
                        if key == "tags":
                            value = [t.strip() for t in value.strip("[]").split(",")]

                        frontmatter[key] = value

                content = parts[2]

        # Extract prevention rules
        prevention_rules = self._extract_prevention_rules(content)

        return {
            "file": str(file_path),
            "title": frontmatter.get("title", ""),
            "date": frontmatter.get("date", ""),
            "category": frontmatter.get("category", ""),
            "severity": frontmatter.get("severity", ""),
            "tags": frontmatter.get("tags", []),
            "status": frontmatter.get("status", "active"),
            "prevention_rules": prevention_rules,
            "content": content
        }

    def _extract_prevention_rules(self, content: str) -> List[Dict[str, str]]:
        """Extract prevention rules from lesson content."""
        rules = []

        # Find "Prevention Rules" section
        match = re.search(
            r"## Prevention Rules.*?\n\n(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL
        )

        if not match:
            return rules

        rules_text = match.group(1)

        # Parse numbered rules
        rule_pattern = r"\d+\.\s+\*\*(ALWAYS|NEVER|CHECK):\*\*\s+(.*?)(?=\n\d+\.|\Z)"
        for match in re.finditer(rule_pattern, rules_text, re.DOTALL):
            rule_type = match.group(1)
            rule_text = match.group(2).strip()

            rules.append({
                "type": rule_type,
                "rule": rule_text
            })

        return rules

    def extract_prevention_rules(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract all prevention rules from lessons."""
        all_rules = []
        for lesson in lessons:
            all_rules.extend(lesson.get("prevention_rules", []))
        return all_rules

    async def record_failure(
        self,
        task: Any,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Record task failure for learning.

        Args:
            task: Task that failed
            error: Exception that occurred
            context: Additional context (e.g., input data, state)
        """
        failure = {
            "timestamp": datetime.now().isoformat(),
            "task_id": getattr(task, "task_id", "unknown"),
            "task_action": getattr(task, "action", "unknown"),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        self.history["total_tasks"] += 1
        self.history["total_failures"] += 1
        self.history["failures"].append(failure)

        # Keep only last 100 failures
        if len(self.history["failures"]) > 100:
            self.history["failures"] = self.history["failures"][-100:]

        self._save_history()

    async def record_success(
        self,
        task: Any,
        result: Any,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Record task success for learning.

        Args:
            task: Task that succeeded
            result: Task result
            metrics: Success metrics (e.g., quality_score, duration)
        """
        success = {
            "timestamp": datetime.now().isoformat(),
            "task_id": getattr(task, "task_id", "unknown"),
            "task_action": getattr(task, "action", "unknown"),
            "metrics": metrics or {}
        }

        self.history["total_tasks"] += 1
        self.history["total_successes"] += 1
        self.history["successes"].append(success)

        # Keep only last 100 successes
        if len(self.history["successes"]) > 100:
            self.history["successes"] = self.history["successes"][-100:]

        self._save_history()

    async def apply_lessons(
        self,
        task: Any,
        lessons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply lessons to current task.

        Returns:
            Dict with applied rules and recommendations
        """
        applied = {
            "lessons_count": len(lessons),
            "rules_applied": [],
            "recommendations": []
        }

        for lesson in lessons:
            # Track that this lesson was applied
            if lesson["title"] not in self.history["lessons_applied"]:
                self.history["lessons_applied"].append(lesson["title"])

            # Extract rules
            for rule in lesson.get("prevention_rules", []):
                applied["rules_applied"].append({
                    "lesson": lesson["title"],
                    "type": rule["type"],
                    "rule": rule["rule"]
                })

            # Add recommendations based on lesson
            if lesson.get("severity") == "critical":
                applied["recommendations"].append(
                    f"CRITICAL: {lesson['title']} - review prevention rules carefully"
                )

        self._save_history()
        return applied

    def get_failure_rate(self) -> float:
        """Calculate agent's failure rate."""
        total = self.history["total_tasks"]
        if total == 0:
            return 0.0
        return self.history["total_failures"] / total

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get agent's learning statistics."""
        return {
            "agent_id": self.agent_id,
            "total_tasks": self.history["total_tasks"],
            "total_failures": self.history["total_failures"],
            "total_successes": self.history["total_successes"],
            "failure_rate": self.get_failure_rate(),
            "lessons_applied_count": len(self.history["lessons_applied"]),
            "lessons_applied": self.history["lessons_applied"]
        }


# Example usage
async def example_usage():
    """Example of how agents should use the learning system."""

    # Initialize learning system
    learning = AgentLearning(agent_id="ci-deep-analyzer")

    # Before task: Get relevant lessons
    lessons = await learning.get_lessons(
        tags=["validation", "ci-system"],
        severity="critical"
    )

    print(f"Found {len(lessons)} relevant lessons")

    # Extract prevention rules
    rules = learning.extract_prevention_rules(lessons)
    print(f"Prevention rules to apply: {len(rules)}")

    for rule in rules:
        print(f"  {rule['type']}: {rule['rule'][:100]}...")

    # Apply lessons
    applied = await learning.apply_lessons(task=None, lessons=lessons)
    print(f"Applied {len(applied['rules_applied'])} rules")

    # During task: Record failure or success
    try:
        # ... execute task ...
        result = {"quality_score": 95.0}
        await learning.record_success(
            task=None,
            result=result,
            metrics={"quality_score": 95.0, "duration": 120.5}
        )
    except Exception as e:
        await learning.record_failure(
            task=None,
            error=e,
            context={"url": "https://example.com"}
        )

    # Get learning stats
    stats = learning.get_learning_stats()
    print(f"Learning stats: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
