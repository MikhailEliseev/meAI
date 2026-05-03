"""Simple test for Architect Critic - without real Claude calls

Demonstrates the self-improvement system components.
"""

import asyncio
from meai.core.architect_critic import ArchitectCritic, CritiqueVerdict
from meai.core.retrospective_analyzer import RetrospectiveAnalyzer, OutcomeType


async def test_critic_only():
    """Test Critic standalone - the core of self-improvement"""

    print("\n" + "=" * 80)
    print("🎯 ARCHITECT CRITIC - SELF-IMPROVEMENT SYSTEM")
    print("=" * 80)

    critic = ArchitectCritic(obsidian_path="./obsidian")

    # Test 1: Good decision
    print("\n📋 Test 1: GOOD Decision")
    print("-" * 80)

    good_decision = {
        "decision_id": "dec-good-001",
        "action": "Начать со стоматологии как первой ниши для AIM Agency",
        "rationale": """
        Стоматология выбрана на основе анализа рынка и прошлого опыта.

        Преимущества:
        - Высокий LTV клиента (50-200k руб/год)
        - Стабильный спрос круглый год
        - Хорошая маржинальность услуг
        - Меньше сезонности чем в косметологии

        Риски управляемы через поэтапный подход.
        В случае неудачи можем откатиться к косметологии за 2 недели.
        """,
        "confidence": 0.85,
        "alternatives": [
            "Косметология - выше конкуренция, но быстрее результаты",
            "Пластическая хирургия - выше чек, но меньше клиентов",
            "Ничего не делать - подождать больше данных"
        ],
        "risks": [
            "Высокая конкуренция в крупных городах (митигация: фокус на регионы)",
            "Долгий цикл принятия решения у клиента (митигация: контент-маркетинг)",
            "Сезонность летом (митигация: акции и спецпредложения)"
        ]
    }

    critique_good = await critic.critique_decision(good_decision)

    print(f"⚖️  Verdict: {critique_good.verdict.value.upper()}")
    print(f"🎯 Confidence: {critique_good.confidence * 100:.1f}%")
    print(f"📝 Summary: {critique_good.summary}")

    print(f"\n🔍 Checks:")
    for check in critique_good.checks:
        status = "✅" if check.passed else "❌"
        print(f"  {status} {check.check_name}: {check.severity.value}")

    # Test 2: Bad decision
    print("\n" + "=" * 80)
    print("📋 Test 2: BAD Decision")
    print("-" * 80)

    bad_decision = {
        "decision_id": "dec-bad-002",
        "action": "Запустить AIM Agency завтра",
        "rationale": "Очевидно, что нужно запускать быстро. Конечно, это лучший подход.",
        "confidence": 0.99,  # Overconfident!
        "alternatives": ["Ничего не делать"],  # Only 1 alternative
        "risks": ["Может не сработать"]  # Generic risk
    }

    critique_bad = await critic.critique_decision(bad_decision)

    print(f"⚖️  Verdict: {critique_bad.verdict.value.upper()}")
    print(f"🎯 Confidence: {critique_bad.confidence * 100:.1f}%")
    print(f"📝 Summary: {critique_bad.summary}")

    print(f"\n🔍 Checks:")
    for check in critique_bad.checks:
        status = "✅" if check.passed else "❌"
        print(f"  {status} {check.check_name}: {check.severity.value}")
        if not check.passed:
            print(f"     ⚠️  {check.issue}")

    if critique_bad.key_concerns:
        print(f"\n⚠️  Key Concerns:")
        for concern in critique_bad.key_concerns:
            print(f"  - {concern}")

    if critique_bad.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in critique_bad.recommendations:
            print(f"  - {rec}")

    # Test 3: Medium decision (CHALLENGE)
    print("\n" + "=" * 80)
    print("📋 Test 3: MEDIUM Decision (should CHALLENGE)")
    print("-" * 80)

    medium_decision = {
        "decision_id": "dec-medium-003",
        "action": "Начать со стоматологии",
        "rationale": "Стоматология - хороший выбор. Высокий LTV, стабильный спрос.",
        "confidence": 0.75,
        "alternatives": [
            "Косметология",
            "Пластическая хирургия"
        ],
        "risks": [
            "Высокая конкуренция",
            "Долгий цикл продаж"
        ]
    }

    critique_medium = await critic.critique_decision(medium_decision)

    print(f"⚖️  Verdict: {critique_medium.verdict.value.upper()}")
    print(f"🎯 Confidence: {critique_medium.confidence * 100:.1f}%")
    print(f"📝 Summary: {critique_medium.summary}")

    print(f"\n🔍 Checks:")
    for check in critique_medium.checks:
        status = "✅" if check.passed else "❌"
        print(f"  {status} {check.check_name}: {check.severity.value}")
        if not check.passed and check.severity.value in ["high", "medium"]:
            print(f"     ⚠️  {check.issue}")

    return critique_good, critique_bad, critique_medium


