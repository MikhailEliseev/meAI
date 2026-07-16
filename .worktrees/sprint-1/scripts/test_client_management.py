"""Tests for Client Management system

Tests Client and Project models, and ClientManager functionality.
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from meai.models.client import Client, ClientContact, ClientStatus, SubscriptionTier
from meai.models.project import Project, ProjectType, ProjectStatus, DeliverableStatus
from meai.agents.client_manager import ClientManager


@pytest.mark.asyncio
async def test_client_creation():
    """Test creating a client"""
    print("\n" + "=" * 70)
    print("TEST 1: Client Creation")
    print("=" * 70)

    contact = ClientContact(
        name="Иван Петров",
        role="CEO",
        email="ivan@smile-dent.ru",
        phone="+7 (495) 123-45-67",
        is_primary=True,
    )

    client = Client.create(
        name="Стоматология Смайл",
        industry="dentistry",
        subscription_tier=SubscriptionTier.PRO,
        primary_contact=contact,
        location="Москва, Арбат",
        monthly_budget=100000,
        target_audience="25-45 лет, средний+ доход",
    )

    print(f"\n✅ Client created:")
    print(f"   ID: {client.client_id}")
    print(f"   Name: {client.name}")
    print(f"   Industry: {client.industry}")
    print(f"   Tier: {client.subscription_tier.value}")
    print(f"   Status: {client.status.value}")
    print(f"   Max projects: {client.get_max_projects()}")
    print(f"   SLA response time: {client.get_sla_response_time_hours()}h")

    # Verify
    assert client.name == "Стоматология Смайл"
    assert client.industry == "dentistry"
    assert client.subscription_tier == SubscriptionTier.PRO
    assert client.status == ClientStatus.LEAD
    assert client.get_max_projects() == 3
    assert client.get_sla_response_time_hours() == 12

    primary = client.get_primary_contact()
    assert primary is not None
    assert primary.name == "Иван Петров"
    assert primary.email == "ivan@smile-dent.ru"

    print("\n✅ TEST 1 PASSED")


@pytest.mark.asyncio
async def test_project_creation():
    """Test creating a project"""
    print("\n" + "=" * 70)
    print("TEST 2: Project Creation")
    print("=" * 70)

    project = Project.create(
        client_id="client-12345678",
        name="SEO продвижение стоматологии",
        project_type=ProjectType.SEO,
        duration_months=3,
        description="Комплексное SEO продвижение",
        goals=["Топ-3 по 20 ключам", "+50% органического трафика"],
        total_budget=150000,
    )

    print(f"\n✅ Project created:")
    print(f"   ID: {project.project_id}")
    print(f"   Name: {project.name}")
    print(f"   Type: {project.project_type.value}")
    print(f"   Status: {project.status.value}")
    print(f"   Duration: {project.duration_months} months")
    print(f"   Budget: {project.total_budget} RUB")
    print(f"   Goals: {len(project.goals)}")

    # Verify
    assert project.name == "SEO продвижение стоматологии"
    assert project.project_type == ProjectType.SEO
    assert project.status == ProjectStatus.PLANNING
    assert project.duration_months == 3
    assert project.total_budget == 150000
    assert len(project.goals) == 2

    print("\n✅ TEST 2 PASSED")


@pytest.mark.asyncio
async def test_project_deliverables():
    """Test project deliverables management"""
    print("\n" + "=" * 70)
    print("TEST 3: Project Deliverables")
    print("=" * 70)

    project = Project.create(
        client_id="client-12345678",
        name="SEO продвижение",
        project_type=ProjectType.SEO,
        duration_months=3,
        total_budget=150000,
    )

    # Add deliverables
    d1 = project.add_deliverable(
        name="SEO аудит",
        description="Полный технический и контентный аудит",
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        assigned_to="seo-magister-1",
    )

    d2 = project.add_deliverable(
        name="Стратегия продвижения",
        description="План работ на 3 месяца",
        due_date=datetime.now(timezone.utc) + timedelta(days=14),
        assigned_to="seo-magister-1",
    )

    d3 = project.add_deliverable(
        name="Оптимизация контента",
        description="Оптимизация 20 страниц",
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        assigned_to="content-magister-1",
    )

    print(f"\n✅ Deliverables added: {len(project.deliverables)}")
    for i, d in enumerate(project.deliverables, 1):
        print(f"   {i}. {d.name} → {d.assigned_to}")

    # Update deliverable status
    project.update_deliverable_status(d1.deliverable_id, DeliverableStatus.COMPLETED)
    project.update_deliverable_status(d2.deliverable_id, DeliverableStatus.IN_PROGRESS)

    completion = project.get_completion_percentage()
    print(f"\n✅ Project completion: {completion:.1f}%")

    # Verify
    assert len(project.deliverables) == 3
    assert project.get_deliverable(d1.deliverable_id).status == DeliverableStatus.COMPLETED
    assert project.get_deliverable(d2.deliverable_id).status == DeliverableStatus.IN_PROGRESS
    assert completion == pytest.approx(33.33, rel=0.1)

    print("\n✅ TEST 3 PASSED")


@pytest.mark.asyncio
async def test_client_manager_crud():
    """Test ClientManager CRUD operations"""
    print("\n" + "=" * 70)
    print("TEST 4: ClientManager CRUD Operations")
    print("=" * 70)

    # Initialize ClientManager
    manager = ClientManager(database_url="sqlite+aiosqlite:///:memory:")
    await manager.initialize()

    # Create client
    contact = ClientContact(
        name="Иван Петров",
        role="CEO",
        email="ivan@smile-dent.ru",
        phone="+7 (495) 123-45-67",
        is_primary=True,
    )

    client = await manager.create_client(
        name="Стоматология Смайл",
        industry="dentistry",
        subscription_tier=SubscriptionTier.PRO,
        primary_contact=contact,
        location="Москва, Арбат",
        monthly_budget=100000,
    )

    print(f"\n✅ Client created in database:")
    print(f"   ID: {client.client_id}")
    print(f"   Name: {client.name}")

    # Read client
    retrieved = await manager.get_client(client.client_id)
    assert retrieved is not None
    assert retrieved.name == "Стоматология Смайл"
    print(f"\n✅ Client retrieved from database")

    # Update client
    client.add_tag("premium")
    client.add_tag("high-priority")
    await manager.update_client(client)

    updated = await manager.get_client(client.client_id)
    assert updated is not None
    assert "premium" in updated.tags
    assert "high-priority" in updated.tags
    print(f"\n✅ Client updated in database")
    print(f"   Tags: {updated.tags}")

    # List clients
    clients = await manager.list_clients()
    assert len(clients) == 1
    print(f"\n✅ Listed {len(clients)} client(s)")

    # Cleanup
    await manager.shutdown()

    print("\n✅ TEST 4 PASSED")


@pytest.mark.asyncio
async def test_client_manager_projects():
    """Test ClientManager project operations"""
    print("\n" + "=" * 70)
    print("TEST 5: ClientManager Project Operations")
    print("=" * 70)

    # Initialize ClientManager
    manager = ClientManager(database_url="sqlite+aiosqlite:///:memory:")
    await manager.initialize()

    # Create client
    contact = ClientContact(
        name="Иван Петров",
        role="CEO",
        email="ivan@smile-dent.ru",
        is_primary=True,
    )

    client = await manager.create_client(
        name="Стоматология Смайл",
        industry="dentistry",
        subscription_tier=SubscriptionTier.PRO,
        primary_contact=contact,
    )

    print(f"\n✅ Client created: {client.name}")

    # Create project
    project = await manager.create_project(
        client_id=client.client_id,
        name="SEO продвижение",
        project_type=ProjectType.SEO,
        duration_months=3,
        description="Комплексное SEO продвижение",
        goals=["Топ-3 по 20 ключам"],
        total_budget=150000,
    )

    print(f"\n✅ Project created:")
    print(f"   ID: {project.project_id}")
    print(f"   Name: {project.name}")
    print(f"   Budget: {project.total_budget} RUB")

    # Verify client has project
    updated_client = await manager.get_client(client.client_id)
    assert updated_client is not None
    assert project.project_id in updated_client.projects
    print(f"\n✅ Client has {len(updated_client.projects)} project(s)")

    # Get client projects
    projects = await manager.get_client_projects(client.client_id)
    assert len(projects) == 1
    assert projects[0].project_id == project.project_id
    print(f"\n✅ Retrieved {len(projects)} project(s) for client")

    # Get client stats
    stats = await manager.get_client_stats(client.client_id)
    print(f"\n✅ Client statistics:")
    print(f"   Total projects: {stats['total_projects']}")
    print(f"   Active projects: {stats['active_projects']}")
    print(f"   Total budget: {stats['total_budget']} RUB")
    print(f"   Can add project: {stats['can_add_project']}")

    assert stats["total_projects"] == 1
    assert stats["total_budget"] == 150000
    assert stats["can_add_project"] is True  # PRO tier allows 3 projects

    # Cleanup
    await manager.shutdown()

    print("\n✅ TEST 5 PASSED")


@pytest.mark.asyncio
async def test_subscription_tier_limits():
    """Test subscription tier project limits"""
    print("\n" + "=" * 70)
    print("TEST 6: Subscription Tier Limits")
    print("=" * 70)

    # Initialize ClientManager
    manager = ClientManager(database_url="sqlite+aiosqlite:///:memory:")
    await manager.initialize()

    # Create BASIC tier client
    contact = ClientContact(
        name="Тест Тестов",
        role="Owner",
        email="test@test.ru",
        is_primary=True,
    )

    client = await manager.create_client(
        name="Тестовая клиника",
        industry="dentistry",
        subscription_tier=SubscriptionTier.BASIC,
        primary_contact=contact,
    )

    print(f"\n✅ BASIC tier client created")
    print(f"   Max projects: {client.get_max_projects()}")

    # Create first project (should succeed)
    project1 = await manager.create_project(
        client_id=client.client_id,
        name="Проект 1",
        project_type=ProjectType.SEO,
    )
    print(f"\n✅ Project 1 created")

    # Try to create second project (should fail for BASIC tier)
    try:
        project2 = await manager.create_project(
            client_id=client.client_id,
            name="Проект 2",
            project_type=ProjectType.CONTENT,
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"\n✅ Project 2 rejected (expected): {e}")

    # Upgrade to PRO tier
    client.subscription_tier = SubscriptionTier.PRO
    await manager.update_client(client)
    print(f"\n✅ Client upgraded to PRO tier")
    print(f"   Max projects: {client.get_max_projects()}")

    # Now second project should succeed
    project2 = await manager.create_project(
        client_id=client.client_id,
        name="Проект 2",
        project_type=ProjectType.CONTENT,
    )
    print(f"\n✅ Project 2 created after upgrade")

    # Verify
    projects = await manager.get_client_projects(client.client_id)
    assert len(projects) == 2

    # Cleanup
    await manager.shutdown()

    print("\n✅ TEST 6 PASSED")


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("CLIENT MANAGEMENT SYSTEM TESTS")
    print("=" * 70)

    try:
        await test_client_creation()
        await test_project_creation()
        await test_project_deliverables()
        await test_client_manager_crud()
        await test_client_manager_projects()
        await test_subscription_tier_limits()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED (6/6)")
        print("=" * 70)
        print("\nClient Management system is working correctly!")
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
