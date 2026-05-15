#!/usr/bin/env python3
"""
Linear CLI - Command-line interface for Linear API.

Usage:
    python scripts/linear_cli.py list                    # List all issues
    python scripts/linear_cli.py show MIK-1              # Show issue details
    python scripts/linear_cli.py create "Title" "Desc"   # Create new issue
    python scripts/linear_cli.py update MIK-1 --state "In Progress"
    python scripts/linear_cli.py comment MIK-1 "Comment text"
"""

import os
import sys
import json
import argparse
from typing import Any, Optional
import httpx


class LinearClient:
    """Linear API client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        self.client = httpx.Client(timeout=30.0)

    def _query(self, query: str, variables: Optional[dict] = None) -> dict[str, Any]:
        """Execute GraphQL query (sync)."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.client.post(
            self.base_url,
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def _execute_query(self, query: str, variables: Optional[dict] = None) -> dict[str, Any]:
        """Execute GraphQL query (async)."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            if "errors" in result:
                raise Exception(f"GraphQL errors: {result['errors']}")
            return result.get("data", {})

    async def close(self):
        """Close HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()

    def list_issues(self, limit: int = 50) -> list[dict]:
        """List all issues."""
        query = """
        query($limit: Int!) {
            issues(first: $limit, orderBy: updatedAt) {
                nodes {
                    id
                    identifier
                    title
                    description
                    state { name }
                    priority
                    assignee { name email }
                    createdAt
                    updatedAt
                    url
                }
            }
        }
        """
        result = self._query(query, {"limit": limit})
        return result["data"]["issues"]["nodes"]

    def get_issue(self, identifier: str) -> Optional[dict]:
        """Get issue by identifier (e.g., MIK-1)."""
        query = """
        query($identifier: String!) {
            issue(id: $identifier) {
                id
                identifier
                title
                description
                state { name }
                priority
                assignee { name email }
                createdAt
                updatedAt
                url
                comments { nodes { body createdAt user { name } } }
            }
        }
        """
        result = self._query(query, {"identifier": identifier})
        return result["data"].get("issue")

    def create_issue(
        self,
        title: str,
        description: str = "",
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        state_id: Optional[str] = None,
        priority: int = 0,
        label_ids: Optional[list[str]] = None,
    ) -> str:
        """Create new issue and return issue ID."""
        if not team_id:
            # Get first team
            teams = self.list_teams()
            if not teams:
                raise ValueError("No teams found")
            team_id = teams[0]["id"]

        query = """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        input_data = {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }

        if project_id:
            input_data["projectId"] = project_id
        if state_id:
            input_data["stateId"] = state_id
        if label_ids:
            input_data["labelIds"] = label_ids

        variables = {"input": input_data}
        result = self._query(query, variables)
        issue = result["data"]["issueCreate"]["issue"]
        return issue["id"]

    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        state_id: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> dict:
        """Update issue."""
        query = """
        mutation($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    state { name }
                }
            }
        }
        """
        input_data = {}
        if title:
            input_data["title"] = title
        if description:
            input_data["description"] = description
        if state_id:
            input_data["stateId"] = state_id
        if priority is not None:
            input_data["priority"] = priority

        variables = {"id": issue_id, "input": input_data}
        result = self._query(query, variables)
        return result["data"]["issueUpdate"]["issue"]

    def add_comment(self, issue_id: str, body: str) -> dict:
        """Add comment to issue."""
        query = """
        mutation($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                    body
                    createdAt
                }
            }
        }
        """
        variables = {
            "input": {
                "issueId": issue_id,
                "body": body,
            }
        }
        result = self._query(query, variables)
        return result["data"]["commentCreate"]["comment"]

    def list_teams(self) -> list[dict]:
        """List all teams."""
        query = """
        {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        result = self._query(query)
        return result["data"]["teams"]["nodes"]

    def list_states(self, team_id: str) -> list[dict]:
        """List workflow states for team."""
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                    }
                }
            }
        }
        """
        result = self._query(query, {"teamId": team_id})
        return result["data"]["team"]["states"]["nodes"]


def format_issue(issue: dict) -> str:
    """Format issue for display."""
    lines = [
        f"ID: {issue['identifier']}",
        f"Title: {issue['title']}",
        f"State: {issue['state']['name']}",
        f"Priority: {issue['priority']}",
    ]

    if issue.get("assignee"):
        lines.append(f"Assignee: {issue['assignee']['name']}")

    if issue.get("description"):
        lines.append(f"\nDescription:\n{issue['description']}")

    if issue.get("url"):
        lines.append(f"\nURL: {issue['url']}")

    if issue.get("comments"):
        lines.append("\nComments:")
        for comment in issue["comments"]["nodes"]:
            user = comment["user"]["name"]
            body = comment["body"]
            lines.append(f"  - {user}: {body}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Linear CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # List command
    list_parser = subparsers.add_parser("list", help="List issues")
    list_parser.add_argument("--limit", type=int, default=50, help="Max issues")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show issue details")
    show_parser.add_argument("identifier", help="Issue identifier (e.g., MIK-1)")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create issue")
    create_parser.add_argument("title", help="Issue title")
    create_parser.add_argument("description", nargs="?", default="", help="Description")
    create_parser.add_argument("--priority", type=int, default=0, help="Priority (0-4)")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update issue")
    update_parser.add_argument("identifier", help="Issue identifier")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument("--state", help="New state name")
    update_parser.add_argument("--priority", type=int, help="New priority")

    # Comment command
    comment_parser = subparsers.add_parser("comment", help="Add comment")
    comment_parser.add_argument("identifier", help="Issue identifier")
    comment_parser.add_argument("body", help="Comment text")

    # Teams command
    subparsers.add_parser("teams", help="List teams")

    # States command
    states_parser = subparsers.add_parser("states", help="List workflow states")
    states_parser.add_argument("team_id", help="Team ID")

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = LinearClient(api_key)

    try:
        if args.command == "list":
            issues = client.list_issues(args.limit)
            for issue in issues:
                print(f"{issue['identifier']}: {issue['title']} [{issue['state']['name']}]")

        elif args.command == "show":
            issue = client.get_issue(args.identifier)
            if issue:
                print(format_issue(issue))
            else:
                print(f"Issue {args.identifier} not found", file=sys.stderr)
                sys.exit(1)

        elif args.command == "create":
            issue = client.create_issue(
                title=args.title,
                description=args.description,
                priority=args.priority,
            )
            print(f"Created: {issue['identifier']} - {issue['title']}")
            print(f"URL: {issue['url']}")

        elif args.command == "update":
            # Get issue ID first
            issues = client.list_issues()
            issue_id = None
            for issue in issues:
                if issue["identifier"] == args.identifier:
                    issue_id = issue["id"]
                    break

            if not issue_id:
                print(f"Issue {args.identifier} not found", file=sys.stderr)
                sys.exit(1)

            # Get state ID if state name provided
            state_id = None
            if args.state:
                teams = client.list_teams()
                if teams:
                    states = client.list_states(teams[0]["id"])
                    for state in states:
                        if state["name"].lower() == args.state.lower():
                            state_id = state["id"]
                            break

            issue = client.update_issue(
                issue_id=issue_id,
                title=args.title,
                description=args.description,
                state_id=state_id,
                priority=args.priority,
            )
            print(f"Updated: {issue['identifier']} - {issue['title']}")

        elif args.command == "comment":
            # Get issue ID first
            issues = client.list_issues()
            issue_id = None
            for issue in issues:
                if issue["identifier"] == args.identifier:
                    issue_id = issue["id"]
                    break

            if not issue_id:
                print(f"Issue {args.identifier} not found", file=sys.stderr)
                sys.exit(1)

            comment = client.add_comment(issue_id, args.body)
            print(f"Added comment to {args.identifier}")

        elif args.command == "teams":
            teams = client.list_teams()
            for team in teams:
                print(f"{team['key']}: {team['name']} (ID: {team['id']})")

        elif args.command == "states":
            states = client.list_states(args.team_id)
            for state in states:
                print(f"{state['name']} ({state['type']}) - ID: {state['id']}")

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
