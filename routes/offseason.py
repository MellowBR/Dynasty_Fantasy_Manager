"""
routes/offseason.py — Offseason flow: standings, lottery, rollover.

Steps:
  1. Close Season (import standings)
  2. Lock Draft Order (lottery for picks 1-6 — M15)
  3. Update ESPN Values
  4. Season Rollover
  5-7. Rookie Draft, Keepers, FA Auction (informational)
"""

import hashlib
import json as _json
import random
import secrets
import requests as req
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import (
    db, Team, Pick, Player, SalaryHistory,
    SeasonStandings, DraftLotteryResult, AppConfig, LotteryAudit,
    get_config, set_config, get_current_season, is_offseason,
    SALARY_CAP, MY_OWNER_ID, MY_TEAM_NAME, LEAGUE_ID,
)
from routes.auth import admin_required

offseason_bp = Blueprint("offseason", __name__)

SLEEPER_BASE = "https://api.sleeper.app/v1"

# ── M15: fonte única da configuração do lottery ───────────────────────────────
# seed_idx → peso (bolinhas). seed 1 = 12º (pior); seed N = (13 - N)º colocado.
# Decisão da liga 05/06/2026: 6 seeds — o 7º colocado entra com 1 bolinha.
# Soma = 96 (não fecha em 100, por decisão da liga). TODOS os pontos do lottery
# (pool, simulação, persistência, fronteira, legendas, paleta) derivam daqui.
DEFAULT_LOTTERY_WEIGHTS = {1: 50, 2: 25, 3: 12, 4: 5, 5: 3, 6: 1}


def _normalize_weights(weights):
    """Normaliza weights (chaves int ou str, vindos de JSON ou do default) → {int: float}."""
    if not weights:
        weights = DEFAULT_LOTTERY_WEIGHTS
    return {int(k): float(v) for k, v in weights.items()}


def _seed_rank(seed_idx) -> int:
    """seed 1 = 12º (pior colocado). Rank no standing = 13 - seed."""
    return 13 - int(seed_idx)


# ── M8: Auditable draw via literal balls + seed ───────────────────────────────

def _draw_weighted_lottery(pool: list, seed: str) -> list:
    """
    Pure, testable draw for the lottery picks using literal balls (each team
    repeated 'weight' times) + random.shuffle with a seeded RNG.

    Option B (continuous seed): random.seed(seed) called ONCE at start.
    Subsequent shuffles consume the RNG state; determinism is preserved as
    long as same seed + same pool are provided.

    pool: list of {"team_id", "team_name", "weight"} (N items; N = nº de seeds)
    seed: hex string (secrets.token_hex result)
    returns: list of N {"pick_number", "team_id", "team_name"}

    M15: a contagem de picks deriva de len(pool) (NUNCA de constante global),
    garantindo que audits antigas de 5 seeds reproduzam exatamente 5 picks.
    """
    # Expand into literal balls
    balls = []
    for entry in pool:
        balls.extend([(entry["team_id"], entry["team_name"])] * int(entry["weight"]))

    random.seed(seed)

    results = []
    for pick_num in range(1, len(pool) + 1):
        if not balls:
            break
        random.shuffle(balls)
        drawn_team_id, drawn_team_name = balls[0]
        results.append({
            "pick_number": pick_num,
            "team_id": drawn_team_id,
            "team_name": drawn_team_name,
        })
        balls = [b for b in balls if b[0] != drawn_team_id]

    return results


def _compute_result_hash(lottery_picks: list) -> str:
    """SHA256 of 'picknum:team_name' comma-joined, for tampering detection.
    M15: deriva do tamanho da lista recebida — mesmo algoritmo p/ qualquer nº
    de seeds (5 ou 6); audits antigas mantêm o mesmo hash."""
    ordered = sorted(lottery_picks, key=lambda p: p["pick_number"])
    key = ",".join(f"{p['pick_number']}:{p['team_name']}" for p in ordered)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ── M15: builders únicos de pool / fronteira / ordem padrão ───────────────────

