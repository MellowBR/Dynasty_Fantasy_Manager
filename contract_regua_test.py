# -*- coding: utf-8 -*-
"""
contract_regua_test.py — OFF26-42: régua de contrato vivo × morto (núcleo puro +
integração ORM em memória + guardas AST).

Cobre as validações da sessão MAN-OFF26-36 (09/09/2026):
  1/2. re-add dentro × fora da janela (contrato mantido × ano 1 novo);
  3.   comissário: pendência + vereditos (real → régua; manobra → intacto, sem drop);
  4.   evento de drop com data da API + fase; segundo sync não duplica;
  9.   drop anterior à season (fora da varredura) → morto por dedução, sem pendência;
  10.  sinais divergentes (Δ dentro + canal free_agent) → pendência com os 2 sinais;
  11.  fase derivada da DATA da transação (offseason_mode NÃO é fonte);
  12.  re-add não zera espn_ref_value (armadilha OFF26-39.2).

⭐ Precedente CANÔNICO Jones×Goff (decisão 5): os timestamps reais medidos na liga de
2025 têm de reproduzir os vereditos arbitrados em produção — é o teste que fixa
`created` nos dois lados (refutação medida da decisão 8: `status_updated` no add
daria Goff 53,1h e inverteria o veredito preservado em produção).

Guardas AST (validação 8): nenhum sítio do sync decide re-add fora de
`contract_regua.decide_readd`; a arbitragem do admin não chama `record_acquisition`
direto (só o executor único `apply_regua_consequence`); o núcleo é PURO (sem
models/flask/requests).
"""

import ast
import json
import re
import unittest
from datetime import datetime, timezone
from unittest import mock
from pathlib import Path

import contract_regua as cr

BASE_DIR = Path(__file__).resolve().parent
MS_H = 60 * 60 * 1000


def _ms(s: str) -> int:
    """'YYYY-MM-DD HH:MM' (UTC) → epoch ms."""
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M")
               .replace(tzinfo=timezone.utc).timestamp() * 1000)


START_26 = cr.season_start_ms("2026-09-09")   # medido no /state/nfl em 09/09/2026
START_25 = cr.season_start_ms("2025-09-04")
W48 = cr.waiver_window_ms(2)                  # waiver_clear_days=2 medido na liga


# ══════════════════════════════════════════════════════════════════════════════
# Núcleo puro
# ══════════════════════════════════════════════════════════════════════════════

class TestJanelaEFase(unittest.TestCase):
    def test_janela_vem_da_config_sem_literal(self):
        self.assertEqual(cr.waiver_window_ms(2), 48 * MS_H)
        self.assertEqual(cr.waiver_window_ms(3), 72 * MS_H)
        self.assertEqual(cr.waiver_window_ms("2"), 48 * MS_H)

    def test_fase_pela_data_da_transacao(self):
        # Validação 11 (metade pura): 20/08 → intertemporada; 15/09 → temporada.
        self.assertEqual(cr.phase_of(_ms("2026-08-20 20:29"), START_26),
                         cr.FASE_INTERTEMPORADA)
        self.assertEqual(cr.phase_of(_ms("2026-09-15 12:00"), START_26),
                         cr.FASE_TEMPORADA)

    def test_timestamp_canonico_e_created_nos_dois_lados(self):
        """⛔ Guarda da refutação da decisão 8: `created`, nunca `status_updated`."""
        tx = {"created": 111, "status_updated": 999}
        self.assertEqual(cr.tx_timestamp(tx), 111)

    def test_latest_before(self):
        evs = [{"ts": 10, "tx_id": "a"}, {"ts": 30, "tx_id": "c"},
               {"ts": 20, "tx_id": "b"}]
        self.assertEqual(cr.latest_before(evs)["tx_id"], "c")
        self.assertEqual(cr.latest_before(evs, before_ts_ms=30)["tx_id"], "b")
        self.assertIsNone(cr.latest_before([], before_ts_ms=30))
        self.assertIsNone(cr.latest_before(evs, before_ts_ms=5))


