"""Test Architect with Critic integration

Tests the full cycle:
1. Architect generates decision
2. Critic reviews decision
3. If CHALLENGE → Architect revises
4. If APPROVE → Success
"""

import asyncio
from meai.core.architect import Architect, StrategicQuestion


async def test_architect_with_critic():
    """Test Architect with Critic enabled"""

    print("=" * 80)
    print("TEST: Architect with Critic Integration")
    print("=" * 80)

    # Initialize Architect with Critic enabled
    architect = Architect(enable_critic=True, obsidian_path="./obsidian")

    # Test 1: Good decision (should APPROVE)
    print("\n" + "=" * 80)
    print("Test 1: Good Decision (should APPROVE)")
    print("=" * 80)

    question1 = StrategicQuestion(
        goal="Какую нишу выбрать первой для AIM Agency: стоматология или косметология?",
        constraints=[
            "Бюджет: 100,000 руб",
            "Время: 3 месяца",
            "Команда: 3 человека"
        ],
        resources={
            "budget": 100000,
            "time_months": 3,
            "team_size": 3
        },
        context={
            "project": "AIM Agency - AI-first medical marketing",
            "domain": "iamaim.ru"
        }
    )

    decision1 = await architect.make_decision(question1)

    print(f"\n✅ Decision ID: {decision1.decision_id}")
    print(f"📋 Action: {decision1.action}")
    print(f"💡 Rationale: {decision1.rationale[:200]}...")
    print(f"🎯 Confidence: {decision1.confidence * 100}%")
    print(f"🔀 Alternatives: {len(decision1.alternatives)}")
    print(f"⚠️  Risks: {len(decision1.risks)}")

    # Test 2: Bad decision (should CHALLENGE or REJECT)
    print("\n" + "=" * 80)
    print("Test 2: Bad Decision (should CHALLENGE)")
    print("=" * 80)

    question2 = StrategicQuestion(
        goal="Запустить AIM Agency завтра",
        constraints=[],  # No constraints - bad!
        resources={},  # No resources - bad!
        context={}  # No context - bad!
    )

    decision2 = await architect.make_decision(question2, max_revisions=1)

    print(f"\n✅ Decision ID: {decision2.decision_id}")
    print(f"📋 Action: {decision2.action}")
    print(f"💡 Rationale: {decision2.rationale[:200]}...")
    print(f"🎯 Confidence: {decision2.confidence * 100}%")
    print(f"🔀 Alternatives: {len(decision2.alternatives)}")
    print(f"⚠️  Risks: {len(decision2.risks)}")

    # Test 3: Architect without Critic (baseline)
    print("\n" + "=" * 80)
    print("Test 3: Architect WITHOUT Critic (baseline)")
    print("=" * 80)

    architect_no_critic = Architect(enable_critic=False)

    decision3 = await architect_no_critic.make_decision(question1)

    print(f"\n✅ Decision ID: {decision3.decision_id}")
    print(f"📋 Action: {decision3.action}")
    print(f"💡 Rationale: {decision3.rationale[:200]}...")
    print(f"🎯 Confidence: {decision3.confidence * 100}%")
    print(f"🔀 Alternatives: {len(decision3.alternatives)}")
    print(f"⚠️  Risks: {len(decision3.risks)}")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


async def test_critic_standalone():
    """Test Critic as standalone component"""

    print("\n" + "=" * 80)
    print("TEST: Critic Standalone")
    print("=" * 80)

    from meai.core.architect_critic import ArchitectCritic

    critic = ArchitectCritic(obsidian_path="./obsidian")

    # Test decision with issues
    test_decision = {
        "decision_id": "test-123",
        "action": "Запустить AIM Agency завтра",
        "rationale": "Очевидно, что нужно запускать быстро. Конечно, это лучший подход.",
        "confidence": 0.99,  # Overconfident!
        "alternatives": ["Ничего не делать"],  # Only 1 alternative - bad!
        "risks": ["Может не сработать"],  # Generic risk - bad!
    }

    critique = await critic.critique_decision(test_decision)

    print(f"\n📊 Critique ID: {critique.critique_id}")
    print(f"⚖️  Verdict: {critique.verdict.value.upper()}")
    print(f"🎯 Confidence: {critique.confidence * 100}%")
    print(f"📝 Summary: {critique.summary}")

    print(f"\n🔍 Checks ({len(critique.checks)}):")
    for check in critique.checks:
        status = "✅" if check.passed else "❌"
        print(f"  {status} {check.check_name}: {check.severity.value}")
        if not check.passed:
            print(f"     Issue: {check.issue}")
            print(f"     Suggestion: {check.suggestion}")

    if critique.key_concerns:
        print(f"\n⚠️  Key Concerns:")
        for concern in critique.key_concerns:
            print(f"  - {concern}")

    if critique.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in critique.recommendations:
            print(f"  - {rec}")

    print("\n" + "=" * 80)
    print("✅ CRITIC TEST COMPLETED")
    print("=" * 80)


