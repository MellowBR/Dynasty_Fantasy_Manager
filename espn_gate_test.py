"""
espn_gate_test.py — o gate MECÂNICO da tabela ESPN definitiva no rollover (OFF26-25).

O passo 4 (rollover) é mutação IRREVERSÍVEL e once-only. Até 14/08/2026 ele destravava
com `espn_values_updated` — flag escrita só pelo botão manual do passo 3, que o import
ESPN nunca escreve e que **não sabe QUAL tabela está no banco**. Podia estar `true` desde
uma provisória de junho: o rollover rodava sobre ESPN ≈1.0, a valorização degradava para
`MAX(prev, floor(0.5×1)) = prev`, e a definitiva que chegasse depois não reprocessava nada
(`rollover_done` já era `"true"`). A defesa eram dois `window.confirm()` — disciplina, a
classe que o OFF26-23 rejeitou. A diagnose existia desde o OFF26-9 (✅, archive); o que
faltava era o mecanismo.

Cobertura:
1. **Núcleo puro** (`espn_gate_message`) — sem DB, sem rede: as mensagens e o motivo.
2. **Predicado** (`espn_final_import`) — ⭐ inclusive o caso que motivou o critério
   "import MAIS RECENTE" em vez de "existe algum final": final seguido de provisória na
   MESMA season (reimport para corrigir match) devolve o banco ao estado provisório.
3. **Matriz de 4 células** do destravamento (dupla condição flag × mecânica).
4. **Endpoint** — recusa 409 server-side, o once-only na frente, e o preview exibindo a
   tabela candidata.
5. **Guardas estáticas** — season nunca literal no predicado; nenhuma réplica da consulta.

Sem rede e sem tocar o `dynasty.db` (SQLite em memória).
"""

import datetime
import unittest


# ══════════════════════════════════════════════════════════════════════════════
# 1. Núcleo puro — a mensagem de recusa (sem DB, sem Flask)
# ══════════════════════════════════════════════════════════════════════════════

class _LogFake:
    """Dublê do ESPNImportLog: o núcleo puro só lê status/season/imported_at/to_dict."""

    def __init__(self, season, status, imported_at=None):
        self.season = season
        self.status = status
        self.imported_at = imported_at or datetime.datetime(2026, 6, 8, 4, 41)

    def to_dict(self):
        return {"season": self.season, "status": self.status,
                "imported_at": (self.imported_at.isoformat() + "Z"
                                if self.imported_at else None)}


class TestEspnGateMessage(unittest.TestCase):

    def _msg(self, target, log):
        from routes.offseason import espn_gate_message
        return espn_gate_message(target, log)

    def test_import_final_da_season_alvo_libera(self):
        self.assertIsNone(self._msg(2026, _LogFake(2026, "final")))

    def test_sem_import_nenhum_recusa_e_diz_o_que_falta(self):
        g = self._msg(2026, None)
        self.assertIsNotNone(g)
        self.assertEqual(g["blocked_by"], "espn_nao_definitiva")
        self.assertEqual(g["espn_gate"], "sem_import")
        self.assertEqual(g["target_season"], 2026)
        self.assertIsNone(g["import"])
        self.assertIn("2026", g["error"])
        self.assertIn("NENHUM import", g["error"])

    def test_provisorio_recusa_citando_o_status_e_a_data(self):
        """A recusa tem que dizer QUE import ela viu — senão vira 'não' sem informação."""
        g = self._msg(2026, _LogFake(2026, "provisional",
                                     datetime.datetime(2026, 7, 28, 0, 30)))
        self.assertEqual(g["espn_gate"], "provisorio")
        self.assertIn("PROVISÓRIO", g["error"])
        self.assertIn("28/07/2026", g["error"])
        # o carimbo do servidor é UTC e o preview formata no fuso do device (M18):
        # sem o rótulo as duas telas mostram datas diferentes perto da meia-noite
        self.assertIn("UTC", g["error"])
        self.assertEqual(g["import"]["status"], "provisional")

    def test_mensagem_orienta_o_caminho_da_solucao(self):
        """Decisão do owner: a recusa manda reimportar com o checkbox marcado."""
        for log in (None, _LogFake(2026, "provisional")):
            g = self._msg(2026, log)
            self.assertIn("Importação final", g["error"])
            self.assertIn("espn_import", g["error"])

    def test_mensagem_explica_o_dano_nao_so_a_regra(self):
        """Molde do OFF26-23: o poka-yoke diz POR QUE recusa (irreversível + once-only)."""
        g = self._msg(2026, None)
        self.assertIn("irreversível", g["error"])
        self.assertIn("uma vez", g["error"])

    def test_sem_data_nao_estoura(self):
        """`imported_at` nulo é possível em linha legada — degrada, não quebra."""
        log = _LogFake(2026, "provisional")
        log.imported_at = None
        self.assertIn("data desconhecida", self._msg(2026, log)["error"])


