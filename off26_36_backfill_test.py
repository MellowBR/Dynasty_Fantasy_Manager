# -*- coding: utf-8 -*-
"""
off26_36_backfill_test.py — Parte 4 do OFF26-36: backfill dos eventos de rollover 2026.

Cobre a validação 5 da sessão MAN-OFF26-36: eventos criados a partir do SalaryHistory
(fonte canônica única), ref `rollover:2026` em TODOS (nunca NULL), idempotência
(segunda execução cria zero) e sobrevivência ao rebuild F8 simulado (DELETE de rows
com ref NULL preserva os criados). Ressalva do team_name: trocado pós-rollover recebe
o time DA ÉPOCA, reconstruído do lado de origem `(src→dst)` do trade mais antigo.

Roda contra arquivo SQLite temporário (o runner abre por caminho + verificação raw).
"""

import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import off26_36_backfill as bf


class TestNucleoPuro(unittest.TestCase):
    def test_classify_rule(self):
        self.assertEqual(bf.classify_rule("VALORIZAÇÃO: MAX($1, floor(0.5×7.0))=$3"),
                         "rollover")
        self.assertEqual(bf.classify_rule("Waiver Ano 2: floor(0.80×5.0)=$4"),
                         "rollover")
        self.assertIsNone(bf.classify_rule("FA Auction: $8 (bid)"))
        self.assertIsNone(bf.classify_rule(None))

    def test_parse_trade_src(self):
        self.assertEqual(bf.parse_trade_src(
            "Trade sleeper_sync tx=139 (Cangaceiros da Colina→mongoloides)"),
            "Cangaceiros da Colina")
        self.assertEqual(bf.parse_trade_src(
            "Trade sleeper_sync tx=139 (Tropa do Jarra  🏆→AlexTheDawg)"),
            "Tropa do Jarra  🏆")
        self.assertIsNone(bf.parse_trade_src("nota sem seta"))
        self.assertIsNone(bf.parse_trade_src(None))

    def test_team_at_rollover(self):
        # sem trades → time atual
        t, rec, warn = bf.team_at_rollover("A", [])
        self.assertEqual((t, rec, warn), ("A", False, None))
        # com trades → ORIGEM do mais antigo
        t, rec, warn = bf.team_at_rollover(
            "C", ["Trade tx=1 (A→B)", "Trade tx=2 (B→C)"])
        self.assertEqual((t, rec), ("A", True))
        # imparseável → fallback COM warning, nunca silêncio
        t, rec, warn = bf.team_at_rollover("C", ["nota quebrada"])
        self.assertEqual((t, rec), ("C", False))
        self.assertIsNotNone(warn)

    def test_plan_events_idempotente_e_filtrado(self):
        rows = [
            {"player_id": 1, "salary": 3.0, "contract_year": 2,
             "rule": "VALORIZAÇÃO: x", "current_team": "A", "name": "P1"},
            {"player_id": 2, "salary": 4.0, "contract_year": 2,
             "rule": "Waiver Ano 2: x", "current_team": "B", "name": "P2"},
            {"player_id": 3, "salary": 8.0, "contract_year": 1,
             "rule": "FA Auction: $8 (bid)", "current_team": "A", "name": "P3"},
        ]
        existing = {(2, bf.SEASON, "rollover", "B", bf.EVENT_REF)}
        events, skipped, warnings = bf.plan_events(rows, existing, {})
        self.assertEqual([e["player_id"] for e in events], [1])   # 2 existe, 3 fora
        self.assertEqual(len(skipped), 2)
        self.assertTrue(all(e["sleeper_event_ref"] == bf.EVENT_REF for e in events))


