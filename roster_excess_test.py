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


class TestObrigacaoVivaNoProjector(unittest.TestCase):
    """UX25-b: a MESMA régua, viva no cap projector — o POST /budget (que já roda a
    cada toggle) devolve `roster {active, ir, limit, cut_needed}`; o JS só exibe."""

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from models import db
        from routes.salary import salary_bp
        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["LOGIN_DISABLED"] = True
        cls.app.config["TESTING"] = True
        db.init_app(cls.app)
        cls.app.register_blueprint(salary_bp)
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        db.create_all()
        cls.client = cls.app.test_client()

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
        self.team = Team(name="Trust The Process")
        db.session.add(self.team)
        db.session.flush()
        self.players = []
        for i in range(24):                      # 24 ativos
            p = Player(name=f"P{i}", position="WR", team_id=self.team.id, salary=5,
                       contract_year=1, acquisition_type="auction_draft")
            db.session.add(p)
            self.players.append(p)
        self.ir = Player(name="Machucado", position="RB", team_id=self.team.id,
                         salary=5, contract_year=1, acquisition_type="auction_draft",
                         is_on_ir=True)          # +1 IR (fora da conta)
        db.session.add(self.ir)
        db.session.commit()

    def _budget(self, kept_ids, rookies=()):
        r = self.client.post("/api/cap_projector/Trust%20The%20Process/budget",
                             json={"kept_ids": kept_ids, "rookie_sids": list(rookies),
                                   "projected": False})
        self.assertEqual(r.status_code, 200)
        return r.get_json()

    def test_excesso_no_cenario_cheio(self):
        d = self._budget([p.id for p in self.players] + [self.ir.id])
        self.assertEqual(d["roster"], {"active": 24, "ir": 1, "limit": 22,
                                       "cut_needed": 2})

    def test_toggles_regularizam_ao_vivo(self):
        kept = [p.id for p in self.players][:-2] + [self.ir.id]   # corta 2
        d = self._budget(kept)
        self.assertEqual((d["roster"]["active"], d["roster"]["cut_needed"]), (22, 0))
        self.assertEqual(d["roster"]["ir"], 1, "+1 IR visível e fora da conta")

    def test_rookie_do_cenario_ocupa_vaga_de_ativo(self):
        from models import db, upsert_rookie_espn, set_config
        set_config("current_season", "2026")
        set_config("rollover_done", "true")     # alvo = 2026 (UX23)
        upsert_rookie_espn(2026, "9901", "Rookie X", "RB", "DAL",
                           espn_raw=10.0, espn_adjusted=12.0, in_class=True)
        db.session.commit()
        kept = [p.id for p in self.players][:22]                  # 22 exatos
        d = self._budget(kept, rookies=["9901"])
        self.assertEqual((d["roster"]["active"], d["roster"]["cut_needed"]), (23, 1))

    def test_regua_do_budget_intocada(self):
        """D9: o campo novo é aditivo — o dict `budget` continua com as chaves e a
        aritmética de sempre (folha = 25 × $5, incluindo o IR — régua OFF26-16)."""
        d = self._budget([p.id for p in self.players] + [self.ir.id])
        self.assertEqual(d["budget"]["keeper_salaries"], 125)
        self.assertEqual(d["budget"]["empty_spots"], 0)   # segue truncado — semântica de auction


if __name__ == "__main__":
    unittest.main(verbosity=2)
