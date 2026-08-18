"""
off26_32_fix_test.py — o runner da correção OFF26-32 (contract_year 3→2 nos `fa_auction` vivos).

Molde da suíte do runner anterior (`contract_year_correction_test.py`), com o que é PRÓPRIO
deste item:

  1. Núcleo puro da derivação (`derive_targets`) — o congelado é o CENSO, não a lista de alvos;
     quem está rosterado é decisão do Sleeper, lida no dia. Sem rede, sem DB.
  2. Núcleo puro do invariante (`invariant_diff`) — a correção mexe na CONTAGEM, nunca no dinheiro.
  3. Configuração do runner — censo dos 24, guarda PÓS-rollover (ano 3), alvo 2, event_ref próprio.
  4. Camada ORM sobre a porta canônica — guarda campo a campo, fora-da-lista intocado,
     idempotência, atomicidade, e o invariante medido de verdade (salário + projeção).
  5. Poka-yokes da CLI — `--apply` recusa sem backup e recusa `--offline`.
  6. Carona UX13 — o event_type desta correção tem rótulo nos DOIS templates da timeline.

⛔ Nenhum teste toca `dynasty.db`, rede ou produção: ORM em SQLite de memória e leitura de texto
dos templates.
"""

import re
import tempfile
import unittest
from pathlib import Path

import off26_32_fix as fix
from contract_year_correction import EVENT_TYPE, apply_contract_year_correction

BASE_DIR = Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════════════════════
# 1. Núcleo puro — derivação da lista do dia
# ══════════════════════════════════════════════════════════════════════════════

class TestDerivacaoPura(unittest.TestCase):

    CENSO = [("100", "Rosterado"), ("200", "Dropado"), ("300", "Excluído")]
    EXCL = {"300": "dropado em 2026"}

    def test_entra_quem_esta_rosterado(self):
        targets, out = fix.derive_targets(self.CENSO, {"100"}, self.EXCL)
        self.assertEqual(targets, [("100", "Rosterado")])
        self.assertEqual({o["sleeper_player_id"] for o in out}, {"200", "300"})

    def test_nao_rosterado_sai_com_motivo(self):
        _, out = fix.derive_targets(self.CENSO, {"100"}, self.EXCL)
        motivo = next(o["reason"] for o in out if o["sleeper_player_id"] == "200")
        self.assertIn("roster", motivo)

    def test_excluido_sai_mesmo_rosterado_ao_vivo(self):
        """O caso do re-add: dropado em 2026 que volta a um roster tem contrato NOVO —
        corrigir a contagem do contrato MORTO produziria o híbrido do OFF26-31."""
        targets, out = fix.derive_targets(self.CENSO, {"100", "300"}, self.EXCL)
        self.assertEqual([sid for sid, _ in targets], ["100"])
        motivo = next(o["reason"] for o in out if o["sleeper_player_id"] == "300")
        self.assertIn("contrato NOVO", motivo)

    def test_roster_vazio_nao_produz_alvo(self):
        targets, out = fix.derive_targets(self.CENSO, set(), self.EXCL)
        self.assertEqual(targets, [])
        self.assertEqual(len(out), 3)

    def test_ids_do_sleeper_normalizados_como_string(self):
        """A API pode devolver id numérico; o censo é string. Nunca coagir a inteiro
        (a armadilha das DEFs, que usam sigla)."""
        targets, _ = fix.derive_targets([("100", "X")], {100}, {})
        self.assertEqual(targets, [("100", "X")])

    def test_ordem_do_censo_e_preservada(self):
        censo = [("3", "C"), ("1", "A"), ("2", "B")]
        targets, _ = fix.derive_targets(censo, {"1", "2", "3"}, {})
        self.assertEqual([s for s, _ in targets], ["3", "1", "2"])


# ══════════════════════════════════════════════════════════════════════════════
# 2. Núcleo puro — invariante salarial
# ══════════════════════════════════════════════════════════════════════════════

