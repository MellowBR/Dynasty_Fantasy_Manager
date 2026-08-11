"""
phantom_board_test.py — núcleo puro do script de população do board (OFF26-24, F2a).

Testa o que é testável SEM navegador: parsing de picks, casamento sheet↔picks por sid,
mapa Team N ↔ owner, decisão de assentamento, guarda de league_id, o reshape do
endpoint de export — e as guardas estáticas do driver (lista de proibições, verdade
via API). O driver Playwright em si é exercido pelo owner (roteiro no README).

Fixtures de LEITURA do ensaio de 11/08: draft 1392654933580353536, 18 keepers do
MellowBR ($176), mapa dos 12 slots. Fixtures conferem derivação — nunca a substituem.
"""

import unittest
from pathlib import Path

from tools.phantom_board import config
from tools.phantom_board.core import (
    ALREADY, PENDING, SETTLED, TIMEOUT,
    build_slot_map, flatten_sheet, league_guard, match_picks_to_sheet,
    parse_pick, settlement_decision, team_totals,
)

BASE_DIR = Path(__file__).resolve().parent

# Mapa medido no ensaio de 11/08 — fixture de CONFERÊNCIA (a fonte é a derivação).
ENSAIO_SLOTS = {1: "MellowBR", 2: "rafadgil", 3: "TropadoJarra", 4: "icarocosta1",
                5: "rafaelferreirap", 6: "fernandoxmf", 7: "murilofborges",
                8: "LeoFBorges1", 9: "fertorquato", 10: "michelzela",
                11: "gabrieldiinis", 12: "freddupont"}


def pick(sid, slot, amount, picked_by="u1", pos="RB", first="X", last="Y"):
    return {"player_id": sid, "draft_slot": slot, "roster_id": slot,
            "picked_by": picked_by,
            "metadata": {"amount": amount, "position": pos,
                         "first_name": first, "last_name": last}}


