import json as _json
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Pick, Team, DraftLotteryResult, SeasonStandings, LotteryAudit, get_config, get_current_season
from dynasty_values import get_dynasty_values, pick_sleeper_id, resolve_asset_value
from routes.auth import admin_required

picks_bp = Blueprint("picks", __name__)

PICK_SEASONS = [2025, 2026, 2027, 2028]
PICK_ROUNDS = [1, 2, 3]

def _build_lottery_odds(weights=None):
    """M15: legenda de odds derivada de pesos (pct = peso/total — nunca hardcoded).
    M15-FIX: audit-first — quando há audit canônica da draft_season, passa-se o
    `weights_json` dela (pesos efetivamente usados no sorteio); sem audit, usa o
    default canônico (`DEFAULT_LOTTERY_WEIGHTS`)."""
    from routes.offseason import DEFAULT_LOTTERY_WEIGHTS, _seed_rank, _normalize_weights
    w = _normalize_weights(weights) if weights else dict(DEFAULT_LOTTERY_WEIGHTS)
    total = sum(w.values())
    odds = {}
    for seed_idx in sorted(w.keys()):
        weight = w[seed_idx]
        odds[seed_idx] = {
            "label": f"{_seed_rank(seed_idx)}º lugar",
            "weight": weight,
            "pct": round(weight * 100.0 / total, 1) if total else 0,
        }
    return odds


def _canonical_lottery_weights(draft_season):
    """M15-FIX: pesos efetivamente usados no sorteio canônico da draft_season,
    lidos de LotteryAudit.weights_json. Retorna None se não houver audit canônica."""
    canonical = LotteryAudit.query.filter_by(
        season=draft_season, is_canonical=True).first()
    if not canonical:
        return None
    try:
        return _json.loads(canonical.weights_json)
    except (ValueError, TypeError):
        return None


