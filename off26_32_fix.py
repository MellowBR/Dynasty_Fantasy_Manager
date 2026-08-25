"""
off26_32_fix.py — runner ONE-SHOT da correção OFF26-32 (contract_year 3→2 nos `fa_auction` vivos).

Aprovação do owner em 18/08/2026, sobre o parecer MAN-OFF26-32-F1: os jogadores readquiridos no
leilão FA de 2025 (canal `fa_auction`, confirmado transação a transação na API no censo do
OFF26-20) abriram contrato NOVO em 2025 pela regra 6.1 — logo 2026 é **ano 2**. O banco os conta
a partir do contrato pré-drop, e o rollover de 17/08 incrementou o número errado: hoje marcam
**ano 3**. Salário NÃO muda (o grupo cai em valorização em qualquer ano ≥ 2, e `fa_auction` está
fora de `_WAIVER_TYPES`); o dano é a renovação um ano cedo (2028 em vez de 2029) e o "Ano 3/4"
enganoso na tela.

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    # 0) BACKUP OBRIGATÓRIO (sem ele o --apply recusa escrever):
    sqlite3 /data/dynasty.db ".backup '/data/pre_off26_32_fix.db'"

    # 1) Conferência read-only (deriva a lista ao vivo + revalida a guarda + invariante):
    python off26_32_fix.py --check

    # 2) Escrita (guarda → escrita+trilha → verificação → commit):
    python off26_32_fix.py --apply --backup /data/pre_off26_32_fix.db

    # Ensaio local: acrescentar --db <caminho de uma CÓPIA pós-rollover>

⛔ **A lista de alvos NÃO é congelada — é derivada NO DIA, ao vivo.** O congelado é o *censo*
(quem pertence ao grupo); quem está **rosterado** é decisão do Sleeper, que é a autoridade sobre
membership (CLAUDE.md, "Data Authority Split"). O `is_dropped` do banco é apenas a fotografia do
último sync — e em 20/08 ele estará **desatualizado de propósito**: os cortes acontecem direto no
Sleeper (OFF26-1 ETAPA2) e pode haver freeze de sync (OPS2). Corrigir contrato de quem acabou de
ser cortado seria escrever em contrato morto. Por isso o cruzamento ao vivo é **obrigatório no
--apply**: sem API, não há escrita (a correção não tem prazo — o efeito é em 2028).
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace

BASE_DIR = Path(__file__).resolve().parent
LEAGUE_ID = "1316547584378048512"

# Censo CONGELADO do OFF26-20 (F1B/F1C, 05-06/08/2026): os 24 do canal `fa_auction` que estavam
# em contrato vivo (ano 2, pré-rollover). IDs são STRINGS — nenhuma DEF neste grupo, mas a
# disciplina é a mesma do OFF26-20-FIX (as DEFs usam sigla; nunca coagir a inteiro).
CENSUS = [
    ("11586", "Blake Corum"),
    ("6803", "Brandon Aiyuk"),
    ("8155", "Breece Hall"),
    ("8111", "Cade Otton"),
    ("11560", "Caleb Williams"),
    ("4039", "Cooper Kupp"),
    ("5022", "Dallas Goedert"),
    ("8110", "Jake Ferguson"),
    ("11618", "Jalen McMillan"),
    ("7526", "Jaylen Waddle"),
    ("4018", "Joe Mixon"),
    ("11637", "Keon Coleman"),
    ("5849", "Kyler Murray"),
    ("5012", "Mark Andrews"),
    ("6819", "Michael Pittman"),
    ("4046", "Patrick Mahomes"),
    ("8136", "Rachaad White"),
    ("7611", "Rhamondre Stevenson"),
    ("7021", "Rico Dowdle"),
    ("8121", "Romeo Doubs"),
    ("4943", "Sam Darnold"),
    ("9502", "Tank Dell"),
    ("7543", "Travis Etienne"),
    ("8126", "Wan'Dale Robinson"),
]

# Dropados em 2026, medidos na API na F1 (18/08). Excluídos SEMPRE, mesmo que reapareçam
# rosterados: um re-add em 2026 abre contrato NOVO (a reaquisição é o evento que conta), e
# corrigir a contagem do contrato MORTO produziria exatamente o híbrido que o [[OFF26-31]]
# documenta. Quem os readquirir entra por `record_acquisition`, não por aqui.
DROPPED_2026 = {
    "4018": "Joe Mixon (drop 05/08)",
    "11637": "Keon Coleman (drop 07/08)",
    "6803": "Brandon Aiyuk (drop 12/08)",
    "4039": "Cooper Kupp (drop 18/08)",
    # MAN-OFF26-32-F1B (25/08/2026): 5ª entrada, medida na revalidação pré-execução. Dropado na
    # JANELA DE CORTES (20/08 22:38 UTC, transação free_agent na liga real) e **arrematado no
    # leilão de 24/08 por $3** — ausente da keeper sheet congelada de 22/08, o que prova arremate
    # e não keeper. Hoje em prod: cy=1 · css=2026 · auction_draft · $3, contrato NOVO e correto.
    # Sem esta linha o --check sairia exit 1 ("19 elegíveis ≠ 20 alvos"): a derivação ao vivo o
    # aprovaria (está rosterado) e só a guarda da porta canônica o pularia — defesa em
    # profundidade funcionando, mas execução suja. A exclusão é auditável, nunca silenciosa.
    "5022": "Dallas Goedert (drop 20/08, arrematado no leilão 24/08 por $3)",
}

# Guarda pré-escrita: o estado esperado PÓS-rollover de 17/08 (o do OFF26-20-FIX esperava o
# estado PRÉ-rollover — é a diferença entre os dois runners).
EXPECTED = {
    "contract_year": 3,
    "contract_start_season": 2025,
    "acquisition_type": "fa_auction",
    "needs_review": False,
    "is_dropped": False,
}
NEW_YEAR = 2
EVENT_REF = "fix:off26-32"
REASON = ("Correção OFF26-32 aprovada pelo owner em 18/08/2026 (canal fa_auction confirmado na "
          "API no censo OFF26-20; regra 6.1: o leilão de 2025 abriu contrato novo)")


# ── Núcleo puro ───────────────────────────────────────────────────────────────

def derive_targets(census: list, rostered_sids, excluded: dict = None) -> tuple:
    """Cruza o censo congelado com os rosters vivos — puro, sem rede e sem DB.

    Devolve (targets, out), onde targets = [(sid, nome), ...] na ordem do censo e
    out = [{"sleeper_player_id", "name", "reason"}, ...]. Duas portas de exclusão:
    `excluded` (decisão congelada — drops de 2026, cujo re-add abriria contrato novo)
    e a ausência do sid entre os rosterados ao vivo.
    """
    excluded = excluded or {}
    rostered = {str(s) for s in rostered_sids}
    targets, out = [], []
    for sid, name in census:
        if sid in excluded:
            out.append({"sleeper_player_id": sid, "name": name,
                        "reason": f"fora por decisão: {excluded[sid]} — re-add abre contrato NOVO"})
        elif sid not in rostered:
            out.append({"sleeper_player_id": sid, "name": name,
                        "reason": "não está em nenhum roster ao vivo (dropado)"})
        else:
            targets.append((sid, name))
    return targets, out


def invariant_diff(before: dict, after: dict) -> list:
    """Compara salário e projeção do ano seguinte antes/depois — puro.

    before/after: sid → {"salary", "projected"}. Devolve a lista de violações; vazia = o
    invariante do parecer F1 se sustenta (a correção mexe na CONTAGEM, nunca no dinheiro).
    """
    viol = []
    for sid, pre in before.items():
        post = after.get(sid)
        if post is None:
            viol.append(f"{sid}: ausente na releitura pós-escrita")
            continue
        if int(pre["salary"]) != int(post["salary"]):
            viol.append(f"{sid}: salário {pre['salary']} -> {post['salary']}")
        if int(pre["projected"]) != int(post["projected"]):
            viol.append(f"{sid}: projeção {pre['projected']} -> {post['projected']}")
    return viol


# ── Camada de IO ──────────────────────────────────────────────────────────────

def fetch_rostered_sids(league_id: str = LEAGUE_ID, timeout: int = 30) -> set:
    """GET read-only dos rosters da liga — devolve o conjunto de sleeper_player_ids rosterados.

    Inclui `reserve` (IR): jogador no IR segue sob contrato. Só leitura; nada é enviado.
    """
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        rosters = json.load(resp)
    sids = set()
    for ro in rosters:
        for key in ("players", "reserve", "taxi"):
            for pid in (ro.get(key) or []):
                sids.add(str(pid))
    return sids


def _db_path(cli_db: str = None) -> Path:
    return Path(cli_db or os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db"))


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco. NÃO roda o boot do app.py (sem import CSV,
    sem sync, sem seed): correção cirúrgica não dispara efeito colateral."""
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


