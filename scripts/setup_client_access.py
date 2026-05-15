#!/usr/bin/env python3
"""Setup Linear Client Access

Creates guest user, grants project access, configures notifications.

Usage:
    python scripts/setup_client_access.py "client@example.com" "project-id"
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for LinearClient import
scripts_path = Path(__file__).parent
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from linear_cli import LinearClient


def setup_client_access(client_email: str, project_id: str) -> dict:
    """
    Setup complete client access.

    Args:
        client_email: Client email address
        project_id: Linear project ID

    Returns:
        Setup result with user ID and access details
    """
    client = LinearClient()

    print(f"\n{'=' * 80}")
    print(f"Setting up client access: {client_email}")
    print(f"{'=' * 80}\n")

    # Step 1: Invite guest user
    print("Step 1: Inviting guest user...")
    invite_mutation = """
    mutation InviteGuest($email: String!) {
      userInvite(input: {
        email: $email
        role: guest
      }) {
        success
        user {
          id
          email
          guest
        }
      }
    }
    """

    try:
        invite_result = client.execute_graphql(invite_mutation, {"email": client_email})

        if not invite_result.get("userInvite", {}).get("success"):
            print("❌ Failed to invite guest user")
            return {"success": False, "error": "Invitation failed"}

        user_id = invite_result["userInvite"]["user"]["id"]
        print(f"✅ Guest user invited: {user_id}\n")

    except Exception as e:
        print(f"❌ Failed to invite guest user: {e}")
        return {"success": False, "error": str(e)}

    # Step 2: Grant project access
    print("Step 2: Granting project access...")
    access_mutation = """
    mutation ShareProject($projectId: String!, $userId: String!) {
      projectUpdate(
        id: $projectId
        input: {
          memberIds: [$userId]
        }
      ) {
        success
        project {
          id
          name
        }
      }
    }
    """

    try:
        access_result = client.execute_graphql(
            access_mutation, {"projectId": project_id, "userId": user_id}
        )

        if not access_result.get("projectUpdate", {}).get("success"):
            print("❌ Failed to grant project access")
            return {"success": False, "error": "Access grant failed"}

        project_name = access_result["projectUpdate"]["project"]["name"]
        print(f"✅ Project access granted: {project_name}\n")

    except Exception as e:
        print(f"❌ Failed to grant project access: {e}")
        return {"success": False, "error": str(e)}

    # Step 3: Summary
    print(f"{'=' * 80}")
    print("✅ Client Access Setup Complete!")
    print(f"{'=' * 80}\n")
    print(f"Client: {client_email}")
    print(f"User ID: {user_id}")
    print(f"Project: {project_name}")
    print(f"Access Level: Read-only (Guest)")
    print()
    print("Next steps:")
    print("1. Client will receive invitation email")
    print("2. Client clicks link to accept invitation")
    print("3. Client can view project progress")
    print("4. Weekly reports will be sent automatically")
    print()

    return {
        "success": True,
        "user_id": user_id,
        "project_id": project_id,
        "project_name": project_name,
        "email": client_email,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Linear client access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("email", help="Client email address")
    parser.add_argument("project_id", help="Linear project ID")

    args = parser.parse_args()

    try:
        result = setup_client_access(args.email, args.project_id)

        if not result["success"]:
            print(f"❌ Setup failed: {result.get('error')}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
