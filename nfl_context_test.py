# -*- coding: utf-8 -*-
"""
nfl_context_test.py — O2 Batch 1: núcleo puro do contexto NFL (idade + depth chart).

Exercita SÓ as funções puras (build_slim_index / compute_age / build_depth_chart /
assemble_context) — sem DB, sem rede, sem filesystem, no padrão do salary_engine_test.

Rodar: python nfl_context_test.py
"""

import unittest
from datetime import date

from nfl_context import (assemble_context, build_depth_chart, build_slim_index,
                         compute_age, normalize_position)

# Pool sintético mínimo — formas reais observadas no cache de 31/07/2026:
# WRs do mesmo time com/sem depth_chart_order, DEF como sigla sem campos, lixo estrutural.
POOL = {
    "1001": {"full_name": "Alpha Um", "team": "CAR", "position": "WR",
             "depth_chart_position": "LWR", "depth_chart_order": 1,
             "birth_date": "1997-04-14", "age": 29, "years_exp": 8},
    "1002": {"full_name": "Bravo Dois", "team": "CAR", "position": "WR",
             "depth_chart_position": "RWR", "depth_chart_order": 2,
             "birth_date": "2000-01-31", "age": 26},
    "1003": {"full_name": "Charlie Sem Ordem", "team": "CAR", "position": "WR",
             "depth_chart_position": None, "depth_chart_order": None,
             "birth_date": None, "age": None},
    "1004": {"full_name": "Delta Outro Time", "team": "BUF", "position": "WR",
             "depth_chart_position": "LWR", "depth_chart_order": 1,
             "birth_date": "1998-12-30", "age": 27},
    "1005": {"full_name": "Echo Outra Pos", "team": "CAR", "position": "RB",
             "depth_chart_position": "RB", "depth_chart_order": 1,
             "birth_date": "1999-06-15", "age": 27},
    # Homônimo em outro time (precedente Brown / os dois DJ Moore do pool real)
    "1006": {"full_name": "Alpha Um", "team": "NYJ", "position": "CB",
             "depth_chart_position": None, "depth_chart_order": None,
             "birth_date": "1987-03-22", "age": 39},
    # Empate de order — desempata por nome
    "1007": {"full_name": "Aaa Empate", "team": "CAR", "position": "WR",
             "depth_chart_position": "SWR", "depth_chart_order": 2,
             "birth_date": "2001-07-01", "age": 25},
    # DEF: sigla como sid, sem campos de depth chart nem birth_date
    "CAR": {"full_name": None, "team": "CAR", "position": "DEF",
            "depth_chart_position": None, "depth_chart_order": None,
            "birth_date": None, "age": None},
    # Lixo estrutural do pool real
    "junk1": "not-a-dict",
    "junk2": {"team": "CAR"},  # sem position → fora do índice
}

TODAY = date(2026, 8, 8)


class TestBuildSlimIndex(unittest.TestCase):
    def test_filtra_lixo_e_preserva_campos(self):
        idx = build_slim_index(POOL)
        self.assertNotIn("junk1", idx)
        self.assertNotIn("junk2", idx)
        self.assertIn("1001", idx)
        self.assertIn("CAR", idx)  # DEF entra no índice (degrada no chart, não aqui)
        self.assertEqual(idx["1001"]["depth_chart_order"], 1)
        self.assertNotIn("years_exp", idx["1001"])  # índice é ENXUTO

    def test_pool_vazio_ou_none(self):
        self.assertEqual(build_slim_index({}), {})
        self.assertEqual(build_slim_index(None), {})


class TestComputeAge(unittest.TestCase):
    def test_aniversario_ja_passou_no_ano(self):
        self.assertEqual(compute_age("1997-04-14", TODAY), 29)

    def test_aniversario_ainda_nao_chegou(self):
        self.assertEqual(compute_age("1998-12-30", TODAY), 27)

    def test_aniversario_hoje_conta(self):
        self.assertEqual(compute_age("2000-08-08", TODAY), 26)

    def test_ausente_ou_ilegivel_vira_none_sem_levantar(self):
        self.assertIsNone(compute_age(None, TODAY))
        self.assertIsNone(compute_age("", TODAY))
        self.assertIsNone(compute_age("31/12/1999", TODAY))
        self.assertIsNone(compute_age("garbage", TODAY))