class TestInvariantePuro(unittest.TestCase):

    def test_estado_identico_nao_viola(self):
        st = {"a": {"salary": 4, "projected": 6}}
        self.assertEqual(fix.invariant_diff(st, dict(st)), [])

    def test_salario_alterado_e_violacao(self):
        viol = fix.invariant_diff({"a": {"salary": 4, "projected": 6}},
                                  {"a": {"salary": 5, "projected": 6}})
        self.assertEqual(len(viol), 1)
        self.assertIn("salário", viol[0])

    def test_projecao_alterada_e_violacao(self):
        viol = fix.invariant_diff({"a": {"salary": 4, "projected": 6}},
                                  {"a": {"salary": 4, "projected": 9}})
        self.assertEqual(len(viol), 1)
        self.assertIn("projeção", viol[0])

    def test_ausente_na_releitura_e_violacao(self):
        viol = fix.invariant_diff({"a": {"salary": 4, "projected": 6}}, {})
        self.assertEqual(len(viol), 1)
        self.assertIn("ausente", viol[0])


# ══════════════════════════════════════════════════════════════════════════════
# 3. Configuração do runner
# ══════════════════════════════════════════════════════════════════════════════

class TestConfiguracaoDoRunner(unittest.TestCase):

    def test_censo_tem_os_24_do_off26_20(self):
        self.assertEqual(len(fix.CENSUS), 24)
        self.assertEqual(len({sid for sid, _ in fix.CENSUS}), 24, "sids duplicados no censo")

    def test_todo_sid_do_censo_e_string(self):
        for sid, _ in fix.CENSUS:
            self.assertIsInstance(sid, str)

    def test_caso_ancora_esta_no_censo(self):
        self.assertIn(("11560", "Caleb Williams"), fix.CENSUS)

    def test_excluidos_sao_subconjunto_do_censo(self):
        self.assertTrue(set(fix.DROPPED_2026) <= {sid for sid, _ in fix.CENSUS})

    def test_guarda_e_o_estado_pos_rollover(self):
        """A diferença para o runner do OFF26-20: lá a guarda esperava o estado PRÉ-rollover."""
        self.assertEqual(fix.EXPECTED["contract_year"], 3)
        self.assertEqual(fix.EXPECTED["contract_start_season"], 2025)
        self.assertEqual(fix.EXPECTED["acquisition_type"], "fa_auction")
        self.assertIs(fix.EXPECTED["needs_review"], False)
        self.assertIs(fix.EXPECTED["is_dropped"], False)

    def test_alvo_e_ano_2(self):
        self.assertEqual(fix.NEW_YEAR, 2)

    def test_event_ref_proprio_e_distinto_do_off26_20(self):
        """A UNIQUE da trilha é por (player, season, tipo, time, ref) — ref repetido
        colidiria com a correção anterior."""
        import off26_20_fix
        self.assertEqual(fix.EVENT_REF, "fix:off26-32")
        self.assertNotEqual(fix.EVENT_REF, off26_20_fix.EVENT_REF)

    def test_reason_cita_a_aprovacao_do_owner(self):
        self.assertIn("18/08/2026", fix.REASON)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Camada ORM — a correção sobre a porta canônica
# ══════════════════════════════════════════════════════════════════════════════

