"""
Operator Dashboard - CLI Dashboard for CI Analysis Results

Provides:
- Rich visualization of analysis results
- Competitor comparison
- Export to multiple formats (JSON, CSV, Markdown, HTML)
- History browsing
- Interactive mode

Usage:
    python3 AIM/scripts/operator_dashboard.py
    python3 AIM/scripts/operator_dashboard.py --analysis-id <id>
    python3 AIM/scripts/operator_dashboard.py --compare
    python3 AIM/scripts/operator_dashboard.py --export markdown
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "AIM" / "src"))
sys.path.insert(0, str(project_root / "src"))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.tree import Tree
    from rich import box
    from rich.markdown import Markdown
except ImportError:
    print("❌ Error: 'rich' library not installed")
    print("Install with: pip install rich")
    sys.exit(1)


class OperatorDashboard:
    """Operator Dashboard for CI Analysis Results"""

    def __init__(self):
        self.console = Console()
        self.data_dir = Path("AIM/data/ci-deep")
        self.golden_dataset_dir = Path("AIM/data/golden_dataset/results")

    def show_header(self):
        """Show dashboard header"""
        header = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                      🎯 OPERATOR DASHBOARD - CI SYSTEM                    ║
║                     Competitive Intelligence Analysis                     ║
╚═══════════════════════════════════════════════════════════════════════════╝
        """
        self.console.print(header, style="bold cyan")

    def list_analyses(self) -> List[Dict[str, Any]]:
        """List all available analyses"""
        if not self.data_dir.exists():
            return []

        analyses = []
        for file in sorted(self.data_dir.glob("deep_analysis_*.json"), reverse=True):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    analyses.append({
                        "file": file,
                        "filename": file.name,
                        "date": data.get("analysis_date", "unknown"),
                        "competitors": data.get("total_analyzed", 0),
                        "data": data
                    })
            except Exception:
                continue

        return analyses

    def show_analyses_list(self):
        """Show list of all analyses"""
        self.console.print("\n📊 Available Analyses\n", style="bold yellow")

        analyses = self.list_analyses()

        if not analyses:
            self.console.print("❌ No analyses found", style="red")
            return

        table = Table(title="Analysis History", box=box.ROUNDED)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Date", style="green", width=20)
        table.add_column("Competitors", style="yellow", width=12)
        table.add_column("File", style="blue")

        for i, analysis in enumerate(analyses, 1):
            date = datetime.fromisoformat(analysis["date"].replace("Z", "+00:00"))
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
            table.add_row(
                str(i),
                date_str,
                str(analysis["competitors"]),
                analysis["filename"]
            )

        self.console.print(table)

    def show_analysis_details(self, analysis_data: Dict[str, Any]):
        """Show detailed analysis results"""
        self.console.print("\n" + "=" * 80, style="cyan")
        self.console.print("📊 ANALYSIS DETAILS", style="bold cyan")
        self.console.print("=" * 80 + "\n", style="cyan")

        # Summary
        date = datetime.fromisoformat(analysis_data["analysis_date"].replace("Z", "+00:00"))
        self.console.print(f"📅 Date: {date.strftime('%Y-%m-%d %H:%M:%S')}", style="green")
        self.console.print(f"🏢 Competitors: {analysis_data['total_analyzed']}", style="yellow")
        self.console.print(f"📈 Quality: {analysis_data['analysis_quality']}", style="blue")
        self.console.print()

        # Each competitor
        for i, profile in enumerate(analysis_data["deep_profiles"], 1):
            self.show_competitor_profile(profile, i)

    def show_competitor_profile(self, profile: Dict[str, Any], index: int):
        """Show single competitor profile"""
        name = profile["name"]
        url = profile["url"]
        deep = profile["deep_analysis"]

        # Create panel
        panel_content = f"""
[bold cyan]🏢 {name}[/bold cyan]
[blue]🔗 {url}[/blue]

[yellow]📊 Quality Score: {deep['quality_score']:.1f}/100[/yellow]
[green]📄 Pages Analyzed: {profile['pages_analyzed']}[/green]
        """

        self.console.print(Panel(panel_content, title=f"Competitor #{index}", border_style="cyan"))

        # Metrics table
        table = Table(title="Metrics Breakdown", box=box.SIMPLE)
        table.add_column("Category", style="cyan", width=20)
        table.add_column("Score", style="yellow", width=10)
        table.add_column("Details", style="green")

        # SEO
        seo_coverage = deep.get("seo_coverage", {})
        seo_details = f"Title: {seo_coverage.get('title', 'N/A')}, Desc: {seo_coverage.get('description', 'N/A')}"
        table.add_row("SEO", "✓", seo_details)

        # CWV
        if "cwv" in deep:
            cwv = deep["cwv"]
            cwv_details = f"LCP: {cwv.get('avg_lcp', 0):.2f}s, CLS: {cwv.get('avg_cls', 0):.3f}"
            table.add_row("Core Web Vitals", f"{cwv['score']:.0f}/100", cwv_details)

        # Mobile
        if "mobile" in deep:
            mobile = deep["mobile"]
            mobile_details = f"Viewport: {mobile.get('viewport_pass_rate', 0):.0f}%, Responsive: {mobile.get('responsive_pass_rate', 0):.0f}%"
            table.add_row("Mobile", f"{mobile['score']:.0f}/100", mobile_details)

        # Accessibility
        if "accessibility" in deep:
            a11y = deep["accessibility"]
            a11y_details = f"Contrast: {a11y.get('color_contrast_pass_rate', 0):.0f}%, ARIA: {a11y.get('aria_pass_rate', 0):.0f}%"
            table.add_row("Accessibility", f"{a11y['score']:.0f}/100", a11y_details)

        # Security
        if "security" in deep:
            security = deep["security"]
            security_details = f"HTTPS: {security.get('https_rate', 0):.0f}%, HSTS: {security.get('hsts_rate', 0):.0f}%"
            table.add_row("Security", f"{security['score']:.0f}/100", security_details)

        self.console.print(table)

        # Issues
        if "issues" in profile:
            issues = profile["issues"]
            self.console.print(f"\n⚠️  Issues Found: {issues['total_issues']}", style="yellow")

            if issues['total_issues'] > 0:
                issues_table = Table(box=box.SIMPLE)
                issues_table.add_column("Severity", width=10)
                issues_table.add_column("Count", width=8)

                by_severity = issues.get("by_severity", {})
                if by_severity.get("critical", 0) > 0:
                    issues_table.add_row("[red]Critical[/red]", str(by_severity["critical"]))
                if by_severity.get("high", 0) > 0:
                    issues_table.add_row("[yellow]High[/yellow]", str(by_severity["high"]))
                if by_severity.get("medium", 0) > 0:
                    issues_table.add_row("[blue]Medium[/blue]", str(by_severity["medium"]))

                self.console.print(issues_table)

        self.console.print()

    def compare_competitors(self, analysis_data: Dict[str, Any]):
        """Compare all competitors side-by-side"""
        self.console.print("\n" + "=" * 80, style="cyan")
        self.console.print("📊 COMPETITOR COMPARISON", style="bold cyan")
        self.console.print("=" * 80 + "\n", style="cyan")

        profiles = analysis_data["deep_profiles"]

        # Comparison table
        table = Table(title="Quality Metrics Comparison", box=box.ROUNDED)
        table.add_column("Competitor", style="cyan", width=20)
        table.add_column("Quality", style="yellow", width=10)
        table.add_column("Pages", style="green", width=8)
        table.add_column("CWV", style="blue", width=8)
        table.add_column("Mobile", style="magenta", width=8)
        table.add_column("A11y", style="cyan", width=8)
        table.add_column("Security", style="green", width=10)

        for profile in profiles:
            name = profile["name"]
            deep = profile["deep_analysis"]

            quality = f"{deep['quality_score']:.1f}"
            pages = str(profile['pages_analyzed'])
            cwv = f"{deep.get('cwv', {}).get('score', 0):.0f}" if "cwv" in deep else "N/A"
            mobile = f"{deep.get('mobile', {}).get('score', 0):.0f}" if "mobile" in deep else "N/A"
            a11y = f"{deep.get('accessibility', {}).get('score', 0):.0f}" if "accessibility" in deep else "N/A"
            security = f"{deep.get('security', {}).get('score', 0):.0f}" if "security" in deep else "N/A"

            table.add_row(name, quality, pages, cwv, mobile, a11y, security)

        self.console.print(table)

        # Winner analysis
        self.console.print("\n🏆 Analysis Summary\n", style="bold yellow")

        # Best quality score
        best_quality = max(profiles, key=lambda p: p["deep_analysis"]["quality_score"])
        self.console.print(f"✨ Best Quality Score: {best_quality['name']} ({best_quality['deep_analysis']['quality_score']:.1f}/100)", style="green")

        # Most pages analyzed
        most_pages = max(profiles, key=lambda p: p["pages_analyzed"])
        self.console.print(f"📄 Most Pages Analyzed: {most_pages['name']} ({most_pages['pages_analyzed']} pages)", style="blue")

        # Best CWV
        profiles_with_cwv = [p for p in profiles if "cwv" in p["deep_analysis"]]
        if profiles_with_cwv:
            best_cwv = max(profiles_with_cwv, key=lambda p: p["deep_analysis"]["cwv"]["score"])
            self.console.print(f"⚡ Best Core Web Vitals: {best_cwv['name']} ({best_cwv['deep_analysis']['cwv']['score']:.0f}/100)", style="yellow")

    def export_to_markdown(self, analysis_data: Dict[str, Any], output_file: Path):
        """Export analysis to Markdown"""
        md_content = f"""# CI Analysis Report

**Date:** {analysis_data['analysis_date']}
**Competitors Analyzed:** {analysis_data['total_analyzed']}
**Quality:** {analysis_data['analysis_quality']}

---

## Competitors

"""

        for i, profile in enumerate(analysis_data["deep_profiles"], 1):
            name = profile["name"]
            url = profile["url"]
            deep = profile["deep_analysis"]

            md_content += f"""
### {i}. {name}

**URL:** {url}
**Quality Score:** {deep['quality_score']:.1f}/100
**Pages Analyzed:** {profile['pages_analyzed']}

#### Metrics

| Category | Score | Details |
|----------|-------|---------|
"""

            # SEO
            seo_coverage = deep.get("seo_coverage", {})
            md_content += f"| SEO | ✓ | Title: {seo_coverage.get('title', 'N/A')}, Desc: {seo_coverage.get('description', 'N/A')} |\n"

            # CWV
            if "cwv" in deep:
                cwv = deep["cwv"]
                md_content += f"| Core Web Vitals | {cwv['score']:.0f}/100 | LCP: {cwv.get('avg_lcp', 0):.2f}s, CLS: {cwv.get('avg_cls', 0):.3f} |\n"

            # Mobile
            if "mobile" in deep:
                mobile = deep["mobile"]
                md_content += f"| Mobile | {mobile['score']:.0f}/100 | Viewport: {mobile.get('viewport_pass_rate', 0):.0f}%, Responsive: {mobile.get('responsive_pass_rate', 0):.0f}% |\n"

            # Accessibility
            if "accessibility" in deep:
                a11y = deep["accessibility"]
                md_content += f"| Accessibility | {a11y['score']:.0f}/100 | Contrast: {a11y.get('color_contrast_pass_rate', 0):.0f}%, ARIA: {a11y.get('aria_pass_rate', 0):.0f}% |\n"

            # Security
            if "security" in deep:
                security = deep["security"]
                md_content += f"| Security | {security['score']:.0f}/100 | HTTPS: {security.get('https_rate', 0):.0f}%, HSTS: {security.get('hsts_rate', 0):.0f}% |\n"

            md_content += "\n"

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        self.console.print(f"\n✅ Exported to: {output_file}", style="green")

    def export_to_csv(self, analysis_data: Dict[str, Any], output_file: Path):
        """Export analysis to CSV"""
        import csv

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Name", "URL", "Quality Score", "Pages Analyzed",
                "CWV Score", "Mobile Score", "Accessibility Score", "Security Score"
            ])

            # Data
            for profile in analysis_data["deep_profiles"]:
                deep = profile["deep_analysis"]
                writer.writerow([
                    profile["name"],
                    profile["url"],
                    f"{deep['quality_score']:.1f}",
                    profile["pages_analyzed"],
                    f"{deep.get('cwv', {}).get('score', 0):.0f}" if "cwv" in deep else "N/A",
                    f"{deep.get('mobile', {}).get('score', 0):.0f}" if "mobile" in deep else "N/A",
                    f"{deep.get('accessibility', {}).get('score', 0):.0f}" if "accessibility" in deep else "N/A",
                    f"{deep.get('security', {}).get('score', 0):.0f}" if "security" in deep else "N/A"
                ])

        self.console.print(f"\n✅ Exported to: {output_file}", style="green")

    def interactive_mode(self):
        """Interactive dashboard mode"""
        self.show_header()

        while True:
            self.console.print("\n" + "=" * 80, style="cyan")
            self.console.print("📋 MAIN MENU", style="bold cyan")
            self.console.print("=" * 80 + "\n", style="cyan")

            self.console.print("1. 📊 List all analyses")
            self.console.print("2. 🔍 View analysis details")
            self.console.print("3. ⚖️  Compare competitors")
            self.console.print("4. 📤 Export to Markdown")
            self.console.print("5. 📤 Export to CSV")
            self.console.print("6. 🚪 Exit")

            choice = self.console.input("\n[cyan]Choose an option (1-6):[/cyan] ")

            if choice == "1":
                self.show_analyses_list()

            elif choice == "2":
                analyses = self.list_analyses()
                if not analyses:
                    self.console.print("❌ No analyses found", style="red")
                    continue

                self.show_analyses_list()
                idx = self.console.input("\n[cyan]Enter analysis number:[/cyan] ")
                try:
                    idx = int(idx) - 1
                    if 0 <= idx < len(analyses):
                        self.show_analysis_details(analyses[idx]["data"])
                    else:
                        self.console.print("❌ Invalid number", style="red")
                except ValueError:
                    self.console.print("❌ Invalid input", style="red")

            elif choice == "3":
                analyses = self.list_analyses()
                if not analyses:
                    self.console.print("❌ No analyses found", style="red")
                    continue

                self.show_analyses_list()
                idx = self.console.input("\n[cyan]Enter analysis number:[/cyan] ")
                try:
                    idx = int(idx) - 1
                    if 0 <= idx < len(analyses):
                        self.compare_competitors(analyses[idx]["data"])
                    else:
                        self.console.print("❌ Invalid number", style="red")
                except ValueError:
                    self.console.print("❌ Invalid input", style="red")

            elif choice == "4":
                analyses = self.list_analyses()
                if not analyses:
                    self.console.print("❌ No analyses found", style="red")
                    continue

                self.show_analyses_list()
                idx = self.console.input("\n[cyan]Enter analysis number:[/cyan] ")
                try:
                    idx = int(idx) - 1
                    if 0 <= idx < len(analyses):
                        output_file = Path(f"AIM/data/exports/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        self.export_to_markdown(analyses[idx]["data"], output_file)
                    else:
                        self.console.print("❌ Invalid number", style="red")
                except ValueError:
                    self.console.print("❌ Invalid input", style="red")

            elif choice == "5":
                analyses = self.list_analyses()
                if not analyses:
                    self.console.print("❌ No analyses found", style="red")
                    continue

                self.show_analyses_list()
                idx = self.console.input("\n[cyan]Enter analysis number:[/cyan] ")
                try:
                    idx = int(idx) - 1
                    if 0 <= idx < len(analyses):
                        output_file = Path(f"AIM/data/exports/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        self.export_to_csv(analyses[idx]["data"], output_file)
                    else:
                        self.console.print("❌ Invalid number", style="red")
                except ValueError:
                    self.console.print("❌ Invalid input", style="red")

            elif choice == "6":
                self.console.print("\n👋 Goodbye!", style="green")
                break

            else:
                self.console.print("❌ Invalid choice", style="red")


def main():
    """Main entry point"""
    dashboard = OperatorDashboard()
    dashboard.interactive_mode()


if __name__ == "__main__":
    main()