class TestPrecedenteJonesGoff(unittest.TestCase):
    """⭐ A formalização canônica TEM de reproduzir os vereditos arbitrados em prod
    (medição do owner, 26/08/2026 — timestamps `created` reais da liga de 2025)."""

    def test_jones_69h_fora_da_janela_morto(self):
        decision = cr.decide_readd(
            add={"ts": 1762394083840, "tx_id": "j-add", "type": "waiver"},
            drop={"ts": 1762145105158, "tx_id": "j-drop", "type": "waiver"},
            window_ms=W48, start_ms=START_25)
        # waiver FORA da janela = sinais divergentes → era exatamente a disputa que a
        # arbitragem humana resolveu. A régua manda para a fila, com Δ 69,2h citado.
        self.assertEqual(decision["acao"], cr.ACAO_PENDENCIA)
        self.assertEqual(decision["kind"], cr.KIND_SINAL_DIVERGENTE)
        self.assertAlmostEqual(decision["delta_h"], 69.2, delta=0.1)

    def test_goff_12h_dentro_da_janela_vivo(self):
        decision = cr.decide_readd(
            add={"ts": 1757511117748, "tx_id": "g-add", "type": "waiver"},
            drop={"ts": 1757466673903, "tx_id": "g-drop", "type": "waiver"},
            window_ms=W48, start_ms=START_25)
        self.assertEqual(decision["acao"], cr.ACAO_MANTER)
        self.assertEqual(decision["caso"], 2)
        self.assertAlmostEqual(decision["delta_h"], 12.3, delta=0.1)


class TestDecideReadd(unittest.TestCase):
    def test_caso2_waiver_dentro_mantem(self):
        # Validação 1: drop na terça, claim na quinta (Δ 47h < 48h), canal waiver.
        d = cr.decide_readd(
            add={"ts": _ms("2026-09-17 12:00"), "tx_id": "t2", "type": "waiver"},
            drop={"ts": _ms("2026-09-15 13:00"), "tx_id": "t1", "type": "free_agent"},
            window_ms=W48, start_ms=START_26)
        self.assertEqual(d["acao"], cr.ACAO_MANTER)
        self.assertEqual(d["caso"], 2)

    def test_caso3_free_agent_fora_abre_ano1(self):
        # Validação 2: drop há 10 dias, add free_agent.
        d = cr.decide_readd(
            add={"ts": _ms("2026-09-25 12:00"), "tx_id": "t2", "type": "free_agent"},
            drop={"ts": _ms("2026-09-15 12:00"), "tx_id": "t1", "type": "free_agent"},
            window_ms=W48, start_ms=START_26)
        self.assertEqual(d["acao"], cr.ACAO_CONTRATO_NOVO)
        self.assertEqual(d["caso"], 3)
        self.assertEqual(d["acq_type"], "free_agent")

    def test_caso3_drop_intertemporada_mata_por_si(self):
        # A letra da régua: não há waiver na intertemporada (padrão Aiyuk/Wicks).
        d = cr.decide_readd(
            add={"ts": _ms("2026-09-10 12:00"), "tx_id": "t2", "type": "free_agent"},
            drop={"ts": _ms("2026-08-20 20:29"), "tx_id": "t1", "type": "free_agent"},
            window_ms=W48, start_ms=START_26)
        self.assertEqual(d["acao"], cr.ACAO_CONTRATO_NOVO)
        self.assertEqual(d["fase_drop"], cr.FASE_INTERTEMPORADA)

    def test_caso3_sem_drop_na_varredura_morto_por_deducao(self):
        # Validação 9 (decisão 7): drop de 2025 não aparece na varredura da season.
        d = cr.decide_readd(
            add={"ts": _ms("2026-09-20 12:00"), "tx_id": "t2", "type": "free_agent"},
            drop=None, window_ms=W48, start_ms=START_26)
        self.assertEqual(d["acao"], cr.ACAO_CONTRATO_NOVO)
        self.assertIn("dedução", d["motivo"])

    def test_sinal_divergente_free_agent_dentro_da_janela(self):
        # Validação 10: Δ dentro + canal free_agent → pendência com os DOIS sinais.
        d = cr.decide_readd(
            add={"ts": _ms("2026-09-16 12:00"), "tx_id": "t2", "type": "free_agent"},
            drop={"ts": _ms("2026-09-15 12:00"), "tx_id": "t1", "type": "free_agent"},
            window_ms=W48, start_ms=START_26)
        self.assertEqual(d["acao"], cr.ACAO_PENDENCIA)
        self.assertEqual(d["kind"], cr.KIND_SINAL_DIVERGENTE)
        self.assertEqual(len(d["sinais"]), 2)
        self.assertTrue(any("dentro" in s for s in d["sinais"]))
        self.assertTrue(any("free_agent" in s for s in d["sinais"]))

    def test_comissario_add_vira_pendencia(self):
        d = cr.decide_readd(
            add={"ts": _ms("2026-09-16 12:00"), "tx_id": "t2", "type": "commissioner"},
            drop=None, window_ms=W48, start_ms=START_26)
        self.assertEqual(d["acao"], cr.ACAO_PENDENCIA)
        self.assertEqual(d["kind"], cr.KIND_COMISSARIO_ADD)

    def test_comissario_add_arbitrado_real_roda_a_regua(self):
        d = cr.decide_readd(
            add={"ts": _ms("2026-09-16 12:00"), "tx_id": "t2", "type": "commissioner"},
            drop=None, window_ms=W48, start_ms=START_26,
            commissioner_add_as_real=True)
        self.assertEqual(d["acao"], cr.ACAO_CONTRATO_NOVO)

    def test_comissario_drop_pendente_manobra_real(self):
        add = {"ts": _ms("2026-09-25 12:00"), "tx_id": "t2", "type": "free_agent"}
        drop = {"ts": _ms("2026-09-15 12:00"), "tx_id": "t1", "type": "commissioner"}
        aberto = cr.decide_readd(add=add, drop=drop, window_ms=W48, start_ms=START_26)
        self.assertEqual(aberto["acao"], cr.ACAO_PENDENCIA)
        self.assertEqual(aberto["kind"], cr.KIND_COMISSARIO_DROP)
        manobra = cr.decide_readd(add=add, drop=drop, window_ms=W48,
                                  start_ms=START_26, drop_verdict="manobra")
        self.assertEqual(manobra["acao"], cr.ACAO_MANTER)
        # Validação 3: arbitrar "real" seguido de add fora da janela → ano 1.
        real = cr.decide_readd(add=add, drop=drop, window_ms=W48,
                               start_ms=START_26, drop_verdict="real")
        self.assertEqual(real["acao"], cr.ACAO_CONTRATO_NOVO)

    def test_sem_add_na_varredura_indeterminado(self):
        d = cr.decide_readd(add=None, drop=None, window_ms=W48, start_ms=START_26)
        self.assertEqual(d["acao"], cr.ACAO_INDETERMINADO)


