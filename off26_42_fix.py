"""
off26_42_fix.py — runner ONE-SHOT do reparo OFF26-42: 5 contratos MORTOS que sobreviveram ao re-add.

Diagnose MAN-MCLAURIN-SALARIO-REG-F1 (18/11/2026, commit `f1bc4fc`) + leitura de produção do owner
(18/11, modo A confirmado): drop e add inteiros entre dois syncs não passam pela régua do sync
(o passo 7 só captura o re-add se `is_dropped=True` já estiver no banco). Pela régua canônica
(OFF26-37), os 5 abaixo foram readquiridos com contrato MORTO → caso 3 → contrato NOVO, ano 1.

O QUE ESCREVE (por alvo, numa transação só, pela porta canônica `models.record_acquisition`):
  contract_year=1 · contract_start_season=2026 · acquisition_type='free_agent' · salary=$1,
  + SalaryHistory + AuctionLog (token `[ref:tx:<add>]`) + evento PlayerHistory (ref `tx:<add>`).
  A marca `tx:<add>` é o MESMO formato que o caso 3 do sync grava: se a porta do sync for fechada
  depois, ela reconhece estes 5 como já registrados (`acquisition_already_recorded`).

DECISÕES DO OWNER (18/11/2026), executadas e não rediscutidas:
  1. ESPN definitivo: a porta chama `set_espn_value(..., is_final=False)` por default e REBAIXA a
     linha do store de definitiva para provisória (4ª armadilha, vizinha do OFF26-39; o caso 3 do
     sync tem o mesmo efeito). Este runner lê (raw, adjusted, is_final) ANTES e, logo após a porta,
     restaura pelo MESMO helper canônico (`set_espn_value`). Verificação pós-commit falha se a linha
     mudar.
  2. Gordon: a porta grava `team_id = time passado`, então recebe o time ATUAL (12) — nunca muda
     time. Quem fez o add (roster 5) e a trade posterior (15/10) vão na NOTA. A aplicação dele
     depende de aviso do owner ao dono do time 12: `--exclude 12495` aplica os outros 4 e o lista
     como PENDENTE; uma execução posterior sem o `--exclude` aplica só ele (os 4 saem como já
     registrados).
  3. Pendência aberta na fila de arbitragem para um alvo → esse alvo é PULADO (guarda obrigatória).
     O runner não lê, não decide, não fecha e não cria pendência.

GUARDAS DE BANCO (restrições do prompt MAN-OFF26-42-FIX):
  * `--db` é OBRIGATÓRIO e ABSOLUTO — ⛔ não existe fallback para `DYNASTY_DB` (no Render essa env
    é o banco VIVO) nem para a raiz do app (o seed do git).
  * A PRIMEIRA linha de toda execução é o caminho absoluto do banco aberto.
  * `--apply` exige `--confirm-db` idêntico (após resolver) ao `--db`.
  * Depois de abrir, o runner confere pelo `PRAGMA database_list` que o arquivo aberto pelo engine
    É o confirmado — senão aborta antes de ler qualquer coisa.
  * `--check` abre o banco em `mode=ro` (SQLite recusa qualquer escrita).
  * NÃO importa `app.py` (o módulo roda `create_app()` no import, contra `DYNASTY_DB`): o app é um
    Flask mínimo com só o bind do banco — sem boot, sem migração, sem seed, sem sync.
  * `--backup` só é conferido por `stat` (existência, tamanho, não ser o mesmo arquivo do alvo) —
    nunca aberto.

O QUE SÓ CONFERE (nunca escreve): o caso McCarthy (11565) e os 7 controles. A verificação
pós-escrita falha se QUALQUER linha de `players` fora dos aplicados mudar.

Uso (Render Shell; ver runbook na seção OFF26-42 do improvements.md):
    python off26_42_fix.py --check --db /data/<copia>.db
    python off26_42_fix.py --apply --db /data/<copia>.db --confirm-db /data/<copia>.db \\
        --backup /data/pre_off26_42_18_11.db [--exclude 12495]
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

LEAGUE_ID = "1316547584378048512"
API = "https://api.sleeper.app/v1"
SEASON = 2026

# ── Lista CONGELADA (estado de prod lido pelo owner em 18/11/2026) ─────────────────────────────
# `team_owner` = sleeper_owner_id do time ATUAL (identidade estável, nunca nome). `add_owner` =
# quem fez o add (só difere no Gordon). `expected` = guarda pré-escrita, campo a campo.
COHORT = [
    {"sid": "5927", "name": "Terry McLaurin", "add_tx": "1419159991641780224",
     "team_owner": "1126909140380569600", "add_owner": "1126909140380569600",
     "expected": {"contract_year": 3, "contract_start_season": 2024,
                  "acquisition_type": "auction_draft", "salary": 13.0},
     "note": "OFF26-42-FIX caso 3: drop r2 20/10 19:15 UTC -> add FA r8 23/10 00:50 UTC (53,6h > 48h)"},
    {"sid": "9511", "name": "Keaton Mitchell", "add_tx": "1427661333444186112",
     "team_owner": "205848303030505472", "add_owner": "205848303030505472",
     "expected": {"contract_year": 1, "contract_start_season": 2026,
                  "acquisition_type": "auction_draft", "salary": 7.0},
     "note": "OFF26-42-FIX caso 3: drop r6 10/11 20:41 UTC -> add FA r4 15/11 11:51 UTC (111,2h > 48h)"},
    {"sid": "9502", "name": "Tank Dell", "add_tx": "1400817370229972992",
     "team_owner": "695859970096328704", "add_owner": "695859970096328704",
     "expected": {"contract_year": 2, "contract_start_season": 2025,
                  "acquisition_type": "fa_auction", "salary": 1.0},
     "note": "OFF26-42-FIX caso 3: drop intertemporada 30/08 -> add FA r9 02/09 (pre-regua no sync)"},
    {"sid": "12547", "name": "Kyle Williams", "add_tx": "1399915496882610176",
     "team_owner": "1133812910268010496", "add_owner": "1133812910268010496",
     "expected": {"contract_year": 1, "contract_start_season": 2025,
                  "acquisition_type": "rookie_draft", "salary": 1.0},
     "note": "OFF26-42-FIX caso 3: drop intertemporada 29/07 -> add FA r11 30/08 (pre-regua no sync)"},
    {"sid": "12495", "name": "Ollie Gordon II", "add_tx": "1399932595008991232",
     "team_owner": "1133818177651224576", "add_owner": "1130162144764506112",
     "expected": {"contract_year": 2, "contract_start_season": 2025,
                  "acquisition_type": "rookie_draft", "salary": 1.0},
     "note": ("OFF26-42-FIX caso 3: add FA por Cangaceiros (r5) 30/08; trade 15/10 "
              "tx 1416520881219391488 -> time 12 (time atual)")},
]
GORDON_SID = "12495"

DUE = {"contract_year": 1, "contract_start_season": SEASON,
       "acquisition_type": "free_agent", "salary": 1.0}

# Só leitura: estado esperado = o devido do caso 3 (já aplicado pelo sync ou por outra via).
CONTROLS = {"11539": "Jake Bates", "12540": "Chimere Dike", "12718": "Konata Mumpfield",
            "4993": "Mike Gesicki", "6039": "Ty Johnson", "7839": "Evan McPherson",
            "96": "Aaron Rodgers"}
MCCARTHY = {"sid": "11565", "name": "J.J. McCarthy", "add_tx": "1418306669443555328",
            "expected": {"contract_year": 1, "contract_start_season": SEASON,
                         "acquisition_type": "fa_waiver", "salary": 1.0}}

GUARD_FIELDS = ("contract_year", "contract_start_season", "acquisition_type", "salary")
ALLOWED_PLAYER_COLS = {"contract_year", "contract_start_season", "acquisition_type",
                       "salary", "updated_at"}
AUCTION_NOTE_MAX = 200


# ── Núcleo puro ────────────────────────────────────────────────────────────────────────────────

def event_ref(t: dict) -> str:
    return f"tx:{t['add_tx']}"


def note_fits(note: str, ref: str, limit: int = AUCTION_NOTE_MAX) -> bool:
    """Reproduz o que a porta faz (concatena o token e corta em 200): o token sobrevive?"""
    tag = f"[ref:{ref}]"
    return tag in ((note or "") + " " + tag).strip()[:limit]


def resolve_db_args(db, confirm, apply: bool):
    """(Path|None, erro|None). ⛔ Sem fallback: --db ausente é erro, nunca DYNASTY_DB."""
    if not db:
        return None, "--db e obrigatorio (sem fallback para DYNASTY_DB nem para o seed)"
    if not Path(db).is_absolute():
        return None, f"--db precisa ser caminho ABSOLUTO (recebido: {db})"
    path = Path(db).resolve()
    if not path.is_file():
        return None, f"banco nao encontrado: {path}"
    if apply:
        if not confirm:
            return path, "--apply exige --confirm-db com o MESMO caminho do --db"
        if not Path(confirm).is_absolute() or Path(confirm).resolve() != path:
            return path, f"--confirm-db ({confirm}) != banco aberto ({path}) - nenhuma escrita"
    return path, None


def guard_mismatches(state: dict, expected: dict) -> list:
    out = []
    for f in GUARD_FIELDS:
        a, e = state.get(f), expected[f]
        if (float(a or 0) != float(e)) if f == "salary" else (a != e):
            out.append(f"{f}={a!r} (esperado {e!r})")
    return out


def plan(cohort: list, states: dict, live, excluded) -> tuple:
    """Puro. Devolve (eligible_sids, skipped[{sid, reason, kind}]).
    kind: 'excluido' (pendente por decisão do operador) | 'ja_registrado' | 'bloqueio'."""
    eligible, skipped = [], []
    for t in cohort:
        sid = t["sid"]
        rows = states.get(sid) or []

        def skip(reason, kind="bloqueio"):
            skipped.append({"sid": sid, "name": t["name"], "reason": reason, "kind": kind})

        if sid in excluded:
            skip("PENDENTE - excluido pelo operador nesta execucao (--exclude)", "excluido")
            continue
        if not rows:
            skip("nao encontrado no banco")
            continue
        if len(rows) > 1:
            skip(f"{len(rows)} linhas para o mesmo sleeper_player_id - ambiguo")
            continue
        st = rows[0]
        if st["already_recorded"]:
            skip(f"ja registrado ({event_ref(t)}) - nada a fazer", "ja_registrado")
            continue
        if st["open_pendencies"]:
            skip(f"pendencia ABERTA na fila de arbitragem (ids {st['open_pendencies']}) - "
                 f"o runner nao arbitra")
            continue
        if live is not None:
            lv = live.get(sid) or {}
            if lv.get("roster_owner") != t["team_owner"]:
                skip(f"ao vivo no roster do owner {lv.get('roster_owner')} "
                     f"(esperado {t['team_owner']}) - membership mudou desde a medicao")
                continue
            if lv.get("add_tx") != t["add_tx"]:
                skip(f"ultimo add ao vivo e tx {lv.get('add_tx')} (congelado {t['add_tx']})")
                continue
            if not (lv.get("acao") == "contrato_novo" and lv.get("caso") == 3
                    and lv.get("acq_type") == DUE["acquisition_type"]):
                skip(f"regua ao vivo nao devolve caso 3 free_agent: {lv.get('acao')} "
                     f"caso={lv.get('caso')} {lv.get('acq_type')}")
                continue
        if st["team_owner"] != t["team_owner"]:
            skip(f"time no banco (owner {st['team_owner']}) != esperado ({t['team_owner']})")
            continue
        if st["is_dropped"]:
            skip("is_dropped=1 no banco")
            continue
        if bool(st["is_my_team"]) != bool(st["team_is_my_team"]):
            # A porta grava player.is_my_team = team.is_my_team: com a coluna atrasada ela
            # alteraria uma coluna fora das devidas (pego pela verificação no ensaio de mecânica).
            skip(f"is_my_team do jogador ({st['is_my_team']}) != do time "
                 f"({st['team_is_my_team']}) - a porta alteraria a coluna")
            continue
        mm = guard_mismatches(st, t["expected"])
        if mm:
            skip("guarda: " + "; ".join(mm))
            continue
        if (st["espn_ref_value"] or 0) > 0:
            store = st["store"]
            if store is None:
                skip(f"sem linha no espn_value_store ({sid}, {SEASON}) - a porta CRIARIA uma "
                     f"(o ESPN nao ficaria identico)")
                continue
            if float(store["espn_adjusted"] or 0) != float(st["espn_ref_value"] or 0):
                skip(f"espn_ref_value {st['espn_ref_value']} != store {store['espn_adjusted']} - "
                     f"divergencia coluna x store fora do escopo")
                continue
        eligible.append(sid)
    return eligible, skipped


def control_divergences(states: dict) -> list:
    out = []
    for sid, name in CONTROLS.items():
        rows = states.get(sid) or []
        if len(rows) != 1:
            out.append(f"{sid} {name}: {len(rows)} linhas no banco")
            continue
        mm = guard_mismatches(rows[0], DUE)
        if mm:
            out.append(f"{sid} {name}: " + "; ".join(mm))
    return out


def projected_next(state: dict, after: bool) -> int:
    from salary_engine import project_next_salary
    base = dict(DUE) if after else {f: state[f] for f in GUARD_FIELDS}
    return project_next_salary(SimpleNamespace(
        contract_year=base["contract_year"], salary=base["salary"],
        acquisition_type=base["acquisition_type"], espn_ref_value=state["espn_ref_value"]))


# ── IO: Sleeper (GET) ──────────────────────────────────────────────────────────────────────────

def _get_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": "dynasty-manager-off26-42-fix"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def fetch_live(fetch=_get_json) -> tuple:
    """Rosters + varredura COMPLETA (legs 0..18, status complete, sem trade) e a régua ao vivo
    (`contract_regua.decide_readd`, helper ÚNICO) para os 5 + McCarthy. Qualquer falha levanta —
    sem leitura completa não há escrita."""
    import contract_regua as cr
    lg = fetch(f"{API}/league/{LEAGUE_ID}")
    wcd = (lg.get("settings") or {}).get("waiver_clear_days")
    if wcd is None:
        raise RuntimeError("settings.waiver_clear_days ausente")
    state = fetch(f"{API}/state/nfl")
    rosters = fetch(f"{API}/league/{LEAGUE_ID}/rosters")
    owner_by_sid = {}
    for ro in rosters:
        for key in ("players", "reserve", "taxi"):
            for pid in (ro.get(key) or []):
                owner_by_sid[str(pid)] = str(ro.get("owner_id") or "")
    index = {}
    for leg in range(19):
        txs = fetch(f"{API}/league/{LEAGUE_ID}/transactions/{leg}")
        if txs is None:
            raise RuntimeError(f"transactions leg {leg} indisponivel")
        for tx in txs:
            if tx.get("status") != "complete" or tx.get("type") == "trade":
                continue
            rec = {"ts": cr.tx_timestamp(tx), "tx_id": str(tx.get("transaction_id")),
                   "type": tx.get("type")}
            adds, drops = tx.get("adds") or {}, tx.get("drops") or {}
            for s in adds:
                index.setdefault(str(s), {"adds": [], "drops": []})["adds"].append(dict(rec))
            for s in drops:
                if s not in adds:
                    index.setdefault(str(s), {"adds": [], "drops": []})["drops"].append(dict(rec))
    window = cr.waiver_window_ms(wcd)
    start = cr.season_start_ms(state["season_start_date"])
    out = {}
    for sid in [t["sid"] for t in COHORT] + [MCCARTHY["sid"]]:
        e = index.get(sid) or {}
        add = cr.latest_before(e.get("adds"))
        drop = cr.latest_before(e.get("drops"), before_ts_ms=add["ts"] if add else None)
        d = cr.decide_readd(add=add, drop=drop, window_ms=window, start_ms=start)
        out[sid] = {"roster_owner": owner_by_sid.get(sid), "add_tx": add and add["tx_id"],
                    "acao": d.get("acao"), "caso": d.get("caso"), "acq_type": d.get("acq_type"),
                    "motivo": d.get("motivo")}
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return out, f"Sleeper ao vivo ({when}; waiver_clear_days={wcd}; {len(owner_by_sid)} rosterados)"


# ── IO: banco ──────────────────────────────────────────────────────────────────────────────────

def _make_app(db_path: Path, read_only: bool):
    """Flask mínimo, só o bind. ⛔ Não importa app.py (create_app roda no import, contra a env)."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    uri = (f"sqlite:///file:{db_path.as_posix()}?mode=ro&uri=true" if read_only
           else "sqlite:///" + db_path.as_posix())
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


