"""
tools/regua_sync_ensaio.py — OFF26-42 (18/11/2026): ensaio e conferência do sync que decide
re-add pelas TRANSAÇÕES.

Dois modos:

  --sync    Roda `sync_sleeper.run_sync()` DUAS vezes sobre uma CÓPIA do banco e compara o
            efeito da régua com o CONJUNTO DECLARADO (aprovado pelo owner em 18/11/2026).
            ⛔ Recusa o banco do `DYNASTY_DB` do ambiente (o vivo, no Render) e qualquer banco
            no MESMO diretório dele — o cache do player DB do Sleeper vive em
            dirname(DYNASTY_DB), e o ensaio não pode tocar o do app em execução.
  --compare Só leitura: compara dois arquivos (backup antes × banco depois do sync real em
            produção) e emite o mesmo relatório.

Mesmas guardas de banco do `off26_42_fix.py`: --db obrigatório e ABSOLUTO, 1ª linha =
caminho aberto, --confirm-db idêntico no --sync, engine conferido por PRAGMA database_list,
não importa app.py (create_app roda no import contra a env). Rede: só GET no Sleeper.

Uso (Render Shell):
    python tools/regua_sync_ensaio.py --sync --db /data/ensaio_regua/ensaio.db \\
        --confirm-db /data/ensaio_regua/ensaio.db
    python tools/regua_sync_ensaio.py --compare --before /data/<backup>.db --after /data/dynasty.db
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── CONJUNTO DECLARADO do 1º sync em produção (aprovado pelo owner, 18/11/2026) ───────────────
# Medido sobre o banco vivo (5 consultas read-only do owner) × cadeia do Sleeper em
# 2026-11-18 17:50 UTC. Diferenças só se explicam por transação POSTERIOR a esse instante.
SNAPSHOT_UTC = datetime(2026, 11, 18, 17, 50, tzinfo=timezone.utc)
DECLARED = {
    "contratos": set(),
    "manter": {("12487", "1405911823215046656"), ("12504", "1406060433634332672")},
    "pendencias": {("11729", "1420870628910600192"), ("6130", "1423523942504603648"),
                   ("TB", "1420519580320673792")},
    "drops": {("11729", "1418306669443555328"), ("12185", "1424510738315096064"),
              ("12487", "1405685909285781504"), ("12499", "1423786132486774784"),
              ("12504", "1405852279164141568"), ("3286", "1425148310028660736"),
              ("4663", "1422875558378745856"), ("5927", "1418350840095260672"),
              ("6039", "1403909705931169792"), ("6130", "1422308083513720832"),
              ("9511", "1425982771129511937"), ("IND", "1416023426086223872"),
              ("TB", "1413392517516324864"), ("TB", "1419104628536078336")},
}
# Não podem mudar de contrato: os 4 reparados, os 7 controles e o McCarthy.
INTOCAVEIS = {"5927", "9511", "9502", "12547", "11539", "12540", "12718", "4993", "6039",
              "7839", "96", "11565"}
CONTRACT_COLS = ("salary", "contract_year", "contract_start_season", "acquisition_type")


def _ro(path: Path):
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def snapshot(path: Path) -> dict:
    con = _ro(path)
    try:
        players = {r[0]: r for r in con.execute(
            "SELECT id, sleeper_player_id, salary, contract_year, contract_start_season, "
            "acquisition_type, team_id, is_dropped, is_on_ir FROM players")}
        ph = {r[0]: r for r in con.execute(
            "SELECT id, player_id, event_type, sleeper_event_ref, notes FROM player_history")}
        al = {r[0]: r for r in con.execute("SELECT id, player_id, notes FROM auction_log")}
        cp = {r[0]: r for r in con.execute(
            "SELECT id, player_id, sleeper_transaction_id, kind, status FROM contract_pendencies")}
        store = {(r[0], r[1]): r[2:] for r in con.execute(
            "SELECT sleeper_player_id, season, espn_raw, espn_adjusted, is_final "
            "FROM espn_value_store")}
        last_log = con.execute("SELECT synced_at, summary FROM sync_log "
                               "ORDER BY id DESC LIMIT 1").fetchone()
    finally:
        con.close()
    return {"players": players, "ph": ph, "al": al, "cp": cp, "store": store,
            "last_log": last_log}


def diff(before: dict, after: dict) -> dict:
    sid = {pid: r[1] for pid, r in after["players"].items()}
    sid.update({pid: r[1] for pid, r in before["players"].items()})
    out = {"contratos": set(), "contratos_det": [], "manter": set(), "pendencias": set(),
           "drops": set(), "tokens": set(), "store": [], "intocaveis": [], "novos_players": 0,
           "outros": 0}
    for pid, a in after["players"].items():
        b = before["players"].get(pid)
        if b is None:
            out["novos_players"] += 1
            continue
        if b[2:6] != a[2:6]:
            out["contratos"].add(sid[pid])
            out["contratos_det"].append(f"{sid[pid]}: {dict(zip(CONTRACT_COLS, b[2:6]))} -> "
                                        f"{dict(zip(CONTRACT_COLS, a[2:6]))}")
            if sid[pid] in INTOCAVEIS:
                out["intocaveis"].append(sid[pid])
        elif b != a:
            out["outros"] += 1
    for hid, r in after["ph"].items():
        old = before["ph"].get(hid)
        ref = r[3] or ""
        if r[2] == "drop" and old is None:
            out["drops"].add((sid.get(r[1]), ref[3:] if ref.startswith("tx:") else ref))
        elif r[2] != "drop" and "[regua:manter:tx:" in (r[4] or "") and \
                (old is None or "[regua:manter:tx:" not in (old[4] or "")):
            out["manter"].add((sid.get(r[1]), ref[3:]))
    for cid, r in after["cp"].items():
        if cid not in before["cp"]:
            out["pendencias"].add((sid.get(r[1]), r[2]))
    for aid, r in after["al"].items():
        if aid not in before["al"] and "[ref:tx:" in (r[2] or ""):
            out["tokens"].add(sid.get(r[1]))
    for k in set(before["store"]) | set(after["store"]):
        if before["store"].get(k) != after["store"].get(k):
            out["store"].append(f"{k}: {before['store'].get(k)} -> {after['store'].get(k)}")
    return out


def _tx_times() -> dict:
    """tx_id → created (ms), GET read-only — para explicar diferenças pelo relógio."""
    import json
    import urllib.request
    import sync_sleeper
    out = {}
    for leg in range(19):
        url = f"https://api.sleeper.app/v1/league/{sync_sleeper.LEAGUE_ID}/transactions/{leg}"
        req = urllib.request.Request(url, headers={"User-Agent": "dynasty-manager-ensaio"})
        with urllib.request.urlopen(req, timeout=30) as r:
            for t in json.load(r) or []:
                out[str(t.get("transaction_id"))] = int(t.get("created") or 0)
    return out


def report(d: dict, label: str, declared: bool) -> bool:
    print(f"\n===== {label} =====")
    print(f"contratos alterados: {len(d['contratos'])}")
    for x in d["contratos_det"]:
        print(f"  {x}")
    print(f"tokens [ref:tx:] novos: {len(d['tokens'])}  |  eventos de manter: {len(d['manter'])}"
          f"  |  pendencias novas: {len(d['pendencias'])}  |  eventos de drop novos: "
          f"{len(d['drops'])}")
    print(f"linhas ESPN do store alteradas: {len(d['store'])}")
    for x in d["store"]:
        print(f"  {x}")
    print(f"intocaveis com contrato alterado: {d['intocaveis'] or 'nenhum'}")
    print(f"(efeitos normais do sync, fora da regua: {d['novos_players']} jogador(es) novo(s), "
          f"{d['outros']} linha(s) de players com outra mudanca)")
    if not declared:
        ok = not (d["contratos"] or d["manter"] or d["pendencias"] or d["drops"]
                  or d["tokens"] or d["store"])
        print(f"--> {'OK - zero escrita da regua' if ok else 'ATENCAO - houve escrita da regua'}")
        return ok
    ok = True
    times = None
    for key in ("contratos", "manter", "pendencias", "drops"):
        got = d[key]
        exp = DECLARED[key]
        extra, missing = got - exp, exp - got
        status = "CONFERE" if not extra and not missing else "DIVERGE"
        print(f"  [{status}] {key}: obtido {len(got)} x declarado {len(exp)}")
        if extra or missing:
            ok = False
            if times is None:
                try:
                    times = _tx_times()
                except Exception as exc:
                    times = {}
                    print(f"     (horario das tx indisponivel: {exc.__class__.__name__})")
            for x in sorted(extra, key=str):
                tx = x[1] if isinstance(x, tuple) else None
                ts = times.get(str(tx)) if tx else None
                quando = (datetime.fromtimestamp(ts / 1000, timezone.utc) if ts else None)
                pos = (" - POSTERIOR ao conjunto declarado" if quando and quando > SNAPSHOT_UTC
                       else "")
                print(f"     EXTRA {x}{' tx ' + quando.strftime('%d/%m %H:%M UTC') if quando else ''}{pos}")
            for x in sorted(missing, key=str):
                print(f"     FALTA {x}")
    if d["intocaveis"] or d["store"]:
        ok = False
    print(f"--> {'OK - conjunto declarado reproduzido' if ok else 'ATENCAO - ver acima'}")
    return ok


def _make_app(db_path: Path):
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def run_sync_on(db_path: Path) -> None:
    from models import db
    from sqlalchemy import text
    import sync_sleeper
    app = _make_app(db_path)
    with app.app_context():
        rows = db.session.execute(text("PRAGMA database_list")).fetchall()
        opened = Path(next(r for r in rows if r[1] == "main")[2]).resolve()
        if opened != db_path:
            raise SystemExit(f"⛔ O engine abriu {opened}, nao {db_path}. Abortado.")
        try:
            s = sync_sleeper.run_sync()
            print(f"  run_sync: {s.get('players_updated')} atualizados, "
                  f"{s.get('players_added')} novos; regua: "
                  f"{ {k: (len(v) if isinstance(v, list) else v) for k, v in (s.get('contract_regua') or {}).items()} }")
        finally:
            db.session.remove()
            db.engine.dispose()


def _abs(p, flag):
    if not p:
        raise SystemExit(f"⛔ {flag} e obrigatorio")
    if not Path(p).is_absolute():
        raise SystemExit(f"⛔ {flag} precisa ser caminho ABSOLUTO (recebido: {p})")
    path = Path(p).resolve()
    if not path.is_file():
        raise SystemExit(f"⛔ arquivo nao encontrado: {path}")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OFF26-42: ensaio/conferencia do sync por transacao")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sync", action="store_true")
    mode.add_argument("--compare", action="store_true")
    ap.add_argument("--db")
    ap.add_argument("--confirm-db")
    ap.add_argument("--before")
    ap.add_argument("--after")
    args = ap.parse_args(argv)
    env_db = os.environ.get("DYNASTY_DB")

    if args.compare:
        before, after = _abs(args.before, "--before"), _abs(args.after, "--after")
        print(f"Banco aberto (so leitura): antes={before} depois={after}")
        ok = report(diff(snapshot(before), snapshot(after)), "Sync real (antes x depois)", True)
        last = snapshot(after)["last_log"]
        print(f"\nUltimo SyncLog: {last}")
        return 0 if ok else 1

    db_path = _abs(args.db, "--db")
    print(f"Banco aberto: {db_path}")
    if not args.confirm_db or Path(args.confirm_db).resolve() != db_path:
        print(f"⛔ --confirm-db ({args.confirm_db}) != --db ({db_path}). Nada executado.")
        return 2
    if env_db:
        live = Path(env_db).resolve()
        if live == db_path:
            print("⛔ --db e o banco VIVO (DYNASTY_DB do ambiente). O ensaio so roda em copia.")
            return 2
        if live.parent == db_path.parent:
            print(f"⛔ a copia esta no MESMO diretorio do banco vivo ({live.parent}): o cache do "
                  f"Sleeper do app seria compartilhado. Use um subdiretorio proprio.")
            return 2
    print(f"DYNASTY_DB do ambiente: {env_db or '(ausente)'} -> alvo NAO e o banco vivo (copia)")
    os.environ["DYNASTY_DB"] = str(db_path)      # cache e helpers apontam para a copia
    # Liga a detecção por transação SÓ neste processo (o app em execução segue sem a chave
    # até o owner liberar no painel do Render).
    os.environ["REGUA_POR_TRANSACAO"] = "1"

    s0 = snapshot(db_path)
    print("\n1o sync na copia...")
    run_sync_on(db_path)
    s1 = snapshot(db_path)
    ok1 = report(diff(s0, s1), "1o sync (antes x depois)", True)
    print(f"\nUltimo SyncLog: {s1['last_log']}")
    print("\n2o sync na copia...")
    run_sync_on(db_path)
    s2 = snapshot(db_path)
    ok2 = report(diff(s1, s2), "2o sync (depois do 1o x depois do 2o)", False)
    print(f"\nUltimo SyncLog: {s2['last_log']}")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
