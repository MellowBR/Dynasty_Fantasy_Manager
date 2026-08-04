"""
cap_regua_test.py — a REGRA ÚNICA de folha salarial (OFF26-16).

Decisão do owner (04/08/2026), explícita e final: **jogador no IR conta no cap hit como
qualquer outro**. Não existem duas réguas — existe UMA folha salarial, que inclui todos os
jogadores do time (ativos e IR), e é a mesma em toda tela, todo cálculo e todo contexto.

Isto REVERTE a F2 do OFF26-14 (`f809a68`), que rotulou duas réguas ("cap ativo" × "folha
total") em vez de unificá-las. O racional daquela decisão — "os dois números têm sentidos
diferentes e ambos são legítimos" — caiu: pela regra do owner, o número sem IR não mede nada.

Estes testes foram escritos ANTES da unificação (pré-requisito duro registrado no OFF26-16:
a cobertura dessas somas era ZERO, e unificar sem rede estava vetado pelo próprio item).

Caso de referência em todos os cenários — `🕯️🕯️ achane 🕯️🕯️`, medido em produção:
    22 ativos = $186  +  2 em IR (Penix $1, Travis Hunter $8) = $9   →   folha $195
    restante = 200 − 195 = $5
"""

import re
import unittest
from pathlib import Path

from salary_engine import roster_salary, SALARY_CAP


BASE_DIR = Path(__file__).resolve().parent


class FakePlayer:
    """Duck-type do `Player` para os núcleos puros (mesmo padrão do salary_engine_test)."""

    def __init__(self, salary, is_on_ir=False, is_dropped=False, sleeper_player_id=None):
        self.salary = salary
        self.is_on_ir = is_on_ir
        self.is_dropped = is_dropped
        self.sleeper_player_id = sleeper_player_id
        self.position = "WR"
        self.dynasty_value = 0


def achane_roster():
    """22 ativos somando $186 + 2 em IR somando $9 = folha $195."""
    ativos = [FakePlayer(9) for _ in range(20)]        # $180
    ativos += [FakePlayer(3), FakePlayer(3)]           # $186 em 22 ativos
    ir = [FakePlayer(1, is_on_ir=True), FakePlayer(8, is_on_ir=True)]   # $9
    return ativos + ir


# ══════════════════════════════════════════════════════════════════════════════
# 1. O núcleo puro — a única definição de folha
# ══════════════════════════════════════════════════════════════════════════════

class TestRosterSalary(unittest.TestCase):

    def test_ir_conta_na_folha(self):
        """O coração da decisão: IR entra na soma como qualquer outro."""
        self.assertEqual(roster_salary(achane_roster()), 195)

    def test_ir_sozinho_conta(self):
        self.assertEqual(roster_salary([FakePlayer(8, is_on_ir=True)]), 8)

    def test_dropado_nao_conta(self):
        """`is_dropped` segue sendo o ÚNICO filtro — inclusive para quem está em IR."""
        players = [
            FakePlayer(10),
            FakePlayer(50, is_dropped=True),
            FakePlayer(7, is_on_ir=True, is_dropped=True),
        ]
        self.assertEqual(roster_salary(players), 10)

    def test_roster_vazio(self):
        self.assertEqual(roster_salary([]), 0)

    def test_time_sem_ir_nao_muda(self):
        """Os 9 times sem IR precisam ver exatamente o número de antes."""
        players = [FakePlayer(s) for s in (50, 40, 30, 20, 10)]
        self.assertEqual(roster_salary(players), 150)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Camada ORM — Team.total_salary() / cap_remaining() / to_dict()
# ══════════════════════════════════════════════════════════════════════════════

