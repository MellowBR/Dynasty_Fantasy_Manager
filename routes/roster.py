from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models import db, Team, Player, SALARY_CAP, MAX_IR, MY_TEAM_NAME, POS_ORDER, sort_players_by_pos
from routes.auth import admin_required

roster_bp = Blueprint("roster", __name__)
POS_DISPLAY = ["QB", "RB", "WR", "TE", "K", "DEF"]


def _normalize_pos(pos: str) -> str:
    """Normalize D/ST and DST to DEF for grouping."""
    return "DEF" if pos in ("DST", "D/ST", "DEF") else pos


def _build_players_by_pos(all_players):
    """
    Group players by position in order: QB → RB → WR → TE → K → DEF.
    Within each group: healthy players first (sorted by salary desc),
    then IR players (sorted by salary desc).
    Returns OrderedDict-like list of (pos, players) tuples.
    """
    from collections import defaultdict
    groups = defaultdict(list)
    others = []

    for p in all_players:
        norm = _normalize_pos(p.position)
        if norm in POS_ORDER:
            groups[norm].append(p)
        else:
            others.append(p)

    result = []
    for pos in POS_DISPLAY:
        players = groups.get(pos, [])
        if not players:
            continue
        # Healthy first (is_on_ir=False → 0), then IR (is_on_ir=True → 1)
        # Within each group, sort by salary descending
        players.sort(key=lambda p: (p.is_on_ir, -p.salary))
        result.append((pos, players))

    if others:
        others.sort(key=lambda p: (p.is_on_ir, -p.salary))
        result.append(("OTHER", others))

    return result


@roster_bp.route("/")
@login_required
def index():
    team_query = request.args.get("team", MY_TEAM_NAME)
    teams = Team.query.order_by(Team.name).all()

    # Match by team name first, then by owner_name
    selected = Team.query.filter_by(name=team_query).first()
    if not selected:
        selected = Team.query.filter(
            Team.owner_name.ilike(team_query)
        ).first()
    if not selected and teams:
        selected = Team.query.filter_by(is_my_team=True).first() or teams[0]

    if not selected:
        return render_template("roster.html", summary=None, teams=teams,
                               selected_team=team_query)

    all_players = Player.query.filter_by(team_id=selected.id, is_dropped=False).all()
    active_players = [p for p in all_players if not p.is_on_ir]
    ir_players = [p for p in all_players if p.is_on_ir]
    players_by_pos = _build_players_by_pos(all_players)

    total_cap = sum(p.salary for p in active_players)
    ir_cap = sum(p.salary for p in ir_players)
    cap_pct = round((total_cap / SALARY_CAP) * 100, 1)

    summary = {
        "team": selected,
        "players_by_pos": players_by_pos,
        "ir_count": len(ir_players),
        "total_cap": total_cap,
        "ir_cap": ir_cap,
        "cap_remaining": SALARY_CAP - total_cap,
        "cap_pct": cap_pct,
        "renewal_candidates": [p for p in active_players if p.is_renewal_candidate()],
        "needs_review": [p for p in all_players if p.needs_review],
    }
    return render_template("roster.html", summary=summary, teams=teams,
                           selected_team=selected.name, cap=SALARY_CAP)


# ── API ──────────────────────────────────────────────────────────────────────

@roster_bp.route("/api/teams")
@login_required
def api_teams():
    teams = Team.query.order_by(Team.name).all()
    return jsonify([t.to_dict() for t in teams])


@roster_bp.route("/api/roster/<int:team_id>")
@login_required
def api_roster_by_id(team_id):
    players = Player.query.filter_by(team_id=team_id, is_dropped=False).all()
    return jsonify([p.to_dict() for p in sort_players_by_pos(players)])


@roster_bp.route("/api/roster/by_name/<path:team_name>")
@login_required
def api_roster_by_name(team_name):
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": "Team not found"}), 404
    players = Player.query.filter_by(team_id=team.id, is_dropped=False).all()
    return jsonify([p.to_dict() for p in sort_players_by_pos(players)])


@roster_bp.route("/api/player/<int:player_id>/ir", methods=["POST"])
@admin_required
def toggle_ir(player_id):
    player = db.get_or_404(Player, player_id)
    data = request.get_json() or {}
    new_state = data.get("is_on_ir", not player.is_on_ir)

    if new_state and not player.is_on_ir:
        ir_count = Player.query.filter_by(
            team_id=player.team_id, is_on_ir=True, is_dropped=False
        ).count()
        if ir_count >= MAX_IR:
            return jsonify({"error": f"IR cheio (máx {MAX_IR} slots)"}), 400

    player.is_on_ir = new_state
    db.session.commit()
    return jsonify({"success": True, "is_on_ir": player.is_on_ir})


@roster_bp.route("/api/player/<int:player_id>", methods=["PATCH"])
@admin_required
def update_player(player_id):
    player = db.get_or_404(Player, player_id)
    data = request.get_json() or {}
    allowed = {"salary", "contract_year", "espn_ref_value", "nfl_team",
               "acquisition_type", "notes", "needs_review", "via_trade"}
    for key, val in data.items():
        if key in allowed:
            setattr(player, key, val)
    db.session.commit()
    return jsonify(player.to_dict())


@roster_bp.route("/api/player/<int:player_id>/history")
@login_required
def player_history(player_id):
    """
    Ordenação cronológica por (season ASC, rollover-last, Sleeper-id-numérico ASC).

    Sleeper IDs (tx_id, draft_id) são monotonic global, então extraí-los do
    sleeper_event_ref reflete a cronologia real — mais robusto que PlayerHistory.id
    (que depende de quando cada row foi inserida, não quando o evento ocorreu).

    Rollover fica no final de cada season (bordadura de fechamento).
    """
    from models import PlayerHistory
    history = PlayerHistory.query.filter_by(player_id=player_id).all()

    def sort_key(h):
        season = h.season or 0
        ref = h.sleeper_event_ref or ""
        if ref.startswith("rollover:"):
            return (season, 1, 0, h.id)  # rollover last within season
        sleeper_num = 0
        if ref.startswith("draft:"):
            parts = ref.split(":")
            if len(parts) >= 2 and parts[1].isdigit():
                sleeper_num = int(parts[1])
        elif ref.startswith("tx:"):
            tail = ref[3:]
            if tail.isdigit():
                sleeper_num = int(tail)
        return (season, 0, sleeper_num, h.id)

    history.sort(key=sort_key)
    player = db.get_or_404(Player, player_id)
    return jsonify({
        "player": player.to_dict(),
        "history": [h.to_dict() for h in history],
    })


@roster_bp.route("/api/player/search")
@login_required
def search_players():
    q = request.args.get("q", "").strip()
    team_id = request.args.get("team_id", type=int)
    if not q:
        return jsonify([])
    query = Player.query.filter(
        Player.name.ilike(f"%{q}%"),
        Player.is_dropped == False,
    )
    if team_id:
        query = query.filter_by(team_id=team_id)
    players = query.limit(20).all()
    return jsonify([p.to_dict() for p in players])
