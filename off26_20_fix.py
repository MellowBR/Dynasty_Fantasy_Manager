"""
off26_20_fix.py — runner ONE-SHOT da correção OFF26-20-FIX (contract_year 2→1 nos 22 FAs de 2025).

Aprovação nominal do owner em 05/08/2026, ao fim da cadeia F1→F1B→F1C→VERIF→CANAL→T4:
os 22 abriram contrato em 2025 pelo canal `free_agent` (confirmado transação a transação na
API), logo o `contract_year` correto é 1 — o banco os tem em 2, o que os mandaria para
valorização em vez de `0,8 × ESPN REF` no rollover de 18/08.

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    # 0) BACKUP OBRIGATÓRIO (sem ele o --apply recusa escrever):
    sqlite3 /data/dynasty.db ".backup '/data/pre_off26_20_fix.db'"

    # 1) Conferência read-only (revalida a guarda dos 22 + dry-run do rollover):
    python off26_20_fix.py --check

    # 2) Escrita (guarda → escrita+trilha → verificação → commit):
    python off26_20_fix.py --apply --backup /data/pre_off26_20_fix.db

    # Ensaio local: acrescentar --db <caminho de uma CÓPIA do seed>

Escreve SOMENTE `players.contract_year` dos elegíveis + `player_history` (trilha), via
`contract_year_correction.apply_contract_year_correction` (a porta canônica). Linha que não
case a guarda é pulada e reportada — a aprovação do owner é sobre o estado conferido no T4.
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

BASE_DIR = Path(__file__).resolve().parent

# Os 22 aprovados nominalmente (MAN-OFF26-20-CANAL, 06654e9). IDs são STRINGS —
# as 5 DEFs usam sigla ('DET'/'HOU'/'IND'/'LAR'/'NO'); nunca coagir a inteiro.
TARGETS = [
    ("11603", "AJ Barner"),
    ("8142", "Alec Pierce"),
    ("8167", "Christian Watson"),
    ("6865", "Colby Parkinson"),
    ("DET", "Detroit Lions"),
    ("11834", "Devaughn Vele"),
    ("9486", "Dontayvion Wicks"),
    ("4066", "Evan Engram"),
    ("5970", "Greg Dortch"),
    ("HOU", "Houston Texans"),
    ("IND", "Indianapolis Colts"),
    ("2747", "Jason Myers"),
    ("11583", "Jonathon Brooks"),
    ("7567", "Kenny Gainwell"),
    ("LAR", "Los Angeles Rams"),
    ("11610", "Malik Washington"),
    ("7607", "Michael Carter"),
    ("10232", "Michael Wilson"),
    ("NO", "New Orleans Saints"),
    ("9487", "Parker Washington"),
    ("11575", "Ray Davis"),
    ("3321", "Tyreek Hill"),
]

# Guarda pré-escrita: o estado conferido no T4 (prod idêntica ao seed, 22/22).
EXPECTED = {
    "contract_year": 2,
    "contract_start_season": 2025,
    "acquisition_type": "free_agent",
    "needs_review": False,
    "is_dropped": False,
}
NEW_YEAR = 1
EVENT_REF = "fix:off26-20"
REASON = ("Correção OFF26-20-FIX aprovada nominalmente pelo owner em 05/08/2026 "
          "(canal free_agent confirmado na API; contrato reaberto em 2025)")

# Casos vivos da validação: sleeper_id → salário 2026 esperado no dry-run pós-correção.
LIVE_CASES = {"8142": 5, "8167": 4, "9487": 4, "10232": 2}


def _db_path(cli_db: str = None) -> Path:
    return Path(cli_db or os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db"))


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco. NÃO roda o boot do app.py (sem
    import CSV, sem sync, sem seed): correção cirúrgica não dispara efeito colateral."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _snapshot_players(db_path: Path) -> dict:
    """Fotografa a tabela players inteira (todas as colunas) para o diff pós-escrita."""
    con = sqlite3.connect(str(db_path))
    cols = [r[1] for r in con.execute("PRAGMA table_info(players)")]
    rows = {r[0]: dict(zip(cols, r)) for r in
            con.execute(f"SELECT {', '.join(cols)} FROM players")}
    con.close()
    return rows


def _dry_run_rollover(salary, espn, acq):
    """Rollover 18/08 simulado sobre o estado PÓS-correção (contract_year=1) — puro, sem escrita."""
    from salary_engine import apply_season_rollover
    stub = SimpleNamespace(salary=salary, espn_ref_value=espn,
                           acquisition_type=acq, contract_year=NEW_YEAR)
    return apply_season_rollover(stub)


def _report_plan(result: dict) -> None:
    print(f"\nElegíveis: {len(result['applied'])}/{len(TARGETS)}")
    for a in result["applied"]:
        print(f"  ok    {a['sleeper_player_id']:>6}  {a['name']:<22} {a['team']:<28} "
              f"contract_year {a['old']} -> {a['new']}")
    for s in result["skipped"]:
        name = dict(TARGETS).get(s["sleeper_player_id"], "?")
        print(f"  PULADO {s['sleeper_player_id']:>6}  {name:<22} {s['reason']}")


def _report_rollover(players) -> bool:
    """Imprime o dry-run do rollover e confere os casos vivos. True = todos conferem."""
    print("\nDry-run do rollover 18/08 (pós-correção, regra Waiver/FA Ano 2 — sem escrita):")
    ok = True
    for p in sorted(players, key=lambda p: p.name):
        new_sal, new_yr, rule = _dry_run_rollover(p.salary, p.espn_ref_value, p.acquisition_type)
        mark = ""
        if p.sleeper_player_id in LIVE_CASES:
            want = LIVE_CASES[p.sleeper_player_id]
            mark = "  ✓ caso vivo" if new_sal == want else f"  ✗ ESPERAVA ${want}"
            ok = ok and (new_sal == want)
        print(f"  {p.name:<22} ${int(p.salary)} -> ${new_sal} (ano {new_yr})  [{rule}]{mark}")
    return ok


def cmd_check(db_path: Path) -> int:
    """Read-only: revalida a guarda dos 22 e simula o rollover pós-correção."""
    from models import Player
    from contract_year_correction import plan_correction, _player_state

    app = _make_app(db_path)
    with app.app_context():
        ids = [sid for sid, _ in TARGETS]
        players = Player.query.filter(Player.sleeper_player_id.in_(ids)).all()
        rows_by_id = {}
        for p in players:
            rows_by_id.setdefault(p.sleeper_player_id, []).append(p)
        eligible, skipped = plan_correction(
            ids, {sid: [_player_state(p) for p in ps] for sid, ps in rows_by_id.items()},
            EXPECTED)

        print(f"Banco: {db_path}")
        print(f"Guarda: {EXPECTED}")
        print(f"\nElegíveis: {len(eligible)}/{len(TARGETS)}")
        for sid in eligible:
            p = rows_by_id[sid][0]
            print(f"  ok    {sid:>6}  {p.name:<22} salary=${int(p.salary)} "
                  f"espn_ref={p.espn_ref_value} cy={p.contract_year} css={p.contract_start_season}")
        for s in skipped:
            name = dict(TARGETS).get(s["sleeper_player_id"], "?")
            print(f"  PULADO {s['sleeper_player_id']:>6}  {name:<22} {s['reason']}")

        rollover_ok = _report_rollover([rows_by_id[sid][0] for sid in eligible])

    all_ok = len(eligible) == len(TARGETS) and rollover_ok
    print(f"\n--check: {'OK — 22/22 elegíveis, casos vivos conferem' if all_ok else 'ATENÇÃO — ver acima'}")
    return 0 if all_ok else 1


def _verify_backup(backup: Path, db_path: Path) -> bool:
    if not backup.exists():
        print(f"⛔ Backup não encontrado: {backup}")
        return False
    b, d = backup.stat().st_size, db_path.stat().st_size
    if b < 0.5 * d:
        print(f"⛔ Backup implausível: {b} bytes contra {d} do banco alvo")
        return False
    print(f"Backup conferido: {backup} ({b} bytes; banco alvo {d} bytes)")
    return True


def cmd_apply(db_path: Path, backup: Path) -> int:
    """Guarda → escrita+trilha (porta canônica) → verificação pós-escrita → commit."""
    from models import db, Player, PlayerHistory
    from contract_year_correction import apply_contract_year_correction, EVENT_TYPE

    # Gate: sem backup conferido, nenhuma escrita.
    if not _verify_backup(backup, db_path):
        return 1

    pre = _snapshot_players(db_path)

    app = _make_app(db_path)
    with app.app_context():
        result = apply_contract_year_correction(
            [sid for sid, _ in TARGETS], expected=EXPECTED, new_year=NEW_YEAR,
            reason=REASON, event_ref=EVENT_REF)
        _report_plan(result)

        if not result["applied"]:
            db.session.rollback()
            print("\nNada elegível — nenhuma escrita. (Já corrigido, ou estado divergente.)")
            return 1

        # Verificação in-transação antes do commit: releitura dos objetos encenados.
        bad = [a for a in result["applied"]
               if db.session.get(Player, a["player_id"]).contract_year != NEW_YEAR]
        if bad:
            db.session.rollback()
            print(f"⛔ Releitura in-transação divergente ({len(bad)}) — rollback, nada escrito.")
            return 1
        db.session.commit()
        applied = result["applied"]

        # Dry-run do rollover sobre o estado real pós-commit.
        players_now = [db.session.get(Player, a["player_id"]) for a in applied]
        rollover_ok = _report_rollover(players_now)

    # ── Verificação pós-commit por conexão independente (raw sqlite) ──────────
    post = _snapshot_players(db_path)
    applied_ids = {a["player_id"] for a in applied}
    errors = []

    if set(pre) != set(post):
        errors.append(f"linhas criadas/apagadas em players: {sorted(set(pre) ^ set(post))}")
    changed = {pid for pid in pre if pid in post
               and any(pre[pid][c] != post[pid][c] for c in pre[pid])}
    if changed != applied_ids:
        errors.append(f"linhas alteradas != elegíveis: {sorted(changed ^ applied_ids)}")
    for pid in applied_ids:
        diff_cols = {c for c in pre[pid] if pre[pid][c] != post[pid][c]}
        if not diff_cols <= {"contract_year", "updated_at"}:
            errors.append(f"player {pid}: colunas alteradas além do campo: {sorted(diff_cols)}")
        if post[pid]["contract_year"] != NEW_YEAR:
            errors.append(f"player {pid}: contract_year={post[pid]['contract_year']} (esperado {NEW_YEAR})")

    con = sqlite3.connect(str(db_path))
    trail = con.execute(
        "SELECT COUNT(*) FROM player_history WHERE event_type=? AND sleeper_event_ref=?",
        (EVENT_TYPE, EVENT_REF)).fetchone()[0]
    con.close()
    if trail != len(applied):
        errors.append(f"trilha: {trail} linhas em player_history (esperado {len(applied)})")
    if not rollover_ok:
        errors.append("dry-run do rollover: casos vivos não conferem")

    print(f"\nVerificação pós-escrita: {len(applied)} corrigidos; "
          f"{len(changed)} linhas alteradas; {trail} linhas de trilha.")
    if errors:
        print("⛔ FALHAS DE VERIFICAÇÃO (o commit JÁ ocorreu — avaliar restore do backup):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ OK — só contract_year (+updated_at) dos elegíveis mudou; trilha completa; "
          "casos vivos conferem.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OFF26-20-FIX: contract_year 2→1 nos 22 FAs de 2025")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only: guarda + dry-run")
    mode.add_argument("--apply", action="store_true", help="escreve (exige --backup conferível)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatório no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrão: env DYNASTY_DB")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        print(f"⛔ Banco não encontrado: {db_path}")
        return 1
    if args.apply and not args.backup:
        print("⛔ --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    return cmd_check(db_path) if args.check else cmd_apply(db_path, Path(args.backup))


if __name__ == "__main__":
    sys.exit(main())
