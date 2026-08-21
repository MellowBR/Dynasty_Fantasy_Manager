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
    BLOQUEADO_TETO, CONFLITO, DESIGNAR, JA_ASSENTADO,
    build_slot_map, campaign_summary, choose_menu_item, conference_report,
    draft_budget_slots, duplicate_handles, flatten_sheet,
    idempotency_decision, is_budget_block, league_guard, match_picks_to_sheet,
    max_bid, menu_label_matches, menu_labels_seen, menu_target_label,
    modal_header_check, parse_pick, parse_price_value,
    parse_result_row, position_matches, price_readback_decision, resolve_slot_map,
    row_matches_name, search_filter_check, select_candidate_rows,
    select_candidate_rows_named, settlement_decision,
    slot_map_from_picks, slot_map_from_rosters, team_pending_keepers,
    team_totals, url_guard,
)

BASE_DIR = Path(__file__).resolve().parent
NL = "\n"     # linhas do DOM real vêm empilhadas por newline (fixtures do FIX5)

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

    # ── FIX 11/08: identidade do board POR CONSTRUÇÃO (URL × draft_id derivado) ──

    def test_url_com_draft_id_derivado_passa(self):
        """O 1º probe real provou: a página do draft NÃO exibe o nome da liga — a
        prova é a URL conter o draft_id que o script derivou pela API."""
        self.assertIsNone(url_guard(
            "https://sleeper.com/draft/nfl/1392654933580353536",
            "1392654933580353536"))

    def test_url_divergente_aborta(self):
        err = url_guard("https://sleeper.com/draft/nfl/999", "1392654933580353536")
        self.assertIn("GUARDA DE IDENTIDADE", err)
        self.assertIn("Nenhum clique", err)

    def test_url_vazia_ou_sem_draft_abortam(self):
        self.assertIsNotNone(url_guard("", "123"))
        self.assertIsNotNone(url_guard("https://sleeper.com/x", ""))


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

    # ── FIX3 (11/08): cadeia de resolução — o abort real do 1º designate ─────────
    # Medido no draft vivo (pre_draft pós-RESET): draft_order=None, MAS
    # slot_to_roster_id presente e completo; rosters dão roster→owner.

    def test_cadeia_a_draft_order_presente(self):
        draft = {"draft_order": {"u10": 1}}
        users = [{"user_id": "u10", "display_name": "MellowBR"}]
        m, fonte = resolve_slot_map(draft, users)
        self.assertEqual(fonte, "draft_order")
        self.assertEqual(m[1]["handle"], "MellowBR")

    def test_cadeia_b_slot_to_roster_com_draft_order_nulo(self):
        """O caso REAL do abort (Cam Ward → michelzela): pre_draft com draft_order
        null resolve por slot_to_roster_id × rosters — API pura, sem ambiguidade."""
        draft = {"draft_order": None,
                 "slot_to_roster_id": {"1": 1, "10": 10}}
        rosters = [{"roster_id": 1, "owner_id": "1130162144764506112"},
                   {"roster_id": 10, "owner_id": "1126909140380569600"}]
        users = [{"user_id": "1130162144764506112", "display_name": "MellowBR"},
                 {"user_id": "1126909140380569600", "display_name": "michelzela"}]
        m, fonte = resolve_slot_map(draft, users, rosters, [])
        self.assertEqual(fonte, "slot_to_roster_id×rosters")
        self.assertEqual(m[10]["handle"], "michelzela")   # o alvo do abort real
        self.assertEqual(m[1]["handle"], "MellowBR")

    def test_cadeia_c_picks_observados(self):
        draft = {"draft_order": None}
        picks = [pick("11628", 1, "1", picked_by="1130162144764506112")]
        users = [{"user_id": "1130162144764506112", "display_name": "MellowBR"}]
        m, fonte = resolve_slot_map(draft, users, [], picks)
        self.assertEqual(fonte, "picks_observados")
        self.assertEqual(m[1]["user_id"], "1130162144764506112")

    def test_cadeia_esgotada_mapa_vazio_e_fonte_nomeada(self):
        """Irresolvível: mapa vazio + fonte 'nenhuma' — o CLI aborta nomeando o que
        faltou (o abort barulhento permanece)."""
        m, fonte = resolve_slot_map({"draft_order": None}, [], [], [])
        self.assertEqual((m, fonte), ({}, "nenhuma"))

    def test_fallback_b_ignora_roster_sem_owner(self):
        m = slot_map_from_rosters({"slot_to_roster_id": {"1": 1, "2": 2}},
                                  [{"roster_id": 1, "owner_id": "u1"},
                                   {"roster_id": 2, "owner_id": None}],
                                  [])
        self.assertEqual(list(m.keys()), [1])

    def test_fallback_c_ignora_pick_sem_slot(self):
        m = slot_map_from_picks([{"player_id": "x", "picked_by": "u1"}], [])
        self.assertEqual(m, {})


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
# 4b. Menu de contexto (FIX4 — o call log do 1º designate virou fixture)
# ══════════════════════════════════════════════════════════════════════════════

class TestChooseMenuItem(unittest.TestCase):

    def test_set_player_do_time_certo_clica(self):
        texts = ["Set Player\nManually set a player for Team 10",
                 "Reset Nomination\nChange nominator to Team 10"]
        self.assertEqual(choose_menu_item(texts, 10), ("click", 0))

    def test_change_player_aborta(self):
        """O call log real: célula PREENCHIDA abriu 'Change Player' e interceptou
        30s de retries — agora é abort imediato, nunca prosseguir."""
        texts = ["Change Player\nManually change the player for Team 1"]
        self.assertEqual(choose_menu_item(texts, 1), ("abort", "change_player"))

    def test_change_player_vence_mesmo_com_set_presente(self):
        """Menu misto: a presença de Change Player denuncia célula errada."""
        texts = ["Change Player\n...", "Set Player\nManually set a player for Team 1"]
        self.assertEqual(choose_menu_item(texts, 1), ("abort", "change_player"))

    def test_set_player_de_outro_time_aborta(self):
        """Coluna↔slot quebrou: fechar e abortar — nada de tentar a próxima."""
        texts = ["Set Player\nManually set a player for Team 3"]
        self.assertEqual(choose_menu_item(texts, 10), ("abort", "wrong_team"))

    def test_team_1_nao_casa_com_team_10(self):
        """'for Team 1' é prefixo de 'for Team 10' — o N esperado tem de casar
        o slot pedido, não um prefixo dele."""
        texts = ["Set Player\nManually set a player for Team 10"]
        self.assertEqual(choose_menu_item(texts, 10), ("click", 0))
        self.assertEqual(choose_menu_item(texts, 1)[0], "abort")

    def test_menu_vazio_ou_irreconhecivel(self):
        self.assertEqual(choose_menu_item([], 5), ("abort", "no_menu"))
        self.assertEqual(choose_menu_item(["Lixo"], 5), ("abort", "no_menu"))


# ══════════════════════════════════════════════════════════════════════════════
# 4b-bis. FIX12 — âncora de identidade da coluna: o NOME DO OWNER (21/08)
#
# Fixture de CAMPO (corrida real de 21/08, slot 1 de `rafadgil`): o menu devolveu
# o nome do owner no lugar do rótulo genérico — a liga ganhou `show_team_names:
# "0"` e os 12 times passaram a exibir username. A guarda de então recusou
# designar (acerto: a coluna era a certa, o RECONHECIMENTO é que falhou).
# ══════════════════════════════════════════════════════════════════════════════

