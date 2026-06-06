"""
Test CI QA Validator
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "AIM" / "src"))
sys.path.insert(0, str(project_root / "src"))

from src.aim.subagents.competitive_intel.agents.ci_qa_validator import CIQAValidator
from meai.agents.base_agent import Task


async def test_qa_validator():
    """Test QA Validator with mock analysis result"""

    print("=" * 80)
    print("TEST: CI QA Validator")
    print("=" * 80)

    # Create validator
    validator = CIQAValidator(
        agent_id="ci-qa-validator-test",
        database_url="sqlite+aiosqlite:///./AIM/data/meai.db",
        vault_path="./AIM/obsidian/ci-qa-validator"
    )

    # Mock analysis result (good quality)
    good_analysis = {
        "name": "Good Competitor",
        "url": "https://example.com",
        "pages_analyzed": 50,
        "deep_analysis": {
            "quality_score": 75.5,
            "total_pages": 50,
            "seo_coverage": {
                "title": "50/50",
                "description": "45/50",
                "h1": "48/50"
            },
            "schema_coverage": "30/50",
            "cwv": {
                "pages_sampled": 10,
                "score": 65.0,
                "avg_lcp": 2.8,
                "avg_inp": 250,
                "avg_cls": 0.15
            },
            "mobile": {
                "pages_sampled": 10,
                "score": 80.0,
                "viewport_pass_rate": 100,
                "responsive_pass_rate": 90
            },
            "accessibility": {
                "pages_sampled": 10,
                "score": 70.0,
                "color_contrast_pass_rate": 80,
                "aria_pass_rate": 85
            },
            "security": {
                "pages_analyzed": 50,
                "score": 85.0,
                "https_rate": 100.0,
                "hsts_rate": 80.0
            }
        },
        "issues": {
            "total_issues": 15
        }
    }

    # Test 1: Good quality analysis
    print("\n" + "=" * 80)
    print("TEST 1: Good Quality Analysis")
    print("=" * 80)

    task1 = Task(
        task_id="test-qa-good",
        subtask_id="test-qa-good-1",
        parent_task_id="test-parent",
        action="validate_analysis",
        description="Test QA validation with good quality analysis",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    task1.payload = {"analysis_result": good_analysis}

    result1 = await validator.execute_task(task1)

    print("\n📊 RESULTS:")
    print(f"  Status: {result1.result['validation_status']}")
    print(f"  Quality Score: {result1.result['quality_report']['quality_score']:.1f}/100")
    print(f"  Completeness: {result1.result['completeness']['coverage_percent']:.1f}%")
    print(f"  Validity: {result1.result['validity']['valid_metrics']}/{result1.result['validity']['total_metrics']}")
    print(f"  Consistency: {len(result1.result['consistency']['issues'])} issues")

    # Test 2: Poor quality analysis (missing metrics)
    print("\n" + "=" * 80)
    print("TEST 2: Poor Quality Analysis (Missing Metrics)")
    print("=" * 80)

    poor_analysis = {
        "name": "Poor Competitor",
        "url": "https://example.com",
        "pages_analyzed": 50,
        "deep_analysis": {
            "quality_score": 45.0,
            "total_pages": 50,
            "seo_coverage": {
                "title": "30/50",
                "description": "20/50",
                "h1": "25/50"
            },
            "schema_coverage": "10/50"
            # Missing: CWV, Mobile, Accessibility, Security
        },
        "issues": {
            "total_issues": 35
        }
    }

    task2 = Task(
        task_id="test-qa-poor",
        subtask_id="test-qa-poor-1",
        parent_task_id="test-parent",
        action="validate_analysis",
        description="Test QA validation with poor quality analysis",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    task2.payload = {"analysis_result": poor_analysis}

    result2 = await validator.execute_task(task2)

    print("\n📊 RESULTS:")
    print(f"  Status: {result2.result['validation_status']}")
    print(f"  Quality Score: {result2.result['quality_report']['quality_score']:.1f}/100")
    print(f"  Completeness: {result2.result['completeness']['coverage_percent']:.1f}%")
    print(f"  Missing Metrics: {len(result2.result['completeness']['missing_metrics'])}")
    print(f"  Validity: {result2.result['validity']['valid_metrics']}/{result2.result['validity']['total_metrics']}")

    # Test 3: Analysis with anomalies
    print("\n" + "=" * 80)
    print("TEST 3: Analysis with Anomalies")
    print("=" * 80)

    anomaly_analysis = {
        "name": "Anomaly Competitor",
        "url": "https://example.com",
        "pages_analyzed": 50,
        "deep_analysis": {
            "quality_score": 150.0,  # ❌ Out of range!
            "total_pages": 50,
            "seo_coverage": {
                "title": "50/50",
                "description": "45/50",
                "h1": "48/50"
            },
            "schema_coverage": "30/50",
            "cwv": {
                "pages_sampled": 10,
                "score": 65.0,
                "avg_lcp": 25.0,  # ❌ Too high!
                "avg_cls": 1.5    # ❌ Out of range!
            },
            "mobile": {
                "score": 80.0
            }
        }
    }

    task3 = Task(
        task_id="test-qa-anomaly",
        subtask_id="test-qa-anomaly-1",
        parent_task_id="test-parent",
        action="validate_analysis",
        description="Test QA validation with anomalies",
        priority=1,
        status="received",
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    task3.payload = {"analysis_result": anomaly_analysis}

    result3 = await validator.execute_task(task3)

    print("\n📊 RESULTS:")
    print(f"  Status: {result3.result['validation_status']}")
    print(f"  Quality Score: {result3.result['quality_report']['quality_score']:.1f}/100")
    print(f"  Anomalies Found: {len(result3.result['validity']['anomalies'])}")
    for anomaly in result3.result['validity']['anomalies']:
        print(f"    ❌ {anomaly['metric']}: {anomaly['value']} - {anomaly['issue']}")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_qa_validator())