class TestVereditoSugerido(unittest.TestCase):
    FREEZE = _ms("2026-08-22 12:02")   # carimbo real do congelamento OFF26-11

    def test_drop_pos_congelamento_em_jogador_da_lista_sugere_manobra(self):
        self.assertEqual(cr.suggest_commissioner_verdict(
            _ms("2026-08-24 10:00"), self.FREEZE, True), "manobra")

    def test_drop_pre_congelamento_sugere_real(self):
        self.assertEqual(cr.suggest_commissioner_verdict(
            _ms("2026-08-20 10:00"), self.FREEZE, False), "real")

    def test_pos_congelamento_fora_da_lista_sem_sugestao(self):
        self.assertIsNone(cr.suggest_commissioner_verdict(
            _ms("2026-08-24 10:00"), self.FREEZE, False))

    def test_sem_ancora_degrada_para_none_nunca_bloqueia(self):
        self.assertIsNone(cr.suggest_commissioner_verdict(
            _ms("2026-08-24 10:00"), None, True))


# ══════════════════════════════════════════════════════════════════════════════
# Integração — ORM em memória (sem rede: _build_regua_context é substituído)
# ══════════════════════════════════════════════════════════════════════════════

def _fake_ctx(index, freeze_ms=None, frozen_sids=None):
    return {"window_ms": W48, "start_ms": START_26, "index": index,
            "freeze_ms": freeze_ms, "frozen_sids": frozen_sids or set()}