class _bound:
    """`with _bound(path, ro):` = contexto do app mínimo + descarte do engine na saída (nenhum
    handle do arquivo sobrevive ao bloco — relevante no Windows e para a conexão raw seguinte)."""

    def __init__(self, db_path: Path, read_only: bool):
        self.app = _make_app(db_path, read_only)

    def __enter__(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        return self.app

    def __exit__(self, *exc):
        from models import db
        try:
            db.session.remove()
            db.engine.dispose()
        finally:
            self.ctx.pop()
        return False


def _opened_file() -> Path:
    from models import db
    from sqlalchemy import text
    rows = db.session.execute(text("PRAGMA database_list")).fetchall()
    main = next(r for r in rows if r[1] == "main")
    return Path(main[2]).resolve()


def _read_states(sids: list) -> dict:
    from models import (Player, ContractPendency, EspnValueStore,
                        acquisition_already_recorded)
    refs = {t["sid"]: event_ref(t) for t in COHORT}
    refs[MCCARTHY["sid"]] = f"tx:{MCCARTHY['add_tx']}"
    out = {}
    for p in Player.query.filter(Player.sleeper_player_id.in_(sids)).all():
        sid = p.sleeper_player_id
        store = EspnValueStore.query.filter_by(sleeper_player_id=sid, season=SEASON).first()
        pend = [c.id for c in ContractPendency.query.filter_by(
            player_id=p.id, status="aberta").all()]
        out.setdefault(sid, []).append({
            "player_id": p.id, "name": p.name, "team_id": p.team_id,
            "team": p.team_rel.name if p.team_rel else "",
            "team_owner": p.team_rel.sleeper_owner_id if p.team_rel else "",
            "contract_year": p.contract_year, "contract_start_season": p.contract_start_season,
            "acquisition_type": p.acquisition_type, "salary": p.salary,
            "espn_ref_value": p.espn_ref_value, "is_on_ir": p.is_on_ir,
            "is_my_team": p.is_my_team,
            "team_is_my_team": p.team_rel.is_my_team if p.team_rel else None,
            "is_dropped": p.is_dropped, "open_pendencies": pend,
            "already_recorded": bool(refs.get(sid)) and acquisition_already_recorded(refs[sid]),
            "store": None if store is None else {
                "espn_raw": store.espn_raw, "espn_adjusted": store.espn_adjusted,
                "is_final": bool(store.is_final)},
        })
    return out


def _raw(db_path: Path):
    return sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)