class TestBuildDepthChart(unittest.TestCase):
    def setUp(self):
        self.idx = build_slim_index(POOL)

    def test_mesmo_time_mesma_posicao_ordenado(self):
        chart = build_depth_chart(self.idx, "CAR", "WR")
        self.assertEqual([r["name"] for r in chart],
                         ["Alpha Um", "Aaa Empate", "Bravo Dois"])  # order 1, 2, 2 (nome)
        self.assertEqual([r["order"] for r in chart], [1, 2, 2])

    def test_sem_ordem_fica_de_fora(self):
        chart = build_depth_chart(self.idx, "CAR", "WR")
        self.assertNotIn("Charlie Sem Ordem", [r["name"] for r in chart])

    def test_outro_time_e_outra_posicao_nao_entram(self):
        names = [r["name"] for r in build_depth_chart(self.idx, "CAR", "WR")]
        self.assertNotIn("Delta Outro Time", names)
        self.assertNotIn("Echo Outra Pos", names)

    def test_is_self_por_sid_nunca_por_nome(self):
        # Os dois "Alpha Um" (1001 CAR/WR e 1006 NYJ/CB): marcar 1001 não marca o homônimo
        chart = build_depth_chart(self.idx, "CAR", "WR", self_sid="1001")
        flags = {r["sid"]: r["is_self"] for r in chart}
        self.assertTrue(flags["1001"])
        self.assertFalse(any(f for s, f in flags.items() if s != "1001"))

    def test_def_degrada_para_vazio(self):
        self.assertEqual(build_depth_chart(self.idx, "CAR", "DEF"), [])

    def test_normalizacao_dst(self):
        self.assertEqual(normalize_position("DST"), "DEF")
        self.assertEqual(normalize_position("D/ST"), "DEF")
        # chart pedido como DST cai na mesma resposta (vazia) do DEF
        self.assertEqual(build_depth_chart(self.idx, "CAR", "DST"), [])

    def test_team_ou_position_ausentes(self):
        self.assertEqual(build_depth_chart(self.idx, None, "WR"), [])
        self.assertEqual(build_depth_chart(self.idx, "CAR", None), [])
        self.assertEqual(build_depth_chart({}, "CAR", "WR"), [])


class TestAssembleContext(unittest.TestCase):
    def setUp(self):
        self.idx = build_slim_index(POOL)

    def test_jogador_completo(self):
        ctx = assemble_context(self.idx, "1001", TODAY)
        self.assertEqual(ctx["age"], 29)
        self.assertEqual(ctx["team"], "CAR")
        self.assertEqual(ctx["position"], "WR")
        self.assertEqual(len(ctx["depth_chart"]), 3)
        self.assertTrue(ctx["in_chart"])

    def test_chart_usa_time_do_POOL_do_proprio_jogador(self):
        ctx = assemble_context(self.idx, "1004", TODAY)
        self.assertEqual(ctx["team"], "BUF")
        self.assertEqual([r["name"] for r in ctx["depth_chart"]], ["Delta Outro Time"])

    def test_sem_birth_date_e_sem_ordem_nao_erra(self):
        ctx = assemble_context(self.idx, "1003", TODAY)
        self.assertIsNone(ctx["age"])
        # o chart do time dele existe (rivais têm ordem), mas ele não está nele
        self.assertEqual(len(ctx["depth_chart"]), 3)
        self.assertFalse(ctx["in_chart"])

    def test_fora_do_pool_contexto_vazio(self):
        ctx = assemble_context(self.idx, "99999", TODAY)
        self.assertIsNone(ctx["age"])
        self.assertEqual(ctx["depth_chart"], [])
        self.assertFalse(ctx["in_chart"])

    def test_sem_sleeper_id_contexto_vazio(self):
        ctx = assemble_context(self.idx, None, TODAY)
        self.assertEqual(ctx["depth_chart"], [])

    def test_sid_inteiro_coage_para_string(self):
        # A rota passa Player.sleeper_player_id (string), mas o núcleo aceita int
        ctx = assemble_context(self.idx, 1001, TODAY)
        self.assertEqual(ctx["team"], "CAR")
        self.assertTrue(ctx["in_chart"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
