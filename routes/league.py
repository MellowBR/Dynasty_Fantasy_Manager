"""League Hub — visão geral da liga + detalhe por time (L1)."""
from collections import defaultdict

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from models import (
    db, Team, Player, Pick, SeasonStandings,
    SALARY_CAP, get_current_season, sort_players_by_pos,
)
from dynasty_values import get_dynasty_values, resolve_asset_value
from routes.roster import _build_players_by_pos as build_players_by_pos, _ACQ_LABELS

league_bp = Blueprint("league", __name__)


def _build_team_card(team, standing, pick_count, players, dv_map, my_team_id=None):
    """Monta dict do card de um time. Sem queries — tudo já carregado.
    M17: `is_my_team` deriva do usuário logado (my_team_id = current_user.team_rel.id),
    não mais da flag legada Team.is_my_team."""
    cap_used = sum(p.salary for p in players if not p.is_on_ir)
    dynasty_total = sum(
        resolve_asset_value(dv_map, p.sleeper_player_id) or 0
        for p in players if not p.is_on_ir
    )
    return {
        "id": team.id,
        "name": team.name,
        "owner_name": team.owner_name or "",
        "owner_avatar": team.owner_avatar or "",
        "is_my_team": team.id == my_team_id,
        "cap_used": cap_used,
        "cap_space": SALARY_CAP - cap_used,
        "pick_count": pick_count,
        "dynasty_total": dynasty_total,
        "rank": standing.rank if standing else 999,
        "wins": standing.wins if standing else None,
        "losses": standing.losses if standing else None,
        "points_for": standing.points_for if standing else None,
        "is_champion": bool(standing.is_champion) if standing else False,
        "is_runner_up": bool(standing.is_runner_up) if standing else False,
    }


@league_bp.route("/league")
@login_required
def league_hub():
    season = get_current_season()
    teams = Team.query.order_by(Team.name).all()
    standings = {s.team_id: s for s in SeasonStandings.query.filter_by(season=season).all()}
    pick_counts = dict(
        db.session.query(Pick.current_team_id, func.count())
        .group_by(Pick.current_team_id).all()
    )
    all_players = Player.query.filter_by(is_dropped=False).all()
    players_by_team = defaultdict(list)
    for p in all_players:
        if p.team_id:
            players_by_team[p.team_id].append(p)
    dv_map = get_dynasty_values().get("values", {})

    my_team_id = current_user.team_rel.id if current_user.team_rel else None
    cards = [
        _build_team_card(
            t, standings.get(t.id), pick_counts.get(t.id, 0),
            players_by_team.get(t.id, []), dv_map, my_team_id,
        )
        for t in teams
    ]
    cards.sort(key=lambda c: (c["rank"], c["name"]))

    return render_template("league.html", cards=cards, season=season)


@league_bp.route("/team/<int:team_id>")
@login_required
def team_detail(team_id):
    team = db.get_or_404(Team, team_id)
    season = get_current_season()

    players = Player.query.filter_by(team_id=team.id, is_dropped=False).all()
    dv_map = get_dynasty_values().get("values", {})
    for p in players:
        p.dynasty_value = resolve_asset_value(dv_map, p.sleeper_player_id)
        p.acquisition_label = _ACQ_LABELS.get(p.acquisition_type, p.acquisition_type or "—")
    players_by_pos = build_players_by_pos(players)

    picks = Pick.query.filter_by(current_team_id=team.id)\
        .order_by(Pick.season, Pick.round).all()
    picks_by_season = defaultdict(list)
    for pk in picks:
        picks_by_season[pk.season].append(pk)

    standing = SeasonStandings.query.filter_by(season=season, team_id=team.id).first()

    active = [p for p in players if not p.is_on_ir]
    ir = [p for p in players if p.is_on_ir]
    cap_used = sum(p.salary for p in active)
    ir_cap = sum(p.salary for p in ir)

    cap_by_pos = defaultdict(float)
    for p in active:
        cap_by_pos[p.position or "OTHER"] += p.salary

    is_my_team = bool(
        current_user.is_authenticated
        and current_user.team_rel
        and current_user.team_rel.id == team.id
    )
    my_team_name = current_user.team_rel.name if (
        current_user.is_authenticated and current_user.team_rel
    ) else None

    summary = {
        "team": team,
        "standing": standing,
        "players_by_pos": players_by_pos,
        "picks_by_season": dict(sorted(picks_by_season.items())),
        "cap_used": cap_used,
        "cap_remaining": SALARY_CAP - cap_used,
        "ir_cap": ir_cap,
        "ir_count": len(ir),
        "active_count": len(active),
        "cap_by_pos": dict(cap_by_pos),
        "dv_map": dv_map,
        "dynasty_total": sum(p.dynasty_value or 0 for p in active),
        "is_my_team": is_my_team,
        "my_team_name": my_team_name,
        "season": season,
        "cap": SALARY_CAP,
    }
    return render_template("team_detail.html", **summary)
