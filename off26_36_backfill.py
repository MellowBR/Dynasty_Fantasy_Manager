# -*- coding: utf-8 -*-
"""
off26_36_backfill.py — backfill dos 222 eventos de rollover de 2026 (OFF26-36, Parte 4).

O rollover de 17/08/2026 avançou 222 contratos gravando SÓ `SalaryHistory` — nenhum
evento de timeline (lacuna 222/222 medida na F1 do OFF26-36; omissão de nascença). O
rollover AO VIVO já foi consertado (grava `rollover`/`renewal` com ref
`rollover:<season>` — MAN-OFF26-36-P1P3); este runner preenche o retroativo de 2026.

⛔ FONTE CANÔNICA ÚNICA (lição F8 — nada de síntese sem fonte): as 222 rows de
`SalaryHistory` season 2026 com regra `VALORIZ%` / `Waiver Ano 2%` (222 rows / 222
jogadores, carimbo único 2026-08-17 21:34 — medido no seed em 09/09/2026; 0 renovações
pós-ano 4 em 2026). Cada row carrega jogador, salário, ano e regra — bastam.

RESSALVA DO TEAM_NAME (mapeada na F1): jogadores trocados por trade DEPOIS do rollover
teriam `team_name` anacrônico se o runner usasse o time atual. A reconstrução usa os
eventos `trade` do S1 (season 2026, criados após o carimbo do rollover): o time da
época = o LADO DE ORIGEM `(src→dst)` do trade MAIS ANTIGO pós-rollover. Nota
imparseável → fallback para o time atual, COM warning nominal (nunca silêncio).

Ref: `rollover:2026` — o formato que o rebuild F8 PRESERVA (deleta só ref NULL).
Idempotente pela UNIQUE `uq_player_history_event` + check-before-insert: segunda
execução cria ZERO.

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    # 0) BACKUP OBRIGATÓRIO (sem ele o --apply recusa escrever):
    sqlite3 /data/dynasty.db ".backup '/data/pre_off26_36_backfill.db'"

    # 1) Conferência read-only (contagem × esperado + reconstrução dos trocados):
    python off26_36_backfill.py --check

    # 2) Escrita (plano → insert → verificação → commit):
    python off26_36_backfill.py --apply --backup /data/pre_off26_36_backfill.db

    # Ensaio local: acrescentar --db <caminho de uma CÓPIA>
"""

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SEASON = 2026
EVENT_REF = f"rollover:{SEASON}"
# Contagem CONGELADA da medição (F1 do OFF26-36 + conferida no seed em 09/09/2026).
# existentes + a criar ≠ 222 → --check sai 1 e explica; não é guarda de escrita.
EXPECTED_TOTAL = 222
RULE_PREFIXES = ("VALORIZ", "Waiver Ano 2")
BACKFILL_TAG = "(backfill OFF26-36, 09/09/2026)"


# ── Núcleo puro ───────────────────────────────────────────────────────────────

def classify_rule(rule: str):
    """Regra do SalaryHistory → event_type do evento, ou None (fora do backfill).
    2026 não teve renovação pós-ano 4 (medido) — só `rollover` nasce daqui."""
    r = rule or ""
    if any(r.startswith(p) for p in RULE_PREFIXES):
        return "rollover"
    return None


def parse_trade_src(notes: str):
    """Origem `(src→dst)` de uma nota de trade do S1 — puro. None se imparseável."""
    m = re.search(r"\(([^()→]+)→[^()]*\)", notes or "")
    return m.group(1).strip() if m else None


def team_at_rollover(current_team: str, post_trades: list):
    """Time do jogador NO MOMENTO do rollover.

    post_trades: notas dos eventos de trade pós-rollover do jogador, na ordem
    cronológica. O time da época é a ORIGEM do trade mais antigo; sem trades →
    o time atual. Devolve (team_name, reconstruido: bool, warning|None)."""
    if not post_trades:
        return current_team, False, None
    src = parse_trade_src(post_trades[0])
    if src:
        return src, True, None
    return current_team, False, (
        f"nota de trade imparseável ({post_trades[0][:60]!r}) — "
        f"team_name caiu no time atual")


