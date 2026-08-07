"""
keeper_exclusion_test.py — OFF26-11: a keeper sheet como LISTA DE EXCLUSÃO do importador.

O que estes testes protegem é uma assimetria: os dois erros possíveis são silenciosos e
simétricos, e nenhum aparece no cap do ano corrente.

  · ingerir um KEEPER   → `record_acquisition` zera a idade do contrato de quem nunca
                          saiu do time; aparece anos depois, na renovação;
  · excluir um ARREMATE → o contrato ano 1 do jogador recomprado simplesmente não nasce.

O segundo é o que uma implementação ingênua produz: a keeper sheet nasce do ROSTER VIVO,
e depois do leilão cada owner adiciona seus arremates na liga real — um sync entre o
leilão e o import faria o arremate aparecer como keeper. Por isso a lista é CONGELADA, e
por isso o teste de CONTAMINAÇÃO é o mais importante do arquivo.

    python keeper_exclusion_test.py

Núcleo puro (sem DB/rede/Flask) + integração ORM em memória com a API do Sleeper
mockada — nenhuma requisição de rede, nenhuma escrita na plataforma.
"""

import json
import unittest
from datetime import datetime, timedelta

import keeper_exclusion as kx


# ══════════════════════════════════════════════════════════════════════════════
# NÚCLEO PURO
# ══════════════════════════════════════════════════════════════════════════════

def _kp(sid, team_id, name="X", salary=10, position="WR"):
    return {"sleeper_player_id": sid, "team_id": team_id, "team_name": f"T{team_id}",
            "name": name, "salary": salary, "position": position}


class TestNucleoPuro(unittest.TestCase):
    def setUp(self):
        self.index = kx.build_index([
            _kp("4881", 1, "Lamar Jackson", 40),
            _kp("LAR", 1, "Rams DEF", 3, "DEF"),      # DEF: id é SIGLA
            _kp("6790", 2, "Do Time Dois", 12),
        ])

    def test_keeper_do_mesmo_time_e_excluido(self):
        self.assertEqual(kx.classify_pick("4881", 1, self.index), kx.KIND_KEEPER)

    def test_keeper_de_outro_time_e_pendencia(self):
        self.assertEqual(kx.classify_pick("4881", 2, self.index), kx.KIND_KEEPER_OTHER)

    def test_fora_da_lista_e_arremate(self):
        self.assertEqual(kx.classify_pick("9999", 1, self.index), kx.KIND_ARREMATE)

    def test_def_com_sigla_classifica_sem_coercao(self):
        """`player_id` de DEF é 'LAR' — coagir a inteiro quebraria a leitura."""
        self.assertEqual(kx.classify_pick("LAR", 1, self.index), kx.KIND_KEEPER)
        self.assertEqual(kx.classify_pick("LAR", 2, self.index), kx.KIND_KEEPER_OTHER)
        self.assertEqual(kx.classify_pick("SEA", 1, self.index), kx.KIND_ARREMATE)

    def test_sem_id_e_pendencia_nunca_arremate(self):
        for vazio in (None, "", "   "):
            self.assertEqual(kx.classify_pick(vazio, 1, self.index), kx.KIND_NO_ID)

    def test_sem_time_local_e_pendencia(self):
        self.assertEqual(kx.classify_pick("4881", None, self.index), kx.KIND_NO_TEAM)

    def test_id_e_sempre_string(self):
        """A API devolve string; um int no índice não pode virar buraco de exclusão."""
        idx = kx.build_index([_kp(4881, 1)])
        self.assertEqual(kx.classify_pick("4881", 1, idx), kx.KIND_KEEPER)

    def test_keeper_sem_id_nao_entra_no_indice(self):
        idx = kx.build_index([_kp(None, 1), _kp("", 1), _kp("7", 1)])
        self.assertEqual(list(idx), ["7"])

    def test_hash_independe_da_ordem_e_muda_com_o_conteudo(self):
        a = [_kp("1", 1, salary=5), _kp("2", 2, salary=9)]
        self.assertEqual(kx.compute_exclusion_hash(a),
                         kx.compute_exclusion_hash(list(reversed(a))))
        self.assertNotEqual(kx.compute_exclusion_hash(a),
                            kx.compute_exclusion_hash([_kp("1", 1, salary=6),
                                                       _kp("2", 2, salary=9)]))

    def test_pendencias_sao_exatamente_tres(self):
        """Toda pendência bloqueia. Nenhuma classe extra: uma quarta seria arbitragem
        que o importador não tem autoridade para fazer."""
        self.assertEqual(set(kx.PENDING_KINDS),
                         {kx.KIND_KEEPER_OTHER, kx.KIND_NO_ID, kx.KIND_NO_TEAM})
        for k in kx.PENDING_KINDS:
            self.assertIn(k, kx.KIND_REASON)

    def test_is_keeper_do_sleeper_nao_e_lido(self):
        """`is_keeper` vem `false` até nas designações — registro, NUNCA insumo."""
        with open(__file__.replace("_test.py", ".py"), encoding="utf-8") as fh:
            corpo = fh.read().split('"""', 2)[2]      # fora do docstring do módulo
        self.assertNotIn("is_keeper", corpo)


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRAÇÃO — ORM em memória + API do Sleeper mockada (nenhuma rede)
# ══════════════════════════════════════════════════════════════════════════════

