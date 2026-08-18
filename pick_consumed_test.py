# -*- coding: utf-8 -*-
"""
pick_consumed_test.py — OFF26-29: pick consumida (draft realizado) some das superfícies
de leitura, com a row VIVA na tabela.

Predicado ÚNICO em models (`consumed_pick_seasons` / `pick_is_consumed`): pick consumida =
existe AuctionLog `entry_type='rookie_draft'` na season da pick — a MESMA evidência do gate
do passo 5 (OFF26-23), materializada em 2026 pelos 36 registros do reparo OFF26-26.

O que se prova aqui (ORM em memória, sem rede):
  * predicado: season com registro de rookie_draft → consumida; sem → viva (2027 tradável);
    fa_auction NÃO consome; banco sem log nenhum → nada consumido.
  * /api/picks (o sítio FUNCIONAL da F1 — alimenta simulador/propostas/preset): não devolve
    pick consumida; 2027 segue normal, inclusive sob filtro ?team=.
  * _fetch_picks (funil do trade flow — preview, proposta nova E render de proposta antiga):
    omite consumida, preserva 2027.
  * a row da Pick permanece na tabela (ocultação é estado de LEITURA, não delete).
  * guardas estáticas: predicado definido SÓ em models; os consumidores o importam
    (⛔ nenhuma réplica da query em rota/JS/template).
"""

import unittest


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from models import db
        from routes.picks import picks_bp

        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["LOGIN_DISABLED"] = True   # o alvo é o filtro, não o login
        cls.app.config["TESTING"] = True
        db.init_app(cls.app)
        cls.app.register_blueprint(picks_bp)
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
        from models import db, Team, Pick
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.t1 = Team(name="Cangaceiros da Colina")
        self.t2 = Team(name="mongoloides")
        db.session.add_all([self.t1, self.t2])
        db.session.flush()
        # Picks 2026 (draft realizado) e 2027 (futuro) para os dois times.
        self.picks = []
        for season in (2026, 2027):
            for team in (self.t1, self.t2):
                pk = Pick(season=season, round=1, original_team_id=team.id,
                          current_team_id=team.id, original_team_name=team.name,
                          current_team_name=team.name)
                db.session.add(pk)
                self.picks.append(pk)
        db.session.commit()

    def _consume_2026(self):
        """Materializa a evidência: 1 AuctionLog rookie_draft season 2026 (em prod são 36)."""
        from models import db, AuctionLog
        db.session.add(AuctionLog(season=2026, player_id=None, team_id=self.t1.id,
                                  player_name="Jeremiyah Love", team_name=self.t1.name,
                                  entry_type="rookie_draft", value_paid=54))
        db.session.commit()


class TestPredicado(_Base):
    def test_season_com_rookie_draft_e_consumida(self):
        from models import consumed_pick_seasons, pick_is_consumed
        self._consume_2026()
        self.assertEqual(consumed_pick_seasons(), {2026})
        p2026 = next(p for p in self.picks if p.season == 2026)
        p2027 = next(p for p in self.picks if p.season == 2027)
        self.assertTrue(pick_is_consumed(p2026))
        self.assertFalse(pick_is_consumed(p2027), "2027 deve permanecer tradável")

    def test_fa_auction_nao_consome(self):
        from models import db, AuctionLog, consumed_pick_seasons
        db.session.add(AuctionLog(season=2026, team_id=self.t1.id, player_name="X",
                                  team_name=self.t1.name, entry_type="fa_auction",
                                  value_paid=10))
        db.session.commit()
        self.assertEqual(consumed_pick_seasons(), set(),
                         "só rookie_draft consome — arremate de FA não é evidência de draft")

    def test_banco_sem_log_nada_consumido(self):
        from models import consumed_pick_seasons, pick_is_consumed
        self.assertEqual(consumed_pick_seasons(), set())
        self.assertFalse(any(pick_is_consumed(p) for p in self.picks))

    def test_caminho_batch_equivale_ao_individual(self):
        from models import consumed_pick_seasons, pick_is_consumed
        self._consume_2026()
        batch = consumed_pick_seasons()
        for p in self.picks:
            self.assertEqual(pick_is_consumed(p, batch), pick_is_consumed(p))


class TestApiPicks(_Base):
    """O sítio funcional da F1: /api/picks alimenta o simulador e as propostas."""

    def _seasons(self, **params):
        from urllib.parse import urlencode
        r = self.client.get("/api/picks" + ("?" + urlencode(params) if params else ""))
        self.assertEqual(r.status_code, 200)
        return sorted({row["season"] for row in r.get_json()})

    def test_consumida_some_e_2027_fica(self):
        self._consume_2026()
        self.assertEqual(self._seasons(), [2027])

    def test_filtro_por_time_tambem_oculta(self):
        self._consume_2026()
        self.assertEqual(self._seasons(team="Cangaceiros da Colina"), [2027])

    def test_sem_consumo_devolve_tudo(self):
        self.assertEqual(self._seasons(), [2026, 2027])

    def test_row_permanece_viva_na_tabela(self):
        """Ocultação ≠ delete: o espelho do _sync_trades depende da row existir."""
        from models import Pick
        self._consume_2026()
        self.assertEqual(Pick.query.filter_by(season=2026).count(), 2)


class TestFetchPicksTrades(_Base):
    """O funil do trade flow: preview, proposta nova e render de proposta antiga."""

    def test_fetch_omite_consumida_preserva_2027(self):
        from routes.trades import _fetch_picks
        self._consume_2026()
        ids = [p.id for p in self.picks]
        got = _fetch_picks(ids)
        self.assertEqual(sorted(p.season for p in got), [2027, 2027])

    def test_fetch_sem_consumo_devolve_tudo(self):
        from routes.trades import _fetch_picks
        got = _fetch_picks([p.id for p in self.picks])
        self.assertEqual(len(got), 4)


class TestGuardasEstaticas(unittest.TestCase):
    """⛔ Predicado em 1 lugar só; consumidores importam — réplica FALHA aqui."""

    CONSUMERS = ["routes/picks.py", "routes/league.py", "routes/trades.py"]

    def _src(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_predicado_definido_so_em_models(self):
        import glob
        defs = [f for f in glob.glob("**/*.py", recursive=True)
                if not f.startswith((".", "_")) and "phantom_board_profile" not in f
                and not f.endswith("_test.py")   # o literal aparece NESTE arquivo
                and "def consumed_pick_seasons" in self._src(f)]
        self.assertEqual(defs, ["models.py"])

    def test_consumidores_importam_a_fonte_unica(self):
        for f in self.CONSUMERS:
            self.assertIn("pick_is_consumed", self._src(f),
                          f"{f} deveria consumir o predicado único")

    def test_nenhuma_replica_da_query_nas_rotas(self):
        """A query de evidência (rookie_draft distinct em AuctionLog) não pode ser
        recriada inline nos consumidores — é o que manteria a fonte única honesta."""
        for f in self.CONSUMERS:
            src = self._src(f)
            self.assertNotIn('AuctionLog.season).filter_by(\n        entry_type="rookie_draft")', src)
            self.assertNotIn("entry_type='rookie_draft').distinct", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