class TestTeamSalaryORM(unittest.TestCase):
    """Exercita o modelo real contra SQLite em memória (sem tocar o dynasty.db)."""

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
        self.team = Team(name="🕯️🕯️ achane 🕯️🕯️")
        db.session.add(self.team)
        db.session.commit()
        for p in achane_roster():
            db.session.add(Player(name="x", position="WR", team_id=self.team.id,
                                  salary=p.salary, is_on_ir=p.is_on_ir,
                                  is_dropped=p.is_dropped))
        # um dropado, para provar que segue fora
        db.session.add(Player(name="dropado", position="WR", team_id=self.team.id,
                              salary=99, is_dropped=True))
        db.session.commit()

    def test_folha_inclui_ir(self):
        self.assertEqual(self.team.total_salary(), 195)

    def test_cap_remaining_sobre_a_folha(self):
        """Caso concreto da validação: achane → $5 restantes, não $14."""
        self.assertEqual(self.team.cap_remaining(), 5)
        self.assertEqual(self.team.cap_remaining(), SALARY_CAP - 195)

    def test_to_dict_expoe_a_folha_unica(self):
        d = self.team.to_dict()
        self.assertEqual(d["salary_total"], 195)
        self.assertEqual(d["cap_remaining"], 5)

    def test_nao_existe_mais_regua_paralela(self):
        """`active_salary` mentia (excluía IR) — não pode ressuscitar sob nenhum nome."""
        from models import Team
        self.assertFalse(hasattr(Team, "active_salary"))
        self.assertFalse(hasattr(Team, "folha_total"))


# ══════════════════════════════════════════════════════════════════════════════
# 3. Card do League Hub — núcleo sem query, testável direto
# ══════════════════════════════════════════════════════════════════════════════

class TestLeagueCard(unittest.TestCase):

    def _card(self, players):
        from routes.league import _build_team_card

        class FakeTeam:
            id = 10
            name = "🕯️🕯️ achane 🕯️🕯️"
            owner_name = "gabrieldiinis"
            owner_avatar = ""
        return _build_team_card(FakeTeam(), None, 3, players, {}, my_team_id=None)

    def test_cap_used_inclui_ir(self):
        self.assertEqual(self._card(achane_roster())["cap_used"], 195)

    def test_cap_space_sobre_a_folha(self):
        self.assertEqual(self._card(achane_roster())["cap_space"], 5)

    def test_sem_chaves_da_regua_dupla(self):
        """A F2 acrescentou ir_cap/folha_total/folha_space ao card — saem na unificação."""
        card = self._card(achane_roster())
        for k in ("folha_total", "folha_space", "ir_cap"):
            self.assertNotIn(k, card)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Guarda de regressão — a réplica não pode voltar
# ══════════════════════════════════════════════════════════════════════════════

class TestSemReplicaDeFolha(unittest.TestCase):
    """A F1 do OFF26-14 mediu SEIS definições da régua sem IR (o helper + 5 somas
    inline reescritas à mão). Este teste existe para que a sétima não apareça: nenhum
    `sum` de salário pode filtrar `is_on_ir`."""

    SOURCES = ["models.py", "app.py", "sync_sleeper.py"] + \
              [f"routes/{n}.py" for n in
               ("roster", "league", "admin", "trades", "salary", "cuts")]

    # sum(...) que mencione salary e is_on_ir na mesma expressão
    PADRAO = re.compile(r"sum\((?:(?!\)).)*salary(?:(?!\)).)*is_on_ir", re.S)
    PADRAO_INV = re.compile(r"sum\((?:(?!\)).)*is_on_ir(?:(?!\)).)*salary", re.S)

    def test_nenhuma_soma_de_folha_filtra_ir(self):
        ofensores = []
        for rel in self.SOURCES:
            src = (BASE_DIR / rel).read_text(encoding="utf-8")
            if self.PADRAO.search(src) or self.PADRAO_INV.search(src):
                ofensores.append(rel)
        self.assertEqual(ofensores, [], f"soma de folha filtrando IR em: {ofensores}")

    def test_active_salary_nao_existe_no_codigo(self):
        """O nome mentia. Removido — não pode voltar nem como chave de payload."""
        ofensores = [rel for rel in self.SOURCES
                     if "active_salary" in (BASE_DIR / rel).read_text(encoding="utf-8")]
        self.assertEqual(ofensores, [], f"`active_salary` ressuscitou em: {ofensores}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
