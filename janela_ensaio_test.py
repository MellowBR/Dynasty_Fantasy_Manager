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