def _build_lottery_pool(standings, weights=None):
    """Pool do lottery a partir dos standings + weights. Fonte única:
    seed i → rank (13-i). Retorna lista ordenada por seed
    [{team_name, team_id, seed, weight}, ...], só com times presentes nos standings."""
    by_rank = {s.rank: s for s in standings}
    w = _normalize_weights(weights)
    pool = []
    for seed_idx in sorted(w.keys()):
        s = by_rank.get(_seed_rank(seed_idx))
        if s:
            pool.append({
                "team_name": s.team_name,
                "team_id": s.team_id,
                "seed": seed_idx,
                "weight": w[seed_idx],
            })
    return pool


def _build_fixed_picks(standings, num_lottery_seeds):
    """Picks fixos por standings, começando logo após os picks do lottery.
    Ranks (pior_fora_do_lottery)…3 viram picks; vice = pick 11, campeão = pick 12.
    Só o limiar lottery/standings muda com num_lottery_seeds; 11/12 são fixos.
    Ex (6 seeds): ranks 6,5,4,3 → picks 7,8,9,10; vice→11; campeão→12."""
    by_rank = {s.rank: s for s in standings}
    worst_lottery_rank = 13 - num_lottery_seeds  # 6 seeds → 7 (pior fora = rank 6)
    fixed = []
    pick_num = num_lottery_seeds + 1
    for rank in range(worst_lottery_rank - 1, 2, -1):  # 6 seeds → [6,5,4,3]
        s = by_rank.get(rank)
        if s:
            fixed.append({"pick_number": pick_num, "team_name": s.team_name,
                          "team_id": s.team_id, "source": "standings"})
        pick_num += 1
    runner_up = next((s for s in standings if s.is_runner_up), None)
    champion = next((s for s in standings if s.is_champion), None)
    if runner_up:
        fixed.append({"pick_number": 11, "team_name": runner_up.team_name,
                      "team_id": runner_up.team_id, "source": "standings"})
    if champion:
        fixed.append({"pick_number": 12, "team_name": champion.team_name,
                      "team_id": champion.team_id, "source": "standings"})
    return fixed


def _build_default_draft_order(standings, weights=None):
    """Ordem completa picks 1-12 por standings, SEM sorteio real (fallback de
    projeção quando não há lottery). Picks 1..N = seeds (rank 13-seed, worst
    first); picks N+1..12 = fixos. Mesma fonte/fronteira do sorteio real.
    Retorna [(pick_number, team_name), ...]."""
    w = _normalize_weights(weights)
    by_rank = {s.rank: s for s in standings}
    order = []
    for seed_idx in sorted(w.keys()):
        s = by_rank.get(_seed_rank(seed_idx))
        if s:
            order.append((seed_idx, s.team_name))
    num_seeds = len(order) if order else len(w)
    for f in _build_fixed_picks(standings, num_seeds):
        order.append((f["pick_number"], f["team_name"]))
    return order


# ── Helper: step status ─────────────────────────────────────────────────────

def _get_step_statuses():
    """Compute status of each offseason step."""
    season = get_current_season()
    step = int(get_config("offseason_step", "0"))

    standings_exist = SeasonStandings.query.filter_by(season=season).count() > 0
    lottery_locked = DraftLotteryResult.query.filter_by(
        season=season + 1, locked=True).count() > 0
    espn_updated = get_config("espn_values_updated", "false") == "true"
    rollover_done = get_config("rollover_done", "false") == "true"
    rookie_done = get_config("rookie_draft_done", "false") == "true"
    auction_done = get_config("auction_done", "false") == "true"

    steps = [
        {"num": 1, "name": "Fechar Temporada", "key": "season_closed",
         "done": standings_exist, "locked": False},
        {"num": 2, "name": "Travar Sorteio do Draft", "key": "season_locked",
         "done": lottery_locked, "locked": not standings_exist},
        {"num": 3, "name": "Atualizar ESPN Values", "key": "espn_values_updated",
         "done": espn_updated, "locked": False},
        {"num": 4, "name": "Season Rollover", "key": "rollover_done",
         "done": rollover_done, "locked": not (lottery_locked and espn_updated)},
        {"num": 5, "name": "Rookie Draft", "key": "rookie_draft_done",
         "done": rookie_done, "locked": False},
        {"num": 6, "name": "Definir Keepers / Cortes", "done": False, "locked": False},
        {"num": 7, "name": "FA Auction", "key": "auction_done",
         "done": auction_done, "locked": False},
    ]

    for s in steps:
        if s["done"]:
            s["status"] = "done"
        elif s.get("locked"):
            s["status"] = "locked"
        else:
            s["status"] = "pending"

    return steps


