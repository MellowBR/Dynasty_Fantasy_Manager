"""
cap_projetado_test.py — o cap PROJETADO das telas de liga (L3, 13/08/2026).

O L3 levou para a `/league` (12 cards) e para o `/team/<id>` o agregado que só existia
no Cap Projector, time a time. A composição que produz esse agregado — **salário-base
por jogador → roster sintético → `draft_budget`** — vivia INLINE no POST `/budget`;
virou o helper único `routes.salary.compose_budget`, com três consumidores.

O que esta suíte protege:

1. **A composição** (`compose_budget`) — as duas bases (projetada e corrente/D9), os
   salários extras do cenário DP2 e o dropado fora da conta.
2. **O card e o breakdown** — projeção coerente com a composição, e o gate de fase.
3. ⛔ **A réplica não pode voltar.** O [[F10]] já matou uma agregação de budget
   replicada (em JS, no cap projector); o L3 seria a ocasião perfeita para criar a
   segunda (em `league.py`). Guarda estática: nenhum roster sintético fora do helper.
4. ⛔ **O Bid Máximo NÃO muda de base.** É corrente de propósito — é o mesmo número
   que a keeper sheet publica (`fa_budget`, D4 do [[OFF26-2]]). Trocá-lo por projeção
   quebraria a coerência tela × sheet, e é um erro fácil de cometer numa tela que
   agora exibe as duas grandezas lado a lado.
5. **Nenhum ano literal** nas superfícies de projeção — todo rótulo deriva da season
   corrente, senão a tela mente no primeiro rollover.
"""

import re
import unittest
from pathlib import Path

from salary_engine import (
    SALARY_CAP, MAX_ROSTER, draft_budget, project_next_salary,
)
from routes.salary import compose_budget

BASE_DIR = Path(__file__).resolve().parent


class FakePlayer:
    """Duck-type do `Player` (mesmo padrão do salary_engine_test / cap_regua_test).
    Carrega o que a projeção lê: salário, ano de contrato, aquisição e ESPN ajustado."""

    def __init__(self, salary, contract_year=1, espn_ref_value=0.0,
                 acquisition_type="auction_draft", is_dropped=False, is_on_ir=False):
        self.salary = salary
        self.contract_year = contract_year
        self.espn_ref_value = espn_ref_value
        self.acquisition_type = acquisition_type
        self.is_dropped = is_dropped
        self.is_on_ir = is_on_ir
        self.position = "WR"
        self.sleeper_player_id = None
        self.dynasty_value = 0


