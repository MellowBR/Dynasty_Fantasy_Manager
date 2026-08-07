"""
late_drop_test.py — OFF26-10 (a URNA do late drop) + U7 (keeper sheet via sync).

Cobre o que o ciclo de 22/08 não pode errar:

  * escolha única, passo explícito e substituição (U1/U2/U4);
  * ⛔ PORTA ÚNICA — a urna NÃO usa `cuts_window_open`, e a rota de declaração legada
    continua recusando enquanto a urna está aberta (a exigência que motivou a flag
    própria; se alguém "simplificar" reusando a flag, este teste cai);
  * sigilo (U1) × contagem agregada (U1-CONT): o selado é **quem** e **o quê**; o "N/12
    depositaram" é público e conta drop e passo indistintamente — nem inclinação vaza;
  * bloqueio mútuo urna × rollover, nos dois sentidos (bilhete é escopado por season:
    virar a season no meio deixaria a revelação vazia, sem erro nenhum);
  * hierarquia owner > admin: suprimento sobre declarante pessoal é recusado SEM vazar;
  * flag do rookie de 1ª rodada: OFF permite, ON recusa com mensagem clara;
  * lock/hash/reveal no molde M8 + U6 (jogador que saiu do roster vira passo com aviso);
  * keeper sheet SEM snapshot de janela: nasce do roster vivo, com carimbo do sync,
    provisória × definitiva pelo sync posterior à revelação, e IR marcado (OFF26-15).

Armadilha registrada (herdada do POSENSAIO): os testes de rota NÃO mantêm app context
externo empurrado — o flask_login cacheia o usuário em `g` e todos os requests herdariam
o primeiro usuário logado.
"""

import unittest
from datetime import datetime, timedelta


def _iso(dt):
    return dt.replace(microsecond=0).isoformat() + "Z"


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User
        from routes.cuts import cuts_bp
        from routes.late_drop import late_drop_bp

        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["SECRET_KEY"] = "teste"
        db.init_app(cls.app)
        lm = LoginManager()
        lm.init_app(cls.app)

        @lm.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

        cls.app.register_blueprint(cuts_bp)
        cls.app.register_blueprint(late_drop_bp)

    def setUp(self):
        from models import db, Team, Player, User, AuctionLog, set_config, get_current_season
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            t_a = Team(name="Time A")
            t_b = Team(name="Time B")
            db.session.add_all([t_a, t_b])
            db.session.commit()
            admin = User(email="admin@x.com", team_id=None, is_admin=True)
            owner_a = User(email="a@x.com", team_id=t_a.id, is_admin=False)
            owner_b = User(email="b@x.com", team_id=t_b.id, is_admin=False)
            kicker = Player(name="Kicker Ficticio", position="K", salary=1.0, team_id=t_a.id)
            estrela = Player(name="Estrela Cara", position="WR", salary=50.0, team_id=t_a.id)
            machucado = Player(name="Lesionado Ir", position="RB", salary=8.0,
                               team_id=t_a.id, is_on_ir=True)
            rookie = Player(name="Rookie Primeira", position="RB", salary=20.0, team_id=t_a.id)
            do_b = Player(name="Jogador Do B", position="TE", salary=5.0, team_id=t_b.id)
            db.session.add_all([admin, owner_a, owner_b, kicker, estrela, machucado,
                                rookie, do_b])
            db.session.commit()
            season = get_current_season()
            db.session.add(AuctionLog(season=season, player_id=rookie.id, team_id=t_a.id,
                                      entry_type="rookie_draft", round_num=1,
                                      value_paid=20.0))
            db.session.commit()
            self.season = season
            self.admin_id, self.owner_a_id, self.owner_b_id = admin.id, owner_a.id, owner_b.id
            self.t_a_id, self.t_b_id = t_a.id, t_b.id
            self.kicker_id, self.estrela_id = kicker.id, estrela.id
            self.ir_id, self.rookie_id, self.do_b_id = machucado.id, rookie.id, do_b.id
            # urna aberta por padrão (agenda ampla, no molde do U3)
            now = datetime.utcnow()
            set_config("late_drop_opens_at", _iso(now - timedelta(hours=1)))
            set_config("late_drop_closes_at", _iso(now + timedelta(hours=1)))
            set_config("late_drop_block_r1_rookie", "false")
            # condição normal de operação (calendário: rollover 18/08 → urna 20/08).
            # O bloqueio mútuo tem classe própria, que mexe nesta flag de propósito.
            set_config("rollover_done", "true")
            set_config("cuts_ensaio_banner", "false")
            db.session.commit()

    def _as(self, user_id):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s["_user_id"] = str(user_id)
            s["_fresh"] = True
        return c

    def _set(self, key, value):
        from models import db, set_config
        with self.app.app_context():
            set_config(key, value)
            db.session.commit()