MENU_CAMPO_21_08 = ["Set Player\nManually set a player for rafadgil",
                    "Reset Nomination\nChange nominator to rafadgil"]


class TestAncoraDeColuna(unittest.TestCase):

    def test_caso_real_do_log_rafadgil_no_slot_1(self):
        """O caso de campo, nominal: com o handle do slot, o item 0 é clicado."""
        self.assertEqual(choose_menu_item(MENU_CAMPO_21_08, 1,
                                          owner_handle="rafadgil"), ("click", 0))

    def test_formato_por_numero_preservado(self):
        """A liga pode voltar a exibir 'Team N' — o caminho por número sobrevive,
        inclusive quando o handle esperado é outro."""
        texts = ["Set Player\nManually set a player for Team 7"]
        self.assertEqual(choose_menu_item(texts, 7, owner_handle="rafadgil"),
                         ("click", 0))
        self.assertEqual(choose_menu_item(texts, 7), ("click", 0))

    def test_owner_de_outro_time_aborta(self):
        """Coluna errada continua sendo recusa — o nome tem de ser O DO SLOT."""
        self.assertEqual(choose_menu_item(MENU_CAMPO_21_08, 1,
                                          owner_handle="michelzela"),
                         ("abort", "wrong_team"))

    def test_handle_desconhecido_nao_designa_as_cegas(self):
        """Sem handle (mapa sem display_name), o rótulo de nome não casa nada:
        abort barulhento, jamais designação silenciosa."""
        self.assertEqual(choose_menu_item(MENU_CAMPO_21_08, 1),
                         ("abort", "wrong_team"))

    def test_casamento_e_exato_nunca_substring(self):
        """⛔ Frouxidão aqui designa elenco na coluna errada: 'rafadgil' não pode
        casar 'rafadgil2' nem 'rafa', em nenhuma direção."""
        texts = ["Set Player\nManually set a player for rafadgil2"]
        self.assertEqual(choose_menu_item(texts, 1, owner_handle="rafadgil"),
                         ("abort", "wrong_team"))
        self.assertEqual(choose_menu_item(MENU_CAMPO_21_08, 1,
                                          owner_handle="rafadgil2"),
                         ("abort", "wrong_team"))

    def test_ambiguidade_aborta(self):
        """Dois itens nomeando a coluna esperada não se resolvem no chute."""
        texts = ["Set Player\nManually set a player for rafadgil",
                 "Set Player\nManually set a player for rafadgil"]
        self.assertEqual(choose_menu_item(texts, 1, owner_handle="rafadgil"),
                         ("abort", "ambiguous"))

    def test_rotulo_ilegivel_aborta_barulhento(self):
        """Formato mudou de novo (item de designação sem rótulo legível) → abort
        próprio, nunca designar às cegas."""
        texts = ["Set Player"]
        self.assertEqual(choose_menu_item(texts, 1, owner_handle="rafadgil"),
                         ("abort", "unreadable_label"))
        texts = ["Set Player\nManually set a player for   "]
        self.assertEqual(choose_menu_item(texts, 1, owner_handle="rafadgil"),
                         ("abort", "unreadable_label"))

    def test_reset_de_nominacao_nunca_e_item_de_designacao(self):
        """⛔ Os dois itens carregam o MESMO nome de owner: o de reset não pode
        ser lido como designação nem sozinho no menu."""
        self.assertIsNone(menu_target_label(
            "Reset Nomination\nChange nominator to rafadgil"))
        so_reset = ["Reset Nomination\nChange nominator to rafadgil"]
        self.assertEqual(choose_menu_item(so_reset, 1, owner_handle="rafadgil"),
                         ("abort", "no_menu"))

    def test_indice_clicado_e_o_do_set_player_nao_o_do_reset(self):
        """Menu na ordem invertida: o índice devolvido segue sendo o do Set Player."""
        texts = ["Reset Nomination\nChange nominator to rafadgil",
                 "Set Player\nManually set a player for rafadgil"]
        self.assertEqual(choose_menu_item(texts, 1, owner_handle="rafadgil"),
                         ("click", 1))

    def test_username_com_o_literal_team_nao_confunde(self):
        """Username 'Team 3' no slot 5: casa como NOME (é o handle do slot), e o
        mesmo rótulo no slot 3 com outro handle segue casando por número — mas
        'Team 3' num slot que não é o 3 nem tem esse handle é recusado."""
        texts = ["Set Player\nManually set a player for Team 3"]
        self.assertEqual(choose_menu_item(texts, 5, owner_handle="Team 3"),
                         ("click", 0))
        self.assertEqual(choose_menu_item(texts, 3, owner_handle="outro"),
                         ("click", 0))
        self.assertEqual(choose_menu_item(texts, 5, owner_handle="outro"),
                         ("abort", "wrong_team"))

    def test_rotulo_tolera_espaco_e_caixa(self):
        """O DOM é a autoridade sobre o formato: aparar e ignorar caixa é
        tolerância de RENDERIZAÇÃO, não afrouxamento do casamento."""
        texts = ["Set Player\n  Manually set a player for   RafaDGil  "]
        self.assertEqual(choose_menu_item(texts, 1, owner_handle="rafadgil"),
                         ("click", 0))

    def test_ancora_reconhecida_e_reportavel(self):
        """Item 5 da tarefa: o rótulo observado sai do núcleo para o relatório —
        mudança futura de formato vira linha de log, não abort mudo."""
        self.assertEqual(menu_labels_seen(MENU_CAMPO_21_08), ["rafadgil"])
        self.assertEqual(menu_label_matches("rafadgil", 1, "rafadgil"), "handle")
        self.assertEqual(menu_label_matches("Team 1", 1, "rafadgil"), "numero")
        self.assertIsNone(menu_label_matches("Team 2", 1, "rafadgil"))
        self.assertIsNone(menu_label_matches(None, 1, "rafadgil"))

    def test_handle_repetido_nao_prova_coluna(self):
        """Handles iguais em 2+ slots: o nome deixa de ser prova (quem chama
        desliga a âncora por nome e sobra a prova por número)."""
        mapa = {1: {"user_id": "a", "handle": "rafa"},
                2: {"user_id": "b", "handle": "rafa"},
                3: {"user_id": "c", "handle": "michelzela"},
                4: {"user_id": "d", "handle": ""}}
        self.assertEqual(duplicate_handles(mapa), {"rafa"})
        self.assertEqual(duplicate_handles(ENSAIO_MAPA_SLOTS), set())


ENSAIO_MAPA_SLOTS = {s: {"user_id": str(s), "handle": h}
                     for s, h in ENSAIO_SLOTS.items()}


# ══════════════════════════════════════════════════════════════════════════════
# 4c. Anti-homônimo: o parser do DOM real (FIX5 — o abort de 11/08 é a fixture)
# ══════════════════════════════════════════════════════════════════════════════

