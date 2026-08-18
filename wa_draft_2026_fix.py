"""
wa_draft_2026_fix.py — runner ONE-SHOT do reparo MAN-OFF26-24-FIX: materializa o rookie
draft 2026 (realizado FORA do board do Sleeper, via WhatsApp) pela porta canônica.

Por que existe: o draft linear da liga real ficou vazio (pre_draft) — o importador OFF26-3
não tem insumo. Os jogadores foram adicionados aos rosters do Sleeper à mão; um sync
intermediário criou parte deles como STUBS (needs_review=1, salary=$1,
contract_start_season=2025 — a raiz é a linha 304 do sync, constante estagnada, provada na
OFF26-24-F1); os demais nem existem no Manager. Este script aplica os 36 picks da lista
canônica (WhatsApp) via `models.record_acquisition` — a MESMA porta que o importador usaria.

O que a F1 provou e este script honra:
  * record_acquisition no update cura salary/contract_year/contract_start_season/
    acquisition_type/espn_ref_value + grava SalaryHistory/AuctionLog — mas NÃO limpa
    needs_review → o clear explícito aqui é o objeto do reparo (trilha `review_approved`,
    molde M2).
  * fallback do valor: player.espn_ref_value → RookieEspnValue(sid, 2026) → $1
    (year1_salary já pisa no MIN_SALARY — o "$1 para quem não está no store" é regra nativa).

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    # 0) BACKUP OBRIGATÓRIO (sem ele o --apply recusa escrever):
    sqlite3 /data/dynasty.db ".backup '/data/dynasty_prod_backup_2026-08-18_wa_draft.db'"

    # 1) Conferência read-only (resolução 36/36 + âncoras + estado por pick):
    python wa_draft_2026_fix.py --preflight

    # 2) Escrita (preflight interno → escrita via porta canônica → auditoria → smoke):
    python wa_draft_2026_fix.py --apply --backup /data/dynasty_prod_backup_2026-08-18_wa_draft.db

    # 3) Auditoria standalone (read-only, reexecutável a qualquer momento):
    python wa_draft_2026_fix.py --audit

    # Ensaio local: acrescentar --db <CÓPIA> [--allow-anchor-mismatch: SÓ ensaio — o
    # store do seed é foto provisória de 07/08 e diverge das âncoras de produção]

Identidade Brown-safe: jogador resolvido contra o POOL GLOBAL por nome+posição+time NFL —
ambíguo ou divergente ABORTA, nunca chuta. Time resolvido por nome exato → normalizado →
hint de owner (só os documentados no prompt). Idempotente por event_ref
`wa_draft:2026:<round>.<pick>` — reexecutar não duplica nada.
"""

import argparse
import hashlib
import os
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SEASON = 2026
EVENT_REF_FMT = "wa_draft:2026:{ref}"
NOTES = "MAN-OFF26-24-FIX: rookie draft 2026 realizado via WhatsApp (fora do board)"

