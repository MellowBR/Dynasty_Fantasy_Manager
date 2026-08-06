"""
contract_year_correction_test.py — a porta canônica de correção de contract_year (OFF26-20-FIX).

Cobre as três camadas:
  1. Núcleo puro (`guard_mismatches`/`plan_correction`) — sem Flask/DB/rede.
  2. Camada ORM (`apply_contract_year_correction`) — SQLite em memória, molde cap_regua_test:
     escrita + trilha na MESMA transação (rollback do chamador desfaz as duas), guarda que pula
     sem forçar, idempotência.
  3. Configuração do runner one-shot (`off26_20_fix`) — a lista dos 22 travada, DEFs como
     string (a armadilha da coerção a inteiro), guarda idêntica ao estado aprovado no T4.
"""

import unittest

from contract_year_correction import (
    EVENT_TYPE, guard_mismatches, plan_correction, apply_contract_year_correction,
)


GUARD = {
    "contract_year": 2,
    "contract_start_season": 2025,
    "acquisition_type": "free_agent",
    "needs_review": False,
    "is_dropped": False,
}


def _state(**overrides):
    """Estado que casa a guarda; overrides criam a divergência sob teste."""
    base = {"contract_year": 2, "contract_start_season": 2025,
            "acquisition_type": "free_agent", "needs_review": False, "is_dropped": False}
    base.update(overrides)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# 1. Núcleo puro — a guarda
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardaPura(unittest.TestCase):

    def test_estado_aprovado_e_elegivel(self):
        self.assertEqual(guard_mismatches(_state(), GUARD), [])

    def test_cada_campo_da_guarda_barra(self):
        """Qualquer divergência num campo da guarda pula a linha — não corrige por força."""
        casos = [
            _state(contract_year=1),           # já corrigido
            _state(contract_year=3),
            _state(contract_start_season=2024),
            _state(acquisition_type="waiver"),
            _state(acquisition_type="fa_auction"),
            _state(needs_review=True),
            _state(is_dropped=True),
        ]
        for st in casos:
            self.assertNotEqual(guard_mismatches(st, GUARD), [], f"deveria barrar: {st}")

    def test_normalizacao_sql_vs_orm(self):
        """0/1 do SQL ≡ False/True; 2025.0 ≡ 2025 — a guarda não pode barrar por tipo."""
        st = _state(needs_review=0, is_dropped=0, contract_start_season=2025.0,
                    contract_year=2.0)
        self.assertEqual(guard_mismatches(st, GUARD), [])

    def test_plan_ausente_e_pulado(self):
        eligible, skipped = plan_correction(["8142"], {}, GUARD)
        self.assertEqual(eligible, [])
        self.assertIn("não encontrado", skipped[0]["reason"])

    def test_plan_ambiguo_e_pulado(self):
        """Duas linhas vivas com o mesmo sleeper_player_id: ninguém decide por adivinhação."""
        eligible, skipped = plan_correction(
            ["8142"], {"8142": [_state(), _state()]}, GUARD)
        self.assertEqual(eligible, [])
        self.assertIn("ambíguo", skipped[0]["reason"])

    def test_plan_def_por_sigla_sem_coercao(self):
        """DEFs usam sigla ('DET') — o plano casa por string, nunca coage a inteiro."""
        eligible, skipped = plan_correction(
            ["DET", "11603"], {"DET": [_state()], "11603": [_state()]}, GUARD)
        self.assertEqual(eligible, ["DET", "11603"])
        self.assertEqual(skipped, [])

    def test_plan_mistura_elegivel_e_pulado(self):
        eligible, skipped = plan_correction(
            ["8142", "8167"],
            {"8142": [_state()], "8167": [_state(needs_review=True)]},
            GUARD)
        self.assertEqual(eligible, ["8142"])
        self.assertEqual(skipped[0]["sleeper_player_id"], "8167")
        self.assertIn("needs_review", skipped[0]["reason"])


