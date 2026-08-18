# -*- coding: utf-8 -*-
"""
picks_inventory_test.py — UX22: visão de INVENTÁRIO no board de picks quando a season
ainda não tem ordem (sem sorteio travado, sem classificação).

O que se prova (ORM em memória + render real do template, sem rede):
  * season COM picks e SEM ordem → seção renderiza o inventário: células por rodada com
    dono atual, "via <original>" na trocada, contagem por time — e NENHUM número de
    posição (ordem não se inventa).
  * o gancho do filtro/realce (data-team-name) está nas células do inventário — é a
    superfície que o JS existente consome (filtro por equipe funciona de graça).
  * season COM ordem (standings fixture) → render ordenado ANTIGO intacto (posições
    R.PP presentes, sem inventário para aquela season).
  * pick consumida (OFF26-29) fora de QUALQUER visão — inclusive do inventário.
"""

import re
import unittest


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db
        from routes.picks import picks_bp
        from routes.trades import trades_bp   # url_for('trades.trades_page') no template

        cls.app = Flask(__name__, template_folder="templates", static_folder="static")
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["LOGIN_DISABLED"] = True
        cls.app.config["TESTING"] = True
        cls.app.config["SECRET_KEY"] = "t"
        db.init_app(cls.app)
        lm = LoginManager()
        lm.init_app(cls.app)                  # current_user (anônimo) no template
        lm.user_loader(lambda uid: None)      # nunca chamado (anônimo), mas exigido
        from timeutil import utc_iso          # M18: filtro que o create_app registra
        cls.app.jinja_env.filters["utc_iso"] = utc_iso
        cls.app.register_blueprint(picks_bp)
        cls.app.register_blueprint(trades_bp)
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
        from models import db, Team
        db.session.remove()
        db.drop_all()
        db.create_all()
        # 12 times (o board é de liga de 12; a fixture de standings exige o vetor cheio)
        self.teams = []
        for i in range(1, 13):
            t = Team(name=f"Time {i:02d}")
            db.session.add(t)
            self.teams.append(t)
        db.session.flush()
        db.session.commit()

    def _pick(self, season, rnd, orig, cur=None, traded=False):
        from models import db, Pick
        cur = cur or orig
        pk = Pick(season=season, round=rnd, original_team_id=orig.id,
                  current_team_id=cur.id, original_team_name=orig.name,
                  current_team_name=cur.name, traded_away=traded)
        db.session.add(pk)
        return pk

    def _page(self):
        r = self.client.get("/picks")
        self.assertEqual(r.status_code, 200)
        return r.get_data(as_text=True)


class TestInventario(_Base):
    def setUp(self):
        super().setUp()
        from models import db
        t1, t2, t3 = self.teams[0], self.teams[1], self.teams[2]
        # 2027 sem ordem: t1 tem a própria R1 + a R1 do t2 (trocada) + R2 própria
        self._pick(2027, 1, t1)
        self._pick(2027, 1, t2, cur=t1, traded=True)
        self._pick(2027, 2, t3)
        db.session.commit()

    def test_inventario_renderiza_posse_e_proveniencia(self):
        html = self._page()
        self.assertIn("Inventário de posse", html)
        self.assertIn("ordem pendente", html)
        self.assertIn("via Time 02", html, "proveniência da pick trocada ausente")
        self.assertNotIn("draft-order-position", html,
                         "inventário NÃO pode exibir número de posição — ordem não se inventa")

    def test_gancho_do_filtro_presente_nas_celulas(self):
        html = self._page()
        rows = re.findall(r'data-team-name="([^"]+)"', html)
        self.assertEqual(sorted(rows), ["Time 01", "Time 01", "Time 03"],
                         "cada célula do inventário carrega o gancho do filtro/realce")

    def test_contagem_por_time_bate_com_a_tabela(self):
        html = self._page()
        self.assertIn("Time 01 ×2", html)
        self.assertIn("Time 03 ×1", html)
        self.assertIn("(3 picks)", html)

    def test_consumida_fora_do_inventario(self):
        from models import db, AuctionLog
        # picks 2026 + evidência de draft realizado (OFF26-29)
        self._pick(2026, 1, self.teams[0])
        db.session.add(AuctionLog(season=2026, team_id=self.teams[0].id,
                                  player_name="X", team_name=self.teams[0].name,
                                  entry_type="rookie_draft", value_paid=1))
        db.session.commit()
        html = self._page()
        titles = re.findall(r'picks-year-title">(\d{4})<', html)
        self.assertNotIn("2026", titles, "season consumida não renderiza seção nenhuma")
        self.assertIn("2027", titles)


class TestOrdenadoIntacto(_Base):
    def setUp(self):
        super().setUp()
        from models import db, SeasonStandings, set_config
        set_config("current_season", "2026")
        # standings de 2026 → _apply_standings_order dá ordem ao draft de 2027
        for rank, t in enumerate(self.teams, start=1):
            db.session.add(SeasonStandings(season=2026, team_id=t.id, rank=rank,
                                           team_name=t.name))
        for t in self.teams:
            self._pick(2027, 1, t)
        db.session.commit()

    def test_season_com_ordem_usa_render_ordenado(self):
        html = self._page()
        self.assertIn("draft-order-position", html, "render ordenado deve manter as posições R.PP")
        self.assertNotIn("Inventário de posse", html,
                         "com ordem existente o inventário não aparece")
        self.assertIn("1.01", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
