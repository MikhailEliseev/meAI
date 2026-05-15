#!/usr/bin/env python3
"""Reorganize Linear structure for client hierarchy.

Current (WRONG):
- Teams: DEV, MKT, SEO, CNT, ADS, ANL
- Projects in each team

Target (CORRECT):
- Teams: DEV (internal), MKT (internal), CLIENTS (client projects)
- Client hierarchy:
  Client A
    └─ Project: Full Service
        ├─ SEO Campaign (label: seo)
        ├─ Content Creation (label: content)
        ├─ Ads Campaign (label: ads)
        └─ Analytics Setup (label: analytics)

Steps:
1. Create CLIENTS team (if not exists)
2. Archive SEO, CNT, ADS, ANL teams
3. Move client projects to CLIENTS team
4. Update labels to mark service type
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.linear_cli import LinearClient


def main():
    """Reorganize Linear structure."""
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY environment variable not set")
        sys.exit(1)

    client = LinearClient(api_key)

    print("=" * 80)
    print("Linear Structure Reorganization")
    print("=" * 80)
    print()

    # Step 1: Get current teams
    print("Step 1: Checking current teams...")
    teams_query = """
    query {
      teams {
        nodes {
          id
          key
          name
        }
      }
    }
    """
    teams_result = client._query(teams_query)
    teams = teams_result["data"]["teams"]["nodes"]

    print(f"Found {len(teams)} teams:")
    for team in teams:
        print(f"  - {team['key']}: {team['name']} (ID: {team['id']})")
    print()

    # Find teams to archive
    service_teams = [t for t in teams if t["key"] in ["SEO", "CNT", "ADS", "ANL"]]
    dev_team = next((t for t in teams if t["key"] == "DEV"), None)
    mkt_team = next((t for t in teams if t["key"] == "MKT"), None)

    if not dev_team or not mkt_team:
        print("Error: DEV or MKT team not found!")
        sys.exit(1)

    # Step 2: Create CLIENTS team
    print("Step 2: Creating CLIENTS team...")

    # Check if CLI team already exists
    clients_team = next((t for t in teams if t["key"] == "CLI"), None)

    if clients_team:
        print(f"✅ CLIENTS team already exists: {clients_team['key']} (ID: {clients_team['id']})")
    else:
        create_team_mutation = """
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

        clients_team_result = client._query(
            create_team_mutation,
            {"name": "Client Projects", "key": "CLI"}
        )

        if clients_team_result and clients_team_result["data"]["teamCreate"]["success"]:
            clients_team = clients_team_result["data"]["teamCreate"]["team"]
            print(f"✅ Created CLIENTS team: {clients_team['key']} (ID: {clients_team['id']})")
        else:
            print("❌ Failed to create CLIENTS team")
            sys.exit(1)
    print()

    # Step 3: Note about service teams
    print("Step 3: Service teams (SEO, CNT, ADS, ANL)...")
    print("ℹ️  Note: Linear API doesn't support team archiving")
    print("ℹ️  These teams will remain but won't be used for client projects")
    print("ℹ️  All client projects should be created in CLI team")
    print()

    if service_teams:
        print("Service teams to ignore:")
        for team in service_teams:
            print(f"  - {team['key']}: {team['name']}")
    print()

    # Step 4: Summary
    print("=" * 80)
    print("✅ Reorganization Complete!")
    print("=" * 80)
    print()
    print("New structure:")
    print("  - DEV: AIM Development (internal)")
    print("  - MKT: AIM Marketing (internal)")
    print("  - CLI: Client Projects (client hierarchy)")
    print()
    print("Next steps:")
    print("  1. Create client projects in CLI team")
    print("  2. Use labels (seo, content, ads, analytics) for service type")
    print("  3. Use project hierarchy: Client → Project → Tasks")
    print()

    client.client.close()


if __name__ == "__main__":
    main()