# ══════════════════════════════════════════════════════════════════════════════
# 2. Camada ORM — escrita + trilha atômicas
# ══════════════════════════════════════════════════════════════════════════════

class TestPortaORM(unittest.TestCase):
    """SQLite em memória (mesmo padrão do cap_regua_test) — nunca toca o dynasty.db."""

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from models import db
        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(cls.app)
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        from models import db
        db.session.remove()
        db.drop_all()
        cls.ctx.pop()

    def setUp(self):
        from models import db, Team, Player
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.team = Team(name="Cangaceiros da Colina")
        db.session.add(self.team)
        db.session.commit()

        def fa(sid, name, espn=1.0, **overrides):
            fields = dict(sleeper_player_id=sid, name=name, position="WR",
                          team_id=self.team.id, salary=1.0, contract_year=2,
                          contract_start_season=2025, acquisition_type="free_agent",
                          espn_ref_value=espn, needs_review=False, is_dropped=False)
            fields.update(overrides)
            return Player(**fields)

        self.pierce = fa("8142", "Alec Pierce", espn=7.0)
        self.lions = fa("DET", "Detroit Lions", position="DEF")
        self.em_revisao = fa("9999", "Em Revisão", needs_review=True)
        # FA 2025 idêntico aos 22, mas FORA da lista — não pode ser tocado.
        self.fora_da_lista = fa("7777", "Fora da Lista")
        db.session.add_all([self.pierce, self.lions, self.em_revisao, self.fora_da_lista])
        db.session.commit()

    def _apply(self, ids):
        return apply_contract_year_correction(
            ids, expected=GUARD, new_year=1, reason="Correção de teste",
            event_ref="fix:test", season=2026)

    def test_corrige_e_grava_trilha(self):
        from models import db, PlayerHistory
        result = self._apply(["8142"])
        db.session.commit()

        self.assertEqual([a["sleeper_player_id"] for a in result["applied"]], ["8142"])
        self.assertEqual(self.pierce.contract_year, 1)

        ph = PlayerHistory.query.filter_by(player_id=self.pierce.id).one()
        self.assertEqual(ph.event_type, EVENT_TYPE)
        self.assertEqual(ph.contract_year, 1)
        self.assertEqual(ph.sleeper_event_ref, "fix:test")
        self.assertIn("contract_year 2 -> 1", ph.notes)
        self.assertIn("Correção de teste", ph.notes)
        self.assertEqual(ph.season, 2026)
        self.assertEqual(ph.team_name, "Cangaceiros da Colina")

    def test_demais_campos_intocados(self):
        from models import db
        self._apply(["8142"])
        db.session.commit()
        self.assertEqual(self.pierce.salary, 1.0)
        self.assertEqual(self.pierce.contract_start_season, 2025)
        self.assertEqual(self.pierce.acquisition_type, "free_agent")
        self.assertEqual(self.pierce.espn_ref_value, 7.0)
        self.assertFalse(self.pierce.needs_review)

    def test_def_por_sigla(self):
        from models import db
        result = self._apply(["DET"])
        db.session.commit()
        self.assertEqual(len(result["applied"]), 1)
        self.assertEqual(self.lions.contract_year, 1)

    def test_guarda_pula_needs_review_sem_forcar(self):
        from models import db, PlayerHistory
        result = self._apply(["9999"])
        db.session.commit()
        self.assertEqual(result["applied"], [])
        self.assertIn("needs_review", result["skipped"][0]["reason"])
        self.assertEqual(self.em_revisao.contract_year, 2)
        self.assertEqual(PlayerHistory.query.count(), 0)

    def test_quem_esta_fora_da_lista_nao_e_tocado(self):
        from models import db
        self._apply(["8142"])
        db.session.commit()
        self.assertEqual(self.fora_da_lista.contract_year, 2)

    def test_rollback_do_chamador_desfaz_escrita_e_trilha_juntas(self):
        """A porta NÃO comita — escrita e trilha vivem ou morrem na mesma transação."""
        from models import db, PlayerHistory
        self._apply(["8142"])
        db.session.rollback()
        self.assertEqual(self.pierce.contract_year, 2)
        self.assertEqual(PlayerHistory.query.count(), 0)

    def test_idempotencia_segunda_execucao_pula_tudo(self):
        """Na 2ª passada, contract_year=1 não casa a guarda: zero escrita, zero trilha nova."""
        from models import db, PlayerHistory
        self._apply(["8142", "DET"])
        db.session.commit()
        result2 = self._apply(["8142", "DET"])
        db.session.commit()
        self.assertEqual(result2["applied"], [])
        self.assertEqual(len(result2["skipped"]), 2)
        self.assertEqual(PlayerHistory.query.count(), 2)

    def test_dropado_duplicado_torna_ambiguo(self):
        """Linha dropada com o mesmo sleeper_id: pulado como ambíguo (nunca adivinhar)."""
        from models import db, Player, PlayerHistory
        db.session.add(Player(sleeper_player_id="8142", name="Alec Pierce (dropado)",
                              position="WR", salary=1.0, contract_year=2,
                              contract_start_season=2025, acquisition_type="free_agent",
                              needs_review=False, is_dropped=True))
        db.session.commit()
        result = self._apply(["8142"])
        db.session.commit()
        self.assertEqual(result["applied"], [])
        self.assertIn("ambíguo", result["skipped"][0]["reason"])
        self.assertEqual(self.pierce.contract_year, 2)
        self.assertEqual(PlayerHistory.query.count(), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Runner one-shot — a lista dos 22 travada e a guarda aprovada
# ══════════════════════════════════════════════════════════════════════════════

class TestRunnerOff2620(unittest.TestCase):

    def test_lista_tem_exatamente_os_22(self):
        import off26_20_fix as run
        ids = [sid for sid, _ in run.TARGETS]
        self.assertEqual(len(ids), 22)
        self.assertEqual(len(set(ids)), 22, "id duplicado na lista")

    def test_defs_por_sigla_como_string(self):
        import off26_20_fix as run
        ids = {sid for sid, _ in run.TARGETS}
        self.assertTrue({"DET", "HOU", "IND", "LAR", "NO"} <= ids)
        for sid, _ in run.TARGETS:
            self.assertIsInstance(sid, str, f"{sid!r} não é string")

    def test_guarda_do_runner_e_o_estado_aprovado_no_t4(self):
        import off26_20_fix as run
        self.assertEqual(run.EXPECTED, GUARD)
        self.assertEqual(run.NEW_YEAR, 1)

    def test_casos_vivos_da_validacao(self):
        """Pierce $5, Watson $4, P. Washington $4, Wilson $2 — com o ESPN REF atual."""
        import off26_20_fix as run
        self.assertEqual(run.LIVE_CASES, {"8142": 5, "8167": 4, "9487": 4, "10232": 2})
        # A conta em si, pelo motor real (floor(0.8×espn), piso $1):
        self.assertEqual(run._dry_run_rollover(1.0, 7.0, "free_agent")[0], 5)   # Pierce
        self.assertEqual(run._dry_run_rollover(1.0, 6.0, "free_agent")[0], 4)   # Watson / P.W.
        self.assertEqual(run._dry_run_rollover(1.0, 3.0, "free_agent")[0], 2)   # Wilson
        self.assertEqual(run._dry_run_rollover(1.0, 1.0, "free_agent")[0], 1)   # massa $1

    def test_dry_run_devolve_regra_de_waiver_ano2(self):
        import off26_20_fix as run
        _, new_yr, rule = run._dry_run_rollover(1.0, 7.0, "free_agent")
        self.assertEqual(new_yr, 2)
        self.assertIn("Waiver Ano 2", rule)


if __name__ == "__main__":
    unittest.main(verbosity=2)
