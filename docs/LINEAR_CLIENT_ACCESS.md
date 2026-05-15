# Linear Client Access Setup

**Purpose:** Configure guest user access for clients to view their project progress in Linear.

**Last Updated:** 2026-05-15

---

## Overview

Clients need read-only access to their Linear projects to:
- View task progress and status
- Track budget utilization
- Monitor timeline and deadlines
- See quality scores from Magisters
- Receive automated progress updates

**Access Level:** Read-only (no editing, no commenting)

---

## Setup Process

### 1. Create Guest User

**Via Linear UI:**

1. Go to **Settings** → **Members**
2. Click **Invite member**
3. Enter client email
4. Select role: **Guest**
5. Click **Send invitation**

**Via API (automated):**

```python
from scripts.linear_cli import LinearClient

client = LinearClient()

# Create guest user
mutation = """
mutation InviteGuest($email: String!, $teamIds: [String!]!) {
  userInvite(input: {
    email: $email
    role: guest
    teamIds: $teamIds
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

result = client.execute_graphql(mutation, {
    "email": "client@example.com",
    "teamIds": ["team-id-here"]
})
```

### 2. Grant Project Access

**Via Linear UI:**

1. Open client's project
2. Click **Share** button (top right)
3. Add guest user email
4. Set permissions: **Can view**
5. Click **Share**

**Via API:**

```python
# Grant project access
mutation = """
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
      members {
        nodes {
          id
          email
        }
      }
    }
  }
}
"""

result = client.execute_graphql(mutation, {
    "projectId": "project-id-here",
    "userId": "user-id-here"
})
```

### 3. Configure Notifications

**Email Notifications:**

Linear automatically sends email notifications for:
- Task status changes (Todo → In Progress → Done)
- New comments on tasks
- Project updates
- Weekly progress summaries

**Custom Notifications:**

For custom notifications (e.g., budget alerts, timeline warnings), use webhooks:

```python
# Setup webhook for project updates
mutation = """
mutation CreateWebhook($url: String!, $teamId: String!) {
  webhookCreate(input: {
    url: $url
    teamId: $teamId
    resourceTypes: ["Issue", "Project"]
  }) {
    success
    webhook {
      id
      url
    }
  }
}
"""

result = client.execute_graphql(mutation, {
    "url": "https://iamaim.ru/api/webhooks/linear",
    "teamId": "team-id-here"
})
```

### 4. Weekly Progress Reports

**Automated Report Generation:**

```python
from src.meai.tracking.progress_tracker import ProgressTracker
from datetime import datetime, timezone

tracker = ProgressTracker()

# Generate weekly report
report = tracker.generate_progress_report(
    project_id="client-project-id",
    client_name="Client Name",
    total_tasks=20,
    completed_tasks=8,
    in_progress_tasks=5,
    total_budget=100000,
    spent_budget=35000,
    start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
    end_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
    seo_score=85.0,
    content_score=78.0,
    ads_score=82.0,
)

# Format as text
report_text = tracker.format_report(report)

# Send via email
send_email(
    to="client@example.com",
    subject=f"Weekly Progress Report: {report.client_name}",
    body=report_text
)
```

**Schedule with cron:**

```bash
# Add to crontab (every Monday at 9 AM)
0 9 * * 1 cd /path/to/meAI && python scripts/send_weekly_reports.py
```

---

## Client View Capabilities

### What Clients Can See:

✅ **Projects:**
- Project name and description
- Overall progress percentage
- Budget utilization
- Timeline status
- Quality scores

✅ **Tasks:**
- Task titles and descriptions
- Task status (Todo, In Progress, Done)
- Task assignees
- Due dates
- Priority labels

✅ **Progress Metrics:**
- Tasks completed / total
- Budget spent / remaining
- Timeline progress
- Quality scores from Magisters

### What Clients Cannot Do:

❌ **Editing:**
- Cannot create tasks
- Cannot edit task details
- Cannot change task status
- Cannot assign tasks

❌ **Commenting:**
- Cannot add comments (read-only)
- Cannot @mention team members

❌ **Administration:**
- Cannot invite other users
- Cannot change project settings
- Cannot access other projects

---

## Security Considerations

### Access Control:

1. **Project Isolation:**
   - Guests only see projects they're invited to
   - No access to internal projects (AIM Development, AIM Marketing)
   - No access to other clients' projects

2. **Data Privacy:**
   - Guests cannot see team discussions
   - Guests cannot see internal comments (use private comments)
   - Guests cannot see budget details (unless explicitly shared)

3. **API Keys:**
   - Guests do not have API access
   - All API operations require team member credentials

### Best Practices:

1. **Use Private Comments:**
   ```
   Internal discussion about client → use private comments
   Client-facing updates → use public comments
   ```

2. **Separate Projects:**
   ```
   Client A Project → only Client A has access
   Client B Project → only Client B has access
   Internal Projects → no guest access
   ```

3. **Regular Access Review:**
   - Review guest access quarterly
   - Remove access when project completes
   - Audit guest activity logs

---

## Automation Script

**Complete setup script:**

```python
#!/usr/bin/env python3
"""Setup Linear Client Access

Creates guest user, grants project access, configures notifications.

Usage:
    python scripts/setup_client_access.py "client@example.com" "project-id"
"""

import argparse
import sys
from pathlib import Path

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
    
    invite_result = client.execute_graphql(invite_mutation, {
        "email": client_email
    })
    
    if not invite_result.get("userInvite", {}).get("success"):
        print("❌ Failed to invite guest user")
        return {"success": False, "error": "Invitation failed"}
    
    user_id = invite_result["userInvite"]["user"]["id"]
    print(f"✅ Guest user invited: {user_id}\n")
    
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
    
    access_result = client.execute_graphql(access_mutation, {
        "projectId": project_id,
        "userId": user_id
    })
    
    if not access_result.get("projectUpdate", {}).get("success"):
        print("❌ Failed to grant project access")
        return {"success": False, "error": "Access grant failed"}
    
    project_name = access_result["projectUpdate"]["project"]["name"]
    print(f"✅ Project access granted: {project_name}\n")
    
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
        "email": client_email
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
```

---

## Testing Client View

### Test Checklist:

1. **Invitation:**
   - [ ] Client receives invitation email
   - [ ] Invitation link works
   - [ ] Client can create Linear account

2. **Project Access:**
   - [ ] Client sees their project
   - [ ] Client does NOT see other projects
   - [ ] Client does NOT see internal projects

3. **Task Visibility:**
   - [ ] Client sees all project tasks
   - [ ] Client sees task status
   - [ ] Client sees task descriptions
   - [ ] Client sees due dates

4. **Progress Metrics:**
   - [ ] Client sees completion percentage
   - [ ] Client sees budget utilization
   - [ ] Client sees timeline status
   - [ ] Client sees quality scores

5. **Restrictions:**
   - [ ] Client CANNOT create tasks
   - [ ] Client CANNOT edit tasks
   - [ ] Client CANNOT comment
   - [ ] Client CANNOT invite others

6. **Notifications:**
   - [ ] Client receives task update emails
   - [ ] Client receives weekly reports
   - [ ] Email format is correct
   - [ ] Unsubscribe link works

---

## Troubleshooting

### Issue: Client cannot see project

**Solution:**
1. Check guest user was invited successfully
2. Verify project access was granted
3. Check client accepted invitation
4. Verify client is logged in

### Issue: Client sees too many projects

**Solution:**
1. Review project access grants
2. Remove access from unrelated projects
3. Verify project isolation

### Issue: Client can edit tasks

**Solution:**
1. Verify user role is "Guest" (not "Member")
2. Check project permissions
3. Contact Linear support if issue persists

### Issue: Weekly reports not sending

**Solution:**
1. Check cron job is running
2. Verify email configuration
3. Check progress tracker is working
4. Review email logs for errors

---

## References

- [Linear Guest Users Documentation](https://linear.app/docs/guest-users)
- [Linear API Documentation](https://developers.linear.app/docs)
- [Linear Webhooks Guide](https://developers.linear.app/docs/webhooks)
- Progress Tracker: `src/meai/tracking/progress_tracker.py`
- Client Project Creator: `scripts/create_client_project.py`

---

**Last Updated:** 2026-05-15  
**Maintained by:** AIM Development Team