def plan_events(rows: list, existing_refs: set, trades_by_player: dict):
    """Decide o que criar — puro.

    rows: [{player_id, salary, contract_year, rule, current_team}].
    existing_refs: chaves (player_id, season, event_type, team_name, ref) já no banco.
    trades_by_player: player_id → [notas de trade pós-rollover, cronológicas].
    Devolve (events, skipped, warnings)."""
    events, skipped, warnings = [], [], []
    for row in rows:
        event_type = classify_rule(row["rule"])
        if not event_type:
            skipped.append({"player_id": row["player_id"],
                            "reason": f"regra fora do backfill: {row['rule']!r}"})
            continue
        team, reconstruido, warn = team_at_rollover(
            row["current_team"], trades_by_player.get(row["player_id"]) or [])
        if warn:
            warnings.append(f"player {row['player_id']}: {warn}")
        key = (row["player_id"], SEASON, event_type, team, EVENT_REF)
        if key in existing_refs:
            skipped.append({"player_id": row["player_id"],
                            "reason": "evento já existe — idempotência"})
            continue
        events.append({
            "player_id": row["player_id"], "season": SEASON,
            "event_type": event_type, "team_name": team,
            "salary": row["salary"], "contract_year": row["contract_year"],
            "notes": f"{row['rule']} {BACKFILL_TAG}",
            "sleeper_event_ref": EVENT_REF,
            "reconstruido": reconstruido,
        })
    return events, skipped, warnings


# ── Camada de IO ──────────────────────────────────────────────────────────────

