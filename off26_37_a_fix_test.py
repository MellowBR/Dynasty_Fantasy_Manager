"""
off26_37_a_fix_test.py — o runner do GRUPO A do OFF26-37 (reset de contrato, caso 3 da régua).

Molde da suíte do runner irmão (`off26_37_b_fix_test.py`), com o que é PRÓPRIO deste item:

  1. Configuração congelada — 2 alvos, guarda por alvo (canal e salário DIFEREM entre eles),
     devido único (é o caso 3, não tabela por jogador), `event_ref` próprio e por alvo.
  2. Casos negativos EXPLÍCITOS — o Goff (3163) e os 11 do Grupo B já corrigidos.
  3. Núcleo puro — cruzamento ao vivo, plano (guarda reusada do `contract_year_correction`),
     delta de cap e a checagem de ESPN.
  4. ⛔ A ARMADILHA DO ESPN — a porta zera `espn_ref_value` quando o valor não é repassado
     (`set_espn_value` atribui ANTES de checar vazio, e o default é 0.0). Há teste que **prova a
     armadilha existindo** e teste que **falha se o runner cair nela**.
  5. Camada ORM sobre a porta canônica — os QUATRO campos, o evento próprio de timeline,
     idempotência por `event_ref`, e nada fora dos 2 alvos.
  6. Poka-yokes da CLI.

⛔ Nenhum teste toca `dynasty.db`, rede ou produção: ORM em SQLite de memória.
"""

import tempfile
import unittest
from pathlib import Path

import off26_37_a_fix as fix

BASE_DIR = Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════════════════════
# 1. Configuração congelada
# ══════════════════════════════════════════════════════════════════════════════

class TestConfiguracaoCongelada(unittest.TestCase):

    def test_sao_exatamente_2_alvos(self):
        self.assertEqual(len(fix.COHORT), 2)
        self.assertEqual(fix.cohort_sids(), ["6803", "9486"])

    def test_devido_e_o_mesmo_para_os_dois(self):
        """É o caso 3 da régua aplicado, não uma tabela por jogador."""
        self.assertEqual(fix.due_state(), {
            "contract_year": 1, "contract_start_season": 2026,
            "acquisition_type": "free_agent", "salary": 1.0})

    def test_guarda_difere_por_alvo_em_canal_e_salario(self):
        g = {t["sid"]: t["expected"] for t in fix.COHORT}
        self.assertEqual(g["6803"]["acquisition_type"], "fa_auction")
        self.assertEqual(g["6803"]["salary"], 8.0)
        self.assertEqual(g["9486"]["acquisition_type"], "free_agent")
        self.assertEqual(g["9486"]["salary"], 1.0)

    def test_guarda_exige_estado_pre_reset_em_ambos(self):
        for t in fix.COHORT:
            self.assertEqual(t["expected"]["contract_year"], 2)
            self.assertEqual(t["expected"]["contract_start_season"], 2025)
            self.assertIs(t["expected"]["needs_review"], False)
            self.assertIs(t["expected"]["is_dropped"], False)

    def test_espn_fora_da_guarda(self):
        """Import ESPN legítimo entre a medição e a execução não pode abortar o reset —
        o runner PRESERVA o que estiver lá em vez de exigir um número."""
        for t in fix.COHORT:
            self.assertNotIn("espn_ref_value", t["expected"])

    def test_event_ref_proprio_e_por_alvo(self):
        self.assertEqual(fix.EVENT_REF, "fix:off26-37-a")
        self.assertEqual(fix.target_event_ref("6803"), "fix:off26-37-a:6803")
        self.assertNotEqual(fix.target_event_ref("6803"), fix.target_event_ref("9486"))
        for outro in ("fix:off26-37-b", "fix:off26-32", "fix:off26-20", "fix:wv1-coorte"):
            self.assertNotEqual(fix.EVENT_REF, outro)

    def test_event_type_e_canonico_e_tem_rotulo_nos_templates(self):
        """⛔ Nenhum event_type novo: rótulo cru na tela exigiria tocar template (gate O7)."""
        self.assertEqual(fix.EVENT_TYPE, "free_agent")
        for tpl in ("templates/player_detail.html", "templates/salary_history.html"):
            texto = (BASE_DIR / tpl).read_text(encoding="utf-8")
            self.assertIn(f"{fix.EVENT_TYPE}:", texto)

    def test_owner_registrado_por_alvo_nunca_nome_de_time(self):
        for t in fix.COHORT:
            self.assertTrue(t["owner"].isdigit())


