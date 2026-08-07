"""
keeper_audit_stage_test.py — OFF26-22: a auditoria reconhece sheet PROVISÓRIA.

Arquivo SEPARADO de propósito: os 34 testes do núcleo puro (`keeper_audit_test.py`) e as
fixtures congeladas **não podem ser editados**, e a garantia de que continuam valendo é
que nada aqui os toca. O que se testa aqui é a **camada de leitura** — `_stage_meta`,
`build_sheet` e `qualify` —, que roda em volta do núcleo sem mudar o que ele vê.

A pergunta: *o relatório pode dizer "pode abrir o leilão" com base numa sheet que ainda
vai mudar?* Antes deste item, podia — o gate `if not raw.get("revealed")` virou código
morto no U7, e o estágio, embora calculado, era descartado na montagem.

    python keeper_audit_stage_test.py
"""

import json
import unittest
from datetime import datetime, timedelta

import keeper_audit as ka
import keeper_audit_fixtures as fx


def _meta(stage="definitiva", available=True, revealed=True, sync="2026-08-22T18:00:00Z",
          executed="2026-08-22T15:00:00Z", num_drops=3):
    """Carimbo no formato que `_stage_meta` produz (o que `qualify` consome)."""
    return ka._stage_meta({
        "available": available,
        "teams": [{"team_id": 1}] if available else [],
        "stage": stage,
        "stage_label": {"definitiva": "DEFINITIVA"}.get(stage, "PROVISÓRIA"),
        "sync_timestamp": sync,
        "source": "sync",
        "late_drop": {"revealed": revealed, "executed_at": executed,
                      "num_drops": num_drops, "result_hash": "abc"},
    })


# ══════════════════════════════════════════════════════════════════════════════
# `qualify` — a decisão de autoridade, sobre o relatório já pronto
# ══════════════════════════════════════════════════════════════════════════════

# Nenhum par das fixtures congeladas produz "liberada" (todas têm 9 times não
# populados por desenho). Para contrastar gate × não-gate com o NÚCLEO REAL, e não com
# um dicionário sintético, monta-se aqui o menor cenário coerente possível.
BOARD_OK = {
    "league_id": "1", "league_name": "Fantasma", "draft_id": "9",
    "draft_status": "pre_draft", "draft_type": "auction", "rounds": 22, "budget": 200,
    "columns": [{"roster_id": "1", "owner_id": "O1"}],
    "designations": [{"roster_id": "1", "sleeper_player_id": "4881",
                      "name": "Lamar Jackson", "position": "QB", "amount": "40"}],
}
SHEET_OK = {
    "revealed": True, "season": 2026, "lock_timestamp": "2026-08-22T18:00:00Z",
    "teams": [{"team_id": 1, "team_name": "Time A", "sleeper_owner_id": "O1",
               "fa_budget": 160, "keepers": [("4881", "Lamar Jackson", "QB", 40)]}],
}


class TestGateRealLiberado(unittest.TestCase):
    """O contraste que importa: o MESMO insumo coerente, nos dois estágios."""

    def test_definitiva_libera(self):
        rep = ka.qualify(ka.audit(BOARD_OK, SHEET_OK), _meta())
        self.assertEqual(rep["verdict"], ka.VERDICT_LIBERADA)
        self.assertTrue(rep["gate_qualified"])
        self.assertEqual(rep["summary"]["divergences"], 0)

    def test_provisoria_NAO_libera_o_mesmo_insumo(self):
        rep = ka.qualify(ka.audit(BOARD_OK, SHEET_OK), _meta(stage="provisoria"))
        self.assertEqual(rep["verdict"], ka.VERDICT_NAO_QUALIFICADA)
        self.assertFalse(rep["gate_qualified"])
        # o diff é o mesmo — zero divergências; o que muda é a AUTORIDADE
        self.assertEqual(rep["summary"]["divergences"], 0)
        self.assertIn("NÃO vale como gate", rep["blocking_reasons"][0])


