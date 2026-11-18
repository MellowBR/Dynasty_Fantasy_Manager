"""
off26_42_tx_test.py — OFF26-42 (18/11/2026): o sync decide re-add pelas TRANSAÇÕES.

Cobre a validação do prompt MAN-OFF26-42 (fechamento da porta): regressão McLaurin (modo A),
waiver dentro de 48h, trade sem drop, comissário, classe Gordon, 2º sync, etapa pulada
(modo B) + log, regras da cadeia (decisões do owner), marcador D2 nas duas formas, guarda
(d) do arremate, nascimento, corte D1, dedupe do D3 e o ESPN definitivo restaurado.
ORM em memória; a varredura é injetada (sem rede). Rodar: `python off26_42_tx_test.py`.
"""

import ast
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import contract_regua as cr

BASE_DIR = Path(__file__).resolve().parent
W48 = cr.waiver_window_ms(2)
START_26 = cr.season_start_ms("2026-09-09")


def _ms(s: str) -> int:
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
               .timestamp() * 1000)


def _rec(ts, tx, typ, roster):
    return {"ts": _ms(ts), "tx_id": tx, "type": typ, "roster": roster}


# Cadeia REAL do McLaurin (API, 18/11/2026).
MCL_DROP = _rec("2026-10-20 19:15", "1418350840095260672", "free_agent", 2)
MCL_ADD = _rec("2026-10-23 00:50", "1419159991641780224", "free_agent", 8)


class Base(unittest.TestCase):
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

    @classmethod
    def tearDownClass(cls):
        from models import db
        db.session.remove()
        cls.ctx.pop()

    def setUp(self):
        from models import db, Team, set_config
        db.session.remove()
        db.drop_all()
        db.create_all()
        set_config("current_season", "2026")
        set_config("offseason_mode", "false")
        self.teams = {}
        for rid in (2, 4, 5, 6, 8, 12):
            t = Team(name=f"Time {rid}", sleeper_roster_id=str(rid))
            db.session.add(t)
            self.teams[rid] = t
        db.session.commit()

    def player(self, sid, team_rid, salary, cy, css, acq, espn=1.0, created="2026-03-25 18:49",
               store=None, ir=False):
        from models import db, Player, EspnValueStore
        p = Player(name=f"P{sid}", position="WR", sleeper_player_id=sid,
                   team_id=self.teams[team_rid].id, fantasy_team=self.teams[team_rid].name,
                   salary=salary, contract_year=cy, contract_start_season=css,
                   acquisition_type=acq, espn_ref_value=espn, is_on_ir=ir,
                   created_at=datetime.strptime(created, "%Y-%m-%d %H:%M"))
        db.session.add(p)
        if store:
            raw, adj, fin = store
            db.session.add(EspnValueStore(sleeper_player_id=sid, season=2026, espn_raw=raw,
                                          espn_adjusted=adj, is_final=fin))
        db.session.commit()
        return p

    def ctx_for(self, index):
        from models import Team
        return {"window_ms": W48, "start_ms": START_26, "index": index, "freeze_ms": None,
                "frozen_sids": set(),
                "team_by_roster": {t.sleeper_roster_id: t for t in Team.query.all()}}

    def sync(self, index, rostered, readds=None, err=None):
        """Um passo 8b como no run_sync (+ commit), com a varredura injetada."""
        import sync_sleeper
        from models import db
        ret = (None, err) if err else (self.ctx_for(index), None)
        with mock.patch.object(sync_sleeper, "_build_regua_context", return_value=ret):
            out = sync_sleeper._process_contract_regua(readds or [], [], {},
                                                       rostered=rostered)
        db.session.commit()
        return out

    def counts(self):
        from models import AuctionLog, SalaryHistory, PlayerHistory, ContractPendency
        return (AuctionLog.query.count(), SalaryHistory.query.count(),
                PlayerHistory.query.count(), ContractPendency.query.count())