class TestParseResultRow(unittest.TestCase):
    """As linhas LITERAIS do abort real ('0 candidatos QB' com o Cam Ward na
    lista): .position empilhado por newlines, sigla duplicada, status de injury."""

    def test_cam_ward_a_linha_do_abort(self):
        self.assertEqual(parse_result_row("QB" + NL + "TEN", "TEN"), ("QB", "TEN"))

    def test_injury_status_tolerado(self):
        self.assertEqual(parse_result_row("RB" + NL + "DET" + NL + "QUES", "DET"),
                         ("RB", "DET"))
        self.assertEqual(parse_result_row("WR" + NL + "NYG" + NL + "QUES", "NYG"),
                         ("WR", "NYG"))
        self.assertEqual(parse_result_row("WR" + NL + "CHI" + NL + "QUES", "CHI"),
                         ("WR", "CHI"))

    def test_string_unica_concatenada(self):
        """O formato como apareceu na mensagem do abort (pos+team juntos)."""
        self.assertEqual(parse_result_row("QB" + NL + "TEN TEN"), ("QB", "TEN"))
        self.assertEqual(parse_result_row("RB" + NL + "DET" + NL + "QUES DET"),
                         ("RB", "DET"))

    def test_formato_limpo_do_ensaio_segue_ok(self):
        self.assertEqual(parse_result_row("QB", "KC"), ("QB", "KC"))
        self.assertEqual(parse_result_row("DEF", "LAR"), ("DEF", "LAR"))

    def test_vazio_degrada(self):
        self.assertEqual(parse_result_row("", ""), ("", ""))


class TestSearchFilterCheck(unittest.TestCase):
    """FIX6 — a lista de FUNDO vazou no matching (57 linhas do ranking geral):
    dezenas de linhas = busca não aplicada/escopo errado → abort, nunca parsear."""

    def test_57_linhas_do_abort_real_abortam(self):
        err = search_filter_check(57)
        self.assertIn("busca não filtrou", err)
        self.assertIn("57", err)

    def test_lista_filtrada_passa(self):
        self.assertIsNone(search_filter_check(1))
        self.assertIsNone(search_filter_check(8))

    def test_limite_configurado(self):
        self.assertIsNone(search_filter_check(10, max_expected=10))
        self.assertIsNotNone(search_filter_check(11, max_expected=10))


class TestModalHeaderCheck(unittest.TestCase):
    """FIX7 — o header 'Make Manual Pick for Team N' do #modal (screenshot do
    abort real) prova que o dialog aberto é o manual pick DO TIME CERTO."""

    def test_header_do_time_certo(self):
        self.assertEqual(modal_header_check(
            "Proj $$ Make Manual Pick for Team 10 Assign a player", 10), "ok")

    def test_time_errado_com_fronteira(self):
        """'Team 1' não pode casar slot 10 — nem 'Team 10' casar slot 1."""
        self.assertEqual(modal_header_check("Make Manual Pick for Team 10", 1),
                         "wrong_team")
        self.assertEqual(modal_header_check("Make Manual Pick for Team 1", 10),
                         "wrong_team")

    def test_dialog_inesperado(self):
        """Dialog residual/aviso sem o header → Esc + abort nomeado (driver)."""
        self.assertEqual(modal_header_check("Draft not started", 10), "unexpected")
        self.assertEqual(modal_header_check("", 10), "unexpected")

    def test_fix12_header_por_nome_de_owner(self):
        """FIX12 — o header nomeia a coluna com o MESMO rótulo do menu: se o board
        exibe username, o header também exibe. A âncora dupla vale nos dois."""
        txt = "Make Manual Pick for rafadgil Assign a player"
        self.assertEqual(modal_header_check(txt, 1, owner_handle="rafadgil"), "ok")
        self.assertEqual(modal_header_check(txt, 1, owner_handle="michelzela"),
                         "wrong_team")
        self.assertEqual(modal_header_check(txt, 1), "wrong_team")

    def test_fix12_header_nome_casa_por_fronteira(self):
        """⛔ 'rafadgil' não pode casar 'rafadgil2' — nome é casamento exato."""
        self.assertEqual(modal_header_check("Make Manual Pick for rafadgil2", 1,
                                            owner_handle="rafadgil"), "wrong_team")


class TestIdempotencyDecision(unittest.TestCase):
    """F2b — a lição da F2a: o pick de Cam Ward gravou numa run que morreu antes
    do poll — idempotência é a PRIMEIRA verificação, não a última."""

    def setUp(self):
        self.picks = [pick("12522", 10, "1", picked_by="u10")]
        self.slots = {10: {"user_id": "u10", "handle": "michelzela"}}

    def test_ausente_designa(self):
        self.assertEqual(idempotency_decision("999", "u10", 1,
                                              self.picks, self.slots),
                         (DESIGNAR, None))

    def test_presente_certo_e_sucesso_zero_cliques(self):
        dec, det = idempotency_decision("12522", "u10", 1, self.picks, self.slots)
        self.assertEqual(dec, JA_ASSENTADO)
        self.assertEqual(det["slot"], 10)

    def test_time_divergente_e_conflito(self):
        dec, det = idempotency_decision("12522", "u1", 1, self.picks, self.slots)
        self.assertEqual(dec, CONFLITO)
        self.assertEqual(det["motivo"], "time divergente")

    def test_preco_divergente_e_conflito(self):
        dec, det = idempotency_decision("12522", "u10", 5, self.picks, self.slots)
        self.assertEqual(dec, CONFLITO)
        self.assertEqual(det["motivo"], "preço divergente")

    def test_preco_sem_amount_no_pick_aceita(self):
        """Pick sem metadata.amount → não conferível → assentado (não conflito)."""
        picks = [{"player_id": "12522", "draft_slot": 10, "picked_by": "u10"}]
        dec, _ = idempotency_decision("12522", "u10", 5, picks, self.slots)
        self.assertEqual(dec, JA_ASSENTADO)


class TestTeamPendingKeepers(unittest.TestCase):
    """F2b — retomabilidade por construção: o que já assentou sai do plano."""

    def test_pula_os_ja_designados(self):
        rows = flatten_sheet(sheet_fixture())          # u1: 4046 + LAR; u2: 4983
        picks = [pick("4046", 1, "42", picked_by="u1")]
        pend = team_pending_keepers(rows, picks, "u1")
        self.assertEqual([r["sid"] for r in pend], ["LAR"])

    def test_time_completo_da_plano_vazio(self):
        rows = flatten_sheet(sheet_fixture())
        picks = [pick("4046", 1, "42"), pick("LAR", 1, "1")]
        self.assertEqual(team_pending_keepers(rows, picks, "u1"), [])

    def test_sem_picks_plano_inteiro(self):
        rows = flatten_sheet(sheet_fixture())
        self.assertEqual(len(team_pending_keepers(rows, [], "u1")), 2)


class TestBudgetBlock(unittest.TestCase):
    """F2b — bloqueado_teto é resultado esperado pré-late-drop (§B.3.2), não
    erro; casos reais da sheet: AlexTheDawg $203 e Miller Time! $200."""

    def test_mensagem_real_do_sleeper(self):
        self.assertTrue(is_budget_block("Team 4 does not have enough budget"))
        self.assertTrue(is_budget_block("DOES NOT HAVE ENOUGH BUDGET!"))

    def test_outros_textos_nao(self):
        self.assertFalse(is_budget_block("This pick could not be processed"))
        self.assertFalse(is_budget_block(""))
        self.assertFalse(is_budget_block(None))


class TestCampaignSummary(unittest.TestCase):

    def test_agregacao_por_status(self):
        times = [
            {"status": "ok", "designados": 20, "ja_assentados": 1},
            {"status": BLOQUEADO_TETO, "designados": 3},
            {"status": "falha", "designados": 2},
            {"status": "conflito", "designados": 0, "conflitos": 1},
        ]
        r = campaign_summary(times)
        self.assertEqual(r["times_processados"], 4)
        self.assertEqual(r["designados"], 25)
        self.assertEqual(r["ja_assentados"], 1)
        self.assertEqual(r["times_ok"], 1)
        self.assertEqual(r["times_bloqueados"], 1)
        self.assertEqual(r["times_com_falha"], 2)      # falha + conflito
        self.assertEqual(r["conflitos"], 1)

    def test_campanha_vazia(self):
        self.assertEqual(campaign_summary([])["times_processados"], 0)


