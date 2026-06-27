"""Unit tests for _extract_structured_regalia() — Phase 4 / SEC-04 / D-08.

Verifies typed extraction of degree, academic_title, experience_years, education
from doctor profile text. Covers behavior cases from plan 04-02 plus edge cases.
"""

import sys
import os
import types

# Stub the hermes-agent `tools.registry` package which is only available
# inside the Docker container. Unit tests run locally need a stub so the
# target module can be imported without the full hermes-agent installation.
if "tools" not in sys.modules:
    tools_pkg = types.ModuleType("tools")
    tools_pkg.__path__ = []  # mark as package
    sys.modules["tools"] = tools_pkg
if "tools.registry" not in sys.modules:
    registry_mod = types.ModuleType("tools.registry")
    class _StubRegistry:
        def register(self, *args, **kwargs):
            return None
    registry_mod.registry = _StubRegistry()
    sys.modules["tools.registry"] = registry_mod
    setattr(tools_pkg, "registry", registry_mod)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.tools.find_doctor_handles import _extract_structured_regalia


def test_empty_text():
    r = _extract_structured_regalia("")
    assert r["degree"] is None
    assert r["academic_title"] is None
    assert r["experience_years"] is None
    assert r["education"] == []


def test_no_regalia():
    r = _extract_structured_regalia("Иванов Иван Иванович, пластический хирург")
    assert r["degree"] is None
    assert r["academic_title"] is None
    assert r["experience_years"] is None
    assert r["education"] == []


def test_kmn_and_experience():
    r = _extract_structured_regalia("Иванов И.И., кандидат медицинских наук, стаж 15 лет")
    assert r["degree"] == "КМН", f"Expected КМН, got {r['degree']}"
    assert r["academic_title"] is None
    assert r["experience_years"] == 15
    assert r["education"] == []


def test_dmn_professor_education():
    r = _extract_structured_regalia("Петров П.П., доктор медицинских наук, профессор, окончил МГМУ им. Сеченова")
    assert r["degree"] == "ДМН"
    assert r["academic_title"] == "профессор"
    assert r["experience_years"] is None
    assert len(r["education"]) > 0
    assert "МГМУ" in " ".join(r["education"])


def test_experience_stazh_raboty():
    r = _extract_structured_regalia("Сидорова С.С., стаж работы 20 лет, окончила РНИМУ им. Пирогова")
    assert r["degree"] is None
    assert r["academic_title"] is None
    assert r["experience_years"] == 20
    assert len(r["education"]) > 0


def test_title_priority_professor_wins():
    r = _extract_structured_regalia("доцент и профессор кафедры")
    assert r["academic_title"] == "профессор", (
        f"Expected профессор (higher rank), got {r['academic_title']}"
    )


def test_title_academic_rank():
    r = _extract_structured_regalia("Академик РАН, ведущий специалист")
    assert r["academic_title"] == "академик"


def test_title_chlen_korr():
    r = _extract_structured_regalia("член-корр РАМН")
    assert r["academic_title"] == "член-корреспондент"


def test_title_dotsent_alone():
    r = _extract_structured_regalia("Доцент кафедры косметологии")
    assert r["academic_title"] == "доцент"


def test_degree_dmn_abbreviated():
    r = _extract_structured_regalia("Иванов И.И., д.м.н., специалист")
    assert r["degree"] == "ДМН"


def test_degree_kmn_abbreviated_with_dot():
    r = _extract_structured_regalia("Иванов И.И., к.м.н., специалист")
    assert r["degree"] == "КМН"


def test_experience_let_opyta():
    r = _extract_structured_regalia("15 лет опыта в косметологии")
    assert r["experience_years"] == 15


def test_experience_opyt_raboty():
    r = _extract_structured_regalia("опыт работы 12 лет")
    assert r["experience_years"] == 12


def test_education_obrazovanie():
    r = _extract_structured_regalia("Образование: МГМСУ им. Евдокимова, 2010 год")
    assert len(r["education"]) > 0


def test_education_multiple():
    r = _extract_structured_regalia(
        "Окончил МГМУ им. Сеченова в 2005. Окончил ординатуру РНИМУ им. Пирогова в 2007."
    )
    assert len(r["education"]) >= 2, f"Expected 2 entries, got {len(r['education'])}"


def test_education_max_three():
    text = (
        "Окончил университет А. Окончил университет Б. "
        "Окончил университет В. Окончил университет Г."
    )
    r = _extract_structured_regalia(text)
    assert len(r["education"]) <= 3, f"Max 3 entries, got {len(r['education'])}"


def test_education_dedup():
    text = "Окончил МГМУ им. Сеченова. Окончил МГМУ им. Сеченова."
    r = _extract_structured_regalia(text)
    assert len(r["education"]) == 1, f"Expected dedup to 1, got {len(r['education'])}"


def test_all_fields_combined():
    r = _extract_structured_regalia(
        "Смирнова А.Б., доктор медицинских наук, профессор. "
        "Стаж работы 25 лет. Окончила ПМГМУ им. Сеченова."
    )
    assert r["degree"] == "ДМН"
    assert r["academic_title"] == "профессор"
    assert r["experience_years"] == 25
    assert len(r["education"]) > 0


def test_education_false_positive_filter():
    """Common false positives should NOT appear in education list."""
    text = "Окончил работу в клинике в 2010 году. Стаж работы 10 лет."
    r = _extract_structured_regalia(text)
    # 'работу в клинике' should be filtered out
    for entry in r["education"]:
        assert "работу" not in entry.lower(), f"False positive in education: {entry}"


def test_education_truncated_to_100_chars():
    """Each entry should be at most 100 chars."""
    long_text = "Окончил " + "А" * 200
    r = _extract_structured_regalia(long_text)
    for entry in r["education"]:
        assert len(entry) <= 100, f"Entry too long: {len(entry)} chars"


if __name__ == "__main__":
    # Manual runner
    test_funcs = [
        v for k, v in sorted(globals().items())
        if k.startswith("test_") and callable(v)
    ]
    passed, failed = 0, 0
    for fn in test_funcs:
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")
    sys.exit(0 if failed == 0 else 1)
