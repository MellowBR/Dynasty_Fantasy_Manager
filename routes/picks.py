import json as _json
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Pick, Team, DraftLotteryResult, SeasonStandings, LotteryAudit, get_config, get_current_season
from routes.auth import admin_required

picks_bp = Blueprint("picks", __name__)

PICK_SEASONS = [2025, 2026, 2027, 2028]
PICK_ROUNDS = [1, 2, 3]

LOTTERY_ODDS = {
    1: {"label": "Último lugar", "pct": 50},
    2: {"label": "2º último",    "pct": 25},
    3: {"label": "3º último",    "pct": 12},
    4: {"label": "4º último",    "pct": 5},
    5: {"label": "5º último",    "pct": 3},
    6: {"label": "6º último",    "pct": 3},
    7: {"label": "7º último",    "pct": 2},
}


@picks_bp.route("/picks")
@login_required
def picks_page():
    teams = Team.query.order_by(Team.name).all()
    all_picks = Pick.query.order_by(Pick.season, Pick.round, Pick.original_team_name).all()

    proj = _build_pick_projections()

    # M9: organizar como matrix {season: {original_team_name: {round: pick}}} com
    # ordem de linhas por projected_pick do R1 (ou alphabet fallback).
    matrix = {}
    for season in PICK_SEASONS:
        # Times únicos desta season (via original_team_name)
        season_picks = [p for p in all_picks if p.season == season]
        if not season_picks:
            continue
        teams_in_season = sorted(set(p.original_team_name for p in season_picks))
        # Ordenar por projected_pick do R1 quando disponível
        teams_in_season.sort(key=lambda name: (
            proj.get((season, 1, name), {}).get("pick_number", 999),
            name,
        ))
        matrix[season] = {
            "teams_ordered": teams_in_season,
            "cells": {},  # (team_name, round) → pick
            "projections": {},  # (team_name, round) → {pick_number, locked}
        }
        for p in season_picks:
            matrix[season]["cells"][(p.original_team_name, p.round)] = p
        for team_name in teams_in_season:
            for rnd in PICK_ROUNDS:
                key = (season, rnd, team_name)
                if key in proj:
                    matrix[season]["projections"][(team_name, rnd)] = proj[key]

    # M9: meu time vinculado (ou None se admin sem time)
    my_team_name = (current_user.team_rel.name
                    if current_user.is_authenticated and current_user.team_rel
                    else None)

    return render_template("picks.html",
                           matrix=matrix,
                           seasons=PICK_SEASONS,
                           rounds=PICK_ROUNDS,
                           teams=[t.name for t in teams],
                           lottery_odds=LOTTERY_ODDS,
                           my_team_name=my_team_name)


# ── API ──────────────────────────────────────────────────────────────────────

@picks_bp.route("/api/picks")
@login_required
def api_picks():
    season = request.args.get("season", type=int)
    team_name = request.args.get("team")
    q = Pick.query
    if season:
        q = q.filter_by(season=season)
    if team_name:
        q = q.filter_by(current_team_name=team_name)
    picks = q.order_by(Pick.season, Pick.round).all()

    # Enrich with projected position
    proj = _build_pick_projections()
    result = []
    for p in picks:
        d = p.to_dict()
        key = (p.season, p.round, p.original_team_name)
        pos_info = proj.get(key)
        if pos_info:
            d["projected_pick"] = pos_info["pick_number"]
            d["projection_locked"] = pos_info["locked"]
        else:
            d["projected_pick"] = None
            d["projection_locked"] = False
        result.append(d)
    return jsonify(result)