DRAFT_ID = "DRAFT-TESTE"
LEAGUE_ID = "LIGA-FANTASMA"


class _Base(unittest.TestCase):
    """Dois times, roster com keepers, e um draft de auction sintético."""

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User
        from routes.cuts import cuts_bp
        from routes.draft_import import draft_import_bp

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
        cls.app.register_blueprint(draft_import_bp)

    def setUp(self):
        from models import db, Team, Player, User, SyncLog, get_current_season
        import sync_sleeper as ss
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            a = Team(name="Time A", sleeper_owner_id="OWNER-A")
            b = Team(name="Time B", sleeper_owner_id="OWNER-B")
            db.session.add_all([a, b])
            db.session.commit()
            admin = User(email="admin@x.com", is_admin=True)
            db.session.add(admin)
            # roster do Time A: 2 keepers + o jogador do CASO CANÔNICO (dropado)
            lamar = Player(name="Lamar Jackson", position="QB", salary=40.0,
                           team_id=a.id, sleeper_player_id="4881", contract_year=2)
            rams = Player(name="Rams DEF", position="DEF", salary=3.0,
                          team_id=a.id, sleeper_player_id="LAR", contract_year=3)
            # dropado na janela, com contrato de $50 e ano 3 — vai a leilão
            zeca = Player(name="Zeca Cinquenta", position="WR", salary=50.0,
                          team_id=a.id, sleeper_player_id="5050", contract_year=3,
                          is_dropped=True)
            dob = Player(name="Do Time B", position="TE", salary=12.0,
                         team_id=b.id, sleeper_player_id="6790", contract_year=1)
            # agente livre já cadastrado (sem time): não é keeper de ninguém, e casa por
            # sleeper_id no import → é o arremate MATCHED do cenário de budget
            livre = Player(name="Livre Agente", position="RB", salary=1.0,
                           team_id=None, sleeper_player_id="7777", contract_year=1)
            db.session.add_all([lamar, rams, zeca, dob, livre])
            db.session.add(SyncLog(synced_at=datetime.utcnow()))
            db.session.commit()
            self.season = get_current_season()
            self.admin_id = admin.id
            self.a_id, self.b_id = a.id, b.id
            self.zeca_id, self.lamar_id, self.rams_id = zeca.id, lamar.id, rams.id

        # A API do Sleeper é substituída por payloads sintéticos: nenhuma requisição
        # de rede sai daqui, e nada é escrito na plataforma.
        orig_get = ss._get
        self.addCleanup(lambda: setattr(ss, "_get", orig_get))

    def _mk_pick(self, pick_no, sid, roster_id, amount, first="Nome", last="Sobrenome"):
        return {"pick_no": pick_no, "round": 1, "player_id": sid,
                "roster_id": roster_id, "is_keeper": False,
                "metadata": {"amount": str(amount), "first_name": first,
                             "last_name": last, "position": "WR"}}

    def _reveal_late_drop(self, when=None):
        """Urna revelada + sync POSTERIOR → sheet DEFINITIVA."""
        from models import db, SyncLog, LateDropAudit, compute_cut_snapshot_hash
        with self.app.app_context():
            snap = [{"team_id": self.a_id, "team_name": "Time A",
                     "cut_ids": [self.zeca_id], "drop_id": self.zeca_id,
                     "drop_name": "Zeca Cinquenta", "declared": True},
                    {"team_id": self.b_id, "team_name": "Time B", "cut_ids": [],
                     "drop_id": None, "drop_name": None, "declared": True}]
            t0 = when or datetime.utcnow()
            db.session.add(LateDropAudit(
                season=self.season, declarations_json=json.dumps(snap),
                executed_at=t0, result_hash=compute_cut_snapshot_hash(snap),
                is_canonical=True))
            db.session.add(SyncLog(synced_at=t0 + timedelta(minutes=5)))
            db.session.commit()

    def _freeze(self, reason=""):
        from keeper_exclusion import freeze_exclusion_list
        with self.app.app_context():
            return freeze_exclusion_list(self.season, executed_by=self.admin_id,
                                         reason=reason)

    def _client(self):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s["_user_id"] = str(self.admin_id)
            s["_fresh"] = True
        return c

    def _preview(self, picks, dtype="auction"):
        import sync_sleeper as ss
        rosters = [{"roster_id": 1, "owner_id": "OWNER-A"},
                   {"roster_id": 2, "owner_id": "OWNER-B"}]
        draft = {"draft_id": DRAFT_ID, "status": "complete", "type": dtype,
                 "league_id": LEAGUE_ID, "season": str(self.season),
                 "settings": {"rounds": 22, "budget": 200}}

        def fake(url, timeout=None):
            if url.endswith(f"/draft/{DRAFT_ID}"):
                return draft
            if url.endswith("/picks"):
                return picks
            if url.endswith("/rosters"):
                return rosters
            return None

        ss._get = fake
        from routes.draft_import import build_preview
        with self.app.app_context():
            return build_preview(DRAFT_ID)

    def _confirm(self, picks, resolutions=None, skip_reasons=None, dtype="auction"):
        import sync_sleeper as ss
        rosters = [{"roster_id": 1, "owner_id": "OWNER-A"},
                   {"roster_id": 2, "owner_id": "OWNER-B"}]
        draft = {"draft_id": DRAFT_ID, "status": "complete", "type": dtype,
                 "league_id": LEAGUE_ID, "season": str(self.season),
                 "settings": {"rounds": 22, "budget": 200}}

        def fake(url, timeout=None):
            if url.endswith(f"/draft/{DRAFT_ID}"):
                return draft
            if url.endswith("/picks"):
                return picks
            if url.endswith("/rosters"):
                return rosters
            return None

        ss._get = fake
        return self._client().post("/api/draft_import/confirm", json={
            "draft_id": DRAFT_ID, "resolutions": resolutions or {},
            "skip_reasons": skip_reasons or {}})

    def _snapshot_jogador(self, player_id):
        """Estado byte a byte do que a porta de aquisição escreveria."""
        from models import db, Player, SalaryHistory, AuctionLog
        with self.app.app_context():
            p = db.session.get(Player, player_id)
            return {
                "salary": p.salary, "contract_year": p.contract_year,
                "contract_start_season": p.contract_start_season,
                "acquisition_type": p.acquisition_type, "team_id": p.team_id,
                "is_dropped": p.is_dropped,
                "n_salary_history": SalaryHistory.query.filter_by(
                    player_id=player_id).count(),
                "n_auction_log": AuctionLog.query.filter_by(
                    player_id=player_id).count(),
            }

    def _contagens(self):
        from models import Player, SalaryHistory, AuctionLog
        with self.app.app_context():
            return (Player.query.count(), SalaryHistory.query.count(),
                    AuctionLog.query.count())