# ══════════════════════════════════════════════════════════════════════════════
# 2-4. Predicado, matriz do destravamento e endpoint — ORM em memória
# ══════════════════════════════════════════════════════════════════════════════

class _BaseORM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User
        from routes.offseason import offseason_bp
        from routes.admin import admin_bp

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
        cls.app.register_blueprint(admin_bp)

    def setUp(self):
        from models import db, Team, User, Player, set_config, DraftLotteryResult

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            team = Team(name="Cangaceiros da Colina")
            db.session.add(team)
            db.session.commit()
            admin = User(email="admin@x.com", team_id=None, is_admin=True)
            db.session.add(admin)
            db.session.commit()
            self.admin_id, self.team_id = admin.id, team.id

            # Estado análogo ao de produção às vésperas de 18/08: season 2025 fechada,
            # sorteio travado, e SÓ tabela provisória de 2026 no log.
            set_config("current_season", "2025")
            set_config("rollover_done", "false")
            set_config("espn_values_updated", "true")   # a flag manual já está ligada
            db.session.add(DraftLotteryResult(season=2026, pick_number=1,
                                              team_id=team.id, team_name=team.name,
                                              locked=True))
            db.session.add(Player(name="Keeper Qualquer", position="RB",
                                  team_id=team.id, salary=10.0, contract_year=2,
                                  acquisition_type="auction_draft",
                                  espn_ref_value=1.0, is_dropped=False))
            db.session.commit()

    def _log(self, season, status, dias_atras=0):
        from models import db, ESPNImportLog
        with self.app.app_context():
            db.session.add(ESPNImportLog(
                season=season, status=status, url_used="upload:teste.pdf",
                imported_at=datetime.datetime(2026, 8, 1) -
                datetime.timedelta(days=dias_atras)))
            db.session.commit()

    def _admin_client(self):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s["_user_id"] = str(self.admin_id)
            s["_fresh"] = True
        return c

    def _step4(self):
        from routes.offseason import _get_step_statuses
        with self.app.app_context():
            return next(s for s in _get_step_statuses() if s["num"] == 4)


class TestPredicadoImportMaisRecente(_BaseORM):
    """⭐ O critério que separa este gate de um que MENTE."""

    def _final(self, season=2026):
        from models import espn_final_import
        with self.app.app_context():
            return espn_final_import(season)

    def test_sem_nenhum_import(self):
        self.assertIsNone(self._final())

    def test_so_provisoria_nao_qualifica(self):
        self._log(2026, "provisional")
        self.assertIsNone(self._final())

    def test_final_qualifica(self):
        self._log(2026, "final")
        self.assertIsNotNone(self._final())

    def test_final_DEPOIS_de_provisoria_qualifica(self):
        """Fluxo normal do dia: provisórias antigas + a definitiva por cima."""
        self._log(2026, "provisional", dias_atras=30)
        self._log(2026, "provisional", dias_atras=10)
        self._log(2026, "final", dias_atras=0)
        self.assertIsNotNone(self._final())

    def test_provisoria_DEPOIS_de_final_NAO_qualifica(self):
        """⭐ O furo que o critério 'existe algum final' teria deixado aberto.

        Reimportar provisória para corrigir um match sobrescreve `espn_ref_value` via
        `set_espn_value` e devolve o banco ao estado provisório — enquanto a linha final
        antiga continua no log. Trava que dá falso OK é pior que trava nenhuma."""
        self._log(2026, "final", dias_atras=5)
        self._log(2026, "provisional", dias_atras=0)
        self.assertIsNone(self._final())

    def test_final_de_OUTRA_season_nao_qualifica(self):
        """Fronteira registrada no preflight: pós-rollover o default do import vira
        `current+1` = 2027; uma definitiva gravada lá não pode destravar 2026."""
        self._log(2027, "final")
        self._log(2025, "final")
        self.assertIsNone(self._final(2026))