def _snap(db_path: Path) -> dict:
    """Foto independente (conexão raw, read-only) do que a verificação compara."""
    con = _raw(db_path)
    try:
        pcols = [r[1] for r in con.execute("PRAGMA table_info(players)")]
        players = {r[0]: dict(zip(pcols, r))
                   for r in con.execute(f"SELECT {', '.join(pcols)} FROM players")}
        store = {(r[0], r[1]): (r[2], r[3], r[4]) for r in con.execute(
            "SELECT sleeper_player_id, season, espn_raw, espn_adjusted, is_final "
            "FROM espn_value_store")}
        pend = con.execute("SELECT * FROM contract_pendencies ORDER BY id").fetchall()
        counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("salary_history", "auction_log", "player_history")}
        teams = {r[0]: r[1] for r in con.execute("SELECT id, name FROM teams")}
        payroll = {tid: 0.0 for tid in teams}
        for tid, s in con.execute("SELECT team_id, SUM(salary) FROM players "
                                  "WHERE is_dropped=0 AND team_id IS NOT NULL GROUP BY team_id"):
            payroll[tid] = float(s or 0)
    finally:
        con.close()
    return {"players": players, "store": store, "pend": pend, "counts": counts,
            "teams": teams, "payroll": payroll}


def _print_payroll(teams: dict, before: dict, after: dict) -> None:
    print(f"\n  {'time':<30} {'antes':>7} {'depois':>7} {'delta':>6}")
    for tid in sorted(teams):
        b, a = before.get(tid, 0.0), after.get(tid, 0.0)
        print(f"  {str(tid) + ' ' + teams[tid][:27]:<30} {b:>7.0f} {a:>7.0f} {a - b:>+6.0f}")
    tb, ta = sum(before.values()), sum(after.values())
    print(f"  {'TOTAL DA LIGA':<30} {tb:>7.0f} {ta:>7.0f} {ta - tb:>+6.0f}")


