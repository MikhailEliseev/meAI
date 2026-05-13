#!/usr/bin/env python3
"""Teacher Agent CLI - Audit and upgrade subagents."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.teacher.teacher_agent import TeacherAgent


def audit_subagent(agent_name: str):
    """Audit a single subagent."""
    teacher = TeacherAgent()

    # Find subagent file
    subagent_path = Path(f"AIM/src/aim/subagents/{agent_name}.py")
    if not subagent_path.exists():
        print(f"❌ Subagent not found: {agent_name}")
        return

    print(f"🔍 Auditing {agent_name}...")

    # Run audit
    result = teacher.audit_subagent(subagent_path)

    # Generate report
    report = teacher.report_generator.generate(result)

    # Save report
    report_path = Path(f"AIM/reports/teacher/{agent_name}_audit.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    teacher.report_generator.save(result, report_path)

    # Print summary
    print(f"\n📊 Score: {result.score:.1f}/100")
    print(f"📝 Report saved to: {report_path}")

    if result.score >= 80:
        print("✅ PASS - Subagent follows best practices")
    elif result.score >= 60:
        print("⚠️  NEEDS IMPROVEMENT - Some gaps detected")
    else:
        print("❌ FAIL - Critical gaps detected")


def audit_all():
    """Audit all subagents."""
    teacher = TeacherAgent()

    print("🔍 Auditing all subagents...")

    results = teacher.audit_all()

    print(f"\n📊 Audited {len(results)} subagents:")

    for result in results:
        status = "✅" if result.score >= 80 else "⚠️" if result.score >= 60 else "❌"
        print(f"{status} {result.subagent_name}: {result.score:.1f}/100")

    # Save summary report
    summary_path = Path("AIM/reports/teacher/audit_summary.md")
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with summary_path.open("w") as f:
        f.write("# Teacher Agent Audit Summary\n\n")
        f.write(f"**Total Subagents:** {len(results)}\n\n")

        for result in results:
            f.write(f"## {result.subagent_name}\n")
            f.write(f"**Score:** {result.score:.1f}/100\n")
            f.write(f"**Gaps:** {len(result.gaps)}\n\n")

    print(f"\n📝 Summary saved to: {summary_path}")


def upgrade_subagent(agent_name: str):
    """Upgrade a subagent."""
    teacher = TeacherAgent()

    # Find subagent file
    subagent_path = Path(f"AIM/src/aim/subagents/{agent_name}.py")
    if not subagent_path.exists():
        print(f"❌ Subagent not found: {agent_name}")
        return

    print(f"🔧 Upgrading {agent_name}...")

    # Run audit first
    result = teacher.audit_subagent(subagent_path)

    if not result.gaps:
        print("✅ No gaps detected - nothing to upgrade")
        return

    # Apply upgrade
    success = teacher.upgrade_subagent(subagent_path, result)

    if success:
        print(f"✅ Upgrade successful - {len(result.gaps)} patterns applied")
    else:
        print("❌ Upgrade failed")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Teacher Agent - Audit and upgrade subagents"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a single subagent")
    audit_parser.add_argument("agent_name", help="Subagent name (without .py)")

    # audit-all command
    subparsers.add_parser("audit-all", help="Audit all subagents")

    # upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade a subagent")
    upgrade_parser.add_argument("agent_name", help="Subagent name (without .py)")

    args = parser.parse_args()

    if args.command == "audit":
        audit_subagent(args.agent_name)
    elif args.command == "audit-all":
        audit_all()
    elif args.command == "upgrade":
        upgrade_subagent(args.agent_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