class TestMatrizDoDestravamento(_BaseORM):
    """Dupla condição: flag manual (humana) E import final (mecânica)."""

    def _flag(self, valor):
        from models import set_config
        with self.app.app_context():
            set_config("espn_values_updated", valor)

    def test_flag_true_sem_import_final_TRAVA(self):
        """A célula que motivou o item: a flag sozinha não destrava mais."""
        self._flag("true")
        self._log(2026, "provisional")
        self.assertEqual(self._step4()["status"], "locked")

    def test_flag_true_com_import_final_LIBERA(self):
        self._flag("true")
        self._log(2026, "final")
        self.assertEqual(self._step4()["status"], "pending")

    def test_flag_false_com_import_final_TRAVA(self):
        """Decisão do owner (14/08): dupla condição — o passo 3 do painel segue intacto."""
        self._flag("false")
        self._log(2026, "final")
        self.assertEqual(self._step4()["status"], "locked")

    def test_flag_false_sem_import_final_TRAVA(self):
        self._flag("false")
        self.assertEqual(self._step4()["status"], "locked")

    def test_once_only_tem_precedencia_sobre_a_condicao_nova(self):
        """Pós-rollover a season alvo vira a seguinte, que nunca tem tabela definitiva —
        o passo tem que continuar reportando 'done', não 'locked'."""
        from models import set_config
        with self.app.app_context():
            set_config("rollover_done", "true")
        self.assertEqual(self._step4()["status"], "done")


class TestEndpointRecusaServerSide(_BaseORM):
    """O POST recusa por si — a UI esconder o botão não é o mecanismo."""

    def test_post_direto_com_so_provisoria_recusa_409(self):
        self._log(2026, "provisional")
        r = self._admin_client().post("/api/offseason/rollover", json={})
        self.assertEqual(r.status_code, 409)
        d = r.get_json()
        self.assertEqual(d["blocked_by"], "espn_nao_definitiva")
        self.assertEqual(d["espn_gate"], "provisorio")
        self.assertEqual(d["target_season"], 2026)
        self.assertIn("PROVISÓRIO", d["error"])

    def test_post_direto_sem_import_recusa_409(self):
        r = self._admin_client().post("/api/offseason/rollover", json={})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["espn_gate"], "sem_import")

    def test_recusa_NAO_muta_nada(self):
        """Recusa é recusa: nem season, nem flag, nem contrato."""
        from models import get_config, Player, db
        self._log(2026, "provisional")
        self._admin_client().post("/api/offseason/rollover", json={})
        with self.app.app_context():
            self.assertEqual(get_config("current_season"), "2025")
            self.assertEqual(get_config("rollover_done", "false"), "false")
            p = db.session.query(Player).first()
            self.assertEqual(p.contract_year, 2)
            self.assertEqual(p.salary, 10.0)

    def test_nao_existe_escape_por_force(self):
        """Decisão do owner: recusa DURA. Não há cenário legítimo de rodar sobre
        provisória — se a definitiva atrasa, adia-se o dia."""
        self._log(2026, "provisional")
        r = self._admin_client().post("/api/offseason/rollover",
                                      json={"force": True})
        self.assertEqual(r.status_code, 409)

    def test_rollover_ja_executado_recusa_por_ISSO(self):
        """Ordem das checagens: once-only na frente da condição nova."""
        from models import set_config
        with self.app.app_context():
            set_config("rollover_done", "true")
        r = self._admin_client().post("/api/offseason/rollover", json={})
        self.assertEqual(r.status_code, 400)
        self.assertIn("ja foi executado", r.get_json()["error"])

    def test_com_import_final_o_gate_do_espn_sai_da_frente(self):
        """Caminho feliz de 18/08: o gate novo não é mais o bloqueio."""
        self._log(2026, "final")
        r = self._admin_client().post("/api/offseason/rollover", json={})
        self.assertNotEqual(r.status_code, 409)
        self.assertEqual(r.get_json().get("new_season"), 2026)


