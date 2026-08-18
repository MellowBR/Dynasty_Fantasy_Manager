# -*- coding: utf-8 -*-
"""
roster_excess_test.py — UX25: excesso de roster vira obrigação explícita no card do Hub.

O truncamento que motivou o item: `empty_spots = max(0, MAX_ROSTER − N)` — time com 27
jogadores mostra "Slots livres 0", indistinguível do time exatamente cheio. A obrigação
usa a contagem de COMPOSIÇÃO (regulamento 1.3): limite = MAX_ROSTER=22 ATIVOS; os até 2
IR ficam fora da conta. ⛔ Nenhuma régua de cap/bid muda — só contagem de exibição.

`_build_team_card` é pura (sem queries) — testável direto com SimpleNamespace.
"""

import unittest
from types import SimpleNamespace


def _player(salary=5, ir=False, dropped=False):
    return SimpleNamespace(salary=salary, is_dropped=dropped, is_on_ir=ir,
                           sleeper_player_id=None)


def _card(players):
    from routes.league import _build_team_card
    team = SimpleNamespace(id=1, name="T", owner_name="o", owner_avatar="")
    return _build_team_card(team, None, 0, players, {}, my_team_id=None,
                            show_projection=False)


class TestObrigacaoDeCorte(unittest.TestCase):
    def test_excesso_vira_obrigacao(self):
        c = _card([_player() for _ in range(25)])
        self.assertEqual((c["cut_needed"], c["active_count"], c["roster_limit"]),
                         (3, 25, 22))

    def test_ir_fora_da_conta(self):
        """22 ativos + 2 IR é composição LEGAL (regulamento 1.3) — zero obrigação."""
        players = [_player() for _ in range(22)] + [_player(ir=True), _player(ir=True)]
        c = _card(players)
        self.assertEqual((c["cut_needed"], c["active_count"], c["ir_count"]), (0, 22, 2))

    def test_excesso_com_ir_conta_so_ativos(self):
        players = [_player() for _ in range(23)] + [_player(ir=True)]
        c = _card(players)
        self.assertEqual((c["cut_needed"], c["active_count"], c["ir_count"]), (1, 23, 1))

    def test_limite_exato_e_abaixo_zero_ruido(self):
        self.assertEqual(_card([_player() for _ in range(22)])["cut_needed"], 0)
        self.assertEqual(_card([_player() for _ in range(20)])["cut_needed"], 0)

    def test_reguas_de_cap_intocadas(self):
        """O card estourado mantém bid/slots exatamente como a régua sempre deu —
        a obrigação é campo NOVO, não substituição."""
        from salary_engine import draft_budget
        players = [_player() for _ in range(25)]
        c = _card(players)
        regua = draft_budget(players)
        self.assertEqual(c["slots"], regua["empty_spots"])       # segue 0 (truncado)
        self.assertEqual(c["bid_max"], int(regua["usable_draft_budget"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
