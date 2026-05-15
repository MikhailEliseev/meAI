#!/usr/bin/env python3
"""
Setup Linear structure for AIM Agency.

Creates:
- 6 Teams (AIM Development, AIM Marketing, SEO, Content, Ads, Analytics)
- Project #0: AIM Development
- Project #0.1: AIM Marketing
- Labels (priority, type, domain)
- Initial tasks for Milestone 1-3
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.linear_cli import LinearClient


async def setup_teams(client: LinearClient) -> dict[str, str]:
    """Get existing teams and return team_id mapping."""
    print("\n=== Loading Existing Teams ===\n")

    teams = client.list_teams()
    team_mapping = {}

    for team in teams:
        team_mapping[team["key"]] = team["id"]
        print(f"  ✅ Found: {team['name']} ({team['key']}) - ID: {team['id']}")

    return team_mapping


async def setup_labels(client: LinearClient, team_id: str) -> dict[str, str]:
    """Create labels and return label_id mapping."""
    print("\n=== Creating Labels ===\n")

    labels_config = [
        # Priority
        {"name": "P0 - Critical", "color": "#FF0000", "description": "Blocks production"},
        {"name": "P1 - High", "color": "#FF8800", "description": "Important for milestone"},
        {"name": "P2 - Medium", "color": "#FFFF00", "description": "Nice to have"},
        {"name": "P3 - Low", "color": "#00FF00", "description": "Future enhancement"},
        # Type
        {"name": "bug", "color": "#D73A4A", "description": "Bug fix"},
        {"name": "feature", "color": "#0E8A16", "description": "New feature"},
        {"name": "docs", "color": "#0075CA", "description": "Documentation"},
        {"name": "test", "color": "#FBCA04", "description": "Testing"},
        {"name": "refactor", "color": "#5319E7", "description": "Code refactoring"},
        {"name": "deploy", "color": "#B60205", "description": "Deployment"},
        {"name": "design", "color": "#D876E3", "description": "UI/UX design"},
        # Domain
        {"name": "seo", "color": "#8B00FF", "description": "SEO related"},
        {"name": "content", "color": "#FF00FF", "description": "Content related"},
        {"name": "ads", "color": "#FF6600", "description": "Advertising related"},
        {"name": "analytics", "color": "#0099FF", "description": "Analytics related"},
        {"name": "infrastructure", "color": "#666666", "description": "Infrastructure"},
        {"name": "automation", "color": "#00CCCC", "description": "Automation"},
    ]

    label_mapping = {}

    for label_config in labels_config:
        print(f"Creating label: {label_config['name']}...")

        mutation = """
        mutation CreateLabel($teamId: String!, $name: String!, $color: String!, $description: String) {
          issueLabelCreate(input: {
            teamId: $teamId
            name: $name
            color: $color
            description: $description
          }) {
            success
            issueLabel {
              id
              name
            }
          }
        }
        """

        variables = {
            "teamId": team_id,
            "name": label_config["name"],
            "color": label_config["color"],
            "description": label_config["description"],
        }

        try:
            result = await client._execute_query(mutation, variables)
            if result.get("issueLabelCreate", {}).get("success"):
                label = result["issueLabelCreate"]["issueLabel"]
                label_mapping[label_config["name"]] = label["id"]
                print(f"  ✅ Created: {label['name']}")
            else:
                print(f"  ❌ Failed to create label: {label_config['name']}")
        except Exception as e:
            error_msg = str(e)
            if "duplicate label name" in error_msg or "already exists" in error_msg:
                print(f"  ⏭️  Skipped (already exists): {label_config['name']}")
            else:
                print(f"  ❌ Error creating label {label_config['name']}: {e}")

    return label_mapping


async def create_project(
    client: LinearClient,
    team_id: str,
    name: str,
    description: str,
) -> str | None:
    """Create project and return project_id."""
    print(f"\nCreating project: {name}...")

    mutation = """
    mutation CreateProject($teamIds: [String!]!, $name: String!, $description: String) {
      projectCreate(input: {
        teamIds: $teamIds
        name: $name
        description: $description
      }) {
        success
        project {
          id
          name
        }
      }
    }
    """

    variables = {
        "teamIds": [team_id],
        "name": name,
        "description": description,
    }

    try:
        result = await client._execute_query(mutation, variables)
        if result.get("projectCreate", {}).get("success"):
            project = result["projectCreate"]["project"]
            print(f"  ✅ Created: {project['name']} (ID: {project['id']})")
            return project["id"]
        else:
            print(f"  ❌ Failed to create project: {name}")
            return None
    except Exception as e:
        print(f"  ❌ Error creating project {name}: {e}")
        return None


async def create_milestone_tasks(
    client: LinearClient,
    team_id: str,
    project_id: str,
    label_mapping: dict[str, str],
) -> None:
    """Create tasks for Milestone 1-3."""
    print("\n=== Creating Milestone Tasks ===\n")

    # Get workflow states
    states = client.list_states(team_id)
    done_state = next((s for s in states if s["type"] == "completed"), None)
    todo_state = next((s for s in states if s["type"] == "unstarted"), None)

    if not done_state or not todo_state:
        print("  ❌ Could not find workflow states")
        return

    # Get feature label ID (if exists)
    feature_label_id = label_mapping.get("feature", "")
    label_ids = [feature_label_id] if feature_label_id else []

    # Milestone 1 tasks (retrospective - mark as Done)
    milestone_1_tasks = [
        "Foundation - Base classes and infrastructure",
        "Event Flow - Async coordination",
        "API Integration - Real API clients",
        "Magister Tests - Production orchestrators",
        "Subagent Tests - P1 subagents training",
        "E2E Tests - Multi-agent coordination",
        "Production Deployment - SSL/TLS and monitoring",
    ]

    print("Milestone 1 (Retrospective):")
    for i, title in enumerate(milestone_1_tasks, 1):
        issue_id = client.create_issue(
            title=f"DEV-{i}: {title}",
            description=f"Phase {i} of Milestone 1: Core Infrastructure",
            team_id=team_id,
            project_id=project_id,
            state_id=done_state["id"],
            priority=2,  # High
            label_ids=label_ids,
        )
        if issue_id:
            print(f"  ✅ Created: DEV-{i}")

    # Milestone 2 tasks (current)
    milestone_2_tasks = [
        ("Linear CLI Integration", "✅ COMPLETED"),
        ("Linear Structure Setup", "🔄 IN PROGRESS"),
        ("Operator ↔ Linear Integration", "⏳ TODO"),
        ("Client Dashboard in Linear", "⏳ TODO"),
        ("Multi-Tenant Frontend", "⏳ TODO"),
    ]

    print("\nMilestone 2 (Current):")
    for i, (title, status) in enumerate(milestone_2_tasks, 8):
        state_id = done_state["id"] if "COMPLETED" in status else todo_state["id"]
        issue_id = client.create_issue(
            title=f"DEV-{i}: {title}",
            description=f"Phase {i} of Milestone 2: Project Management\nStatus: {status}",
            team_id=team_id,
            project_id=project_id,
            state_id=state_id,
            priority=2,  # High
            label_ids=label_ids,
        )
        if issue_id:
            print(f"  ✅ Created: DEV-{i}")

    # Milestone 3 tasks (future)
    milestone_3_tasks = [
        "Marketing Automation",
        "First Client Onboarding",
    ]

    print("\nMilestone 3 (Future):")
    for i, title in enumerate(milestone_3_tasks, 13):
        issue_id = client.create_issue(
            title=f"DEV-{i}: {title}",
            description=f"Phase {i} of Milestone 3: Client Acquisition",
            team_id=team_id,
            project_id=project_id,
            state_id=todo_state["id"],
            priority=3,  # Medium
            label_ids=label_ids,
        )
        if issue_id:
            print(f"  ✅ Created: DEV-{i}")


async def create_marketing_tasks(
    client: LinearClient,
    team_id: str,
    project_id: str,
    label_mapping: dict[str, str],
) -> None:
    """Create tasks for AIM Marketing project."""
    print("\n=== Creating Marketing Tasks ===\n")

    # Get workflow states
    states = client.list_states(team_id)
    todo_state = next((s for s in states if s["type"] == "unstarted"), None)

    if not todo_state:
        print("  ❌ Could not find workflow states")
        return

    marketing_tasks = [
        ("Blog content plan", "content"),
        ("Case studies", "content"),
        ("Social media strategy", "content"),
        ("Keyword research for iamaim.ru", "seo"),
        ("Technical SEO audit", "seo"),
        ("Content optimization", "seo"),
        ("Yandex Direct campaign", "ads"),
        ("Google Ads campaign", "ads"),
    ]

    for i, (title, domain) in enumerate(marketing_tasks, 1):
        # Get domain label ID
        domain_label_id = label_mapping.get(domain, "")
        label_ids = [domain_label_id] if domain_label_id else []

        issue_id = client.create_issue(
            title=f"MKT-{i}: {title}",
            description=f"Marketing task for AIM self-promotion",
            team_id=team_id,
            project_id=project_id,
            state_id=todo_state["id"],
            priority=3,  # Medium
            label_ids=label_ids,
        )
        if issue_id:
            print(f"  ✅ Created: MKT-{i}")


async def main():
    """Main setup function."""
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        # Try to read from settings.json
        import json
        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                config = json.load(f)
                api_key = (
                    config.get("mcpServers", {})
                    .get("linear", {})
                    .get("env", {})
                    .get("LINEAR_API_KEY")
                )

    if not api_key:
        print("Error: LINEAR_API_KEY not found")
        print("Set it in ~/.claude/settings.json or as environment variable")
        return

    client = LinearClient(api_key)

    try:
        print("=" * 60)
        print("Setting up Linear structure for AIM Agency")
        print("=" * 60)

        # Step 1: Create teams
        team_mapping = await setup_teams(client)

        if not team_mapping:
            print("\n❌ Failed to create teams. Aborting.")
            return

        # Step 2: Create labels for DEV team
        dev_team_id = team_mapping.get("DEV")
        if dev_team_id:
            label_mapping = await setup_labels(client, dev_team_id)
        else:
            print("\n❌ DEV team not found. Skipping labels.")
            label_mapping = {}

        # Step 3: Create Project #0: AIM Development
        print("\n=== Creating Projects ===")
        dev_project_id = None
        if dev_team_id:
            dev_project_id = await create_project(
                client,
                dev_team_id,
                "AIM Development",
                "Building the AIM platform - Project #0 (сапожник с сапогами)",
            )

        # Step 4: Create Project #0.1: AIM Marketing
        mkt_team_id = team_mapping.get("MKT")
        mkt_project_id = None
        if mkt_team_id:
            mkt_project_id = await create_project(
                client,
                mkt_team_id,
                "AIM Marketing",
                "Promoting AIM to clients - Project #0.1",
            )

        # Step 5: Create milestone tasks for DEV project
        if dev_project_id and dev_team_id:
            await create_milestone_tasks(
                client,
                dev_team_id,
                dev_project_id,
                label_mapping,
            )

        # Step 6: Create marketing tasks for MKT project
        if mkt_project_id and mkt_team_id:
            # Create labels for MKT team
            mkt_label_mapping = await setup_labels(client, mkt_team_id)
            await create_marketing_tasks(
                client,
                mkt_team_id,
                mkt_project_id,
                mkt_label_mapping,
            )

        print("\n" + "=" * 60)
        print("✅ Linear structure setup complete!")
        print("=" * 60)
        print("\nCreated:")
        print(f"  - {len(team_mapping)} teams")
        print(f"  - {len(label_mapping)} labels")
        print(f"  - 2 projects (AIM Development, AIM Marketing)")
        print(f"  - 22 tasks (7 Milestone 1, 5 Milestone 2, 2 Milestone 3, 8 Marketing)")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