class TestSelectCandidateRows(unittest.TestCase):

    def _rows(self):
        return [parse_result_row("WR" + NL + "CHI" + NL + "QUES", "CHI"),
                parse_result_row("QB" + NL + "TEN", "TEN"),
                parse_result_row("RB" + NL + "DET" + NL + "QUES", "DET")]

    def test_cam_ward_acha_exatamente_um_qb(self):
        """O caso do abort: 1 QB na lista → 1 candidato, o índice certo."""
        self.assertEqual(select_candidate_rows(self._rows(), "QB"), [1])

    def test_dois_homonimos_mesma_posicao_dao_dois(self):
        """Anti-homônimo NÃO relaxou: 2+ candidatos → quem chama aborta."""
        rows = self._rows() + [parse_result_row("QB" + NL + "MIA", "MIA")]
        self.assertEqual(len(select_candidate_rows(rows, "QB")), 2)

    def test_zero_candidatos_quando_posicao_nao_esta(self):
        self.assertEqual(select_candidate_rows(self._rows(), "K"), [])

    def test_posicao_case_insensitive(self):
        self.assertEqual(select_candidate_rows(self._rows(), "qb"), [1])


# ══════════════════════════════════════════════════════════════════════════════
# 4d. FIX9 — a busca do Sleeper é FUZZY: candidato REAL exige o NOME
# ══════════════════════════════════════════════════════════════════════════════

# A fixture LITERAL do abort da campanha de 12/08 (run populate_20260812T131804Z):
# busca "Malik Willis" no modal do Team 3 devolveu 4 linhas REAIS — o alvo (QB·MIA)
# e três OUTROS jogadores (FAs, sigla vazia): Malik Williams WR, Malik Williams RB
# e Hajj-Malik Williams QB. O parse estava CERTO (screenshot abort_slot3.png);
# o que faltava era o NOME no critério de candidato.
MALIK_PARSED = [("QB", "MIA"), ("WR", ""), ("RB", ""), ("QB", "")]
MALIK_TEXTS = [
    "141 Malik Willis QB MIA $1 6 270.1 15.0 125 712 5 0 0 0 419 2848 17",
    "401 Malik Williams WR $1 - 0.0 0.0 0 0 0 0 0 0 0 0 0",
    "1501 Malik Williams RB $1 - 0.0 0.0 0 0 0 0 0 0 0 0 0",
    "2655 Hajj-Malik Williams QB $1 - 0.0 0.0 0 0 0 0 0 0 0 0 0",
]


class TestRowMatchesName(unittest.TestCase):
    """FIX9 — o nome buscado tem de aparecer como SEQUÊNCIA de tokens na linha."""

    def test_nome_exato_casa_no_meio_das_stats(self):
        self.assertTrue(row_matches_name(MALIK_TEXTS[0], "Malik Willis"))

    def test_williams_nao_e_willis(self):
        """A busca fuzzy devolveu Malik Williams ×2 — nenhum casa Malik Willis."""
        self.assertFalse(row_matches_name(MALIK_TEXTS[1], "Malik Willis"))
        self.assertFalse(row_matches_name(MALIK_TEXTS[2], "Malik Willis"))

    def test_hifen_preserva_identidade(self):
        """'Hajj-Malik' é UM token: não casa 'Malik' — nem 'Malik Williams'."""
        self.assertFalse(row_matches_name(MALIK_TEXTS[3], "Malik Willis"))
        self.assertFalse(row_matches_name(MALIK_TEXTS[3], "Malik Williams"))
        self.assertTrue(row_matches_name(MALIK_TEXTS[3], "Hajj-Malik Williams"))

    def test_normalizacao_acentos_caixa_pontuacao(self):
        self.assertTrue(row_matches_name("7 Amon-Ra St. Brown WR DET",
                                         "Amon-Ra St. Brown"))
        self.assertTrue(row_matches_name("12 JA'MARR CHASE WR CIN",
                                         "Ja'Marr Chase"))
        self.assertTrue(row_matches_name("3 Andre Lopes QB", "André Lopes"))

    def test_newlines_do_dom_toleradas(self):
        self.assertTrue(row_matches_name("141" + NL + "Malik Willis" + NL +
                                         "QB" + NL + "MIA", "Malik Willis"))

    def test_vazio_nao_casa(self):
        self.assertFalse(row_matches_name("", "Malik Willis"))
        self.assertFalse(row_matches_name("Malik Willis QB", ""))


class TestSelectCandidateRowsNamed(unittest.TestCase):
    """FIX9 — o que mudou é O QUE CONTA como candidato (posição exata + nome);
    a REGRA do anti-homônimo (0 ou 2+ candidatos reais → abort) está intacta."""

    def test_fixture_do_abort_da_exatamente_um_candidato(self):
        """As 4 linhas literais de 12/08 → 1 candidato QB real (o índice 0) —
        a designação do Malik Willis prossegue."""
        self.assertEqual(select_candidate_rows_named(
            MALIK_PARSED, "QB", MALIK_TEXTS, "Malik Willis"), [0])

    def test_sigla_vazia_nao_desqualifica(self):
        """FA real (sem time NFL) é candidato legítimo — o discriminador é o
        NOME, nunca a sigla (filtrar por sigla excluiria keeper cortado)."""
        self.assertEqual(select_candidate_rows_named(
            MALIK_PARSED, "QB", MALIK_TEXTS, "Hajj-Malik Williams"), [3])

    def test_posicao_segue_exata(self):
        self.assertEqual(select_candidate_rows_named(
            MALIK_PARSED, "WR", MALIK_TEXTS, "Malik Williams"), [1])
        self.assertEqual(select_candidate_rows_named(
            MALIK_PARSED, "RB", MALIK_TEXTS, "Malik Williams"), [2])

    def test_homonimos_reais_seguem_dando_dois(self):
        """⛔ Critério intacto: MESMO nome + MESMA posição em 2 linhas → 2
        candidatos → quem chama aborta."""
        parsed = [("QB", "MIA"), ("QB", "")]
        texts = ["141 Malik Willis QB MIA", "999 Malik Willis QB"]
        self.assertEqual(len(select_candidate_rows_named(
            parsed, "QB", texts, "Malik Willis")), 2)

    def test_zero_candidatos_quando_nome_nao_esta(self):
        self.assertEqual(select_candidate_rows_named(
            MALIK_PARSED, "QB", MALIK_TEXTS, "Cam Ward"), [])

    def test_textos_ausentes_nao_viram_candidato(self):
        """Sem texto de linha não há como provar o nome — não conta (nunca
        degradar para posição-só em silêncio)."""
        self.assertEqual(select_candidate_rows_named(
            MALIK_PARSED, "QB", [], "Malik Willis"), [])
        self.assertEqual(select_candidate_rows_named(
            MALIK_PARSED, "QB", None, "Malik Willis"), [])


# ══════════════════════════════════════════════════════════════════════════════
# 4e. FIX10 — as duas caras do teto: clamp silencioso do input + max bid
# ══════════════════════════════════════════════════════════════════════════════