class TestQualifyDefinitiva(unittest.TestCase):
    """Sheet DEFINITIVA: comportamento IDÊNTICO ao de hoje."""

    def _report(self, board, sheet):
        return ka.audit(board, sheet)

    def test_liberada_continua_liberada_e_vale_como_gate(self):
        base = self._report(fx.BOARD_A, fx.SHEET_A)
        # fixture A é coerente, mas tem 9 times não populados → o núcleo bloqueia
        self.assertEqual(base["verdict"], "bloqueada")
        rep = ka.qualify(self._report(fx.BOARD_A, fx.SHEET_A), _meta())
        self.assertEqual(rep["verdict"], "bloqueada")
        self.assertFalse(rep["gate_qualified"])

    def test_relatorio_identico_exceto_pelas_chaves_novas(self):
        """Item 2 da validação: mesmo insumo → mesmo relatório, campo a campo."""
        antes = self._report(fx.BOARD_A, fx.SHEET_A)
        depois = ka.qualify(self._report(fx.BOARD_A, fx.SHEET_A), _meta())
        novas = {"sheet_stage", "gate_qualified"}
        self.assertEqual(set(depois) - set(antes), novas)
        for k in antes:
            self.assertEqual(json.dumps(antes[k], sort_keys=True, default=str),
                             json.dumps(depois[k], sort_keys=True, default=str),
                             f"campo {k} mudou com sheet definitiva")

    def test_gate_qualified_true_so_quando_liberada(self):
        rep = {"verdict": "liberada", "blocking_reasons": []}
        self.assertTrue(ka.qualify(rep, _meta())["gate_qualified"])
        rep2 = {"verdict": "bloqueada", "blocking_reasons": ["x"]}
        self.assertFalse(ka.qualify(rep2, _meta())["gate_qualified"])


class TestQualifyProvisoria(unittest.TestCase):
    """Sheet PROVISÓRIA: roda, lista tudo, mas NÃO é gate."""

    def test_liberada_vira_nao_qualificada(self):
        rep = ka.qualify({"verdict": "liberada", "blocking_reasons": []},
                         _meta(stage="provisoria"))
        self.assertEqual(rep["verdict"], ka.VERDICT_NAO_QUALIFICADA)
        self.assertFalse(rep["gate_qualified"])

    def test_liberada_e_impossivel_em_qualquer_combinacao_provisoria(self):
        """A garantia central do item: nenhum caminho produz 'liberada' com provisória."""
        for revealed in (True, False):
            for verdict in ("liberada", "bloqueada"):
                rep = ka.qualify({"verdict": verdict, "blocking_reasons": []},
                                 _meta(stage="provisoria", revealed=revealed))
                self.assertNotEqual(rep["verdict"], ka.VERDICT_LIBERADA)
                self.assertFalse(rep["gate_qualified"])

    def test_divergencias_continuam_listadas(self):
        """O valor da execução antecipada: o que ela achou não some."""
        rep = ka.qualify({"verdict": "bloqueada",
                          "blocking_reasons": ["2 keeper(s) ausente(s) do board."]},
                         _meta(stage="provisoria"))
        self.assertIn("2 keeper(s) ausente(s) do board.", rep["blocking_reasons"])

    def test_motivo_do_estagio_vem_primeiro(self):
        rep = ka.qualify({"verdict": "bloqueada", "blocking_reasons": ["outra coisa"]},
                         _meta(stage="provisoria"))
        self.assertIn("NÃO vale como gate", rep["blocking_reasons"][0])
        self.assertEqual(rep["blocking_reasons"][-1], "outra coisa")

    def test_nomeia_o_estado_perigoso_com_os_dois_carimbos(self):
        """Revelada e sem sync depois: o relatório diz QUANDO revelou e QUAL é o sync."""
        m = _meta(stage="provisoria", revealed=True,
                  executed="2026-08-22T15:00:00Z", sync="2026-08-20T09:00:00Z")
        rep = ka.qualify({"verdict": "liberada", "blocking_reasons": []}, m)
        texto = rep["blocking_reasons"][0]
        self.assertIn("2026-08-22T15:00:00Z", texto)
        self.assertIn("2026-08-20T09:00:00Z", texto)
        self.assertIn("sync final", texto)

    def test_urna_nao_revelada_diz_isso_e_nao_o_outro(self):
        m = _meta(stage="provisoria", revealed=False)
        self.assertIn("ainda não foi revelada", m["missing"])
        self.assertNotIn("sync final", m["missing"])

    def test_relatorio_completo_preservado(self):
        base = ka.audit(fx.BOARD_A, fx.SHEET_A)
        rep = ka.qualify(ka.audit(fx.BOARD_A, fx.SHEET_A), _meta(stage="provisoria"))
        self.assertEqual(len(rep["teams"]), len(base["teams"]))
        self.assertEqual(rep["summary"], base["summary"])


