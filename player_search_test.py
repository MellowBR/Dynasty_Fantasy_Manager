"""
player_search_test.py — a busca de jogador (M10), os DOIS consumidores.

Cobre o backend único (`GET /api/player/search`) e as guardas de identidade que a
spec do M10 impõe. A régua é a do `player_lookup`: **substring é sugestão exibida,
nunca resolução**. O que a busca entrega é uma lista distinguível; quem resolve é o
clique do usuário, e o destino sai do `id` da linha — nunca do nome.

Caso âncora (28/04/2026): "queria ver o contrato do Mahomes e teria que abrir os 12
rosters". Caso de homônimo: **dois DJ Moore** existem no pool do Sleeper (o WR e o
CB) — hoje só um está rosterado, então o cenário é montado aqui, que é o único lugar
onde ele pode ser exercido de forma determinística.

Sem rede, sem tocar o `dynasty.db` (SQLite em memória).
"""

import re
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SEARCH_KEYS = {
    "id", "sleeper_player_id", "name", "position", "nfl_team", "fantasy_team",
    "team_id", "salary", "contract_year", "contract_display", "acquisition_type",
    "espn_ref_value",
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. Núcleo puro — escape dos curingas do LIKE
# ══════════════════════════════════════════════════════════════════════════════

class TestLikeEscape(unittest.TestCase):

    def test_percent_vira_literal(self):
        from routes.roster import _like_term
        self.assertEqual(_like_term("%"), r"\%")

    def test_underscore_vira_literal(self):
        from routes.roster import _like_term
        self.assertEqual(_like_term("a_b"), r"a\_b")

    def test_barra_invertida_escapada_antes(self):
        """A ordem importa: escapar a barra depois do '%' duplicaria o escape."""
        from routes.roster import _like_term
        self.assertEqual(_like_term("a\\%"), r"a\\\%")

    def test_nome_comum_passa_intacto(self):
        from routes.roster import _like_term
        self.assertEqual(_like_term("D.J. Moore"), "D.J. Moore")


# ══════════════════════════════════════════════════════════════════════════════
# 2. O endpoint contra ORM em memória
# ══════════════════════════════════════════════════════════════════════════════

class TestSearchEndpoint(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from flask import Flask
        from models import db
        from routes.roster import roster_bp

        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["LOGIN_DISABLED"] = True   # o alvo é a query, não o login
        cls.app.config["TESTING"] = True
        db.init_app(cls.app)
        cls.app.register_blueprint(roster_bp)
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
        self.t1 = Team(name="Cangaceiros da Colina")
        self.t2 = Team(name="mongoloides")
        db.session.add_all([self.t1, self.t2])
        db.session.commit()

        def add(name, pos, nfl, team, sid, **kw):
            p = Player(name=name, position=pos, nfl_team=nfl, team_id=team.id,
                       sleeper_player_id=sid, salary=kw.pop("salary", 5),
                       contract_year=kw.pop("contract_year", 1),
                       acquisition_type=kw.pop("acquisition_type", "auction_draft"),
                       espn_ref_value=kw.pop("espn_ref_value", 12.0), **kw)
            db.session.add(p)
            return p

        # Os dois DJ Moore — homônimos REAIS do pool (WR e CB), aqui rosterados.
        add("DJ Moore", "WR", "BUF", self.t2, "4983")
        add("DJ Moore", "CB", "CHI", self.t1, "8154")
        add("Moorehead Silva", "TE", "NYJ", self.t1, "9001")
        add("Patrick Mahomes", "QB", "KC", self.t1, "4046",
            salary=42, contract_year=3, acquisition_type="rookie_draft",
            espn_ref_value=48.0)
        add("Cortado Moore", "RB", "LAR", self.t1, "9002", is_dropped=True)
        db.session.commit()

    def get(self, **params):
        from urllib.parse import urlencode
        r = self.client.get("/api/player/search?" + urlencode(params))
        self.assertEqual(r.status_code, 200)
        return r.get_json()

    # ── caso âncora ──────────────────────────────────────────────────────────
    def test_mahomes_chega_pelo_nome(self):
        """O caso de 28/04: 'Mahomes' resolve sem passar por roster de time nenhum."""
        res = self.get(q="Mahomes")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "Patrick Mahomes")
        self.assertTrue(res[0]["id"])           # o destino /player/<id> sai daqui

    def test_busca_parcial_encontra(self):
        self.assertEqual([p["name"] for p in self.get(q="mah")], ["Patrick Mahomes"])

    # ── homônimos ────────────────────────────────────────────────────────────
    def test_homonimos_vem_os_dois(self):
        self.assertEqual(len(self.get(q="DJ Moore")), 2)

    def test_homonimos_tem_ids_diferentes(self):
        """A navegação não pode ser ambígua: dois destinos distintos."""
        res = self.get(q="DJ Moore")
        self.assertEqual(len({p["id"] for p in res}), 2)
        self.assertEqual(len({p["sleeper_player_id"] for p in res}), 2)

    def test_homonimos_sao_distinguiveis_na_lista(self):
        """Posição + time NFL são o que separa um DJ Moore do outro na tela."""
        res = self.get(q="DJ Moore")
        marcas = {(p["position"], p["nfl_team"]) for p in res}
        self.assertEqual(marcas, {("WR", "BUF"), ("CB", "CHI")})

    # ── ordenação ────────────────────────────────────────────────────────────
    def test_prefixo_vem_antes_do_meio_do_nome(self):
        """'moore' → 'Moorehead' (prefixo) antes dos 'DJ Moore' (substring)."""
        nomes = [p["name"] for p in self.get(q="moore")]
        self.assertEqual(nomes[0], "Moorehead Silva")
        self.assertEqual(len(nomes), 3)

    def test_ordem_alfabetica_dentro_do_grupo(self):
        nomes = [p["name"] for p in self.get(q="o")]
        self.assertEqual(nomes, sorted(nomes, key=str.lower))

    # ── filtros e limites ────────────────────────────────────────────────────
    def test_dropado_fica_fora(self):
        self.assertNotIn("Cortado Moore", [p["name"] for p in self.get(q="Moore")])

    def test_filtro_por_time_da_liga(self):
        res = self.get(q="Moore", team_id=self.t2.id)
        self.assertEqual([p["name"] for p in res], ["DJ Moore"])
        self.assertEqual(res[0]["nfl_team"], "BUF")

    def test_q_vazio_devolve_lista_vazia(self):
        self.assertEqual(self.get(q=""), [])
        self.assertEqual(self.get(q="   "), [])

    def test_jogador_inexistente_degrada_gracioso(self):
        """Vazio é vazio — nunca erro, nunca 'o mais parecido'."""
        self.assertEqual(self.get(q="Zzzz Ninguem"), [])

    def test_curinga_digitado_nao_traz_todo_mundo(self):
        """'%' é texto, não 'tudo' — senão a lista mentiria sobre o que casou."""
        self.assertEqual(self.get(q="%"), [])
        self.assertEqual(self.get(q="_"), [])

    def test_teto_de_20(self):
        from models import db, Player
        from routes.roster import SEARCH_LIMIT
        for i in range(30):
            db.session.add(Player(name=f"Moore Clone {i:02d}", position="WR",
                                  team_id=self.t1.id, salary=1))
        db.session.commit()
        self.assertEqual(SEARCH_LIMIT, 20)
        self.assertEqual(len(self.get(q="Moore")), 20)

    # ── payload ──────────────────────────────────────────────────────────────
    def test_payload_e_o_enxuto(self):
        self.assertEqual(set(self.get(q="Mahomes")[0].keys()), SEARCH_KEYS)

    def test_payload_nao_carrega_projecao(self):
        """20 resultados por tecla não podem arrastar projeção de contrato."""
        res = self.get(q="Mahomes")[0]
        self.assertNotIn("projected_next_salary", res)
        self.assertNotIn("is_renewal_candidate", res)

    def test_payload_alimenta_o_autocomplete_da_calculadora(self):
        """Os 3 campos que a calculadora preenche vêm no payload, ESPN AJUSTADO."""
        res = self.get(q="Mahomes")[0]
        self.assertEqual(res["espn_ref_value"], 48.0)     # ajustado (raw × 1.2)
        self.assertEqual(res["contract_year"], 3)
        self.assertEqual(res["acquisition_type"], "rookie_draft")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Guardas de identidade (estáticas) — o que NÃO pode voltar
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardasDeIdentidade(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base = (BASE_DIR / "templates" / "base.html").read_text(encoding="utf-8")
        cls.calc = (BASE_DIR / "templates" / "salary.html").read_text(encoding="utf-8")
        cls.roster = (BASE_DIR / "routes" / "roster.py").read_text(encoding="utf-8")

    def test_engrenagem_e_unica(self):
        """Um componente para navbar (x2) e calculadora — não três buscas."""
        self.assertEqual(self.base.count("function createPlayerSearch"), 1)
        self.assertEqual(self.base.count("createPlayerSearch({"), 2)   # desktop + mobile
        self.assertEqual(self.calc.count("createPlayerSearch({"), 1)   # calculadora

    def test_enter_nao_seleciona_sem_item_destacado(self):
        """Zero resolução silenciosa: Enter só escolhe o que o usuário destacou."""
        self.assertIn("if (open && active >= 0)", self.base)
        self.assertIn("if (!p) return;", self.base)

    def test_navegacao_pelo_id_nunca_pelo_nome(self):
        self.assertIn("'/player/' + p.id", self.base)
        self.assertNotRegex(self.base, r"/player/\$\{[^}]*\.name")

    def test_busca_nao_usa_o_matching_estrito_do_player_lookup(self):
        """player_lookup é reconciliação de import — não é autocomplete (M10)."""
        corpo = self.roster.split("def search_players")[1].split("\n@")[0]
        corpo = corpo.split('"""')[2]        # fora do docstring, que o cita de propósito
        self.assertNotIn("find_player_by_name", corpo)
        self.assertNotIn("player_lookup", corpo)

    def test_calculadora_nao_inventa_o_valor_do_ano_1(self):
        """O banco guarda salário corrente, não o pago no ano 1."""
        bloco = self.calc.split("function fillFromPlayer")[1].split("\n}")[0]
        self.assertNotIn("year1-value", bloco)

    def test_calculadora_converte_espn_para_cru(self):
        """O campo é RAW e o backend multiplica por 1.2 — sem a divisão, infla."""
        self.assertIn("p.espn_ref_value / 1.2", self.calc)

    def test_sem_replica_de_escape_no_js_global(self):
        """escapeHtml é fonte única — as réplicas inline viraram uma."""
        self.assertEqual(len(re.findall(r"'&':'&amp;'", self.base)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