# A sheet REAL do AlexTheDawg (run de 12/08, validate 144919Z): 18 keepers, $203,
# em ordem de comando. Os 6 primeiros somam $180; o board tem 22 slots.
ALEX_SHEET = [61, 59, 21, 19, 10, 10, 6, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1]


class TestParsePriceValue(unittest.TestCase):

    def test_formatos_do_input(self):
        self.assertEqual(parse_price_value("6"), 6)
        self.assertEqual(parse_price_value("$6"), 6)
        self.assertEqual(parse_price_value(" 12 "), 12)

    def test_ilegivel_da_none(self):
        self.assertIsNone(parse_price_value(""))
        self.assertIsNone(parse_price_value("abc"))
        self.assertIsNone(parse_price_value(None))


class TestPriceReadbackDecision(unittest.TestCase):
    """FIX10 — o read-back do input é a VERDADE OPERACIONAL: clampou → teto
    (nunca gravar preço ≠ sheet); ilegível/maior → abortar, nunca às cegas."""

    def test_igual_libera_o_set(self):
        self.assertEqual(price_readback_decision(6, 6), "ok")
        self.assertEqual(price_readback_decision(1, 1), "ok")

    def test_clamp_vira_bloqueado_teto(self):
        """Os 4 clamps reais da run: 6→5, 4→1, 3→1, 2→1."""
        self.assertEqual(price_readback_decision(6, 5), BLOQUEADO_TETO)
        self.assertEqual(price_readback_decision(4, 1), BLOQUEADO_TETO)
        self.assertEqual(price_readback_decision(3, 1), BLOQUEADO_TETO)
        self.assertEqual(price_readback_decision(2, 1), BLOQUEADO_TETO)

    def test_ilegivel_ou_maior_aborta(self):
        """Read-back None (input ilegível) ou MAIOR que o comandado = estado
        indeterminado — abort barulhento, o SET PLAYER não é acionado."""
        self.assertEqual(price_readback_decision(6, None), "abortar")
        self.assertEqual(price_readback_decision(6, 7), "abortar")


class TestMaxBid(unittest.TestCase):
    """FIX10 — modelo verificado contra a run: max_bid = budget − gasto −
    $1 × (vagas vazias RESTANTES do board além da atual)."""

    def test_os_quatro_clamps_da_run(self):
        self.assertEqual(max_bid(200, 180, 6, 22), 5)    # Keenan Allen 6→5
        self.assertEqual(max_bid(200, 185, 7, 22), 1)    # Croskey-Merritt 4→1
        self.assertEqual(max_bid(200, 186, 8, 22), 1)    # Kaleb Johnson 3→1
        self.assertEqual(max_bid(200, 187, 9, 22), 1)    # Baltimore Ravens 2→1

    def test_fixture_aritmetica_do_alexthedawg(self):
        """A sheet real ($203) simulada SEM detecção (o que a run fez): os 4
        clamps caem nos keepers certos com os valores certos e o total fecha em
        $196 — exatamente o gravado no board em 12/08."""
        gasto, picks, clamps = 0, 0, []
        for i, preco in enumerate(ALEX_SHEET):
            efetivo = min(preco, max_bid(200, gasto, picks, 22))
            if efetivo < preco:
                clamps.append((i, preco, efetivo))
            gasto += efetivo
            picks += 1
        self.assertEqual(clamps, [(6, 6, 5), (7, 4, 1), (8, 3, 1), (9, 2, 1)])
        self.assertEqual(gasto, 196)

    def test_com_deteccao_os_clampados_sao_pulados(self):
        """COM o FIX10 (clamp → keeper pulado, nada gravado) a dinâmica muda:
        pular o Keenan ($6) libera teto p/ o Croskey ($4 ≤ $5). O modelo prevê
        16 designados a preço de SHEET ($194) + 2 bloqueados (Keenan $6 e Kaleb
        $3) — zero preço errado no board."""
        gasto, picks, bloqueados, designados = 0, 0, [], 0
        for i, preco in enumerate(ALEX_SHEET):
            if preco > 1 and preco > max_bid(200, gasto, picks, 22):
                bloqueados.append((i, preco))
                continue
            designados += 1
            gasto += preco
            picks += 1
        self.assertEqual(bloqueados, [(6, 6), (8, 3)])
        self.assertEqual((designados, gasto), (16, 194))


class TestDraftBudgetSlots(unittest.TestCase):

    def test_settings_do_draft(self):
        d = {"settings": {"budget": 300, "rounds": 25}}
        self.assertEqual(draft_budget_slots(d), (300, 25))

    def test_defaults_da_fantasma(self):
        self.assertEqual(draft_budget_slots({}), (200, 22))
        self.assertEqual(draft_budget_slots(None), (200, 22))
        self.assertEqual(draft_budget_slots({"settings": {"budget": "x"}}),
                         (200, 22))


class TestConferenceReport(unittest.TestCase):
    """FIX10 — a conferência APONTA os picks: o $196/$203 do AlexTheDawg
    denunciou QUE divergia, não QUAIS (os 4 só apareceram no validate)."""

    def _rows(self):
        return [{"sid": "1479", "name": "Keenan Allen", "salary": 6},
                {"sid": "12533", "name": "Jacory Croskey-Merritt", "salary": 4},
                {"sid": "4144", "name": "Jonnu Smith", "salary": 1}]

    def test_divergentes_nomeados_com_esperado_e_gravado(self):
        """Contagem bate (3/3), soma diverge — o caso exato da run: o relatório
        nomeia QUEM divergiu, com sheet × board."""
        picks = [pick("1479", 12, "5"), pick("12533", 12, "1"),
                 pick("4144", 12, "1")]
        c = conference_report(picks, self._rows())
        self.assertEqual((c["picks_no_board"], c["keepers_na_sheet"]), (3, 3))
        self.assertEqual((c["total_no_board"], c["total_na_sheet"]), (7, 11))
        self.assertEqual(c["divergentes"], [
            {"sid": "1479", "name": "Keenan Allen", "sheet": 6, "board": 5},
            {"sid": "12533", "name": "Jacory Croskey-Merritt",
             "sheet": 4, "board": 1}])
        self.assertEqual(c["faltantes"], [])

    def test_bloqueado_por_teto_sai_da_expectativa(self):
        """Keeper pulado por teto não é divergência nem faltante — vai em campo
        próprio e a conta fecha sem ele."""
        picks = [pick("12533", 12, "4"), pick("4144", 12, "1")]
        c = conference_report(picks, self._rows(), excluidos=["1479"])
        self.assertEqual((c["picks_no_board"], c["keepers_na_sheet"]), (2, 2))
        self.assertEqual((c["total_no_board"], c["total_na_sheet"]), (5, 5))
        self.assertEqual(c["divergentes"], [])
        self.assertEqual(c["bloqueados_excluidos"], ["1479"])

    def test_faltante_e_nomeado(self):
        picks = [pick("1479", 12, "6")]
        c = conference_report(picks, self._rows())
        self.assertEqual(c["picks_no_board"], 1)
        self.assertEqual([m["name"] for m in c["faltantes"]],
                         ["Jacory Croskey-Merritt", "Jonnu Smith"])

    def test_pick_sem_amount_nao_e_divergencia(self):
        """amount None = não conferível (mesma regra da idempotência)."""
        picks = [{"player_id": "4144", "draft_slot": 12}]
        c = conference_report(picks, [self._rows()[2]])
        self.assertEqual(c["divergentes"], [])
        self.assertEqual(c["picks_no_board"], 1)


