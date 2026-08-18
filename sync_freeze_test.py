# -*- coding: utf-8 -*-
"""
sync_freeze_test.py — OPS2: freeze administrativo do sync (janela de operação manual
no Sleeper). Lição OFF26-23: o sistema recusa; não se depende da disciplina dos admins.

O que se prova (ORM em memória, sem rede):
  * flag ativa → `run_sync` recusa ANTES de qualquer I/O (nenhum SyncLog, nenhuma
    chamada de rede) com a mensagem acionável; `_sync_trades` (a 2ª entrada de motor,
    usada direto pelo backfill) recusa pelo MESMO helper.
  * flag inativa → a guarda deixa passar (o sync alcança a camada de rede — provado
    com um sentinela no lugar do loader do pool).
  * endpoint POST /api/admin/sync_freeze liga/desliga (admin_required) e o
    POST /api/admin/sync devolve 409 com a mensagem quando congelado.
"""

import unittest
from unittest import mock


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User
        from routes.admin import admin_bp

        cls.app = Flask(__name__, template_folder="templates", static_folder="static")
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["TESTING"] = True
        cls.app.config["SECRET_KEY"] = "t"
        db.init_app(cls.app)
        lm = LoginManager()
        lm.init_app(cls.app)

        @lm.user_loader
        def load_user(uid):
            return db.session.get(User, int(uid))

        cls.app.register_blueprint(admin_bp)
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
        from flask import g
        from models import db, User
        # O ctx de app é permanente no teste ⇒ o flask-login cacheia o user em `g`
        # entre requests; sem limpar, o request seguinte recebe o objeto DETACHED
        # do setUp anterior (DetachedInstanceError em current_user.is_admin).
        if hasattr(g, "_login_user"):
            del g._login_user
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.admin = User(email="admin@x.com", is_admin=True)
        db.session.add(self.admin)
        db.session.commit()
        with self.client.session_transaction() as s:
            s["_user_id"] = str(self.admin.id)
            s["_fresh"] = True

    def _freeze(self, frozen=True):
        return self.client.post("/api/admin/sync_freeze", json={"frozen": frozen})


class TestGuardaDoMotor(_Base):
    def test_run_sync_recusa_antes_de_qualquer_io(self):
        from models import db, set_config, SyncLog
        import sync_sleeper
        set_config("sync_frozen", "true")
        db.session.commit()
        # Sentinela: se a guarda vazar, a 1ª chamada de rede estoura o teste.
        with mock.patch.object(sync_sleeper, "_load_players_db",
                               side_effect=AssertionError("guarda vazou — rede alcançada")):
            result = sync_sleeper.run_sync()
        self.assertTrue(result.get("frozen"))
        self.assertIn("congelado", result["error"].lower())
        self.assertIn("/admin", result["error"], "mensagem deve dizer ONDE destravar")
        self.assertEqual(SyncLog.query.count(), 0, "recusa não fotografa SyncLog")

    def test_sync_trades_recusa_pelo_mesmo_helper(self):
        """A 2ª entrada de motor: o backfill chama _sync_trades DIRETO."""
        from models import db, set_config
        import sync_sleeper
        set_config("sync_frozen", "true")
        db.session.commit()
        with mock.patch.object(sync_sleeper, "_get",
                               side_effect=AssertionError("guarda vazou — rede alcançada")):
            result = sync_sleeper._sync_trades("123")
        self.assertTrue(result.get("frozen"))
        self.assertEqual(result["imported"], 0)

    def test_destravado_a_guarda_deixa_passar(self):
        """Comportamento idêntico ao atual quando a flag está inativa: o sync alcança
        a camada de rede (sentinela) — a guarda não intercepta nada."""
        import sync_sleeper

        class Reached(Exception):
            pass

        with mock.patch.object(sync_sleeper, "_load_players_db", side_effect=Reached):
            with self.assertRaises(Reached):
                sync_sleeper.run_sync()


class TestToggleEEndpoint(_Base):
    def test_toggle_liga_e_desliga(self):
        from models import get_config
        r = self._freeze(True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(get_config("sync_frozen", "false"), "true")
        r = self._freeze(False)
        self.assertTrue(r.get_json()["ok"])
        self.assertEqual(get_config("sync_frozen", "false"), "false")

    def test_porta_do_botao_devolve_409_com_mensagem(self):
        self._freeze(True)
        r = self.client.post("/api/admin/sync")
        self.assertEqual(r.status_code, 409)
        d = r.get_json()
        self.assertFalse(d["success"])
        self.assertIn("congelado", d["error"].lower())

    def test_toggle_exige_admin(self):
        from models import db, User
        comum = User(email="owner@x.com", is_admin=False)
        db.session.add(comum)
        db.session.commit()
        with self.client.session_transaction() as s:
            s["_user_id"] = str(comum.id)
        r = self._freeze(True)
        self.assertEqual(r.status_code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
