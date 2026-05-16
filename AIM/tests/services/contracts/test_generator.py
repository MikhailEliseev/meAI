"""
Tests for Contract Generator

Tests contract generation, PDF creation, and versioning.
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from aim.services.contracts.generator import ContractGenerator, ContractVersioning
from aim.services.contracts.templates import ContractType


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def generator(temp_output_dir):
    """Create contract generator with temp directory"""
    return ContractGenerator(output_dir=temp_output_dir)


@pytest.fixture
def sample_client_data():
    """Sample client data"""
    return {
        "client_name": "ООО \"Тестовая Клиника\"",
        "client_inn": "7701234567",
        "client_kpp": "770101001",
        "client_ogrn": "1234567890123",
        "client_address": "123456, г. Москва, ул. Тестовая, д. 1",
        "client_phone": "+7 (495) 123-45-67",
        "client_email": "test@clinic.ru",
        "client_representative": "Генеральный директор Петров П.П.",
        "client_authority": "Устава",
        "client_account": "40702810100000000002",
        "client_bank": "ПАО \"Сбербанк\"",
        "client_bik": "044525225",
        "client_correspondent": "30101810400000000225",
    }


@pytest.fixture
def sample_pricing():
    """Sample pricing data"""
    return {
        "monthly_fee": 250000,
        "min_ad_budget": 150000,
        "seo_cost": 80000,
        "ads_cost": 100000,
        "content_cost": 50000,
        "analytics_cost": 20000,
    }


def test_generate_service_agreement(generator, sample_client_data, sample_pricing):
    """Test service agreement generation"""
    # Generate contract
    contract_path = generator.generate_service_agreement(
        client_data=sample_client_data,
        pricing=sample_pricing,
    )

    # Verify file exists
    assert Path(contract_path).exists()
    assert contract_path.endswith(".pdf")

    # Verify file size (should be > 0)
    assert Path(contract_path).stat().st_size > 0


def test_generate_nda(generator, sample_client_data):
    """Test NDA generation"""
    # Generate NDA
    contract_path = generator.generate_nda(
        client_data=sample_client_data,
    )

    # Verify file exists
    assert Path(contract_path).exists()
    assert "nda" in contract_path.lower()


def test_generate_addendum(generator, sample_client_data):
    """Test addendum generation"""
    # Generate addendum
    contract_path = generator.generate_addendum(
        client_data=sample_client_data,
        original_contract_number="AIM-2026-001",
        original_contract_date="01.05.2026",
        changes="1.1. Изменить стоимость услуг на 300 000 рублей в месяц.",
    )

    # Verify file exists
    assert Path(contract_path).exists()
    assert "addendum" in contract_path.lower()


def test_contract_number_generation(generator):
    """Test contract number generation"""
    # Generate first contract
    number1 = generator._generate_contract_number()
    assert number1.startswith("AIM-")
    assert str(datetime.now().year) in number1

    # Generate second contract (should increment)
    number2 = generator._generate_contract_number()
    assert number2 != number1


def test_contract_number_with_prefix(generator):
    """Test contract number with custom prefix"""
    number = generator._generate_contract_number(prefix="NDA")
    assert number.startswith("NDA-")


def test_addendum_number_generation(generator):
    """Test addendum number generation"""
    contract_number = "AIM-2026-001"

    # First addendum
    addendum1 = generator._generate_addendum_number(contract_number)
    assert addendum1 == "1"

    # Second addendum (would be 2 if file existed)
    addendum2 = generator._generate_addendum_number(contract_number)
    assert addendum2 == "1"  # Still 1 because no files created


def test_multiple_contracts_same_session(generator, sample_client_data, sample_pricing):
    """Test generating multiple contracts in same session"""
    # Generate 3 contracts
    paths = []
    for _ in range(3):
        path = generator.generate_service_agreement(
            client_data=sample_client_data,
            pricing=sample_pricing,
        )
        paths.append(path)

    # Verify all exist and are unique
    assert len(paths) == 3
    assert len(set(paths)) == 3
    for path in paths:
        assert Path(path).exists()


def test_contract_versioning(temp_output_dir):
    """Test contract versioning"""
    versioning = ContractVersioning(storage_dir=temp_output_dir)

    contract_number = "AIM-2026-001"

    # Save version 1
    versioning.save_version(
        contract_number=contract_number,
        version=1,
        file_path="/path/to/contract_v1.pdf",
        changes="Initial version",
    )

    # Verify version saved
    latest = versioning.get_latest_version(contract_number)
    assert latest == 1

    # Save version 2
    versioning.save_version(
        contract_number=contract_number,
        version=2,
        file_path="/path/to/contract_v2.pdf",
        changes="Updated pricing",
    )

    # Verify latest version
    latest = versioning.get_latest_version(contract_number)
    assert latest == 2


def test_version_history(temp_output_dir):
    """Test version history retrieval"""
    versioning = ContractVersioning(storage_dir=temp_output_dir)

    contract_number = "AIM-2026-001"

    # Save 3 versions
    for i in range(1, 4):
        versioning.save_version(
            contract_number=contract_number,
            version=i,
            file_path=f"/path/to/contract_v{i}.pdf",
            changes=f"Version {i}",
        )

    # Get history
    history = versioning.get_version_history(contract_number)

    # Verify history
    assert len(history) == 3
    assert history[0]["version"] == 1
    assert history[1]["version"] == 2
    assert history[2]["version"] == 3


def test_no_version_history(temp_output_dir):
    """Test version history for non-existent contract"""
    versioning = ContractVersioning(storage_dir=temp_output_dir)

    # Get history for non-existent contract
    history = versioning.get_version_history("NON-EXISTENT")

    # Should be empty
    assert len(history) == 0


def test_latest_version_none(temp_output_dir):
    """Test latest version for non-existent contract"""
    versioning = ContractVersioning(storage_dir=temp_output_dir)

    # Get latest version for non-existent contract
    latest = versioning.get_latest_version("NON-EXISTENT")

    # Should be None
    assert latest is None


def test_contract_with_cyrillic_data(generator, sample_client_data, sample_pricing):
    """Test contract generation with Cyrillic characters"""
    # Add more Cyrillic text
    sample_client_data["client_name"] = "ООО \"Стоматологическая Клиника Здоровая Улыбка\""
    sample_client_data["client_address"] = "123456, г. Москва, ул. Ленина, д. 10, корп. 2, офис 305"

    # Generate contract
    contract_path = generator.generate_service_agreement(
        client_data=sample_client_data,
        pricing=sample_pricing,
    )

    # Verify file exists
    assert Path(contract_path).exists()


def test_contract_output_directory_creation(temp_output_dir):
    """Test that output directory is created if it doesn't exist"""
    # Create generator with non-existent directory
    non_existent_dir = Path(temp_output_dir) / "contracts" / "nested"
    generator = ContractGenerator(output_dir=str(non_existent_dir))

    # Verify directory was created
    assert non_existent_dir.exists()


def test_contract_metadata(generator, sample_client_data, sample_pricing):
    """Test contract PDF metadata"""
    # Generate contract
    contract_path = generator.generate_service_agreement(
        client_data=sample_client_data,
        pricing=sample_pricing,
    )

    # Verify file exists
    assert Path(contract_path).exists()

    # TODO: Add PDF metadata verification when PyPDF2 is available
    # For now, just verify file is valid PDF
    with open(contract_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"
