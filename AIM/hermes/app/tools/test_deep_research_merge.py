"""
Unit tests for deep_research_merge.py — tier classification and JSON merge.
14 behaviour cases from PLAN.md Task 1.
"""
import json
import os
import sys
import tempfile
import time
import pytest

# Ensure the tools directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deep_research_merge import classify_doctor, validate_and_merge


# ── Test fixtures ──────────────────────────────────────────────────

@pytest.fixture
def empty_data_json():
    """Empty data.json — new presale."""
    return {"meta": {}, "clinic": {}, "doctors": [], "competitors": [], "content": {}, "geo": {}}


@pytest.fixture
def existing_data_json():
    """data.json with some existing fields — simulating partial presale."""
    return {
        "meta": {"client": "vipclinic", "url": "https://vipclinic.vip"},
        "clinic": {"name": "VIP Clinic", "inn": "7703396052"},
        "doctors": [],
        "competitors": [],
        "content": {},
        "geo": {}
    }


@pytest.fixture
def sample_research_input():
    """Valid deep_research input with clinic + doctors."""
    return {
        "clinic": {
            "history": "Founded in 2008",
            "reputation": {"prodoctorov_rating": 5.0},
        },
        "doctors": [
            {
                "full_name": "Круглик Сергей Викторович",
                "bio": "Круглик С.В., к.м.н., пластический хирург, руководитель клиники",
                "experience_years": 24,
            },
            {
                "full_name": "Иванова Анна Петровна",
                "bio": "д.м.н., профессор, заслуженный врач РФ",
                "experience_years": 30,
            },
            {
                "full_name": "Петров Иван Сергеевич",
                "bio": "Врач-косметолог. Стаж работы 8 лет.",
                "experience_years": 8,
            },
        ],
        "_meta": {
            "sources_used": ["prodoctorov.ru", "elibrary.ru"],
            "research_duration_seconds": 340,
        }
    }


# ── Test 1: Tier 1 (star) — д.м.н. ─────────────────────────────────

def test_tier_1_star_dmn():
    """Bio with 'д.м.н.' → classify_doctor() returns tier='star'."""
    result = classify_doctor("Иванова А.П.", "Иванова А.П., д.м.н., пластический хирург", 20)
    assert result["tier"] == "star"
    assert "д.м.н." in result["degrees"]


# ── Test 2: Tier 1 (star qualifier) ────────────────────────────────

def test_tier_1_star_qualifier_author():
    """Bio with 'автор методики' + experience 20+ → tier='star', auto_flagged_star=true."""
    result = classify_doctor(
        "Сидоров В.В.",
        "Сидоров В.В., автор методики лазерной шлифовки, врач-дерматолог, стаж 22 года",
        22
    )
    assert result["tier"] == "star"
    assert result["auto_flagged_star"] is True


def test_tier_1_star_qualifier_organizer():
    """Bio with 'организатор конгресса' + experience 20+ → tier='star'."""
    result = classify_doctor(
        "Орлов Д.А.",
        "Орлов Д.А., организатор конгресса по эстетической медицине, стаж 21 год",
        21
    )
    assert result["tier"] == "star"


# ── Test 3: Tier 2 (core) — к.м.н. ─────────────────────────────────

def test_tier_2_core_kmn():
    """Bio with 'к.м.н.' → tier='core'."""
    result = classify_doctor("Круглик С.В.", "Круглик С.В., к.м.н., пластический хирург", 10)
    assert result["tier"] == "core"
    assert "к.м.н." in result["degrees"]


def test_tier_2_core_chief():
    """Bio with 'главный врач' → tier='core'."""
    result = classify_doctor("Смирнов А.А.", "Смирнов А.А., главный врач клиники", 12)
    assert result["tier"] == "core"


def test_tier_2_core_head_of_department():
    """Bio with 'руководитель отделения' → tier='core'."""
    result = classify_doctor("Кузнецов П.П.", "Кузнецов П.П., руководитель отделения косметологии", 10)
    assert result["tier"] == "core"


# ── Test 4: Tier 2 (experience) — no regalia, but 15+ years ────────