def roster_misto():
    """Elenco com as três trilhas de projeção vivas ao mesmo tempo:
    valorização (ano 2), renovação (fim do ano 4) e waiver/FA ano 2 (0,8 × ESPN)."""
    return [
        FakePlayer(10, contract_year=2, espn_ref_value=48.0),   # VALORIZAÇÃO → 24
        FakePlayer(30, contract_year=4, espn_ref_value=36.0),   # renovação   → 36
        FakePlayer(1, contract_year=1, espn_ref_value=20.0,
                   acquisition_type="free_agent"),              # waiver ano 2 → 16
        FakePlayer(5, contract_year=1, espn_ref_value=0.0),     # sem ESPN → mantém 5
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 1. A composição — fonte única do agregado projetado
# ══════════════════════════════════════════════════════════════════════════════

class TestComposeBudget(unittest.TestCase):

    def test_base_projetada_é_project_next_salary(self):
        """A folha projetada é a soma das projeções individuais — nem mais, nem menos."""
        players = roster_misto()
        esperado = sum(project_next_salary(p) for p in players)
        self.assertEqual(compose_budget(players)["keeper_salaries"], esperado)
        self.assertEqual(esperado, 24 + 36 + 16 + 5)

    def test_base_corrente_quando_projected_false(self):
        """D9 do [[OFF26-1]]: pós-rollover o salário armazenado já está valorizado."""
        players = roster_misto()
        b = compose_budget(players, projected=False)
        self.assertEqual(b["keeper_salaries"], 10 + 30 + 1 + 5)

    def test_as_duas_bases_divergem_de_verdade(self):
        """Se convergissem, o teste acima não provaria nada."""
        players = roster_misto()
        self.assertNotEqual(compose_budget(players)["keeper_salaries"],
                            compose_budget(players, projected=False)["keeper_salaries"])

    def test_agregação_é_do_draft_budget(self):
        """⛔ Nenhuma aritmética de cap no helper: o payload é o do `draft_budget`,
        campo a campo, sobre os mesmos salários."""
        players = roster_misto()
        from types import SimpleNamespace
        equivalente = draft_budget([
            SimpleNamespace(salary=project_next_salary(p), is_dropped=False)
            for p in players])
        self.assertEqual(compose_budget(players), equivalente)

    def test_extra_salaries_ocupam_spot_e_custam(self):
        """Rookies do cenário DP2 entram como membros de roster adicionais."""
        players = roster_misto()
        sem = compose_budget(players)
        com = compose_budget(players, extra_salaries=[12, 3])
        self.assertEqual(com["keeper_salaries"], sem["keeper_salaries"] + 15)
        self.assertEqual(com["num_keepers"], sem["num_keepers"] + 2)
        self.assertEqual(com["empty_spots"], sem["empty_spots"] - 2)

    def test_dropado_fora_da_conta(self):
        """Mesmo filtro único do `roster_salary` ([[OFF26-16]]): só `is_dropped`."""
        players = roster_misto() + [FakePlayer(99, is_dropped=True)]
        self.assertEqual(compose_budget(players)["keeper_salaries"],
                         compose_budget(roster_misto())["keeper_salaries"])

    def test_ir_conta_na_projeção(self):
        """A régua é uma só e inclui o IR ([[OFF26-16]]) — projetada também."""
        players = roster_misto() + [FakePlayer(8, contract_year=2, is_on_ir=True)]
        self.assertEqual(compose_budget(players)["keeper_salaries"], 24 + 36 + 16 + 5 + 8)

    def test_roster_vazio(self):
        b = compose_budget([])
        self.assertEqual(b["keeper_salaries"], 0)
        self.assertEqual(b["empty_spots"], MAX_ROSTER)

    def test_over_cap_projetado_vem_pronto(self):
        """A tela não recalcula "estourou": a flag sai do helper."""
        caros = [FakePlayer(60, contract_year=2, espn_ref_value=160.0) for _ in range(3)]
        b = compose_budget(caros)                     # 3 × 80 = 240
        self.assertEqual(b["keeper_salaries"], 240)
        self.assertTrue(b["over_cap"])
        self.assertFalse(compose_budget(roster_misto())["over_cap"])


# ══════════════════════════════════════════════════════════════════════════════
# 2. Card da /league e breakdown do /team/<id>
# ══════════════════════════════════════════════════════════════════════════════

class FakeTeam:
    id = 7
    name = "Cangaceiros da Colina"
    owner_name = "MellowBR"
    owner_avatar = ""


class TestCardDaLiga(unittest.TestCase):

    def _card(self, players, show_projection=True):
        from routes.league import _build_team_card
        return _build_team_card(FakeTeam(), None, 5, players, {}, None, show_projection)

    def test_projeção_bate_com_a_composição(self):
        players = roster_misto()
        card = self._card(players)
        b = compose_budget(players)
        self.assertEqual(card["proj_used"], b["keeper_salaries"])
        self.assertEqual(card["proj_space"], SALARY_CAP - b["keeper_salaries"])
        self.assertEqual(card["proj_over_cap"], b["over_cap"])

    def test_atual_e_projetado_convivem(self):
        """A decisão do owner é exibir as DUAS grandezas — a atual não sai da tela."""
        card = self._card(roster_misto())
        self.assertEqual(card["cap_used"], 46)                  # 10+30+1+5, corrente
        self.assertEqual(card["cap_space"], SALARY_CAP - 46)
        self.assertEqual(card["proj_used"], 81)                 # 24+36+16+5, projetado

    def test_gate_fechado_zera_a_projeção(self):
        card = self._card(roster_misto(), show_projection=False)
        self.assertIsNone(card["proj_used"])
        self.assertIsNone(card["proj_space"])
        self.assertFalse(card["proj_over_cap"])
        self.assertEqual(card["cap_used"], 46)                  # o corrente permanece

    def test_over_cap_projetado_marcado_no_card(self):
        caros = [FakePlayer(60, contract_year=2, espn_ref_value=160.0) for _ in range(3)]
        card = self._card(caros)
        self.assertTrue(card["proj_over_cap"])
        self.assertLess(card["proj_space"], 0)

    def test_bid_maximo_nao_muda_de_base(self):
        """⛔ O Bid Máximo é CORRENTE — o mesmo número da keeper sheet (D4). A tela
        exibir projeção ao lado não pode contaminá-lo."""
        players = roster_misto()
        esperado = int(draft_budget(players)["usable_draft_budget"])
        for gate in (True, False):
            self.assertEqual(self._card(players, show_projection=gate)["bid_max"],
                             esperado)
        # e é MESMO diferente do bid que a base projetada daria (senão nada se prova)
        self.assertNotEqual(esperado,
                            int(compose_budget(players)["usable_draft_budget"]))


class TestGateDeFase(unittest.TestCase):
    """`_projection_open` contra AppConfig real (SQLite em memória, sem tocar o
    dynasty.db) — o gate é a diferença entre projetar a season seguinte e projetar
    season+2 sobre um salário já valorizado."""

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

    def test_aberta_antes_do_rollover(self):
        from models import set_config
        from routes.league import _projection_open
        set_config("rollover_done", "false")
        self.assertTrue(_projection_open())

    def test_fechada_depois_do_rollover(self):
        from models import set_config
        from routes.league import _projection_open
        set_config("rollover_done", "true")
        self.assertFalse(_projection_open())

    def test_ausencia_da_flag_abre(self):
        """Ciclo novo de intertemporada (flag ainda não escrita) → projeção visível."""
        from models import db, AppConfig
        from routes.league import _projection_open
        row = db.session.get(AppConfig, "rollover_done")
        if row:
            db.session.delete(row)
            db.session.commit()
        self.assertTrue(_projection_open())


# ══════════════════════════════════════════════════════════════════════════════
# 3. Guardas estáticas — a réplica não pode voltar, o ano não pode ser literal
# ══════════════════════════════════════════════════════════════════════════════

class TestSemReplicaDeComposicao(unittest.TestCase):
    """O [[F10]] eliminou uma agregação de budget replicada em JS. O L3 dá acesso à
    mesma tentação em Python: montar o roster sintético direto em `league.py`."""

    # `SimpleNamespace(salary=...)` = assinatura do roster sintético.
    # ⚠️ As guardas miram USO (chamada/import), nunca menção: comentário e docstring
    # citam esses nomes de propósito, e um teste que proíbe a PROSA empurra o próximo
    # autor a apagar a explicação para o teste passar.
    ROSTER_SINTETICO = re.compile(r"SimpleNamespace\(\s*salary=")
    CHAMADA = re.compile(r"(?<![\w.])(project_next_salary|draft_budget|compose_budget)\s*\(")
    IMPORTA_PROJ = re.compile(r"^\s*from\s+\S+\s+import[^\n]*\bproject_next_salary\b", re.M)

    def _src(self, rel):
        return (BASE_DIR / rel).read_text(encoding="utf-8")

    def test_roster_sintetico_existe_uma_vez_so(self):
        """Duas linhas, ambas dentro do `compose_budget`. Uma terceira = réplica."""
        n = len(self.ROSTER_SINTETICO.findall(self._src("routes/salary.py")))
        self.assertEqual(n, 2, "esperado: só as 2 linhas de compose_budget "
                               "(jogadores + extra_salaries)")

    def test_league_nao_monta_roster_proprio(self):
        src = self._src("routes/league.py")
        self.assertFalse(self.ROSTER_SINTETICO.search(src),
                         "league.py montou roster sintético — use compose_budget")
        self.assertFalse(self.IMPORTA_PROJ.search(src),
                         "league.py importou a projeção por jogador — a composição é "
                         "do helper compose_budget")
        self.assertNotIn("project_next_salary(", src,
                         "league.py projetou por conta própria")

    def test_templates_nao_calculam_projecao(self):
        """Telas consomem valores prontos (a lição do T2-FIX-2 e do [[F10]])."""
        ofensores = []
        for tpl in ("league.html", "team_detail.html", "cap_projector.html"):
            for m in self.CHAMADA.finditer(self._src(f"templates/{tpl}")):
                ofensores.append(f"{tpl}: {m.group(0)}")
        self.assertEqual(ofensores, [], f"cálculo de projeção no template: {ofensores}")


class TestSemAnoLiteral(unittest.TestCase):
    """Rótulo de ano fixo mente no primeiro rollover — e a tela de projeção é onde
    isso dói mais. Todos derivam de `g_current_season` (context processor)."""

    SUPERFICIES = ["league.html", "team_detail.html", "roster.html", "cap_projector.html"]
    LITERAL = re.compile(r"(Proj|Projetado|Projector|Sal|proj\.)\s+20\d\d")

    def test_nenhum_ano_literal_nas_superficies_de_projecao(self):
        ofensores = []
        for tpl in self.SUPERFICIES:
            src = (BASE_DIR / "templates" / tpl).read_text(encoding="utf-8")
            for m in self.LITERAL.finditer(src):
                ofensores.append(f"{tpl}: {m.group(0)}")
        self.assertEqual(ofensores, [], f"ano literal em: {ofensores}")

    def test_a_guarda_pegaria_o_texto_antigo(self):
        """O padrão casa com o que estava lá antes do L3 (senão não guarda nada)."""
        for antigo in ("Proj 2026", "Cap Projetado 2026", "Cap Projector 2026",
                       "Sal 2025", "Cap proj. 2026"):
            self.assertTrue(self.LITERAL.search(antigo), antigo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
