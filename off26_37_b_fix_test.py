"""
off26_37_b_fix_test.py — o runner da correção do GRUPO B do OFF26-37 (`contract_year` 3→2 nos 11).

Molde da suíte do runner anterior (`off26_32_fix_test.py`), com o que é PRÓPRIO deste item:

  1. Configuração congelada — os 11, em DOIS lotes por canal (6 `fa_waiver` + 5 `free_agent`),
     guarda PÓS-rollover (ano 3), alvo 2, `event_ref` próprio.
  2. Casos negativos EXPLÍCITOS — o Goff (3163) e os dois do Grupo A (6803, 9486) não podem ser
     alcançados por lista, plano ou log nenhum.
  3. Núcleo puro do cruzamento ao vivo (`derive_eligible_by_roster`) — dropado no dia sai COM
     motivo; o congelado é a lista, o derivado é a elegibilidade.
  4. Núcleo puro do invariante (`invariant_diff`) — a correção mexe na CONTAGEM, nunca no dinheiro.
  5. Camada ORM sobre a porta canônica — guarda campo a campo, canal misto exigindo dois lotes,
     divergente pulado SEM abortar o lote, fora-da-lista intocado, idempotência e atomicidade.
  6. Poka-yokes da CLI — `--apply` recusa sem backup e recusa `--offline`.

⛔ Nenhum teste toca `dynasty.db`, rede ou produção: ORM em SQLite de memória.
"""

import tempfile
import unittest
from pathlib import Path

import off26_37_b_fix as fix
from contract_year_correction import EVENT_TYPE, apply_contract_year_correction

BASE_DIR = Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════════════════════
# 1. Configuração congelada do runner
# ══════════════════════════════════════════════════════════════════════════════

class TestConfiguracaoCongelada(unittest.TestCase):

    ESPERADOS = {"3451", "5870", "8259", "CHI", "CLE", "NE",
                 "421", "8154", "9225", "10213", "11539"}

    def test_sao_exatamente_11_alvos(self):
        self.assertEqual(len(fix.all_targets()), 11)
        self.assertEqual(set(fix.cohort_sids()), self.ESPERADOS)

    def test_dois_lotes_6_e_5_por_canal(self):
        self.assertEqual(len(fix.LOTS), 2)
        por_canal = {lot["canal"]: len(lot["cohort"]) for lot in fix.LOTS}
        self.assertEqual(por_canal, {"fa_waiver": 6, "free_agent": 5})

    def test_cada_lote_tem_guarda_do_proprio_canal(self):
        for lot in fix.LOTS:
            self.assertEqual(lot["expected"]["acquisition_type"], lot["canal"])

    def test_guarda_e_forte_pos_rollover(self):
        """Ano 3 (pós-rollover de 17/08), css 2025 preservado, vivo e fora de revisão."""
        for lot in fix.LOTS:
            exp = lot["expected"]
            self.assertEqual(exp["contract_year"], 3)
            self.assertEqual(exp["contract_start_season"], 2025)
            self.assertIs(exp["needs_review"], False)
            self.assertIs(exp["is_dropped"], False)
        self.assertEqual(fix.NEW_YEAR, 2)

    def test_event_ref_proprio_e_nao_colide_com_runners_anteriores(self):
        self.assertEqual(fix.EVENT_REF, "fix:off26-37-b")
        for outro in ("fix:off26-32", "fix:off26-20", "fix:wv1-coorte", "fix:wv1-coorte-b"):
            self.assertNotEqual(fix.EVENT_REF, outro)

    def test_sids_sao_strings_defs_por_sigla(self):
        """A armadilha conhecida: DEF tem sigla como id, nunca coagir a inteiro."""
        for sid in fix.cohort_sids():
            self.assertIsInstance(sid, str)
        self.assertIn("CHI", fix.cohort_sids())

    def test_chi_esta_no_lote_fa_waiver(self):
        """Divergência medida e resolvida: o handoff dizia free_agent; produção grava fa_waiver."""
        waiver = {sid for sid, _n, _o in fix.COHORT_FA_WAIVER}
        self.assertIn("CHI", waiver)

    def test_nenhum_sid_repetido_entre_os_lotes(self):
        sids = fix.cohort_sids()
        self.assertEqual(len(sids), len(set(sids)))

    def test_owner_id_registrado_por_alvo_nunca_nome_de_time(self):
        """Identidade de time é `sleeper_owner_id` — nome de time não aparece na lista."""
        for _sid, _name, owner in fix.all_targets():
            self.assertTrue(owner.isdigit())