class OrmBase(unittest.TestCase):
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
        from models import db, Team, Player, set_config
        db.session.remove()
        db.drop_all()
        db.create_all()
        set_config("current_season", "2026")
        set_config("offseason_mode", "false")
        self.team = Team(name="Haliburton Time!")
        db.session.add(self.team)
        db.session.commit()
        self.player = Player(
            name="Dontayvion Wicks", position="WR", team_id=self.team.id,
            fantasy_team=self.team.name, sleeper_player_id="9486",
            salary=5.0, contract_year=3, contract_start_season=2024,
            acquisition_type="auction_draft", espn_ref_value=7.7,
            is_dropped=True,
        )
        db.session.add(self.player)
        db.session.commit()

    def _run(self, readds=None, dropped=None, index=None, **ctx_kw):
        import sync_sleeper
        from models import db
        with mock.patch.object(sync_sleeper, "_build_regua_context",
                               return_value=(_fake_ctx(index or {}, **ctx_kw), None)):
            out = sync_sleeper._process_contract_regua(
                readds or [], dropped or [], {})
        # Espelha a produção: o run_sync commita depois do passo 8b. (Sem o commit,
        # o inspect() dentro de get_config devolve a conexão ÚNICA do SQLite em
        # memória com rollback e apaga a transação pendente — artefato de teste.)
        db.session.commit()
        return out


class TestReaddIntegracao(OrmBase):
    def test_caso2_mantem_contrato_e_grava_evento(self):
        from models import PlayerHistory
        index = {"9486": {
            "adds": [{"ts": _ms("2026-09-17 12:00"), "tx_id": "tx-add", "type": "waiver"}],
            "drops": [{"ts": _ms("2026-09-15 13:00"), "tx_id": "tx-drop", "type": "free_agent"}],
        }}
        out = self._run(readds=[(self.player, self.team)], index=index)
        self.assertEqual(len(out["mantidos"]), 1)
        self.assertEqual(self.player.contract_year, 3)      # cy idêntico
        self.assertEqual(self.player.salary, 5.0)           # salário idêntico
        ev = PlayerHistory.query.filter_by(sleeper_event_ref="tx:tx-add").first()
        self.assertIsNotNone(ev)                            # evento de add com ref da tx
        self.assertEqual(ev.event_type, "fa_waiver")        # vocabulário do rebuild F8

    def test_caso3_abre_ano1_pela_porta_canonica(self):
        from models import PlayerHistory, AuctionLog, SalaryHistory
        index = {"9486": {
            "adds": [{"ts": _ms("2026-09-25 12:00"), "tx_id": "tx-add", "type": "free_agent"}],
            "drops": [{"ts": _ms("2026-09-15 12:00"), "tx_id": "tx-drop", "type": "free_agent"}],
        }}
        out = self._run(readds=[(self.player, self.team)], index=index)
        self.assertEqual(len(out["contratos_novos"]), 1)
        self.assertEqual(self.player.contract_year, 1)
        self.assertEqual(self.player.contract_start_season, 2026)
        self.assertEqual(self.player.acquisition_type, "free_agent")
        self.assertEqual(self.player.salary, 1.0)
        # Validação 12: espn_ref_value PRESERVADO (armadilha OFF26-39.2).
        self.assertEqual(self.player.espn_ref_value, 7.7)
        # Canal REAL no AuctionLog (sem o off-label fa_auction do OFF26-34).
        log = AuctionLog.query.filter_by(player_id=self.player.id).first()
        self.assertEqual(log.entry_type, "free_agent")
        self.assertIn("[ref:tx:tx-add]", log.notes)         # token de idempotência vivo
        # Evento de timeline da porta canônica, ref = tx (dedupe simétrico c/ rebuild).
        ev = PlayerHistory.query.filter_by(sleeper_event_ref="tx:tx-add").first()
        self.assertIsNotNone(ev)
        self.assertEqual(ev.event_type, "free_agent")
        self.assertEqual(ev.contract_year, 1)
        # Idempotência: segunda passada não reescreve nada.
        n_logs = AuctionLog.query.count()
        n_sal = SalaryHistory.query.count()
        out2 = self._run(readds=[(self.player, self.team)], index=index)
        self.assertEqual(AuctionLog.query.count(), n_logs)
        self.assertEqual(SalaryHistory.query.count(), n_sal)
        self.assertEqual(len(out2["contratos_novos"]), 0)

    def test_falha_de_varredura_nao_muda_contrato(self):
        import sync_sleeper
        with mock.patch.object(sync_sleeper, "_build_regua_context",
                               return_value=(None, "transactions leg 3 indisponivel")):
            out = sync_sleeper._process_contract_regua(
                [(self.player, self.team)], [], {})
        self.assertEqual(out["skipped"], "transactions leg 3 indisponivel")
        self.assertEqual(self.player.contract_year, 3)
        self.assertEqual(self.player.salary, 5.0)