class TestRegressaoMcLaurin(Base):
    def test_um_sync_apos_o_add_abre_ano1_com_marca_e_espn_identico(self):
        from models import db, AuctionLog, PlayerHistory, EspnValueStore
        # Estado ANTERIOR ao drop: roster 2, contrato morto $13 · ano 3 · 2024 · auction.
        p = self.player("5927", 2, 13.0, 3, 2024, "auction_draft", espn=20.0,
                        store=(17.0, 20.0, True))
        # Nenhum sync entre drop e add. O sync seguinte (passo 7) só vê o jogador no
        # roster 8 — reatribuição de time, SEM transição observada (modo A).
        p.team_id, p.fantasy_team = self.teams[8].id, self.teams[8].name
        p.is_on_ir = True
        db.session.commit()
        index = {"5927": {"adds": [dict(MCL_ADD)], "drops": [dict(MCL_DROP)]}}
        out = self.sync(index, rostered=[(p, self.teams[8])])
        self.assertEqual(len(out["contratos_novos"]), 1, out)
        self.assertEqual((p.salary, p.contract_year, p.contract_start_season,
                          p.acquisition_type), (1.0, 1, 2026, "free_agent"))
        self.assertEqual(p.team_id, self.teams[8].id)          # time intacto
        self.assertTrue(p.is_on_ir)                            # IR intacto
        log = AuctionLog.query.filter_by(player_id=p.id).one()
        self.assertIn("[ref:tx:1419159991641780224]", log.notes)
        self.assertIsNotNone(PlayerHistory.query.filter_by(
            player_id=p.id, sleeper_event_ref="tx:1419159991641780224").first())
        st = EspnValueStore.query.filter_by(sleeper_player_id="5927", season=2026).one()
        self.assertEqual((st.espn_raw, st.espn_adjusted, bool(st.is_final)),
                         (17.0, 20.0, True))                   # linha ESPN IDÊNTICA
        self.assertEqual(p.espn_ref_value, 20.0)
        # D3: o drop não visto ganha evento retroativo (fato + fase), com o time do drop.
        ev = PlayerHistory.query.filter_by(player_id=p.id, event_type="drop").one()
        self.assertEqual(ev.sleeper_event_ref, "tx:1418350840095260672")
        self.assertEqual(ev.team_name, self.teams[2].name)
        from salary_engine import project_next_salary
        self.assertEqual(project_next_salary(p), 16)           # 2027: floor(0,8×20)

    def test_segundo_sync_zero_escrita(self):
        from models import db
        p = self.player("5927", 8, 13.0, 3, 2024, "auction_draft", espn=20.0,
                        store=(17.0, 20.0, True))
        index = {"5927": {"adds": [dict(MCL_ADD)], "drops": [dict(MCL_DROP)]}}
        self.sync(index, rostered=[(p, self.teams[8])])
        before = self.counts()
        out = self.sync(index, rostered=[(p, self.teams[8])])
        self.assertEqual(self.counts(), before)
        self.assertEqual((out["contratos_novos"], out["pendencias"], out["drop_events"]),
                         ([], [], 0))

    def test_reparado_pelo_runner_nao_e_redecidido(self):
        """Os 4 reparados de 18/11 têm o token do add — o sync não escreve nada."""
        from models import db, AuctionLog
        p = self.player("5927", 8, 1.0, 1, 2026, "free_agent", espn=20.0)
        db.session.add(AuctionLog(season=2026, player_id=p.id, team_id=self.teams[8].id,
                                  player_name=p.name, team_name="Time 8",
                                  entry_type="free_agent", value_paid=1.0,
                                  notes="OFF26-42-FIX caso 3 [ref:tx:1419159991641780224]"))
        db.session.commit()
        index = {"5927": {"adds": [dict(MCL_ADD)], "drops": [dict(MCL_DROP)]}}
        before = self.counts()
        out = self.sync(index, rostered=[(p, self.teams[8])])
        self.assertEqual(out["contratos_novos"], [])
        self.assertEqual(self.counts()[0:2], before[0:2])      # nada no log/histórico de salário


