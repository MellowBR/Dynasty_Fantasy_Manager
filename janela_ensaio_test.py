"""
janela_ensaio_test.py — OFF26-1-ENSAIO: o desfazer do ciclo de ensaio da janela selada.

O achado bloqueante da Etapa 0: NÃO existia caminho de desfazer — e o estado "travada"
da janela É a existência do snapshot canônico (`CutWindowAudit.is_canonical`), então um
ensaio sem reset deixaria a janela REAL de 20/08 bloqueada (o /open recusa com 409).

Cobre: o núcleo `stage_reset`/`window_report` (SQLite em memória, molde cap_regua_test),
a propriedade crítica (pós-reset a janela reabre), o escopo por season, a atomicidade
(sem commit — rollback desfaz), e a presença do rótulo de ensaio nas telas.
"""

import json
import unittest
from pathlib import Path

from ensaio_janela_selada import stage_reset, window_report, BANNER_KEY, WINDOW_KEY

BASE_DIR = Path(__file__).resolve().parent


class TestResetDoEnsaio(unittest.TestCase):
    """SQLite em memória — nunca toca o dynasty.db."""

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
        from models import db, Team, CutDeclaration, CutWindowAudit, set_config
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.t1 = Team(name="Cangaceiros da Colina")
        self.t2 = Team(name="Time do Michel")
        db.session.add_all([self.t1, self.t2])
        db.session.commit()
        # Ciclo de ensaio completo encenado: janela aberta → 2 declarações →
        # lock (canônico) → replace (superseded + novo canônico) → banner ligado.
        set_config(WINDOW_KEY, "true")
        set_config(BANNER_KEY, "true")
        db.session.add_all([
            CutDeclaration(season=2026, team_id=self.t1.id,
                           cut_ids_json="[101]", declared=True),
            CutDeclaration(season=2026, team_id=self.t2.id,
                           cut_ids_json="[202]", declared=True),
        ])
        old = CutWindowAudit(season=2026, declarations_json="[]",
                             result_hash="a" * 64, is_canonical=False)
        db.session.add(old)
        db.session.commit()
        db.session.add(CutWindowAudit(season=2026, declarations_json="[]",
                                      result_hash="b" * 64, is_canonical=True,
                                      previous_audit_id=old.id, reason="ensaio"))
        # Sujeira de OUTRA season — o reset não pode alcançá-la.
        db.session.add(CutDeclaration(season=2025, team_id=self.t1.id,
                                      cut_ids_json="[9]", declared=True))
        db.session.add(CutWindowAudit(season=2025, declarations_json="[]",
                                      result_hash="c" * 64, is_canonical=True))
        db.session.commit()

    def test_report_ve_o_ciclo(self):
        r = window_report(2026)
        self.assertEqual(r["state"], "locked")
        self.assertEqual(len(r["declarations"]), 2)
        self.assertEqual(len(r["audits"]), 2)
        self.assertEqual(r["banner_flag"], "true")

    def test_report_nao_expoe_conteudo_de_declaracao(self):
        """D6 vale até no relatório do operador: contagens, nunca cut_ids/nomes."""
        dump = json.dumps(window_report(2026))
        self.assertNotIn("101", dump)
        self.assertNotIn("cut_ids", dump)

    def test_reset_zera_a_season_e_fecha_tudo(self):
        from models import db
        staged = stage_reset(2026)
        db.session.commit()
        self.assertEqual(staged, {"deleted_declarations": 2, "deleted_audits": 2})
        r = window_report(2026)
        self.assertEqual(r["state"], "closed")
        self.assertEqual(r["declarations"], [])
        self.assertEqual(r["audits"], [])
        self.assertEqual(r["window_flag"], "false")
        self.assertEqual(r["banner_flag"], "false")

    def test_propriedade_critica_pos_reset_a_janela_reabre(self):
        """O motivo de o reset existir: snapshot canônico de ensaio bloquearia o
        /open da janela REAL de 20/08. Pós-reset, _window_locked cai."""
        from models import db
        from routes.cuts import _window_locked, _window_state
        self.assertTrue(_window_locked(2026))          # ensaio travou
        stage_reset(2026)
        db.session.commit()
        self.assertFalse(_window_locked(2026))          # destravou
        self.assertEqual(_window_state(2026), "closed")  # e pode abrir de novo

    def test_escopo_por_season(self):
        """A season 2025 (trilha real de outro ano) fica intacta."""
        from models import db, CutDeclaration, CutWindowAudit
        stage_reset(2026)
        db.session.commit()
        self.assertEqual(CutDeclaration.query.filter_by(season=2025).count(), 1)
        self.assertEqual(CutWindowAudit.query.filter_by(season=2025).count(), 1)

    def test_sem_commit_rollback_desfaz(self):
        """stage_reset não comita — molde da porta do FIX: o chamador decide."""
        from models import db
        stage_reset(2026)
        db.session.rollback()
        r = window_report(2026)
        self.assertEqual(r["state"], "locked")
        self.assertEqual(len(r["declarations"]), 2)
        self.assertEqual(len(r["audits"]), 2)

    def test_reset_idempotente(self):
        from models import db
        stage_reset(2026)
        db.session.commit()
        staged2 = stage_reset(2026)
        db.session.commit()
        self.assertEqual(staged2, {"deleted_declarations": 0, "deleted_audits": 0})
        self.assertEqual(window_report(2026)["state"], "closed")