# ── Page route ───────────────────────────────────────────────────────────────

@offseason_bp.route("/offseason")
@login_required
def offseason_page():
    season = get_current_season()
    steps = _get_step_statuses()
    standings = SeasonStandings.query.filter_by(season=season)\
        .order_by(SeasonStandings.rank).all()
    lottery = DraftLotteryResult.query.filter_by(season=season + 1)\
        .order_by(DraftLotteryResult.pick_number).all()
    teams = Team.query.order_by(Team.name).all()

    # M8: só consideramos que houve sorteio oficial se existir audit canônica.
    # DraftLotteryResult pode ter rows de execuções pré-M8 sem audit — nesse
    # caso a UI deve mostrar o toggle + botão de simulação/oficial.
    has_canonical_audit = LotteryAudit.query.filter_by(
        season=season + 1, is_canonical=True).first() is not None

    # Build lottery seed → team name map from standings (M15: deriva da config)
    lottery_seeds = {}  # seed i = (13-i)º colocado
    by_rank = {s.rank: s for s in standings}
    for seed_idx in DEFAULT_LOTTERY_WEIGHTS:
        s = by_rank.get(_seed_rank(seed_idx))
        if s:
            lottery_seeds[seed_idx] = s.team_name

    return render_template("offseason.html",
                           season=season,
                           steps=steps,
                           standings=standings,
                           lottery=lottery,
                           has_canonical_audit=has_canonical_audit,
                           teams=teams,
                           lottery_weights=DEFAULT_LOTTERY_WEIGHTS,
                           lottery_seeds=lottery_seeds)


@offseason_bp.route("/api/offseason/status")
@login_required
def offseason_status():
    return jsonify({
        "season": get_current_season(),
        "offseason_mode": is_offseason(),
        "steps": _get_step_statuses(),
    })


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Close Season (standings)
# ══════════════════════════════════════════════════════════════════════════════

@offseason_bp.route("/api/offseason/check_previous_league")
@login_required
def check_previous_league():
    """Check if Sleeper has a previous league matching current_season."""
    season = get_current_season()
    data = _sleeper_get(f"{SLEEPER_BASE}/league/{LEAGUE_ID}")
    if not data:
        return jsonify({"available": False, "reason": "Erro ao consultar Sleeper API"})

    prev_id = data.get("previous_league_id")
    if not prev_id:
        return jsonify({"available": False,
                        "reason": "O Sleeper ainda nao gerou a liga anterior. "
                                  "Preencha os standings manualmente."})

    prev_data = _sleeper_get(f"{SLEEPER_BASE}/league/{prev_id}")
    if not prev_data:
        return jsonify({"available": False, "reason": "Erro ao buscar liga anterior"})

    prev_season = prev_data.get("season")
    if str(prev_season) != str(season):
        return jsonify({"available": False,
                        "reason": f"Liga anterior e da temporada {prev_season}, "
                                  f"nao {season}. Preencha manualmente."})

    return jsonify({"available": True, "previous_league_id": prev_id, "season": prev_season})