def _money_state(players: dict) -> dict:
    """sid → {salary, projected} com a projeção do ano seguinte pela fonte única."""
    from salary_engine import project_next_salary
    return {sid: {"salary": int(p.salary), "projected": int(project_next_salary(p))}
            for sid, p in players.items()}


def _money_state_from(sid_to_fields: dict) -> dict:
    """Mesma projeção sobre estado JÁ LIDO (stubs) — usado para o 'depois' simulado do --check."""
    from salary_engine import project_next_salary
    out = {}
    for sid, f in sid_to_fields.items():
        stub = SimpleNamespace(salary=f["salary"], espn_ref_value=f["espn"],
                               acquisition_type=f["acq"], contract_year=f["year"])
        out[sid] = {"salary": int(f["salary"]), "projected": int(project_next_salary(stub))}
    return out


# ── Relatórios ────────────────────────────────────────────────────────────────

def _report_derivation(targets: list, out: list, source: str) -> None:
    print(f"\nLista derivada ({source}): {len(targets)}/{len(CENSUS)} do censo")
    for sid, name in targets:
        print(f"  alvo   {sid:>6}  {name}")
    for o in out:
        print(f"  fora   {o['sleeper_player_id']:>6}  {o['name']:<22} {o['reason']}")


def _report_plan(result: dict, names: dict) -> None:
    print(f"\nElegíveis: {len(result['applied'])}/{len(result['applied']) + len(result['skipped'])}")
    for a in result["applied"]:
        print(f"  ok    {a['sleeper_player_id']:>6}  {a['name']:<22} {a['team']:<28} "
              f"contract_year {a['old']} -> {a['new']}")
    for s in result["skipped"]:
        print(f"  PULADO {s['sleeper_player_id']:>6}  {names.get(s['sleeper_player_id'], '?'):<22} "
              f"{s['reason']}")


