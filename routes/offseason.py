"""
routes/offseason.py — Offseason flow: standings, lottery, rollover.

Steps:
  1. Close Season (import standings)
  2. Lock Draft Order (lottery for picks 1-5)
  3. Update ESPN Values
  4. Season Rollover
  5-7. Rookie Draft, Keepers, FA Auction (informational)
"""

import random
import requests as req
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from models import (
    db, Team, Pick, Player, SalaryHistory,
    SeasonStandings, DraftLotteryResult, AppConfig,
    get_config, set_config, get_current_season, is_offseason,
    SALARY_CAP, MY_OWNER_ID, MY_TEAM_NAME, LEAGUE_ID,
)
from routes.auth import admin_required

offseason_bp = Blueprint("offseason", __name__)

SLEEPER_BASE = "https://api.sleeper.app/v1"

# Default lottery weights: 12th place → 8th place
DEFAULT_LOTTERY_WEIGHTS = {1: 50, 2: 25, 3: 12, 4: 5, 5: 3}


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

    # Build lottery seed → team name map from standings (8th-12th place)
    lottery_seeds = {}  # seed 1=12th, 2=11th, 3=10th, 4=9th, 5=8th
    by_rank = {s.rank: s for s in standings}
    for seed, rank in [(1, 12), (2, 11), (3, 10), (4, 9), (5, 8)]:
        s = by_rank.get(rank)
        if s:
            lottery_seeds[seed] = s.team_name

    return render_template("offseason.html",
                           season=season,
                           steps=steps,
                           standings=standings,
                           lottery=lottery,
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
    Run weighted lottery for picks 1-5 and assign fixed picks 6-12.
    Draft order rules:
      Picks 1-5:  Lottery among 8th-12th place (worst teams)
      Pick 6:     7th place (fixed)
      Picks 7-10: 3rd-6th place (reverse order: 6th gets pick 7, etc.)
      Pick 11:    Runner-up
      Pick 12:    Champion
    """
    season = get_current_season()
    draft_season = season + 1
    data = request.get_json() or {}
    weights = data.get("weights", DEFAULT_LOTTERY_WEIGHTS)

    standings = SeasonStandings.query.filter_by(season=season)\
        .order_by(SeasonStandings.rank).all()
    if len(standings) < 12:
        return jsonify({"error": f"Standings incompletos ({len(standings)} times)"}), 400

    # Identify groups by rank
    by_rank = {s.rank: s for s in standings}

    # Lottery pool: ranks 8-12 (worst 5 teams)
    lottery_pool = []
    for i, rank in enumerate([12, 11, 10, 9, 8]):
        s = by_rank.get(rank)
        if s:
            seed = i + 1  # 1=worst (12th place), 5=best (8th)
            w = float(weights.get(str(seed), weights.get(seed, 1)))
            lottery_pool.append({"team_name": s.team_name, "team_id": s.team_id,
                                 "seed": seed, "weight": w})

    # Weighted lottery draw (without replacement)
    lottery_results = []
    pool = list(lottery_pool)
    for pick_num in range(1, 6):
        total_w = sum(p["weight"] for p in pool)
        if total_w <= 0:
            break
        r = random.uniform(0, total_w)
        cumulative = 0
        drawn = pool[0]
        for p in pool:
            cumulative += p["weight"]
            if r <= cumulative:
                drawn = p
                break
        lottery_results.append({
            "pick_number": pick_num,
            "team_name": drawn["team_name"],
            "team_id": drawn["team_id"],
            "source": "lottery",
        })
        pool = [p for p in pool if p["team_name"] != drawn["team_name"]]

    # Fixed picks 6-12
    fixed_results = []

    # Pick 6: 7th place
    s7 = by_rank.get(7)
    if s7:
        fixed_results.append({"pick_number": 6, "team_name": s7.team_name,
                               "team_id": s7.team_id, "source": "standings"})

    # Picks 7-10: 6th, 5th, 4th, 3rd place
    for pick_num, rank in [(7, 6), (8, 5), (9, 4), (10, 3)]:
        s = by_rank.get(rank)
        if s:
            fixed_results.append({"pick_number": pick_num, "team_name": s.team_name,
                                   "team_id": s.team_id, "source": "standings"})

    # Pick 11: runner-up, Pick 12: champion
    runner_up = next((s for s in standings if s.is_runner_up), None)
    champion = next((s for s in standings if s.is_champion), None)
    if runner_up:
        fixed_results.append({"pick_number": 11, "team_name": runner_up.team_name,
                               "team_id": runner_up.team_id, "source": "standings"})
    if champion:
        fixed_results.append({"pick_number": 12, "team_name": champion.team_name,
                               "team_id": champion.team_id, "source": "standings"})

    all_results = lottery_results + fixed_results

    # Save (but don't lock)
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
    db.session.commit()

    return jsonify({"success": True, "results": all_results})


@offseason_bp.route("/api/offseason/save_lottery", methods=["POST"])
@admin_required
def save_lottery():
    """Save manually edited lottery results (picks 1-5)."""
    season = get_current_season()
    draft_season = season + 1
    data = request.get_json() or {}
    picks = data.get("picks", [])

    # Only update picks 1-5, keep fixed picks 6-12
    for p in picks:
        pick_num = p.get("pick_number")
        if not pick_num or pick_num > 5:
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