class TestCenarios(Base):
    def test_waiver_dentro_de_48h_sem_sync_entre_mantem(self):
        from models import PlayerHistory
        p = self.player("12487", 5, 1.0, 1, 2026, "auction_draft")
        index = {"12487": {"adds": [_rec("2026-09-16 11:26", "1405911823215046656", "waiver", 5)],
                           "drops": [_rec("2026-09-15 20:29", "1405685909285781504", "waiver", 2)]}}
        out = self.sync(index, rostered=[(p, self.teams[5])])
        self.assertEqual(len(out["mantidos"]), 1)
        self.assertEqual((p.salary, p.acquisition_type), (1.0, "auction_draft"))
        ev = PlayerHistory.query.filter_by(sleeper_event_ref="tx:1405911823215046656").one()
        self.assertTrue(ev.notes.startswith("[regua:manter:tx:1405911823215046656]"))
        self.assertEqual(self.sync(index, rostered=[(p, self.teams[5])])["mantidos"], [])

    def test_trade_sem_drop_nao_chama_a_regua(self):
        import sync_sleeper
        p = self.player("5967", 2, 41.0, 1, 2026, "auction_draft")
        with mock.patch.object(sync_sleeper, "_get", side_effect=lambda url: [] if "/transactions/" in url and not url.endswith("/1") else [
                {"status": "complete", "type": "trade", "transaction_id": "t1", "created": 1,
                 "adds": {"5967": 2}, "drops": {"5967": 8}}]):
            index, err = sync_sleeper._sweep_transactions("L")
        self.assertIsNone(err)
        self.assertNotIn("5967", index)                         # trade fora da varredura
        before = self.counts()
        with mock.patch.object(cr, "decide_readd", wraps=cr.decide_readd) as spy:
            self.sync(index, rostered=[(p, self.teams[2])])
        spy.assert_not_called()
        self.assertEqual(self.counts(), before)
        self.assertEqual(p.salary, 41.0)

    def test_varredura_carrega_o_roster(self):
        import sync_sleeper
        tx = {"status": "complete", "type": "free_agent", "transaction_id": "x", "created": 5,
              "adds": {"1": 8}, "drops": {"2": 8}}
        with mock.patch.object(sync_sleeper, "_get",
                               side_effect=lambda url: [tx] if url.endswith("/0") else []):
            index, _ = sync_sleeper._sweep_transactions("L")
        self.assertEqual(index["1"]["adds"][0]["roster"], 8)
        self.assertEqual(index["2"]["drops"][0]["roster"], 8)

    def test_comissario_vira_pendencia_nunca_decisao(self):
        from models import ContractPendency
        p = self.player("700", 4, 9.0, 2, 2025, "fa_auction")
        index = {"700": {"adds": [_rec("2026-10-01 12:00", "c-add", "commissioner", 4)],
                         "drops": [_rec("2026-09-20 12:00", "c-drop", "free_agent", 6)]}}
        out = self.sync(index, rostered=[(p, self.teams[4])])
        self.assertEqual(len(out["pendencias"]), 1)
        self.assertEqual(ContractPendency.query.one().kind, cr.KIND_COMISSARIO_ADD)
        self.assertEqual((p.salary, p.contract_year), (9.0, 2))
        out2 = self.sync(index, rostered=[(p, self.teams[4])])
        self.assertEqual(ContractPendency.query.count(), 1)     # 2º sync: nenhuma nova

    def test_classe_gordon_add_seguido_de_trade(self):
        """Desenho aprovado: régua normal, porta com o time ATUAL, nota com quem adicionou."""
        from models import AuctionLog
        p = self.player("12495", 12, 1.0, 2, 2025, "rookie_draft")
        index = {"12495": {"adds": [_rec("2026-10-01 12:00", "g-add", "free_agent", 5)],
                           "drops": [_rec("2026-09-20 12:00", "g-drop", "free_agent", 5)]}}
        out = self.sync(index, rostered=[(p, self.teams[12])])
        self.assertEqual(len(out["contratos_novos"]), 1)
        self.assertEqual((p.team_id, p.contract_year, p.contract_start_season),
                         (self.teams[12].id, 1, 2026))
        log = AuctionLog.query.filter_by(player_id=p.id).one()
        self.assertEqual(log.team_id, self.teams[12].id)
        self.assertIn("add por Time 5 (r5)", log.notes)
        self.assertIn("[ref:tx:g-add]", log.notes)

    def test_nascimento_nao_e_re_add(self):
        p = self.player("13999", 4, 1.0, 1, 2026, "unknown", created="2026-10-02 03:00")
        index = {"13999": {"adds": [_rec("2026-10-01 12:00", "b-add", "free_agent", 4)],
                           "drops": [_rec("2026-09-20 12:00", "b-drop", "free_agent", 6)]}}
        before = self.counts()
        out = self.sync(index, rostered=[(p, self.teams[4])])
        self.assertEqual(self.counts(), before)
        self.assertEqual(p.acquisition_type, "unknown")

    def test_corte_d1_exclui_add_anterior(self):
        p = self.player("800", 4, 5.0, 2, 2025, "fa_auction")
        index = {"800": {"adds": [_rec("2026-09-05 12:00", "pre-add", "free_agent", 4)],
                         "drops": [_rec("2026-08-20 12:00", "pre-drop", "free_agent", 4)]}}
        before = self.counts()
        self.sync(index, rostered=[(p, self.teams[4])])
        self.assertEqual(self.counts(), before)
        self.assertEqual(p.salary, 5.0)

    def test_guarda_d_arremate_do_leilao_nao_e_reescrito(self):
        """Contrato do importador (ref draft:) registrado DEPOIS do drop: o add é a
        materialização do arremate — nunca caso 3."""
        from models import db, AuctionLog
        p = self.player("900", 4, 23.0, 1, 2026, "auction_draft")
        db.session.add(AuctionLog(season=2026, player_id=p.id, team_id=self.teams[4].id,
                                  player_name=p.name, team_name="Time 4",
                                  entry_type="fa_auction", value_paid=23.0,
                                  notes="import [ref:draft:999:12]",
                                  created_at=datetime(2026, 9, 25, 3, 0)))
        db.session.commit()
        index = {"900": {"adds": [_rec("2026-09-26 12:00", "a-add", "free_agent", 4)],
                         "drops": [_rec("2026-09-20 12:00", "a-drop", "free_agent", 6)]}}
        out = self.sync(index, rostered=[(p, self.teams[4])])
        self.assertEqual(out["contratos_novos"], [])
        self.assertEqual(p.salary, 23.0)