# ── Comandos ──────────────────────────────────────────────────────────────────

def _resolve_targets(offline: bool) -> tuple:
    """Deriva a lista do dia. offline=True usa o censo inteiro menos os excluídos (sem rede)."""
    if offline:
        targets, out = derive_targets(
            CENSUS, {sid for sid, _ in CENSUS}, DROPPED_2026)
        return targets, out, "SEM cruzamento ao vivo — só a guarda do banco filtra"
    rostered = fetch_rostered_sids()
    targets, out = derive_targets(CENSUS, rostered, DROPPED_2026)
    return targets, out, f"rosters ao vivo do Sleeper ({len(rostered)} jogadores rosterados)"


def cmd_check(db_path: Path, offline: bool = False) -> int:
    """Read-only: deriva a lista, revalida a guarda e confere o invariante salarial."""
    from models import Player
    from contract_year_correction import plan_correction, _player_state

    targets, out, source = _resolve_targets(offline)
    if offline:
        print("⚠️  MODO OFFLINE — lista NÃO cruzada com os rosters ao vivo. Só para inspeção.")
    _report_derivation(targets, out, source)
    names = dict(CENSUS)

    app = _make_app(db_path)
    with app.app_context():
        ids = [sid for sid, _ in targets]
        players = Player.query.filter(Player.sleeper_player_id.in_(ids)).all()
        rows_by_id = {}
        for p in players:
            rows_by_id.setdefault(p.sleeper_player_id, []).append(p)
        eligible, skipped = plan_correction(
            ids, {sid: [_player_state(p) for p in ps] for sid, ps in rows_by_id.items()},
            EXPECTED)

        print(f"\nBanco: {db_path}")
        print(f"Guarda: {EXPECTED}")
        print(f"\nElegíveis: {len(eligible)}/{len(targets)}")
        for sid in eligible:
            p = rows_by_id[sid][0]
            print(f"  ok    {sid:>6}  {p.name:<22} salary=${int(p.salary)} "
                  f"espn_ref={p.espn_ref_value} cy={p.contract_year} css={p.contract_start_season}")
        for s in skipped:
            print(f"  PULADO {s['sleeper_player_id']:>6}  {names.get(s['sleeper_player_id'], '?'):<22} "
                  f"{s['reason']}")

        # Invariante: a projeção do ano seguinte com a contagem corrigida tem que dar o MESMO
        # número (o grupo cai em valorização em qualquer ano ≥ 2 — parecer F1, ponto 3).
        elig_players = {sid: rows_by_id[sid][0] for sid in eligible}
        before = _money_state(elig_players)
        after = _money_state_from({sid: {"salary": p.salary, "espn": p.espn_ref_value,
                                         "acq": p.acquisition_type, "year": NEW_YEAR}
                                   for sid, p in elig_players.items()})
        viol = invariant_diff(before, after)
        print(f"\nInvariante salarial (simulado, ano {NEW_YEAR}): "
              f"{'OK — salário e projeção idênticos' if not viol else 'VIOLADO'}")
        for v in viol:
            print(f"  ✗ {v}")

    all_ok = bool(eligible) and len(eligible) == len(targets) and not viol
    print(f"\n--check: {'OK — ' + str(len(eligible)) + '/' + str(len(targets)) + ' elegíveis, invariante intacto' if all_ok else 'ATENÇÃO — ver acima'}")
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
    from models import db, Player
    from contract_year_correction import apply_contract_year_correction, EVENT_TYPE

    if not _verify_backup(backup, db_path):
        return 1

    # ⛔ Sem cruzamento ao vivo não há escrita: o banco pode estar congelado (OPS2) ou
    # simplesmente atrasado, e o Sleeper é a autoridade sobre quem ainda está rosterado.
    try:
        targets, out, source = _resolve_targets(offline=False)
    except Exception as exc:
        print(f"⛔ Falha ao ler os rosters ao vivo do Sleeper ({exc.__class__.__name__}: {exc}).")
        print("   Nenhuma escrita. A lista de alvos SÓ é válida cruzada ao vivo — reagende.")
        return 1
    _report_derivation(targets, out, source)
    names = dict(CENSUS)

    if not targets:
        print("\nNenhum alvo vivo — nada a fazer.")
        return 1

    pre = _snapshot_players(db_path)

    app = _make_app(db_path)
    with app.app_context():
        ids = [sid for sid, _ in targets]

        # Estado financeiro ANTES (para o invariante), lido antes de qualquer encenação.
        pre_players = {p.sleeper_player_id: p for p in
                       Player.query.filter(Player.sleeper_player_id.in_(ids)).all()}
        money_before = _money_state(pre_players)

        result = apply_contract_year_correction(
            ids, expected=EXPECTED, new_year=NEW_YEAR,
            reason=REASON, event_ref=EVENT_REF)
        _report_plan(result, names)

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

        # Invariante sobre o estado REAL pós-commit.
        post_players = {a["sleeper_player_id"]: db.session.get(Player, a["player_id"])
                        for a in applied}
        money_after = _money_state(post_players)
        viol = invariant_diff({sid: money_before[sid] for sid in post_players}, money_after)

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
    errors.extend(f"invariante salarial: {v}" for v in viol)

    print(f"\nVerificação pós-escrita: {len(applied)} corrigidos; "
          f"{len(changed)} linhas alteradas; {trail} linhas de trilha; "
          f"invariante {'OK' if not viol else 'VIOLADO'}.")
    if errors:
        print("⛔ FALHAS DE VERIFICAÇÃO (o commit JÁ ocorreu — avaliar restore do backup):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ OK — só contract_year (+updated_at) dos elegíveis mudou; trilha completa; "
          "salário e projeção inalterados.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="OFF26-32: contract_year 3→2 nos fa_auction de 2025 ainda rosterados")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only: derivação + guarda + invariante")
    mode.add_argument("--apply", action="store_true", help="escreve (exige --backup conferível)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatório no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrão: env DYNASTY_DB")
    ap.add_argument("--offline", action="store_true",
                    help="--check apenas: inspeciona sem cruzar com os rosters ao vivo")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        print(f"⛔ Banco não encontrado: {db_path}")
        return 1
    if args.apply and args.offline:
        print("⛔ --offline não vale no --apply: a lista de alvos só é válida cruzada com os "
              "rosters ao vivo (o banco pode estar congelado ou atrasado). Nenhuma escrita.")
        return 1
    if args.apply and not args.backup:
        print("⛔ --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    return cmd_check(db_path, args.offline) if args.check else cmd_apply(db_path, Path(args.backup))


if __name__ == "__main__":
    sys.exit(main())
