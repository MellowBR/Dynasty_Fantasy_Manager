# -*- coding: utf-8 -*-
"""
espn_prov_badge_test.py — UX26: badge PROV por-jogador do cap projector.

Semântica verdadeira: PROV marca salário PROJETADO de fonte ESPN não-final. Jogador com
CONTRATO gravado na season corrente (evidência AuctionLog — família OFF26-29/UX23) nunca
exibe PROV, independentemente do carimbo do store — a raiz do badge errado nos 36 do
reparo é o `record_acquisition` → `set_espn_value` com default `is_final=False`.

Decisão calculada no SERVIDOR (`espn_prov` no payload); o JS só exibe. `espn_is_final`
segue no payload como dado cru do store, intocado.
"""

import unittest


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from models import db
        from routes.salary import salary_bp
        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["LOGIN_DISABLED"] = True
        cls.app.config["TESTING"] = True
        db.init_app(cls.app)
        cls.app.register_blueprint(salary_bp)
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        db.create_all()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        from models import db
        db.session.remove()
        db.drop_all()
        cls.ctx.pop()

    def setUp(self):
        from models import db, Team, Player, set_config
        db.session.remove()
        db.drop_all()
        db.create_all()
        set_config("current_season", "2026")
        set_config("rollover_done", "true")   # alvo/modo corrente (UX23): store 2026
        self.team = Team(name="Trust The Process")
        db.session.add(self.team)
        db.session.flush()

        def add(name, sid, salary=1, espn=0.0):
            p = Player(name=name, position="WR", team_id=self.team.id, salary=salary,
                       contract_year=1, acquisition_type="rookie_draft",
                       espn_ref_value=espn, sleeper_player_id=sid,
                       contract_start_season=2026)
            db.session.add(p)
            return p

        # rookie contratado pelo reparo: store row is_final=False (o default que o
        # record_acquisition grava) + AuctionLog rookie_draft 2026
        self.cooper = add("Omar Cooper", "13276", salary=1, espn=1.2)
        # veterano com valor provisório e SEM contrato 2026 — o caso legítimo de PROV
        self.vet = add("Veterano Prov", "5001", salary=10, espn=24.0)
        self.vet.acquisition_type = "auction_draft"
        self.vet.contract_start_season = 2025
        db.session.commit()

        from models import db as _db, set_espn_value, AuctionLog
        set_espn_value(self.cooper, 2026, 1.2)            # is_final default = False
        set_espn_value(self.vet, 2026, 24.0)              # idem — provisório real
        _db.session.add(AuctionLog(season=2026, player_id=self.cooper.id,
                                   team_id=self.team.id, player_name=self.cooper.name,
                                   team_name=self.team.name, entry_type="rookie_draft",
                                   value_paid=1))
        _db.session.commit()

    def _payload(self):
        r = self.client.get("/api/cap_projector/Trust%20The%20Process")
        self.assertEqual(r.status_code, 200)
        return {p["name"]: p for p in r.get_json()["players"]}


class TestCriterio(_Base):
    def test_contratado_na_season_nunca_exibe_prov(self):
        p = self._payload()["Omar Cooper"]
        self.assertFalse(p["espn_prov"],
                         "contrato gravado (AuctionLog 2026) — salário real, não projeção")
        self.assertIs(p["espn_is_final"], False,
                      "o dado CRU do store segue no payload, intocado")

    def test_caso_legitimo_de_prov_preservado(self):
        p = self._payload()["Veterano Prov"]
        self.assertTrue(p["espn_prov"],
                        "store provisório SEM contrato 2026 — o PROV continua")

    def test_store_final_nao_exibe(self):
        from models import db, set_espn_value
        set_espn_value(self.vet, 2026, 24.0, is_final=True)
        db.session.commit()
        self.assertFalse(self._payload()["Veterano Prov"]["espn_prov"])

    def test_sem_store_nao_exibe(self):
        from models import db, EspnValueStore
        EspnValueStore.query.delete()
        db.session.commit()
        pay = self._payload()
        self.assertFalse(pay["Omar Cooper"]["espn_prov"])
        self.assertFalse(pay["Veterano Prov"]["espn_prov"])


class TestGuardas(unittest.TestCase):
    def test_criterio_definido_so_em_models(self):
        import glob
        defs = [f for f in glob.glob("**/*.py", recursive=True)
                if not f.startswith((".", "_")) and "phantom_board_profile" not in f
                and not f.endswith("_test.py")
                and "def contracted_player_ids" in open(f, encoding="utf-8",
                                                        errors="replace").read()]
        self.assertEqual(defs, ["models.py"])

    def test_js_consome_a_decisao_do_servidor(self):
        with open("templates/cap_projector.html", encoding="utf-8") as f:
            src = f.read()
        self.assertIn("p.espn_prov", src)
        self.assertNotIn("espn_is_final === false", src,
                         "o JS não decide mais o badge pelo dado cru do store")


if __name__ == "__main__":
    unittest.main(verbosity=2)