# ══════════════════════════════════════════════════════════════════════════════
# 2. Casos negativos explícitos
# ══════════════════════════════════════════════════════════════════════════════

class TestCasosNegativos(unittest.TestCase):

    def test_goff_e_grupo_b_fora_da_lista(self):
        for sid in ["3163"] + fix.GRUPO_B_SIDS:
            self.assertNotIn(sid, fix.cohort_sids())

    def test_proibidos_cobrem_goff_e_os_11(self):
        self.assertEqual(len(fix.FORBIDDEN), 12)
        self.assertIn("3163", fix.FORBIDDEN)
        for sid in fix.GRUPO_B_SIDS:
            self.assertIn(sid, fix.FORBIDDEN)

    def test_proibido_rosterado_ao_vivo_nao_vira_alvo(self):
        vivos = set(fix.cohort_sids()) | set(fix.FORBIDDEN)
        targets, _ = fix.derive_eligible_by_roster(fix.COHORT, vivos)
        self.assertEqual({t["sid"] for t in targets}, {"6803", "9486"})


# ══════════════════════════════════════════════════════════════════════════════
# 3. Núcleo puro
# ══════════════════════════════════════════════════════════════════════════════

class TestNucleoPuro(unittest.TestCase):

    def _estado(self, **over):
        st = {"player_id": 1, "name": "X", "team": "T", "team_owner": "1",
              "contract_year": 2, "contract_start_season": 2025,
              "acquisition_type": "fa_auction", "salary": 8.0, "espn_ref_value": 1.0,
              "needs_review": False, "is_dropped": False, "already_recorded": False}
        st.update(over)
        return st

    def test_rosterado_entra_cortado_sai_com_motivo(self):
        targets, out = fix.derive_eligible_by_roster(fix.COHORT, {"6803"})
        self.assertEqual([t["sid"] for t in targets], ["6803"])
        self.assertEqual(out[0]["sleeper_player_id"], "9486")
        self.assertIn("roster", out[0]["reason"])

    def test_plano_aceita_estado_exato(self):
        eleg, skip = fix.plan_reset([fix.COHORT[0]], {"6803": [self._estado()]})
        self.assertEqual(eleg, ["6803"])
        self.assertEqual(skip, [])

    def test_plano_pula_guarda_divergente(self):
        eleg, skip = fix.plan_reset([fix.COHORT[0]], {"6803": [self._estado(contract_year=1)]})
        self.assertEqual(eleg, [])
        self.assertIn("contract_year", skip[0]["reason"])

    def test_plano_pula_dropado(self):
        eleg, skip = fix.plan_reset([fix.COHORT[0]], {"6803": [self._estado(is_dropped=True)]})
        self.assertEqual(eleg, [])
        self.assertIn("is_dropped", skip[0]["reason"])

    def test_plano_pula_ja_registrado(self):
        eleg, skip = fix.plan_reset([fix.COHORT[0]], {"6803": [self._estado(already_recorded=True)]})
        self.assertEqual(eleg, [])
        self.assertIn("ja registrado", skip[0]["reason"])

    def test_plano_pula_ausente_e_ambiguo(self):
        eleg, skip = fix.plan_reset([fix.COHORT[0]], {})
        self.assertIn("nao encontrado", skip[0]["reason"])
        eleg, skip = fix.plan_reset([fix.COHORT[0]],
                                    {"6803": [self._estado(), self._estado()]})
        self.assertEqual(eleg, [])
        self.assertIn("ambiguo", skip[0]["reason"])

    def test_delta_de_cap_soma_por_time(self):
        states = {"6803": [self._estado(team="AlexTheDawg", salary=8.0)],
                  "9486": [self._estado(team="Haliburton Time!", salary=1.0)]}
        d = fix.cap_delta(states, ["6803", "9486"])
        self.assertEqual(d["AlexTheDawg"], -7.0)
        self.assertEqual(d["Haliburton Time!"], 0.0)

    def test_ARMADILHA_nota_longa_trunca_o_token_de_idempotencia(self):
        """Medida nesta sessão: `record_acquisition` concatena `notes + [ref:...]` e só então
        corta em 200 (`AuctionLog.notes` é String(200)). Com a REASON inteira (178) o total dá
        204 e o token some — a segunda execução não reconheceria o alvo."""
        self.assertFalse(fix.note_fits(fix.REASON, "6803"))
        self.assertTrue(fix.note_fits(fix.AUCTION_NOTE, "6803"))

    def test_nota_do_log_cabe_com_folga_nos_dois_alvos(self):
        for sid in fix.cohort_sids():
            self.assertTrue(fix.note_fits(fix.AUCTION_NOTE, sid))

    def test_espn_violations_detecta_zeramento(self):
        self.assertEqual(fix.espn_violations({"A": 1.0}, {"A": 1.0}), [])
        viol = fix.espn_violations({"A": 1.0}, {"A": 0.0})
        self.assertEqual(len(viol), 1)
        self.assertIn("NAO pode mudar", viol[0])
        self.assertEqual(len(fix.espn_violations({"A": 1.0}, {})), 1)