def _header(db_path: Path, env_db) -> None:
    """Segunda linha da saída (a primeira, 'Banco aberto:', sai do main antes de tudo)."""
    viva = env_db and Path(env_db).resolve() == db_path
    print(f"DYNASTY_DB do ambiente: {env_db or '(ausente)'} -> "
          f"{'⚠️  ALVO = BANCO VIVO' if viva else 'alvo NAO e o banco vivo (copia/ensaio)'}")


def _report_target(t: dict, st: dict) -> None:
    print(f"\n  {t['sid']:>6}  {st['name']}  (time {st['team_id']} {st['team']}; IR={st['is_on_ir']})")
    print(f"          nota: {t['note']}")
    for f in GUARD_FIELDS:
        mark = "  " if str(st[f]) == str(DUE[f]) else " *"
        print(f"        {mark}{f:<24} {str(st[f]):>14} -> {str(DUE[f]):>14}")
    s = st["store"]
    print(f"          espn_ref_value {st['espn_ref_value']}; store {SEASON}: "
          f"{'(sem linha)' if s is None else s} -> PRESERVADO (restaurado apos a porta)")
    print(f"          projecao {SEASON + 1}: ${projected_next(st, after=False)} hoje -> "
          f"${projected_next(st, after=True)} pos-reparo")