class TestDeposito(_Base):
    """U1/U2/U4 — um bilhete por time: jogador OU passo, substituível até o lock."""

    def test_deposita_um_jogador(self):
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                           json={"player_id": self.kicker_id})
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertTrue(d["success"])
        self.assertEqual(d["player_id"], self.kicker_id)
        self.assertFalse(d["passed"])

    def test_deposita_passo_explicito(self):
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration", json={"pass": True})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["passed"])

    def test_substituicao_vale_a_ultima(self):
        c = self._as(self.owner_a_id)
        c.post("/api/late_drop/declaration", json={"player_id": self.kicker_id})
        c.post("/api/late_drop/declaration", json={"player_id": self.estrela_id})
        c.post("/api/late_drop/declaration", json={"pass": True})
        d = c.get("/api/late_drop/declaration").get_json()
        self.assertTrue(d["passed"])
        self.assertIsNone(d["player_id"])

    def test_uma_linha_por_time_mesmo_com_varias_trocas(self):
        from models import LateDropDeclaration
        c = self._as(self.owner_a_id)
        c.post("/api/late_drop/declaration", json={"player_id": self.kicker_id})
        c.post("/api/late_drop/declaration", json={"player_id": self.estrela_id})
        with self.app.app_context():
            self.assertEqual(LateDropDeclaration.query.filter_by(
                season=self.season, team_id=self.t_a_id).count(), 1)

    def test_nao_dropa_jogador_de_outro_time(self):
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                           json={"player_id": self.do_b_id})
        self.assertEqual(r.status_code, 400)
        self.assertIn("não está no roster", r.get_json()["error"])

    def test_body_vazio_e_recusado(self):
        """Sem escolha explícita não há depósito — 'passo' tem de ser ATO, não default."""
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration", json={})
        self.assertEqual(r.status_code, 400)

    def test_fora_da_janela_nao_aceita(self):
        now = datetime.utcnow()
        self._set("late_drop_opens_at", _iso(now + timedelta(hours=2)))
        self._set("late_drop_closes_at", _iso(now + timedelta(hours=3)))
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                           json={"pass": True})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["reason"], "ainda_nao_abriu")

    def test_janela_encerrada_nao_aceita(self):
        now = datetime.utcnow()
        self._set("late_drop_opens_at", _iso(now - timedelta(hours=3)))
        self._set("late_drop_closes_at", _iso(now - timedelta(hours=2)))
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                           json={"pass": True})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["reason"], "encerrada")

    def test_sem_agenda_a_urna_esta_fechada(self):
        self._set("late_drop_opens_at", "")
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration", json={"pass": True})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["reason"], "nao_agendada")