def _db_path(cli_db: str = None) -> Path:
    """Caminho do banco, SEMPRE absoluto (OFF26-40: relativo faria o Flask-SQLAlchemy
    criar um banco vazio em instance/)."""
    return Path(cli_db or os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db")).resolve()


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco (sem o boot do app.py)."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _read_inputs():
    """Lê as rows do rollover + trades pós-rollover. O carimbo do rollover é DERIVADO
    das próprias rows (min created_at) — nenhum literal de data no filtro."""
    from models import db, SalaryHistory, PlayerHistory, Player

    like_any = [SalaryHistory.rule_applied.like(f"{p}%") for p in RULE_PREFIXES]
    sh_rows = (SalaryHistory.query
               .filter(SalaryHistory.season == SEASON, db.or_(*like_any))
               .all())
    if not sh_rows:
        return [], {}, set(), None

    carimbo = min(r.created_at for r in sh_rows if r.created_at)
    players = {p.id: p for p in Player.query.filter(
        Player.id.in_([r.player_id for r in sh_rows])).all()}
    rows = []
    for r in sh_rows:
        p = players.get(r.player_id)
        rows.append({"player_id": r.player_id, "salary": r.salary,
                     "contract_year": r.contract_year, "rule": r.rule_applied,
                     "current_team": (p.fantasy_team or "") if p else "",
                     "name": p.name if p else f"pid={r.player_id}"})

    trade_evs = (PlayerHistory.query
                 .filter(PlayerHistory.event_type == "trade",
                         PlayerHistory.season == SEASON,
                         PlayerHistory.created_at > carimbo)
                 .order_by(PlayerHistory.created_at.asc())
                 .all())
    trades_by_player = {}
    for ev in trade_evs:
        trades_by_player.setdefault(ev.player_id, []).append(ev.notes or "")

    existing = {(e.player_id, e.season, e.event_type, e.team_name, e.sleeper_event_ref)
                for e in PlayerHistory.query.filter(
                    PlayerHistory.sleeper_event_ref == EVENT_REF).all()}
    return rows, trades_by_player, existing, carimbo


def _count_ref(db_path: Path) -> int:
    con = sqlite3.connect(str(db_path))
    n = con.execute("SELECT COUNT(*) FROM player_history WHERE sleeper_event_ref=?",
                    (EVENT_REF,)).fetchone()[0]
    con.close()
    return n


def _verify_backup(backup: Path, db_path: Path) -> bool:
    if not backup.exists():
        print(f"⛔ Backup nao encontrado: {backup}")
        return False
    b, d = backup.stat().st_size, db_path.stat().st_size
    if b < 0.5 * d:
        print(f"⛔ Backup implausivel: {b} bytes contra {d} do banco alvo")
        return False
    print(f"Backup conferido: {backup} ({b} bytes; banco alvo {d} bytes)")
    return True


# ── Comandos ──────────────────────────────────────────────────────────────────

def _plan(db_path: Path):
    rows, trades_by_player, existing, carimbo = _read_inputs()
    events, skipped, warnings = plan_events(rows, existing, trades_by_player)
    return rows, events, skipped, warnings, existing, carimbo


def _report_plan(rows, events, skipped, warnings, existing, carimbo):
    print(f"\nRows de rollover no SalaryHistory {SEASON}: {len(rows)} "
          f"(carimbo derivado: {carimbo})")
    print(f"Eventos ja existentes ({EVENT_REF}): {len(existing)}")
    print(f"A criar: {len(events)}  |  pulados: {len(skipped)}")
    recon = [e for e in events if e["reconstruido"]]
    if recon:
        print(f"\nTeam_name RECONSTRUIDO pelos trades pos-rollover ({len(recon)}):")
        for e in recon:
            print(f"  pid {e['player_id']:>5}  {e['team_name']}")
    for w in warnings:
        print(f"  ⚠️  {w}")
    por_time = {}
    for e in events:
        por_time[e["team_name"]] = por_time.get(e["team_name"], 0) + 1
    if por_time:
        print("\nPor time (a criar):")
        for t, n in sorted(por_time.items()):
            print(f"  {t:<28} {n}")
    total = len(existing) + len(events)
    ok = total == EXPECTED_TOTAL
    print(f"\nTotal (existentes + a criar): {total}  |  esperado: {EXPECTED_TOTAL}  "
          f"→ {'OK' if ok else 'DIVERGENTE — conferir antes de aplicar'}")
    return ok


def cmd_check(db_path: Path) -> int:
    app = _make_app(db_path)
    with app.app_context():
        print(f"Banco: {db_path}")
        ok = _report_plan(*_plan(db_path))
    return 0 if ok else 1


def cmd_apply(db_path: Path, backup: Path) -> int:
    from models import db, PlayerHistory

    if not _verify_backup(backup, db_path):
        return 1

    pre_count = _count_ref(db_path)
    app = _make_app(db_path)
    with app.app_context():
        print(f"Banco: {db_path}")
        rows, events, skipped, warnings, existing, carimbo = _plan(db_path)
        ok = _report_plan(rows, events, skipped, warnings, existing, carimbo)
        if not ok:
            print("⛔ Plano divergente do esperado — nada escrito. "
                  "Rode --check e confira antes.")
            db.session.rollback()
            return 1
        if not events:
            print("\nNada a criar — backfill ja aplicado (idempotencia).")
            return 0
        for e in events:
            db.session.add(PlayerHistory(
                player_id=e["player_id"], season=e["season"],
                event_type=e["event_type"], team_name=e["team_name"],
                salary=e["salary"], contract_year=e["contract_year"],
                notes=e["notes"], sleeper_event_ref=e["sleeper_event_ref"],
            ))
        db.session.commit()

    # Verificação pós-commit por conexão independente (raw sqlite).
    post_count = _count_ref(db_path)
    print(f"\nVerificacao pos-escrita: {EVENT_REF} = {pre_count} -> {post_count} "
          f"(criados {post_count - pre_count}, plano {len(events)})")
    if post_count - pre_count != len(events) or post_count != EXPECTED_TOTAL:
        print("⛔ Contagem divergente (o commit JA ocorreu — avaliar restore do backup).")
        return 1
    print(f"✅ OK — {post_count}/{EXPECTED_TOTAL} eventos {EVENT_REF}; "
          f"ref presente em todos (o rebuild F8 os preserva).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=f"OFF26-36 Parte 4: backfill dos {EXPECTED_TOTAL} eventos de "
                    f"rollover {SEASON} a partir do SalaryHistory")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="read-only: plano + reconstrucao + contagem x esperado")
    mode.add_argument("--apply", action="store_true",
                      help="escreve (exige --backup conferivel)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatorio no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrao: env DYNASTY_DB")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        print(f"⛔ Banco nao encontrado: {db_path}")
        return 1
    if args.apply and not args.backup:
        print("⛔ --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    return cmd_check(db_path) if args.check else cmd_apply(db_path, Path(args.backup))


if __name__ == "__main__":
    sys.exit(main())