class TestCampaignSummaryBloqueados(unittest.TestCase):

    def test_bloqueados_contados_por_keeper(self):
        """FIX10: o resumo soma os contadores por time (teto pula o keeper);
        times_bloqueados segue vindo do status."""
        times = [{"status": BLOQUEADO_TETO, "designados": 16,
                  "bloqueados_teto": 2},
                 {"status": "ok", "designados": 20, "bloqueados_teto": 0}]
        r = campaign_summary(times)
        self.assertEqual(r["bloqueados_teto"], 2)
        self.assertEqual(r["times_bloqueados"], 1)
        self.assertEqual(r["times_ok"], 1)


# ══════════════════════════════════════════════════════════════════════════════
# 4f. FIX11 — rótulo multi-posição ("DB,WR"): o caso Travis Hunter RESOLVIDO
# ══════════════════════════════════════════════════════════════════════════════

# O micro-probe do owner (12/08, screenshots) fechou a pendência OFF26-24-HUNTER:
# o Hunter ESTÁ no pool da sala (rank 167, tabs All e WR, "+" habilitado) — a
# linha existia e foi DESCARTADA pelo filtro de posição: o rótulo dela é "DB,WR"
# (espelho de fantasy_positions da API, DB primeiro) e a eleição exigia
# igualdade com o "WR" da sheet. Único multi-posição entre os 237 keepers.
HUNTER_TEXT = "167 Travis Hunter DB,WR JAX $1 - 0.0 0.0 0 0 0 0 0 0 0 0 0"


class TestPositionMatches(unittest.TestCase):
    """FIX11 — pertencimento ao conjunto do rótulo, não igualdade com o rótulo
    inteiro. Pertencimento NÃO é afrouxamento."""

    def test_membro_do_rotulo_casa(self):
        self.assertTrue(position_matches("DB,WR", "WR"))
        self.assertTrue(position_matches("DB,WR", "DB"))
        self.assertTrue(position_matches("db,wr", "wr"))   # caixa

    def test_nao_membro_nao_casa(self):
        """Sheet "QB" contra a linha do Hunter → 0 candidatos (a regra não
        afrouxou)."""
        self.assertFalse(position_matches("DB,WR", "QB"))
        self.assertFalse(position_matches("DB,WR", "TE"))

    def test_igualdade_comum_segue_valendo(self):
        self.assertTrue(position_matches("WR", "WR"))
        self.assertTrue(position_matches("D/ST", "D/ST"))  # rótulo único, pré-split

    def test_vazios_nao_casam(self):
        self.assertFalse(position_matches("", "WR"))
        self.assertFalse(position_matches("DB,WR", ""))


class TestParseResultRowMultiPos(unittest.TestCase):
    """FIX11 — o parse (família FIX5) extrai o rótulo "DB,WR" ÍNTEGRO do
    innerText real, sem quebrá-lo em posição+sigla."""

    def test_rotulo_integro_com_sigla(self):
        self.assertEqual(parse_result_row("DB,WR" + NL + "JAX", "JAX"),
                         ("DB,WR", "JAX"))

    def test_string_unica_do_dom(self):
        self.assertEqual(parse_result_row("DB,WR JAX"), ("DB,WR", "JAX"))

    def test_injury_status_tolerado_no_multi(self):
        self.assertEqual(parse_result_row("DB,WR" + NL + "JAX" + NL + "QUES",
                                          "JAX"),
                         ("DB,WR", "JAX"))

    def test_compound_sem_membro_do_vocabulario_nao_e_posicao(self):
        """Um compound sem NENHUMA parte no vocabulário não vira rótulo."""
        self.assertEqual(parse_result_row("A,B" + NL + "JAX", "JAX")[0], "")


