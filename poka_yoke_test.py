"""
poka_yoke_test.py — os 3 poka-yokes da ordem da intertemporada (OFF26-23).

A F1 (10/08/2026) provou que a ordem segura da semana 17→24/08 era disciplina
operacional, não invariante. Diretriz do owner: o sistema recusa a ordem errada.
Os 3 pontos de não-retorno, agora cercados:

1. **Import do draft antes do rollover** → `rollover_order_gate` (draft_import) recusa
   importar classe de season futura (a varredura do rollover é cega a contrato
   recém-aberto — todo rookie viraria Ano 2).
2. **Passo 5 antes do import** → o toggle "Rookie Draft Done" recusa (409) quando não há
   registro de rookie_draft na season; cenário legítimo passa por `force` explícito.
3. **Clear sem undo** → `clear_rookie_espn_store` grava backup automático antes de
   apagar (padrão F13: dirname(DYNASTY_DB), carimbo dentro do arquivo) e
   `restore_rookie_espn_backup` reidrata pela porta única.

Sem rede, sem tocar o `dynasty.db` (SQLite em memória + tmpdir p/ backups).
"""

import json
import os
import tempfile
import unittest


# ══════════════════════════════════════════════════════════════════════════════
# 1. Gate do import (núcleo puro — sem DB, sem rede)
# ══════════════════════════════════════════════════════════════════════════════

class TestRolloverOrderGate(unittest.TestCase):

    def _gate(self, *a):
        from routes.draft_import import rollover_order_gate
        return rollover_order_gate(*a)

    def test_classe_de_season_futura_bloqueia(self):
        """O ponto de não-retorno nº 1: draft 2026 com Manager em 2025 → recusa."""
        g = self._gate(True, 2026, 2025)
        self.assertIsNotNone(g)
        self.assertEqual(g["order_gate"], "rollover_pendente")
        self.assertIn("Season Rollover", g["error"])
        self.assertIn("Ano 2", g["error"])          # a mensagem diz o dano, não só "não"

    def test_ordem_correta_passa(self):
        """Rollover feito (current avançou p/ 2026) → import da classe liberado."""
        self.assertIsNone(self._gate(True, 2026, 2026))

    def test_import_historico_segue_permitido(self):
        """Comportamento antigo preservado: draft de season passada não é bloqueado."""
        self.assertIsNone(self._gate(True, 2025, 2026))

    def test_modo_auction_fora_do_gate(self):
        """Auction é transitivamente gateado (sheet congelada ← urna ← rollover)."""
        self.assertIsNone(self._gate(False, 2026, 2025))


# ══════════════════════════════════════════════════════════════════════════════
# 2. Gate do passo 5 + 3. clear com rede — endpoint + ORM em memória
# ══════════════════════════════════════════════════════════════════════════════

