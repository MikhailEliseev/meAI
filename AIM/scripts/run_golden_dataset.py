"""
Golden Dataset Runner

Запускает CI Deep Analyzer на всех сайтах из Golden Dataset.
Сохраняет результаты для последующей валидации.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "AIM" / "src"))
sys.path.insert(0, str(project_root / "src"))

from aim.subagents.competitive_intel.agents.ci_deep_analyzer import CIDeepAnalyzer
from aim.subagents.competitive_intel.agents.ci_qa_validator import CIQAValidator
from meai.agents.base_agent import Task

# Import config
sys.path.insert(0, str(project_root / "AIM" / "data" / "golden_dataset"))
from config import GOLDEN_DATASET


async def run_golden_dataset_analysis():
    """Run CI Deep Analyzer on all sites in Golden Dataset"""

    print("=" * 80)
    print("GOLDEN DATASET ANALYSIS")
    print("=" * 80)
    print(f"Total sites: {GOLDEN_DATASET['total_sites']}")
    print(f"Categories: {GOLDEN_DATASET['categories']}")
    print()

    # Create agents
    analyzer = CIDeepAnalyzer(
        agent_id="ci-deep-analyzer-golden",
        database_url="sqlite+aiosqlite:///./AIM/data/meai.db",
        vault_path="./AIM/obsidian/ci-deep-analyzer",
        max_pages=50  # Limit for faster testing
    )

    validator = CIQAValidator(
        agent_id="ci-qa-validator-golden",
        database_url="sqlite+aiosqlite:///./AIM/data/meai.db",
        vault_path="./AIM/obsidian/ci-qa-validator"
    )

    results = []
    output_dir = project_root / "AIM" / "data" / "golden_dataset" / "results"
    output_dir.mkdir(exist_ok=True)

    # Process each site
    for i, site in enumerate(GOLDEN_DATASET["sites"], 1):
        print(f"\n{'=' * 80}")
        print(f"[{i}/{GOLDEN_DATASET['total_sites']}] {site['name']}")
        print(f"{'=' * 80}")
        print(f"URL: {site['url']}")
        print(f"Category: {site['category']}")
        print(f"Expected Quality Score: {site['expected_metrics']['quality_score']}")
        print()

        try:
            # Run analysis
            task = Task(
                task_id=f"golden-{site['id']}",
                subtask_id=f"golden-{site['id']}-1",
                parent_task_id="golden-dataset",
                action="analyze_deeply",
                description=f"Golden dataset analysis: {site['name']}",
                priority=1,
                status="received",
                created_at=datetime.now(),
                received_at=datetime.now()
            )
            task.payload = {
                "competitors": [
                    {"name": site["name"], "url": site["url"]}
                ]
            }

            print(f"🔍 Running CI Deep Analyzer...")
            analysis_result = await analyzer.execute_task(task)

            if analysis_result.status == "success":
                competitor_profile = analysis_result.result["deep_profiles"][0]

                print(f"✅ Analysis completed!")
                print(f"  Pages analyzed: {competitor_profile['pages_analyzed']}")
                print(f"  Quality Score: {competitor_profile['deep_analysis']['quality_score']:.1f}")

                # Run QA validation
                print(f"\n🔍 Running QA Validator...")
                qa_task = Task(
                    task_id=f"golden-qa-{site['id']}",
                    subtask_id=f"golden-qa-{site['id']}-1",
                    parent_task_id="golden-dataset",
                    action="validate_analysis",
                    description=f"QA validation: {site['name']}",
                    priority=1,
                    status="received",
                    created_at=datetime.now(),
                    received_at=datetime.now()
                )
                qa_task.payload = {"analysis_result": competitor_profile}

                qa_result = await validator.execute_task(qa_task)

                if qa_result.status == "completed":
                    print(f"✅ QA Validation: {qa_result.result['validation_status'].upper()}")
                    print(f"  QA Score: {qa_result.result['quality_report']['quality_score']:.1f}/100")

                # Save result
                result = {
                    "site": site,
                    "analysis": competitor_profile,
                    "qa_validation": qa_result.result if qa_result.status == "completed" else None,
                    "analyzed_at": datetime.now().isoformat()
                }
                results.append(result)

                # Save individual result
                result_file = output_dir / f"{site['id']}.json"
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Saved: {result_file}")

            else:
                print(f"❌ Analysis failed: {analysis_result.error}")
                results.append({
                    "site": site,
                    "error": analysis_result.error,
                    "analyzed_at": datetime.now().isoformat()
                })

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "site": site,
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            })

        # Delay between sites to be respectful
        if i < GOLDEN_DATASET['total_sites']:
            print(f"\n⏳ Waiting 5 seconds before next site...")
            await asyncio.sleep(5)

    # Save summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    successful = sum(1 for r in results if "analysis" in r)
    failed = len(results) - successful

    print(f"Total sites: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if successful > 0:
        avg_quality = sum(r["analysis"]["deep_analysis"]["quality_score"] for r in results if "analysis" in r) / successful
        avg_pages = sum(r["analysis"]["pages_analyzed"] for r in results if "analysis" in r) / successful

        print(f"\nAverage Quality Score: {avg_quality:.1f}")
        print(f"Average Pages Analyzed: {avg_pages:.0f}")

    # Save summary
    summary = {
        "dataset_version": GOLDEN_DATASET["version"],
        "analyzed_at": datetime.now().isoformat(),
        "total_sites": len(results),
        "successful": successful,
        "failed": failed,
        "results": results
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Summary saved: {summary_file}")
    print(f"\n✅ Golden Dataset analysis completed!")


if __name__ == "__main__":
    asyncio.run(run_golden_dataset_analysis())