def _report_readonly(states: dict, live) -> list:
    div = control_divergences(states)
    print(f"\nControles (so leitura, devido = ano 1 · {SEASON} · free_agent · $1): "
          f"{len(CONTROLS) - len(div)}/{len(CONTROLS)} conferem")
    for d in div:
        print(f"  ⛔ divergencia: {d}")
    m = (states.get(MCCARTHY["sid"]) or [None])[0]
    lv = (live or {}).get(MCCARTHY["sid"]) or {}
    print(f"\nCaso McCarthy ({MCCARTHY['sid']}, so leitura):")
    if m is None:
        print("  nao encontrado no banco")
    else:
        mm = guard_mismatches(m, MCCARTHY["expected"])
        print(f"  banco: ${m['salary']:.0f} · ano {m['contract_year']} · "
              f"{m['contract_start_season']} · {m['acquisition_type']} -> "
              f"{'confere com o devido' if not mm else 'DIVERGE: ' + '; '.join(mm)}")
        if live is not None:
            print(f"  regua ao vivo: {lv.get('acao')} caso={lv.get('caso')} canal={lv.get('acq_type')} "
                  f"(add tx {lv.get('add_tx')}; congelado {MCCARTHY['add_tx']}) -> canal gravado "
                  f"{'CONFERE' if lv.get('acq_type') == m['acquisition_type'] else 'NAO confere'}")
        print(f"  token [ref:tx:{MCCARTHY['add_tx']}] no auction_log: {m['already_recorded']}")
    return div