class TestCongelamento(_Base):
    """A lista tem de ser congelada, e só num estado utilizável."""

    def test_sheet_provisoria_recusa_congelamento(self):
        res = self._freeze()
        self.assertIn("error", res)
        self.assertEqual(res["state"], "provisoria")
        self.assertIn("PROVIS", res["error"])

    def test_definitiva_congela_com_hash_e_carimbos(self):
        self._reveal_late_drop()
        res = self._freeze()
        self.assertTrue(res.get("success"), res)
        f = res["frozen"]
        self.assertEqual(f["season"], self.season)
        self.assertEqual(f["source_stage"], "definitiva")
        self.assertEqual(f["num_keepers"], 3)      # Lamar, Rams DEF, Do Time B
        self.assertTrue(f["hash"])
        self.assertTrue(f["sync_timestamp"])
        self.assertTrue(f["late_drop_executed_at"])

    def test_dropado_nao_entra_na_lista(self):
        """Zeca foi dropado na janela: ele NÃO é keeper — é o que vai a leilão."""
        self._reveal_late_drop()
        f = self._freeze()["frozen"]
        self.assertNotIn("5050", {k["sleeper_player_id"] for k in f["keepers"]})

    def test_keeper_sem_sleeper_id_recusa_congelamento(self):
        from models import db, Player
        self._reveal_late_drop()
        with self.app.app_context():
            p = db.session.get(Player, self.lamar_id)
            p.sleeper_player_id = None
            db.session.commit()
        res = self._freeze()
        self.assertEqual(res["state"], "sem_identidade")
        self.assertIn("Lamar Jackson", res["error"])

    def test_recongelar_exige_justificativa(self):
        self._reveal_late_drop()
        self.assertTrue(self._freeze().get("success"))
        segundo = self._freeze()
        self.assertEqual(segundo["state"], "ja_congelada")
        terceiro = self._freeze(reason="board recomposto")
        self.assertTrue(terceiro.get("success"))
        self.assertEqual(terceiro["frozen"]["reason"], "board recomposto")

    def test_congelada_de_outra_season_nao_serve(self):
        from keeper_exclusion import get_frozen_exclusion
        self._reveal_late_drop()
        self._freeze()
        with self.app.app_context():
            self.assertIsNotNone(get_frozen_exclusion(self.season))
            self.assertIsNone(get_frozen_exclusion(self.season + 1))


