# -*- coding: utf-8 -*-
"""
planning_target_test.py — UX23: season-alvo de planejamento do cap projector.

Fonte única `models.planning_target_season()`:
  pré-rollover → current+1 · pós-rollover sem auction → current ·
  auction realizada (evidência AuctionLog fa_auction ≥ AUCTION_EVIDENCE_MIN) → current+1.

Guardas estáticas (molde OFF26-29): os sítios do projector NÃO podem voltar a derivar
`get_current_season() + 1` inline — nem a rota, nem o template.
"""

import ast
import unittest


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from models import db
        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["LOGIN_DISABLED"] = True
        cls.app.config["TESTING"] = True
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
        from models import db
        db.session.remove()
        db.drop_all()
        db.create_all()

    def _fa_logs(self, n, season=2026, entry_type="fa_auction"):
        from models import db, AuctionLog
        for i in range(n):
            db.session.add(AuctionLog(season=season, team_id=1, player_name=f"P{i}",
                                      team_name="T", entry_type=entry_type, value_paid=1))
        db.session.commit()


class TestFases(_Base):
    def test_pre_rollover_mira_a_proxima(self):
        from models import db, set_config, planning_target_season
        set_config("current_season", "2025")
        set_config("rollover_done", "false")
        db.session.commit()
        self.assertEqual(planning_target_season(), 2026)

    def test_pos_rollover_sem_auction_mira_a_corrente(self):
        from models import db, set_config, planning_target_season
        set_config("current_season", "2026")
        set_config("rollover_done", "true")
        db.session.commit()
        self.assertEqual(planning_target_season(), 2026,
                         "a janela operacional é a auction da season que acabou de virar")

    def test_auction_realizada_volta_a_proxima(self):
        from models import db, set_config, planning_target_season, AUCTION_EVIDENCE_MIN
        set_config("current_season", "2026")
        set_config("rollover_done", "true")
        db.session.commit()
        self._fa_logs(AUCTION_EVIDENCE_MIN)
        self.assertEqual(planning_target_season(), 2027)


class TestCalibracao(_Base):
    """O limiar protege a janela 20-24/08 de um registro avulso no /auction."""

    def setUp(self):
        super().setUp()
        from models import db, set_config
        set_config("current_season", "2026")
        set_config("rollover_done", "true")
        db.session.commit()

    def test_registro_avulso_nao_vira_a_chave(self):
        from models import planning_target_season, AUCTION_EVIDENCE_MIN
        self._fa_logs(AUCTION_EVIDENCE_MIN - 1)
        self.assertEqual(planning_target_season(), 2026,
                         "1-2 registros são assinatura de teste manual, não de leilão")

    def test_no_limiar_vira(self):
        from models import planning_target_season, AUCTION_EVIDENCE_MIN
        self._fa_logs(AUCTION_EVIDENCE_MIN)
        self.assertEqual(planning_target_season(), 2027)

    def test_rookie_draft_nao_conta_como_auction(self):
        from models import planning_target_season
        self._fa_logs(36, entry_type="rookie_draft")   # o estado real de prod hoje
        self.assertEqual(planning_target_season(), 2026,
                         "36 registros do draft não são evidência de FA auction")

    def test_fa_auction_de_outra_season_nao_conta(self):
        from models import planning_target_season, AUCTION_EVIDENCE_MIN
        self._fa_logs(AUCTION_EVIDENCE_MIN, season=2025)
        self.assertEqual(planning_target_season(), 2026)


class TestEndpointMode(_Base):
    """O payload do GET carrega target_season/mode — o cliente não deriva nada."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from routes.salary import salary_bp
        cls.app.register_blueprint(salary_bp)
        cls.client = cls.app.test_client()

    def test_payload_em_modo_corrente(self):
        from models import db, set_config, Team, Player
        set_config("current_season", "2026")
        set_config("rollover_done", "true")
        t = Team(name="Cangaceiros da Colina")
        db.session.add(t)
        db.session.flush()
        db.session.add(Player(name="X", position="QB", team_id=t.id, salary=10,
                              contract_year=1, acquisition_type="auction_draft"))
        db.session.commit()
        r = self.client.get("/api/cap_projector/Cangaceiros%20da%20Colina")
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertEqual((d["target_season"], d["mode"]), (2026, "corrente"))

    def test_payload_em_modo_projetado(self):
        from models import db, set_config, Team
        set_config("current_season", "2025")
        set_config("rollover_done", "false")
        db.session.add(Team(name="mongoloides"))
        db.session.commit()
        r = self.client.get("/api/cap_projector/mongoloides")
        d = r.get_json()
        self.assertEqual((d["target_season"], d["mode"]), (2026, "projetado"))

    def test_board_de_rookies_usa_o_alvo_de_fase(self):
        from models import db, set_config, upsert_rookie_espn
        set_config("current_season", "2026")
        set_config("rollover_done", "true")
        upsert_rookie_espn(2026, "9901", "Rookie X", "RB", "DAL",
                           espn_raw=40.0, espn_adjusted=48.0, in_class=True)
        db.session.commit()
        d = self.client.get("/api/cap_projector/rookies").get_json()
        self.assertEqual(d["season"], 2026)
        self.assertEqual(len(d["rookies"]), 1,
                         "pós-rollover o board lê a season CORRENTE (o store só tem ela)")


class TestGuardasEstaticas(unittest.TestCase):
    """⛔ `current+1` inline não pode voltar aos sítios do projector (F1: eram 6)."""

    PROJECTOR_FUNCS = {"cap_projector_page", "cap_projector_data",
                       "cap_projector_budget", "cap_projector_rookies",
                       "_planning_ctx"}

    def test_rotas_do_projector_sem_derivacao_inline(self):
        with open("routes/salary.py", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for fn in ast.walk(tree):
            if not (isinstance(fn, ast.FunctionDef) and fn.name in self.PROJECTOR_FUNCS):
                continue
            for node in ast.walk(fn):
                if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
                        and isinstance(node.left, ast.Call)
                        and isinstance(node.left.func, ast.Name)
                        and node.left.func.id == "get_current_season"):
                    self.fail(f"{fn.name}: derivação `get_current_season() + 1` inline "
                              f"voltou (linha {node.lineno}) — use planning_target_season()")

    def test_template_sem_derivacao_inline(self):
        with open("templates/cap_projector.html", encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("g_current_season + 1", src,
                         "o template deve receber target_season da rota")


if __name__ == "__main__":
    unittest.main(verbosity=2)