class TestPortaUnicaESigilo(_Base):
    """⛔ A exigência estrutural: uma porta só, e sigilo sobre a própria existência."""

    def test_a_urna_nao_usa_a_flag_da_janela_legada(self):
        """Se alguém reusar `cuts_window_open`, a porta antiga reabre junto — este teste
        é o que impede a 'simplificação'."""
        from models import get_config
        with self.app.app_context():
            self.assertNotEqual(get_config("cuts_window_open", "false"), "true")
        # urna aberta (setUp) e, ainda assim, a rota legada recusa:
        r = self._as(self.owner_a_id).post("/api/cuts/declaration",
                                           json={"cut_ids": [self.kicker_id]})
        self.assertEqual(r.status_code, 409)
        self.assertIn("não está aberta", r.get_json()["error"])

    def test_estado_nao_expoe_declaracao_alheia(self):
        """A contagem agregada existe (U1-CONT); QUEM e O QUÊ, não."""
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        body = self._as(self.owner_b_id).get("/api/late_drop/state").get_data(as_text=True)
        self.assertNotIn("Kicker", body)
        self.assertNotIn("player_id", body)      # nenhum id de jogador no agregado
        self.assertNotIn("Time A", body)         # nem o time de quem declarou
        self.assertIn('"i_declared":false', body.replace(" ", ""))

    def test_declaracao_alheia_nao_vaza_pela_rota_do_owner(self):
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        d = self._as(self.owner_b_id).get("/api/late_drop/declaration").get_json()
        self.assertEqual(d["team_id"], self.t_b_id)
        self.assertFalse(d["declared"])

    def test_audit_nao_revela_antes_do_lock(self):
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        d = self._as(self.owner_b_id).get("/api/late_drop/audit").get_json()
        self.assertFalse(d["revealed"])
        self.assertNotIn("audit", d)


class TestContagemAgregada(_Base):
    """U1-CONT (arbitragem do owner, 07/08/2026): o selado é QUEM e O QUÊ. A contagem
    agregada não expõe nenhum dos dois — drop e passo contam igual, então nem inclinação
    vaza — e tem função operacional (andamento; e quantos faltam cutucar antes do lock)."""

    def _count(self, uid):
        return self._as(uid).get("/api/late_drop/state").get_json()

    def test_comeca_em_zero(self):
        d = self._count(self.owner_b_id)
        self.assertEqual(d["declared_count"], 0)
        self.assertEqual(d["total_teams"], 2)

    def test_o_passo_conta_igual_ao_drop(self):
        """Se só o drop contasse, o N viraria dedo-duro de inclinação."""
        self._as(self.owner_a_id).post("/api/late_drop/declaration", json={"pass": True})
        self.assertEqual(self._count(self.owner_b_id)["declared_count"], 1)
        self._as(self.owner_b_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.do_b_id})
        self.assertEqual(self._count(self.owner_a_id)["declared_count"], 2)

    def test_substituicao_nao_infla_a_contagem(self):
        c = self._as(self.owner_a_id)
        c.post("/api/late_drop/declaration", json={"player_id": self.kicker_id})
        c.post("/api/late_drop/declaration", json={"player_id": self.estrela_id})
        c.post("/api/late_drop/declaration", json={"pass": True})
        self.assertEqual(self._count(self.owner_b_id)["declared_count"], 1)

    def test_suprimento_do_admin_tambem_conta(self):
        self._as(self.admin_id).post("/api/late_drop/admin/declare",
                                      json={"team_id": self.t_b_id, "pass": True})
        self.assertEqual(self._count(self.owner_a_id)["declared_count"], 1)

    def test_a_contagem_nao_individualiza_ninguem(self):
        """⛔ O agregado devolve NÚMEROS, não times: nenhuma chave permite reconstruir
        quem compõe o N, nem separar drop de passo."""
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        d = self._count(self.owner_b_id)
        proibidas = ("declared_teams", "teams_declared", "declarations", "declarantes",
                     "num_drops", "num_passes", "drops", "passes", "pending_teams")
        for k in proibidas:
            self.assertNotIn(k, d, f"chave {k} individualizaria/separaria o agregado")
        self.assertEqual(
            set(d) - {"season", "state", "reason", "opens_at", "closes_at",
                      "block_r1_rookie", "is_admin", "my_team_id", "my_team_name",
                      "declared_count", "total_teams", "i_declared"},
            set(), "chave nova no /state — conferir se não vaza")

    def test_nem_o_admin_ve_quem_declarou(self):
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        body = self._as(self.admin_id).get("/api/late_drop/state").get_data(as_text=True)
        self.assertIn('"declared_count":1', body.replace(" ", ""))
        self.assertNotIn("Time A", body)
        self.assertNotIn("Kicker", body)