class TestBloqueioDoImport(_Base):
    """Sheet inutilizável BLOQUEIA — nunca degrada para 'ingerir tudo'."""

    def _picks_basicos(self):
        return [self._mk_pick(1, "4881", 1, 40), self._mk_pick(2, "9999", 1, 7)]

    def test_sem_lista_congelada_bloqueia_com_mensagem_propria(self):
        self._reveal_late_drop()          # DEFINITIVA, mas não congelada
        prev = self._preview(self._picks_basicos())
        self.assertIn("error", prev)
        self.assertEqual(prev["exclusion_state"], "nao_congelada")
        self.assertEqual(prev["exclusion_source"]["stage"], "definitiva")

    def test_sheet_provisoria_bloqueia_com_OUTRA_mensagem(self):
        prev = self._preview(self._picks_basicos())
        self.assertEqual(prev["exclusion_state"], "provisoria")
        self.assertIn("PROVIS", prev["error"])

    def test_mensagens_de_bloqueio_sao_distintas(self):
        prov = self._preview(self._picks_basicos())["error"]
        self._reveal_late_drop()
        nao_cong = self._preview(self._picks_basicos())["error"]
        self.assertNotEqual(prov, nao_cong)

    def test_bloqueio_nao_escreve_nada(self):
        antes = self._contagens()
        self._preview(self._picks_basicos())
        r = self._confirm(self._picks_basicos())
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self._contagens(), antes)

    def test_lista_de_outra_season_bloqueia(self):
        from models import db, set_config
        import keeper_exclusion as k
        self._reveal_late_drop()
        self._freeze()
        with self.app.app_context():
            snap = k.get_frozen_exclusion()
            snap["season"] = self.season - 1
            set_config(k.FROZEN_KEY, json.dumps(snap))
            db.session.commit()
        prev = self._preview(self._picks_basicos())
        self.assertEqual(prev["exclusion_state"], "season_errada")