class TestDropEventos(OrmBase):
    def test_drop_grava_fato_e_fase_sem_duplicar(self):
        from models import PlayerHistory
        # Validação 4 + 11: data da TRANSAÇÃO (não do sync), fase derivada da data.
        index = {"9486": {"adds": [], "drops": [
            {"ts": _ms("2026-09-15 12:00"), "tx_id": "tx-d", "type": "free_agent"}]}}
        out = self._run(dropped=[self.player], index=index)
        self.assertEqual(out["drop_events"], 1)
        ev = PlayerHistory.query.filter_by(event_type="drop").one()
        self.assertEqual(ev.sleeper_event_ref, "tx:tx-d")
        self.assertIn("temporada", ev.notes)
        self.assertIn("15/09/2026 12:00 UTC", ev.notes)      # o FATO, da API
        out2 = self._run(dropped=[self.player], index=index)  # segundo sync
        self.assertEqual(out2["drop_events"], 0)
        self.assertEqual(PlayerHistory.query.filter_by(event_type="drop").count(), 1)

    def test_drop_intertemporada_com_flag_stale(self):
        from models import PlayerHistory, set_config
        # Validação 11: offseason_mode "true" NÃO muda a fase (decisão 6, log-only).
        set_config("offseason_mode", "true")
        index = {"9486": {"adds": [], "drops": [
            {"ts": _ms("2026-08-20 20:29"), "tx_id": "tx-ag", "type": "free_agent"}]}}
        self._run(dropped=[self.player], index=index)
        ev = PlayerHistory.query.filter_by(event_type="drop").one()
        self.assertIn("intertemporada", ev.notes)
        index2 = {"9486": {"adds": [], "drops": [
            {"ts": _ms("2026-09-15 12:00"), "tx_id": "tx-set", "type": "free_agent"}]}}
        out = self._run(dropped=[self.player], index=index2)
        ev2 = PlayerHistory.query.filter_by(sleeper_event_ref="tx:tx-set").one()
        self.assertIn("(temporada)", ev2.notes)
        self.assertTrue(any("offseason_mode" in w for w in out["warnings"]))

    def test_drop_sem_transacao_nao_sintetiza(self):
        from models import PlayerHistory
        out = self._run(dropped=[self.player], index={})
        self.assertEqual(out["drop_events"], 0)
        self.assertEqual(PlayerHistory.query.filter_by(event_type="drop").count(), 0)
        self.assertTrue(any("sem transação" in w for w in out["warnings"]))