@picks_bp.route("/picks")
@login_required
def picks_page():
    teams = Team.query.order_by(Team.name).all()
    all_picks = Pick.query.order_by(Pick.season, Pick.round, Pick.original_team_name).all()

    proj = _build_pick_projections()

    # M9: organizar como matrix {season: {team: {round: pick}}} com ordem de linhas
    # por projected_pick do R1 (ou alphabet fallback).
    # S3: linhas e células são chaveadas pelo **id** do time; o nome vem do Team vivo
    # (rótulo). Antes o eixo era `original_team_name` — um rename criava uma segunda
    # linha para o mesmo time, sem projeção.
    teams_by_id = {t.id: t for t in teams}
    matrix = {}
    for season in PICK_SEASONS:
        season_picks = [p for p in all_picks if p.season == season]
        if not season_picks:
            continue
        tids_in_season = {p.original_team_id for p in season_picks if p.original_team_id}
        rows = [{"id": tid, "name": teams_by_id[tid].name}
                for tid in tids_in_season if tid in teams_by_id]
        # Ordenar por projected_pick do R1 quando disponível
        rows.sort(key=lambda r: (
            proj.get((season, 1, r["id"]), {}).get("pick_number", 999),
            r["name"],
        ))
        matrix[season] = {
            "teams_ordered": rows,
            "cells": {},  # (team_id, round) → pick
            "projections": {},  # (team_id, round) → {pick_number, locked}
        }
        for p in season_picks:
            matrix[season]["cells"][(p.original_team_id, p.round)] = p
        for r in rows:
            for rnd in PICK_ROUNDS:
                key = (season, rnd, r["id"])
                if key in proj:
                    matrix[season]["projections"][(r["id"], rnd)] = proj[key]

    # M9: meu time vinculado (ou None se admin sem time)
    my_team_name = (current_user.team_rel.name
                    if current_user.is_authenticated and current_user.team_rel
                    else None)

    return render_template("picks.html",
                           matrix=matrix,
                           seasons=PICK_SEASONS,
                           rounds=PICK_ROUNDS,
                           teams=[t.name for t in teams],
                           lottery_odds=_build_lottery_odds(
                               _canonical_lottery_weights(get_current_season() + 1)),
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
        # S3: o parâmetro segue sendo o nome (contrato público da API), mas o filtro
        # roda sobre o id — resolve-se o Team uma vez em vez de casar string.
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            return jsonify([])
        q = q.filter_by(current_team_id=team.id)
    picks = q.order_by(Pick.season, Pick.round).all()

    # Enrich with projected position and pre-resolved dynasty value.
    # dynasty_value pré-resolvido no backend elimina réplica da lógica DP_/FP_
    # no frontend (T2-FIX-2). Fonte única: dynasty_values.pick_sleeper_id.
    proj = _build_pick_projections()
    values_map = get_dynasty_values().get("values", {})
    current_season = get_current_season()
    result = []
    for p in picks:
        d = p.to_dict()
        key = (p.season, p.round, p.original_team_id)  # S3: join por id estável
        pos_info = proj.get(key)
        if pos_info:
            d["projected_pick"] = pos_info["pick_number"]
            d["projection_locked"] = pos_info["locked"]
            p.projected_pick = pos_info["pick_number"]
        else:
            d["projected_pick"] = None
            d["projection_locked"] = False
        sid = pick_sleeper_id(p, current_season, values_map)
        d["dynasty_value"] = resolve_asset_value(values_map, sid)
        # T3: picks têm redraft=0 sempre (puro futuro). Mantém key explícito para simetria.
        d["redraft_value"] = 0
        result.append(d)
    return jsonify(result)


def _resolve_tid(team_id, team_name, name_to_id):
    """
    S3 — id estável do time, com queda para o nome apenas em linhas legadas.

    `DraftLotteryResult.team_id` e `SeasonStandings.team_id` são nullable; linhas
    antigas podem não tê-lo. O nome é fallback de compatibilidade, nunca o caminho
    principal — e não é atualizado em lugar nenhum (o `team_name` dessas tabelas é
    congelado de propósito: é a referência da auditoria do M8).
    """
    if team_id:
        return team_id
    return name_to_id.get(team_name)


def _build_pick_projections() -> dict:
    """
    Build (season, round, original_team_id) → {pick_number, locked} map.

    S3: a chave do join é o **id do time**, não o nome. `Team.name` é mutável (o
    sync o reescreve em rename) e o join cruza três tabelas — `Pick`,
    `DraftLotteryResult` e `SeasonStandings`. Casar por string fazia o time
    renomeado perder a projeção (fallback 999). Refrescar o nome nas tabelas de
    lottery/standings **não** era alternativa: quebraria o verify do M8, que
    compara o `team_name` congelado no `pool_json` com o da tabela viva.

    Draft order for the draft_season with a lottery result:
      Picks 1..N:  from draft_lottery_result (weighted lottery; N = nº de seeds)
      Picks N+1..: fixed by standings (M15: default N=6 → picks 1-6 são lottery)
    O branch de lottery é data-driven (lê lr.pick_number direto do DB).

    M16: o lottery define APENAS o Round 1. Rounds 2 e 3 revertem para a ordem
    standings-invertida (12º abre, campeão fecha — picks 13/25 ... 24/36), via a
    fonte única _build_default_draft_order — NÃO a ordem sorteada.

    For future seasons without a lottery: fall back to standings order via
    _apply_standings_order → fonte única _build_default_draft_order.
    If no standings either: no projection (alphabetical fallback in template).
    """
    proj = {}
    season = get_current_season()
    draft_season = season + 1
    lottery_locked = get_config("season_locked", "false") == "true"
    name_to_id = {t.name: t.id for t in Team.query.all()}

    # ── Draft season with lottery result ────────────────────────────────
    lottery = DraftLotteryResult.query.filter_by(season=draft_season).all()

    if lottery:
        # M16: R1 = lottery; R2/R3 = standings invertido (fonte única).
        _apply_lottery_with_standings_tail(
            proj, lottery, standings_season=season,
            draft_season=draft_season, tail_locked=lottery_locked,
            name_to_id=name_to_id)
    else:
        # No lottery for draft_season: build order from standings
        _apply_standings_order(proj, season, draft_season, lottery_locked,
                               name_to_id)

    # ── Future seasons (2027, 2028, ...) ────────────────────────────────
    for future_season in PICK_SEASONS:
        if future_season <= draft_season:
            continue
        # Check if there's a lottery for this future season
        future_lottery = DraftLotteryResult.query.filter_by(season=future_season).all()
        if future_lottery:
            f_locked = future_lottery[0].locked
            _apply_lottery_with_standings_tail(
                proj, future_lottery, standings_season=future_season - 1,
                draft_season=future_season, tail_locked=f_locked,
                name_to_id=name_to_id)
        else:
            # Try standings from the season before this draft
            _apply_standings_order(proj, future_season - 1, future_season, False,
                                   name_to_id)

    return proj


def _apply_standings_order(proj: dict, standings_season: int,
                           draft_season: int, locked: bool, name_to_id: dict):
    """
    Build pick order from standings when no lottery result exists.
    M15: delega à fonte única _build_default_draft_order (mesma config de seeds
    e fronteira lottery/standings do sorteio real), evitando réplica do limiar.
    """
    from routes.offseason import _build_default_draft_order
    standings = SeasonStandings.query.filter_by(season=standings_season)\
        .order_by(SeasonStandings.rank).all()
    if not standings:
        return

    for pick_num, team_id, team_name in _build_default_draft_order(standings):
        tid = _resolve_tid(team_id, team_name, name_to_id)
        if tid is None:
            continue
        for rnd in PICK_ROUNDS:
            proj[(draft_season, rnd, tid)] = {
                "pick_number": pick_num,
                "locked": locked,
            }


def _apply_lottery_with_standings_tail(proj, lottery_rows, standings_season,
                                       draft_season, tail_locked, name_to_id):
    """
    M16: o lottery define APENAS o Round 1. R2/R3 revertem para a ordem
    standings-invertida (12º abre, campeão fecha), reusando a fonte única
    _build_default_draft_order — sem reimplementar a ordem por standings.
    Corrige o fan-out anterior que aplicava a ordem sorteada aos 3 rounds.
    """
    from routes.offseason import _build_default_draft_order
    # R1 = ordem sorteada (data-driven do DraftLotteryResult)
    for lr in lottery_rows:
        tid = _resolve_tid(lr.team_id, lr.team_name, name_to_id)
        if tid is None:
            continue
        proj[(draft_season, 1, tid)] = {
            "pick_number": lr.pick_number,
            "locked": lr.locked,
        }
    # R2/R3 = standings invertido (lottery não se aplica aos rounds seguintes)
    standings = SeasonStandings.query.filter_by(season=standings_season)\
        .order_by(SeasonStandings.rank).all()
    tail_rounds = [r for r in PICK_ROUNDS if r != 1]
    for pick_num, team_id, team_name in _build_default_draft_order(standings):
        tid = _resolve_tid(team_id, team_name, name_to_id)
        if tid is None:
            continue
        for rnd in tail_rounds:
            proj[(draft_season, rnd, tid)] = {
                "pick_number": pick_num,
                "locked": tail_locked,
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

    # Actual from DraftLotteryResult (picks do lottery). M15: a contagem deriva
    # de len(pool) do snapshot salvo — audits de 5 ou 6 seeds verificam certo.
    n_lottery = len(pool)
    actual_rows = (DraftLotteryResult.query
                   .filter(DraftLotteryResult.season == season,
                           DraftLotteryResult.pick_number <= n_lottery)
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
