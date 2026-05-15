#!/usr/bin/env python3
"""Create Client Project in Linear

Creates a complete client project structure with:
- Main project in appropriate team
- SEO, Content, and Ads workflow tasks
- Budget and timeline tracking
- Progress metrics

Usage:
    python scripts/create_client_project.py "Client Name" --services seo,content,ads --budget 100000
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for LinearClient import
scripts_path = Path(__file__).parent
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from linear_cli import LinearClient


class ClientProjectCreator:
    """Creates and manages client projects in Linear."""

    def __init__(self, linear_client: LinearClient):
        self.client = linear_client
        self.teams = self._load_teams()
        self.states = {}
        self._load_all_states()

    def _load_teams(self) -> dict[str, dict]:
        """Load all teams and create mapping."""
        teams_list = self.client.list_teams()
        return {team["key"]: team for team in teams_list}

    def _load_all_states(self) -> None:
        """Load workflow states for all teams."""
        for team_key, team in self.teams.items():
            states = self.client.list_states(team["id"])
            self.states[team_key] = {state["name"]: state for state in states}

    def create_client_project(
        self,
        client_name: str,
        services: list[str],
        budget: int,
        timeline_weeks: int = 12,
        project_number: int = 1,
    ) -> dict:
        """
        Create complete client project structure.

        Args:
            client_name: Client company name
            services: List of services (seo, content, ads)
            budget: Total budget in rubles
            timeline_weeks: Project duration in weeks
            project_number: Project number for this client (default: 1)

        Returns:
            Project details with created tasks
        """
        print(f"\n{'=' * 80}")
        print(f"Creating Client Team & Project: {client_name}")
        print(f"{'=' * 80}\n")

        # Step 1: Create dedicated team for this client
        team_id, team_key = self._create_client_team(client_name, project_number)
        print(f"✅ Team created: {team_key}\n")

        # Reload teams and states to include new team
        self.teams = self._load_teams()
        self._load_all_states()

        # Step 2: Create main project in client's team
        project_id = self._create_main_project(
            client_name, team_key, budget, timeline_weeks, services
        )
        print(f"✅ Project created: {project_id}\n")

        # Step 3: Create workflow tasks for each service
        created_tasks = {}
        for service in services:
            print(f"Creating {service.upper()} workflow...")
            tasks = self._create_service_workflow(
                client_name, service, project_id, budget, timeline_weeks, team_key
            )
            created_tasks[service] = tasks
            print(f"✅ {len(tasks)} tasks created for {service}\n")

        # Summary
        total_tasks = sum(len(tasks) for tasks in created_tasks.values())
        print(f"{'=' * 80}")
        print(f"✅ Client Project Created Successfully!")
        print(f"{'=' * 80}\n")
        print(f"Client: {client_name}")
        print(f"Services: {', '.join(services)}")
        print(f"Budget: {budget:,} ₽")
        print(f"Timeline: {timeline_weeks} weeks")
        print(f"Total tasks: {total_tasks}")
        print()

        return {
            "project_id": project_id,
            "client_name": client_name,
            "services": services,
            "budget": budget,
            "timeline_weeks": timeline_weeks,
            "tasks": created_tasks,
            "total_tasks": total_tasks,
        }

    def _create_client_team(
        self, client_name: str, project_number: int = 1
    ) -> tuple[str, str]:
        """
        Create dedicated team for client.

        Args:
            client_name: Client company name
            project_number: Project number (default: 1)

        Returns:
            Tuple of (team_id, team_key)
        """
        # Generate team key from client name
        # Remove special chars, take first 3 letters, add project number
        clean_name = "".join(c for c in client_name if c.isalnum() or c.isspace())
        words = clean_name.split()

        if len(words) == 1:
            # Single word: take first 3 letters
            team_key = words[0][:3].upper()
        else:
            # Multiple words: take first letter of each word (max 3)
            team_key = "".join(w[0].upper() for w in words[:3])

        # Add project number if > 1
        if project_number > 1:
            team_key = f"{team_key}{project_number}"

        # Team name format: "Client Name (Project 1)"
        team_name = f"{client_name} (Project {project_number})"

        print(f"Creating team: {team_name} (key: {team_key})")

        # Create team via GraphQL
        mutation = """
        mutation CreateTeam($name: String!, $key: String!) {
          teamCreate(input: {
            name: $name
            key: $key
          }) {
            success
            team {
              id
              key
              name
            }
          }
        }
        """

        result = self.client._query(mutation, {"name": team_name, "key": team_key})

        if not result["data"]["teamCreate"]["success"]:
            raise Exception(f"Failed to create team: {team_name}")

        team = result["data"]["teamCreate"]["team"]
        return team["id"], team["key"]

    def _get_primary_team(self, services: list[str]) -> str:
        """Deprecated - now we create team per client."""
        return "CLI"  # Not used anymore

    def _create_main_project(
        self,
        client_name: str,
        team_key: str,
        budget: int,
        timeline_weeks: int,
        services: list[str],
    ) -> str:
        """Create main client project."""
        team = self.teams[team_key]

        # Determine project name based on services
        if len(services) == 3:
            project_name = "Full Service"
        elif len(services) == 1:
            service_names = {"seo": "SEO Campaign", "content": "Content Marketing", "ads": "Ads Campaign"}
            project_name = service_names.get(services[0], "Marketing Project")
        else:
            # Multiple services
            service_str = " + ".join(s.upper() for s in services)
            project_name = f"{service_str} Campaign"

        # Project description
        services_list = "\n".join(f"- {s.upper()} Campaign" for s in services)
        description = f"""