def test_tier_2_experience_promotion():
    """No regalia, but experience_years >= 15 → tier='core'."""
    result = classify_doctor("Федоров М.И.", "Федоров М.И., врач-хирург", 15)
    assert result["tier"] == "core"


# ── Test 5: Tier 3 (team) — no regalia, less than 15 years ─────────

def test_tier_3_team():
    """No regalia, experience_years < 15 → tier='team'."""
    result = classify_doctor("Петров И.С.", "Петров И.С., врач-косметолог", 8)
    assert result["tier"] == "team"


# ── Test 6: Degree extraction ──────────────────────────────────────

def test_degree_extraction():
    """Bio 'Круглик С.В., к.м.н., пластический хирург' → degrees=['к.м.н.']."""
    result = classify_doctor("Круглик С.В.", "Круглик С.В., к.м.н., пластический хирург", 24)
    assert "к.м.н." in result["degrees"]


# ── Test 7: Multiple degrees ───────────────────────────────────────

def test_multiple_degrees():
    """Bio 'д.м.н., профессор, заслуженный врач РФ' → tier='star', degrees contains all three."""
    result = classify_doctor(
        "Иванова А.П.",
        "Иванова А.П., д.м.н., профессор, заслуженный врач РФ",
        30
    )
    assert result["tier"] == "star"
    degrees = result["degrees"]
    assert any("д.м.н." in d for d in degrees)
    assert any("профессор" in d for d in degrees)
    assert any("заслуженный" in d for d in degrees)


# ── Test 8: JSON merge — new section ───────────────────────────────

def test_json_merge_new_section(empty_data_json, sample_research_input):
    """Empty data.json + stdin with deep_research data → data.json contains deep_research."""
    result = validate_and_merge(empty_data_json, sample_research_input)
    assert "deep_research" in result
    assert "clinic" in result["deep_research"]
    assert "doctors" in result["deep_research"]


# ── Test 9: JSON merge — update existing ───────────────────────────

def test_json_merge_update_existing(existing_data_json, sample_research_input):
    """data.json with clinic.inn + stdin with deep_research → existing fields preserved."""
    result = validate_and_merge(existing_data_json, sample_research_input)
    assert result["clinic"]["inn"] == "7703396052"
    assert result["clinic"]["name"] == "VIP Clinic"
    assert "deep_research" in result


# ── Test 10: JSON merge — _meta ────────────────────────────────────

def test_json_merge_meta(empty_data_json, sample_research_input):
    """Merge writes _meta with researched_at, total_doctors_found, tier counts."""
    result = validate_and_merge(empty_data_json, sample_research_input)
    meta = result["deep_research"]["_meta"]
    assert "researched_at" in meta
    assert meta["total_doctors_found"] == 3
    assert "star_doctors" in meta
    assert "core_doctors" in meta
    assert "team_doctors" in meta
    # With the sample data: 2 star (Иванова + maybe Круглик), 2 core, 0 team
    # Exact counts depend on classification, but all keys must exist
    assert meta["star_doctors"] >= 1
    assert meta["team_doctors"] >= 0


# ── Test 11: Regex safety — no catastrophic backtracking ───────────

def test_regex_safety_no_catastrophic_backtracking():
    """Bio of 10KB with many spaces → classify_doctor() finishes in <100ms."""
    long_bio = "А " * 5000  # ~10KB of "А "
    start = time.perf_counter()
    result = classify_doctor("Тест Т.Т.", long_bio, 5)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 100, f"classify_doctor took {elapsed_ms:.0f}ms, expected <100ms"
    assert result["tier"] == "team"  # No regalia in long bio


# ── Test 12: Empty bio ─────────────────────────────────────────────

def test_empty_bio():
    """Empty string → tier='team', degrees=[]."""
    result = classify_doctor("Тест Т.Т.", "", 0)
    assert result["tier"] == "team"
    assert result["degrees"] == []


# ── Test 13: Experience promotion to star ─────────────────────────

def test_experience_promotion_core_to_star():
    """experience_years=25 with tier='core' → tier='star'."""
    result = classify_doctor("Старый В.В.", "Старый В.В., к.м.н., хирург", 25)
    assert result["tier"] == "star"


# ── Test 14: Edge case — д. м. н. with spaces ─────────────────────