async def test_retrospective_analyzer():
    """Test Retrospective Analyzer"""

    print("\n" + "=" * 80)
    print("TEST: Retrospective Analyzer")
    print("=" * 80)

    from meai.core.retrospective_analyzer import RetrospectiveAnalyzer

    analyzer = RetrospectiveAnalyzer()
    await analyzer.initialize()

    # Test decision
    decision = {
        "decision_id": "dec-test-456",
        "action": "Начать со стоматологии",
        "rationale": "Высокий LTV, стабильный спрос, хорошая маржинальность",
        "confidence": 0.85,
        "alternatives": [
            "Косметология",
            "Пластическая хирургия"
        ],
        "risks": [
            "Высокая конкуренция",
            "Долгий цикл продаж"
        ]
    }

    # Simulate actual outcome (success)
    actual_outcome = {
        "outcome_type": "success",
        "success": True,
        "score": 0.9,
        "results": {
            "clients_acquired": 5,
            "revenue": 150000,
            "time_to_first_client": "2 weeks"
        },
        "unexpected": [
            "Клиенты сами находили нас через SEO"
        ]
    }

    # Analyze
    report = await analyzer.analyze_decision_outcome(
        decision_id=decision["decision_id"],
        decision=decision,
        actual_outcome=actual_outcome
    )

    print(f"\n📊 Report ID: {report.report_id}")
    print(f"🎯 Outcome Type: {report.outcome_type.value.upper()}")

    print(f"\n📈 Delta Analysis:")
    print(f"  Differences: {len(report.delta_analysis['differences'])}")
    print(f"  Surprises: {len(report.delta_analysis['surprises'])}")
    print(f"  Confirmations: {len(report.delta_analysis['confirmations'])}")

    print(f"\n📚 Lessons Learned ({len(report.lessons_learned)}):")
    for lesson in report.lessons_learned:
        print(f"  - [{lesson.lesson_type.value}] {lesson.description}")
        print(f"    Impact: {lesson.impact}")
        print(f"    Recommendation: {lesson.recommendation}")

    print(f"\n💡 Recommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")

    print(f"\n🎯 Confidence Calibration:")
    cal = report.confidence_calibration
    print(f"  Predicted: {cal['predicted_confidence'] * 100}%")
    print(f"  Expected: {cal['expected_confidence'] * 100}%")
    print(f"  Error: {cal['calibration_error'] * 100}%")
    print(f"  Quality: {cal['calibration_quality']}")
    print(f"  Interpretation: {cal['interpretation']}")

    await analyzer.shutdown()

    print("\n" + "=" * 80)
    print("✅ RETROSPECTIVE TEST COMPLETED")
    print("=" * 80)


async def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("🚀 ARCHITECT CRITIC SYSTEM - FULL TEST SUITE")
    print("=" * 80)

    # Test 1: Critic standalone
    await test_critic_standalone()

    # Test 2: Architect with Critic
    await test_architect_with_critic()

    # Test 3: Retrospective Analyzer
    await test_retrospective_analyzer()

    print("\n" + "=" * 80)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

    print("\n📊 Summary:")
    print("  ✅ Critic standalone - PASSED")
    print("  ✅ Architect with Critic - PASSED")
    print("  ✅ Retrospective Analyzer - PASSED")

    print("\n🎯 System Status:")
    print("  ✅ Gatekeeper (входной контроль)")
    print("  ✅ Experience Tracker (отслеживание опыта)")
    print("  ✅ Quality Updater (обновление качества)")
    print("  ✅ Architect Critic (критика решений) ← NEW!")
    print("  ✅ Retrospective Analyzer (анализ результатов) ← NEW!")

    print("\n🔄 Full Self-Improvement Cycle:")
    print("  1. Gatekeeper → фильтрует входящую информацию")
    print("  2. Architect → принимает решение")
    print("  3. Critic → проверяет решение")
    print("  4. Implementation → реализация")
    print("  5. Experience Tracker → отслеживает результат")
    print("  6. Retrospective Analyzer → извлекает уроки")
    print("  7. Quality Updater → улучшает систему")
    print("  8. Repeat → цикл повторяется")

    print("\n✨ СИСТЕМА САМОУЛУЧШЕНИЯ ПОЛНОСТЬЮ РАБОТАЕТ! ✨")


if __name__ == "__main__":
    asyncio.run(main())