# ── Comandos ───────────────────────────────────────────────────────────────────────────────────

def _all_sids() -> list:
    return [t["sid"] for t in COHORT] + list(CONTROLS) + [MCCARTHY["sid"]]


def cmd_check(db_path: Path, excluded: set, live=None, offline: bool = False) -> int:
    if not offline and live is None:
        try:
            live, source = fetch_live()
        except Exception as exc:
            print(f"⛔ Falha na leitura ao vivo do Sleeper ({exc.__class__.__name__}: {exc}). "
                  f"Use --offline para inspecionar sem rede (nao vale no --apply).")
            return 1
        print(f"Cruzamento: {source}")
    elif offline:
        print("⚠️  MODO OFFLINE - sem cruzamento com o Sleeper. So para inspecao.")
    from models import db, get_current_season
    with _bound(db_path, read_only=True):
        opened = _opened_file()
        if opened != db_path:
            print(f"⛔ O engine abriu {opened}, nao {db_path}. Abortado.")
            return 1
        if get_current_season() != SEASON:
            print(f"⛔ current_season={get_current_season()} != {SEASON}. Abortado.")
            return 1
        states = _read_states(_all_sids())
        eligible, skipped = plan(COHORT, states, None if offline else live, excluded)
        print(f"\nAlvos: {len(COHORT)} congelados; a corrigir: {len(eligible)}")
        for t in COHORT:
            if t["sid"] in eligible:
                _report_target(t, states[t["sid"]][0])
        for s in skipped:
            print(f"\n  {'PENDENTE' if s['kind'] == 'excluido' else 'PULADO':<8} "
                  f"{s['sid']:>6}  {s['name']:<18} {s['reason']}")
        div = _report_readonly(states, None if offline else live)
        db.session.rollback()
    snap = _snap(db_path)
    after = dict(snap["payroll"])
    for sid in eligible:
        st = states[sid][0]
        after[st["team_id"]] = after.get(st["team_id"], 0.0) + DUE["salary"] - float(st["salary"])
    print("\nFolha por time (projetada se aplicar):")
    _print_payroll(snap["teams"], snap["payroll"], after)
    done = [s for s in skipped if s["kind"] == "ja_registrado"]
    blocked = [s for s in skipped if s["kind"] == "bloqueio"]
    expected_n = len([t for t in COHORT if t["sid"] not in excluded]) - len(done)
    ok = len(eligible) == expected_n and not blocked and not div
    print(f"\n--check: {'OK' if ok else 'ATENCAO'} - {len(eligible)}/{expected_n} a corrigir; "
          f"{len(done)} ja registrado(s); {len(blocked)} bloqueado(s); "
          f"{len(div)} divergencia(s) nos controles")
    return 0 if ok else 1


def _verify_backup(backup: Path, db_path: Path) -> bool:
    if not backup.is_absolute() or not backup.is_file():
        print(f"⛔ Backup nao encontrado (ou caminho relativo): {backup}")
        return False
    if os.path.samefile(backup, db_path):
        print("⛔ --backup e o PROPRIO banco alvo. Nenhuma escrita.")
        return False
    b, d = backup.stat().st_size, db_path.stat().st_size
    if b < 0.5 * d:
        print(f"⛔ Backup implausivel: {b} bytes contra {d} do alvo")
        return False
    print(f"Backup conferido por stat (nao aberto): {backup} ({b} bytes; alvo {d} bytes)")
    return True