@offseason_bp.route("/api/offseason/import_standings", methods=["POST"])
@admin_required
def import_standings():
    """Import standings from Sleeper previous league."""
    season = get_current_season()
    data = request.get_json() or {}
    prev_league_id = data.get("previous_league_id")

    if not prev_league_id:
        return jsonify({"error": "previous_league_id obrigatorio"}), 400

    # Fetch rosters (have W/L/points)
    rosters = _sleeper_get(f"{SLEEPER_BASE}/league/{prev_league_id}/rosters") or []
    users = _sleeper_get(f"{SLEEPER_BASE}/league/{prev_league_id}/users") or []

    if not rosters:
        return jsonify({"error": "Nao foi possivel buscar rosters"}), 500

    # Build owner_id → user info
    user_map = {}
    for u in users:
        uid = u.get("user_id", "")
        meta = u.get("metadata", {}) or {}
        team_name = meta.get("team_name", "") or u.get("display_name", "")
        if uid == MY_OWNER_ID:
            team_name = MY_TEAM_NAME
        user_map[uid] = team_name or u.get("display_name", "")

    # Fetch winners bracket to identify champion/runner-up
    bracket = _sleeper_get(f"{SLEEPER_BASE}/league/{prev_league_id}/winners_bracket") or []
    champion_rid, runner_up_rid = _find_champion_runner_up(bracket)

    # Build standings from rosters
    standings_data = []
    for r in rosters:
        rid = str(r.get("roster_id", ""))
        oid = str(r.get("owner_id", "") or "")
        settings = r.get("settings", {}) or {}
        team_name = user_map.get(oid, f"Team {rid}")

        # Match to local team
        local_team = Team.query.filter_by(sleeper_owner_id=oid).first()

        standings_data.append({
            "roster_id": rid,
            "team_name": local_team.name if local_team else team_name,
            "team_id": local_team.id if local_team else None,
            "wins": settings.get("wins", 0),
            "losses": settings.get("losses", 0),
            "points_for": settings.get("fpts", 0) + settings.get("fpts_decimal", 0) / 100,
            "is_champion": rid == champion_rid,
            "is_runner_up": rid == runner_up_rid,
        })

    # Sort by wins desc, then points desc
    standings_data.sort(key=lambda x: (-x["wins"], -x["points_for"]))

    # Clear previous standings for this season and save
    SeasonStandings.query.filter_by(season=season).delete()
    for i, s in enumerate(standings_data):
        entry = SeasonStandings(
            season=season,
            team_id=s["team_id"],
            team_name=s["team_name"],
            rank=i + 1,
            wins=s["wins"],
            losses=s["losses"],
            points_for=s["points_for"],
            is_champion=s["is_champion"],
            is_runner_up=s["is_runner_up"],
        )
        db.session.add(entry)

    set_config("season_closed", "true")
    db.session.commit()

    return jsonify({"success": True, "count": len(standings_data)})


@offseason_bp.route("/api/offseason/save_standings", methods=["POST"])
@admin_required
def save_standings():
    """Save manually edited standings."""
    season = get_current_season()
    data = request.get_json() or {}
    entries = data.get("standings", [])

    SeasonStandings.query.filter_by(season=season).delete()
    for s in entries:
        entry = SeasonStandings(
            season=season,
            team_id=s.get("team_id"),
            team_name=s.get("team_name", ""),
            rank=s.get("rank", 0),
            wins=s.get("wins", 0),
            losses=s.get("losses", 0),
            points_for=float(s.get("points_for", 0)),
            is_champion=s.get("is_champion", False),
            is_runner_up=s.get("is_runner_up", False),
        )
        db.session.add(entry)

    set_config("season_closed", "true")
    db.session.commit()
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Draft Order + Lottery
# ══════════════════════════════════════════════════════════════════════════════