class TestDiscriminadorNoImport(_Base):
    """O comportamento que o leilão de 24/08 depende."""

    def setUp(self):
        super().setUp()
        self._reveal_late_drop()
        self.assertTrue(self._freeze().get("success"))

    def test_keeper_do_mesmo_time_zero_escritas_e_estado_intacto(self):
        antes_l = self._snapshot_jogador(self.lamar_id)
        antes_c = self._contagens()
        picks = [self._mk_pick(1, "4881", 1, 40, "Lamar", "Jackson")]
        prev = self._preview(picks)
        self.assertEqual(prev["n_keepers_excluded"], 1)
        self.assertEqual(prev["n_matched"], 0)
        self.assertEqual(prev["n_unmatched"], 0)
        self.assertEqual(prev["keepers_excluded"][0]["keeper_name"], "Lamar Jackson")
        r = self._confirm(picks)
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(r.get_json()["created"], 0)
        self.assertEqual(r.get_json()["keepers_excluded"], 1)
        self.assertEqual(self._snapshot_jogador(self.lamar_id), antes_l)
        self.assertEqual(self._contagens(), antes_c)

    def test_caso_canonico_50_vira_contrato_ano_1(self):
        """Dropado na janela, recomprado pelo MESMO time por $50: valor idêntico,
        natureza diferente — o contrato antigo morreu."""
        antes = self._snapshot_jogador(self.zeca_id)
        self.assertEqual((antes["contract_year"], antes["is_dropped"]), (3, True))

        picks = [self._mk_pick(1, "5050", 1, 50, "Zeca", "Cinquenta")]
        prev = self._preview(picks)
        # `find_player_by_sleeper_id` filtra is_dropped=False → cai em unmatched, com a
        # sugestão de reativar o MESMO Player (criar novo duplicaria a linha).
        self.assertEqual(prev["n_keepers_excluded"], 0)
        u = prev["unmatched"][0]
        self.assertEqual(u["cause"], "jogador dropado no banco")
        self.assertEqual(u["suggested_player_id"], self.zeca_id)
        self.assertEqual(u["suggested_contract_year"], 3)

        r = self._confirm(picks, resolutions={"5050": str(self.zeca_id)})
        self.assertEqual(r.status_code, 200, r.get_json())
        depois = self._snapshot_jogador(self.zeca_id)
        self.assertEqual(depois["contract_year"], 1)          # antes 3 → agora 1
        self.assertEqual(depois["salary"], 50)
        self.assertFalse(depois["is_dropped"])
        self.assertEqual(depois["team_id"], self.a_id)
        self.assertEqual(depois["acquisition_type"], "auction_draft")
        self.assertEqual(depois["n_salary_history"], antes["n_salary_history"] + 1)
        self.assertEqual(depois["n_auction_log"], antes["n_auction_log"] + 1)

    def test_keeper_de_outro_time_e_pendencia_que_bloqueia(self):
        antes = self._contagens()
        picks = [self._mk_pick(1, "6790", 1, 30, "Do", "TimeB"),   # keeper do B, pick do A
                 self._mk_pick(2, "9999", 1, 5, "Novo", "Arremate")]
        prev = self._preview(picks)
        self.assertEqual(prev["n_pendencies"], 1)
        p = prev["pendencies"][0]
        self.assertEqual(p["kind"], kx.KIND_KEEPER_OTHER)
        self.assertEqual(p["sheet_team"], "Time B")
        self.assertEqual(prev["n_keepers_excluded"], 0)
        r = self._confirm(picks)
        self.assertEqual(r.status_code, 400)
        self.assertIn("pendencies", r.get_json())
        self.assertEqual(self._contagens(), antes)      # nem o arremate válido entrou

    def test_pick_sem_id_e_pendencia(self):
        picks = [self._mk_pick(1, "", 1, 5)]
        prev = self._preview(picks)
        self.assertEqual([p["kind"] for p in prev["pendencies"]], [kx.KIND_NO_ID])

    def test_roster_nao_mapeado_e_pendencia_no_auction(self):
        picks = [self._mk_pick(1, "9999", 99, 5)]
        prev = self._preview(picks)
        self.assertEqual([p["kind"] for p in prev["pendencies"]], [kx.KIND_NO_TEAM])

    def test_def_com_sigla_nao_quebra_nem_vira_falso_keeper(self):
        picks = [self._mk_pick(1, "LAR", 1, 3, "Rams", "DEF"),     # keeper do A
                 self._mk_pick(2, "SEA", 2, 4, "Hawks", "DEF")]    # arremate do B
        prev = self._preview(picks)
        self.assertEqual(prev["n_keepers_excluded"], 1)
        self.assertEqual(prev["keepers_excluded"][0]["sleeper_player_id"], "LAR")
        self.assertEqual(prev["n_pendencies"], 0)
        self.assertEqual([u["sleeper_player_id"] for u in prev["unmatched"]], ["SEA"])
        self.assertEqual(prev["unmatched"][0]["cause"], "DST/defesa (id não-numérico)")

    def test_contaminacao_arremate_readicionado_continua_sendo_ingerido(self):
        """⭐ O caso que separa a implementação correta da que INVERTE o dano.

        Depois do leilão cada owner adiciona seus arremates na liga real. Um sync devolve
        o jogador ao roster vivo — e uma lista derivada AO VIVO passaria a chamá-lo de
        keeper, excluindo da ingestão exatamente o que precisa entrar."""
        from models import db, Player, SyncLog
        with self.app.app_context():          # o owner readiciona o Zeca no Sleeper
            z = db.session.get(Player, self.zeca_id)
            z.is_dropped = False
            db.session.add(SyncLog(synced_at=datetime.utcnow() + timedelta(hours=2)))
            db.session.commit()

        # a sheet AO VIVO agora o lista como keeper...
        from keeper_exclusion import build_exclusion_source
        with self.app.app_context():
            vivo = build_exclusion_source(self.season)
        self.assertIn("5050", {k["sleeper_player_id"] for k in vivo["keepers"]})

        # ...mas a lista CONGELADA (pré-leilão) não, e é ela que manda.
        picks = [self._mk_pick(1, "5050", 1, 50, "Zeca", "Cinquenta")]
        prev = self._preview(picks)
        self.assertEqual(prev["n_keepers_excluded"], 0,
                         "arremate readicionado foi excluído — dano invertido")
        self.assertEqual(prev["n_matched"], 1)         # agora casa: não está mais dropado
        self.assertEqual(prev["matched"][0]["salary"], 50)

        r = self._confirm(picks)
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(r.get_json()["created"], 1)
        self.assertEqual(self._snapshot_jogador(self.zeca_id)["contract_year"], 1)

    def test_idempotencia_reimport_nao_cria_nada(self):
        picks = [self._mk_pick(1, "9999", 1, 7, "Novo", "Arremate")]
        r1 = self._confirm(picks, resolutions={"9999": "create"})
        self.assertEqual(r1.get_json()["created"], 1)
        depois_1 = self._contagens()
        r2 = self._confirm(picks, resolutions={"9999": "create"})
        self.assertEqual(r2.get_json()["created"], 0)
        self.assertEqual(r2.get_json()["already_imported"], 1)
        self.assertEqual(self._contagens(), depois_1)

    def test_preview_nao_escreve_nada(self):
        antes = self._contagens()
        picks = [self._mk_pick(1, "4881", 1, 40), self._mk_pick(2, "9999", 1, 7),
                 self._mk_pick(3, "6790", 1, 30), self._mk_pick(4, "", 2, 1)]
        self._preview(picks)
        self._preview(picks)
        self.assertEqual(self._contagens(), antes)

    def test_transparencia_sem_reconciliacao(self):
        """Keeper excluído aparece com nome/time/salário DA SHEET. O salário do board
        não é comparado — reconciliação foi descartada pela decisão A."""
        picks = [self._mk_pick(1, "4881", 1, 999)]     # board com valor absurdo
        prev = self._preview(picks)
        k = prev["keepers_excluded"][0]
        self.assertEqual(k["sheet_salary"], 40)
        self.assertEqual(k["amount"], "999")
        for chave in k:
            self.assertNotIn("diverg", chave)
        self.assertEqual(prev["n_pendencies"], 0)