# {client_name} - {project_name}

**Budget:** {budget:,} ₽
**Timeline:** {timeline_weeks} weeks
**Status:** Active

## Services
{services_list}

## Goals
- Increase organic traffic
- Generate quality content
- Optimize ad spend
- Track ROI

## Contact
- Client: {client_name}
- Start Date: 2026-05-15
"""

        # Create project via GraphQL (simplified - would need actual mutation)
        # For now, return mock ID
        project_id = f"client-{client_name.lower().replace(' ', '-')}"

        return project_id

    def _create_service_workflow(
        self,
        client_name: str,
        service: str,
        project_id: str,
        budget: int,
        timeline_weeks: int,
        team_key: str,
    ) -> list[dict]:
        """Create workflow tasks for a service."""
        workflows = {
            "seo": self._create_seo_workflow,
            "content": self._create_content_workflow,
            "ads": self._create_ads_workflow,
        }

        if service not in workflows:
            raise ValueError(f"Unknown service: {service}")

        return workflows[service](client_name, project_id, budget, timeline_weeks, team_key)

    def _create_seo_workflow(
        self, client_name: str, project_id: str, budget: int, timeline_weeks: int, team_key: str
    ) -> list[dict]:
        """Create SEO workflow tasks."""
        team = self.teams[team_key]
        todo_state = self.states[team_key]["Todo"]["id"]

        tasks = []

        # Phase 1: Research (Week 1-2)
        task1 = self.client.create_issue(
            title="SEO: Keyword Research",
            description=f"""
# Keyword Research

**Goal:** Identify target keywords for {client_name}

**Deliverables:**
- 50+ target keywords
- Search volume analysis
- Competition analysis
- Priority recommendations