# ── Lista canônica dos 36 picks (fonte: owner, prompt MAN-OFF26-24-FIX) ─────────
# (ref, franquia, jogador, posição, time NFL)
PICKS = [
    ("1.1",  "Haliburton Time!",      "Jeremiyah Love",    "RB", "ARI"),
    ("1.2",  "Julia Mendes",          "Carnell Tate",      "WR", "TEN"),
    ("1.3",  "Trust The Process",     "Jadarian Price",    "RB", "SEA"),
    ("1.4",  "mongoloides",           "Jordyn Tyson",      "WR", "NO"),
    ("1.5",  "Cangaceiros da Colina", "De'Zhaun Stribling","WR", "SF"),
    ("1.6",  "Haliburton Time!",      "Makai Lemon",       "WR", "PHI"),
    ("1.7",  "ESPN FANTASY LEAGUE",   "KC Concepcion",     "WR", "CLE"),
    ("1.8",  "rafaelferreirap",       "Denzel Boston",     "WR", "CLE"),
    ("1.9",  "Cangaceiros da Colina", "Jonah Coleman",     "RB", "DEN"),
    ("1.10", "Tropa do Jarra",        "Kenyon Sadiq",      "TE", "NYJ"),
    ("1.11", "Pitbull do Samba",      "Nicholas Singleton","RB", "TEN"),
    ("1.12", "Trust The Process",     "Omar Cooper",       "WR", "NYJ"),
    ("2.01", "Haliburton Time!",      "Ja'Kobi Lane",      "WR", "BAL"),
    ("2.02", "Trust The Process",     "Chris Bell",        "WR", "MIA"),
    ("2.03", "SAFIEL",                "Cyrus Allen",       "WR", "KC"),
    ("2.04", "Trust The Process",     "Emmett Johnson",    "RB", "KC"),
    ("2.05", "SAFIEL",                "Zachariah Branch",  "WR", "ATL"),
    ("2.06", "Cangaceiros da Colina", "Ted Hurst",         "WR", "TB"),
    ("2.07", "ESPN FANTASY LEAGUE",   "Eli Stowers",       "TE", "PHI"),
    ("2.08", "Cangaceiros da Colina", "Eli Raridon",       "TE", "NE"),
    ("2.09", "Cangaceiros da Colina", "Germie Bernard",    "WR", "PIT"),
    ("2.10", "SAFIEL",                "Antonio Williams",  "WR", "WAS"),
    ("2.11", "Trust The Process",     "Caleb Douglas",     "WR", "MIA"),
    ("2.12", "Cangaceiros da Colina", "Mike Washington",   "RB", "LV"),
    ("3.01", "Haliburton Time!",      "Elijah Sarratt",    "WR", "BAL"),
    ("3.02", "mongoloides",           "Malachi Fields",    "WR", "NYG"),
    ("3.03", "mongoloides",           "Kaytron Allen",     "RB", "WAS"),
    ("3.04", "ESPN FANTASY LEAGUE",   "Fernando Mendoza",  "QB", "LV"),
    ("3.05", "Julia Mendes",          "Skyler Bell",       "WR", "BUF"),
    ("3.06", "AlexTheDawg",           "Kaelon Black",      "RB", "SF"),
    ("3.07", "Cangaceiros da Colina", "Adam Randall",      "RB", "BAL"),
    ("3.08", "rafaelferreirap",       "Zavion Thomas",     "WR", "CHI"),
    ("3.09", "mongoloides",           "Drew Allar",        "QB", "PIT"),
    ("3.10", "Tropa do Jarra",        "Dean Connors",      "RB", "LAR"),
    ("3.11", "mongoloides",           "Oscar Delp",        "TE", "NO"),
    ("3.12", "ESPN FANTASY LEAGUE",   "Max Klare",         "TE", "LAR"),
]

# Âncoras de PRODUÇÃO (prompt): salário previsto dos valorados; TODO o resto deve dar $1.
# Divergência ABORTA o preflight — exceto sob --allow-anchor-mismatch (SÓ ensaio local,
# onde o store do seed é foto provisória de 07/08).
ANCHORS = {
    "Jeremiyah Love": 54,
    "Carnell Tate": 12,
    "Jadarian Price": 9,
    "Jordyn Tyson": 6,
    "Kenyon Sadiq": 2,
}

# Hints de owner APENAS os documentados no prompt (renames conhecidos). Nunca chutar
# além disso: franquia irresolúvel aborta.
TEAM_OWNER_HINTS = {
    "Haliburton Time!": "murilofborges",
    "SAFIEL": "gabrieldiinis",
}


# ── Infra (molde off26_20_fix) ──────────────────────────────────────────────────

