from flask import Blueprint, render_template, request, jsonify
from models import db, Player, Pick, Trade, Team, PlayerHistory, SALARY_CAP, MY_TEAM_NAME, get_current_season
from datetime import datetime

trades_bp = Blueprint("trades", __name__)


@trades_bp.route("/trades")
def trades_page():
    teams = Team.query.order_by(Team.name).all()
    recent = Trade.query.order_by(Trade.created_at.desc()).limit(30).all()
    owner_map = {t.name: t.owner_name or "" for t in teams}
    avatar_map = {t.name: t.owner_avatar or "" for t in teams}
    return render_template("trades.html",
                           teams=teams,
                           recent_trades=recent,
                           owner_map=owner_map,
                           avatar_map=avatar_map)


# ── API ──────────────────────────────────────────────────────────────────────

@trades_bp.route("/api/trades/preview", methods=["POST"])
def preview_trade():
    data = request.get_json() or {}
    team_a_name = data.get("team_a", "")
    team_b_name = data.get("team_b", "")

    team_a = Team.query.filter_by(name=team_a_name).first()
    team_b = Team.query.filter_by(name=team_b_name).first()

    if not team_a or not team_b:
        return jsonify({"error": "Uma ou ambas as equipes não encontradas"}), 404
    if team_a.id == team_b.id:
        return jsonify({"error": "Não é possível fazer trade consigo mesmo"}), 400

    players_a = _fetch_players(data.get("players_a", []))
    players_b = _fetch_players(data.get("players_b", []))
    picks_a   = _fetch_picks(data.get("picks_a", []))
    picks_b   = _fetch_picks(data.get("picks_b", []))

    cap_a = team_a.active_salary()
    cap_b = team_b.active_salary()

    sal_a_out = sum(p.salary for p in players_a)
    sal_a_in  = sum(p.salary for p in players_b)
    sal_b_out = sum(p.salary for p in players_b)
    sal_b_in  = sum(p.salary for p in players_a)

    cap_a_after = cap_a - sal_a_out + sal_a_in
    cap_b_after = cap_b - sal_b_out + sal_b_in

    def side(team, cap_before, cap_after, out_players, in_players, out_picks, in_picks):
        return {
            "name": team.name,
            "cap_before": cap_before,
            "cap_after": round(cap_after, 2),
            "cap_remaining_after": round(SALARY_CAP - cap_after, 2),
            "over_cap": cap_after > SALARY_CAP,
            "players_out": [p.to_dict() for p in out_players],
            "players_in":  [p.to_dict() for p in in_players],
            "picks_out": [p.to_dict() for p in out_picks],
            "picks_in":  [p.to_dict() for p in in_picks],
        }

    return jsonify({
        "team_a": side(team_a, cap_a, cap_a_after, players_a, players_b, picks_a, picks_b),
        "team_b": side(team_b, cap_b, cap_b_after, players_b, players_a, picks_b, picks_a),
    })


@trades_bp.route("/api/trades/confirm", methods=["POST"])
def confirm_trade():
    data = request.get_json() or {}
    team_a_name = data.get("team_a", "")
    team_b_name = data.get("team_b", "")

    team_a = Team.query.filter_by(name=team_a_name).first()
    team_b = Team.query.filter_by(name=team_b_name).first()
    if not team_a or not team_b:
        return jsonify({"error": "Equipes não encontradas"}), 404
    if team_a.id == team_b.id:
        return jsonify({"error": "Mesmo time"}), 400

    players_a = _fetch_players(data.get("players_a", []))
    players_b = _fetch_players(data.get("players_b", []))
    picks_a   = _fetch_picks(data.get("picks_a", []))
    picks_b   = _fetch_picks(data.get("picks_b", []))

    desc_parts = []

    season = get_current_season()

    for p in players_a:
        if p.team_id != team_a.id:
            return jsonify({"error": f"{p.name} não pertence a {team_a_name}"}), 400
        p.team_id = team_b.id
        p.fantasy_team = team_b.name
        p.is_my_team = team_b.is_my_team
        p.via_trade = True
        desc_parts.append(f"{p.name} ({team_a_name}→{team_b_name})")
        db.session.add(PlayerHistory(
            player_id=p.id, season=season, team_name=team_b.name,
            event_type="trade", salary=p.salary, contract_year=p.contract_year,
            notes=f"Trade: {team_a_name} -> {team_b_name}"))

    for p in players_b:
        if p.team_id != team_b.id:
            return jsonify({"error": f"{p.name} não pertence a {team_b_name}"}), 400
        p.team_id = team_a.id
        p.fantasy_team = team_a.name
        p.is_my_team = team_a.is_my_team
        p.via_trade = True
        desc_parts.append(f"{p.name} ({team_b_name}→{team_a_name})")
        db.session.add(PlayerHistory(
            player_id=p.id, season=season, team_name=team_a.name,
            event_type="trade", salary=p.salary, contract_year=p.contract_year,
            notes=f"Trade: {team_b_name} -> {team_a_name}"))

    for pk in picks_a:
        pk.current_team_id = team_b.id
        pk.current_team_name = team_b.name
        pk.traded_away = True
        desc_parts.append(f"Pick {pk.season} Rd{pk.round} ({team_a_name}→{team_b_name})")

    for pk in picks_b:
        pk.current_team_id = team_a.id
        pk.current_team_name = team_a.name
        pk.traded_away = True
        desc_parts.append(f"Pick {pk.season} Rd{pk.round} ({team_b_name}→{team_a_name})")

    trade = Trade(
        team_a=team_a_name,
        team_b=team_b_name,
        description="; ".join(desc_parts),
        trade_date=datetime.utcnow(),
    )
    db.session.add(trade)
    db.session.commit()
    return jsonify({"success": True, "trade_id": trade.id, "description": trade.description})


@trades_bp.route("/api/trades")
def list_trades():
    trades = Trade.query.order_by(Trade.created_at.desc()).limit(50).all()
    return jsonify([t.to_dict() for t in trades])


@trades_bp.route("/api/trades/<int:tid>", methods=["DELETE"])
def delete_trade(tid):
    trade = db.get_or_404(Trade, tid)
    db.session.delete(trade)
    db.session.commit()
    return jsonify({"success": True})


def _fetch_players(ids: list) -> list:
    return [p for pid in ids if (p := Player.query.get(pid))]


def _fetch_picks(ids: list) -> list:
    return [p for pid in ids if (p := Pick.query.get(pid))]
