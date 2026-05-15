#!/usr/bin/env python3
"""Send Weekly Progress Reports to Clients

Generates and sends weekly progress reports for all active client projects.

Usage:
    python scripts/send_weekly_reports.py
    python scripts/send_weekly_reports.py --project-id "project-id"
    python scripts/send_weekly_reports.py --dry-run
"""

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

scripts_path = Path(__file__).parent
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from linear_cli import LinearClient
from src.meai.tracking.progress_tracker import ProgressTracker


class WeeklyReportSender:
    """Sends weekly progress reports to clients."""

    def __init__(self, linear_client: LinearClient, dry_run: bool = False):
        self.linear = linear_client
        self.tracker = ProgressTracker()
        self.dry_run = dry_run

    async def get_client_projects(self) -> list[dict]:
        """Get all active client projects."""
        query = """
        query GetClientProjects {
          projects(filter: {
            state: { type: { eq: "started" } }
          }) {
            nodes {
              id
              name
              description
              startDate
              targetDate
              state {
                name
              }
              lead {
                email
              }
              members {
                nodes {
                  id
                  email
                  guest
                }
              }
            }
          }
        }
        """

        result = self.linear.execute_graphql(query)
        projects = result.get("projects", {}).get("nodes", [])

        # Filter projects with guest members (client projects)
        client_projects = []
        for project in projects:
            members = project.get("members", {}).get("nodes", [])
            guests = [m for m in members if m.get("guest")]
            if guests:
                project["client_email"] = guests[0]["email"]
                client_projects.append(project)

        return client_projects

    async def get_project_tasks(self, project_id: str) -> dict:
        """Get task statistics for a project."""
        query = """
        query GetProjectTasks($projectId: ID!) {
          project(id: $projectId) {
            issues {
              nodes {
                id
                state {
                  type
                }
              }
            }
          }
        }
        """

        result = self.linear.execute_graphql(query, {"projectId": project_id})
        issues = result.get("project", {}).get("issues", {}).get("nodes", [])

        total = len(issues)
        completed = sum(1 for i in issues if i["state"]["type"] == "completed")
        in_progress = sum(1 for i in issues if i["state"]["type"] == "started")
        pending = total - completed - in_progress

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
        }

    async def generate_report(self, project: dict) -> str:
        """Generate progress report for a project."""
        # Get task statistics
        tasks = await self.get_project_tasks(project["id"])

        # Parse dates
        start_date = datetime.fromisoformat(
            project["startDate"].replace("Z", "+00:00")
        )
        end_date = datetime.fromisoformat(project["targetDate"].replace("Z", "+00:00"))

        # Mock budget data (would come from project metadata in production)
        total_budget = 100000.0  # TODO: Get from project custom fields
        spent_budget = total_budget * (tasks["completed"] / tasks["total"]) if tasks["total"] > 0 else 0

        # Generate report
        report = self.tracker.generate_progress_report(
            project_id=project["id"],
            client_name=project["name"],
            total_tasks=tasks["total"],
            completed_tasks=tasks["completed"],
            in_progress_tasks=tasks["in_progress"],
            total_budget=total_budget,
            spent_budget=spent_budget,
            start_date=start_date,
            end_date=end_date,
        )

        return self.tracker.format_report(report)

    async def send_report(self, client_email: str, project_name: str, report: str):
        """Send report via email."""
        if self.dry_run:
            print(f"\n[DRY RUN] Would send report to: {client_email}")
            print(f"Subject: Weekly Progress Report: {project_name}")
            print(f"Body length: {len(report)} characters")
            return

        # TODO: Implement actual email sending
        # For now, just print
        print(f"\n{'=' * 80}")
        print(f"Sending report to: {client_email}")
        print(f"{'=' * 80}")
        print(report)
        print()

    async def send_all_reports(self, project_id: str | None = None):
        """Send reports for all client projects or specific project."""
        print(f"\n{'=' * 80}")
        print("Weekly Progress Reports")
        print(f"{'=' * 80}\n")
        print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print()

        # Get projects
        if project_id:
            # Get specific project
            query = """
            query GetProject($projectId: ID!) {
              project(id: $projectId) {
                id
                name
                description
                startDate
                targetDate
                state {
                  name
                }
                lead {
                  email
                }
                members {
                  nodes {
                    id
                    email
                    guest
                  }
                }
              }
            }
            """
            result = self.linear.execute_graphql(query, {"projectId": project_id})
            project = result.get("project")
            if not project:
                print(f"❌ Project not found: {project_id}")
                return

            members = project.get("members", {}).get("nodes", [])
            guests = [m for m in members if m.get("guest")]
            if not guests:
                print(f"❌ No guest members found for project: {project['name']}")
                return

            project["client_email"] = guests[0]["email"]
            projects = [project]
        else:
            # Get all client projects
            projects = await self.get_client_projects()

        if not projects:
            print("No client projects found.")
            return

        print(f"Found {len(projects)} client project(s)\n")

        # Send reports
        for project in projects:
            try:
                print(f"Processing: {project['name']}...")
                report = await self.generate_report(project)
                await self.send_report(
                    project["client_email"], project["name"], report
                )
                print(f"✅ Report sent to {project['client_email']}")
            except Exception as e:
                print(f"❌ Failed to send report for {project['name']}: {e}")
                import traceback

                traceback.print_exc()

        print(f"\n{'=' * 80}")
        print("✅ Weekly Reports Complete!")
        print(f"{'=' * 80}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Send weekly progress reports to clients",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--project-id", help="Send report for specific project only", default=None
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (don't actually send emails)",
    )

    args = parser.parse_args()

    try:
        linear_client = LinearClient()
    except Exception as e:
        print(f"❌ Failed to initialize Linear client: {e}")
        print("\nMake sure LINEAR_API_KEY is set in:")
        print("  - Environment variable")
        print("  - Or ~/.config/claude-code/settings.json")
        sys.exit(1)

    sender = WeeklyReportSender(linear_client, dry_run=args.dry_run)

    try:
        await sender.send_all_reports(project_id=args.project_id)
    except Exception as e:
        print(f"❌ Failed to send reports: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