class TestCorrecaoORM(unittest.TestCase):
    """SQLite em memória (molde cap_regua_test) — nunca toca o dynasty.db."""

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
        self.team = Team(name="Cangaceiros da Colina")
        db.session.add(self.team)
        db.session.commit()

        def fa(sid, name, **over):
            fields = dict(sleeper_player_id=sid, name=name, position="QB",
                          team_id=self.team.id, salary=4.0, contract_year=3,
                          contract_start_season=2025, acquisition_type="fa_auction",
                          espn_ref_value=12.0, needs_review=False, is_dropped=False)
            fields.update(over)
            return Player(**fields)

        self.caleb = fa("11560", "Caleb Williams")
        self.mahomes = fa("4046", "Patrick Mahomes", salary=9.0, espn_ref_value=9.6)
        self.em_revisao = fa("9999", "Em Revisão", needs_review=True)
        self.ja_corrigido = fa("8888", "Já Corrigido", contract_year=2)
        self.outro_canal = fa("7777", "Outro Canal", acquisition_type="free_agent")
        # fa_auction idêntico aos alvos, mas FORA da lista — não pode ser tocado.
        self.fora_da_lista = fa("6666", "Fora da Lista")
        db.session.add_all([self.caleb, self.mahomes, self.em_revisao,
                            self.ja_corrigido, self.outro_canal, self.fora_da_lista])
        db.session.commit()

    def _apply(self, ids):
        return apply_contract_year_correction(
            ids, expected=fix.EXPECTED, new_year=fix.NEW_YEAR,
            reason=fix.REASON, event_ref=fix.EVENT_REF, season=2026)

    def test_corrige_3_para_2_e_grava_trilha(self):
        from models import db, PlayerHistory
        result = self._apply(["11560"])
        db.session.commit()
        self.assertEqual(len(result["applied"]), 1)
        self.assertEqual(self.caleb.contract_year, 2)
        trilha = PlayerHistory.query.filter_by(event_type=EVENT_TYPE).all()
        self.assertEqual(len(trilha), 1)
        self.assertIn("3 -> 2", trilha[0].notes)
        self.assertEqual(trilha[0].sleeper_event_ref, fix.EVENT_REF)

    def test_salario_e_inicio_de_contrato_intocados(self):
        from models import db
        self._apply(["11560"])
        db.session.commit()
        self.assertEqual(self.caleb.salary, 4.0)
        self.assertEqual(self.caleb.contract_start_season, 2025)
        self.assertEqual(self.caleb.acquisition_type, "fa_auction")

    def test_invariante_projecao_do_ano_seguinte_nao_muda(self):
        """O ponto 3 do parecer F1, medido: `fa_auction` cai em valorização em ano 3 E em
        ano 4 — o ramo de waiver ano 2 (0,8×ESPN) não existe para este canal."""
        from models import db
        from salary_engine import project_next_salary, waiver_year2_salary
        antes = project_next_salary(self.caleb)
        self._apply(["11560"])
        db.session.commit()
        self.assertEqual(project_next_salary(self.caleb), antes)
        self.assertNotEqual(antes, waiver_year2_salary(self.caleb.espn_ref_value),
                            "se coincidirem, o teste deixa de provar que o ramo não dispara")

    def test_guarda_pula_quem_diverge_sem_forcar(self):
        from models import db
        result = self._apply(["9999", "8888", "7777"])
        db.session.commit()
        self.assertEqual(result["applied"], [])
        self.assertEqual(len(result["skipped"]), 3)
        self.assertEqual(self.em_revisao.contract_year, 3)
        self.assertEqual(self.ja_corrigido.contract_year, 2)
        self.assertEqual(self.outro_canal.contract_year, 3)

    def test_quem_esta_fora_da_lista_nao_e_tocado(self):
        from models import db
        self._apply(["11560", "4046"])
        db.session.commit()
        self.assertEqual(self.fora_da_lista.contract_year, 3)

    def test_rollback_desfaz_escrita_e_trilha_juntas(self):
        from models import db, PlayerHistory, Player
        self._apply(["11560"])
        db.session.rollback()
        self.assertEqual(db.session.get(Player, self.caleb.id).contract_year, 3)
        self.assertEqual(PlayerHistory.query.filter_by(event_type=EVENT_TYPE).count(), 0)

    def test_idempotencia_segunda_passada_pula_tudo(self):
        from models import db
        self._apply(["11560", "4046"])
        db.session.commit()
        segunda = self._apply(["11560", "4046"])
        self.assertEqual(segunda["applied"], [])
        self.assertEqual(len(segunda["skipped"]), 2)
        for s in segunda["skipped"]:
            self.assertIn("contract_year=2", s["reason"])

    def test_lista_completa_do_ensaio(self):
        from models import db
        result = self._apply(["11560", "4046"])
        db.session.commit()
        self.assertEqual({a["sleeper_player_id"] for a in result["applied"]}, {"11560", "4046"})
        self.assertTrue(all(a["old"] == 3 and a["new"] == 2 for a in result["applied"]))


