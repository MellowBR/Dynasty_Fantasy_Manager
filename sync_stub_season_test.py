# -*- coding: utf-8 -*-
"""
sync_stub_season_test.py — OFF26 (fix da linha 304): a criação de stub do sync lê a season
da FONTE CANÔNICA (AppConfig via get_current_season), não da constante estagnada.

Contexto (OFF26-24-F1, 18/08/2026): todo Player novo criado pelo sync nascia com
contract_start_season=CURRENT_SEASON — constante de módulo fixa em 2025, que o rollover
nunca avança (ele escreve AppConfig). Resultado: a classe de rookies 2026 inteira nasceu
carimbada 2025 (curada pelo one-shot wa_draft_2026_fix); o defeito seguia ativo para
qualquer entrante pós-rollover.

Três guardas, sem rede e sem tocar o banco do repo:
  1. AST: o construtor Player( do sync não referencia CURRENT_SEASON em nenhum campo —
     regressão reintroduzindo a constante na criação de dados FALHA aqui.
  2. Comportamento: get_current_season() com AppConfig em 2026 devolve 2026 (o que o
     stub passa a carimbar); sem a linha no AppConfig, cai no fallback sem quebrar.
  3. Escopo: o fix não criou nenhum outro uso da constante crua no sync além do import.
"""

import ast
import unittest


def _sync_source():
    with open("sync_sleeper.py", encoding="utf-8") as f:
        return f.read()


class TestGuardaEstatica(unittest.TestCase):
    """A raiz do carimbo 2025 não pode voltar — provado por AST, não por grep."""

    def test_construtor_player_nao_usa_constante(self):
        tree = ast.parse(_sync_source())
        player_calls = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "Player"
        ]
        self.assertTrue(player_calls, "construtor Player( não encontrado no sync")
        for call in player_calls:
            for kw in call.keywords:
                names = [x.id for x in ast.walk(kw.value) if isinstance(x, ast.Name)]
                self.assertNotIn(
                    "CURRENT_SEASON", names,
                    f"Player({kw.arg}=...) referencia a constante estagnada — "
                    f"a raiz do carimbo 2025 (OFF26-24-F1) voltou")

    def test_stub_season_vem_da_fonte_canonica(self):
        """run_sync deve conter a leitura get_current_season() (uma vez, hoisted)."""
        tree = ast.parse(_sync_source())
        run_sync = next(n for n in ast.walk(tree)
                        if isinstance(n, ast.FunctionDef) and n.name == "run_sync")
        calls = [n for n in ast.walk(run_sync)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "get_current_season"]
        self.assertTrue(calls, "run_sync não lê get_current_season() — fonte canônica ausente")

    def test_constante_so_no_import(self):
        """Fora do bloco de import, nenhuma referência crua à constante no módulo."""
        tree = ast.parse(_sync_source())
        uses = [n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Name) and n.id == "CURRENT_SEASON"]
        self.assertEqual(uses, [], f"uso(s) cru(s) de CURRENT_SEASON no sync: linhas {uses}")


class TestFonteCanonica(unittest.TestCase):
    """O que o stub carimba agora — ORM em memória, molde das demais suítes."""

    def setUp(self):
        from flask import Flask
        from models import db
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def test_appconfig_2026_stub_nasce_2026(self):
        from models import db, set_config, get_current_season
        with self.app.app_context():
            set_config("current_season", "2026")
            db.session.commit()
            self.assertEqual(get_current_season(), 2026)

    def test_appconfig_ausente_cai_no_fallback_sem_quebrar(self):
        from models import get_current_season, CURRENT_SEASON
        with self.app.app_context():
            self.assertEqual(get_current_season(), CURRENT_SEASON)

    def test_pos_rollover_acompanha(self):
        """A propriedade que a constante nunca teve: avançar a season avança o carimbo."""
        from models import db, set_config, get_current_season
        with self.app.app_context():
            set_config("current_season", "2026")
            db.session.commit()
            before = get_current_season()
            set_config("current_season", "2027")
            db.session.commit()
            self.assertEqual((before, get_current_season()), (2026, 2027))


if __name__ == "__main__":
    unittest.main(verbosity=2)