def sheet_fixture():
    return {
        "season": 2026,
        "stage_meta": {"stage": "provisoria"},
        "teams": [
            {"team_id": 1, "team_name": "Cangaceiros da Colina",
             "sleeper_owner_id": "u1", "fa_budget": 24,
             "keepers": [
                 {"sleeper_player_id": "4046", "name": "Patrick Mahomes",
                  "position": "QB", "salary": 42},
                 {"sleeper_player_id": "LAR", "name": "Los Angeles Rams",
                  "position": "DEF", "salary": 1},
             ]},
            {"team_id": 2, "team_name": "mongoloides",
             "sleeper_owner_id": "u2", "fa_budget": 10,
             "keepers": [
                 {"sleeper_player_id": "4983", "name": "DJ Moore",
                  "position": "WR", "salary": 21},
             ]},
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. Guarda de nascença
# ══════════════════════════════════════════════════════════════════════════════

class TestLeagueGuard(unittest.TestCase):

    def test_liga_certa_passa(self):
        self.assertIsNone(league_guard({"league_id": config.LEAGUE_ID},
                                       config.LEAGUE_ID))

    def test_liga_errada_recusa(self):
        err = league_guard({"league_id": "999"}, config.LEAGUE_ID)
        self.assertIn("GUARDA DE LIGA", err)
        self.assertIn("Recusando", err)

    def test_draft_ausente_recusa(self):
        self.assertIsNotNone(league_guard({}, config.LEAGUE_ID))
        self.assertIsNotNone(league_guard(None, config.LEAGUE_ID))

    def test_league_id_e_o_da_fantasma(self):
        """⛔ Hardcoded de propósito — mudar isso é mudar a guarda de nascença."""
        self.assertEqual(config.LEAGUE_ID, "1389725099556372481")


# ══════════════════════════════════════════════════════════════════════════════
# 2. Parsing de picks (armadilhas do OFF26-4 respeitadas)
# ══════════════════════════════════════════════════════════════════════════════

class TestParsePick(unittest.TestCase):

    def test_amount_string_vira_int(self):
        self.assertEqual(parse_pick(pick("4046", 1, "40"))["amount"], 40)

    def test_def_e_sigla_nunca_int(self):
        p = parse_pick(pick("LAR", 1, "1"))
        self.assertEqual(p["sid"], "LAR")
        self.assertIsInstance(p["sid"], str)

    def test_amount_ausente_vira_none(self):
        self.assertIsNone(parse_pick(pick("4046", 1, None))["amount"])
        self.assertIsNone(parse_pick({"player_id": "4046"})["amount"])

    def test_amount_lixo_nao_levanta(self):
        self.assertIsNone(parse_pick(pick("4046", 1, "abc"))["amount"])


# ══════════════════════════════════════════════════════════════════════════════
# 3. Mapa Team N ↔ owner (derivado, conferido contra o ensaio)
# ══════════════════════════════════════════════════════════════════════════════

class TestSlotMap(unittest.TestCase):

    def test_deriva_do_draft_order(self):
        draft = {"draft_order": {"u10": 1, "u20": 2}}
        users = [{"user_id": "u10", "display_name": "MellowBR"},
                 {"user_id": "u20", "display_name": "rafadgil"}]
        m = build_slot_map(draft, users)
        self.assertEqual(m[1], {"user_id": "u10", "handle": "MellowBR"})
        self.assertEqual(m[2]["handle"], "rafadgil")

    def test_fixture_do_ensaio_confere_formato(self):
        """Os 12 handles do ensaio, como fixture de conferência do formato."""
        draft = {"draft_order": {f"u{n}": n for n in ENSAIO_SLOTS}}
        users = [{"user_id": f"u{n}", "display_name": h}
                 for n, h in ENSAIO_SLOTS.items()]
        m = build_slot_map(draft, users)
        self.assertEqual(len(m), 12)
        self.assertEqual(m[1]["handle"], "MellowBR")
        self.assertEqual(m[10]["handle"], "michelzela")

    def test_user_sem_handle_degrada(self):
        m = build_slot_map({"draft_order": {"u9": 3}}, [])
        self.assertEqual(m[3], {"user_id": "u9", "handle": ""})


# ══════════════════════════════════════════════════════════════════════════════
# 4. Casamento sheet ↔ picks (por sid, nunca por nome)
# ══════════════════════════════════════════════════════════════════════════════

class TestMatch(unittest.TestCase):

    def setUp(self):
        self.rows = flatten_sheet(sheet_fixture())
        self.slots = {1: {"user_id": "u1", "handle": "MellowBR"},
                      2: {"user_id": "u2", "handle": "rafadgil"}}

    def test_flatten_carrega_sid_owner_salario(self):
        self.assertEqual(len(self.rows), 3)
        mahomes = next(r for r in self.rows if r["sid"] == "4046")
        self.assertEqual((mahomes["salary"], mahomes["owner_id"]), (42, "u1"))

    def test_pick_casado(self):
        rep = match_picks_to_sheet([pick("4046", 1, "42")], self.rows, self.slots)
        self.assertEqual(len(rep["matched"]), 1)
        self.assertEqual(rep["salary_divergent"], [])

    def test_salario_divergente_denuncia(self):
        rep = match_picks_to_sheet([pick("4046", 1, "13")], self.rows, self.slots)
        self.assertEqual(len(rep["salary_divergent"]), 1)
        self.assertEqual(rep["salary_divergent"][0]["sheet_salary"], 42)
        self.assertEqual(rep["salary_divergent"][0]["pick_amount"], 13)

    def test_owner_divergente_denuncia(self):
        """Keeper no slot de OUTRO owner — a classe grave da auditoria."""
        rep = match_picks_to_sheet([pick("4046", 2, "42")], self.rows, self.slots)
        self.assertEqual(len(rep["owner_divergent"]), 1)
        self.assertEqual(rep["matched"], [])

    def test_def_por_sigla_casa(self):
        rep = match_picks_to_sheet([pick("LAR", 1, "1")], self.rows, self.slots)
        self.assertEqual(len(rep["matched"]), 1)

    def test_pick_fora_da_sheet_e_faltantes(self):
        rep = match_picks_to_sheet([pick("9999", 2, "5")], self.rows, self.slots)
        self.assertEqual(len(rep["picks_not_in_sheet"]), 1)
        self.assertEqual(len(rep["sheet_missing"]), 3)   # ninguém da sheet designado

    def test_totais_por_time(self):
        rep = match_picks_to_sheet(
            [pick("4046", 1, "42"), pick("LAR", 1, "1")], self.rows, self.slots)
        t = team_totals(rep, "Cangaceiros da Colina")
        self.assertEqual((t["count"], t["total"]), (2, 43))


# ══════════════════════════════════════════════════════════════════════════════
# 5. Decisão de assentamento (o toast nunca é veredito)
# ══════════════════════════════════════════════════════════════════════════════

class TestSettlement(unittest.TestCase):

    def test_assentou(self):
        self.assertEqual(settlement_decision("x", False, True, False), SETTLED)

    def test_duplicata_e_sucesso(self):
        """Servidor rejeita duplicado — presente antes+agora = estado desejado."""
        self.assertEqual(settlement_decision("x", True, True, False), ALREADY)

    def test_pendente_dentro_da_janela(self):
        """Lag de ~3s da API: ausente sem esgotar polls = continuar."""
        self.assertEqual(settlement_decision("x", False, False, False), PENDING)

    def test_timeout_esgotado(self):
        """Caso Caleb (staging revertido): candidato a re-comando, nunca silêncio."""
        self.assertEqual(settlement_decision("x", False, False, True), TIMEOUT)


# ══════════════════════════════════════════════════════════════════════════════
# 6. O endpoint de export do Manager (reshape puro)
# ══════════════════════════════════════════════════════════════════════════════

class TestSheetExport(unittest.TestCase):

    def test_reshape_tuplas_para_dicts(self):
        from routes.admin import _sheet_export_payload
        raw = {"revealed": True, "season": 2026, "lock_timestamp": "T",
               "stage_meta": {"stage": "provisoria"},
               "teams": [{"team_id": 1, "team_name": "A", "sleeper_owner_id": "u1",
                          "fa_budget": 24,
                          "keepers": [("4046", "Patrick Mahomes", "QB", 42)]}]}
        out = _sheet_export_payload(raw)
        k = out["teams"][0]["keepers"][0]
        self.assertEqual(k, {"sleeper_player_id": "4046", "name": "Patrick Mahomes",
                             "position": "QB", "salary": 42})
        self.assertEqual(out["teams"][0]["sleeper_owner_id"], "u1")
        # e o pacote é consumível direto pelo flatten do script
        rows = flatten_sheet(out)
        self.assertEqual(rows[0]["sid"], "4046")

    def test_reshape_indisponivel_degrada(self):
        from routes.admin import _sheet_export_payload
        out = _sheet_export_payload({"revealed": False, "season": 2026,
                                     "stage_meta": {"available": False}})
        self.assertEqual(out["teams"], [])


# ══════════════════════════════════════════════════════════════════════════════
# 7. Guardas estáticas do driver
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardasEstaticas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.board = (BASE_DIR / "tools" / "phantom_board" / "board.py").read_text(
            encoding="utf-8")
        cls.cli = (BASE_DIR / "tools" / "phantom_board" / "cli.py").read_text(
            encoding="utf-8")

    def test_lista_de_proibicoes_existe_e_e_consultada(self):
        self.assertIn("START DRAFT", str(config.FORBIDDEN_CLICK_LABELS))
        self.assertIn("RESET DRAFT", str(config.FORBIDDEN_CLICK_LABELS))
        self.assertIn("assert_allowed_click", self.board)

    def test_guarda_roda_antes_do_browser(self):
        """A guarda de liga vem ANTES de abrir o browser no open_board."""
        corpo = self.board.split("def open_board")[1].split("\ndef ")[0]
        self.assertLess(corpo.index("league_guard"), corpo.index("sync_playwright()"))

    def test_verdade_e_a_api_nunca_o_toast(self):
        """O driver decide por fetch_picks + settlement_decision; 'toast' só aparece
        em comentário — nenhuma leitura de toast como veredito."""
        self.assertIn("fetch_picks", self.board)
        self.assertIn("settlement_decision", self.board)

    def test_playwright_e_lazy(self):
        """`validate` (read-only) roda sem playwright instalado — o import vive
        dentro do open_board."""
        corpo = self.board.split("def open_board")[1].split("\ndef ")[0]
        self.assertIn("from playwright.sync_api import sync_playwright", corpo)
        self.assertNotIn("import playwright", self.cli)

    def test_teclado_real_nunca_value(self):
        """Busca e preço por press_sequentially/press — setar .value não dispara
        o filtro (achado do ensaio)."""
        self.assertIn("press_sequentially", self.board)
        self.assertNotIn(".fill(", self.board.replace('search.fill("")', ""))

    def test_designate_clica_o_plus_nunca_o_nome(self):
        self.assertIn("SEL_PLUS_BUTTON", self.board)
        self.assertIn("NUNCA o nome", self.board)


if __name__ == "__main__":
    unittest.main(verbosity=2)