# ══════════════════════════════════════════════════════════════════════════════
# 2. Casos negativos explícitos — quem NÃO pode ser alcançado
# ══════════════════════════════════════════════════════════════════════════════

class TestCasosNegativos(unittest.TestCase):

    def test_goff_fora_da_lista(self):
        self.assertNotIn("3163", fix.cohort_sids())

    def test_grupo_a_fora_da_lista(self):
        self.assertNotIn("6803", fix.cohort_sids())
        self.assertNotIn("9486", fix.cohort_sids())

    def test_proibidos_registrados_com_motivo(self):
        self.assertEqual(set(fix.FORBIDDEN), {"3163", "6803", "9486"})
        for sid, motivo in fix.FORBIDDEN.items():
            self.assertTrue(motivo.strip())

    def test_proibido_rosterado_ao_vivo_nao_entra_no_alvo(self):
        """Estar rosterado não basta: quem não está na lista congelada não é alcançado."""
        vivos = set(fix.cohort_sids()) | {"3163", "6803", "9486"}
        for lot in fix.LOTS:
            targets, _out = fix.derive_eligible_by_roster(lot["cohort"], vivos)
            alcancados = {sid for sid, _n, _o in targets}
            self.assertEqual(alcancados & {"3163", "6803", "9486"}, set())


# ══════════════════════════════════════════════════════════════════════════════
# 3. Núcleo puro — elegibilidade derivada ao vivo
# ══════════════════════════════════════════════════════════════════════════════

class TestElegibilidadeAoVivo(unittest.TestCase):

    COHORT = [("100", "Vivo", "1"), ("200", "Cortado", "2")]

    def test_rosterado_entra_cortado_sai_com_motivo(self):
        targets, out = fix.derive_eligible_by_roster(self.COHORT, {"100"})
        self.assertEqual([sid for sid, _n, _o in targets], ["100"])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["sleeper_player_id"], "200")
        self.assertIn("roster", out[0]["reason"])

    def test_roster_vazio_nao_produz_alvo(self):
        targets, out = fix.derive_eligible_by_roster(self.COHORT, set())
        self.assertEqual(targets, [])
        self.assertEqual(len(out), 2)

    def test_cruzamento_aceita_ids_inteiros_da_api(self):
        """A API devolve ids como string, mas o cruzamento normaliza — DEF por sigla incluída."""
        targets, _ = fix.derive_eligible_by_roster([("CHI", "Bears", "1")], {"CHI"})
        self.assertEqual(len(targets), 1)

    def test_lista_congelada_nao_muda_com_o_roster(self):
        """O roster filtra elegibilidade; jamais acrescenta alvo."""
        targets, _ = fix.derive_eligible_by_roster(self.COHORT, {"100", "200", "999"})
        self.assertEqual({sid for sid, _n, _o in targets}, {"100", "200"})


# ══════════════════════════════════════════════════════════════════════════════
# 4. Núcleo puro — invariante salarial
# ══════════════════════════════════════════════════════════════════════════════

class TestInvariantePuro(unittest.TestCase):

    def test_sem_mudanca_nao_ha_violacao(self):
        est = {"A": {"salary": 1, "projected": 1}}
        self.assertEqual(fix.invariant_diff(est, est), [])

    def test_salario_alterado_e_violacao(self):
        viol = fix.invariant_diff({"A": {"salary": 2, "projected": 2}},
                                  {"A": {"salary": 3, "projected": 2}})
        self.assertEqual(len(viol), 1)
        self.assertIn("salário", viol[0])

    def test_projecao_alterada_e_violacao(self):
        viol = fix.invariant_diff({"A": {"salary": 1, "projected": 1}},
                                  {"A": {"salary": 1, "projected": 2}})
        self.assertEqual(len(viol), 1)
        self.assertIn("projeção", viol[0])

    def test_ausente_na_releitura_e_violacao(self):
        viol = fix.invariant_diff({"A": {"salary": 1, "projected": 1}}, {})
        self.assertEqual(len(viol), 1)
        self.assertIn("ausente", viol[0])


# ══════════════════════════════════════════════════════════════════════════════
# 5. Camada ORM sobre a porta canônica
# ══════════════════════════════════════════════════════════════════════════════