class TestBloqueioMutuoComRollover(_Base):
    """MAN-OFF26-10-AJUSTES: a ordem rollover → urna deixou de ser instrução de runbook.

    Motivo: bilhetes e snapshot são escopados por `current_season`. Virar a season no meio
    deixa os bilhetes órfãos e **a revelação sai vazia, sem erro nenhum**."""

    def test_urna_agendada_bloqueia_o_rollover(self):
        from routes.late_drop import urn_blocks_rollover
        with self.app.app_context():
            motivo = urn_blocks_rollover(self.season)
        self.assertIsNotNone(motivo)
        self.assertIn("órfãos", motivo)
        self.assertIn("revelação", motivo)

    def test_urna_com_bilhete_mas_sem_agenda_tambem_bloqueia(self):
        from routes.late_drop import urn_blocks_rollover
        self._as(self.owner_a_id).post("/api/late_drop/declaration", json={"pass": True})
        self._set("late_drop_opens_at", "")
        self._set("late_drop_closes_at", "")
        with self.app.app_context():
            self.assertIsNotNone(urn_blocks_rollover(self.season))

    def test_sem_urna_nao_bloqueia(self):
        from routes.late_drop import urn_blocks_rollover
        self._set("late_drop_opens_at", "")
        self._set("late_drop_closes_at", "")
        with self.app.app_context():
            self.assertIsNone(urn_blocks_rollover(self.season))

    def test_apos_a_revelacao_o_rollover_libera(self):
        """Snapshot congelado: virar a season já não perde nada."""
        from routes.late_drop import urn_blocks_rollover
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        self._as(self.admin_id).post("/api/late_drop/admin/lock")
        with self.app.app_context():
            self.assertIsNone(urn_blocks_rollover(self.season))

    # ── sentido inverso ──

    def test_rollover_pendente_bloqueia_o_agendamento(self):
        self._set("rollover_done", "false")
        self._set("cuts_ensaio_banner", "false")
        now = datetime.utcnow()
        r = self._as(self.admin_id).post("/api/late_drop/admin/schedule", json={
            "opens_at": _iso(now), "closes_at": _iso(now + timedelta(hours=2))})
        self.assertEqual(r.status_code, 409)
        d = r.get_json()
        self.assertEqual(d["blocked_by"], "rollover_pendente")
        self.assertIn("passo 4", d["error"])

    def test_com_rollover_feito_o_agendamento_passa(self):
        self._set("rollover_done", "true")
        now = datetime.utcnow()
        r = self._as(self.admin_id).post("/api/late_drop/admin/schedule", json={
            "opens_at": _iso(now - timedelta(minutes=1)),
            "closes_at": _iso(now + timedelta(hours=2))})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["state"], "open")

    def test_banner_de_ensaio_libera_o_smoke_antes_do_rollover(self):
        """Escape declarado: sem ele, o gate impediria o próprio smoke da urna, que roda
        antes de 20/08 e pode cair antes do rollover de 18/08."""
        self._set("rollover_done", "false")
        self._set("cuts_ensaio_banner", "true")
        now = datetime.utcnow()
        r = self._as(self.admin_id).post("/api/late_drop/admin/schedule", json={
            "opens_at": _iso(now), "closes_at": _iso(now + timedelta(hours=2))})
        self.assertEqual(r.status_code, 200)

    def test_limpar_a_agenda_e_sempre_permitido(self):
        """É o caminho de destravar: se o gate barrasse a limpeza, urna e rollover
        ficariam em impasse."""
        self._set("rollover_done", "false")
        self._set("cuts_ensaio_banner", "false")
        r = self._as(self.admin_id).post("/api/late_drop/admin/schedule",
                                          json={"opens_at": "", "closes_at": ""})
        self.assertEqual(r.status_code, 200)
        from routes.late_drop import urn_blocks_rollover
        with self.app.app_context():
            self.assertIsNone(urn_blocks_rollover(self.season))


