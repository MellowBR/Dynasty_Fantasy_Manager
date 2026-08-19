# -*- coding: utf-8 -*-
"""
wv1_fix_coorte_test.py — testes do runner MAN-WV1-FIX-COORTE.

Núcleo PURO (triagem, seleção de salário, invariante) sem DB e sem rede, no molde do
off26_32_fix_test. Âncoras exigidas pelo owner: Mitchell ($2→$1, cy 3→2), um sid de delta
zero (só contagem) e um dropado (pulado, decisão 2).
"""
import unittest

import wv1_fix_coorte as R


def st(**kw):
    """Estado de player no formato que a triagem lê — default = elegível."""
    base = {
        "player_id": 1, "name": "X", "team": "T",
        "contract_year": 3, "contract_start_season": 2025,
        "acquisition_type": "fa_waiver", "needs_review": False,
        "is_dropped": False, "salary": 1.0, "espn_ref_value": 1.0,
    }
    base.update(kw)
    return [base]


COHORT3 = [("A", "Alice"), ("B", "Bob"), ("C", "Carol")]


class TestTriagem(unittest.TestCase):
    def test_todos_elegiveis(self):
        states = {"A": st(), "B": st(), "C": st()}
        el, sk, ab = R.triage(states, cohort=COHORT3)
        self.assertEqual(el, ["A", "B", "C"])
        self.assertEqual((sk, ab), ([], []))

    def test_dropado_e_pulado_nao_abortado(self):
        """ÂNCORA (decisão 2 do owner): dropado sai da lista, mas não cancela a execução."""
        states = {"A": st(), "B": st(is_dropped=True), "C": st()}
        el, sk, ab = R.triage(states, cohort=COHORT3)
        self.assertEqual(el, ["A", "C"])
        self.assertEqual(ab, [])
        self.assertEqual(len(sk), 1)
        self.assertEqual(sk[0]["sleeper_player_id"], "B")
        self.assertIn("DROPADO", sk[0]["reason"])

    def test_ja_corrigido_e_pulado_idempotencia(self):
        states = {"A": st(), "B": st(contract_year=2), "C": st()}
        el, sk, ab = R.triage(states, cohort=COHORT3)
        self.assertEqual(el, ["A", "C"])
        self.assertEqual(ab, [])
        self.assertIn("ja e 2", sk[0]["reason"])

    def test_css_divergente_aborta(self):
        """ÂNCORA (decisão 3 do owner): contract_start_season ≠ 2025 cancela tudo."""
        states = {"A": st(), "B": st(contract_start_season=2024), "C": st()}
        el, sk, ab = R.triage(states, cohort=COHORT3)
        self.assertEqual(len(ab), 1)
        self.assertEqual(ab[0]["sleeper_player_id"], "B")
        self.assertIn("contract_start_season", ab[0]["reason"])

    def test_css_none_aborta(self):
        el, sk, ab = R.triage({"A": st(contract_start_season=None)}, cohort=[("A", "Alice")])
        self.assertEqual(len(ab), 1)

    def test_sid_ausente_aborta(self):
        el, sk, ab = R.triage({"A": st(), "C": st()}, cohort=COHORT3)
        self.assertEqual([a["sleeper_player_id"] for a in ab], ["B"])
        self.assertIn("ausente", ab[0]["reason"])

    def test_sid_ambiguo_aborta(self):
        states = {"A": st(), "B": st() + st(), "C": st()}
        el, sk, ab = R.triage(states, cohort=COHORT3)
        self.assertIn("ambiguo", ab[0]["reason"])

    def test_canal_mudado_aborta(self):
        states = {"A": st(acquisition_type="fa_auction")}
        el, sk, ab = R.triage(states, cohort=[("A", "Alice")])
        self.assertIn("acquisition_type", ab[0]["reason"])

    def test_needs_review_aborta(self):
        el, sk, ab = R.triage({"A": st(needs_review=True)}, cohort=[("A", "Alice")])
        self.assertIn("needs_review", ab[0]["reason"])

    def test_contract_year_inesperado_aborta(self):
        el, sk, ab = R.triage({"A": st(contract_year=4)}, cohort=[("A", "Alice")])
        self.assertIn("contract_year", ab[0]["reason"])

    def test_dropado_com_css_ruim_ainda_aborta(self):
        """A ordem importa: estado inesperado vence o 'pular dropado'."""
        el, sk, ab = R.triage({"A": st(is_dropped=True, contract_start_season=2024)},
                              cohort=[("A", "Alice")])
        self.assertEqual(len(ab), 1)
        self.assertEqual(sk, [])


