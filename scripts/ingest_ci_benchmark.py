#!/usr/bin/env python3
"""
CI Research Ingest Script

Обрабатывает benchmark reports от CI Research Agent и сохраняет в Obsidian vault.

Usage:
    python scripts/ingest_ci_benchmark.py <benchmark_report.json>
    python scripts/ingest_ci_benchmark.py --industry "dental clinics" --report-path /path/to/report.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_benchmark_report(report_path: Path) -> Dict[str, Any]:
    """Загрузить benchmark report из JSON"""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_raw_benchmark(
    vault_path: Path,
    industry: str,
    report: Dict[str, Any]
) -> Path:
    """
    Сохранить raw benchmark в vault

    Returns:
        Path to saved benchmark directory
    """
    # Создать директорию для benchmark
    timestamp = datetime.now().strftime("%Y-%m-%d")
    industry_slug = industry.lower().replace(" ", "-")
    benchmark_dir = vault_path / "raw" / "benchmarks" / f"{timestamp}_{industry_slug}"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    # Сохранить manifest
    manifest = {
        "industry": industry,
        "timestamp": timestamp,
        "competitors_count": len(report.get("competitor_profiles", [])),
        "growth_laws_count": len(report.get("growth_laws", [])),
        "sales_laws_count": len(report.get("sales_laws", [])),
        "copy_patterns_count": len(report.get("do_copy", [])),
        "ignore_patterns_count": len(report.get("do_ignore", [])),
        "status": "processed"
    }

    with open(benchmark_dir / "manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Сохранить полный отчёт
    with open(benchmark_dir / "report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Сохранить competitor profiles
    competitors_dir = benchmark_dir / "competitors"
    competitors_dir.mkdir(exist_ok=True)

    for profile in report.get("competitor_profiles", []):
        domain = profile.get("domain", "unknown")
        domain_slug = domain.replace(".", "_")
        with open(competitors_dir / f"{domain_slug}.json", 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

    print(f"✅ Raw benchmark saved: {benchmark_dir}")
    return benchmark_dir


def create_project_page(
    vault_path: Path,
    industry: str,
    report: Dict[str, Any]
) -> Path:
    """Создать project page в wiki/projects/"""

    industry_slug = industry.lower().replace(" ", "-")
    project_path = vault_path / "wiki" / "projects" / f"{industry_slug}.md"

    # Frontmatter
    frontmatter = f"""---
title: "{industry.title()} Benchmark"
type: project
created: {datetime.now().strftime("%Y-%m-%dT%H:%M")}
updated: {datetime.now().strftime("%Y-%m-%dT%H:%M")}
status: active
tags: [benchmark, {industry_slug}]
sources: [[raw/benchmarks/{datetime.now().strftime("%Y-%m-%d")}_{industry_slug}]]
---

"""

    # Content
    competitors = report.get("competitor_profiles", [])
    growth_laws = report.get("growth_laws", [])
    copy_patterns = report.get("do_copy", [])
    ignore_patterns = report.get("do_ignore", [])
    roadmap = report.get("sequencing_roadmap", [])

    content = f"""# {industry.title()} Benchmark

**Industry:** {industry}
**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Competitors Analyzed:** {len(competitors)}

---

## Executive Summary

**Key Findings:**
- {len(growth_laws)} Growth Laws identified (prevalence ≥30%)
- {len(copy_patterns)} Copy Patterns (ICE > 200)
- {len(ignore_patterns)} Ignore Patterns (unique advantages)
- {len(roadmap)} Implementation Phases

---

## Competitors

"""

    for profile in competitors:
        domain = profile.get("domain", "unknown")
        content += f"- **{domain}**\n"
        content += f"  - Acquisition: {', '.join(profile.get('acquisition_channels', []))}\n"
        content += f"  - ACV: ${profile.get('acv', 0):,.0f}\n"
        content += f"  - CAC: ${profile.get('cac', 0):,.0f}\n"
        content += f"  - LTV: ${profile.get('ltv', 0):,.0f}\n"
        content += f"  - Payback: {profile.get('payback_period', 0)} months\n\n"

    content += """---

## Growth Laws

See [[growth-laws]] for full analysis.

"""

    for law in growth_laws[:5]:  # Top 5
        content += f"- **{law.get('law', 'Unknown')}** (prevalence: {law.get('prevalence', 0):.0%})\n"

    content += """
---

## Copy Patterns

See [[copy-patterns]] in decisions/ for implementation plan.

"""

    for pattern in copy_patterns[:5]:  # Top 5
        content += f"- **{pattern.get('pattern', 'Unknown')}** (ICE: {pattern.get('ice_score', 0)})\n"

    content += """
---

## Ignore Patterns

See [[ignore-patterns]] in decisions/ for rationale.

"""

    for pattern in ignore_patterns[:3]:  # Top 3
        content += f"- **{pattern.get('pattern', 'Unknown')}** — {pattern.get('reason', 'N/A')}\n"

    content += """
---

## Implementation Roadmap