class TestPreviewExibeATabela(_BaseORM):
    """O operador tem que VER com o que a mutação rodaria, antes de disparar."""

    def test_preview_recusando_mostra_provisoria(self):
        self._log(2026, "provisional")
        d = self._admin_client().get("/api/admin/rollover/preview").get_json()
        self.assertFalse(d["espn_gate_ok"])
        self.assertEqual(d["espn_import"]["status"], "provisional")
        self.assertEqual(d["espn_import"]["season"], 2026)

    def test_preview_aceito_mostra_definitiva(self):
        self._log(2026, "final")
        d = self._admin_client().get("/api/admin/rollover/preview").get_json()
        self.assertTrue(d["espn_gate_ok"])
        self.assertEqual(d["espn_import"]["status"], "final")

    def test_preview_sem_import_nao_estoura(self):
        d = self._admin_client().get("/api/admin/rollover/preview").get_json()
        self.assertFalse(d["espn_gate_ok"])
        self.assertIsNone(d["espn_import"])

    def test_preview_segue_read_only(self):
        from models import get_config
        self._log(2026, "final")
        self._admin_client().get("/api/admin/rollover/preview")
        with self.app.app_context():
            self.assertEqual(get_config("current_season"), "2025")


# ══════════════════════════════════════════════════════════════════════════════
# 5. Guardas estáticas — o que não pode voltar
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardasEstaticas(unittest.TestCase):

    def _src(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_predicado_sem_season_literal(self):
        """⛔ Nenhuma season hardcoded: a alvo é derivada de `current_season + 1`.

        Checagem por AST (não por texto) — as docstrings citam seasons de propósito,
        como exemplo do achado; o que não pode existir é o literal no CÓDIGO."""
        import ast
        import inspect
        import textwrap
        import models
        import routes.offseason as off
        for fn in (models.espn_final_import, models.latest_espn_import,
                   off.espn_gate_message):
            arvore = ast.parse(textwrap.dedent(inspect.getsource(fn)))
            anos = [n.value for n in ast.walk(arvore)
                    if isinstance(n, ast.Constant) and isinstance(n.value, int)
                    and 1900 < n.value < 2100]
            self.assertEqual(anos, [], f"{fn.__name__} tem season literal: {anos}")

    def test_sem_replica_da_consulta_de_definitiva(self):
        """OFF26-25 — a definição de 'a tabela definitiva entrou' mora em models.py.

        Eram 2 cópias inline na league.py (+ preview e gate teriam virado 3ª e 4ª).
        Guarda no molde do OFF26-16 (`TestSemReplicaDeFolha`). ⚠️ `routes/admin.py` fica
        fora da varredura de texto porque ali `status="final"` é a ESCRITA do log (o
        produtor legítimo); a garantia do preview é o teste seguinte."""
        for path in ("routes/league.py", "routes/offseason.py", "routes/salary.py"):
            src = self._src(path)
            self.assertNotIn('status="final"', src,
                             f"{path} recriou a consulta de import definitivo — "
                             f"consuma models.espn_final_import")
            self.assertNotIn("status='final'", src, path)
            self.assertNotIn("ESPNImportLog.query", src,
                             f"{path} consulta o log direto — use o helper")

    def test_preview_consome_o_helper(self):
        """O preview julga pela mesma fonte, não por consulta própria."""
        src = self._src("routes/admin.py")
        i = src.index("def rollover_preview")
        corpo = src[i:i + 1500]
        self.assertIn("espn_final_import", corpo)
        self.assertIn("latest_espn_import", corpo)
        self.assertNotIn("ESPNImportLog.query", corpo)

    def test_gate_e_consultado_pelo_endpoint_do_rollover(self):
        """Fiação: a recusa vive no POST, não só no cálculo de status do painel."""
        src = self._src("routes/offseason.py")
        i_def = src.index("def do_rollover")
        corpo = src[i_def:i_def + 2000]
        self.assertIn("espn_gate_message", corpo)
        self.assertIn("409", corpo)

    def test_flag_manual_preservada(self):
        """Decisão do owner: `espn_values_updated` continua como confirmação humana."""
        src = self._src("routes/offseason.py")
        self.assertIn('get_config("espn_values_updated"', src)
        self.assertIn("espn_updated and espn_final", src)

    def test_varredura_do_rollover_intocada(self):
        """O cálculo do rollover não é escopo deste item (restrição do prompt)."""
        src = self._src("routes/offseason.py")
        self.assertIn("Player.query.filter_by(is_dropped=False).all()", src)
        self.assertIn("apply_season_rollover(p)", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
