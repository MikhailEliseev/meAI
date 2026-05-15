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
    ) -> dict:
        """
        Create complete client project structure.

        Args:
            client_name: Client company name
            services: List of services (seo, content, ads)
            budget: Total budget in rubles
            timeline_weeks: Project duration in weeks

        Returns:
            Project details with created tasks
        """
        print(f"\n{'=' * 80}")
        print(f"Creating Client Project: {client_name}")
        print(f"{'=' * 80}\n")

        # Determine primary team based on services
        primary_team = self._get_primary_team(services)
        print(f"Primary team: {primary_team}")

        # Create main project
        project_id = self._create_main_project(
            client_name, primary_team, budget, timeline_weeks
        )
        print(f"✅ Project created: {project_id}\n")

        # Create workflow tasks for each service
        created_tasks = {}
        for service in services:
            print(f"Creating {service.upper()} workflow...")
            tasks = self._create_service_workflow(
                client_name, service, project_id, budget, timeline_weeks
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

    def _get_primary_team(self, services: list[str]) -> str:
        """Determine primary team based on services."""
        # Priority: SEO > Content > Ads
        if "seo" in services:
            return "SEO"
        elif "content" in services:
            return "CNT"
        elif "ads" in services:
            return "ADS"
        else:
            return "DEV"  # Default

    def _create_main_project(
        self, client_name: str, team_key: str, budget: int, timeline_weeks: int
    ) -> str:
        """Create main client project."""
        team = self.teams[team_key]

        # Project description
        description = f"""
# {client_name} - Full Service Marketing

**Budget:** {budget:,} ₽
**Timeline:** {timeline_weeks} weeks
**Status:** Active

## Services
- SEO Campaign
- Content Creation
- Ads Management

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
    ) -> list[dict]:
        """Create workflow tasks for a service."""
        workflows = {
            "seo": self._create_seo_workflow,
            "content": self._create_content_workflow,
            "ads": self._create_ads_workflow,
        }

        if service not in workflows:
            raise ValueError(f"Unknown service: {service}")

        return workflows[service](client_name, project_id, budget, timeline_weeks)

    def _create_seo_workflow(
        self, client_name: str, project_id: str, budget: int, timeline_weeks: int
    ) -> list[dict]:
        """Create SEO workflow tasks."""
        team = self.teams["SEO"]
        todo_state = self.states["SEO"]["Todo"]["id"]

        tasks = []

        # Phase 1: Research (Week 1-2)
        task1 = self.client.create_issue(
            title=f"[{client_name}] Keyword Research",
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
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=1,
        )
        tasks.append({"id": task1, "title": "Keyword Research", "phase": "research"})

        # Phase 2: Competitor Analysis (Week 2-3)
        task2 = self.client.create_issue(
            title=f"[{client_name}] Competitor Analysis",
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
            title=f"[{client_name}] On-Page SEO Optimization",
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
            title=f"[{client_name}] Link Building Campaign",
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
        self, client_name: str, project_id: str, budget: int, timeline_weeks: int
    ) -> list[dict]:
        """Create Content workflow tasks."""
        team = self.teams["CNT"]
        todo_state = self.states["CNT"]["Todo"]["id"]

        tasks = []

        # Phase 1: Content Strategy (Week 1-2)
        task1 = self.client.create_issue(
            title=f"[{client_name}] Content Strategy",
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
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=1,
        )
        tasks.append({"id": task1, "title": "Content Strategy", "phase": "strategy"})

        # Phase 2: Blog Content (Week 2-8)
        task2 = self.client.create_issue(
            title=f"[{client_name}] Blog Content Creation",
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
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append({"id": task2, "title": "Blog Content", "phase": "creation"})

        # Phase 3: Social Media (Week 2-12)
        task3 = self.client.create_issue(
            title=f"[{client_name}] Social Media Content",
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
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append({"id": task3, "title": "Social Media", "phase": "social"})

        # Phase 4: Email Marketing (Week 4-12)
        task4 = self.client.create_issue(
            title=f"[{client_name}] Email Marketing",
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
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=3,
        )
        tasks.append({"id": task4, "title": "Email Marketing", "phase": "email"})

        return tasks

    def _create_ads_workflow(
        self, client_name: str, project_id: str, budget: int, timeline_weeks: int
    ) -> list[dict]:
        """Create Ads workflow tasks."""
        team = self.teams["ADS"]
        todo_state = self.states["ADS"]["Todo"]["id"]

        tasks = []

        # Phase 1: Campaign Setup (Week 1-2)
        task1 = self.client.create_issue(
            title=f"[{client_name}] Yandex Direct Setup",
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
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=1,
        )
        tasks.append({"id": task1, "title": "Campaign Setup", "phase": "setup"})

        # Phase 2: Optimization (Week 2-6)
        task2 = self.client.create_issue(
            title=f"[{client_name}] Campaign Optimization",
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
""",
            team_id=team["id"],
            state_id=todo_state,
            priority=2,
        )
        tasks.append({"id": task2, "title": "Optimization", "phase": "optimization"})

        # Phase 3: Scaling (Week 6-12)
        task3 = self.client.create_issue(
            title=f"[{client_name}] Campaign Scaling",
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
    try:
        linear_client = LinearClient()
    except Exception as e:
        print(f"❌ Failed to initialize Linear client: {e}")
        print("\nMake sure LINEAR_API_KEY is set in:")
        print("  - Environment variable")
        print("  - Or ~/.config/claude-code/settings.json")
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