class TestModoB(Base):
    def test_etapa_pulada_preserva_o_caso_loga_e_o_sync_seguinte_decide(self):
        import sync_sleeper
        from models import SyncLog
        p = self.player("5927", 8, 13.0, 3, 2024, "auction_draft", espn=20.0,
                        store=(17.0, 20.0, True))
        index = {"5927": {"adds": [dict(MCL_ADD)], "drops": [dict(MCL_DROP)]}}
        before = self.counts()
        out = self.sync(index, rostered=[(p, self.teams[8])],
                        readds=[(p, self.teams[8])], err="transactions leg 7 indisponivel")
        self.assertEqual(out["skipped"], "transactions leg 7 indisponivel")
        self.assertEqual((p.salary, self.counts()), (13.0, before))
        summary = {"players_updated": 0, "players_added": 0, "teams_updated": 12,
                   "picks_updated": 0, "contract_regua": out}
        sync_sleeper._log_sync(summary)
        self.assertIn("Regua PULADA: transactions leg 7 indisponivel",
                      SyncLog.query.order_by(SyncLog.id.desc()).first().summary)
        # Sync seguinte, SEM transição observada (is_dropped já zerado): decide.
        out2 = self.sync(index, rostered=[(p, self.teams[8])])
        self.assertEqual(len(out2["contratos_novos"]), 1)
        self.assertEqual(p.salary, 1.0)

    def test_log_do_sync_registra_o_resultado(self):
        import sync_sleeper
        from models import SyncLog
        out = {"contratos_novos": ["a"], "mantidos": [], "pendencias": ["b", "c"],
               "drop_events": 4, "bloqueados": [], "skipped": None}
        sync_sleeper._log_sync({"players_updated": 0, "players_added": 0, "teams_updated": 12,
                                "picks_updated": 0, "contract_regua": out})
        s = SyncLog.query.order_by(SyncLog.id.desc()).first().summary
        self.assertIn("Regua: 1 contrato(s) novo(s), 0 mantido(s), 2 pendencia(s), 4 drop(s)", s)