class TestDbPathResolucao(unittest.TestCase):
    """POSENSAIO (A): --db relativo abria o banco errado — o exists() checava o cwd,
    mas a URI do SQLAlchemy resolvia contra OUTRO diretório e o SQLite criava um banco
    VAZIO em silêncio ("no such table"). Agora tudo resolve para absoluto ANTES."""

    def test_relativo_resolve_contra_o_cwd(self):
        from ensaio_janela_selada import _db_path
        p = _db_path("ensaio_local.db")
        self.assertTrue(p.is_absolute())
        self.assertEqual(p, Path.cwd() / "ensaio_local.db")

    def test_absoluto_passa_intacto(self):
        from ensaio_janela_selada import _db_path
        alvo = (BASE_DIR / "dynasty.db").resolve()
        self.assertEqual(_db_path(str(alvo)), alvo)

    def test_env_relativa_tambem_resolve(self):
        import os
        from ensaio_janela_selada import _db_path
        old = os.environ.get("DYNASTY_DB")
        os.environ["DYNASTY_DB"] = "rel_env.db"
        try:
            self.assertTrue(_db_path().is_absolute())
        finally:
            if old is None:
                os.environ.pop("DYNASTY_DB", None)
            else:
                os.environ["DYNASTY_DB"] = old

    def test_banco_inexistente_e_recusado(self):
        """Criar banco novo nunca é intenção de quem passa --db — recusa clara, exit 1."""
        from ensaio_janela_selada import main
        rc = main(["--status", "--db", "nao_existe_mesmo_12345.db"])
        self.assertEqual(rc, 1)

    def test_reset_sem_backup_recusado_antes_de_qualquer_escrita(self):
        from ensaio_janela_selada import main
        rc = main(["--reset", "--db", str(BASE_DIR / "dynasty.db")])
        self.assertEqual(rc, 1)