class TestRotaDoRolloverRecusa(unittest.TestCase):
    """O gate no lugar onde o botão vive (`POST /api/offseason/rollover`)."""

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User
        from routes.offseason import offseason_bp
        from routes.late_drop import late_drop_bp

        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["SECRET_KEY"] = "teste"
        db.init_app(cls.app)
        lm = LoginManager()
        lm.init_app(cls.app)

        @lm.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

        cls.app.register_blueprint(offseason_bp)
        cls.app.register_blueprint(late_drop_bp)

    def setUp(self):
        from models import (db, Team, Player, User, SeasonStandings, DraftLotteryResult,
                            set_config, get_current_season)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            t = Team(name="Time Unico")
            db.session.add(t)
            db.session.commit()
            admin = User(email="admin@x.com", team_id=None, is_admin=True)
            p = Player(name="Jogador X", position="WR", salary=10.0, team_id=t.id,
                       contract_year=1)
            db.session.add_all([admin, p])
            db.session.commit()
            season = get_current_season()
            # destrava o passo 4 (exige lottery travado + ESPN atualizado)
            db.session.add(SeasonStandings(season=season, team_id=t.id,
                                           team_name=t.name, rank=1))
            db.session.add(DraftLotteryResult(season=season + 1, pick_number=1,
                                              team_id=t.id, team_name=t.name, locked=True))
            set_config("espn_values_updated", "true")
            set_config("rollover_done", "false")
            db.session.commit()
            self.season, self.admin_id, self.t_id = season, admin.id, t.id

    def _admin(self):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s["_user_id"] = str(self.admin_id)
            s["_fresh"] = True
        return c

    def _agendar(self):
        from models import db, set_config
        with self.app.app_context():
            now = datetime.utcnow()
            set_config("late_drop_opens_at", _iso(now - timedelta(minutes=5)))
            set_config("late_drop_closes_at", _iso(now + timedelta(hours=2)))
            db.session.commit()

    def test_rollover_recusado_com_a_urna_aberta(self):
        self._agendar()
        r = self._admin().post("/api/offseason/rollover")
        self.assertEqual(r.status_code, 409)
        d = r.get_json()
        self.assertEqual(d["blocked_by"], "urna_late_drop")
        self.assertIn("lock + revelação", d["error"])

    def test_rollover_passa_sem_urna(self):
        r = self._admin().post("/api/offseason/rollover")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["success"])

    def test_rollover_passa_apos_a_revelacao(self):
        self._agendar()
        self.assertEqual(self._admin().post("/api/late_drop/admin/lock").status_code, 200)
        r = self._admin().post("/api/offseason/rollover")
        self.assertEqual(r.status_code, 200)


class TestHierarquia(_Base):
    """Herdada da janela e confirmada em produção no ensaio de 06/08."""

    def test_admin_supre_time_silencioso(self):
        r = self._as(self.admin_id).post("/api/late_drop/admin/declare",
                                          json={"team_id": self.t_b_id, "pass": True})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["success"])

    def test_admin_nao_sobrescreve_declarante_pessoal_e_nao_vaza(self):
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        r = self._as(self.admin_id).post("/api/late_drop/admin/declare",
                                          json={"team_id": self.t_a_id, "pass": True})
        self.assertEqual(r.status_code, 409)
        corpo = r.get_data(as_text=True)
        self.assertIn("declarou pessoalmente", corpo)
        self.assertNotIn("Kicker", corpo)
        self.assertNotIn("player_id", corpo)

    def test_admin_nao_sobrescreve_nem_o_passo_do_owner(self):
        self._as(self.owner_a_id).post("/api/late_drop/declaration", json={"pass": True})
        r = self._as(self.admin_id).post("/api/late_drop/admin/declare",
                                          json={"team_id": self.t_a_id,
                                                "player_id": self.kicker_id})
        self.assertEqual(r.status_code, 409)

    def test_owner_sobrescreve_suprimento_do_admin(self):
        r = self._as(self.admin_id).post("/api/late_drop/admin/declare",
                                          json={"team_id": self.t_a_id, "pass": True})
        self.assertEqual(r.status_code, 200)
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                            json={"player_id": self.kicker_id})
        self.assertEqual(r.status_code, 200)