class TestCadeia(unittest.TestCase):
    """plan_chain — as regras do owner (18/11/2026), puras."""

    def it(self, add, drop, mark=None):
        return {"add": add, "drop": drop, "mark": mark, "drop_verdict": None}

    def kw(self):
        return {"window_ms": W48, "start_ms": START_26}

    def test_ambiguo_antes_do_ultimo_caso3_e_superado(self):
        items = [self.it(_rec("2026-10-05 12:00", "a1", "waiver", 4),
                         _rec("2026-09-20 12:00", "d1", "free_agent", 6)),   # divergente
                 self.it(_rec("2026-10-20 12:00", "a2", "free_agent", 4),
                         _rec("2026-10-10 12:00", "d2", "free_agent", 4))]   # caso 3
        plan = cr.plan_chain(items, **self.kw())
        self.assertEqual((plan["novo"], plan["pendencia"], plan["superados"]), (1, None, [0]))

    def test_ambiguo_depois_do_caso3_abre_pendencia_e_para(self):
        items = [self.it(_rec("2026-10-01 12:00", "a1", "free_agent", 4),
                         _rec("2026-09-20 12:00", "d1", "free_agent", 6)),   # caso 3
                 self.it(_rec("2026-10-20 12:00", "a2", "waiver", 4),
                         _rec("2026-10-10 12:00", "d2", "free_agent", 4)),   # divergente
                 self.it(_rec("2026-10-30 12:00", "a3", "waiver", 4),
                         _rec("2026-10-29 12:00", "d3", "free_agent", 4))]   # caso 2 (espera)
        plan = cr.plan_chain(items, **self.kw())
        self.assertEqual((plan["novo"], plan["pendencia"], plan["manter"]), (0, 1, []))

    def test_caso2_depois_de_caso3_grava_manter(self):
        items = [self.it(_rec("2026-10-01 12:00", "a1", "free_agent", 4),
                         _rec("2026-09-20 12:00", "d1", "free_agent", 6)),
                 self.it(_rec("2026-10-21 12:00", "a2", "waiver", 4),
                         _rec("2026-10-20 12:00", "d2", "free_agent", 4))]
        plan = cr.plan_chain(items, **self.kw())
        self.assertEqual((plan["novo"], plan["manter"]), (0, [1]))

    def test_pendencia_aberta_bloqueia_so_sem_caso3_depois(self):
        base = [self.it(_rec("2026-10-01 12:00", "a1", "waiver", 4),
                        _rec("2026-09-20 12:00", "d1", "free_agent", 6), cr.MARK_PEND_ABERTA)]
        so_caso2 = base + [self.it(_rec("2026-10-21 12:00", "a2", "waiver", 4),
                                   _rec("2026-10-20 12:00", "d2", "free_agent", 4))]
        self.assertIsNotNone(cr.plan_chain(so_caso2, **self.kw())["bloqueado"])
        com_caso3 = base + [self.it(_rec("2026-11-01 12:00", "a2", "free_agent", 4),
                                    _rec("2026-10-20 12:00", "d2", "free_agent", 4))]
        plan = cr.plan_chain(com_caso3, **self.kw())
        self.assertIsNone(plan["bloqueado"])
        self.assertEqual(plan["novo"], 1)
        # Caso 3 JÁ APLICADO (token) depois da pendência também desbloqueia.
        com_token = base + [self.it(_rec("2026-11-01 12:00", "a2", "free_agent", 4),
                                    _rec("2026-10-20 12:00", "d2", "free_agent", 4),
                                    cr.MARK_TOKEN),
                            self.it(_rec("2026-11-10 12:00", "a3", "waiver", 4),
                                    _rec("2026-11-09 12:00", "d3", "free_agent", 4))]
        plan = cr.plan_chain(com_token, **self.kw())
        self.assertIsNone(plan["bloqueado"])
        self.assertEqual(plan["manter"], [2])

    def test_pendencia_no_ultimo_add_sem_nada_pendente_nao_e_bloqueio(self):
        items = [self.it(_rec("2026-10-01 12:00", "a1", "waiver", 4),
                         _rec("2026-09-20 12:00", "d1", "free_agent", 6), cr.MARK_PEND_ABERTA)]
        plan = cr.plan_chain(items, **self.kw())
        self.assertIsNone(plan["bloqueado"])
        self.assertEqual((plan["novo"], plan["manter"], plan["pendencia"]), (None, [], None))

    def test_pendencia_orfa_bloqueia_sem_caso3(self):
        items = [self.it(_rec("2026-10-21 12:00", "a2", "waiver", 4),
                         _rec("2026-10-20 12:00", "d2", "free_agent", 4))]
        self.assertIsNotNone(cr.plan_chain(items, orphan_open_pendency=True,
                                           **self.kw())["bloqueado"])

    def test_cadeia_toda_marcada_nao_faz_nada(self):
        items = [self.it(_rec("2026-10-01 12:00", "a1", "free_agent", 4),
                         _rec("2026-09-20 12:00", "d1", "free_agent", 6), cr.MARK_TOKEN)]
        plan = cr.plan_chain(items, **self.kw())
        self.assertEqual((plan["novo"], plan["manter"], plan["pendencia"]), (None, [], None))