# ══════════════════════════════════════════════════════════════════════════════
# 4/5. Camada ORM sobre a porta canônica
# ══════════════════════════════════════════════════════════════════════════════

class TestResetORM(unittest.TestCase):

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
        from models import db, Team, Player
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.alex = Team(name="AlexTheDawg", sleeper_owner_id="698015187109773312")
        self.hali = Team(name="Haliburton Time!", sleeper_owner_id="1131747074137272320")
        db.session.add_all([self.alex, self.hali])
        db.session.commit()

        def mk(sid, name, team, **over):
            fields = dict(sleeper_player_id=sid, name=name, position="WR", team_id=team.id,
                          salary=1.0, contract_year=2, contract_start_season=2025,
                          acquisition_type="free_agent", espn_ref_value=1.0,
                          needs_review=False, is_dropped=False)
            fields.update(over)
            return Player(**fields)

        self.aiyuk = mk("6803", "Brandon Aiyuk", self.alex,
                        salary=8.0, acquisition_type="fa_auction")
        self.wicks = mk("9486", "Dontayvion Wicks", self.hali)
        # Vizinhos que NÃO podem ser tocados.
        self.goff = mk("3163", "Jared Goff", self.hali, contract_year=3,
                       acquisition_type="fa_waiver")
        self.fairbairn = mk("3451", "Ka'imi Fairbairn", self.alex, acquisition_type="fa_waiver")
        self.stafford = mk("421", "Matthew Stafford", self.hali, salary=2.0)
        db.session.add_all([self.aiyuk, self.wicks, self.goff, self.fairbairn, self.stafford])
        db.session.commit()

    def _reset(self, player, espn=None, team=None):
        """Chama a porta canônica como o runner chama — ESPN repassado por padrão."""
        from models import record_acquisition
        return record_acquisition(
            team=team or player.team_rel, acquisition_type=fix.NEW_ACQ, season=fix.NEW_SEASON,
            player=player, value_paid=0.0,
            espn_adjusted=player.espn_ref_value if espn is None else espn,
            sleeper_player_id=player.sleeper_player_id,
            event_ref=fix.target_event_ref(player.sleeper_player_id), notes=fix.AUCTION_NOTE)

    # ── os quatro campos ──────────────────────────────────────────────────────

    def test_quatro_campos_nos_devidos_em_ambos(self):
        from models import db
        for p in (self.aiyuk, self.wicks):
            self._reset(p)
        db.session.commit()
        due = fix.due_state()
        for p in (self.aiyuk, self.wicks):
            self.assertEqual(p.contract_year, due["contract_year"])
            self.assertEqual(p.contract_start_season, due["contract_start_season"])
            self.assertEqual(p.acquisition_type, due["acquisition_type"])
            self.assertEqual(float(p.salary), due["salary"])

    def test_salario_sai_1_pela_porta_sem_conta_local(self):
        """Decisão 3: contrato novo em ano 1 não valoriza — `free_agent` cai no piso."""
        from models import db
        _p, salary = self._reset(self.aiyuk)
        db.session.commit()
        self.assertEqual(int(salary), 1)
        self.assertEqual(int(self.aiyuk.salary), 1)

    def test_efeito_de_cap_menos_7_no_aiyuk_e_zero_no_wicks(self):
        from models import db
        antes = (self.aiyuk.salary, self.wicks.salary)
        for p in (self.aiyuk, self.wicks):
            self._reset(p)
        db.session.commit()
        self.assertEqual(self.aiyuk.salary - antes[0], -7.0)
        self.assertEqual(self.wicks.salary - antes[1], 0.0)

    def test_time_nao_muda(self):
        from models import db
        self._reset(self.aiyuk)
        db.session.commit()
        self.assertEqual(self.aiyuk.team_id, self.alex.id)

    # ── ⛔ a armadilha do ESPN ────────────────────────────────────────────────

    def test_ARMADILHA_a_porta_zera_espn_se_o_valor_nao_for_repassado(self):
        """Prova que a armadilha da F1 EXISTE — é o que justifica o requisito.
        `set_espn_value` atribui antes de checar vazio, e o default da porta é 0.0."""
        from models import db
        self.assertEqual(self.wicks.espn_ref_value, 1.0)
        self._reset(self.wicks, espn=0.0)          # <- o default da porta
        db.session.commit()
        self.assertEqual(self.wicks.espn_ref_value, 0.0)

    def test_runner_preserva_espn_nos_dois(self):
        """⛔ O teste que falha se o runner cair na armadilha."""
        from models import db
        antes = {p.sleeper_player_id: p.espn_ref_value for p in (self.aiyuk, self.wicks)}
        for p in (self.aiyuk, self.wicks):
            self._reset(p)
        db.session.commit()
        depois = {p.sleeper_player_id: p.espn_ref_value for p in (self.aiyuk, self.wicks)}
        self.assertEqual(antes, depois)
        self.assertEqual(depois, {"6803": 1.0, "9486": 1.0})
        self.assertEqual(fix.espn_violations(antes, depois), [])

    # ── trilha própria ────────────────────────────────────────────────────────

    def test_evento_de_timeline_por_alvo_com_ref_proprio(self):
        from models import db, PlayerHistory
        for p in (self.aiyuk, self.wicks):
            self._reset(p)
            db.session.add(PlayerHistory(
                player_id=p.id, season=fix.NEW_SEASON, team_name=p.team_rel.name,
                event_type=fix.EVENT_TYPE, salary=1, contract_year=fix.NEW_YEAR,
                notes="reset", sleeper_event_ref=fix.EVENT_REF))
        db.session.commit()
        trilha = PlayerHistory.query.filter_by(
            event_type=fix.EVENT_TYPE, sleeper_event_ref=fix.EVENT_REF).all()
        self.assertEqual(len(trilha), 2)
        self.assertEqual({t.season for t in trilha}, {2026})

    def test_ref_gravado_no_auction_log_por_alvo(self):
        from models import db, AuctionLog, acquisition_already_recorded
        self._reset(self.aiyuk)
        db.session.commit()
        self.assertTrue(acquisition_already_recorded(fix.target_event_ref("6803")))
        self.assertFalse(acquisition_already_recorded(fix.target_event_ref("9486")))
        log = AuctionLog.query.filter(AuctionLog.notes.like("%fix:off26-37-a:6803%")).all()
        self.assertEqual(len(log), 1)

    def test_salary_history_ano_1_gravado(self):
        from models import db, SalaryHistory
        self._reset(self.aiyuk)
        db.session.commit()
        sh = SalaryHistory.query.filter_by(player_id=self.aiyuk.id, season=2026).all()
        self.assertEqual(len(sh), 1)
        self.assertEqual(sh[0].contract_year, 1)
        self.assertEqual(int(sh[0].salary), 1)

    # ── idempotência ──────────────────────────────────────────────────────────

    def test_reexecucao_nao_escreve_de_novo(self):
        """Duas travas: o token por alvo no AuctionLog e a guarda (pós-reset o estado
        não casa mais o esperado)."""
        from models import db
        for p in (self.aiyuk, self.wicks):
            self._reset(p)
        db.session.commit()

        states = fix._read_states(fix.COHORT)
        eleg, skip = fix.plan_reset(fix.COHORT, states)
        self.assertEqual(eleg, [])
        self.assertEqual(len(skip), 2)
        for s in skip:
            self.assertIn("ja registrado", s["reason"])

    def test_guarda_barra_segunda_rodada_mesmo_sem_o_token(self):
        from models import db
        self._reset(self.aiyuk)
        db.session.commit()
        states = fix._read_states([fix.COHORT[0]])
        states["6803"][0]["already_recorded"] = False      # simula token perdido
        eleg, skip = fix.plan_reset([fix.COHORT[0]], states)
        self.assertEqual(eleg, [])
        self.assertIn("guarda:", skip[0]["reason"])

    # ── nada fora dos 2 ───────────────────────────────────────────────────────

    def test_goff_e_grupo_b_intocados(self):
        from models import db, PlayerHistory
        for p in (self.aiyuk, self.wicks):
            self._reset(p)
        db.session.commit()
        self.assertEqual((self.goff.contract_year, self.goff.contract_start_season,
                          self.goff.acquisition_type, self.goff.salary),
                         (3, 2025, "fa_waiver", 1.0))
        self.assertEqual((self.fairbairn.contract_year, self.fairbairn.contract_start_season),
                         (2, 2025))
        self.assertEqual((self.stafford.contract_year, self.stafford.salary), (2, 2.0))
        tocados = {ph.player_id for ph in PlayerHistory.query.all()}
        self.assertEqual(tocados & {self.goff.id, self.fairbairn.id, self.stafford.id}, set())

    def test_leitura_de_estado_alcanca_so_os_2(self):
        states = fix._read_states(fix.COHORT)
        self.assertEqual(set(states), {"6803", "9486"})

    def test_atomicidade_rollback_desfaz_tudo(self):
        from models import db, AuctionLog, SalaryHistory
        self._reset(self.aiyuk)
        db.session.rollback()
        self.assertEqual(self.aiyuk.contract_year, 2)
        self.assertEqual(self.aiyuk.salary, 8.0)
        self.assertEqual(AuctionLog.query.count(), 0)
        self.assertEqual(SalaryHistory.query.count(), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Poka-yokes da CLI
# ══════════════════════════════════════════════════════════════════════════════

class TestPokaYokesCLI(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_apply_sem_backup_recusa(self):
        self.assertEqual(fix.main(["--apply", "--db", self.tmp.name]), 1)

    def test_apply_com_offline_recusa(self):
        self.assertEqual(
            fix.main(["--apply", "--offline", "--db", self.tmp.name, "--backup", self.tmp.name]), 1)

    def test_banco_inexistente_recusa(self):
        self.assertEqual(fix.main(["--check", "--db", "/caminho/que/nao/existe.db"]), 1)

    def test_backup_ausente_recusa_escrita(self):
        self.assertFalse(fix._verify_backup(Path("/nao/existe.db"), Path(self.tmp.name)))

    def test_db_path_e_sempre_absoluto(self):
        """⛔ Caminho relativo faria o Flask-SQLAlchemy criar um banco vazio em instance/."""
        self.assertTrue(fix._db_path("dynasty.db").is_absolute())


if __name__ == "__main__":
    unittest.main(verbosity=2)