def cmd_apply(db_path: Path, backup: Path, excluded: set, live=None) -> int:
    if not _verify_backup(backup, db_path):
        return 1
    if live is None:
        try:
            live, source = fetch_live()
        except Exception as exc:
            print(f"⛔ Falha na leitura ao vivo do Sleeper ({exc.__class__.__name__}: {exc}). "
                  f"Nenhuma escrita.")
            return 1
        print(f"Cruzamento: {source}")
    from models import db, Player, get_current_season, record_acquisition, set_espn_value
    pre = _snap(db_path)
    applied = []
    with _bound(db_path, read_only=False):
        opened = _opened_file()
        if opened != db_path:
            print(f"⛔ O engine abriu {opened}, nao {db_path}. Nenhuma escrita.")
            return 1
        if get_current_season() != SEASON:
            print(f"⛔ current_season={get_current_season()} != {SEASON}. Nenhuma escrita.")
            return 1
        states = _read_states(_all_sids())
        eligible, skipped = plan(COHORT, states, live, excluded)
        for s in skipped:
            print(f"  {'PENDENTE' if s['kind'] == 'excluido' else 'PULADO':<8} "
                  f"{s['sid']:>6}  {s['name']:<18} {s['reason']}")
        if not eligible:
            db.session.rollback()
            blocked = [s for s in skipped if s["kind"] == "bloqueio"]
            print(f"\nNada a aplicar - zero escrita. "
                  f"({len(skipped)} pulados; {len(blocked)} por bloqueio)")
            return 1 if blocked else 0
        by_sid = {t["sid"]: t for t in COHORT}
        for sid in eligible:
            t, st = by_sid[sid], states[sid][0]
            ref = event_ref(t)
            if not note_fits(t["note"], ref):
                db.session.rollback()
                print(f"⛔ {sid}: nota longa demais - o token [ref:] seria truncado. Nada escrito.")
                return 1
            player = db.session.get(Player, st["player_id"])
            espn = player.espn_ref_value or 0.0
            _p, salary = record_acquisition(
                team=player.team_rel, acquisition_type=DUE["acquisition_type"], season=SEASON,
                player=player, value_paid=0.0, espn_adjusted=espn,
                sleeper_player_id=player.sleeper_player_id, event_ref=ref, notes=t["note"])
            store = st["store"]
            if store is not None:   # decisão 1: restaura (raw, adjusted, is_final) pelo helper
                set_espn_value(player, SEASON, store["espn_adjusted"], raw=store["espn_raw"],
                               is_final=store["is_final"])
            if float(salary) != DUE["salary"]:
                db.session.rollback()
                print(f"⛔ {sid}: porta devolveu ${salary} (esperado $1). Rollback, nada escrito.")
                return 1
            applied.append({"sid": sid, "player_id": player.id, "name": player.name,
                            "team_id": player.team_id, "antes": st, "ref": ref})
            print(f"  ok       {sid:>6}  {player.name:<18} time {player.team_id}  "
                  f"ano {st['contract_year']}->1  css {st['contract_start_season']}->{SEASON}  "
                  f"{st['acquisition_type']}->free_agent  ${st['salary']:.0f}->$1")
        db.session.commit()

    # ── Verificação pós-commit por conexão independente (raw, read-only) ──────────────────────
    post = _snap(db_path)
    ids = {a["player_id"] for a in applied}
    sids = {a["sid"] for a in applied}
    errors = []
    if set(pre["players"]) != set(post["players"]):
        errors.append("linhas criadas/apagadas em players")
    changed = {pid for pid in pre["players"] if pid in post["players"]
               and pre["players"][pid] != post["players"][pid]}
    if changed != ids:
        errors.append(f"linhas de players alteradas != aplicadas: {sorted(changed ^ ids)}")
    for a in applied:
        b, p = pre["players"][a["player_id"]], post["players"][a["player_id"]]
        cols = {c for c in b if b[c] != p[c]}
        if not cols <= ALLOWED_PLAYER_COLS:
            errors.append(f"{a['sid']}: colunas alem das devidas: {sorted(cols - ALLOWED_PLAYER_COLS)}")
        final = {f: p[f] for f in GUARD_FIELDS}
        if guard_mismatches(final, DUE):
            errors.append(f"{a['sid']}: estado final {final} != devido")
    if pre["store"] != post["store"]:
        diff = sorted(k for k in set(pre["store"]) | set(post["store"])
                      if pre["store"].get(k) != post["store"].get(k))
        errors.append(f"espn_value_store mudou (raw/adjusted/is_final): {diff}")
    if pre["pend"] != post["pend"]:
        errors.append("contract_pendencies mudou")
    for tbl in ("salary_history", "auction_log"):
        if post["counts"][tbl] - pre["counts"][tbl] != len(applied):
            errors.append(f"{tbl}: +{post['counts'][tbl] - pre['counts'][tbl]} (esperado +{len(applied)})")
    con = _raw(db_path)
    try:
        for a in applied:
            n_log = con.execute("SELECT COUNT(*) FROM auction_log WHERE notes LIKE ?",
                                (f"%[ref:{a['ref']}]%",)).fetchone()[0]
            n_ev = con.execute("SELECT COUNT(*) FROM player_history WHERE player_id=? AND "
                               "sleeper_event_ref=? AND event_type='free_agent'",
                               (a["player_id"], a["ref"])).fetchone()[0]
            n_sh = con.execute("SELECT COUNT(*) FROM salary_history WHERE player_id=? AND "
                               "season=? AND salary=1 AND contract_year=1",
                               (a["player_id"], SEASON)).fetchone()[0]
            if n_log != 1 or n_ev < 1 or n_sh < 1:
                errors.append(f"{a['sid']}: trilha incompleta (auction_log {n_log}, "
                              f"timeline {n_ev}, salary_history {n_sh})")
    finally:
        con.close()
    exp_delta = {}
    for a in applied:
        exp_delta[a["team_id"]] = exp_delta.get(a["team_id"], 0.0) + DUE["salary"] - float(a["antes"]["salary"])
    for tid in pre["teams"]:
        got = post["payroll"].get(tid, 0.0) - pre["payroll"].get(tid, 0.0)
        if abs(got - exp_delta.get(tid, 0.0)) > 1e-9:
            errors.append(f"folha do time {tid}: delta {got:+.0f} (esperado {exp_delta.get(tid, 0.0):+.0f})")

    print(f"\nVerificacao pos-escrita: {len(applied)} aplicados; {len(changed)} linhas de players alteradas")
    for a in applied:
        p = post["players"][a["player_id"]]
        print(f"  {a['sid']:>6} {a['name']:<18} time {p['team_id']} IR={p['is_on_ir']} "
              f"espn {p['espn_ref_value']} store {post['store'].get((a['sid'], SEASON))} "
              f"proj {SEASON + 1} ${projected_next({**{f: p[f] for f in GUARD_FIELDS}, 'espn_ref_value': p['espn_ref_value']}, after=False)}")
    print("\nFolha por time:")
    _print_payroll(pre["teams"], pre["payroll"], post["payroll"])
    pend = [s for s in skipped if s["kind"] == "excluido"]
    for s in pend:
        print(f"\n  PENDENTE {s['sid']} {s['name']}: aplicar depois com o mesmo comando sem --exclude")
    if errors:
        print("\n⛔ FALHAS DE VERIFICACAO (o commit JA ocorreu - avaliar restore do backup):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"\n✅ OK - {len(applied)} no devido; ESPN identico; time/IR intactos; pendencias "
          f"intactas; trilha completa; nenhuma outra linha tocada.")
    return 0


