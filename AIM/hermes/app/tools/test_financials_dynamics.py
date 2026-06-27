"""Unit tests for _format_revenue_dynamics() and _format_clinic_metrics() helpers.

Covers all behavior cases listed in PLAN.md 04-01 Task 1 + Task 2:
- Empty / None / non-dict input
- <3 years (strict 3-year gate per D-13)
- Exactly 3 years (growth case)
- Exactly 3 years (decline case)
- More than 3 years (truncates to latest 3)
- Clinic metrics structure (revenue, profit, okved, status, address)
"""

import os
import sys
import types
import unittest

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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


class TestFormatRevenueDynamics(unittest.TestCase):
    def test_empty_dict(self):
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics({})
        self.assertFalse(r["dynamics_available"])
        self.assertIn("нет данных", r["reason"])

    def test_none_input(self):
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics(None)
        self.assertFalse(r["dynamics_available"])

    def test_one_year_strict_gate(self):
        """D-13: <3 years = do not show partial data."""
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics({"2023": 100})
        self.assertFalse(r["dynamics_available"])
        self.assertIn("1", r["reason"])

    def test_two_years_strict_gate(self):
        """D-13: 2 years is still partial — must not show."""
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics({"2023": 100, "2022": 90})
        self.assertFalse(r["dynamics_available"])

    def test_three_years_growth(self):
        """Reference case: +79% over 3 years."""
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics({
            "2023": 4_300_000_000,
            "2022": 3_400_000_000,
            "2021": 2_400_000_000,
        })
        self.assertTrue(r["dynamics_available"])
        self.assertEqual(len(r["years"]), 3)
        # Latest year first
        self.assertEqual(r["years"][0]["year"], "2023")
        self.assertEqual(r["years"][1]["year"], "2022")
        self.assertEqual(r["years"][2]["year"], "2021")
        # Oldest year has no YoY
        self.assertIsNone(r["years"][2]["yoy_pct"])
        # 2022 YoY = (3.4 - 2.4) / 2.4 * 100 = 41.666... → 41.7
        self.assertAlmostEqual(r["years"][1]["yoy_pct"], 41.7, places=1)
        # 2023 YoY = (4.3 - 3.4) / 3.4 * 100 = 26.47... → 26.5
        self.assertAlmostEqual(r["years"][0]["yoy_pct"], 26.5, places=1)
        # Total growth = (4.3 - 2.4) / 2.4 * 100 = 79.166... → 79.2
        self.assertAlmostEqual(r["total_growth_pct"], 79.2, places=1)
        # Summary text mentions growth
        self.assertIn("вырос", r["summary_text"].lower())

    def test_three_years_decline(self):
        """Decline case: total growth is negative."""
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics({
            "2023": 100,
            "2022": 200,
            "2021": 300,
        })
        self.assertTrue(r["dynamics_available"])
        self.assertLess(r["total_growth_pct"], 0)
        self.assertIn("снизил", r["summary_text"].lower())

    def test_more_than_three_years_truncates(self):
        """If 5 years available, take latest 3 only."""
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics({
            "2024": 5000,
            "2023": 4300,
            "2022": 3400,
            "2021": 2400,
            "2020": 2000,
        })
        self.assertTrue(r["dynamics_available"])
        self.assertEqual(len(r["years"]), 3)
        self.assertEqual(r["years"][0]["year"], "2024")
        self.assertEqual(r["years"][2]["year"], "2022")

    def test_years_sorted_descending(self):
        """Ensure years are always sorted latest-first regardless of input order."""
        from app.tools.find_company_financials import _format_revenue_dynamics
        r = _format_revenue_dynamics({
            "2021": 100,
            "2023": 300,
            "2022": 200,
        })
        self.assertEqual(r["years"][0]["year"], "2023")
        self.assertEqual(r["years"][1]["year"], "2022")
        self.assertEqual(r["years"][2]["year"], "2021")


class TestFormatClinicMetrics(unittest.TestCase):
    def test_full_company_dict(self):
        from app.tools.find_company_financials import _format_clinic_metrics
        company = {
            "latest_revenue": 4_300_000_000,
            "latest_profit": 500_000_000,
            "okved_main": "86.21",
            "status": "Действующее",
            "legal_address": "г. Москва, ул. Пример",
            "employees": 50,
        }
        m = _format_clinic_metrics(company)
        self.assertEqual(m["revenue_latest"], 4_300_000_000)
        self.assertEqual(m["profit_latest"], 500_000_000)
        self.assertEqual(m["employees"], 50)
        self.assertEqual(m["okved_codes"][0]["code"], "86.21")
        self.assertEqual(m["okved_codes"][0]["description"], "")  # LLM fills in Pass 3
        self.assertEqual(m["licenses"], [])
        self.assertEqual(m["status"], "Действующее")
        self.assertEqual(m["legal_address"], "г. Москва, ул. Пример")

    def test_missing_employees(self):
        """Backend may not return employees — must default to None."""
        from app.tools.find_company_financials import _format_clinic_metrics
        m = _format_clinic_metrics({"okved_main": "86.21"})
        self.assertIsNone(m["employees"])

    def test_missing_okved(self):
        """If no okved_main, okved_codes is empty list."""
        from app.tools.find_company_financials import _format_clinic_metrics
        m = _format_clinic_metrics({"latest_revenue": 100})
        self.assertEqual(m["okved_codes"], [])

    def test_falls_back_to_latest_value_helper(self):
        """If latest_revenue not pre-computed, derive from revenue dict."""
        from app.tools.find_company_financials import _format_clinic_metrics
        m = _format_clinic_metrics({
            "revenue": {"2023": 999, "2022": 100},
            "profit": {"2023": 50},
        })
        self.assertEqual(m["revenue_latest"], 999)
        self.assertEqual(m["profit_latest"], 50)


if __name__ == "__main__":
    unittest.main()