class TestCorrecaoORM(unittest.TestCase):

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

        def mk(sid, name, acq, **over):
            fields = dict(sleeper_player_id=sid, name=name, position="QB",
                          team_id=self.team.id, salary=1.0, contract_year=3,
                          contract_start_season=2025, acquisition_type=acq,
                          espn_ref_value=1.0, needs_review=False, is_dropped=False)
            fields.update(over)
            return Player(**fields)

        # Os 11 alvos reais, no canal de cada lote.
        self.alvos = {}
        for lot in fix.LOTS:
            for sid, name, _o in lot["cohort"]:
                p = mk(sid, name, lot["canal"])
                self.alvos[sid] = p
        self.stafford = self.alvos["421"]
        self.stafford.salary = 2.0
        self.stafford.espn_ref_value = 4.0

        # Vizinhos que NÃO podem ser tocados.
        self.goff = mk("3163", "Jared Goff", "fa_waiver")
        self.aiyuk = mk("6803", "Brandon Aiyuk", "fa_auction", contract_year=2, salary=8.0)
        self.wicks = mk("9486", "Dontayvion Wicks", "free_agent", contract_year=2)
        db.session.add_all(list(self.alvos.values()) + [self.goff, self.aiyuk, self.wicks])
        db.session.commit()

    def _apply_lot(self, lot, ids=None):
        ids = ids if ids is not None else [sid for sid, _n, _o in lot["cohort"]]
        return apply_contract_year_correction(
            ids, expected=lot["expected"], new_year=fix.NEW_YEAR,
            reason=fix.REASON, event_ref=fix.EVENT_REF, season=2026)

    def _apply_all(self):
        return [self._apply_lot(lot) for lot in fix.LOTS]

    # ── plano: os 11 e apenas eles ────────────────────────────────────────────

    def test_os_11_sao_corrigidos_e_apenas_eles(self):
        from models import db
        results = self._apply_all()
        db.session.commit()
        aplicados = {a["sleeper_player_id"] for r in results for a in r["applied"]}
        self.assertEqual(aplicados, set(fix.cohort_sids()))
        self.assertEqual(len(aplicados), 11)
        for p in self.alvos.values():
            self.assertEqual(p.contract_year, 2)

    def test_goff_e_grupo_a_intocados(self):
        from models import db
        self._apply_all()
        db.session.commit()
        self.assertEqual(self.goff.contract_year, 3)
        self.assertEqual(self.aiyuk.contract_year, 2)
        self.assertEqual(self.aiyuk.salary, 8.0)
        self.assertEqual(self.wicks.contract_year, 2)

    def test_trilha_com_11_linhas_e_event_ref_proprio(self):
        from models import db, PlayerHistory
        self._apply_all()
        db.session.commit()
        trilha = PlayerHistory.query.filter_by(event_type=EVENT_TYPE).all()
        self.assertEqual(len(trilha), 11)
        for row in trilha:
            self.assertEqual(row.sleeper_event_ref, fix.EVENT_REF)
            self.assertIn("3 -> 2", row.notes)

    # ── canal misto: por que dois lotes ───────────────────────────────────────

    def test_guarda_de_um_canal_nao_alcanca_o_outro(self):
        """A prova da decisão 2: com guarda única, metade do grupo seria pulada."""
        from models import db
        lot_waiver = fix.LOTS[0]
        r = self._apply_lot(lot_waiver, ids=fix.cohort_sids())
        db.session.commit()
        self.assertEqual(len(r["applied"]), 6)
        self.assertEqual(len(r["skipped"]), 5)
        for s in r["skipped"]:
            self.assertIn("acquisition_type", s["reason"])

    def test_cada_lote_corrige_o_seu_tamanho(self):
        from models import db
        for lot, esperado in zip(fix.LOTS, (6, 5)):
            r = self._apply_lot(lot)
            db.session.commit()
            self.assertEqual(len(r["applied"]), esperado)

    # ── guarda: dropado, divergente, em revisão ───────────────────────────────

    def test_dropado_no_dia_e_pulado_nao_corrigido(self):
        from models import db
        self.alvos["3451"].is_dropped = True
        db.session.commit()
        r = self._apply_lot(fix.LOTS[0])
        db.session.commit()
        self.assertEqual(self.alvos["3451"].contract_year, 3)
        pulado = [s for s in r["skipped"] if s["sleeper_player_id"] == "3451"]
        self.assertEqual(len(pulado), 1)
        self.assertIn("is_dropped", pulado[0]["reason"])
        # e o lote inteiro NÃO aborta:
        self.assertEqual(len(r["applied"]), 5)

    def test_contract_year_divergente_e_pulado_com_relato_sem_abortar(self):
        from models import db
        self.alvos["5870"].contract_year = 4
        db.session.commit()
        r = self._apply_lot(fix.LOTS[0])
        db.session.commit()
        self.assertEqual(self.alvos["5870"].contract_year, 4)
        pulado = [s for s in r["skipped"] if s["sleeper_player_id"] == "5870"]
        self.assertEqual(len(pulado), 1)
        self.assertIn("contract_year", pulado[0]["reason"])
        self.assertEqual(len(r["applied"]), 5)

    def test_needs_review_e_pulado(self):
        from models import db
        self.alvos["8154"].needs_review = True
        db.session.commit()
        r = self._apply_lot(fix.LOTS[1])
        db.session.commit()
        self.assertEqual(self.alvos["8154"].contract_year, 3)
        self.assertEqual(len(r["applied"]), 4)

    def test_css_divergente_e_pulado(self):
        """`css` fora de 2025 significa outro contrato — a correção de contagem não se aplica."""
        from models import db
        self.alvos["9225"].contract_start_season = 2026
        db.session.commit()
        r = self._apply_lot(fix.LOTS[1])
        db.session.commit()
        self.assertEqual(self.alvos["9225"].contract_year, 3)
        self.assertEqual(len(r["applied"]), 4)

    # ── idempotência ──────────────────────────────────────────────────────────

    def test_reexecucao_nao_escreve_de_novo(self):
        from models import db, PlayerHistory
        self._apply_all()
        db.session.commit()
        segunda = self._apply_all()
        db.session.commit()
        aplicados = [a for r in segunda for a in r["applied"]]
        self.assertEqual(aplicados, [])
        pulados = [s for r in segunda for s in r["skipped"]]
        self.assertEqual(len(pulados), 11)
        for s in pulados:
            self.assertIn("contract_year", s["reason"])
        self.assertEqual(PlayerHistory.query.filter_by(event_type=EVENT_TYPE).count(), 11)
        for p in self.alvos.values():
            self.assertEqual(p.contract_year, 2)

    # ── invariante e campos intocados ─────────────────────────────────────────

    def test_salario_css_e_canal_intocados(self):
        from models import db
        self._apply_all()
        db.session.commit()
        for sid, p in self.alvos.items():
            self.assertEqual(p.contract_start_season, 2025)
            self.assertIn(p.acquisition_type, ("fa_waiver", "free_agent"))
        self.assertEqual(self.stafford.salary, 2.0)
        self.assertEqual(self.alvos["3451"].salary, 1.0)

    def test_invariante_projecao_do_ano_seguinte_nao_muda_em_nenhum_dos_11(self):
        """Eixo 2 da F1, medido no motor real: ano 3 e ano 2 caem ambos em valorização."""
        from models import db
        from salary_engine import project_next_salary
        antes = {sid: project_next_salary(p) for sid, p in self.alvos.items()}
        self._apply_all()
        db.session.commit()
        depois = {sid: project_next_salary(p) for sid, p in self.alvos.items()}
        self.assertEqual(antes, depois)

    def test_stafford_nao_tem_salario_tocado_aqui(self):
        """Decisão 4 do owner: o passivo $2→$3 é outra raiz e vira item próprio."""
        from models import db
        self._apply_all()
        db.session.commit()
        self.assertEqual(self.stafford.salary, 2.0)

    def test_atomicidade_rollback_desfaz_escrita_e_trilha(self):
        from models import db, PlayerHistory
        self._apply_all()
        db.session.rollback()
        self.assertEqual(self.alvos["3451"].contract_year, 3)
        self.assertEqual(PlayerHistory.query.filter_by(event_type=EVENT_TYPE).count(), 0)

    def test_fora_da_lista_com_estado_identico_nao_e_alcancado(self):
        """O Goff tem estado byte-a-byte igual aos alvos do lote waiver — e não é tocado."""
        from models import db
        self.assertEqual(
            (self.goff.contract_year, self.goff.contract_start_season,
             self.goff.acquisition_type, self.goff.is_dropped),
            (3, 2025, "fa_waiver", False))
        self._apply_all()
        db.session.commit()
        self.assertEqual(self.goff.contract_year, 3)


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