See [[sequencing-roadmap]] in decisions/ for full plan.

"""

    for phase in roadmap:
        content += f"- **Phase {phase.get('phase', 0)}** ({phase.get('duration', 'N/A')}): {len(phase.get('patterns', []))} patterns\n"

    content += """
---

## Related Pages

- [[growth-laws]] — Growth Laws analysis
- [[sales-laws]] — Sales Laws analysis
- [[archetypes]] — Industry Archetypes
- [[copy-patterns]] — What to copy
- [[ignore-patterns]] — What to ignore
- [[sequencing-roadmap]] — Implementation plan

---

**Version:** 1.0.0
**Status:** ✅ Active
"""

    # Write file
    with open(project_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter + content)

    print(f"✅ Project page created: {project_path}")
    return project_path


def update_log(vault_path: Path, industry: str, report: Dict[str, Any]) -> None:
    """Обновить wiki/log.md"""

    log_path = vault_path / "wiki" / "log.md"

    # Прочитать существующий log
    with open(log_path, 'r', encoding='utf-8') as f:
        log_content = f.read()

    # Добавить новую запись
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    industry_slug = industry.lower().replace(" ", "-")

    new_entry = f"""
## [{timestamp}] ingest | {industry.title()} benchmark

**Operation:** Benchmark ingest

**Details:**
- Industry: {industry}
- Competitors: {len(report.get("competitor_profiles", []))}
- Growth Laws: {len(report.get("growth_laws", []))}
- Copy Patterns: {len(report.get("do_copy", []))} (ICE > 200)
- Output: [[{industry_slug}]]

**Status:** ✅ Completed

---
"""

    # Вставить после заголовка "# CI Research Vault Log"
    lines = log_content.split('\n')
    insert_index = None
    for i, line in enumerate(lines):
        if line.startswith('---') and i > 10:  # Найти первый разделитель после frontmatter
            insert_index = i + 1
            break

    if insert_index:
        lines.insert(insert_index, new_entry)
        log_content = '\n'.join(lines)
    else:
        log_content += new_entry

    # Записать обновлённый log
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(log_content)

    print(f"✅ Log updated: {log_path}")


def update_index(vault_path: Path, industry: str, report: Dict[str, Any]) -> None:
    """Обновить wiki/index.md"""

    index_path = vault_path / "wiki" / "index.md"

    # Прочитать существующий index
    with open(index_path, 'r', encoding='utf-8') as f:
        index_content = f.read()

    # Обновить статистику
    # TODO: Реализовать полное обновление статистики
    # Пока просто добавим проект в список

    industry_slug = industry.lower().replace(" ", "-")
    project_entry = f"- [[{industry_slug}]] — {len(report.get('competitor_profiles', []))} competitors, {len(report.get('do_copy', []))} copy patterns\n"

    # Найти секцию Projects и добавить
    if "## Projects (0)" in index_content:
        index_content = index_content.replace(
            "## Projects (0)\n\n*No projects yet.",
            f"## Projects (1)\n\n{project_entry}\n*First benchmark ingested!"
        )

    # Записать обновлённый index
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    print(f"✅ Index updated: {index_path}")


def main():
    parser = argparse.ArgumentParser(description="Ingest CI Research benchmark report")
    parser.add_argument("report_path", type=str, help="Path to benchmark report JSON")
    parser.add_argument("--industry", type=str, help="Industry name (e.g., 'dental clinics')")
    parser.add_argument("--vault", type=str, default="AIM/obsidian/ci-research", help="Path to vault")

    args = parser.parse_args()

    # Paths
    report_path = Path(args.report_path)
    vault_path = Path(args.vault)

    if not report_path.exists():
        print(f"❌ Error: Report not found: {report_path}")
        return 1

    if not vault_path.exists():
        print(f"❌ Error: Vault not found: {vault_path}")
        return 1

    # Load report
    print(f"📖 Loading benchmark report: {report_path}")
    report = load_benchmark_report(report_path)

    # Extract industry
    industry = args.industry or report.get("industry", "unknown")

    print(f"\n🔄 Processing benchmark for: {industry}")
    print(f"   Competitors: {len(report.get('competitor_profiles', []))}")
    print(f"   Growth Laws: {len(report.get('growth_laws', []))}")
    print(f"   Copy Patterns: {len(report.get('do_copy', []))}")

    # Ingest workflow
    print("\n📥 Starting ingest workflow...\n")

    # 1. Save raw benchmark
    benchmark_dir = save_raw_benchmark(vault_path, industry, report)

    # 2. Create project page
    project_path = create_project_page(vault_path, industry, report)

    # 3. Update log
    update_log(vault_path, industry, report)

    # 4. Update index
    update_index(vault_path, industry, report)

    print(f"\n✅ Ingest completed successfully!")
    print(f"\n📊 Summary:")
    print(f"   Raw data: {benchmark_dir}")
    print(f"   Project page: {project_path}")
    print(f"   Vault: {vault_path}")

    return 0


if __name__ == "__main__":
    exit(main())