class TestQualifySemInsumo(unittest.TestCase):
    """Sheet indisponível: bloqueio por falta de insumo — REVIVIDO."""

    def test_bloqueia_e_diz_a_causa_real(self):
        rep = ka.qualify(ka.audit(fx.BOARD_A, {"revealed": False, "season": 2026}),
                         _meta(available=False))
        self.assertEqual(rep["verdict"], "bloqueada")
        self.assertFalse(rep["gate_qualified"])
        self.assertIn("indisponível", rep["blocking_reasons"][0])

    def test_nao_vira_nao_qualificada(self):
        """Sem insumo é outro ramo — não se confunde com provisória."""
        rep = ka.qualify(ka.audit(None, {"revealed": False, "season": 2026}),
                         _meta(available=False, stage="provisoria"))
        self.assertNotEqual(rep["verdict"], ka.VERDICT_NAO_QUALIFICADA)


class TestStageMeta(unittest.TestCase):
    """`_stage_meta` CONSOME a decisão da fonte — não a recalcula."""

    def test_nao_recalcula_o_estagio(self):
        """Mesmo com carimbos que 'pareceriam' definitivos, vale o `stage` da fonte."""
        m = _meta(stage="provisoria", revealed=True,
                  executed="2026-08-22T15:00:00Z", sync="2026-08-22T23:00:00Z")
        self.assertFalse(m["is_definitiva"])
        m2 = _meta(stage="definitiva", revealed=False, sync=None)
        self.assertTrue(m2["is_definitiva"])
        self.assertIsNone(m2["missing"])

    def test_available_exige_sheet_disponivel_E_times(self):
        self.assertFalse(ka._stage_meta({"available": True, "teams": [],
                                         "stage": "definitiva"})["available"])
        self.assertFalse(ka._stage_meta({"available": False, "teams": [{"team_id": 1}],
                                         "stage": "definitiva"})["available"])
        self.assertTrue(ka._stage_meta({"available": True, "teams": [{"team_id": 1}],
                                        "stage": "definitiva"})["available"])

    def test_sheet_vazia_nao_explode(self):
        m = ka._stage_meta({})
        self.assertFalse(m["available"])
        self.assertFalse(m["is_definitiva"])