class TestComissarioEArbitragem(OrmBase):
    DROP = {"ts": _ms("2026-08-24 10:00"), "tx_id": "tx-com", "type": "commissioner"}

    def _pendencia_de_drop(self, freeze_ms=None, frozen=False):
        index = {"9486": {"adds": [], "drops": [dict(self.DROP)]}}
        out = self._run(dropped=[self.player], index=index, freeze_ms=freeze_ms,
                        frozen_sids={"9486"} if frozen else set())
        return out

    def test_comissario_drop_vira_pendencia_sem_evento(self):
        from models import PlayerHistory, ContractPendency
        out = self._pendencia_de_drop()
        self.assertEqual(len(out["pendencias"]), 1)
        self.assertEqual(PlayerHistory.query.filter_by(event_type="drop").count(), 0)
        row = ContractPendency.query.one()
        self.assertEqual(row.kind, cr.KIND_COMISSARIO_DROP)
        self.assertEqual(row.status, "aberta")
        self.assertEqual(row.sleeper_transaction_id, "tx-com")
        # contrato intocado
        self.assertEqual(self.player.contract_year, 3)

    def test_veredito_sugerido_nos_dois_cenarios(self):
        from models import ContractPendency
        # drop PÓS-congelamento, jogador NA lista → sugere manobra
        self._pendencia_de_drop(freeze_ms=_ms("2026-08-22 12:02"), frozen=True)
        self.assertEqual(ContractPendency.query.one().suggested_verdict, "manobra")
        # drop PRÉ-congelamento → sugere real
        from models import db
        ContractPendency.query.delete()
        db.session.commit()
        index = {"9486": {"adds": [], "drops": [
            {"ts": _ms("2026-08-20 10:00"), "tx_id": "tx-pre", "type": "commissioner"}]}}
        self._run(dropped=[self.player], index=index,
                  freeze_ms=_ms("2026-08-22 12:02"))
        self.assertEqual(ContractPendency.query.one().suggested_verdict, "real")

    def test_arbitrar_manobra_contrato_intacto_sem_evento(self):
        from models import db, PlayerHistory, ContractPendency
        from sync_sleeper import apply_regua_consequence
        self._pendencia_de_drop()
        row = ContractPendency.query.one()
        apply_regua_consequence(row, "manobra")
        row.status, row.verdict = "arbitrada", "manobra"
        db.session.commit()
        self.assertEqual(PlayerHistory.query.filter_by(event_type="drop").count(), 0)
        self.assertEqual(self.player.contract_year, 3)
        self.assertEqual(self.player.salary, 5.0)

    def test_arbitrar_real_e_add_posterior_fora_da_janela_ano1(self):
        """Validação 3: 'real' grava o drop; o re-add seguinte segue a régua (ano 1)."""
        from models import db, PlayerHistory, ContractPendency
        from sync_sleeper import apply_regua_consequence
        self._pendencia_de_drop()
        row = ContractPendency.query.one()
        apply_regua_consequence(row, "real")
        row.status, row.verdict = "arbitrada", "real"
        db.session.commit()
        self.assertEqual(PlayerHistory.query.filter_by(event_type="drop").count(), 1)
        # re-add semanas depois, por free agent: veredito arbitrado alimenta a régua
        index = {"9486": {
            "adds": [{"ts": _ms("2026-09-20 12:00"), "tx_id": "tx-fa", "type": "free_agent"}],
            "drops": [dict(self.DROP)],
        }}
        out = self._run(readds=[(self.player, self.team)], index=index)
        self.assertEqual(len(out["contratos_novos"]), 1)
        self.assertEqual(self.player.contract_year, 1)
        self.assertEqual(self.player.contract_start_season, 2026)

    def test_pendencia_de_um_jogador_nao_bloqueia_outro(self):
        """Validação 3 (cauda): a pendência bloqueia SÓ o jogador dela."""
        from models import db, Player, ContractPendency
        outro = Player(name="Outro", position="RB", team_id=self.team.id,
                       fantasy_team=self.team.name, sleeper_player_id="777",
                       salary=2.0, contract_year=2, contract_start_season=2025,
                       acquisition_type="free_agent", espn_ref_value=0.0,
                       is_dropped=True)
        db.session.add(outro)
        db.session.commit()
        index = {
            "9486": {"adds": [{"ts": _ms("2026-09-20 12:00"), "tx_id": "tx-a2",
                               "type": "free_agent"}],
                     "drops": [dict(self.DROP)]},
            "777": {"adds": [{"ts": _ms("2026-09-25 12:00"), "tx_id": "tx-o",
                              "type": "free_agent"}],
                    "drops": [{"ts": _ms("2026-09-15 12:00"), "tx_id": "tx-od",
                               "type": "free_agent"}]},
        }
        out = self._run(readds=[(self.player, self.team), (outro, self.team)],
                        dropped=[], index=index)
        # 9486 (drop de comissário na cadeia) → pendência; 777 → caso 3 normal.
        self.assertEqual(len(out["pendencias"]), 1)
        self.assertEqual(len(out["contratos_novos"]), 1)
        self.assertEqual(outro.contract_year, 1)
        self.assertEqual(self.player.contract_year, 3)
        self.assertEqual(ContractPendency.query.count(), 1)

    def test_sinal_divergente_arbitrado_morto(self):
        from models import db, ContractPendency
        from sync_sleeper import apply_regua_consequence
        index = {"9486": {
            "adds": [{"ts": _ms("2026-09-16 12:00"), "tx_id": "tx-dv", "type": "free_agent"}],
            "drops": [{"ts": _ms("2026-09-15 12:00"), "tx_id": "tx-dd", "type": "free_agent"}],
        }}
        out = self._run(readds=[(self.player, self.team)], index=index)
        self.assertEqual(len(out["pendencias"]), 1)
        self.assertEqual(self.player.contract_year, 3)     # intocado até arbitrar
        row = ContractPendency.query.one()
        self.assertEqual(row.kind, cr.KIND_SINAL_DIVERGENTE)
        apply_regua_consequence(row, "morto")
        row.status, row.verdict = "arbitrada", "morto"
        db.session.commit()
        self.assertEqual(self.player.contract_year, 1)
        self.assertEqual(self.player.salary, 1.0)