def _db_path(cli_db: str = None) -> Path:
    return Path(cli_db or os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db"))


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco. NÃO roda o boot do app.py (sem import
    CSV, sem sync, sem seed): reparo cirúrgico não dispara efeito colateral."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


# ── Resolução Brown-safe (núcleo puro — pool e times entram como dados) ─────────

def _norm_team_name(name: str) -> str:
    """Normalização CONSERVADORA de nome de franquia: casefold + colapso de espaços +
    remoção de decoração não-alfanumérica das pontas (emoji/troféu). Não remove nada
    do miolo — 'Tropa do Jarra  🏆' casa 'Tropa do Jarra'; nomes distintos seguem distintos."""
    import re
    n = (name or "").casefold()
    n = re.sub(r"\s+", " ", n).strip()
    n = re.sub(r"^[^0-9a-zà-ÿ]+|[^0-9a-zà-ÿ!]+$", "", n).strip()
    return n


def build_pool_index(pool: dict) -> dict:
    """Índice nome-normalizado → [(sid, info)]. Usa a MESMA normalização do
    player_lookup (fonte única do Brown-safe) — sufixos Jr/III, acentos, pontuação."""
    from player_lookup import _normalize
    idx = {}
    for sid, info in pool.items():
        if not isinstance(info, dict):
            continue
        name = (info.get("full_name")
                or f"{info.get('first_name', '')} {info.get('last_name', '')}".strip())
        if not name:
            continue
        idx.setdefault(_normalize(name), []).append((str(sid), info))
    return idx


def resolve_player(pool_idx: dict, name: str, pos: str, nfl_team: str):
    """(sid, info, None) ou (None, None, motivo). Exige nome+posição+time do pool —
    OFF26-24-FIX11: posição por PERTENCIMENTO (pos ∈ rótulo 'DB,WR'), nunca igualdade."""
    from player_lookup import _normalize
    cands = pool_idx.get(_normalize(name), [])
    if not cands:
        return None, None, "nome não encontrado no pool"
    full = [(sid, info) for sid, info in cands
            if pos.upper() in [p.strip() for p in (info.get("position") or "").upper().split(",")]
            and (info.get("team") or "").upper() == nfl_team.upper()]
    if len(full) == 1:
        return full[0][0], full[0][1], None
    detail = "; ".join(f"sid={sid} pos={i.get('position')} team={i.get('team')}"
                       for sid, i in cands[:6])
    if len(full) > 1:
        return None, None, f"AMBÍGUO mesmo com pos+time ({detail})"
    return None, None, f"nome achado mas pos/time divergem ({detail})"


def resolve_team(franchise: str, teams: list):
    """(team, caminho, None) ou (None, None, motivo). Exato → normalizado → hint de owner."""
    exact = [t for t in teams if t.name == franchise]
    if len(exact) == 1:
        return exact[0], "nome exato", None
    norm = [t for t in teams if _norm_team_name(t.name) == _norm_team_name(franchise)]
    if len(norm) == 1:
        return norm[0], "nome normalizado", None
    hint = TEAM_OWNER_HINTS.get(franchise)
    if hint:
        by_owner = [t for t in teams if (t.owner_name or "").casefold() == hint.casefold()]
        if len(by_owner) == 1:
            return by_owner[0], f"owner hint ({hint})", None
    n = len(exact) or len(norm)
    return None, None, ("ambígua" if n > 1 else "não encontrada (sem hint aplicável)")


# ── Preflight ───────────────────────────────────────────────────────────────────

def run_preflight(allow_anchor_mismatch: bool):
    """Resolve tudo, classifica estados, confere âncoras. Retorna (plan, errors).
    plan: lista de dicts prontos para o apply. 100% read-only no banco."""
    from models import (Team, get_config, acquisition_already_recorded,
                        rookie_espn_adjusted)
    from player_lookup import find_player_by_sleeper_id
    from salary_engine import year1_salary
    from sync_sleeper import _load_players_db

    errors, warnings = [], []

    # Guarda de fase: o reparo pressupõe rollover feito (F1: stubs nasceram DEPOIS dele).
    cs = get_config("current_season", "?")
    rd = get_config("rollover_done", "?")
    if str(cs) != str(SEASON):
        errors.append(f"current_season={cs} (esperado {SEASON}) — banco errado ou rollover pendente")
    if str(rd) != "true":
        errors.append(f"rollover_done={rd} (esperado true)")

    pool = _load_players_db()
    if not pool:
        return None, ["pool global do Sleeper indisponível (sem cache válido e sem rede)"]
    pool_idx = build_pool_index(pool)
    teams = Team.query.all()

    # Franquias primeiro (11 distintas) — qualquer uma irresolúvel aborta.
    team_by_franchise = {}
    for franchise in sorted({p[1] for p in PICKS}):
        team, path, err = resolve_team(franchise, teams)
        if err:
            errors.append(f"franquia '{franchise}': {err}")
            continue
        team_by_franchise[franchise] = team
        print(f"  franquia  {franchise:<22} -> team_id={team.id:<3} "
              f"'{team.name}' (via {path}; sleeper_owner_id={team.sleeper_owner_id})")

    plan, sids = [], {}
    print()
    for ref, franchise, name, pos, nfl in PICKS:
        sid, info, err = resolve_player(pool_idx, name, pos, nfl)
        if err:
            errors.append(f"pick {ref} '{name}' ({pos}/{nfl}): {err}")
            continue
        if sid in sids:
            errors.append(f"pick {ref} '{name}': sid {sid} DUPLICADO (também em {sids[sid]})")
            continue
        sids[sid] = ref

        ev_ref = EVENT_REF_FMT.format(ref=ref)
        already = acquisition_already_recorded(ev_ref)
        player = find_player_by_sleeper_id(sid)

        # Estado do Player local — qualquer coisa fora de stub/ausente/já-aplicado aborta.
        if already:
            state = "já aplicado (idempotente — será pulado)"
        elif player is None:
            state = "ausente (criação)"
        elif (player.needs_review and (player.acquisition_type or "unknown") == "unknown"
              and float(player.salary or 0) == 1.0):
            state = "stub (update)"
        else:
            errors.append(
                f"pick {ref} '{name}' sid={sid}: estado INESPERADO no banco — "
                f"acq={player.acquisition_type} salary=${player.salary} "
                f"needs_review={player.needs_review} (nem stub, nem ausente, nem aplicado)")
            continue

        # Valor: MESMA precedência do importador OFF26-3 (coluna do player → store → $1).
        espn_adj = float(player.espn_ref_value or 0.0) if player else 0.0
        store_val = rookie_espn_adjusted(sid, SEASON)
        if not espn_adj:
            espn_adj = float(store_val or 0.0)
        salary = year1_salary("rookie_draft", 0, espn_adj)

        expected = ANCHORS.get(name, 1)
        anchor_ok = salary == expected
        if not anchor_ok:
            msg = (f"pick {ref} '{name}': salário previsto ${salary} ≠ âncora ${expected} "
                   f"(store={store_val})")
            (warnings if allow_anchor_mismatch else errors).append(msg)

        team = team_by_franchise.get(franchise)
        rnd = int(ref.split(".")[0])
        plan.append({
            "ref": ref, "event_ref": ev_ref, "name": name, "pos": pos, "nfl": nfl,
            "sid": sid, "franchise": franchise, "team_id": team.id if team else None,
            "player_id": player.id if player else None, "state": state,
            "espn_adj": espn_adj, "salary": salary, "round": rnd,
            "already": already,
        })
        mark = "" if anchor_ok else "  ⚠ âncora"
        print(f"  {ref:>5}  {name:<20} sid={sid:>6}  {pos}/{nfl:<4} "
              f"-> {franchise:<22} ${salary:>3}  [{state}]{mark}")

    n_unique = len({p['sid'] for p in plan})
    print(f"\nResolução: {len(plan)}/{len(PICKS)} picks | {n_unique} sids únicos | "
          f"{sum(1 for p in plan if 'stub' in p['state'])} stubs | "
          f"{sum(1 for p in plan if 'ausente' in p['state'])} criações | "
          f"{sum(1 for p in plan if p['already'])} já aplicados")
    for w in warnings:
        print(f"  ⚠ (tolerado por --allow-anchor-mismatch) {w}")
    if len(plan) != len(PICKS) or n_unique != len(PICKS):
        errors.append(f"contagem: {len(plan)} resolvidos / {n_unique} únicos (exigido {len(PICKS)})")
    return plan, errors


# ── Smoke de escopo (fora dos 36, nada muda) ────────────────────────────────────

def _scope_snapshot(db_path: Path, sids: set) -> dict:
    """Raw sqlite, conexão independente: hash dos players FORA dos 36 (todas as colunas)
    + contagem/max(id) de salary_history e auction_log para delimitar as linhas novas."""
    con = sqlite3.connect(str(db_path))
    cols = [r[1] for r in con.execute("PRAGMA table_info(players)")]
    h = hashlib.sha256()
    outside_ids = set()
    marks = ",".join("?" * len(sids))
    for row in con.execute(
            f"SELECT {', '.join(cols)} FROM players WHERE sleeper_player_id IS NULL "
            f"OR sleeper_player_id NOT IN ({marks}) ORDER BY id", sorted(sids)):
        h.update(repr(row).encode())
        outside_ids.add(row[0])
    sh_n, sh_max = con.execute("SELECT COUNT(*), IFNULL(MAX(id),0) FROM salary_history").fetchone()
    al_n, al_max = con.execute("SELECT COUNT(*), IFNULL(MAX(id),0) FROM auction_log").fetchone()
    con.close()
    return {"players_hash": h.hexdigest(), "outside_ids": outside_ids,
            "sh": (sh_n, sh_max), "al": (al_n, al_max)}


def _scope_verify(db_path: Path, pre: dict, sids: set, target_pids: set) -> list:
    """Pós-escrita: players fora idênticos; toda linha nova de SH/AL pertence aos 36;
    nenhuma linha antiga sumiu."""
    errors = []
    post = _scope_snapshot(db_path, sids)
    if post["players_hash"] != pre["players_hash"]:
        errors.append("players FORA dos 36 mudaram (hash divergente)")
    con = sqlite3.connect(str(db_path))
    for table, key in (("salary_history", "sh"), ("auction_log", "al")):
        n_pre, max_pre = pre[key]
        old_n = con.execute(f"SELECT COUNT(*) FROM {table} WHERE id <= ?", (max_pre,)).fetchone()[0]
        if old_n != n_pre:
            errors.append(f"{table}: linhas pré-existentes alteradas em número ({old_n} != {n_pre})")
        bad = con.execute(
            f"SELECT COUNT(*) FROM {table} WHERE id > ? AND player_id NOT IN "
            f"({','.join('?' * len(target_pids))})",
            (max_pre, *sorted(target_pids))).fetchone()[0]
        if bad:
            errors.append(f"{table}: {bad} linha(s) nova(s) fora dos 36")
    con.close()
    return errors


# ── Auditoria (molde OFF26-4: exit 0 = limpo) ──────────────────────────────────

def run_audit(db_path: Path, allow_anchor_mismatch: bool) -> int:
    """Para cada um dos 36: salary/cy/css/acq/needs_review/time + 1 SalaryHistory 2026
    + 1 AuctionLog com o event_ref. Read-only; reexecutável."""
    from models import db, Team, SalaryHistory, AuctionLog
    from player_lookup import find_player_by_sleeper_id
    from sync_sleeper import _load_players_db

    app = _make_app(db_path)
    failures, anchor_warns = [], []
    with app.app_context():
        pool_idx = build_pool_index(_load_players_db())
        teams = Team.query.all()
        cap_delta = {}
        for ref, franchise, name, pos, nfl in PICKS:
            sid, _info, err = resolve_player(pool_idx, name, pos, nfl)
            if err:
                failures.append(f"{ref} {name}: resolução falhou na auditoria ({err})")
                continue
            p = find_player_by_sleeper_id(sid)
            if p is None:
                failures.append(f"{ref} {name} sid={sid}: NÃO EXISTE no banco")
                continue
            team, _, terr = resolve_team(franchise, teams)
            checks = {
                "contract_year=1": p.contract_year == 1,
                f"contract_start_season={SEASON}": p.contract_start_season == SEASON,
                "acquisition_type=rookie_draft": p.acquisition_type == "rookie_draft",
                "needs_review=0": not p.needs_review,
                "team correto": (team is not None and p.team_id == team.id),
                "salary=floor(espn,min1)": p.salary == max(1, int(p.espn_ref_value or 0)),
            }
            expected = ANCHORS.get(name, 1)
            if p.salary != expected:
                msg = f"{ref} {name}: salary ${int(p.salary)} ≠ âncora ${expected}"
                (anchor_warns if allow_anchor_mismatch else failures).append(msg)
            sh = SalaryHistory.query.filter_by(player_id=p.id, season=SEASON).filter(
                SalaryHistory.rule_applied.like("Rookie Draft%")).count()
            ev = EVENT_REF_FMT.format(ref=ref)
            al = AuctionLog.query.filter(AuctionLog.player_id == p.id,
                                         AuctionLog.notes.like(f"%[ref:{ev}]%")).count()
            checks["1 SalaryHistory 2026 (Rookie Draft)"] = sh == 1
            checks["1 AuctionLog c/ event_ref"] = al == 1
            bad = [k for k, ok in checks.items() if not ok]
            if terr:
                bad.append(f"franquia: {terr}")
            if bad:
                failures.append(f"{ref} {name} sid={sid}: " + "; ".join(bad))
            if team is not None:
                cap_delta[team.name] = cap_delta.get(team.name, 0) + int(p.salary)

        print("\nSoma dos salários do draft por franquia (informativo p/ conferência de cap):")
        for tname, total in sorted(cap_delta.items()):
            t = next((x for x in teams if x.name == tname), None)
            folha = t.total_salary() if t else "?"
            print(f"  {tname:<24} +${total:<4} (folha total agora: ${folha})")

    for w in anchor_warns:
        print(f"  ⚠ (âncora, tolerado) {w}")
    if failures:
        print(f"\n⛔ AUDITORIA: {len(failures)} falha(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\n✅ AUDITORIA LIMPA — {len(PICKS)}/36 conferem (salário, ano 1, season {SEASON}, "
          f"rookie_draft, review zerado, time, trilha SH+AL).")
    return 0


# ── Comandos ────────────────────────────────────────────────────────────────────

def cmd_preflight(db_path: Path, allow_anchor_mismatch: bool) -> int:
    app = _make_app(db_path)
    with app.app_context():
        print(f"Banco: {db_path}\n")
        plan, errors = run_preflight(allow_anchor_mismatch)
    if errors:
        print(f"\n⛔ PREFLIGHT REPROVADO ({len(errors)} problema(s)) — NENHUMA escrita permitida:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\n✅ PREFLIGHT OK — 36/36 resolvidos, 0 ambíguos, estados e âncoras conferem.")
    return 0


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


def cmd_apply(db_path: Path, backup: Path, allow_anchor_mismatch: bool) -> int:
    from models import db, Player, PlayerHistory, record_acquisition, Team

    if not _verify_backup(backup, db_path):
        return 1

    app = _make_app(db_path)
    with app.app_context():
        print(f"Banco: {db_path}\n── Preflight interno ──")
        plan, errors = run_preflight(allow_anchor_mismatch)
        if errors:
            print(f"\n⛔ Preflight reprovado ({len(errors)}) — ABORTADO, nenhuma escrita:")
            for e in errors:
                print(f"  - {e}")
            return 1

        sids = {p["sid"] for p in plan}
        pre = _scope_snapshot(db_path, sids)

        print("\n── Aplicação (porta canônica record_acquisition) ──")
        applied, skipped = [], 0
        for item in plan:
            if item["already"]:
                skipped += 1
                continue
            team = db.session.get(Team, item["team_id"])
            player = db.session.get(Player, item["player_id"]) if item["player_id"] else None
            player, salary = record_acquisition(
                player=player, player_name=item["name"], position=item["pos"],
                team=team, acquisition_type="rookie_draft", season=SEASON,
                espn_adjusted=item["espn_adj"], value_paid=0.0,
                round_num=item["round"],
                sleeper_player_id=(item["sid"] if item["player_id"] is None else None),
                event_ref=item["event_ref"], notes=NOTES,
            )
            item["applied_player"] = player
            item["applied_salary"] = salary
            applied.append(item)

        if not applied and skipped:
            db.session.rollback()
            print(f"\nNada a escrever — {skipped}/36 já aplicados (idempotência). "
                  f"Rodando auditoria:")
            return run_audit(db_path, allow_anchor_mismatch)

        # Clear de needs_review (o objeto do reparo — F1 provou que o update não limpa).
        # Trilha molde M2 (review_approved) para cada flag efetivamente limpa.
        cleared = 0
        for item in applied:
            p = item["applied_player"]
            if p.needs_review:
                p.needs_review = False
                db.session.add(PlayerHistory(
                    player_id=p.id, season=SEASON,
                    team_name=item["franchise"], event_type="review_approved",
                    salary=p.salary, contract_year=p.contract_year,
                    notes=f"{NOTES} — pick {item['ref']}; revisão = o próprio reparo auditado",
                ))
                cleared += 1

        # Verificação in-transação: releitura dos objetos antes do commit.
        bad = []
        for item in applied:
            p = item["applied_player"]
            if (p.salary != item["salary"] or p.contract_year != 1
                    or p.contract_start_season != SEASON
                    or p.acquisition_type != "rookie_draft" or p.needs_review):
                bad.append(f"{item['ref']} {item['name']}")
        if bad:
            db.session.rollback()
            print(f"⛔ Releitura in-transação divergente ({len(bad)}: {bad}) — rollback, "
                  f"nada escrito.")
            return 1

        db.session.commit()
        print(f"Aplicados: {len(applied)} | pulados (já aplicados): {skipped} | "
              f"needs_review limpos: {cleared}")

        target_pids = {item["applied_player"].id for item in applied}

    # ── Smoke de escopo por conexão independente ──
    scope_errors = _scope_verify(db_path, pre, sids, target_pids)
    if scope_errors:
        print("⛔ SMOKE DE ESCOPO FALHOU (commit JÁ ocorreu — avaliar restore do backup):")
        for e in scope_errors:
            print(f"  - {e}")
        return 1
    print("✅ Smoke de escopo: players fora dos 36 intactos; toda linha nova de "
          "SalaryHistory/AuctionLog pertence aos 36.")

    print("\n── Auditoria pós-execução ──")
    return run_audit(db_path, allow_anchor_mismatch)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="MAN-OFF26-24-FIX: materializa o rookie draft 2026 (WhatsApp) "
                    "pela porta canônica")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true", help="read-only: resolução + âncoras")
    mode.add_argument("--apply", action="store_true", help="escreve (exige --backup conferível)")
    mode.add_argument("--audit", action="store_true", help="read-only: auditoria pós")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatório no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrão: env DYNASTY_DB")
    ap.add_argument("--allow-anchor-mismatch", action="store_true",
                    help="SÓ ENSAIO LOCAL: tolera divergência das âncoras (store do seed "
                         "é foto provisória). Em produção, rodar SEM esta flag.")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        print(f"⛔ Banco não encontrado: {db_path}")
        return 1
    if args.apply and not args.backup:
        print("⛔ --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    if args.preflight:
        return cmd_preflight(db_path, args.allow_anchor_mismatch)
    if args.audit:
        return run_audit(db_path, args.allow_anchor_mismatch)
    return cmd_apply(db_path, Path(args.backup), args.allow_anchor_mismatch)


if __name__ == "__main__":
    sys.exit(main())