class TestFix11Hunter(unittest.TestCase):
    """A fixture literal do probe: a linha existia — agora conta como candidato."""

    def test_fixture_do_probe_da_um_candidato(self):
        """"Travis Hunter" · "DB,WR" · JAX, sheet WR → exatamente 1 candidato;
        a designação prossegue."""
        self.assertEqual(select_candidate_rows_named(
            [("DB,WR", "JAX")], "WR", [HUNTER_TEXT], "Travis Hunter"), [0])

    def test_sheet_qb_contra_a_mesma_linha_da_zero(self):
        self.assertEqual(select_candidate_rows_named(
            [("DB,WR", "JAX")], "QB", [HUNTER_TEXT], "Travis Hunter"), [])

    def test_busca_por_hunter_com_outras_linhas(self):
        """O probe por "hunter" devolveu múltiplas linhas — só a dele casa nome
        E posição."""
        parsed = [("DB,WR", "JAX"), ("WR", "ARI"), ("RB", "CHI")]
        texts = [HUNTER_TEXT,
                 "5 Marvin Harrison WR ARI $22 11",
                 "80 Hunter Renfrow RB CHI $1 -"]
        self.assertEqual(select_candidate_rows_named(
            parsed, "WR", texts, "Travis Hunter"), [0])

    def test_homonimos_verdadeiros_seguem_abortando(self):
        """⛔ Critério intacto: dois "Travis Hunter" cujos rótulos CONTÊM a
        posição da sheet → 2 candidatos → quem chama aborta."""
        parsed = [("DB,WR", "JAX"), ("WR", "")]
        texts = [HUNTER_TEXT, "900 Travis Hunter WR $1 -"]
        self.assertEqual(len(select_candidate_rows_named(
            parsed, "WR", texts, "Travis Hunter")), 2)

    def test_selecao_por_posicao_tambem_ve_o_multi(self):
        """select_candidate_rows (camada posição-só do FIX5) inclui a linha
        multi-posição — o pertencimento vive numa fonte única."""
        rows = [("QB", "TEN"), ("DB,WR", "JAX")]
        self.assertEqual(select_candidate_rows(rows, "WR"), [1])
        self.assertEqual(select_candidate_rows(rows, "QB"), [0])


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
        self.assertIn("JOIN DRAFT", str(config.FORBIDDEN_CLICK_LABELS))
        self.assertIn("CHANGE PLAYER", str(config.FORBIDDEN_CLICK_LABELS))  # FIX4
        self.assertIn("assert_allowed_click", self.board)

    def test_navegacao_por_coluna_nunca_nth_global(self):
        """FIX4: a célula vem da COLUNA do slot (.team-column nth(N-1) → .cell sem
        .drafted); índice global de célula não navega o board."""
        corpo = self.board.split("def _open_set_player_menu")[1].split("\ndef ")[0]
        self.assertIn("SEL_TEAM_COLUMN", corpo)
        self.assertIn("CELL_DRAFTED_CLASS", corpo)
        self.assertIn("choose_menu_item", corpo)       # decisão no núcleo puro
        self.assertNotIn("BOARD_CELL_SELECTOR", self.board)

    def test_fix12_ancora_por_owner_chega_ao_menu(self):
        """FIX12: o handle do slot (que o mapa já tem — sem chamada nova de API)
        atravessa cli → command_pick → _open_set_player_menu, e a decisão continua
        no núcleo puro. O rótulo observado é LOGADO sempre."""
        corpo = self.board.split("def _open_set_player_menu")[1].split("\ndef ")[0]
        self.assertIn("owner_handle=owner_handle", corpo)
        self.assertIn("menu_labels_seen", corpo)
        self.assertIn("menu_rotulo", corpo)            # evento no relatório
        cmd = self.board.split("def command_pick")[1].split("\ndef ")[0]
        self.assertIn("owner_handle=owner_handle", cmd)
        pop = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertIn("owner_handle=ancora", pop)
        self.assertIn("duplicate_handles", pop)        # handle repetido não prova

    def test_fix12_abort_de_time_nao_contamina_o_seguinte(self):
        """FIX12: o menu de contexto NÃO fecha com Escape (5 screenshots de
        21/08) — o abort fecha pelo underlay, e a abertura do time seguinte
        re-confere o estado antes de qualquer clique."""
        # o underlay que aparece no erro do Playwright interceptando os cliques
        self.assertIn("context-menu-underlay", config.SEL_MENU_UNDERLAY)
        self.assertIn("def _dismiss_context_menu", self.board)
        abre = self.board.split("def _open_set_player_menu")[1].split("\ndef ")[0]
        self.assertIn("_is_context_menu_open(page)", abre)   # guarda de entrada
        self.assertIn("_dismiss_context_menu(page)", abre)   # e no abort
        self.assertLess(abre.index("_dismiss_context_menu(page)"),
                        abre.index("raise BoardAbort(f\"Slot {team_slot}: {motivo}"))
        cmd = self.board.split("def command_pick")[1].split("\ndef ")[0]
        self.assertIn("_dismiss_context_menu(page)", cmd)    # e em erro cru

    def test_plus_clicado_e_o_da_linha_eleita(self):
        """FIX5: o "+" vem de rows.nth(idx) — a linha que o matcher elegeu, nunca
        a primeira; e a eleição passa pelo núcleo puro."""
        corpo = self.board.split("def _pick_search_result")[1].split("def _set_price")[0]
        self.assertIn("select_candidate_rows", corpo)
        self.assertIn("parse_result_row", corpo)
        self.assertIn("rows.nth(idx)", corpo)

    def test_ancora_e_o_modal_real_com_fallback_logado(self):
        """FIX7: a âncora é #modal[role=alertdialog] quando presente (o caso do
        abort — input resolvido FORA do dialog aberto — é impossível por
        construção: o escopo nasce do próprio #modal); a heurística de ancestral
        é FALLBACK e se anuncia no log. O modal certo é provado pelo header."""
        corpo = self.board.split("def _modal")[1].split("def _pick_search_result")[0]
        self.assertIn("config.SEL_MODAL", corpo)
        self.assertIn("modal_header_check", corpo)
        self.assertIn("ancestral_fallback", corpo)
        self.assertIn("NÃO abriu", corpo)              # espera de ESTADO nomeada
        # e a espera acontece antes de qualquer interação de busca
        pick = self.board.split("def _pick_search_result")[1].split("def _set_price")[0]
        self.assertIn("wait_open=True", pick)

    def test_busca_e_linhas_escopadas_ao_modal(self):
        """FIX6: nenhum locator GLOBAL de busca/linha sobrevive — tudo sai do
        container do modal (_modal), e o filtro é conferido ANTES do matching."""
        corpo = self.board.split("def _pick_search_result")[1].split("def _set_price")[0]
        self.assertIn("_modal(page", corpo)
        self.assertIn("modal.locator(config.SEL_SEARCH_INPUT", corpo)
        self.assertIn("modal.locator(config.SEL_RESULT_ROW", corpo)
        self.assertNotIn("page.locator(config.SEL_SEARCH_INPUT", corpo)
        self.assertNotIn("page.locator(config.SEL_RESULT_ROW", corpo)
        # o check do filtro vem antes da eleição
        self.assertLess(corpo.index("search_filter_check"),
                        corpo.index("select_candidate_rows"))

    def test_preco_escopado_ao_modal(self):
        corpo = self.board.split("def _set_price_and_confirm")[1].split("def ")[0]
        self.assertIn("_modal(page)", corpo)
        self.assertIn("modal.locator(", corpo)

    def test_f2b_idempotencia_primeiro_e_recheck(self):
        """F2b/FIX8: o populate classifica o LOTE (classify_team_keepers) ANTES
        do primeiro comando; a busca vazia cruza run própria → API → board local
        antes de abortar (tarefa 5)."""
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertLess(corpo.index("classify_team_keepers"),
                        corpo.index("command_pick(page"))
        self.assertIn("sumiu_da_busca_pos_comando", corpo)   # sinal da própria run
        self.assertIn("board_shows_designated", corpo)       # board local por último
        self.assertIn("EmptySearchResult", self.board)

    def test_fix8_assincrono_com_reconciliacao(self):
        """FIX8: comando SEM poll (pendente_confirmacao e segue); reconciliação
        POR TIME com teto generoso + reload no MEIO do teto (tarefa 7 — a visita
        como possível gatilho do cache); telemetria por keeper; pendente com
        board local designado NUNCA é re-comandado."""
        self.assertIn("def command_pick", self.board)
        rec = self.board.split("def reconcile_team")[1].split("def settle_pendentes")[0]
        self.assertIn("teto / 2", rec)                       # reload no meio
        self.assertIn("reload_do_board", rec)
        self.assertIn("segundos_apos_comando", rec)          # telemetria
        self.assertIn("apos_reload", rec)
        sett = self.board.split("def settle_pendentes")[1].split("def designate")[0]
        self.assertIn("post_teto_decision", sett)            # decisão no núcleo
        self.assertEqual(config.RECONCILE_TETO_SECONDS, 300)
        # populate comanda e SEGUE — o poll bloqueante por keeper morreu
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertIn("pendente de confirmação", corpo)
        self.assertIn("settle_pendentes", corpo)

    def test_f2b_teto_e_resultado_nao_erro(self):
        """FIX10 mudou o grão de propósito: o teto pula O KEEPER (nada gravado;
        o resto do time é alcançável — $1 sempre cabe na reserva), não aborta
        mais o time inteiro."""
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertIn("BLOQUEADO_TETO", corpo)
        self.assertIn("pulando o keeper", corpo)
        self.assertIn('res["bloqueados_teto"] += 1', corpo)
        # e o exit code trata bloqueado_teto como não-falha
        self.assertIn('("ok", BLOQUEADO_TETO, "sem_keepers_na_sheet")', corpo)

    def test_f2b_falha_aborta_o_time_sem_contaminar(self):
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertIn("abortando o time", corpo)
        self.assertIn("o que assentou permanece", corpo)

    def test_f2b_juiz_e_a_auditoria(self):
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertIn("keeper_audit", corpo)
        self.assertIn("juiz", corpo)

    def test_f2b_populate_nao_toca_reset_ou_start(self):
        """RESET é ato do owner — o script nunca o executa."""
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertNotIn("RESET DRAFT", corpo)
        self.assertNotIn("START DRAFT", corpo)

    def test_cli_nao_crasha_no_handler(self):
        """FIX4: ok nasce antes do try e QUALQUER exceção vira abort padrão
        (o UnboundLocalError real engoliu o abort limpo)."""
        corpo = self.cli.split("def cmd_designate")[1]
        self.assertLess(corpo.index("ok = False"), corpo.index("try:"))
        self.assertIn("except Exception as e:", corpo)

    def test_identidade_por_url_nao_por_texto(self):
        """FIX 11/08: o gate é url_guard(page.url, draft_id); o título da página é
        log informativo — LEAGUE_NAME não pode voltar a ser gate no driver."""
        corpo = self.board.split("def open_board")[1].split("\ndef ")[0]
        self.assertIn("url_guard(page.url, draft_id)", corpo)
        self.assertIn("informativo", corpo)
        self.assertNotIn("config.LEAGUE_NAME", corpo)

    def test_canal_chrome_real_nunca_chromium_de_teste(self):
        """FIX2: hCaptcha recusa o Chromium de teste — launch pelo Chrome real
        (channel), com erro ACIONÁVEL se ausente; nunca fallback silencioso. As
        flags são as mitigações padrão p/ o desafio renderizar ao humano — nada
        resolve/burla captcha."""
        self.assertEqual(config.CHROME_CHANNEL, "chrome")
        corpo = self.board.split("def open_board")[1].split(chr(92) + "ndef ")[0]
        corpo = self.board.split("def open_board")[1]
        self.assertIn("channel=config.CHROME_CHANNEL", corpo)
        self.assertIn("Instale o Google Chrome", corpo)
        self.assertIn("AutomationControlled", corpo)
        # nada de serviço/lib de resolução de captcha — a solução é humana
        for proibido in ("2captcha", "anticaptcha", "capsolver", "hcaptcha_solver"):
            self.assertNotIn(proibido, self.board.lower())

    def test_login_espera_nunca_clica_join(self):
        """1ª vida do perfil: espera o login manual; JOIN DRAFT jamais é clicado."""
        corpo = self.board.split("def _wait_for_login_if_needed")[1].split("\ndef ")[0]
        self.assertIn("input(", corpo)                 # Enter do owner
        self.assertIn("LOGIN_WAIT_SECONDS", corpo)     # fallback sem stdin
        self.assertNotIn(".click()", corpo)            # nenhum clique no fluxo de login

    def test_guarda_roda_antes_do_browser(self):
        """A guarda de liga vem ANTES de abrir o browser no open_board."""
        corpo = self.board.split("def open_board")[1].split("\ndef ")[0]
        self.assertLess(corpo.index("league_guard"), corpo.index("sync_playwright()"))

    def test_verdade_e_a_api_nunca_o_toast(self):
        """FIX8: o driver decide por fetch_picks + split_settled (reconciliação
        assíncrona); o toast só entra como RECUSA nomeada (teto) — nunca como
        veredito de sucesso."""
        self.assertIn("fetch_picks", self.board)
        self.assertIn("split_settled", self.board)
        self.assertIn("reconcile_team", self.board)

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

    # ── FIX9 (12/08): higiene de modal em TODO abort + nada de traceback cru ────

    def test_fix9_abort_de_comando_limpa_o_modal(self):
        """FIX9: QUALQUER exceção dentro do command_pick fecha menu/modal antes
        de propagar — o abort do anti-homônimo de 12/08 deixou o SET PLAYER
        aberto e o clique do time seguinte foi interceptado até TimeoutError."""
        corpo = self.board.split("def command_pick")[1].split("\ndef ")[0]
        self.assertIn("except Exception", corpo)
        self.assertIn("_dismiss_modal(page)", corpo)
        self.assertIn("raise", corpo)

    def test_fix9_estado_sujo_detectado_antes_do_clique(self):
        """FIX9: verificação defensiva ANTES do primeiro clique de cada abertura
        de menu — modal residual → limpar; não limpou → abort barulhento, nunca
        clicar através."""
        corpo = self.board.split("def _open_set_player_menu")[1].split("\ndef ")[0]
        self.assertIn("_is_modal_open(page)", corpo)
        self.assertIn("_dismiss_modal(page)", corpo)
        self.assertIn("estado SUJO", corpo)
        self.assertLess(corpo.index("_is_modal_open"), corpo.index(".click()"))

    def test_fix9_candidato_exige_nome_alem_da_posicao(self):
        """FIX9: a eleição passa por select_candidate_rows_named (posição exata
        + nome buscado) — a busca fuzzy do Sleeper devolve OUTROS nomes (Malik
        Willis → Malik Williams ×2 + Hajj-Malik Williams, 12/08)."""
        corpo = self.board.split("def _pick_search_result")[1].split("def _set_price")[0]
        self.assertIn("select_candidate_rows_named", corpo)
        self.assertIn("player_name", corpo)
        # e o texto integral da linha vai ao relatório como evidência
        self.assertIn("inner_text()", corpo)

    def test_fix9_populate_nunca_vaza_traceback_cru(self):
        """FIX9: exceção crua num keeper → abort padrão do TIME (screenshot +
        evento) e a campanha segue; crua fora do loop → abort padrão da CAMPANHA
        (abort_campanha no relatório); falha do open_board → mensagem limpa."""
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertGreaterEqual(corpo.count("except Exception"), 3)
        self.assertIn("abort_campanha", corpo)
        self.assertIn("abort_slot", corpo)
        self.assertIn("ERRO ao abrir o board", corpo)
        # o time entra no relatório ANTES de processar — falha não o apaga
        self.assertLess(corpo.index("team_results.append(res)"),
                        corpo.index("classify_team_keepers"))

    def test_fix9_settle_nao_deixa_cru_derrubar_o_time(self):
        """FIX9: no settle_pendentes, exceção CRUA no re-comando tem o mesmo
        destino do BoardAbort — falha DO KEEPER, preservando o resto."""
        sett = self.board.split("def settle_pendentes")[1].split("def designate")[0]
        self.assertIn("except Exception as e", sett)
        self.assertIn("falhas", sett)

    # ── FIX10 (12/08): read-back do preço ANTES do SET + conferência que aponta ─

    def test_fix10_readback_antes_do_set_player(self):
        """FIX10: depois de digitar, o valor EFETIVO do input é lido de volta e
        julgado no núcleo puro ANTES do confirm.click(); clamp → _dismiss_modal
        + bloqueado_teto com os números no relatório, NADA gravado."""
        corpo = self.board.split("def _set_price_and_confirm")[1].split("\ndef ")[0]
        self.assertIn("input_value", corpo)
        self.assertIn("price_readback_decision", corpo)
        self.assertIn("clamp_do_input", corpo)
        self.assertIn("preco_efetivo", corpo)
        self.assertIn("_dismiss_modal(page)", corpo)
        self.assertIn("return BLOQUEADO_TETO", corpo)
        self.assertLess(corpo.index("input_value"), corpo.index("confirm.click()"))
        # e a recusa síncrona segue coberta no command_pick (as DUAS caras)
        cmd = self.board.split("def command_pick")[1].split("\ndef ")[0]
        self.assertIn("recusa_sincrona", cmd)
        self.assertIn("is_budget_block", cmd)

    def test_fix10_teto_pula_o_keeper_e_conferencia_exclui(self):
        """FIX10: teto no populate → keeper pulado (continue), contador por
        time, sid excluído da conferência; a conferência nomeia divergentes e
        faltantes no stdout e no relatório."""
        corpo = self.cli.split("def cmd_populate")[1].split("def main")[0]
        self.assertIn("bloqueados.append(r[\"sid\"])", corpo)
        self.assertIn("conference_report", corpo)
        self.assertIn("excluidos=bloqueados", corpo)
        self.assertIn("preço divergente", corpo)
        self.assertIn("AUSENTE do board", corpo)
        self.assertIn("divergentes", corpo)
        # o max bid do modelo entra como ANOTAÇÃO no comando
        self.assertIn("expected_max=max_bid(", corpo)
        # e não existe segunda definição de conferência no CLI
        self.assertNotIn("def _team_conference", self.cli)


if __name__ == "__main__":
    unittest.main(verbosity=2)
