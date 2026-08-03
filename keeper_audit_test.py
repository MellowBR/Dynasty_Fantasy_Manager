"""
keeper_audit_test.py — testes do núcleo puro do OFF26-4 (F2).

Roda sem Flask, sem banco e sem rede: `audit()` é função pura, e as fixtures são
dado congelado (`keeper_audit_fixtures.py` — material de teste, NÃO a sheet real).

    python keeper_audit_test.py

A pergunta que estes testes respondem não é "a auditoria acusa?" — é "a auditoria
acusa EXATAMENTE o que existe?". Uma auditoria que inventa uma quarta divergência
é tão inútil quanto uma que perde a primeira: nos dois casos o gate deixa de ser
confiável na véspera do leilão.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import keeper_audit_fixtures as fx
from keeper_audit import (
    audit, CLASS_LABEL, CLS_MISSING, CLS_SALARY, CLS_WRONG_TEAM, CLS_EXTRA,
    ST_OK, ST_UNPOPULATED, ST_NO_COLUMN,
)


def _findings(report):
    return [f for t in report["teams"] for f in t["findings"]]


def _team(report, name):
    return next(t for t in report["teams"] if t["team_name"] == name)


def _team_of_column(report, roster_id):
    return next(t for t in report["teams"] if t["roster_id"] == roster_id)


class TestFixtureACoerente(unittest.TestCase):
    """Board e sheet batendo: a auditoria não pode achar NADA."""

    def setUp(self):
        self.rep = audit(fx.BOARD_A, fx.SHEET_A)

    def test_zero_divergencias(self):
        self.assertEqual(self.rep["summary"]["divergences"], 0, _findings(self.rep))

    def test_tres_populados_nove_nao_populados(self):
        s = self.rep["summary"]
        self.assertEqual((s["teams"], s["populated"], s["unpopulated"]), (12, 3, 9))
        self.assertEqual(s["no_column"], 0)
        self.assertEqual(s["orphan_columns"], 0)

    def test_nao_populado_nao_e_divergencia(self):
        """D4: estado próprio. Um time sem coluna populada tem keepers na sheet e
        nenhum no board — e mesmo assim NÃO gera 'keeper ausente'."""
        for t in self.rep["teams"]:
            if t["state"] == ST_UNPOPULATED:
                self.assertGreater(t["num_keepers_sheet"], 0)
                self.assertEqual(t["findings"], [])

    def test_totais_do_board_conferem(self):
        for rid, total in (("3", 148), ("4", 95), ("5", 60)):
            t = _team_of_column(self.rep, rid)
            self.assertEqual(t["state"], ST_OK)
            self.assertEqual(t["board_total"], total)
            self.assertEqual(t["sheet_total"], total)

    def test_amount_string_nao_gera_falso_positivo(self):
        """`metadata.amount` vem como STRING; sem coerção, todo keeper viraria
        'salário divergente' e a fixture A acusaria 24 erros."""
        self.assertTrue(all(isinstance(d["amount"], str)
                            for d in fx.BOARD_A["designations"]))
        self.assertEqual([f for f in _findings(self.rep)
                          if f["class"] == CLS_SALARY], [])

    def test_def_com_id_sigla_casa(self):
        """`player_id` de DEF é sigla ('LAR'), não número. Coerção a int quebraria."""
        siglas = [d["sleeper_player_id"] for d in fx.BOARD_A["designations"]
                  if not d["sleeper_player_id"].isdigit()]
        self.assertEqual(sorted(siglas), ["HOU", "LAR"])
        self.assertEqual([f for f in _findings(self.rep)
                          if f["sleeper_player_id"] in siglas], [])

    def test_verdict_bloqueada_so_por_nao_populados(self):
        """Zero divergências NÃO libera: 9 times sem board = keepers expostos."""
        self.assertEqual(self.rep["verdict"], "bloqueada")
        self.assertEqual(len(self.rep["blocking_reasons"]), 1)
        self.assertIn("não populado", self.rep["blocking_reasons"][0])


class TestFixtureBDivergente(unittest.TestCase):
    """Três erros plantados: exatamente três achados, um por classe."""

    def setUp(self):
        self.rep = audit(fx.BOARD_A, fx.SHEET_B)
        self.f = _findings(self.rep)

    def test_exatamente_tres(self):
        self.assertEqual(self.rep["summary"]["divergences"], 3,
                         [(x["class"], x["player"]) for x in self.f])

    def test_uma_de_cada_classe(self):
        self.assertEqual(sorted(x["class"] for x in self.f),
                         sorted([CLS_SALARY, CLS_WRONG_TEAM, CLS_EXTRA]))

    def test_salario_divergente_com_os_dois_numeros(self):
        f = next(x for x in self.f if x["class"] == CLS_SALARY)
        self.assertEqual(f["sleeper_player_id"], fx._MAHOMES)
        self.assertEqual((f["sheet_salary"], f["board_amount"]), (17, 22))

    def test_fora_da_sheet(self):
        f = next(x for x in self.f if x["class"] == CLS_EXTRA)
        self.assertEqual(f["sleeper_player_id"], fx._IRVING)
        self.assertEqual(f["board_amount"], 10)

    def test_time_errado_conta_UMA_vez(self):
        """O cruzamento é UM erro. Contá-lo como 'ausente lá' + 'sobrando cá' daria
        a quarta divergência que denuncia auditoria que inventa."""
        f = [x for x in self.f if x["class"] == CLS_WRONG_TEAM]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["sleeper_player_id"], fx._LONDON)
        self.assertEqual(f[0]["board_roster_id"], "3")
        self.assertEqual([x for x in self.f
                          if x["sleeper_player_id"] == fx._LONDON
                          and x["class"] != CLS_WRONG_TEAM], [])

    def test_nenhum_bloqueante_entre_os_tres(self):
        """Nenhum dos três erros é da classe 1 — o veredito segue bloqueado, mas
        pelos não populados, não por exposição de keeper."""
        self.assertEqual(self.rep["summary"]["blocking_findings"], 0)

    def test_achados_atribuidos_aos_times_certos(self):
        """Os três erros caem em DOIS times: a coluna 4 acumula o 'fora da sheet' e
        o 'time errado' (foi para a sheet dela que o London mudou); a coluna 5 fica
        com o salário. Os outros dez seguem limpos."""
        por_time = {t["roster_id"]: [f["class"] for f in t["findings"]]
                    for t in self.rep["teams"] if t["findings"]}
        self.assertEqual({k: sorted(v) for k, v in por_time.items()},
                         {"4": sorted([CLS_EXTRA, CLS_WRONG_TEAM]),
                          "5": [CLS_SALARY]})

    def test_pior_primeiro(self):
        """O gate se lê de cima: times com achado vêm antes dos sem achado."""
        com = [i for i, t in enumerate(self.rep["teams"]) if t["findings"]]
        self.assertEqual(com, [0, 1])


class TestClasseBloqueante(unittest.TestCase):
    """Classe 1 — a que não é escolha de desenho."""

    def setUp(self):
        self.rep = audit(fx.BOARD_C, fx.SHEET_C)

    def test_acusa_e_marca_bloqueante(self):
        f = _findings(self.rep)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["class"], CLS_MISSING)
        self.assertEqual(f[0]["severity"], "bloqueante")
        self.assertTrue(f[0]["blocking"])
        self.assertEqual(f[0]["sleeper_player_id"], "9509")

    def test_distinguivel_das_demais(self):
        self.assertEqual(self.rep["summary"]["blocking_findings"], 1)
        self.assertEqual(self.rep["verdict"], "bloqueada")
        self.assertIn("expostos ao leilão", self.rep["blocking_reasons"][0])


class TestColunaSemOwner(unittest.TestCase):
    """Terreno de 03/08: convite não aceito → coluna sem dono."""

    def setUp(self):
        self.rep = audit(fx.BOARD_SEM_OWNER, fx.SHEET_SEM_OWNER)

    def test_coluna_nao_atribuivel_fica_no_balde_proprio(self):
        self.assertEqual(len(self.rep["orphan_columns"]), 1)
        orf = self.rep["orphan_columns"][0]
        self.assertEqual((orf["roster_id"], orf["num_designations"]), ("2", 1))

    def test_designacao_orfa_nao_vira_divergencia_de_time(self):
        """Não é 'fora da sheet' de ninguém: a coluna não pertence a time nenhum."""
        self.assertEqual(self.rep["summary"]["divergences"], 0)

    def test_time_sem_coluna_tem_estado_proprio(self):
        t = _team(self.rep, "Sem coluna")
        self.assertEqual(t["state"], ST_NO_COLUMN)
        self.assertIsNone(t["roster_id"])
        self.assertEqual(t["findings"], [])

    def test_os_dois_bloqueiam_a_abertura(self):
        self.assertEqual(self.rep["verdict"], "bloqueada")
        motivos = " ".join(self.rep["blocking_reasons"])
        self.assertIn("sem coluna atribuída", motivos)
        self.assertIn("não atribuível", motivos)


class TestKeeperSemSleeperId(unittest.TestCase):
    """Identidade não resolvível é limite de insumo, não divergência — e jamais
    se cai para nome (incidente 'Brown')."""

    def setUp(self):
        self.rep = audit(fx.BOARD_C, fx.SHEET_SEM_SID)

    def test_nao_acusa_ausencia(self):
        self.assertEqual(self.rep["summary"]["divergences"], 0)

    def test_conta_e_avisa(self):
        self.assertEqual(self.rep["summary"]["unresolved_keepers"], 2)
        t = self.rep["teams"][0]
        self.assertEqual(len(t["warnings"]), 2)
        self.assertIn("Brown", " ".join(t["warnings"]))

    def test_auditoria_incompleta_bloqueia(self):
        self.assertEqual(self.rep["verdict"], "bloqueada")
        self.assertIn("auditoria incompleta", " ".join(self.rep["blocking_reasons"]))


class TestInsumoFaltando(unittest.TestCase):
    """Sem sheet ou sem board o relatório DIZ isso — não acusa 12 times."""

    def test_janela_nao_revelada(self):
        rep = audit(fx.BOARD_A, {"revealed": False, "season": 2026})
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["teams"], [])
        self.assertEqual(rep["summary"]["divergences"], 0)
        self.assertIn("não foi revelada", rep["reason"])

    def test_sheet_inexistente(self):
        rep = audit(fx.BOARD_A, None)
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["verdict"], "bloqueada")

    def test_board_com_erro(self):
        rep = audit({"error": "Draft 123 não respondeu"}, fx.SHEET_A)
        self.assertFalse(rep["ok"])
        self.assertIn("não respondeu", rep["reason"])
        self.assertEqual(rep["teams"], [])


class TestMetaDaLigaIndependeDaSheet(unittest.TestCase):
    """O buraco que o smoke de produção expôs: sem sheet, o bloco de meta some — e
    com ele a única prova de que o serviço ALCANÇA a API do Sleeper de onde roda.
    A leitura da liga não pode depender da existência da sheet."""

    def test_meta_preenchida_com_sheet_ausente(self):
        rep = audit(fx.BOARD_A, {"revealed": False, "season": 2026})
        self.assertFalse(rep["ok"])                      # o bloqueio continua
        lg = rep["league"]
        self.assertTrue(lg["available"])                 # ...e a meta vem junto
        self.assertEqual(lg["draft_id"], "1389755381567213568")
        self.assertEqual(lg["draft_status"], "pre_draft")
        self.assertEqual(lg["rounds"], 22)               # do DRAFT, não da liga
        self.assertEqual(lg["num_designations"], 24)

    def test_contagem_de_donos_vem_da_leitura(self):
        rep = audit(fx.BOARD_SEM_OWNER, {"revealed": False, "season": 2026})
        lg = rep["league"]
        self.assertEqual((lg["columns_total"], lg["columns_with_owner"],
                          lg["columns_without_owner"]), (2, 1, 1))

    def test_erro_de_liga_e_estado_proprio_do_bloco(self):
        """Falha ao ler a liga não se confunde com falta de sheet: o veredito segue
        dizendo o que falta de insumo, e o bloco diz o que houve com a liga."""
        rep = audit({"error": "Liga 999 não respondeu"},
                    {"revealed": False, "season": 2026})
        self.assertIn("não foi revelada", rep["reason"])       # motivo do bloqueio
        self.assertFalse(rep["league"]["available"])
        self.assertEqual(rep["league"]["error"], "Liga 999 não respondeu")

    def test_liga_nao_configurada_nao_finge_disponibilidade(self):
        rep = audit(None, {"revealed": False, "season": 2026})
        self.assertFalse(rep["league"]["available"])
        self.assertIsNone(rep["league"]["draft_id"])
        self.assertEqual(rep["league"]["num_designations"], 0)

    def test_meta_tambem_presente_no_relatorio_completo(self):
        lg = audit(fx.BOARD_A, fx.SHEET_A)["league"]
        self.assertTrue(lg["available"])
        self.assertEqual(lg["num_designations"], 24)


class TestClassesDeclaradas(unittest.TestCase):

    def test_sao_quatro_e_slot_errado_nao_existe(self):
        """A classe 'slot errado' foi medida como NÃO auditável (pick_no/round não
        indicam vaga) e não precisa existir — a atribuição é automática por posição."""
        self.assertEqual(len(CLASS_LABEL), 4)
        self.assertNotIn("slot", " ".join(CLASS_LABEL).lower())

    def test_estados_nao_sao_classes(self):
        self.assertNotIn(ST_OK, CLASS_LABEL)
        self.assertNotIn(ST_UNPOPULATED, CLASS_LABEL)
        self.assertNotIn(ST_NO_COLUMN, CLASS_LABEL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