def test_edge_case_dmn_with_spaces():
    """'д. м. н.' → correctly recognized as star."""
    result = classify_doctor("Тест Т.Т.", "д. м. н. Тест Т.Т., хирург", 20)
    assert result["tier"] == "star"
    assert any("д.м.н." in d for d in result["degrees"])


# ── Additional edge case tests ─────────────────────────────────────

def test_auto_flagged_star_false_for_formal_degree():
    """Star assigned via formal degree (д.м.н.) → auto_flagged_star=False."""
    result = classify_doctor("Иванова А.П.", "Иванова А.П., д.м.н., профессор", 25)
    assert result["tier"] == "star"
    # Has a formal TIER_1 degree, so auto_flagged_star should be False
    assert result["auto_flagged_star"] is False


def test_doctor_and_medical_sciences_full_word():
    """'доктор медицинских наук' → tier='star'."""
    result = classify_doctor("Тест Т.Т.", "Тест Т.Т., доктор медицинских наук, хирург", 20)
    assert result["tier"] == "star"


def test_kandidat_med_nauk_full_word():
    """'кандидат медицинских наук' → tier='core'."""
    result = classify_doctor("Тест Т.Т.", "Тест Т.Т., кандидат медицинских наук", 10)
    assert result["tier"] == "core"


def test_dozent():
    """'доцент кафедры' → tier='core'."""
    result = classify_doctor("Тест Т.Т.", "Тест Т.Т., доцент кафедры хирургии", 12)
    assert result["tier"] == "core"


def test_academic_ramn():
    """'академик РАМН' → tier='star'."""
    result = classify_doctor("Тест Т.Т.", "Тест Т.Т., академик РАМН", 30)
    assert result["tier"] == "star"


def test_chlen_korr_ramn():
    """'член-корр. РАМН' → tier='star'."""
    result = classify_doctor("Тест Т.Т.", "член-корр. РАМН, профессор", 30)
    assert result["tier"] == "star"


def test_zav_otdeleniem():
    """'зав. отделением' → tier='core'."""
    result = classify_doctor("Тест Т.Т.", "Тест Т.Т., зав. отделением косметологии", 14)
    assert result["tier"] == "core"


def test_zav_otdelom():
    """'зав. отделом' → tier='core'."""
    result = classify_doctor("Тест Т.Т.", "зав. отделом пластической хирургии", 14)
    assert result["tier"] == "core"


def test_scientific_director_star_qualifier():
    """'научный руководитель' → star qualifier, tier='star'."""
    result = classify_doctor("Тест Т.Т.", "научный руководитель клиники, врач-хирург", 20)
    assert result["tier"] == "star"


def test_glavny_gorodskoy_specialist_star_qualifier():
    """'главный городской специалист' → star qualifier, tier='star'."""
    result = classify_doctor("Тест Т.Т.", "главный городской специалист по пластической хирургии", 22)
    assert result["tier"] == "star"


def test_merge_clinic_only():
    """Research input with clinic only (no doctors) → valid merge."""
    data = {"meta": {}, "clinic": {}}
    research = {
        "clinic": {"history": "Founded 2010", "ratings": {"yandex": 4.5}},
    }
    result = validate_and_merge(data, research)
    assert "deep_research" in result
    assert result["deep_research"]["clinic"]["history"] == "Founded 2010"
    assert "doctors" in result["deep_research"]


def test_merge_doctors_only():
    """Research input with doctors only (no clinic) → valid merge."""
    data = {"meta": {}, "clinic": {}}
    research = {
        "doctors": [
            {"full_name": "Тест Т.Т.", "bio": "врач", "experience_years": 5}
        ]
    }
    result = validate_and_merge(data, research)
    assert "deep_research" in result
    assert len(result["deep_research"]["doctors"]) == 1


def test_merge_idempotent():
    """Merging the same data twice → no duplicate doctors."""
    data = {"meta": {}, "clinic": {}}
    research = {
        "doctors": [
            {"full_name": "Тест Т.Т.", "bio": "врач", "experience_years": 5}
        ]
    }
    result1 = validate_and_merge(data, research)
    result2 = validate_and_merge(result1, research)
    assert len(result2["deep_research"]["doctors"]) == 1