# ══════════════════════════════════════════════════════════════════════════════
# 5. Poka-yokes da CLI
# ══════════════════════════════════════════════════════════════════════════════

class TestPokaYokesCLI(unittest.TestCase):
    """Nenhum destes chega a abrir o banco ou a rede — todos recusam antes."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.write(b"")
        self.tmp.close()

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_apply_sem_backup_recusa(self):
        self.assertEqual(fix.main(["--apply", "--db", self.tmp.name]), 1)

    def test_apply_com_offline_recusa(self):
        """A lista só é válida cruzada ao vivo: o banco pode estar congelado (OPS2) ou
        atrasado, e o Sleeper é a autoridade sobre membership."""
        self.assertEqual(
            fix.main(["--apply", "--offline", "--db", self.tmp.name, "--backup", self.tmp.name]), 1)

    def test_banco_inexistente_recusa(self):
        self.assertEqual(fix.main(["--check", "--db", "/caminho/que/nao/existe.db"]), 1)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Carona UX13 — rótulo da timeline
# ══════════════════════════════════════════════════════════════════════════════

class TestRotulosDaTimelineUX13(unittest.TestCase):
    """O event_type desta correção aparecerá ~20 vezes na timeline. Os dois dicionários
    são réplica declarada (comentário no próprio template) — o teste cobre os dois."""

    TEMPLATES = ["templates/player_detail.html", "templates/salary_history.html"]

    def _dict_keys(self, texto: str, nome: str) -> set:
        bloco = re.search(rf"const {nome} = {{(.*?)}};", texto, re.S)
        self.assertIsNotNone(bloco, f"{nome} não encontrado")
        return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", bloco.group(1), re.M))

    def test_event_type_da_correcao_tem_rotulo_e_badge_nos_dois(self):
        for tpl in self.TEMPLATES:
            texto = (BASE_DIR / tpl).read_text(encoding="utf-8")
            self.assertIn(EVENT_TYPE, self._dict_keys(texto, "EVENT_LABELS"), tpl)
            self.assertIn(EVENT_TYPE, self._dict_keys(texto, "EVENT_BADGES"), tpl)

    def test_review_approved_tambem_coberto(self):
        """O outro event_type que o código escreve e a timeline exibia cru (M2)."""
        for tpl in self.TEMPLATES:
            texto = (BASE_DIR / tpl).read_text(encoding="utf-8")
            self.assertIn("review_approved", self._dict_keys(texto, "EVENT_LABELS"), tpl)

    def test_labels_e_badges_cobrem_as_mesmas_chaves(self):
        for tpl in self.TEMPLATES:
            texto = (BASE_DIR / tpl).read_text(encoding="utf-8")
            self.assertEqual(self._dict_keys(texto, "EVENT_LABELS"),
                             self._dict_keys(texto, "EVENT_BADGES"), tpl)

    def test_replica_declarada_segue_sincronizada(self):
        chaves = [self._dict_keys((BASE_DIR / t).read_text(encoding="utf-8"), "EVENT_LABELS")
                  for t in self.TEMPLATES]
        self.assertEqual(chaves[0], chaves[1],
                         "os dois dicionários são cópia declarada — divergiram")

    def test_rotulo_em_pt_br_nao_e_a_string_crua(self):
        texto = (BASE_DIR / self.TEMPLATES[0]).read_text(encoding="utf-8")
        rotulo = re.search(rf"{EVENT_TYPE}:\s*'([^']+)'", texto).group(1)
        self.assertNotEqual(rotulo, EVENT_TYPE)
        self.assertIn("ontrato", rotulo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
