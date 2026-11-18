"""
off26_42_fix_test.py — suíte do runner OFF26-42-FIX (reparo dos 5 contratos mortos).

Banco SQLite em arquivo temporário com o schema real (`db.create_all` dos models), populado com
o estado de produção de 18/11/2026 descrito no prompt. A leitura ao vivo do Sleeper é injetada
(`live=`) — nenhum teste faz rede. Rodar: `python off26_42_fix_test.py`.
"""

import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import off26_42_fix as fix

OWNERS = {1: "695859519976210432", 2: "732411754436526080", 3: "1129822349391470592",
          4: "205848303030505472", 5: "1130162144764506112", 6: "1131747074137272320",
          7: "698015187109773312", 8: "1126909140380569600", 9: "695859970096328704",
          10: "867557566065045504", 11: "1133812910268010496", 12: "1133818177651224576"}
TEAM_OF = {"5927": 8, "9511": 4, "9502": 9, "12547": 11, "12495": 12}
ESPN = {"5927": (17.0, 20.0, True), "9511": (1.0, 1.0, False), "9502": (0.0, 1.0, True),
        "12547": (0.0, 1.0, False), "12495": (0.0, 1.0, True)}


def live_ok():
    out = {t["sid"]: {"roster_owner": t["team_owner"], "add_tx": t["add_tx"],
                      "acao": "contrato_novo", "caso": 3, "acq_type": "free_agent"}
           for t in fix.COHORT}
    out[fix.MCCARTHY["sid"]] = {"roster_owner": OWNERS[9], "add_tx": fix.MCCARTHY["add_tx"],
                                "acao": "contrato_novo", "caso": 3, "acq_type": "fa_waiver"}
    return out


def build_db(path: Path):
    """Schema real + estado de prod de 18/11 (DADOS do prompt)."""
    from models import db, Team, Player, AppConfig, EspnValueStore
    with fix._bound(path, read_only=False):
        db.create_all()
        db.session.add(AppConfig(key="current_season", value="2026"))
        for tid, owner in OWNERS.items():
            db.session.add(Team(id=tid, sleeper_roster_id=str(tid), sleeper_owner_id=owner,
                                name=f"Time {tid}"))
        db.session.flush()
        for t in fix.COHORT:
            e = t["expected"]
            p = Player(sleeper_player_id=t["sid"], name=t["name"], position="WR",
                       team_id=TEAM_OF[t["sid"]], salary=e["salary"],
                       contract_year=e["contract_year"],
                       contract_start_season=e["contract_start_season"],
                       acquisition_type=e["acquisition_type"], espn_ref_value=ESPN[t["sid"]][1],
                       is_on_ir=(t["sid"] == "5927"), is_dropped=False, needs_review=False)
            db.session.add(p)
            raw, adj, fin = ESPN[t["sid"]]
            db.session.add(EspnValueStore(sleeper_player_id=t["sid"], season=2026,
                                          espn_raw=raw, espn_adjusted=adj, is_final=fin))
        for sid, name in fix.CONTROLS.items():
            db.session.add(Player(sleeper_player_id=sid, name=name, position="WR", team_id=3,
                                  salary=1.0, contract_year=1, contract_start_season=2026,
                                  acquisition_type="free_agent", espn_ref_value=1.0))
        db.session.add(Player(sleeper_player_id="11565", name="J.J. McCarthy", position="QB",
                              team_id=9, salary=1.0, contract_year=1, contract_start_season=2026,
                              acquisition_type="fa_waiver", espn_ref_value=1.0))
        db.session.add(Player(sleeper_player_id="9999", name="Outro", position="RB", team_id=1,
                              salary=30.0, contract_year=2, contract_start_season=2025,
                              acquisition_type="auction_draft", espn_ref_value=40.0))
        db.session.commit()


def run(argv, live="ok"):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fix.main(argv, live=live_ok() if live == "ok" else live)
    return rc, buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name).resolve()
        self.db = d / "copia.db"
        self.backup = d / "backup.db"
        build_db(self.db)
        self.backup.write_bytes(self.db.read_bytes())
        self._env = os.environ.get("DYNASTY_DB")

    def tearDown(self):
        if self._env is None:
            os.environ.pop("DYNASTY_DB", None)
        else:
            os.environ["DYNASTY_DB"] = self._env
        from models import db
        try:
            db.session.remove()
        except Exception:
            pass
        self.tmp.cleanup()

    def apply(self, *extra, live="ok"):
        return run(["--apply", "--db", str(self.db), "--confirm-db", str(self.db),
                    "--backup", str(self.backup), *extra], live=live)

    def q(self, sql, *a):
        con = sqlite3.connect(str(self.db))
        try:
            return con.execute(sql, a).fetchall()
        finally:
            con.close()

    def player(self, sid):
        return self.q("SELECT salary, contract_year, contract_start_season, acquisition_type, "
                      "team_id, is_on_ir, espn_ref_value FROM players WHERE sleeper_player_id=?",
                      sid)[0]