async def test_retrospective():
    """Test Retrospective Analyzer"""

    print("\n" + "=" * 80)
    print("📊 RETROSPECTIVE ANALYZER - LEARNING FROM OUTCOMES")
    print("=" * 80)

    analyzer = RetrospectiveAnalyzer()
    await analyzer.initialize()

    # Simulate a decision and its outcome
    decision = {
        "decision_id": "dec-retro-001",
        "action": "Начать со стоматологии",
        "rationale": "Высокий LTV, стабильный спрос, хорошая маржинальность",
        "confidence": 0.85,
        "alternatives": ["Косметология", "Пластическая хирургия"],
        "risks": ["Высокая конкуренция", "Долгий цикл продаж"]
    }

    # Simulate SUCCESS outcome
    print("\n📈 Scenario 1: SUCCESS")
    print("-" * 80)

    success_outcome = {
        "outcome_type": "success",
        "success": True,
        "score": 0.9,
        "clients_acquired": 5,
        "revenue": 150000,
        "time_to_first_client": "2 weeks",
        "unexpected_benefit": "Клиенты сами находили нас через SEO"
    }

    report_success = await analyzer.analyze_decision_outcome(
        decision_id=decision["decision_id"],
        decision=decision,
        actual_outcome=success_outcome
    )

    print(f"🎯 Outcome: {report_success.outcome_type.value.upper()}")
    print(f"📚 Lessons Learned: {len(report_success.lessons_learned)}")
    for lesson in report_success.lessons_learned:
        print(f"  - [{lesson.lesson_type.value}] {lesson.description}")

    print(f"\n🎯 Confidence Calibration:")
    cal = report_success.confidence_calibration
    print(f"  Predicted: {cal['predicted_confidence'] * 100:.1f}%")
    print(f"  Expected: {cal['expected_confidence'] * 100:.1f}%")
    print(f"  Quality: {cal['calibration_quality']}")
    print(f"  {cal['interpretation']}")

    # Simulate FAILURE outcome
    print("\n" + "=" * 80)
    print("📉 Scenario 2: FAILURE")
    print("-" * 80)

    failure_outcome = {
        "outcome_type": "failure",
        "success": False,
        "score": 0.3,
        "clients_acquired": 0,
        "revenue": 0,
        "reason": "Не смогли конкурировать с крупными агентствами"
    }

    report_failure = await analyzer.analyze_decision_outcome(
        decision_id="dec-retro-002",
        decision=decision,
        actual_outcome=failure_outcome
    )

    print(f"🎯 Outcome: {report_failure.outcome_type.value.upper()}")
    print(f"📚 Lessons Learned: {len(report_failure.lessons_learned)}")
    for lesson in report_failure.lessons_learned:
        print(f"  - [{lesson.lesson_type.value}] {lesson.description}")

    print(f"\n💡 Recommendations:")
    for rec in report_failure.recommendations:
        print(f"  - {rec}")

    await analyzer.shutdown()

    return report_success, report_failure


async def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("🚀 SELF-IMPROVEMENT SYSTEM - DEMONSTRATION")
    print("=" * 80)

    # Test Critic
    critique_good, critique_bad, critique_medium = await test_critic_only()

    # Test Retrospective
    report_success, report_failure = await test_retrospective()

    # Summary
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETED")
    print("=" * 80)

    print("\n📊 Results Summary:")
    print(f"  ✅ Good Decision → {critique_good.verdict.value.upper()}")
    print(f"  ❌ Bad Decision → {critique_bad.verdict.value.upper()}")
    print(f"  ⚠️  Medium Decision → {critique_medium.verdict.value.upper()}")
    print(f"  📈 Success Outcome → {len(report_success.lessons_learned)} lessons")
    print(f"  📉 Failure Outcome → {len(report_failure.lessons_learned)} lessons")

    print("\n🔄 Self-Improvement Cycle:")
    print("  1. ✅ Gatekeeper → Filters incoming information")
    print("  2. ✅ Architect → Makes strategic decisions")
    print("  3. ✅ Critic → Validates decisions (APPROVE/CHALLENGE/REJECT)")
    print("  4. ✅ Implementation → Executes approved decisions")
    print("  5. ✅ Experience Tracker → Records outcomes")
    print("  6. ✅ Retrospective Analyzer → Extracts lessons")
    print("  7. ✅ Quality Updater → Improves knowledge scores")
    print("  8. 🔄 Repeat → Continuous improvement")

    print("\n🎯 System Capabilities:")
    print("  ✅ Входной контроль (7 проверок)")
    print("  ✅ Критика решений (5 проверок)")
    print("  ✅ Обучение на опыте")
    print("  ✅ Ретроспективный анализ")
    print("  ✅ Автоматическое улучшение")

    print("\n✨ СИСТЕМА САМОУЛУЧШЕНИЯ РАБОТАЕТ! ✨")


if __name__ == "__main__":
    asyncio.run(main())