class TestPasso5EClear(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User
        from routes.offseason import offseason_bp

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

    def setUp(self):
        from models import db, Team, User, set_config, upsert_rookie_espn
        # backups do clear vão para um tmpdir isolado (padrão F13: dirname(DYNASTY_DB))
        self.tmpdir = tempfile.mkdtemp(prefix="poka_yoke_")
        self._old_db_env = os.environ.get("DYNASTY_DB")
        os.environ["DYNASTY_DB"] = os.path.join(self.tmpdir, "dynasty.db")

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            team = Team(name="Time A")
            db.session.add(team)
            db.session.commit()
            admin = User(email="admin@x.com", team_id=None, is_admin=True)
            db.session.add(admin)
            db.session.commit()
            self.admin_id, self.team_id = admin.id, team.id
            set_config("current_season", "2026")
            set_config("rookie_draft_done", "false")
            # 2 linhas no store: uma da classe, uma de veterano do Top-300
            upsert_rookie_espn(2026, "9901", "Rookie Estrela", "RB", "DAL",
                               espn_raw=46.0, espn_adjusted=55.2, in_class=True)
            upsert_rookie_espn(2026, "9902", "Veterano Top300", "WR", "KC",
                               espn_raw=10.0, espn_adjusted=12.0)
            db.session.commit()

    def tearDown(self):
        if self._old_db_env is None:
            os.environ.pop("DYNASTY_DB", None)
        else:
            os.environ["DYNASTY_DB"] = self._old_db_env

    def _admin(self):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s["_user_id"] = str(self.admin_id)
            s["_fresh"] = True
        return c

    def _add_rookie_log(self):
        from models import db, AuctionLog
        with self.app.app_context():
            db.session.add(AuctionLog(season=2026, team_id=self.team_id,
                                      player_name="Rookie Estrela",
                                      entry_type="rookie_draft", round_num=1))
            db.session.commit()

    def _backups(self):
        return [f for f in os.listdir(self.tmpdir)
                if f.startswith("rookie_espn_backup_")]

    # ── gate do passo 5 ──────────────────────────────────────────────────────
    def test_passo5_sem_import_recusa_com_force_disponivel(self):
        """O ponto de não-retorno nº 2: sem registro de rookie_draft na season → 409."""
        r = self._admin().post("/api/offseason/rookie_draft_done", json={})
        self.assertEqual(r.status_code, 409)
        d = r.get_json()
        self.assertTrue(d["requires_force"])
        self.assertEqual(d["order_gate"], "import_pendente")
        self.assertIn("$1", d["error"])              # a mensagem diz o dano
        # nada mudou: flag intacta, store intacto
        from models import get_config, RookieEspnValue
        with self.app.app_context():
            self.assertEqual(get_config("rookie_draft_done", "false"), "false")
            self.assertEqual(RookieEspnValue.query.count(), 2)
        self.assertEqual(self._backups(), [])

    def test_passo5_com_import_passa(self):
        """Caminho feliz intocado: import registrado → marca e o clear roda."""
        self._add_rookie_log()
        r = self._admin().post("/api/offseason/rookie_draft_done", json={})
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertTrue(d["ok"])
        self.assertEqual(d["rookie_store_cleared"], 2)
        self.assertTrue(d["rookie_store_backup"])    # a rede existe e é reportada

    def test_passo5_force_e_confirmacao_explicita(self):
        """Cenário legítimo de pular o import: só com force — nunca silêncio."""
        r = self._admin().post("/api/offseason/rookie_draft_done",
                               json={"force": True})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_undo_nao_passa_pelo_gate(self):
        """Reverter não exige import (o gate é só do sentido marcar)."""
        from models import set_config, db
        with self.app.app_context():
            set_config("rookie_draft_done", "true")
            db.session.commit()
        r = self._admin().post("/api/offseason/rookie_draft_done",
                               json={"undo": True})
        self.assertEqual(r.status_code, 200)

    # ── clear com rede ───────────────────────────────────────────────────────
    def test_clear_grava_backup_antes_de_apagar(self):
        """O ponto de não-retorno nº 3: o backup nasce ANTES do delete, verificável."""
        from models import db, clear_rookie_espn_store, RookieEspnValue
        with self.app.app_context():
            n, path = clear_rookie_espn_store()
            db.session.commit()
            self.assertEqual(n, 2)
            self.assertTrue(os.path.isfile(path))
            self.assertIn(self.tmpdir, os.path.abspath(path))   # volume "persistente"
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload["count"], 2)
            self.assertIn("cleared_at", payload)                 # carimbo DENTRO (F13)
            sids = {r["sleeper_player_id"] for r in payload["rows"]}
            self.assertEqual(sids, {"9901", "9902"})
            self.assertEqual(RookieEspnValue.query.count(), 0)   # apagou de verdade

    def test_backup_e_restauravel_pela_porta_unica(self):
        """'Sem undo' deixou de ser verdade: restore reidrata valores E membership."""
        from models import (db, clear_rookie_espn_store, restore_rookie_espn_backup,
                            RookieEspnValue)
        with self.app.app_context():
            _, path = clear_rookie_espn_store()
            db.session.commit()
            n = restore_rookie_espn_backup(path)
            db.session.commit()
            self.assertEqual(n, 2)
            rows = {r.sleeper_player_id: r for r in RookieEspnValue.query.all()}
            self.assertEqual(rows["9901"].espn_adjusted, 55.2)
            self.assertTrue(rows["9901"].in_class)               # membership volta
            self.assertFalse(rows["9902"].in_class)

    def test_clear_vazio_nao_cria_arquivo(self):
        from models import db, clear_rookie_espn_store
        with self.app.app_context():
            clear_rookie_espn_store()
            db.session.commit()
            n, path = clear_rookie_espn_store()   # segunda vez: nada a apagar
            self.assertEqual((n, path), (0, None))
        self.assertEqual(len(self._backups()), 1)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Guardas estáticas — o que NÃO pode regredir
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardasEstaticas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from pathlib import Path
        base = Path(__file__).resolve().parent
        cls.off = (base / "routes" / "offseason.py").read_text(encoding="utf-8")
        cls.di = (base / "routes" / "draft_import.py").read_text(encoding="utf-8")

    def test_once_only_do_rollover_nao_regrediu(self):
        """A reexecução segue bloqueada — o gate novo não mexeu no antigo."""
        self.assertIn("Rollover ja foi executado", self.off)

    def test_gate_roda_no_preview_e_por_tabela_no_confirm(self):
        """confirm() reusa build_preview — o gate no preview bloqueia os dois."""
        corpo = self.di.split("def build_preview")[1].split("\ndef ")[0]
        self.assertIn("rollover_order_gate", corpo)

    def test_varredura_do_rollover_intocada(self):
        """A restrição do prompt: o gate cerca a ordem, não muda o que o passo faz."""
        self.assertIn('Player.query.filter_by(is_dropped=False)', self.off)

    def test_gate_do_passo5_nunca_silencioso(self):
        """force existe, mas a recusa padrão é 409 com o dano explicado."""
        bloco = self.off.split("def toggle_rookie_draft")[1].split("\n@")[0]
        self.assertIn("requires_force", bloco)
        self.assertIn("409", bloco)


if __name__ == "__main__":
    unittest.main(verbosity=2)
