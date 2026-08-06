"""
trilha_fa_proj_test.py — OFF26-20-CLOSE: enum `fa_waiver` na trilha de FA (T2) +
coluna PROJ na fonte única (T4).

T2 — decisão do owner (06/08/2026): quem entra por waiver SEM contrato prévio a carregar
segue a trilha de FA (ano 1 = $1, ano 2 = 0,8 × ESPN REF). `fa_waiver` — o valor que o
`sync_sleeper` grava para waiver claims — entra em `_WAIVER_TYPES`. Alcance medido no banco
na hora da mudança (06/08): **5 em ano 1** (Dike, Noel, Willis, Gadsden, Shough — os únicos
que o ramo 0,8 alcança) e **32 em ano 2** (contrato carregado; `next_yr = 3` ⇒ nunca entram
no ramo 0,8 — seguem em VALORIZAÇÃO, inalterados).

Caso Noel (registrado, decisão do owner): waiver $0 pelo próprio time que o draftou —
padrão 6.8, efeito prático hoje nulo (ESPN REF 1.0 ⇒ $1 nas duas trilhas), incluído na
trilha FA por decisão explícita.

T4 — a coluna PROJ de `/` e `/team/<id>` (`_macros.html`, via `Player.projected_next_salary()`)
passa a delegar a `salary_engine.project_next_salary` — a MESMA fonte do Cap Projector, da
porta `/budget` e do rollover real. A reconstrução via `compute_salary_for_year` (que
descartava o salário armazenado) morreu nesse método; há guarda para não ressuscitar.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace

from salary_engine import (
    _WAIVER_TYPES, year1_salary, apply_season_rollover, project_next_salary,
    valorization_rule,
)

BASE_DIR = Path(__file__).resolve().parent


def fake(acq, salary, espn, cy):
    return SimpleNamespace(acquisition_type=acq, salary=salary,
                           espn_ref_value=espn, contract_year=cy)


# ══════════════════════════════════════════════════════════════════════════════
# T2 — fa_waiver na trilha de FA
# ══════════════════════════════════════════════════════════════════════════════

class TestFaWaiverTrilhaFA(unittest.TestCase):

    def test_fa_waiver_esta_no_vocabulario(self):
        self.assertIn("fa_waiver", _WAIVER_TYPES)

    def test_ano1_e_1_dolar(self):
        """Waiver sem contrato prévio entra de graça — mesmo com lance FAAB registrado."""
        self.assertEqual(year1_salary("fa_waiver", 0, 60.0), 1)
        self.assertEqual(year1_salary("fa_waiver", 7, 60.0), 1)

    def test_rollover_ano1_para_ano2_aplica_0_8(self):
        """O coração da decisão: fa_waiver em ano 1 rola para 0,8×ESPN REF, não valorização."""
        new_sal, new_yr, rule = apply_season_rollover(fake("fa_waiver", 1.0, 6.0, 1))
        self.assertEqual((new_sal, new_yr), (4, 2))          # floor(0.8×6.0)=4
        self.assertIn("Waiver Ano 2", rule)

    def test_os_5_reais_hoje_dao_piso_1(self):
        """Dike, Noel, Willis, Gadsden, Shough: $1, ESPN REF 1.0 → 0,8 trunca no piso $1.
        Efeito prático hoje nulo; a trilha certa aparece quando a ESPN definitiva entrar."""
        for nome in ("Dike", "Noel", "Willis", "Gadsden", "Shough"):
            new_sal, new_yr, _ = apply_season_rollover(fake("fa_waiver", 1.0, 1.0, 1))
            self.assertEqual((new_sal, new_yr), (1, 2), nome)

    def test_contrato_carregado_ano2_segue_valorizacao(self):
        """Representante dos 32 (ex.: Adonai Mitchell $2, ESPN 1.0, ano 2): next_yr=3 nunca
        entra no ramo 0,8 — VALORIZAÇÃO idêntica à de antes do enum."""
        new_sal, new_yr, rule = apply_season_rollover(fake("fa_waiver", 2.0, 1.0, 2))
        self.assertEqual((new_sal, new_yr), (2, 3))          # max(2, floor(0.5×1))=2
        self.assertIn("VALORIZAÇÃO", rule)
        self.assertEqual(new_sal, valorization_rule(2.0, 1.0))

    def test_alcance_do_0_8_e_so_o_ano1(self):
        """A guarda de alcance como regra: em todo o ciclo, só a transição 1→2 usa 0,8."""
        espn = 10.0
        s2, _, r2 = apply_season_rollover(fake("fa_waiver", 1.0, espn, 1))
        self.assertEqual(s2, 8)                               # 1→2: floor(0.8×10)
        self.assertIn("Waiver Ano 2", r2)
        for cy in (2, 3):
            _, yr, rule = apply_season_rollover(fake("fa_waiver", 8.0, espn, cy))
            self.assertEqual(yr, cy + 1)
            self.assertIn("VALORIZAÇÃO", rule)
        _, yr, rule = apply_season_rollover(fake("fa_waiver", 8.0, espn, 4))
        self.assertEqual(yr, 1)                               # 4→renovação
        self.assertIn("Renovação", rule)

    def test_projecao_consistente_com_rollover(self):
        """project_next_salary (PROJ/Cap Projector) e apply_season_rollover concordam."""
        for cy in (1, 2, 3, 4):
            p = fake("fa_waiver", 3.0, 9.0, cy)
            self.assertEqual(project_next_salary(p), apply_season_rollover(p)[0], f"cy={cy}")


# ══════════════════════════════════════════════════════════════════════════════
# T4 — coluna PROJ na fonte única
# ══════════════════════════════════════════════════════════════════════════════

class TestProjFonteUnica(unittest.TestCase):
    """`Player.projected_next_salary()` (o consumidor é a coluna PROJ em `_macros.html`)
    delega à fonte que respeita o salário armazenado. Player é instanciado direto —
    sem DB — porque o método é puro sobre os atributos."""

    def _player(self, acq, salary, espn, cy):
        from models import Player
        return Player(name="x", position="WR", acquisition_type=acq, salary=salary,
                      espn_ref_value=espn, contract_year=cy)

    def test_hampton_26_nao_44(self):
        """Rookie $26 com ESPN 44: a reconstrução mostrava $44; a fonte única dá $26."""
        self.assertEqual(self._player("rookie_draft", 26.0, 44.0, 1).projected_next_salary(), 26)

    def test_jeanty_57_nao_45(self):
        """O caso que SOBE — salário $57 > ESPN 45: valorização preserva os $57."""
        self.assertEqual(self._player("rookie_draft", 57.0, 45.0, 1).projected_next_salary(), 57)

    def test_egbuka_13_nao_26(self):
        self.assertEqual(self._player("rookie_draft", 2.0, 26.0, 1).projected_next_salary(), 13)

    def test_mcmillan_15_nao_30(self):
        self.assertEqual(self._player("rookie_draft", 8.0, 30.0, 1).projected_next_salary(), 15)

    def test_watson_da_f1_agora_3_nao_4(self):
        """O caso que abriu a F1: free_agent ano 2, $1, ESPN 6 — tela dizia $4, rollover fará
        $3 (valorização de $1). Agora a tela diz o que o rollover fará."""
        self.assertEqual(self._player("free_agent", 1.0, 6.0, 2).projected_next_salary(), 3)

    def test_pierce_pos_correcao_5(self):
        """Os 22 corrigidos (ano 1): a PROJ passa a exibir o valor do dry-run (Pierce $5)."""
        self.assertEqual(self._player("free_agent", 1.0, 7.0, 1).projected_next_salary(), 5)

    def test_sem_espn_devolve_salario(self):
        self.assertEqual(self._player("auction_draft", 12.0, 0.0, 2).projected_next_salary(), 12)

    def test_iguala_o_rollover_em_todo_tipo(self):
        """A tela e a escrita de 18/08 não podem divergir — em nenhum tipo, em nenhum ano."""
        for acq in ("auction_draft", "rookie_draft", "free_agent", "fa_waiver", "waiver"):
            for cy in (1, 2, 3, 4):
                p = self._player(acq, 5.0, 14.0, cy)
                self.assertEqual(p.projected_next_salary(), apply_season_rollover(p)[0],
                                 f"{acq} cy={cy}")


class TestGuardaAntiReplica(unittest.TestCase):
    """A reconstrução não pode voltar à PROJ (molde do TestSemReplicaDeFolha do OFF26-16)."""

    def test_models_nao_reconstroi_contrato(self):
        """`compute_salary_for_year` reconstrói do ano 1 — display de contrato completo é da
        calculadora (`full_contract_table`), nunca de projeção em models.py."""
        src = (BASE_DIR / "models.py").read_text(encoding="utf-8")
        self.assertNotIn("compute_salary_for_year", src,
                         "a réplica reconstrutora ressuscitou em models.py")

    def test_coluna_proj_segue_no_consumidor_unico(self):
        """`_macros.html` continua consumindo projected_next_salary() — que agora delega."""
        src = (BASE_DIR / "templates" / "_macros.html").read_text(encoding="utf-8")
        self.assertIn("projected_next_salary()", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