class TestGuardaDeBanco(Base):
    def test_db_obrigatorio_sem_fallback_para_env(self):
        os.environ["DYNASTY_DB"] = str(self.db)       # mesmo com env válida: recusa
        rc, out = run(["--check"])
        self.assertEqual(rc, 2)
        self.assertTrue(out.startswith("Banco aberto: (nenhum)"))
        self.assertIn("--db e obrigatorio", out)

    def test_db_relativo_recusado(self):
        rc, out = run(["--check", "--db", "copia.db"])
        self.assertEqual(rc, 2)
        self.assertIn("ABSOLUTO", out)

    def test_primeira_linha_e_o_caminho(self):
        rc, out = run(["--check", "--db", str(self.db)])
        self.assertEqual(out.splitlines()[0], f"Banco aberto: {self.db}")

    def test_primeira_linha_mesmo_com_argumento_invalido(self):
        rc, out = run(["--check", "--db", str(self.db), "--xpto"])
        self.assertEqual(rc, 2)
        self.assertTrue(out.startswith("Banco aberto: (nenhum)"))

    def test_apply_sem_confirm_recusa(self):
        rc, out = run(["--apply", "--db", str(self.db), "--backup", str(self.backup)])
        self.assertEqual(rc, 2)
        self.assertIn("--confirm-db", out)
        self.assertEqual(self.player("5927")[0], 13.0)

    def test_apply_confirm_divergente_recusa(self):
        rc, out = run(["--apply", "--db", str(self.db), "--confirm-db", str(self.backup),
                       "--backup", str(self.backup)])
        self.assertEqual(rc, 2)
        self.assertEqual(self.player("5927")[0], 13.0)

    def test_backup_igual_ao_alvo_recusa(self):
        rc, out = run(["--apply", "--db", str(self.db), "--confirm-db", str(self.db),
                       "--backup", str(self.db)])
        self.assertEqual(rc, 1)
        self.assertIn("PROPRIO banco alvo", out)
        self.assertEqual(self.player("5927")[0], 13.0)

    def test_check_nao_escreve_nem_toca_mtime(self):
        before = (self.db.stat().st_size, self.db.stat().st_mtime_ns, self.db.read_bytes())
        bk = (self.backup.stat().st_size, self.backup.stat().st_mtime_ns)
        rc, out = run(["--check", "--db", str(self.db)])
        self.assertEqual(rc, 0, out)
        self.assertEqual(before, (self.db.stat().st_size, self.db.stat().st_mtime_ns,
                                  self.db.read_bytes()))
        self.assertEqual(bk, (self.backup.stat().st_size, self.backup.stat().st_mtime_ns))

    def test_apply_nao_toca_o_backup(self):
        bk = (self.backup.stat().st_size, self.backup.stat().st_mtime_ns, self.backup.read_bytes())
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        self.assertEqual(bk, (self.backup.stat().st_size, self.backup.stat().st_mtime_ns,
                              self.backup.read_bytes()))

    def test_env_aponta_para_o_alvo_durante_a_execucao(self):
        os.environ["DYNASTY_DB"] = "/data/dynasty.db"
        rc, out = run(["--check", "--db", str(self.db)])
        self.assertIn("alvo NAO e o banco vivo", out)
        self.assertEqual(os.environ["DYNASTY_DB"], str(self.db))

    def test_nao_importa_app_py(self):
        src = Path(fix.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from app import", src)
        self.assertNotIn("import app\n", src)


class TestCheck(Base):
    def test_check_lista_5_e_controles_ok(self):
        rc, out = run(["--check", "--db", str(self.db)])
        self.assertEqual(rc, 0, out)
        self.assertIn("a corrigir: 5", out)
        self.assertIn("7/7 conferem", out)
        self.assertIn("projecao 2027: $13 hoje -> $16 pos-reparo", out)
        self.assertIn("canal gravado CONFERE", out)

    def test_controle_divergente_derruba_o_check(self):
        self.q_write("UPDATE players SET contract_year=2 WHERE sleeper_player_id='96'")
        rc, out = run(["--check", "--db", str(self.db)])
        self.assertEqual(rc, 1)
        self.assertIn("divergencia: 96", out)

    def q_write(self, sql):
        con = sqlite3.connect(str(self.db))
        con.execute(sql)
        con.commit()
        con.close()


class TestApply(Base):
    def test_aplica_os_5_no_devido(self):
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        for t in fix.COHORT:
            sal, cy, css, acq, team, ir, espn = self.player(t["sid"])
            self.assertEqual((sal, cy, css, acq), (1.0, 1, 2026, "free_agent"), t["sid"])
            self.assertEqual(team, TEAM_OF[t["sid"]])
        self.assertEqual(self.player("5927")[5], 1)            # McLaurin segue em IR
        self.assertEqual(self.player("5927")[6], 20.0)         # ESPN preservado

    def test_linha_espn_identica_inclusive_is_final(self):
        before = self.q("SELECT sleeper_player_id, espn_raw, espn_adjusted, is_final "
                        "FROM espn_value_store ORDER BY 1")
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        after = self.q("SELECT sleeper_player_id, espn_raw, espn_adjusted, is_final "
                       "FROM espn_value_store ORDER BY 1")
        self.assertEqual(before, after)

    def test_folha_por_time(self):
        def folha():
            return dict(self.q("SELECT team_id, SUM(salary) FROM players WHERE is_dropped=0 "
                               "GROUP BY team_id"))
        b = folha()
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        a = folha()
        delta = {t: a.get(t, 0) - b.get(t, 0) for t in set(a) | set(b)}
        self.assertEqual(delta[8], -12.0)
        self.assertEqual(delta[4], -6.0)
        self.assertEqual({t for t, d in delta.items() if d}, {8, 4})
        self.assertEqual(sum(a.values()) - sum(b.values()), -18.0)

    def test_trilha_com_a_marca_do_add(self):
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        for t in fix.COHORT:
            ref = f"tx:{t['add_tx']}"
            pid = self.q("SELECT id FROM players WHERE sleeper_player_id=?", t["sid"])[0][0]
            self.assertEqual(len(self.q("SELECT 1 FROM auction_log WHERE notes LIKE ?",
                                        f"%[ref:{ref}]%")), 1)
            self.assertEqual(len(self.q("SELECT 1 FROM player_history WHERE player_id=? AND "
                                        "sleeper_event_ref=?", pid, ref)), 1)
            self.assertEqual(len(self.q("SELECT 1 FROM salary_history WHERE player_id=? AND "
                                        "season=2026 AND salary=1 AND contract_year=1", pid)), 1)
        nota = self.q("SELECT notes FROM player_history WHERE sleeper_event_ref=?",
                      "tx:1399932595008991232")[0][0]
        self.assertIn("Cangaceiros (r5)", nota)
        self.assertIn("1416520881219391488", nota)

    def test_segunda_aplicacao_zero_escrita(self):
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        snap = self.db.read_bytes()
        rc2, out2 = self.apply()
        self.assertEqual(rc2, 0, out2)
        self.assertEqual(out2.count("ja registrado"), 5)
        self.assertIn("zero escrita", out2)
        self.assertEqual(snap, self.db.read_bytes())

    def test_controles_mccarthy_e_terceiros_intocados(self):
        sids = list(fix.CONTROLS) + ["11565", "9999"]
        ph = ",".join("?" * len(sids))
        before = self.q(f"SELECT * FROM players WHERE sleeper_player_id IN ({ph}) ORDER BY id", *sids)
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        self.assertEqual(before, self.q(f"SELECT * FROM players WHERE sleeper_player_id IN ({ph}) "
                                        f"ORDER BY id", *sids))

    def test_parcial_sem_gordon_e_depois_so_ele(self):
        rc, out = self.apply("--exclude", "12495")
        self.assertEqual(rc, 0, out)
        self.assertIn("PENDENTE", out)
        self.assertEqual(self.player("12495")[1:4], (2, 2025, "rookie_draft"))
        self.assertEqual(sum(1 for t in fix.COHORT if self.player(t["sid"])[1:4] ==
                             (1, 2026, "free_agent")), 4)
        rc2, out2 = self.apply()
        self.assertEqual(rc2, 0, out2)
        self.assertEqual(out2.count("ja registrado"), 4)
        self.assertEqual(self.player("12495")[1:4], (1, 2026, "free_agent"))

    def test_check_apos_parcial_conta_ja_registrados_como_ok(self):
        rc, out = self.apply("--exclude", "12495")
        self.assertEqual(rc, 0, out)
        rc2, out2 = run(["--check", "--db", str(self.db)])
        self.assertEqual(rc2, 0, out2)
        self.assertIn("1/1 a corrigir; 4 ja registrado(s); 0 bloqueado(s)", out2)
        rc3, out3 = run(["--check", "--db", str(self.db), "--exclude", "12495"])
        self.assertEqual(rc3, 0, out3)
        self.assertIn("0/0 a corrigir; 4 ja registrado(s)", out3)

    def test_check_com_bloqueio_nao_e_ok(self):
        lv = live_ok()
        lv["9511"] = dict(lv["9511"], roster_owner=OWNERS[2])
        rc, out = run(["--check", "--db", str(self.db)], live=lv)
        self.assertEqual(rc, 1)
        self.assertIn("1 bloqueado(s)", out)

    def test_exclude_fora_da_lista_recusa(self):
        rc, out = self.apply("--exclude", "96")
        self.assertEqual(rc, 2)


class TestGuardaPendencia(Base):
    def test_pendencia_aberta_pula_o_alvo(self):
        from models import db, ContractPendency, Player
        with fix._bound(self.db, read_only=False):
            p = Player.query.filter_by(sleeper_player_id="5927").first()
            db.session.add(ContractPendency(season=2026, player_id=p.id, team_id=8,
                                            kind="sinal_divergente",
                                            sleeper_transaction_id="1419159991641780224",
                                            tx_type="free_agent", tx_timestamp_ms=1,
                                            phase="temporada", status="aberta",
                                            context_json="{}"))
            db.session.commit()
        pend_before = self.q("SELECT * FROM contract_pendencies")
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        self.assertIn("pendencia ABERTA", out)
        self.assertEqual(self.player("5927")[0], 13.0)                  # não tocado
        self.assertEqual(self.player("9511")[0], 1.0)                   # os outros seguem
        self.assertEqual(pend_before, self.q("SELECT * FROM contract_pendencies"))

    def test_pendencia_arbitrada_nao_bloqueia(self):
        from models import db, ContractPendency, Player
        with fix._bound(self.db, read_only=False):
            p = Player.query.filter_by(sleeper_player_id="5927").first()
            db.session.add(ContractPendency(season=2026, player_id=p.id, kind="sinal_divergente",
                                            sleeper_transaction_id="x", tx_type="waiver",
                                            tx_timestamp_ms=1, status="arbitrada",
                                            verdict="morto", context_json="{}"))
            db.session.commit()
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.player("5927")[0], 1.0)