@offseason_bp.route("/api/offseason/run_lottery", methods=["POST"])
@admin_required
def run_lottery():
    """
    Run weighted lottery for picks 1..N and assign fixed picks N+1..12.
    M15: N = nº de seeds (default 6 — inclui o 7º colocado com 1 bolinha).
    Draft order rules (6 seeds):
      Picks 1-6:   Lottery among 7th-12th place (worst teams)
      Picks 7-10:  6th-3rd place (fixed; 6th → pick 7, etc.)
      Pick 11:     Runner-up
      Pick 12:     Champion
    """
    # M8: block duplicate official execution — force /replace with reason
    season = get_current_season()
    draft_season = season + 1
    existing = LotteryAudit.query.filter_by(season=draft_season, is_canonical=True).first()
    if existing:
        return jsonify({
            "error": "Lottery já foi executada oficialmente. Use /api/offseason/lottery/replace com justificativa se precisa re-executar."
        }), 409

    data = request.get_json() or {}
    weights = data.get("weights", DEFAULT_LOTTERY_WEIGHTS)

    standings = SeasonStandings.query.filter_by(season=season)\
        .order_by(SeasonStandings.rank).all()
    if len(standings) < 12:
        return jsonify({"error": f"Standings incompletos ({len(standings)} times)"}), 400

    audit, all_results = _execute_lottery_and_persist(
        season=season,
        draft_season=draft_season,
        standings=standings,
        weights=weights,
        previous_audit_id=None,
        reason=None,
    )
    return jsonify({"success": True, "results": all_results, "audit": audit.to_dict()})


@offseason_bp.route("/api/offseason/lottery/simulate", methods=["POST"])
@login_required
def lottery_simulate():
    """
    M8: Simulação pura — roda o sorteio em memória com seed descartável, NÃO
    persiste nada. Zero impacto em LotteryAudit e DraftLotteryResult.
    Apenas retorna resultados para preview animado na UI.
    MAN-M8-02: aberto para owners (login_required) + bloqueado após oficial.
    """
    season = get_current_season()
    draft_season = season + 1

    # MAN-M8-02: bloqueio pós-oficial — espelha guarda do run_lottery
    existing = LotteryAudit.query.filter_by(
        season=draft_season, is_canonical=True).first()
    if existing:
        return jsonify({
            "error": f"Sorteio oficial da temporada {draft_season} já realizado. Simulação indisponível até a próxima temporada."
        }), 409

    data = request.get_json() or {}
    weights = data.get("weights", DEFAULT_LOTTERY_WEIGHTS)

    standings = SeasonStandings.query.filter_by(season=season)\
        .order_by(SeasonStandings.rank).all()
    if len(standings) < 12:
        return jsonify({"error": f"Standings incompletos ({len(standings)} times)"}), 400

    # M15: mesma fonte única do sorteio oficial
    pool = _build_lottery_pool(standings, weights)

    # Disposable seed — no persistence
    sim_seed = secrets.token_hex(16)
    lottery_draws = _draw_weighted_lottery(pool, sim_seed)
    lottery_results = [{**d, "source": "lottery"} for d in lottery_draws]

    fixed_results = _build_fixed_picks(standings, len(pool))

    return jsonify({
        "simulated": True,
        "results": lottery_results + fixed_results,
    })


@offseason_bp.route("/api/offseason/lottery/replace", methods=["POST"])
@admin_required
def lottery_replace():
    """
    M8: Re-executa lottery depois da canônica ter sido criada. Exige reason.
    Marca canônica anterior como superseded (is_canonical=False), grava nova row
    com previous_audit_id = id da anterior.
    """
    season = get_current_season()
    draft_season = season + 1
    data = request.get_json() or {}
    reason = (data.get("reason") or "").strip()
    if not reason:
        return jsonify({"error": "Campo 'reason' é obrigatório para re-execução"}), 400

    prev_audit = LotteryAudit.query.filter_by(season=draft_season, is_canonical=True).first()
    if not prev_audit:
        return jsonify({"error": "Nenhuma lottery canônica encontrada. Use /run_lottery primeiro."}), 404

    standings = SeasonStandings.query.filter_by(season=season)\
        .order_by(SeasonStandings.rank).all()
    if len(standings) < 12:
        return jsonify({"error": f"Standings incompletos ({len(standings)} times)"}), 400

    # Demote previous
    prev_audit.is_canonical = False
    db.session.add(prev_audit)

    weights = data.get("weights", DEFAULT_LOTTERY_WEIGHTS)
    audit, all_results = _execute_lottery_and_persist(
        season=season,
        draft_season=draft_season,
        standings=standings,
        weights=weights,
        previous_audit_id=prev_audit.id,
        reason=reason,
    )
    return jsonify({
        "success": True,
        "results": all_results,
        "audit": audit.to_dict(),
        "superseded_audit_id": prev_audit.id,
    })


