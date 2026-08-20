# -*- coding: utf-8 -*-
"""
wv1_fix_coorte_b_test.py — testes do runner MAN-WV1-FIX-COORTE-B.

Âncoras exigidas pelo owner: um vivo cy3→2; o caso Dike (já correto, pulado); um dropado
pulado. Mais as guardas próprias da coorte B: DET e Bryce Young fora com motivo, nenhum
dinheiro se move, e o filtro pós-lock por roster ao vivo.
"""
import unittest

import wv1_fix_coorte as A
import wv1_fix_coorte_b as B


def st(**kw):
    base = {
        "player_id": 1, "name": "X", "team": "T",
        "contract_year": 3, "contract_start_season": 2025,
        "acquisition_type": "fa_waiver", "needs_review": False,
        "is_dropped": False, "salary": 1.0, "espn_ref_value": 1.0,
    }
    base.update(kw)
    return [base]


class TestCoorteBCongelada(unittest.TestCase):
    def test_9_sids_unicos(self):
        sids = [s for s, _ in B.COHORT_B]
        self.assertEqual(len(sids), 9)
        self.assertEqual(len(set(sids)), 9)

    def test_det_e_bryce_young_fora_com_motivo(self):
        """⛔ DET fora é requisito de correção: dentro, ele abortaria a execução inteira."""
        self.assertIn("DET", B.EXCLUDED)
        self.assertIn("9228", B.EXCLUDED)
        self.assertNotIn("DET", dict(B.COHORT_B))
        self.assertNotIn("9228", dict(B.COHORT_B))
        self.assertIn("free_agent", B.EXCLUDED["DET"])
        self.assertIn("coorte A", B.EXCLUDED["9228"])

    def test_det_dentro_da_lista_abortaria(self):
        """Prova do motivo da exclusão: canal free_agent dispara ABORT, não skip."""
        el, sk, ab = A.triage({"DET": st(acquisition_type="free_agent", is_dropped=True)},
                              cohort=[("DET", "Detroit Lions")], expected=A.EXPECTED)
        self.assertEqual(len(ab), 1)
        self.assertIn("acquisition_type", ab[0]["reason"])

    def test_nenhuma_intersecao_com_a_coorte_A(self):
        self.assertEqual(set(s for s, _ in B.COHORT_B) & set(s for s, _ in A.COHORT), set())

    def test_nenhuma_intersecao_com_o_censo_off26_32(self):
        import re
        census = set(re.findall(r'\("(\w+)",\s*"[^"]+"\)',
                                open("off26_32_fix.py", encoding="utf-8").read()))
        self.assertTrue(census)
        self.assertEqual(set(s for s, _ in B.COHORT_B) & census, set())

    def test_nenhum_dinheiro_se_move(self):
        """⭐ Invariante da coorte B: SALARY_FIXES vazio, como no OFF26-32."""
        self.assertEqual(B.SALARY_FIXES_B, {})

    def test_reusa_a_guarda_do_runner_A_sem_redefinir(self):
        """A guarda e a régua vêm do módulo A — zero réplica."""
        src = open("wv1_fix_coorte_b.py", encoding="utf-8").read()
        self.assertIn("import wv1_fix_coorte as A", src)
        self.assertNotIn("EXPECTED = {", src)
        self.assertNotIn("def triage(", src)

    def test_event_ref_separado_da_coorte_A(self):
        self.assertNotEqual(B.EVENT_REF, "fix:wv1-coorte")
        self.assertEqual(B.EVENT_REF, "fix:wv1-coorte-b")


class TestTriagemDaCoorteB(unittest.TestCase):
    def test_vivo_cy3_e_elegivel(self):
        """ÂNCORA: um vivo em cy=3 entra para 3→2."""
        states = {"3451": st(name="Fairbairn")}
        el, sk, ab = A.triage(states, cohort=[("3451", "Fairbairn")], expected=A.EXPECTED)
        self.assertEqual(el, ["3451"])
        self.assertEqual((sk, ab), ([], []))

    def test_dike_ja_correto_e_pulado_nao_abortado(self):
        """ÂNCORA Dike: cy=2 por MÉRITO (ano 1 = 2025 pelas duas rotas) → pulado, sem abortar."""
        states = {"12540": st(name="Chimere Dike", contract_year=2)}
        el, sk, ab = A.triage(states, cohort=[("12540", "Chimere Dike")], expected=A.EXPECTED)
        self.assertEqual(el, [])
        self.assertEqual(ab, [])
        self.assertIn("ja e 2", sk[0]["reason"])

    def test_dropado_e_pulado(self):
        """ÂNCORA: dropado no banco sai da lista (decisão 2 de 19/08)."""
        states = {"3678": st(name="Wil Lutz", is_dropped=True)}
        el, sk, ab = A.triage(states, cohort=[("3678", "Wil Lutz")], expected=A.EXPECTED)
        self.assertEqual(el, [])
        self.assertIn("DROPADO", sk[0]["reason"])


class TestFiltroPosLock(unittest.TestCase):
    def test_nao_rosterado_ao_vivo_vira_pulado(self):
        """⚠️ Pós-lock o banco está atrasado de propósito: o Sleeper é a autoridade."""
        el, sk = B._live_filter(["3451", "8259"], [], not_live={"8259"})
        self.assertEqual(el, ["3451"])
        self.assertEqual(len(sk), 1)
        self.assertEqual(sk[0]["sleeper_player_id"], "8259")
        self.assertIn("ao vivo", sk[0]["reason"])

    def test_sem_divergencia_nada_muda(self):
        el, sk = B._live_filter(["3451", "8259"], [], not_live=set())
        self.assertEqual(el, ["3451", "8259"])
        self.assertEqual(sk, [])

    def test_offline_nao_filtra(self):
        not_live, nota = B._resolve_live(["3451"], offline=True)
        self.assertEqual(not_live, set())
        self.assertIn("SEM cruzamento", nota)


class TestInvariante(unittest.TestCase):
    def test_projecao_e_salario_identicos_apos_a_correcao(self):
        states = {"3451": st(salary=1.0, espn_ref_value=1.0)}
        before = A._money_state(states, ["3451"])
        after = A.expected_money_after(states, ["3451"], fixes=B.SALARY_FIXES_B)
        self.assertEqual(A.money_diff(before, after), [])
        self.assertEqual(before["3451"], after["3451"])

    def test_nenhuma_correcao_de_salario_selecionada(self):
        states = {"BAL": st(salary=2.0)}
        to_fix, mm = A.select_salary_fixes(["BAL"], states, fixes=B.SALARY_FIXES_B)
        self.assertEqual((to_fix, mm), ([], []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