class TestHierarquiaOwnerAdmin(unittest.TestCase):
    """POSENSAIO (B): declaração pessoal do owner (cortes OU manter-todos) prevalece —
    o suprimento do admin sobre time que declarou pessoalmente é RECUSADO (recusa seca),
    sem vazar conteúdo. Time silencioso ou suprido por admin: funciona como antes.

    Estrutura deliberada: NENHUM app context fica empurrado durante os requests — o
    flask_login cacheia o usuário em `g` (escopo de app context), e um contexto externo
    persistente faria todos os requests herdarem o usuário do primeiro."""

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User
        from routes.cuts import cuts_bp

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

    def setUp(self):
        from models import db, Team, Player, User, set_config
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            t_owner = Team(name="Time do Owner")
            t_silent = Team(name="Time Silencioso")
            db.session.add_all([t_owner, t_silent])
            db.session.commit()
            admin = User(email="admin@x.com", team_id=None, is_admin=True)
            owner = User(email="owner@x.com", team_id=t_owner.id, is_admin=False)
            jogador = Player(name="Kicker Ficticio", position="K", salary=1.0,
                             team_id=t_owner.id)
            db.session.add_all([admin, owner, jogador])
            set_config("cuts_window_open", "true")
            db.session.commit()
            # IDs como ints puros — nada de instância ORM viva fora de contexto.
            self.admin_id, self.owner_id = admin.id, owner.id
            self.t_owner_id, self.t_silent_id = t_owner.id, t_silent.id
            self.jogador_id = jogador.id

    def _as(self, user_id):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s["_user_id"] = str(user_id)
            s["_fresh"] = True
        return c

    def test_manter_todos_explicito_declara_e_conta(self):
        c = self._as(self.owner_id)
        r = c.post("/api/cuts/declaration", json={"cut_ids": []})
        self.assertTrue(r.get_json()["success"])
        state = c.get("/api/cuts/state").get_json()
        self.assertEqual(state["declared_count"], 1)   # manter-todos conta no N/12
        self.assertTrue(state["i_declared"])

    def test_admin_nao_sobrescreve_manter_todos_do_owner(self):
        self._as(self.owner_id).post("/api/cuts/declaration", json={"cut_ids": []})
        r = self._as(self.admin_id).post("/api/cuts/admin/declare",
                                         json={"team_id": self.t_owner_id, "cut_ids": []})
        self.assertEqual(r.status_code, 409)
        self.assertIn("declarou pessoalmente", r.get_json()["error"])

    def test_admin_nao_sobrescreve_cortes_do_owner_e_nao_vaza_conteudo(self):
        self._as(self.owner_id).post("/api/cuts/declaration",
                                     json={"cut_ids": [self.jogador_id]})
        r = self._as(self.admin_id).post("/api/cuts/admin/declare",
                                         json={"team_id": self.t_owner_id, "cut_ids": []})
        self.assertEqual(r.status_code, 409)
        corpo = r.get_data(as_text=True)
        self.assertNotIn("Kicker", corpo)      # nem o nome do jogador declarado
        self.assertNotIn("cut_ids", corpo)     # nem a estrutura da declaração
        self.assertIn("selado", corpo)         # a resposta afirma o sigilo

    def test_admin_supre_time_silencioso_como_antes(self):
        r = self._as(self.admin_id).post("/api/cuts/admin/declare",
                                         json={"team_id": self.t_silent_id, "cut_ids": []})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["success"])

    def test_admin_reajusta_o_proprio_suprimento(self):
        """Suprimento sobre suprimento anterior do admin segue permitido (não é do owner)."""
        a = self._as(self.admin_id)
        a.post("/api/cuts/admin/declare", json={"team_id": self.t_silent_id, "cut_ids": []})
        r = a.post("/api/cuts/admin/declare", json={"team_id": self.t_silent_id, "cut_ids": []})
        self.assertEqual(r.status_code, 200)

    def test_owner_sobrescreve_suprimento_do_admin(self):
        """A hierarquia no outro sentido: o dono sempre pode retomar a própria declaração."""
        r = self._as(self.admin_id).post("/api/cuts/admin/declare",
                                         json={"team_id": self.t_owner_id, "cut_ids": []})
        self.assertEqual(r.status_code, 200)   # suprimento sobre silêncio: permitido
        r = self._as(self.owner_id).post("/api/cuts/declaration",
                                         json={"cut_ids": [self.jogador_id]})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["success"])

    def test_sheet_distingue_os_tres_manteve_todos(self):
        """3º status (POSENSAIO): 'Declarou (manteve todos)' ≠ 'Declarou' ≠ 'Default'."""
        self._as(self.owner_id).post("/api/cuts/declaration", json={"cut_ids": []})
        self._as(self.admin_id).post("/api/cuts/admin/declare",
                                     json={"team_id": self.t_silent_id, "cut_ids": []})

        from routes.cuts import _declared_status, _DECL_STATUS_LABEL
        from models import get_current_season
        with self.app.app_context():
            season = get_current_season()
            s_owner_empty = {"team_id": self.t_owner_id, "declared": True, "cut_ids": []}
            s_owner_cuts = {"team_id": self.t_owner_id, "declared": True,
                            "cut_ids": [self.jogador_id]}
            s_silent = {"team_id": self.t_silent_id, "declared": False, "cut_ids": []}
            s_admin = {"team_id": self.t_silent_id, "declared": True, "cut_ids": []}

            self.assertEqual(_declared_status(s_owner_empty, season), "owner_kept_all")
            self.assertEqual(_declared_status(s_owner_cuts, season), "owner_declared")
            self.assertEqual(_declared_status(s_silent, season), "default_zero")
            self.assertEqual(_declared_status(s_admin, season), "admin_supplied")
        self.assertEqual(_DECL_STATUS_LABEL["owner_kept_all"], "Declarou (manteve todos)")


class TestRotuloDeEnsaio(unittest.TestCase):
    """O banner existe nas duas telas e as rotas passam a flag (guarda de fonte)."""

    def test_templates_tem_o_banner(self):
        for tpl in ("cuts.html", "keeper_sheet.html"):
            src = (BASE_DIR / "templates" / tpl).read_text(encoding="utf-8")
            self.assertIn("ensaio_banner", src, tpl)
            self.assertIn("ENSAIO", src, tpl)

    def test_rotas_passam_a_flag(self):
        src = (BASE_DIR / "routes" / "cuts.py").read_text(encoding="utf-8")
        self.assertEqual(src.count('get_config("cuts_ensaio_banner"'), 2,
                         "as DUAS páginas (cuts + keeper_sheet) devem ler a flag")

    def test_banner_key_consistente(self):
        """A chave do script é a mesma que as rotas leem."""
        self.assertEqual(BANNER_KEY, "cuts_ensaio_banner")


if __name__ == "__main__":
    unittest.main(verbosity=2)