class TestBudgetSoAremates(_Base):
    """Item 9: o alerta soft soma APENAS arremates."""

    def setUp(self):
        super().setUp()
        self._reveal_late_drop()
        self._freeze()

    def test_keeper_nao_entra_na_soma_de_arremates(self):
        """Keeper ($40) e arremate ($30) no MESMO time. A soma dos picks que entram na
        simulação de budget é a dos ARREMATES; o keeper só conta pela base (o roster
        corrente já o contém) — se entrasse nos dois, contaria DUAS vezes."""
        from types import SimpleNamespace
        from salary_engine import draft_budget
        from models import Player

        picks = [self._mk_pick(1, "4881", 1, 40, "Lamar", "Jackson"),   # keeper
                 self._mk_pick(2, "7777", 1, 30, "Livre", "Agente")]    # arremate
        prev = self._preview(picks)

        self.assertEqual(prev["n_keepers_excluded"], 1)
        soma_arremates = sum(m["salary"] for m in prev["matched"])
        self.assertEqual(soma_arremates, 30)            # o keeper NÃO está na soma
        self.assertEqual(prev["matched"][0]["matched_name"], "Livre Agente")

        with self.app.app_context():
            base_roster = Player.query.filter_by(team_id=self.a_id,
                                                 is_dropped=False).all()
            base = [SimpleNamespace(salary=p.salary, is_dropped=False)
                    for p in base_roster]
            # base de comparação = roster corrente (keepers $40 + $3 = $43)
            self.assertEqual(sum(p.salary for p in base), 43.0)
            certo = draft_budget(base + [SimpleNamespace(salary=30, is_dropped=False)])
            errado = draft_budget(base + [SimpleNamespace(salary=30, is_dropped=False),
                                          SimpleNamespace(salary=40, is_dropped=False)])
        # o número que o alerta usa é `certo`; a dupla contagem daria `errado`
        self.assertNotEqual(certo["usable_draft_budget"],
                            errado["usable_draft_budget"])
        self.assertEqual(certo["keeper_salaries"], 73)
        print(f"\n    [budget] arremates=${soma_arremates} · base(roster)=$43 "
              f"· folha simulada=${certo['keeper_salaries']} "
              f"· bid máximo=${certo['usable_draft_budget']} "
              f"(dupla contagem daria folha ${errado['keeper_salaries']})")