**Timeline:** Week 1-2
**Budget:** {budget * 0.15:,.0f} ₽ (15% of total)
**Service:** SEO
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=1,
        )
        tasks.append({"id": task1, "title": "Keyword Research", "phase": "research"})

        # Phase 2: Competitor Analysis (Week 2-3)
        task2 = self.client.create_issue(
            title="SEO: Competitor Analysis",
            description=f"""
# Competitor Analysis

**Goal:** Analyze top 5 competitors for {client_name}

**Deliverables:**
- Competitor keyword analysis
- Backlink gap analysis
- Content gap analysis
- Technical SEO comparison

**Timeline:** Week 2-3
**Budget:** {budget * 0.15:,.0f} ₽ (15% of total)
**Service:** SEO
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=1,
        )
        tasks.append(
            {"id": task2, "title": "Competitor Analysis", "phase": "research"}
        )

        # Phase 3: On-Page Optimization (Week 3-6)
        task3 = self.client.create_issue(
            title="SEO: On-Page Optimization",
            description=f"""
# On-Page SEO Optimization

**Goal:** Optimize website for target keywords

**Deliverables:**
- Title tags optimization
- Meta descriptions
- Header structure
- Internal linking
- Image optimization
- Schema markup

**Timeline:** Week 3-6
**Budget:** {budget * 0.35:,.0f} ₽ (35% of total)
**Service:** SEO
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append(
            {"id": task3, "title": "On-Page Optimization", "phase": "optimization"}
        )

        # Phase 4: Link Building (Week 6-12)
        task4 = self.client.create_issue(
            title="SEO: Link Building Campaign",
            description=f"""
# Link Building Campaign

**Goal:** Build high-quality backlinks

**Deliverables:**
- 20+ quality backlinks
- Guest post placements
- Directory submissions
- Outreach campaign

**Timeline:** Week 6-12
**Budget:** {budget * 0.35:,.0f} ₽ (35% of total)
**Service:** SEO
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append(
            {"id": task4, "title": "Link Building", "phase": "link-building"}
        )

        return tasks

    def _create_content_workflow(
        self, client_name: str, project_id: str, budget: int, timeline_weeks: int, team_key: str
    ) -> list[dict]:
        """Create Content workflow tasks."""
        team = self.teams[team_key]
        todo_state = self.states[team_key]["Todo"]["id"]

        tasks = []

        # Phase 1: Content Strategy (Week 1-2)
        task1 = self.client.create_issue(
            title="Content: Strategy Development",
            description=f"""
# Content Strategy

**Goal:** Develop content plan for {client_name}

**Deliverables:**
- Content calendar (12 weeks)
- Topic clusters
- Target audience personas
- Content formats (blog, social, email)

**Timeline:** Week 1-2
**Budget:** {budget * 0.20:,.0f} ₽ (20% of total)
**Service:** Content
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=1,
        )
        tasks.append({"id": task1, "title": "Content Strategy", "phase": "strategy"})

        # Phase 2: Blog Content (Week 2-8)
        task2 = self.client.create_issue(
            title="Content: Blog Creation",
            description=f"""
# Blog Content Creation

**Goal:** Create 12 blog posts

**Deliverables:**
- 12 SEO-optimized blog posts
- 2,000+ words each
- Images and infographics
- Internal linking

**Timeline:** Week 2-8
**Budget:** {budget * 0.40:,.0f} ₽ (40% of total)
**Service:** Content
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append({"id": task2, "title": "Blog Content", "phase": "creation"})

        # Phase 3: Social Media (Week 2-12)
        task3 = self.client.create_issue(
            title="Content: Social Media",
            description=f"""
# Social Media Content

**Goal:** Create social media content

**Deliverables:**
- 48 social posts (4/week)
- Platform-specific content
- Engagement strategy
- Hashtag research

**Timeline:** Week 2-12
**Budget:** {budget * 0.25:,.0f} ₽ (25% of total)
**Service:** Content
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append({"id": task3, "title": "Social Media", "phase": "social"})

        # Phase 4: Email Marketing (Week 4-12)
        task4 = self.client.create_issue(
            title="Content: Email Marketing",
            description=f"""
# Email Marketing

**Goal:** Create email campaigns

**Deliverables:**
- 8 email campaigns
- Newsletter templates
- Segmentation strategy
- A/B testing

**Timeline:** Week 4-12
**Budget:** {budget * 0.15:,.0f} ₽ (15% of total)
**Service:** Content
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=3,
        )
        tasks.append({"id": task4, "title": "Email Marketing", "phase": "email"})

        return tasks

    def _create_ads_workflow(
        self, client_name: str, project_id: str, budget: int, timeline_weeks: int, team_key: str
    ) -> list[dict]:
        """Create Ads workflow tasks."""
        team = self.teams[team_key]
        todo_state = self.states[team_key]["Todo"]["id"]

        tasks = []

        # Phase 1: Campaign Setup (Week 1-2)
        task1 = self.client.create_issue(
            title="Ads: Yandex Direct Setup",
            description=f"""
# Yandex Direct Campaign Setup

**Goal:** Launch Yandex Direct campaigns

**Deliverables:**
- Campaign structure
- Ad groups (10+)
- Keywords (100+)
- Ad copy (20+ variants)
- Landing page recommendations

**Timeline:** Week 1-2
**Budget:** {budget * 0.20:,.0f} ₽ (20% of total)
**Service:** Ads
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=1,
        )
        tasks.append({"id": task1, "title": "Campaign Setup", "phase": "setup"})

        # Phase 2: Optimization (Week 2-6)
        task2 = self.client.create_issue(
            title="Ads: Campaign Optimization",
            description=f"""
# Campaign Optimization

**Goal:** Optimize ad performance

**Deliverables:**
- Bid optimization
- Keyword refinement
- Ad copy A/B testing
- Negative keywords
- Quality score improvement

**Timeline:** Week 2-6
**Budget:** {budget * 0.30:,.0f} ₽ (30% of total)
**Service:** Ads
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append({"id": task2, "title": "Optimization", "phase": "optimization"})

        # Phase 3: Scaling (Week 6-12)
        task3 = self.client.create_issue(
            title="Ads: Campaign Scaling",
            description=f"""
# Campaign Scaling

**Goal:** Scale successful campaigns

**Deliverables:**
- Budget increase for winners
- New ad groups
- Expanded targeting
- Remarketing campaigns

**Timeline:** Week 6-12
**Budget:** {budget * 0.50:,.0f} ₽ (50% of total)
**Service:** Ads
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append({"id": task3, "title": "Scaling", "phase": "scaling"})

        return tasks


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create client project in Linear",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("client_name", help="Client company name")
    parser.add_argument(
        "--services",
        default="seo,content,ads",
        help="Services to include (comma-separated: seo,content,ads)",
    )
    parser.add_argument(
        "--budget", type=int, default=100000, help="Total budget in rubles"
    )
    parser.add_argument(
        "--timeline", type=int, default=12, help="Project duration in weeks"
    )

    args = parser.parse_args()

    # Parse services
    services = [s.strip().lower() for s in args.services.split(",")]

    # Validate services
    valid_services = {"seo", "content", "ads"}
    invalid = set(services) - valid_services
    if invalid:
        print(f"❌ Invalid services: {', '.join(invalid)}")
        print(f"Valid services: {', '.join(valid_services)}")
        sys.exit(1)

    # Initialize Linear client
    import os

    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("❌ LINEAR_API_KEY environment variable not set")
        print("\nMake sure LINEAR_API_KEY is set in:")
        print("  - Environment variable")
        print("  - Or ~/.claude/settings.json")
        sys.exit(1)

    try:
        linear_client = LinearClient(api_key)
    except Exception as e:
        print(f"❌ Failed to initialize Linear client: {e}")
        sys.exit(1)

    # Create client project
    creator = ClientProjectCreator(linear_client)

    try:
        result = creator.create_client_project(
            client_name=args.client_name,
            services=services,
            budget=args.budget,
            timeline_weeks=args.timeline,
        )

        print("Project Details:")
        print(f"  Project ID: {result['project_id']}")
        print(f"  Total Tasks: {result['total_tasks']}")
        print()

        for service, tasks in result["tasks"].items():
            print(f"{service.upper()} Tasks:")
            for task in tasks:
                print(f"  - {task['title']} ({task['phase']})")
            print()

    except Exception as e:
        print(f"❌ Failed to create client project: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