def _build_pick_projections() -> dict:
    """
    Build (season, round, original_team_name) → {pick_number, locked} map.

    Draft order for the draft_season with a lottery result:
      Picks 1-5:  from draft_lottery_result (weighted lottery)
      Pick 6:     7th place in standings
      Picks 7-10: 3rd-6th place in standings (6th→pick7, 5th→pick8, etc.)
      Pick 11:    runner-up
      Pick 12:    champion

    Rounds 2 and 3 follow the same order as Round 1.

    For future seasons without a lottery: fall back to standings (reverse rank).
    If no standings either: no projection (alphabetical fallback in template).
    """
    proj = {}
    season = get_current_season()
    draft_season = season + 1
    lottery_locked = get_config("season_locked", "false") == "true"

    # ── Draft season with lottery result ────────────────────────────────
    lottery = DraftLotteryResult.query.filter_by(season=draft_season).all()

    if lottery:
        # Lottery result contains pick_number → team_name for all 12 picks.
        # Apply the same order to all 3 rounds.
        for lr in lottery:
            for rnd in PICK_ROUNDS:
                proj[(draft_season, rnd, lr.team_name)] = {
                    "pick_number": lr.pick_number,
                    "locked": lr.locked if rnd == 1 else lottery_locked,
                }
    else:
        # No lottery for draft_season: build order from standings
        _apply_standings_order(proj, season, draft_season, lottery_locked)

    # ── Future seasons (2027, 2028, ...) without lottery ────────────────
    for future_season in PICK_SEASONS:
        if future_season <= draft_season:
            continue
        # Check if there's a lottery for this future season
        future_lottery = DraftLotteryResult.query.filter_by(season=future_season).all()
        if future_lottery:
            for lr in future_lottery:
                for rnd in PICK_ROUNDS:
                    proj[(future_season, rnd, lr.team_name)] = {
                        "pick_number": lr.pick_number,
                        "locked": lr.locked,
                    }
        else:
            # Try standings from the season before this draft
            prev_season = future_season - 1
            _apply_standings_order(proj, prev_season, future_season, False)

    return proj


def _apply_standings_order(proj: dict, standings_season: int,
                           draft_season: int, locked: bool):
    """
    Build pick order from standings when no lottery result exists.
    Uses the same logic as the lottery fixed picks:
      Picks 1-5:  8th-12th place (worst teams, ordered worst-first)
      Pick 6:     7th place
      Picks 7-10: 6th, 5th, 4th, 3rd place
      Pick 11:    runner-up
      Pick 12:    champion
    Falls back to reverse rank if standings don't match the expected structure.
    """
    standings = SeasonStandings.query.filter_by(season=standings_season)\
        .order_by(SeasonStandings.rank).all()
    if not standings:
        return

    by_rank = {s.rank: s for s in standings}
    runner_up = next((s for s in standings if s.is_runner_up), None)
    champion = next((s for s in standings if s.is_champion), None)

    order = []  # list of (pick_number, team_name)

    # Picks 1-5: ranks 12, 11, 10, 9, 8 (worst first)
    for pick_num, rank in [(1, 12), (2, 11), (3, 10), (4, 9), (5, 8)]:
        s = by_rank.get(rank)
        if s:
            order.append((pick_num, s.team_name))

    # Pick 6: rank 7
    s7 = by_rank.get(7)
    if s7:
        order.append((6, s7.team_name))

    # Picks 7-10: ranks 6, 5, 4, 3
    for pick_num, rank in [(7, 6), (8, 5), (9, 4), (10, 3)]:
        s = by_rank.get(rank)
        if s:
            order.append((pick_num, s.team_name))

    # Pick 11: runner-up, Pick 12: champion
    if runner_up:
        order.append((11, runner_up.team_name))
    if champion:
        order.append((12, champion.team_name))

    # Apply to all rounds
    for pick_num, team_name in order:
        for rnd in PICK_ROUNDS:
            proj[(draft_season, rnd, team_name)] = {
                "pick_number": pick_num,
                "locked": locked,
            }


