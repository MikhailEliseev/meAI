"""
Комплексный тест CI системы (5 ключевых агентов)

Проверяет работу:
1. CI Scout - поиск и кластеризация конкурентов
2. CI Auditor - аудит сайтов конкурентов
3. CI Reputation - анализ репутации
4. CI Factchecker - проверка фактов
5. CI Strategist - стратегический синтез
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавить путь к проекту
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.meai.agents.base_agent import Task, TaskStatus

# Импорт всех агентов
import importlib.util

def load_agent(agent_name, file_path):
    """Загрузить агента из файла."""
    spec = importlib.util.spec_from_file_location(agent_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_ci_pipeline():
    """Тест полного CI pipeline."""
    print("=" * 80)
    print("CI Pipeline Integration Test")
    print("=" * 80)

    # Загрузить агентов
    ci_path = os.path.join(project_root, 'AIM/src/aim/subagents/competitive_intel/agents')

    scout_module = load_agent("ci_scout", os.path.join(ci_path, "ci_scout.py"))
    auditor_module = load_agent("ci_auditor", os.path.join(ci_path, "ci_auditor.py"))
    reputation_module = load_agent("ci_reputation", os.path.join(ci_path, "ci_reputation.py"))
    factchecker_module = load_agent("ci_factchecker", os.path.join(ci_path, "ci_factchecker.py"))
    strategist_module = load_agent("ci_strategist", os.path.join(ci_path, "ci_strategist.py"))

    # Создать агентов
    scout = scout_module.CIScoutAgent(
        agent_id="ci-scout-test",
        database_url="sqlite+aiosqlite:///./data/meai.db"
    )

    auditor = auditor_module.CIAuditorAgent(
        agent_id="ci-auditor-test",
        database_url="sqlite+aiosqlite:///./data/meai.db"
    )

    reputation = reputation_module.CIReputationAgent(
        agent_id="ci-reputation-test",
        database_url="sqlite+aiosqlite:///./data/meai.db"
    )

    factchecker = factchecker_module.CIFactcheckerAgent(
        agent_id="ci-factchecker-test",
        database_url="sqlite+aiosqlite:///./data/meai.db"
    )

    strategist = strategist_module.CIStrategistAgent(
        agent_id="ci-strategist-test",
        database_url="sqlite+aiosqlite:///./data/meai.db"
    )

    # Phase 1: Scout - поиск конкурентов
    print("\n" + "=" * 80)
    print("PHASE 1: CI Scout - Поиск и кластеризация конкурентов")
    print("=" * 80)

    scout_task = Task(
        task_id="test_task_001",
        subtask_id="subtask_001",
        parent_task_id="parent_001",
        action="competitor_discovery",
        description="Найти конкурентов в стоматологии Москвы",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    scout_task.payload = {
        "niche": "стоматология",
        "geo": "Москва",
        "target_audience": "взрослые 25-55",
        "price_segment": "mid"
    }

    scout_result = await scout.execute_task(scout_task)

    if scout_result.status != "success":
        print(f"❌ Scout failed: {scout_result.error}")
        return False

    print(f"✅ Scout: найдено {scout_result.result['total_found']} конкурентов")
    print(f"   TOP для анализа: {scout_result.result['top_selected']}")

    competitors = scout_result.result['competitors']

    # Phase 2: Auditor - аудит конкурентов
    print("\n" + "=" * 80)
    print("PHASE 2: CI Auditor - Аудит сайтов конкурентов")
    print("=" * 80)

    auditor_task = Task(
        task_id="test_task_002",
        subtask_id="subtask_002",
        parent_task_id="parent_001",
        action="competitor_audit",
        description="Провести аудит конкурентов",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    auditor_task.payload = {
        "competitors": competitors,
        "audit_type": "deep"
    }

    auditor_result = await auditor.execute_task(auditor_task)

    if auditor_result.status != "success":
        print(f"❌ Auditor failed: {auditor_result.error}")
        return False

    print(f"✅ Auditor: проверено {auditor_result.result['total_audited']} конкурентов")
    print(f"   Средняя оценка рынка: {auditor_result.result['insights']['market_average']}")
    print(f"   Найдено gaps: {len(auditor_result.result['gaps'])}")

    # Phase 3: Reputation - анализ репутации
    print("\n" + "=" * 80)
    print("PHASE 3: CI Reputation - Анализ репутации")
    print("=" * 80)

    reputation_task = Task(
        task_id="test_task_003",
        subtask_id="subtask_003",
        parent_task_id="parent_001",
        action="reputation_analysis",
        description="Проанализировать репутацию конкурентов",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    reputation_task.payload = {
        "competitors": competitors
    }

    reputation_result = await reputation.execute_task(reputation_task)

    if reputation_result.status != "success":
        print(f"❌ Reputation failed: {reputation_result.error}")
        return False

    print(f"✅ Reputation: проанализировано {reputation_result.result['total_analyzed']} конкурентов")
    print(f"   Средняя репутация рынка: {reputation_result.result['insights']['market_avg_reputation']}")
    print(f"   Найдено рисков: {len(reputation_result.result['risks_opportunities']['risks'])}")
    print(f"   Найдено возможностей: {len(reputation_result.result['risks_opportunities']['opportunities'])}")

    # Phase 4: Factchecker - проверка фактов
    print("\n" + "=" * 80)
    print("PHASE 4: CI Factchecker - Проверка фактов")
    print("=" * 80)

    factchecker_task = Task(
        task_id="test_task_004",
        subtask_id="subtask_004",
        parent_task_id="parent_001",
        action="fact_checking",
        description="Проверить факты и данные",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    factchecker_task.payload = {
        "previous_results": {
            "phase_1": scout_result.result,
            "phase_2": auditor_result.result,
            "phase_4": reputation_result.result
        }
    }

    factchecker_result = await factchecker.execute_task(factchecker_task)

    if factchecker_result.status != "success":
        print(f"❌ Factchecker failed: {factchecker_result.error}")
        return False

    print(f"✅ Factchecker: проверено {factchecker_result.result['total_facts_checked']} фактов")
    print(f"   Validated: {factchecker_result.result['report']['summary']['validated']}")
    print(f"   Failed: {factchecker_result.result['report']['summary']['failed']}")
    print(f"   Warnings: {factchecker_result.result['report']['summary']['warnings']}")
    print(f"   Contradictions: {factchecker_result.result['report']['summary']['contradictions']}")
    print(f"   Data quality: {factchecker_result.result['report']['data_quality']}")

    # Phase 5: Strategist - стратегический синтез
    print("\n" + "=" * 80)
    print("PHASE 5: CI Strategist - Стратегический синтез")
    print("=" * 80)

    strategist_task = Task(
        task_id="test_task_005",
        subtask_id="subtask_005",
        parent_task_id="parent_001",
        action="strategic_synthesis",
        description="Сгенерировать стратегию",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(),
        received_at=datetime.now()
    )
    strategist_task.payload = {
        "previous_results": {
            "phase_1": scout_result.result,
            "phase_2": auditor_result.result,
            "phase_4": reputation_result.result
        },
        "client_context": {
            "target_audience": "взрослые 25-55",
            "price_segment": "mid"
        }
    }

    strategist_result = await strategist.execute_task(strategist_task)

    if strategist_result.status != "success":
        print(f"❌ Strategist failed: {strategist_result.error}")
        return False

    print(f"✅ Strategist: стратегия сгенерирована")
    print(f"   Позиционирование: {strategist_result.result['positioning']['recommended_position']}")
    print(f"   Дифференциация: {strategist_result.result['differentiation']['primary']['description']}")
    print(f"   Конкурентных преимуществ: {len(strategist_result.result['competitive_advantages'])}")
    print(f"   Рекомендаций: {len(strategist_result.result['recommendations'])}")

    # Итоговый отчёт
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)

    print("\n📊 Результаты по фазам:")
    print(f"  Phase 1 (Scout):       {scout_result.result['total_found']} конкурентов найдено")
    print(f"  Phase 2 (Auditor):     {auditor_result.result['insights']['market_average']}/100 средняя оценка")
    print(f"  Phase 3 (Reputation):  {reputation_result.result['insights']['market_avg_reputation']}/100 средняя репутация")
    print(f"  Phase 4 (Factchecker): {factchecker_result.result['report']['data_quality']} качество данных")
    print(f"  Phase 5 (Strategist):  {len(strategist_result.result['recommendations'])} рекомендаций")

    print("\n🎯 TOP-3 Рекомендации:")
    for i, rec in enumerate(strategist_result.result['recommendations'][:3], 1):
        print(f"  {i}. [{rec['priority'].upper()}] {rec['recommendation']}")

    print("\n📁 Результаты сохранены:")
    print("  - AIM/data/ci-competitors.json")
    print("  - AIM/data/ci-audits.json")
    print("  - AIM/data/ci-reputation.json")
    print("  - AIM/data/ci-factcheck.json")
    print("  - AIM/data/ci-strategy.json")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_ci_pipeline())

    print("\n" + "=" * 80)
    if success:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("CI система работает корректно. Все 5 агентов интегрированы.")
    else:
        print("❌ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("Проверьте логи выше для деталей.")
    print("=" * 80)

    sys.exit(0 if success else 1)