class _ArgError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgError(message)


def _peek_db(argv) -> str:
    for i, a in enumerate(argv):
        if a == "--db" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--db="):
            return a.split("=", 1)[1]
    return ""


def main(argv=None, live=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    env_db = os.environ.get("DYNASTY_DB")
    ap = _Parser(description="OFF26-42-FIX: caso 3 da regua nos 5 contratos mortos")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("--db")
    ap.add_argument("--confirm-db")
    ap.add_argument("--backup")
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--offline", action="store_true")
    try:
        args = ap.parse_args(argv)
    except _ArgError as exc:
        peek = _peek_db(argv)
        print(f"Banco aberto: (nenhum) - argumentos invalidos; --db recebido: {peek or '(ausente)'}")
        print(f"⛔ {exc}")
        return 2
    path, err = resolve_db_args(args.db, args.confirm_db, args.apply)
    print(f"Banco aberto: {path if path else '(nenhum)'}")
    if err:
        print(f"⛔ {err}")
        return 2
    _header(path, env_db)
    # Defesa em profundidade: qualquer leitor de DYNASTY_DB neste processo vê o MESMO alvo.
    os.environ["DYNASTY_DB"] = str(path)
    if not (args.check or args.apply):
        print("⛔ informe --check ou --apply")
        return 2
    bad = [s for s in args.exclude if s not in {t["sid"] for t in COHORT}]
    if bad:
        print(f"⛔ --exclude fora da lista congelada: {bad}")
        return 2
    if args.apply and args.offline:
        print("⛔ --offline nao vale no --apply. Nenhuma escrita.")
        return 2
    if args.apply and not args.backup:
        print("⛔ --apply exige --backup <backup feito antes>. Nenhuma escrita.")
        return 2
    excluded = set(args.exclude)
    if args.check:
        return cmd_check(path, excluded, live=live, offline=args.offline)
    return cmd_apply(path, Path(args.backup), excluded, live=live)


if __name__ == "__main__":
    sys.exit(main())
