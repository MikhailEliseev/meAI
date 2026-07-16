"""End-to-end test of Experience Learning system"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.learning.experience_tracker import ExperienceTracker
from meai.learning.quality_updater import QualityUpdater
from meai.learning.deprecation_manager import DeprecationManager
from meai.learning.learning_analytics import LearningAnalytics


def print_header(title: str):
    """Print section header"""
    print()
    print("=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"📋 {message}")


async def test_1_initialize_system():
    """Test 1: Initialize experience learning system"""
    print_header("Initialize Experience Learning System")

    try:
        tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
        await tracker.initialize()
        print_success("ExperienceTracker initialized")

        updater = QualityUpdater(
            experience_tracker=tracker,
            database_url="sqlite+aiosqlite:///:memory:",
        )
        await updater.initialize()
        print_success("QualityUpdater initialized")

        deprecation = DeprecationManager(
            experience_tracker=tracker,
            database_url="sqlite+aiosqlite:///:memory:",
        )
        await deprecation.initialize()
        print_success("DeprecationManager initialized")

        analytics = LearningAnalytics(
            experience_tracker=tracker,
            quality_updater=updater,
            deprecation_manager=deprecation,
        )
        print_success("LearningAnalytics initialized")

        return {
            "tracker": tracker,
            "updater": updater,
            "deprecation": deprecation,
            "analytics": analytics,
        }

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        raise


async def test_2_record_experiences(components):
    """Test 2: Record task experiences"""
    print_header("Record Task Experiences")

    tracker = components["tracker"]

    # Simulate 3 knowledge items with different performance
    print_info("Recording experiences for 3 knowledge items...")

    # Excellent performer
    for i in range(30):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-excellent-{i}",
            knowledge_ids=["knowledge-excellent"],
            outcome="success",
            outcome_score=0.95,
        )
    print_success("Recorded 30 excellent experiences")

    # Average performer
    for i in range(30):
        outcome = "success" if i < 20 else "failure"
        score = 0.7 if outcome == "success" else 0.3

        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-average-{i}",
            knowledge_ids=["knowledge-average"],
            outcome=outcome,
            outcome_score=score,
        )
    print_success("Recorded 30 average experiences")

    # Poor performer
    for i in range(30):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-poor-{i}",
            knowledge_ids=["knowledge-poor"],
            outcome="failure",
            outcome_score=0.15,
        )
    print_success("Recorded 30 poor experiences")

    # Get stats
    excellent_stats = await tracker.get_knowledge_stats("knowledge-excellent")
    average_stats = await tracker.get_knowledge_stats("knowledge-average")
    poor_stats = await tracker.get_knowledge_stats("knowledge-poor")

    print()
    print_info(f"Excellent: {excellent_stats['success_rate']:.1%} success, {excellent_stats['average_score']:.2f} avg score")
    print_info(f"Average: {average_stats['success_rate']:.1%} success, {average_stats['average_score']:.2f} avg score")
    print_info(f"Poor: {poor_stats['success_rate']:.1%} success, {poor_stats['average_score']:.2f} avg score")

    return True


async def test_3_update_quality_scores(components):
    """Test 3: Update quality scores based on experience"""
    print_header("Update Quality Scores")

    updater = components["updater"]

    print_info("Calculating new quality scores...")

    # Update excellent knowledge
    excellent_result = await updater.update_knowledge_quality(
        knowledge_id="knowledge-excellent",
        current_score=7.0,
    )
    print_success(f"Excellent: {excellent_result['old_score']:.1f} → {excellent_result['new_score']:.1f} ({excellent_result['reason']})")

    # Update average knowledge
    average_result = await updater.update_knowledge_quality(
        knowledge_id="knowledge-average",
        current_score=7.0,
    )
    print_success(f"Average: {average_result['old_score']:.1f} → {average_result['new_score']:.1f} ({average_result['reason']})")

    # Update poor knowledge
    poor_result = await updater.update_knowledge_quality(
        knowledge_id="knowledge-poor",
        current_score=7.0,
    )
    print_success(f"Poor: {poor_result['old_score']:.1f} → {poor_result['new_score']:.1f} ({poor_result['reason']})")

    return {
        "excellent_score": excellent_result["new_score"],
        "average_score": average_result["new_score"],
        "poor_score": poor_result["new_score"],
    }


async def test_4_check_deprecation(components, scores):
    """Test 4: Check deprecation candidates"""
    print_header("Check Deprecation Candidates")

    deprecation = components["deprecation"]

    print_info("Checking which knowledge should be deprecated...")

    # Check excellent
    should_dep_excellent, reason_excellent = await deprecation.should_deprecate(
        knowledge_id="knowledge-excellent",
        current_quality=scores["excellent_score"],
    )
    print_info(f"Excellent: {'DEPRECATE' if should_dep_excellent else 'KEEP'} - {reason_excellent}")

    # Check average
    should_dep_average, reason_average = await deprecation.should_deprecate(
        knowledge_id="knowledge-average",
        current_quality=scores["average_score"],
    )
    print_info(f"Average: {'DEPRECATE' if should_dep_average else 'KEEP'} - {reason_average}")

    # Check poor
    should_dep_poor, reason_poor = await deprecation.should_deprecate(
        knowledge_id="knowledge-poor",
        current_quality=scores["poor_score"],
    )
    print_info(f"Poor: {'DEPRECATE' if should_dep_poor else 'KEEP'} - {reason_poor}")

    # Deprecate poor performer
    if should_dep_poor:
        print()
        print_info("Deprecating poor performer...")
        result = await deprecation.deprecate_knowledge(
            knowledge_id="knowledge-poor",
            reason=reason_poor,
            current_quality=scores["poor_score"],
        )
        print_success(f"Deprecated: {result['knowledge_id']}")

    return True


async def test_5_analytics_insights(components):
    """Test 5: Get analytics insights"""
    print_header("Analytics Insights")

    analytics = components["analytics"]

    # System health
    print_info("Getting system health...")
    health = await analytics.get_system_health()
    print_success(f"Health Score: {health['health_score']}/10")
    print_info(f"   Success Rate: {health['overall_success_rate']:.1%}")
    print_info(f"   Avg Score: {health['average_outcome_score']:.2f}")
    print_info(f"   Deprecated: {health['active_deprecated']}")

    print()

    # Knowledge reports
    print_info("Getting knowledge performance reports...")

    excellent_report = await analytics.get_knowledge_performance_report("knowledge-excellent")
    print_success(f"Excellent: Grade {excellent_report['performance_grade']}")
    print_info(f"   Recommendations: {', '.join(excellent_report['recommendations'])}")

    average_report = await analytics.get_knowledge_performance_report("knowledge-average")
    print_success(f"Average: Grade {average_report['performance_grade']}")
    print_info(f"   Recommendations: {', '.join(average_report['recommendations'])}")

    poor_report = await analytics.get_knowledge_performance_report("knowledge-poor")
    print_success(f"Poor: Grade {poor_report['performance_grade']}")
    print_info(f"   Recommendations: {', '.join(poor_report['recommendations'])}")

    print()

    # Magister performance
    print_info("Getting Magister performance...")
    magister_report = await analytics.get_magister_performance_report("seo-magister-1")
    print_success(f"SEO Magister: Grade {magister_report['performance_grade']}")
    print_info(f"   Total Tasks: {magister_report['total_tasks']}")
    print_info(f"   Success Rate: {magister_report['success_rate']:.1%}")
    print_info(f"   Avg Score: {magister_report['average_score']:.2f}")

    print()

    # Top performers
    print_info("Getting top performers...")
    top_performers = await analytics.get_top_performing_knowledge(limit=3, min_usage=10)
    for i, performer in enumerate(top_performers, 1):
        print_success(f"#{i}: {performer['knowledge_id']}")
        print_info(f"   Performance: {performer['performance_score']:.2f}")
        print_info(f"   Success Rate: {performer['success_rate']:.1%}")

    return True


async def main():
    """Run all tests"""
    print()
    print("🧪 Testing Experience Learning System")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_passed = True

    try:
        # Test 1: Initialize
        components = await test_1_initialize_system()

        # Test 2: Record experiences
        if not await test_2_record_experiences(components):
            all_passed = False

        # Test 3: Update quality
        scores = await test_3_update_quality_scores(components)

        # Test 4: Check deprecation
        if not await test_4_check_deprecation(components, scores):
            all_passed = False

        # Test 5: Analytics
        if not await test_5_analytics_insights(components):
            all_passed = False

        # Cleanup
        await components["tracker"].shutdown()
        await components["updater"].shutdown()
        await components["deprecation"].shutdown()

    except Exception as e:
        print_error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Final result
    print()
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
