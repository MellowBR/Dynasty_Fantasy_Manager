from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models import db, Player, Team, PlayerHistory, SALARY_CAP, MAX_ROSTER, sort_players_by_pos
from salary_engine import (
    full_contract_table, project_next_salary, draft_budget
)
from routes.auth import admin_required

salary_bp = Blueprint("salary", __name__)


@salary_bp.route("/salary")
@login_required
def salary_page():
    return render_template("salary.html")


@salary_bp.route("/cap_projector")
@login_required
def cap_projector_page():
    teams = Team.query.order_by(Team.name).all()
    my_team = Team.query.filter_by(is_my_team=True).first()
    return render_template("cap_projector.html",
                           teams=[t.name for t in teams],
                           my_team=my_team.name if my_team else "")


@salary_bp.route("/salary_history")
@login_required
def salary_history_page():
    teams = Team.query.order_by(Team.name).all()
    return render_template("salary_history.html", teams=[t.name for t in teams])


# ── API ──────────────────────────────────────────────────────────────────────

@salary_bp.route("/api/salary/calculate", methods=["POST"])
@login_required
def calculate():
    data = request.get_json() or {}
    try:
        espn_raw = float(data.get("espn_ref_value", 0) or 0)
        espn_adj = espn_raw * 1.2  # UI sends raw; engine expects already-adjusted
        table = full_contract_table(
            acquisition_type=data.get("acquisition_type", "auction_draft"),
            year1_value_paid=float(data.get("year1_value", 0) or 0),
            espn_adj=espn_adj,
            current_contract_year=int(data.get("contract_year", 1) or 1),
        )
        return jsonify({
            "player_name": data.get("player_name", ""),
            "espn_ref_value": espn_raw,
            "espn_adjusted": espn_adj,
            "acquisition_type": data.get("acquisition_type", ""),
            "table": table,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@salary_bp.route("/api/cap_projector/<path:team_name>")
@login_required
def cap_projector_data(team_name):
    from models import ESPNValue, ESPNImportLog, get_current_season
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    players = sort_players_by_pos(
        Player.query.filter_by(team_id=team.id, is_dropped=False).all()
    )

    # Build ESPN value index for this season+1
    target_season = get_current_season() + 1
    espn_vals = {ev.player_id: ev for ev in
                 ESPNValue.query.filter_by(season=target_season).all()}

    player_data = []
    for p in players:
        ev = espn_vals.get(p.id)
        player_data.append({
            **p.to_dict(),
            "next_salary": project_next_salary(p),
            "espn_is_final": ev.is_final if ev else None,
            "espn_season": ev.season if ev else None,
        })

    budget = draft_budget(players)

    # ESPN import status
    last_import = ESPNImportLog.query.filter_by(season=target_season)\
        .order_by(ESPNImportLog.imported_at.desc()).first()
    espn_status = None
    if last_import:
        espn_status = {
            "status": last_import.status,
            "date": last_import.imported_at.strftime("%d/%m/%Y %H:%M") if last_import.imported_at else "",
            "season": last_import.season,
        }

    return jsonify({
        "team": team.to_dict(),
        "players": player_data,
        "budget": budget,
        "salary_cap": SALARY_CAP,
        "espn_status": espn_status,
    })


@salary_bp.route("/api/salary_history")
@login_required
def salary_history_data():
    """
    Returns events from PlayerHistory (not SalaryHistory) to narrate how each
    player got to their current salary. Filters by current team, player name,
    or event season. Grouped client-side by player_id.
    """
    team_name = request.args.get("team")
    player_name = request.args.get("player")
    season = request.args.get("season", type=int)

    q = PlayerHistory.query.join(Player, PlayerHistory.player_id == Player.id)

    if team_name:
        team = Team.query.filter_by(name=team_name).first()
        if team:
            q = q.filter(Player.team_id == team.id)
    if player_name:
        q = q.filter(Player.name.ilike(f"%{player_name}%"))
    if season:
        q = q.filter(PlayerHistory.season == season)

    records = q.order_by(
        Player.name.asc(),
        PlayerHistory.season.desc(),
        PlayerHistory.id.desc(),
    ).limit(500).all()

    out = []
    for ph in records:
        p = ph.player
        out.append({
            "player_id": p.id,
            "player_name": p.name,
            "position": p.position,
            "team_name": p.fantasy_team_name,
            "current_salary": p.salary,
            "season": ph.season,
            "event_type": ph.event_type,
            "notes": ph.notes or "",
            "salary": ph.salary,
            "contract_year": ph.contract_year,
            "created_at": ph.created_at.strftime("%d/%m/%Y %H:%M") if ph.created_at else "",
        })
    return jsonify(out)


@salary_bp.route("/api/espn_values/update", methods=["POST"])
@admin_required
def update_espn_values():
    """
    Bulk update ESPN ref values.
    Body: {players: [{player_id or name, espn_value}, ...]}
    """
    from models import ESPNValue, get_current_season
    data = request.get_json() or {}
    updates = data.get("players", [])
    updated = 0
    errors = []

    for entry in updates:
        pid = entry.get("player_id")
        name = entry.get("name", "").strip()
        espn_raw = float(entry.get("espn_value", 0) or 0)

        if pid:
            player = Player.query.get(pid)
        elif name:
            from player_lookup import find_player_by_name
            player = find_player_by_name(name)
        else:
            continue

        if not player:
            errors.append(f"Player not found: {name or pid}")
            continue

        player.espn_ref_value = espn_raw * 1.2  # store adjusted
        # Log in ESPNValue table
        ev = ESPNValue.query.filter_by(player_id=player.id, season=get_current_season()).first()
        if ev:
            ev.espn_raw = espn_raw
            ev.espn_adjusted = espn_raw * 1.2
        else:
            ev = ESPNValue(player_id=player.id, season=get_current_season(),
                           espn_raw=espn_raw, espn_adjusted=espn_raw * 1.2)
            db.session.add(ev)
        updated += 1

    db.session.commit()
    return jsonify({"updated": updated, "errors": errors})