class TestSelecaoDeSalario(unittest.TestCase):
    def test_so_corrige_quem_esta_no_mapa_e_bate(self):
        """ÂNCORA Mitchell: $2 esperado → corrige p/ $1."""
        states = {"A": st(salary=2.0), "B": st(salary=1.0)}
        to_fix, mm = R.select_salary_fixes(["A", "B"], states, fixes={"A": (2.0, 1.0)})
        self.assertEqual(to_fix, [("A", 2.0, 1.0)])
        self.assertEqual(mm, [])

    def test_salario_divergente_nao_corrige_e_reporta(self):
        states = {"A": st(salary=3.0)}
        to_fix, mm = R.select_salary_fixes(["A"], states, fixes={"A": (2.0, 1.0)})
        self.assertEqual(to_fix, [])
        self.assertEqual(len(mm), 1)
        self.assertIn("salary", mm[0]["reason"])

    def test_nao_elegivel_nao_recebe_correcao_de_salario(self):
        states = {"A": st(salary=2.0, is_dropped=True)}
        el, sk, ab = R.triage(states, cohort=[("A", "Alice")])
        to_fix, mm = R.select_salary_fixes(el, states, fixes={"A": (2.0, 1.0)})
        self.assertEqual((to_fix, mm), ([], []))


class TestInvarianteFinanceiro(unittest.TestCase):
    def test_delta_zero_so_muda_contagem(self):
        """ÂNCORA delta zero: quem não está no mapa de salário não move dinheiro."""
        states = {"A": st(salary=1.0, espn_ref_value=1.0)}
        before = {"A": {"salary": 1, "projected": 1}}
        after = R.expected_money_after(states, ["A"], fixes={})
        self.assertEqual(R.money_diff(before, after), [])

    def test_salario_aprovado_pode_mudar(self):
        states = {"A": st(salary=2.0, espn_ref_value=1.0)}
        before = {"A": {"salary": 2, "projected": 2}}
        after = R.expected_money_after(states, ["A"], fixes={"A": (2.0, 1.0)})
        self.assertEqual(after["A"]["salary"], 1)
        self.assertEqual(R.money_diff(before, after, allowed={"A"}), [])
        self.assertTrue(R.money_diff(before, after))  # sem allowlist, acusa

    def test_projecao_do_ano_seguinte_nao_muda_com_a_contagem(self):
        """cy 3 e cy 2 caem os dois em valorização — o número tem de sair igual."""
        from salary_engine import project_next_salary
        from types import SimpleNamespace
        a = SimpleNamespace(salary=1.0, espn_ref_value=1.0,
                            acquisition_type="fa_waiver", contract_year=3)
        b = SimpleNamespace(salary=1.0, espn_ref_value=1.0,
                            acquisition_type="fa_waiver", contract_year=2)
        self.assertEqual(project_next_salary(a), project_next_salary(b))


class TestCoorteCongelada(unittest.TestCase):
    def test_18_sids_unicos(self):
        sids = [s for s, _ in R.COHORT]
        self.assertEqual(len(sids), 18)
        self.assertEqual(len(set(sids)), 18)

    def test_defs_permanecem_string(self):
        for sid, _ in R.COHORT:
            self.assertIsInstance(sid, str)
        self.assertIn("BUF", dict(R.COHORT))

    def test_alvos_de_salario_estao_na_coorte(self):
        for sid in R.SALARY_FIXES:
            self.assertIn(sid, dict(R.COHORT))

    def test_nao_ha_intersecao_com_o_censo_off26_32(self):
        import re
        src = open("off26_32_fix.py", encoding="utf-8").read()
        census = set(re.findall(r'\("(\w+)",\s*"[^"]+"\)', src))
        self.assertTrue(census)
        self.assertEqual(set(s for s, _ in R.COHORT) & census, set())

    def test_guarda_exige_css_2025_e_canal_waiver(self):
        self.assertEqual(R.EXPECTED["contract_start_season"], 2025)
        self.assertEqual(R.EXPECTED["acquisition_type"], "fa_waiver")
        self.assertIs(R.EXPECTED["is_dropped"], False)
        self.assertEqual(R.NEW_YEAR, 2)

    def test_nao_seleciona_por_acquisition_type(self):
        """⛔ A lista é congelada — filtrar por canal foi como o OFF26-32 perdeu membros."""
        src = open("wv1_fix_coorte.py", encoding="utf-8").read()
        self.assertNotIn("filter_by(acquisition_type", src)
        self.assertNotIn("Player.acquisition_type ==", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