class TestGuardaAoVivo(Base):
    def test_regua_ao_vivo_diferente_pula(self):
        lv = live_ok()
        lv["9511"] = dict(lv["9511"], acao="pendencia", caso=None)
        rc, out = self.apply(live=lv)
        self.assertIn("regua ao vivo nao devolve caso 3", out)
        self.assertEqual(self.player("9511")[0], 7.0)

    def test_membership_mudou_pula(self):
        lv = live_ok()
        lv["5927"] = dict(lv["5927"], roster_owner=OWNERS[2])
        rc, out = self.apply(live=lv)
        self.assertIn("membership mudou", out)
        self.assertEqual(self.player("5927")[0], 13.0)

    def test_estado_divergente_da_guarda_pula(self):
        con = sqlite3.connect(str(self.db))
        con.execute("UPDATE players SET salary=14 WHERE sleeper_player_id='5927'")
        con.commit()
        con.close()
        rc, out = self.apply()
        self.assertIn("guarda: salary=14.0", out)
        self.assertEqual(self.player("5927")[0], 14.0)


class TestGuardaIsMyTeam(Base):
    def test_is_my_team_atrasado_pula_sem_escrever(self):
        con = sqlite3.connect(str(self.db))
        con.execute("UPDATE players SET is_my_team=1 WHERE sleeper_player_id='12495'")
        con.commit()
        con.close()
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)                              # os outros 4 passam limpos
        self.assertIn("is_my_team do jogador", out)
        self.assertEqual(self.player("12495")[1:4], (2, 2025, "rookie_draft"))
        self.assertEqual(self.q("SELECT is_my_team FROM players WHERE sleeper_player_id='12495'"),
                         [(1,)])


class TestNucleo(unittest.TestCase):
    def test_todas_as_notas_preservam_o_token(self):
        for t in fix.COHORT:
            self.assertTrue(fix.note_fits(t["note"], fix.event_ref(t)), t["sid"])

    def test_lista_congelada(self):
        self.assertEqual([t["sid"] for t in fix.COHORT],
                         ["5927", "9511", "9502", "12547", "12495"])
        self.assertFalse(set(fix.CONTROLS) & {t["sid"] for t in fix.COHORT})
        self.assertNotIn("11565", {t["sid"] for t in fix.COHORT})


if __name__ == "__main__":
    unittest.main(verbosity=1)