class TestRunnerIntegracao(unittest.TestCase):
    """Banco-arquivo temporário com 3 rows de rollover + 1 fora + 1 trocado pós-rollover."""

    EXPECTED = 3

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = self.tmp / "ensaio.db"
        self._orig_expected = bf.EXPECTED_TOTAL
        bf.EXPECTED_TOTAL = self.EXPECTED

        app = bf._make_app(self.db_path)
        from models import db, Team, Player, SalaryHistory, PlayerHistory
        with app.app_context():
            db.create_all()
            t1 = Team(name="Time Atual")
            t2 = Team(name="Time Antigo")
            db.session.add_all([t1, t2])
            db.session.commit()
            carimbo = datetime(2026, 8, 17, 21, 34, 0)
            pós = datetime(2026, 8, 18, 2, 4, 9)
            for i, (nome, rule, sal, cy) in enumerate([
                ("Fica", "VALORIZAÇÃO: MAX($1, floor(0.5×7.0))=$3", 3.0, 2),
                ("WaiverAno2", "Waiver Ano 2: floor(0.80×5.0)=$4", 4.0, 2),
                ("Trocado", "VALORIZAÇÃO: MAX($2, floor(0.5×9.0))=$4", 4.0, 3),
            ], start=1):
                p = Player(name=nome, position="WR", team_id=t1.id,
                           fantasy_team=t1.name, sleeper_player_id=str(1000 + i),
                           salary=sal, contract_year=cy)
                db.session.add(p)
                db.session.flush()
                db.session.add(SalaryHistory(
                    player_id=p.id, season=2026, salary=sal, contract_year=cy,
                    rule_applied=rule, created_at=carimbo))
                if nome == "Trocado":
                    db.session.add(PlayerHistory(
                        player_id=p.id, season=2026, team_name=t1.name,
                        event_type="trade", salary=sal, contract_year=cy,
                        notes=f"Trade sleeper_sync tx=99 ({t2.name}→{t1.name})",
                        sleeper_event_ref="tx:99", created_at=pós))
            # row fora do backfill (aquisição do leilão — não entra)
            fora = Player(name="Fora", position="RB", team_id=t1.id,
                          fantasy_team=t1.name, sleeper_player_id="2000",
                          salary=8.0, contract_year=1)
            db.session.add(fora)
            db.session.flush()
            db.session.add(SalaryHistory(
                player_id=fora.id, season=2026, salary=8.0, contract_year=1,
                rule_applied="FA Auction: $8 (bid)", created_at=carimbo))
            db.session.commit()

        self.backup = self.tmp / "backup.db"
        shutil.copy(self.db_path, self.backup)

    def tearDown(self):
        bf.EXPECTED_TOTAL = self._orig_expected
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _refs(self):
        import sqlite3
        con = sqlite3.connect(str(self.db_path))
        rows = con.execute(
            "SELECT player_id, team_name, sleeper_event_ref FROM player_history "
            "WHERE sleeper_event_ref=? ORDER BY player_id", (bf.EVENT_REF,)).fetchall()
        con.close()
        return rows

    def test_check_apply_idempotencia_e_f8(self):
        # --check antes: plano de 3, exit 0
        self.assertEqual(bf.cmd_check(self.db_path), 0)
        # --apply: cria os 3, com o trocado no time DA ÉPOCA
        self.assertEqual(bf.cmd_apply(self.db_path, self.backup), 0)
        rows = self._refs()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r[2] == bf.EVENT_REF for r in rows))   # ref NUNCA NULL
        times = {r[0]: r[1] for r in rows}
        self.assertIn("Time Antigo", times.values())               # reconstrução
        # segunda execução: cria ZERO (validação 5)
        self.assertEqual(bf.cmd_apply(self.db_path, self.backup), 0)
        self.assertEqual(len(self._refs()), 3)
        # --check depois: existentes=3, a criar=0, exit 0
        self.assertEqual(bf.cmd_check(self.db_path), 0)
        # rebuild F8 simulado: DELETE ref NULL preserva os 3 (ref sempre presente)
        import sqlite3
        con = sqlite3.connect(str(self.db_path))
        con.execute("INSERT INTO player_history (player_id, season, event_type, "
                    "team_name, salary, contract_year, notes, sleeper_event_ref) "
                    "VALUES (1, 2025, 'legacy', 'X', 0, 0, 'sem ref', NULL)")
        con.execute("DELETE FROM player_history WHERE sleeper_event_ref IS NULL")
        con.commit()
        con.close()
        self.assertEqual(len(self._refs()), 3)

    def test_contagem_divergente_bloqueia(self):
        bf.EXPECTED_TOTAL = 99
        self.assertEqual(bf.cmd_check(self.db_path), 1)
        self.assertEqual(bf.cmd_apply(self.db_path, self.backup), 1)
        self.assertEqual(len(self._refs()), 0)      # nada escrito

    def test_apply_exige_backup(self):
        self.assertEqual(bf.main(["--apply"]), 1)
        self.assertEqual(len(self._refs()), 0)

    def test_db_path_e_sempre_absoluto(self):
        self.assertTrue(bf._db_path("dynasty.db").is_absolute())


if __name__ == "__main__":
    unittest.main(verbosity=2)