class TestPortaCanonicaTimeline(OrmBase):
    def test_record_acquisition_grava_evento_com_ref_nunca_null(self):
        from models import record_acquisition, PlayerHistory
        p, sal = record_acquisition(
            team=self.team, acquisition_type="fa_waiver", season=2026,
            player=self.player, value_paid=0.0, espn_adjusted=7.7,
            sleeper_player_id="9486", event_ref=None, notes="porta manual")
        ev = PlayerHistory.query.filter_by(player_id=p.id,
                                           event_type="fa_waiver").one()
        # Sem event_ref do chamador, a ref nasce acq:<id> — NUNCA NULL (o rebuild F8
        # deleta rows sem ref; contrato de sobrevivência do OFF26-36).
        self.assertIsNotNone(ev.sleeper_event_ref)
        self.assertTrue(ev.sleeper_event_ref.startswith("acq:"))

    def test_rollover_do_offseason_gera_evento_com_ref(self):
        """Guarda de fonte: o loop do do_rollover grava PlayerHistory com
        ref rollover:<season> (OFF26-36 — a lacuna 222/222 não se repete)."""
        src = (BASE_DIR / "routes" / "offseason.py").read_text(encoding="utf-8")
        self.assertIn('sleeper_event_ref=f"rollover:{next_season}"', src)
        self.assertIn('event_type="renewal" if new_yr == 1 else "rollover"', src)


# ══════════════════════════════════════════════════════════════════════════════
# Guardas AST / de fonte (validação 8)
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardasAST(unittest.TestCase):
    def _src(self, rel):
        return (BASE_DIR / rel).read_text(encoding="utf-8")

    def test_nucleo_e_puro(self):
        src = self._src("contract_regua.py")
        self.assertIsNone(re.search(
            r"^\s*(from|import)\s+(models|flask|sqlalchemy|requests|sync_sleeper)",
            src, re.M), "contract_regua.py deve permanecer PURO (sem DB/rede/Flask)")

    def test_sync_nao_decide_readd_fora_do_helper(self):
        """A decisão vivo × morto só existe em contract_regua.decide_readd — o sync a
        importa e executa. Nenhuma aritmética de janela (×24) nem literal 48 no sync."""
        src = self._src("sync_sleeper.py")
        self.assertIn("decide_readd", src)
        self.assertLessEqual(src.count("waiver_clear_days"), 3,
                             "waiver_clear_days deve aparecer só na leitura do "
                             "_build_regua_context (docstring + get + msg de erro)")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == 48:
                self.fail(f"literal 48 (janela) em sync_sleeper.py linha {node.lineno}")
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                for side in (node.left, node.right):
                    if isinstance(side, ast.Constant) and side.value == 24:
                        self.fail(f"aritmética de janela (×24) em sync_sleeper.py "
                                  f"linha {node.lineno} — pertence ao helper")

    def test_admin_nao_aplica_consequencia_fora_do_executor(self):
        """A arbitragem executa SÓ via apply_regua_consequence (executor único do
        sync); nada de record_acquisition ou escrita de contrato direta no admin."""
        src = self._src("routes/admin.py")
        self.assertIn("apply_regua_consequence", src)
        tree = ast.parse(src)
        refs = [n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Name) and n.id == "record_acquisition"]
        self.assertEqual(refs, [], f"record_acquisition referenciado em "
                                   f"routes/admin.py (linhas {refs}) — a arbitragem "
                                   f"só executa via apply_regua_consequence")

    def test_nao_existe_quarta_classe_de_pendencia(self):
        """3 tipos, cada um com o par de vereditos do owner — uma 4ª classe seria
        arbitragem que o sync não tem autoridade para criar."""
        self.assertEqual(set(cr.VERDICTS_BY_KIND), {
            cr.KIND_COMISSARIO_DROP, cr.KIND_COMISSARIO_ADD,
            cr.KIND_SINAL_DIVERGENTE})

    def test_varredura_filtra_status_complete(self):
        """Lição Jones×Goff: sem o filtro, os 3 claims failed mudam a cadeia."""
        src = self._src("sync_sleeper.py")
        self.assertIn('tx.get("status") != "complete"', src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