class TestMarcadorD2(unittest.TestCase):
    def test_formato_travado(self):
        self.assertEqual(cr.manter_marker("1405911823215046656"),
                         "[regua:manter:tx:1405911823215046656]")
        self.assertTrue(cr.manter_marker("x").isascii())

    def test_leitura_aceita_as_duas_formas(self):
        self.assertTrue(cr.notes_mark_manter("[regua:manter:tx:42] fa_waiver ...", "42"))
        self.assertTrue(cr.notes_mark_manter(
            "fa_waiver (temporada) — tx 42; contrato mantido (caso 2 da régua)", "42"))
        self.assertFalse(cr.notes_mark_manter("fa_waiver r5 (rebuild F8)", "42"))
        self.assertFalse(cr.notes_mark_manter(None, "42"))

    def test_corte_d1(self):
        self.assertEqual(cr.tx_floor_ms(), _ms("2026-09-09 00:00"))


class TestDedupeD3(Base):
    def test_evento_de_drop_com_outro_team_name_nao_duplica(self):
        from models import db, PlayerHistory
        p = self.player("5927", 8, 13.0, 3, 2024, "auction_draft", espn=20.0)
        db.session.add(PlayerHistory(player_id=p.id, season=2026, team_name="3 peat (rebuild)",
                                     event_type="drop", salary=13.0, contract_year=3,
                                     notes="rebuild F8", sleeper_event_ref="tx:1418350840095260672"))
        db.session.commit()
        index = {"5927": {"adds": [dict(MCL_ADD)], "drops": [dict(MCL_DROP)]}}
        out = self.sync(index, rostered=[(p, self.teams[8])])
        self.assertEqual(out["drop_events"], 0)
        self.assertEqual(PlayerHistory.query.filter_by(event_type="drop").count(), 1)

    def test_evento_do_rebuild_sem_marcador_recebe_o_marcador(self):
        from models import db, PlayerHistory
        p = self.player("12487", 5, 1.0, 1, 2026, "auction_draft")
        db.session.add(PlayerHistory(player_id=p.id, season=2026, team_name="Outro nome",
                                     event_type="fa_waiver", salary=1.0, contract_year=1,
                                     notes="fa_waiver (rebuild F8)",
                                     sleeper_event_ref="tx:1405911823215046656"))
        db.session.commit()
        index = {"12487": {"adds": [_rec("2026-09-16 11:26", "1405911823215046656", "waiver", 5)],
                           "drops": [_rec("2026-09-15 20:29", "1405685909285781504", "waiver", 2)]}}
        self.sync(index, rostered=[(p, self.teams[5])])
        evs = PlayerHistory.query.filter_by(event_type="fa_waiver").all()
        self.assertEqual(len(evs), 1)
        self.assertTrue(evs[0].notes.startswith("[regua:manter:tx:1405911823215046656]"))


class TestGuardasDeFonte(unittest.TestCase):
    def test_run_sync_chama_o_8b_sempre_e_os_rosterados_atras_da_chave(self):
        src = (BASE_DIR / "sync_sleeper.py").read_text(encoding="utf-8")
        self.assertIn("summary[\"contract_regua\"] = _process_contract_regua(\n"
                      "        readd_candidates, newly_dropped, league_data,\n"
                      "        rostered=rostered_now if regua_por_transacao() else None)", src)
        self.assertNotIn("if readd_candidates or newly_dropped:", src)

    def test_chave_de_liberacao(self):
        import os
        import sync_sleeper
        with mock.patch.dict(os.environ, {"REGUA_POR_TRANSACAO": "1"}):
            self.assertTrue(sync_sleeper.regua_por_transacao())
        for v in ("", "0", "true", "sim"):
            with mock.patch.dict(os.environ, {"REGUA_POR_TRANSACAO": v}):
                self.assertFalse(sync_sleeper.regua_por_transacao())
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(sync_sleeper.regua_por_transacao())

    def test_ferramenta_de_ensaio_liga_a_chave_so_no_proprio_processo(self):
        src = (BASE_DIR / "tools" / "regua_sync_ensaio.py").read_text(encoding="utf-8")
        self.assertIn('os.environ["REGUA_POR_TRANSACAO"] = "1"', src)

    def test_decisao_continua_so_no_helper(self):
        tree = ast.parse((BASE_DIR / "contract_regua.py").read_text(encoding="utf-8"))
        fns = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        self.assertIn("decide_readd", fns)
        src = (BASE_DIR / "contract_regua.py").read_text(encoding="utf-8")
        plan_src = src[src.index("def plan_chain"):]
        self.assertIn("decide_readd(", plan_src)                # a cadeia CHAMA o helper
        self.assertNotIn("window_ms) <=", plan_src)             # e não refaz a janela


if __name__ == "__main__":
    unittest.main(verbosity=1)