class TestNucleoNaoVeOEstagio(unittest.TestCase):
    """⛔ Invariante do item: o carimbo viaja POR FORA da estrutura que o núcleo lê."""

    def test_audit_nao_menciona_stage(self):
        with open("keeper_audit.py", encoding="utf-8") as fh:
            src = fh.read()
        nucleo = src.split("def audit(")[1].split("\ndef _finding(")[0]
        for proibido in ("stage", "gate_qualified", "sheet_stage"):
            self.assertNotIn(proibido, nucleo,
                             f"o núcleo puro passou a olhar `{proibido}` — o estágio é "
                             f"metadado do relatório, nunca insumo do diff")

    def test_qualify_com_meta_none_nao_quebra(self):
        rep = ka.qualify({"verdict": "liberada", "blocking_reasons": []}, None)
        self.assertTrue(rep["gate_qualified"])


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRAÇÃO — `build_sheet`/`run_audit` com ORM em memória (sem rede)
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegracaoORM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from models import db
        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(cls.app)

    def setUp(self):
        from models import db, Team, Player, SyncLog, get_current_season
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            t = Team(name="Time A", sleeper_owner_id="OWNER-A")
            db.session.add(t)
            db.session.commit()
            db.session.add(Player(name="Lamar Jackson", position="QB", salary=40.0,
                                  team_id=t.id, sleeper_player_id="4881"))
            db.session.add(SyncLog(synced_at=datetime.utcnow()))
            db.session.commit()
            self.season = get_current_season()
            self.t_id = t.id

    def _reveal(self, sync_after=True):
        from models import db, SyncLog, LateDropAudit, compute_cut_snapshot_hash
        with self.app.app_context():
            snap = [{"team_id": self.t_id, "team_name": "Time A", "cut_ids": [],
                     "drop_id": None, "drop_name": None, "declared": True}]
            t0 = datetime.utcnow() + timedelta(hours=1)
            db.session.add(LateDropAudit(
                season=self.season, declarations_json=json.dumps(snap),
                executed_at=t0, result_hash=compute_cut_snapshot_hash(snap),
                is_canonical=True))
            if sync_after:
                db.session.add(SyncLog(synced_at=t0 + timedelta(minutes=5)))
            db.session.commit()

    def _sheet(self):
        with self.app.app_context():
            return ka.build_sheet(self.season)

    def test_build_sheet_carrega_o_carimbo(self):
        s = self._sheet()
        self.assertIn("stage_meta", s)
        self.assertEqual(s["stage_meta"]["stage"], "provisoria")
        self.assertFalse(s["stage_meta"]["is_definitiva"])

    def test_carimbo_vira_definitiva_pelo_sync_posterior(self):
        self._reveal(sync_after=True)
        self.assertTrue(self._sheet()["stage_meta"]["is_definitiva"])

    def test_revelada_sem_sync_continua_provisoria(self):
        """O estado perigoso: drops revelados e não executados/sincronizados."""
        self._reveal(sync_after=False)
        m = self._sheet()["stage_meta"]
        self.assertFalse(m["is_definitiva"])
        self.assertIn("sync final", m["missing"])

    def test_run_audit_desqualifica_sobre_provisoria(self):
        from models import db, set_config
        with self.app.app_context():
            set_config(ka.PHANTOM_LEAGUE_KEY, "")   # board indisponível é irrelevante aqui
            db.session.commit()
            rep = ka.run_audit(self.season)
        self.assertFalse(rep["gate_qualified"])
        self.assertNotEqual(rep["verdict"], ka.VERDICT_LIBERADA)
        self.assertEqual(rep["sheet_stage"]["stage"], "provisoria")

    def test_o_nucleo_nunca_recebe_stage_meta(self):
        """`run_audit` remove o carimbo antes de chamar `audit()`."""
        visto = {}
        orig = ka.audit

        def espiao(board, sheet):
            visto["chaves"] = sorted(sheet or {})
            return orig(board, sheet)

        ka.audit = espiao
        try:
            with self.app.app_context():
                ka.run_audit(self.season)
        finally:
            ka.audit = orig
        self.assertNotIn("stage_meta", visto["chaves"])
        self.assertIn("teams", visto["chaves"])

    def test_sem_times_e_indisponivel(self):
        from models import db, Team, Player
        with self.app.app_context():
            Player.query.delete()
            Team.query.delete()
            db.session.commit()
            s = ka.build_sheet(self.season)
            rep = ka.run_audit(self.season)
        self.assertFalse(s["stage_meta"]["available"])
        self.assertNotIn("teams", s)
        self.assertFalse(rep["gate_qualified"])
        self.assertIn("indisponível", rep["blocking_reasons"][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