@picks_bp.route("/api/picks/<int:pick_id>", methods=["PATCH"])
@admin_required
def update_pick(pick_id):
    pick = db.get_or_404(Pick, pick_id)
    data = request.get_json() or {}
    for field in ("current_team_name", "traded_away", "notes"):
        if field in data:
            setattr(pick, field, data[field])
    # Sync current_team_id if name changed
    if "current_team_name" in data:
        team = Team.query.filter_by(name=data["current_team_name"]).first()
        if team:
            pick.current_team_id = team.id
            pick.traded_away = (team.id != pick.original_team_id)
    db.session.commit()
    return jsonify(pick.to_dict())


@picks_bp.route("/api/picks/<int:pick_id>/reset", methods=["POST"])
@admin_required
def reset_pick(pick_id):
    pick = db.get_or_404(Pick, pick_id)
    pick.current_team_id = pick.original_team_id
    pick.current_team_name = pick.original_team_name
    pick.traded_away = False
    pick.notes = ""
    db.session.commit()
    return jsonify(pick.to_dict())


# ── M8: Draft Lottery Audit ──────────────────────────────────────────────────

@picks_bp.route("/picks/lottery/<int:season>")
@login_required
def lottery_audit_page(season):
    """M8 — página de auditoria do lottery. Mostra audit canônica + histórico
    de tentativas superseded + botão de verificação."""
    canonical = LotteryAudit.query.filter_by(season=season, is_canonical=True).first()
    if not canonical:
        return render_template("lottery_audit.html",
                               season=season,
                               error=f"Nenhum lottery executado para a season {season}."), 404

    superseded = (LotteryAudit.query
                  .filter_by(season=season, is_canonical=False)
                  .order_by(LotteryAudit.executed_at.desc())
                  .all())

    picks = (DraftLotteryResult.query
             .filter_by(season=season)
             .order_by(DraftLotteryResult.pick_number)
             .all())

    try:
        pool = _json.loads(canonical.pool_json or "[]")
    except (ValueError, TypeError):
        pool = []

    return render_template("lottery_audit.html",
                           season=season,
                           audit=canonical,
                           pool=pool,
                           superseded=superseded,
                           picks=picks)


@picks_bp.route("/api/picks/lottery/<int:season>/verify")
@login_required
def lottery_audit_verify(season):
    """M8 — re-roda o lottery com seed + pool salvos e compara com DraftLotteryResult.
    Retorna match booleano + hash_match + diff."""
    from routes.offseason import _draw_weighted_lottery, _compute_result_hash

    canonical = LotteryAudit.query.filter_by(season=season, is_canonical=True).first()
    if not canonical:
        return jsonify({"error": f"Nenhum audit canônico para season {season}"}), 404

    try:
        pool = _json.loads(canonical.pool_json)
        weights = _json.loads(canonical.weights_json)
    except (ValueError, TypeError):
        return jsonify({"error": "Audit corrompida"}), 500

    # Reproduce
    reproduced = _draw_weighted_lottery(pool, canonical.random_seed)
    reproduced_hash = _compute_result_hash(reproduced)

    # Actual from DraftLotteryResult (picks 1-5 com source='lottery')
    actual_rows = (DraftLotteryResult.query
                   .filter(DraftLotteryResult.season == season,
                           DraftLotteryResult.pick_number <= 5)
                   .order_by(DraftLotteryResult.pick_number)
                   .all())
    actual = [{"pick_number": r.pick_number, "team_name": r.team_name, "team_id": r.team_id}
              for r in actual_rows]

    # Compare
    match = (len(reproduced) == len(actual) and
             all(r["pick_number"] == a["pick_number"] and r["team_name"] == a["team_name"]
                 for r, a in zip(reproduced, actual)))
    hash_match = reproduced_hash == canonical.result_hash

    return jsonify({
        "match": match,
        "result_hash_match": hash_match,
        "seed": canonical.random_seed,
        "weights": weights,
        "pool": pool,
        "reproduced": reproduced,
        "actual": actual,
        "reproduced_hash": reproduced_hash,
        "stored_hash": canonical.result_hash,
    })
