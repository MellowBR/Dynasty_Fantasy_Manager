"""
salary_engine_test.py — Unit tests for salary_engine.py

NOTE: All ESPN values passed to the engine are ALREADY-ADJUSTED (raw × 1.2),
exactly as stored in the DB. Tests use realistic adjusted values.

Run with:
    python salary_engine_test.py
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from salary_engine import (
    year1_salary,
    valorization_rule,
    waiver_year2_salary,
    compute_salary_for_year,
    full_contract_table,
    draft_budget,
    MIN_SALARY,
    SALARY_CAP,
    MAX_ROSTER,
)


class TestYear1Salary(unittest.TestCase):

    def test_auction_draft_uses_value_paid(self):
        self.assertEqual(year1_salary("auction_draft", 25, 36.0), 25)

    def test_rookie_draft_uses_espn_adj(self):
        # espn_adj=12.0 (raw 10 × 1.2), floor(12.0)=12
        self.assertEqual(year1_salary("rookie_draft", 0, 12.0), 12)

    def test_rookie_draft_min_salary(self):
        self.assertEqual(year1_salary("rookie_draft", 0, 0.0), MIN_SALARY)

    def test_waiver_is_1(self):
        self.assertEqual(year1_salary("waiver", 0, 60.0), 1)

    def test_free_agent_is_1(self):
        self.assertEqual(year1_salary("free_agent", 0, 60.0), 1)

    def test_fa_alias_is_1(self):
        self.assertEqual(year1_salary("fa", 0, 60.0), 1)

    def test_auction_min_floor(self):
        self.assertEqual(year1_salary("auction_draft", 0, 36.0), MIN_SALARY)

    def test_case_insensitive(self):
        self.assertEqual(year1_salary("WAIVER", 0, 12.0), 1)
        self.assertEqual(year1_salary("Rookie_Draft", 0, 12.0), 12)


class TestValorizationRule(unittest.TestCase):

    def test_prev_salary_wins(self):
        # prev=35, floor(0.5×66.0)=33 → MAX(35,33)=35
        # This is the Saquon Barkley case: the correct answer
        self.assertEqual(valorization_rule(35, 66.0), 35)

    def test_espn_wins_when_higher(self):
        # prev=10, floor(0.5×60.0)=30 → MAX(10,30)=30
        self.assertEqual(valorization_rule(10, 60.0), 30)

    def test_floor_behavior(self):
        # prev=5, floor(0.5×8.4)=floor(4.2)=4 → MAX(5,4)=5
        self.assertEqual(valorization_rule(5, 8.4), 5)

    def test_zero_espn_preserves_salary(self):
        # prev=15, floor(0)=0 → MAX(15,0)=15
        self.assertEqual(valorization_rule(15, 0.0), 15)

    def test_minimum_salary_floor(self):
        self.assertEqual(valorization_rule(0, 0.0), MIN_SALARY)

    def test_rounding_down(self):
        # prev=1, floor(0.5×3.3)=floor(1.65)=1 → MAX(1,1)=1
        self.assertEqual(valorization_rule(1, 3.3), 1)


class TestWaiverYear2(unittest.TestCase):

    def test_waiver_year2_basic(self):
        # espn_adj=36.0, floor(0.80×36.0)=floor(28.8)=28
        self.assertEqual(waiver_year2_salary(36.0), 28)

    def test_waiver_year2_min(self):
        self.assertEqual(waiver_year2_salary(0.0), MIN_SALARY)

    def test_waiver_year2_floor(self):
        # espn_adj=6.0, floor(0.80×6.0)=floor(4.8)=4
        self.assertEqual(waiver_year2_salary(6.0), 4)


class TestComputeSalaryForYear(unittest.TestCase):

    # ── Auction Draft ─────────────────────────────────────────────────
    def test_auction_year1(self):
        self.assertEqual(compute_salary_for_year("auction_draft", 35, 60.0, 1), 35)

    def test_auction_year2_prev_wins(self):
        # prev=35, floor(0.5×66.0)=33 → MAX(35,33)=35  (Saquon scenario)
        self.assertEqual(compute_salary_for_year("auction_draft", 35, 66.0, 2), 35)

    def test_auction_year2_espn_wins(self):
        # prev=5, floor(0.5×60.0)=30 → MAX(5,30)=30
        self.assertEqual(compute_salary_for_year("auction_draft", 5, 60.0, 2), 30)

    def test_auction_year4(self):
        # yr1=5, yr2=30, yr3=30, yr4=30
        self.assertEqual(compute_salary_for_year("auction_draft", 5, 60.0, 4), 30)

    # ── Saquon Barkley exact scenario ────────────────────────────────
    def test_saquon_projection(self):
        # salary=35, espn_adj=66.0, contract_year=2, project year 3
        # VALORIZAÇÃO: MAX(35, floor(0.5×66.0)) = MAX(35,33) = 35
        self.assertEqual(compute_salary_for_year("auction_draft", 35, 66.0, 3), 35)

    # ── Rookie Draft ──────────────────────────────────────────────────
    def test_rookie_year1(self):
        # espn_adj=12.0 → floor(12.0)=12
        self.assertEqual(compute_salary_for_year("rookie_draft", 0, 12.0, 1), 12)

    def test_rookie_year2(self):
        # yr1=12, yr2=MAX(12, floor(0.5×12.0))=MAX(12,6)=12
        self.assertEqual(compute_salary_for_year("rookie_draft", 0, 12.0, 2), 12)

    def test_rookie_year2_high_espn(self):
        # espn_adj=48.0, yr1=48, yr2=MAX(48, floor(0.5×48))=MAX(48,24)=48
        self.assertEqual(compute_salary_for_year("rookie_draft", 0, 48.0, 2), 48)

    # ── Waiver / FA ───────────────────────────────────────────────────
    def test_waiver_year1(self):
        self.assertEqual(compute_salary_for_year("waiver", 0, 60.0, 1), 1)

    def test_waiver_year2_special(self):
        # espn_adj=36.0, floor(0.80×36.0)=floor(28.8)=28
        self.assertEqual(compute_salary_for_year("waiver", 0, 36.0, 2), 28)

    def test_waiver_year3_valorization(self):
        # yr1=1, yr2=28, yr3=MAX(28, floor(0.5×36.0))=MAX(28,18)=28
        self.assertEqual(compute_salary_for_year("waiver", 0, 36.0, 3), 28)

    def test_fa_year2(self):
        self.assertEqual(compute_salary_for_year("free_agent", 0, 36.0, 2), 28)

    # ── Min salary floor ──────────────────────────────────────────────
    def test_min_salary_always_1(self):
        for yr in range(1, 5):
            result = compute_salary_for_year("waiver", 0, 0.0, yr)
            self.assertGreaterEqual(result, MIN_SALARY, f"Year {yr} salary below $1")

    # ── Contract renewal ──────────────────────────────────────────────
    def test_renewal_year1(self):
        # Year 5 = renewal year 1 = floor(espn_adj) = floor(36.0) = 36
        self.assertEqual(compute_salary_for_year("auction_draft", 10, 36.0, 5), 36)

    def test_renewal_year2(self):
        # Year 6 = renewal year 2: yr1=36, MAX(36, floor(0.5×36))=MAX(36,18)=36
        self.assertEqual(compute_salary_for_year("auction_draft", 10, 36.0, 6), 36)

    def test_renewal_year1_low_espn(self):
        # espn_adj=0.96 → floor(0.96)=1 (min $1)
        self.assertEqual(compute_salary_for_year("auction_draft", 1, 0.96, 5), 1)


class TestFullContractTable(unittest.TestCase):

    def test_table_has_5_rows(self):
        table = full_contract_table("auction_draft", 10, 24.0, 1)
        self.assertEqual(len(table), 5)  # 4 years + renewal

    def test_renewal_row_is_last(self):
        table = full_contract_table("auction_draft", 10, 24.0, 1)
        self.assertTrue(table[-1]["is_renewal"])
        self.assertEqual(table[-1]["year"], 5)

    def test_current_year_flagged(self):
        table = full_contract_table("auction_draft", 10, 24.0, 2)
        current_rows = [r for r in table if r["is_current"]]
        self.assertEqual(len(current_rows), 1)
        self.assertEqual(current_rows[0]["year"], 2)

    def test_all_salaries_at_least_1(self):
        table = full_contract_table("waiver", 0, 0.0, 1)
        for row in table:
            self.assertGreaterEqual(row["salary"], 1, f"Row {row['label']} salary < $1")


class TestDraftBudget(unittest.TestCase):

    def _make_player(self, salary, is_dropped=False):
        class FakePlayer:
            pass
        p = FakePlayer()
        p.salary = salary
        p.is_dropped = is_dropped
        return p

    def test_basic_budget(self):
        players = [self._make_player(s) for s in [35, 25, 15, 10, 5]]
        result = draft_budget(players)
        self.assertEqual(result["keeper_salaries"], 90)
        self.assertEqual(result["raw_budget"], 110)
        self.assertEqual(result["num_keepers"], 5)
        self.assertEqual(result["empty_spots"], MAX_ROSTER - 5)
        self.assertFalse(result["over_cap"])

    def test_over_cap(self):
        players = [self._make_player(50)] * 5  # 250
        result = draft_budget(players)
        self.assertTrue(result["over_cap"])

    def test_dropped_not_counted(self):
        players = [
            self._make_player(50, is_dropped=False),
            self._make_player(200, is_dropped=True),
        ]
        result = draft_budget(players)
        self.assertEqual(result["keeper_salaries"], 50)

    def test_insufficient_budget(self):
        players = [self._make_player(10)] * 22  # $220 > $200
        result = draft_budget(players)
        self.assertTrue(result["over_cap"])

    def test_usable_budget_accounts_for_spots(self):
        players = [self._make_player(10)] * 11  # 11 keepers, 11 empty spots
        result = draft_budget(players)
        self.assertEqual(result["min_required_for_spots"], 11)
        self.assertEqual(result["usable_draft_budget"], result["raw_budget"] - 11)

    def test_empty_roster(self):
        result = draft_budget([])
        self.assertEqual(result["keeper_salaries"], 0)
        self.assertEqual(result["raw_budget"], SALARY_CAP)
        self.assertEqual(result["min_required_for_spots"], MAX_ROSTER)


class TestEdgeCases(unittest.TestCase):

    def test_zero_espn_all_years_waiver(self):
        for yr in range(1, 5):
            sal = compute_salary_for_year("waiver", 0, 0.0, yr)
            self.assertEqual(sal, 1, f"Waiver year {yr} with 0 ESPN should be $1")

    def test_high_espn_rookie(self):
        # espn_adj=84.0 (raw 70 × 1.2), floor(84)=84
        self.assertEqual(compute_salary_for_year("rookie_draft", 0, 84.0, 1), 84)

    def test_valorization_never_decreases(self):
        """Salary should never decrease via VALORIZAÇÃO."""
        prev_sal = 35
        espn = 66.0  # even when espn floor < prev, salary holds
        new_sal = valorization_rule(prev_sal, espn)
        self.assertGreaterEqual(new_sal, prev_sal)

    def test_contract_year_progression(self):
        """Each year should be >= previous year for auction draft with rising ESPN."""
        espn = 24.0
        salaries = [compute_salary_for_year("auction_draft", 5, espn, yr) for yr in range(1, 5)]
        for i in range(1, len(salaries)):
            self.assertGreaterEqual(
                salaries[i], salaries[i - 1],
                f"Salary decreased year {i}→{i+1}: {salaries}"
            )

    def test_saquon_full_scenario(self):
        """Saquon: salary=$35, espn_adj=$66.0, yr2 → yr3 stays $35."""
        # Reported bug: was computing $39 (due to double ×1.2). Correct is $35.
        projected = valorization_rule(35, 66.0)
        self.assertEqual(projected, 35)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