class TestModoLinearIntocado(_Base):
    """Restrição dura: o rookie draft na liga REAL não muda em nada."""

    def test_linear_roda_sem_lista_congelada(self):
        picks = [self._mk_pick(1, "9999", 1, 0, "Rookie", "Novo")]
        prev = self._preview(picks, dtype="linear")
        self.assertNotIn("error", prev)
        self.assertIsNone(prev["exclusion"])
        self.assertEqual(prev["n_keepers_excluded"], 0)
        self.assertEqual(prev["n_pendencies"], 0)

    def test_linear_nao_exclui_keeper(self):
        """No rookie draft um jogador do roster nos picks NÃO é excluído — o modo
        linear roda na liga real, onde não existe designação de keeper."""
        self._reveal_late_drop()
        self._freeze()
        picks = [self._mk_pick(1, "4881", 1, 0, "Lamar", "Jackson")]
        prev = self._preview(picks, dtype="linear")
        self.assertEqual(prev["n_keepers_excluded"], 0)
        self.assertEqual(prev["n_matched"], 1)

    def test_linear_mantem_roster_nao_mapeado_como_unmatched(self):
        picks = [self._mk_pick(1, "9999", 99, 0)]
        prev = self._preview(picks, dtype="linear")
        self.assertEqual(prev["n_pendencies"], 0)
        self.assertEqual(prev["unmatched"][0]["cause"],
                         "roster não mapeado a um time local")


if __name__ == "__main__":
    unittest.main(verbosity=2)