def _execute_lottery_and_persist(season, draft_season, standings, weights,
                                  previous_audit_id, reason):
    """
    M8/M15 shared body: draws picks 1..N via _draw_weighted_lottery, computes
    picks N+1..12 from standings (fonte única), replaces DraftLotteryResult,
    persists LotteryAudit. Returns (audit_row, all_results_list).
    """
    # M15: pool + fronteira derivam da fonte única (_build_lottery_pool /
    # _build_fixed_picks). Picks 1..N = lottery; picks N+1..12 = standings.
    lottery_pool = _build_lottery_pool(standings, weights)

    # Generate seed + draw via helper (contagem deriva de len(pool))
    random_seed = secrets.token_hex(16)
    lottery_draws = _draw_weighted_lottery(lottery_pool, random_seed)
    lottery_results = [{**d, "source": "lottery"} for d in lottery_draws]

    fixed_results = _build_fixed_picks(standings, len(lottery_pool))

    all_results = lottery_results + fixed_results

    # Save picks (replaces unlocked rows)
    DraftLotteryResult.query.filter_by(season=draft_season, locked=False).delete()
    for r in all_results:
        db.session.add(DraftLotteryResult(
            season=draft_season,
            pick_number=r["pick_number"],
            team_id=r["team_id"],
            team_name=r["team_name"],
            source=r["source"],
            locked=False,
        ))

    # M8: persist audit
    result_hash = _compute_result_hash(lottery_results)
    pool_json_str = _json.dumps(lottery_pool, ensure_ascii=False)
    # Convert weights keys to string for JSON stability
    weights_serializable = {str(k): v for k, v in weights.items()}
    weights_json_str = _json.dumps(weights_serializable, ensure_ascii=False)

    audit = LotteryAudit(
        season=draft_season,
        random_seed=random_seed,
        weights_json=weights_json_str,
        pool_json=pool_json_str,
        executed_by=current_user.id if current_user.is_authenticated else None,
        result_hash=result_hash,
        previous_audit_id=previous_audit_id,
        reason=reason,
        is_canonical=True,
    )
    db.session.add(audit)
    db.session.commit()

    return audit, all_results


@offseason_bp.route("/api/offseason/save_lottery", methods=["POST"])
@admin_required
def save_lottery():
    """Save manually edited lottery results (picks 1..N do lottery)."""
    season = get_current_season()
    draft_season = season + 1
    data = request.get_json() or {}
    picks = data.get("picks", [])

    # M15: edita só os picks do lottery (1..N), mantém os fixos N+1..12
    num_seeds = len(DEFAULT_LOTTERY_WEIGHTS)
    for p in picks:
        pick_num = p.get("pick_number")
        if not pick_num or pick_num > num_seeds:
            continue
        existing = DraftLotteryResult.query.filter_by(
            season=draft_season, pick_number=pick_num, locked=False).first()
        if existing:
            existing.team_name = p.get("team_name", existing.team_name)
            existing.team_id = p.get("team_id", existing.team_id)
            existing.source = "lottery"
        else:
            db.session.add(DraftLotteryResult(
                season=draft_season, pick_number=pick_num,
                team_name=p.get("team_name", ""),
                team_id=p.get("team_id"),
                source="lottery", locked=False,
            ))

    db.session.commit()
    return jsonify({"success": True})


@offseason_bp.route("/api/offseason/lock_lottery", methods=["POST"])
@admin_required
def lock_lottery():
    """Irreversibly lock lottery results."""
    season = get_current_season()
    draft_season = season + 1

    results = DraftLotteryResult.query.filter_by(season=draft_season).all()
    if len(results) < 12:
        return jsonify({"error": "Sorteio incompleto — faltam picks"}), 400

    for r in results:
        r.locked = True

    set_config("season_locked", "true")
    db.session.commit()

    return jsonify({"success": True, "locked": len(results)})


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — ESPN Values (just a gate check)
# ══════════════════════════════════════════════════════════════════════════════