class TestFlagRookiePrimeiraRodada(_Base):
    """U6 — a flag nasce OFF; o código não arbitra regra em disputa na liga."""

    def test_default_e_desligada_e_permite(self):
        from models import get_config
        with self.app.app_context():
            self.assertEqual(get_config("late_drop_block_r1_rookie", "false"), "false")
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                            json={"player_id": self.rookie_id})
        self.assertEqual(r.status_code, 200)

    def test_ligada_recusa_com_mensagem_clara(self):
        self._as(self.admin_id).post("/api/late_drop/admin/config",
                                      json={"block_r1_rookie": True})
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                            json={"player_id": self.rookie_id})
        self.assertEqual(r.status_code, 400)
        erro = r.get_json()["error"]
        self.assertIn("rookie de 1ª rodada", erro)
        self.assertIn("Rookie Primeira", erro)

    def test_ligada_nao_bloqueia_os_demais(self):
        self._as(self.admin_id).post("/api/late_drop/admin/config",
                                      json={"block_r1_rookie": True})
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                            json={"player_id": self.estrela_id})
        self.assertEqual(r.status_code, 200)

    def test_marca_o_bloqueado_na_lista_de_elegiveis(self):
        from routes.late_drop import _eligible
        self._as(self.admin_id).post("/api/late_drop/admin/config",
                                      json={"block_r1_rookie": True})
        with self.app.app_context():
            elig = {p["id"]: p for p in _eligible(self.t_a_id, self.season)}
        self.assertTrue(elig[self.rookie_id]["blocked"])
        self.assertFalse(elig[self.kicker_id]["blocked"])


class TestLockRevelacao(_Base):
    """U5/U6 — molde M8: snapshot canônico, hash verificável, cadeia no replace."""

    def _lock(self):
        return self._as(self.admin_id).post("/api/late_drop/admin/lock")

    def test_lock_revela_drops_e_passos(self):
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        self._as(self.owner_b_id).post("/api/late_drop/declaration", json={"pass": True})
        self.assertEqual(self._lock().status_code, 200)

        d = self._as(self.owner_b_id).get("/api/late_drop/audit").get_json()
        self.assertTrue(d["revealed"])
        self.assertEqual(d["num_drops"], 1)
        self.assertEqual(d["drops_to_execute"][0]["drop_name"], "Kicker Ficticio")
        por_time = {t["team_id"]: t for t in d["audit"]["declarations"]}
        self.assertTrue(por_time[self.t_b_id]["passed"])
        self.assertIsNone(por_time[self.t_b_id]["drop_id"])

    def test_hash_confere(self):
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        self._lock()
        d = self._as(self.admin_id).get("/api/late_drop/audit/verify").get_json()
        self.assertTrue(d["hash_match"])

    def test_hash_e_o_da_janela_reuso_nao_reimplementacao(self):
        """U5: o núcleo de integridade é a MESMA função da janela de cortes."""
        from models import compute_cut_snapshot_hash, LateDropAudit
        import json
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        self._lock()
        with self.app.app_context():
            a = LateDropAudit.query.filter_by(is_canonical=True).first()
            self.assertEqual(
                a.result_hash,
                compute_cut_snapshot_hash(json.loads(a.declarations_json)))

    def test_time_silencioso_entra_como_passo(self):
        self._lock()
        d = self._as(self.admin_id).get("/api/late_drop/audit").get_json()
        self.assertEqual(d["num_drops"], 0)
        for t in d["audit"]["declarations"]:
            self.assertFalse(t["declared"])
            self.assertIsNone(t["drop_id"])

    def test_jogador_que_saiu_do_roster_vira_passo_com_aviso(self):
        """U6: trade/drop entre o depósito e o lock não pode virar drop fantasma."""
        from models import db, Player
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        with self.app.app_context():
            p = db.session.get(Player, self.kicker_id)
            p.team_id = self.t_b_id            # foi trocado
            db.session.commit()
        self._lock()
        d = self._as(self.admin_id).get("/api/late_drop/audit").get_json()
        self.assertEqual(d["num_drops"], 0)
        a = {t["team_id"]: t for t in d["audit"]["declarations"]}[self.t_a_id]
        self.assertTrue(a["invalidated"])
        self.assertIn("não estava mais no roster", a["invalid_reason"])

    def test_segundo_lock_recusado_sem_reason(self):
        self._lock()
        r = self._lock()
        self.assertEqual(r.status_code, 409)

    def test_replace_exige_reason_e_encadeia(self):
        self._lock()
        r = self._as(self.admin_id).post("/api/late_drop/admin/replace", json={})
        self.assertEqual(r.status_code, 400)
        r = self._as(self.admin_id).post("/api/late_drop/admin/replace",
                                          json={"reason": "erro operacional"})
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.get_json()["audit"]["previous_audit_id"])

    def test_pos_lock_a_urna_nao_aceita_mais_deposito(self):
        self._lock()
        r = self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                            json={"pass": True})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["reason"], "revelada")

    def test_suprimento_admin_tambem_trava_pos_lock(self):
        self._lock()
        r = self._as(self.admin_id).post("/api/late_drop/admin/declare",
                                          json={"team_id": self.t_b_id, "pass": True})
        self.assertEqual(r.status_code, 409)


class TestAgenda(_Base):
    """U3 — a janela abre e fecha por horário definido pelo admin."""

    def test_admin_grava_horarios(self):
        now = datetime.utcnow()
        r = self._as(self.admin_id).post("/api/late_drop/admin/schedule", json={
            "opens_at": _iso(now - timedelta(minutes=5)),
            "closes_at": _iso(now + timedelta(hours=2)),
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["state"], "open")

    def test_fechamento_antes_da_abertura_e_recusado(self):
        now = datetime.utcnow()
        r = self._as(self.admin_id).post("/api/late_drop/admin/schedule", json={
            "opens_at": _iso(now + timedelta(hours=2)),
            "closes_at": _iso(now + timedelta(hours=1)),
        })
        self.assertEqual(r.status_code, 400)

    def test_horario_invalido_e_recusado(self):
        r = self._as(self.admin_id).post("/api/late_drop/admin/schedule",
                                          json={"opens_at": "ontem à tarde"})
        self.assertEqual(r.status_code, 400)

    def test_owner_nao_agenda(self):
        r = self._as(self.owner_a_id).post("/api/late_drop/admin/schedule", json={})
        self.assertIn(r.status_code, (401, 403))


class TestKeeperSheetViaSync(_Base):
    """U7 — a sheet nasce do SYNC, sem gate de snapshot da janela extinta."""

    def _sheet(self):
        from routes.cuts import _build_keeper_sheet
        with self.app.app_context():
            return _build_keeper_sheet(self.season)

    def _sync(self, when=None):
        from models import db, SyncLog
        with self.app.app_context():
            db.session.add(SyncLog(synced_at=when or datetime.utcnow()))
            db.session.commit()

    def test_sai_sem_nenhum_snapshot_de_janela(self):
        from models import CutWindowAudit
        with self.app.app_context():
            self.assertEqual(CutWindowAudit.query.count(), 0)
        s = self._sheet()
        self.assertTrue(s["available"])
        self.assertEqual(s["source"], "sync")
        self.assertEqual(len(s["teams"]), 2)

    def test_keepers_sao_o_roster_vivo(self):
        s = self._sheet()
        a = {t["team_name"]: t for t in s["teams"]}["Time A"]
        self.assertEqual(a["num_keepers"], 4)          # kicker, estrela, IR, rookie
        self.assertEqual(a["num_ir"], 1)               # OFF26-15
        nomes = {k["name"] for k in a["keepers"]}
        self.assertIn("Lesionado Ir", nomes)           # IR é keeper e ocupa designação

    def test_ir_vem_marcado_por_jogador(self):
        a = {t["team_name"]: t for t in self._sheet()["teams"]}["Time A"]
        por_nome = {k["name"]: k for k in a["keepers"]}
        self.assertTrue(por_nome["Lesionado Ir"]["is_on_ir"])
        self.assertFalse(por_nome["Kicker Ficticio"]["is_on_ir"])

    def test_bid_maximo_vem_da_fonte_unica(self):
        from salary_engine import draft_budget
        from types import SimpleNamespace
        s = self._sheet()
        a = {t["team_name"]: t for t in s["teams"]}["Time A"]
        esperado = draft_budget([SimpleNamespace(salary=x, is_dropped=False)
                                 for x in (1.0, 50.0, 8.0, 20.0)])["usable_draft_budget"]
        self.assertEqual(a["fa_budget"], int(esperado))

    def test_carimbo_do_sync(self):
        self._sync()
        s = self._sheet()
        self.assertIsNotNone(s["sync_timestamp"])
        self.assertEqual(s["lock_timestamp"], s["sync_timestamp"])

    def test_provisoria_antes_da_urna(self):
        self._sync()
        s = self._sheet()
        self.assertEqual(s["stage"], "provisoria")
        self.assertFalse(s["late_drop"]["revealed"])

    def test_continua_provisoria_se_nao_houve_sync_apos_a_revelacao(self):
        """O estado perigoso: revelado e não executado. A sheet não pode dizer 'definitiva'."""
        self._sync(datetime.utcnow() - timedelta(hours=2))
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        self._as(self.admin_id).post("/api/late_drop/admin/lock")
        s = self._sheet()
        self.assertEqual(s["stage"], "provisoria")
        self.assertTrue(s["late_drop"]["revealed"])
        self.assertEqual(s["late_drop"]["num_drops"], 1)

    def test_definitiva_apos_execucao_e_sync_final(self):
        from models import db, Player
        self._as(self.owner_a_id).post("/api/late_drop/declaration",
                                        json={"player_id": self.kicker_id})
        self._as(self.admin_id).post("/api/late_drop/admin/lock")
        # execução manual no Sleeper + sync final: o jogador sai do roster
        with self.app.app_context():
            p = db.session.get(Player, self.kicker_id)
            p.is_dropped = True
            db.session.commit()
        self._sync()
        s = self._sheet()
        self.assertEqual(s["stage"], "definitiva")
        a = {t["team_name"]: t for t in s["teams"]}["Time A"]
        self.assertEqual(a["num_keepers"], 3)
        self.assertNotIn("Kicker Ficticio", {k["name"] for k in a["keepers"]})
        self.assertEqual(a["late_drop_label"], "Late drop: Kicker Ficticio")

    def test_rotulo_de_time_sem_late_drop(self):
        self._as(self.admin_id).post("/api/late_drop/admin/lock")
        a = {t["team_name"]: t for t in self._sheet()["teams"]}["Time A"]
        self.assertEqual(a["late_drop_label"], "Sem late drop")

    def test_contrato_do_nucleo_da_auditoria_preservado(self):
        """A auditoria (OFF26-4, núcleo puro + fixtures congeladas) lê `revealed` para
        saber se há sheet utilizável. A chave permanece — mudou a ORIGEM, não o contrato."""
        s = self._sheet()
        self.assertTrue(s["revealed"])
        for t in s["teams"]:
            self.assertIn("fa_budget", t)
            self.assertIn("keepers", t)

    def test_sheet_e_artefato_de_admin(self):
        r = self._as(self.owner_a_id).get("/api/cuts/keeper_sheet")
        self.assertIn(r.status_code, (401, 403))
        r = self._as(self.admin_id).get("/api/cuts/keeper_sheet")
        self.assertEqual(r.status_code, 200)

    def test_csv_traz_ir_e_bid_maximo(self):
        r = self._as(self.admin_id).get("/api/cuts/keeper_sheet.csv")
        self.assertEqual(r.status_code, 200)
        txt = r.get_data(as_text=True)
        self.assertIn("Bid Maximo (time)", txt)
        self.assertIn("Lesionado Ir", txt)
        linha_ir = [l for l in txt.splitlines() if "Lesionado Ir" in l][0]
        self.assertIn(",IR,", linha_ir)


class TestSemConfirmNativo(unittest.TestCase):
    """U-CONF — o pop-up nativo travou o co-admin no celular durante o ensaio."""

    def test_nenhum_window_confirm_no_caminho_de_declaracao(self):
        from pathlib import Path
        base = Path(__file__).resolve().parent
        for tpl in ("late_drop.html", "cuts.html"):
            src = (base / "templates" / tpl).read_text(encoding="utf-8")
            # comentários citam `window.confirm()` de propósito (é o que NÃO se usa) —
            # a guarda vale para código executável: fora comentário Jinja e linha `//`
            import re
            sem_jinja = re.sub(r"\{#.*?#\}", "", src, flags=re.S)
            codigo = "\n".join(l for l in sem_jinja.splitlines()
                               if not l.strip().startswith("//"))
            self.assertNotIn("confirm(", codigo.replace("confirmarInline(", ""), tpl)
            self.assertIn("confirmarInline", src, tpl)


if __name__ == "__main__":
    unittest.main(verbosity=2)