@offseason_bp.route("/api/offseason/confirm_espn", methods=["POST"])
@admin_required
def confirm_espn():
    """Mark ESPN values as updated."""
    set_config("espn_values_updated", "true")
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Season Rollover
# ══════════════════════════════════════════════════════════════════════════════

@offseason_bp.route("/api/offseason/rollover", methods=["POST"])
@admin_required
def do_rollover():
    """Execute season rollover (gated by steps 2+3)."""
    steps = _get_step_statuses()
    step4 = next(s for s in steps if s["num"] == 4)
    if step4["status"] == "locked":
        return jsonify({"error": "Rollover bloqueado — complete etapas anteriores"}), 400
    if step4["done"]:
        return jsonify({"error": "Rollover ja foi executado"}), 400

    from salary_engine import apply_season_rollover
    season = get_current_season()
    next_season = season + 1

    players = Player.query.filter_by(is_dropped=False).all()
    applied = 0
    renewals = 0

    for p in players:
        new_sal, new_yr, rule = apply_season_rollover(p)
        p.salary = new_sal
        p.contract_year = new_yr
        if new_yr == 1:
            p.contract_start_season = next_season
            renewals += 1
        db.session.add(SalaryHistory(
            player_id=p.id, season=next_season, salary=new_sal,
            contract_year=new_yr, rule_applied=rule,
            espn_ref_value=p.espn_ref_value or 0.0,
        ))
        applied += 1

    # Advance season
    set_config("current_season", str(next_season))
    set_config("offseason_mode", "true")
    set_config("rollover_done", "true")
    db.session.commit()

    return jsonify({
        "success": True,
        "applied": applied,
        "renewals": renewals,
        "new_season": next_season,
    })


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Rookie Draft Done
# ══════════════════════════════════════════════════════════════════════════════

@offseason_bp.route("/api/offseason/rookie_draft_done", methods=["POST"])
@admin_required
def toggle_rookie_draft():
    data = request.get_json() or {}
    undo = data.get("undo", False)
    val = "false" if undo else "true"
    set_config("rookie_draft_done", val)
    msg = "Rookie Draft revertido" if undo else "Rookie Draft marcado como concluido"
    return jsonify({"ok": True, "key": "rookie_draft_done", "value": val, "message": msg})


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — FA Auction Done
# ══════════════════════════════════════════════════════════════════════════════

@offseason_bp.route("/api/offseason/auction_done", methods=["POST"])
@admin_required
def toggle_auction():
    data = request.get_json() or {}
    undo = data.get("undo", False)
    val = "false" if undo else "true"
    set_config("auction_done", val)
    msg = "FA Auction revertido" if undo else "FA Auction marcado como concluido"
    return jsonify({"ok": True, "key": "auction_done", "value": val, "message": msg})


# ══════════════════════════════════════════════════════════════════════════════
# Season Flags API
# ══════════════════════════════════════════════════════════════════════════════

SEASON_FLAG_KEYS = [
    "offseason_mode", "current_season", "rollover_done",
    "rookie_draft_done", "auction_done", "playoffs_started",
    "season_closed", "season_locked", "espn_values_updated",
]


@offseason_bp.route("/api/offseason/season_flags")
@login_required
def season_flags():
    return jsonify({k: get_config(k, "false") for k in SEASON_FLAG_KEYS})


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _sleeper_get(url, timeout=15):
    try:
        r = req.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _find_champion_runner_up(bracket):
    """Parse Sleeper winners_bracket to find champion and runner-up roster IDs."""
    if not bracket:
        return None, None

    # The championship match has p=1 (determines 1st place)
    # Fallback: highest round, lowest matchup number
    final = None
    for match in bracket:
        if match.get("p") == 1:
            final = match
            break

    if not final:
        max_round = max((m.get("r", 0) for m in bracket), default=0)
        candidates = [m for m in bracket if m.get("r") == max_round]
        if candidates:
            final = min(candidates, key=lambda m: m.get("m", 999))

    if not final:
        return None, None

    winner = str(final.get("w", ""))
    loser = str(final.get("l", ""))
    return winner, loser
