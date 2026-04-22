import json
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user

from models import db, Player, Pick, Trade, Team, TradeProposal, SALARY_CAP, MY_TEAM_NAME, get_current_season
from routes.auth import admin_required

trades_bp = Blueprint("trades", __name__)

PROPOSAL_TTL_DAYS = 7


@trades_bp.route("/trades")
@login_required
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

def _compute_cap_impact(team_a, team_b, players_a, players_b, picks_a, picks_b):
    """
    Pure cap impact calculation — shared between preview endpoint and proposal
    rendering. Picks don't affect cap (are future assets, salary=0).
    Returns {team_a: {...}, team_b: {...}} with before/after/over_cap/assets.
    """
    cap_a = team_a.active_salary()
    cap_b = team_b.active_salary()

    sal_a_out = sum(p.salary for p in players_a)
    sal_a_in = sum(p.salary for p in players_b)
    sal_b_out = sum(p.salary for p in players_b)
    sal_b_in = sum(p.salary for p in players_a)

    cap_a_after = cap_a - sal_a_out + sal_a_in
    cap_b_after = cap_b - sal_b_out + sal_b_in

    def side(team, cap_before, cap_after, out_players, in_players, out_picks, in_picks):
        return {
            "name": team.name,
            "owner_name": team.owner_name or "",
            "owner_avatar": team.owner_avatar or "",
            "cap_before": cap_before,
            "cap_after": round(cap_after, 2),
            "cap_remaining_after": round(SALARY_CAP - cap_after, 2),
            "over_cap": cap_after > SALARY_CAP,
            "players_out": [p.to_dict() for p in out_players],
            "players_in":  [p.to_dict() for p in in_players],
            "picks_out": [p.to_dict() for p in out_picks],
            "picks_in":  [p.to_dict() for p in in_picks],
        }

    return {
        "team_a": side(team_a, cap_a, cap_a_after, players_a, players_b, picks_a, picks_b),
        "team_b": side(team_b, cap_b, cap_b_after, players_b, players_a, picks_b, picks_a),
    }


@trades_bp.route("/api/trades/preview", methods=["POST"])
@login_required
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
    picks_a = _fetch_picks(data.get("picks_a", []))
    picks_b = _fetch_picks(data.get("picks_b", []))

    return jsonify(_compute_cap_impact(team_a, team_b, players_a, players_b, picks_a, picks_b))


# ── T1: Shareable proposals ──────────────────────────────────────────────────

@trades_bp.route("/api/trades/proposals", methods=["POST"])
@login_required
def create_trade_proposal():
    """Persiste uma simulação com UUID e TTL de 7 dias. Simulação pura — não
    move nada no DB. A trade real é confirmada pelo Sleeper via S1."""
    data = request.get_json() or {}
    team_a_name = data.get("team_a", "")
    team_b_name = data.get("team_b", "")

    team_a = Team.query.filter_by(name=team_a_name).first()
    team_b = Team.query.filter_by(name=team_b_name).first()
    if not team_a or not team_b:
        return jsonify({"error": "Uma ou ambas as equipes não encontradas"}), 404
    if team_a.id == team_b.id:
        return jsonify({"error": "Selecione dois times diferentes"}), 400

    players_a_ids = list(data.get("players_a", []) or [])
    players_b_ids = list(data.get("players_b", []) or [])
    picks_a_ids = list(data.get("picks_a", []) or [])
    picks_b_ids = list(data.get("picks_b", []) or [])

    total_a = len(players_a_ids) + len(picks_a_ids)
    total_b = len(players_b_ids) + len(picks_b_ids)
    if total_a == 0 or total_b == 0:
        return jsonify({"error": "Selecione pelo menos 1 ativo em cada lado"}), 400

    now = datetime.utcnow()
    proposal = TradeProposal(
        id=str(uuid.uuid4()),
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        players_a=json.dumps(players_a_ids),
        players_b=json.dumps(players_b_ids),
        picks_a=json.dumps(picks_a_ids),
        picks_b=json.dumps(picks_b_ids),
        created_by=current_user.id if current_user.is_authenticated else None,
        created_at=now,
        expires_at=now + timedelta(days=PROPOSAL_TTL_DAYS),
    )
    db.session.add(proposal)
    db.session.commit()

    return jsonify({
        "proposal_id": proposal.id,
        "url": url_for("trades.view_trade_proposal", proposal_id=proposal.id),
        "expires_at": proposal.expires_at.isoformat(),
        "ttl_days": PROPOSAL_TTL_DAYS,
    })


@trades_bp.route("/trades/proposta/<proposal_id>")
@login_required
def view_trade_proposal(proposal_id):
    """Renderiza a proposta read-only. Cap impact recalculado com os salários
    atuais dos players (reflete estado atual do cap, não do momento da criação)."""
    proposal = TradeProposal.query.get(proposal_id)
    if not proposal:
        return render_template("trade_proposal.html",
                               error="Proposta não encontrada."), 404
    if proposal.is_expired():
        return render_template("trade_proposal.html",
                               error="Esta proposta expirou.",
                               expired_at=proposal.expires_at), 410

    team_a = proposal.team_a
    team_b = proposal.team_b
    if not team_a or not team_b:
        return render_template("trade_proposal.html",
                               error="Times da proposta não estão mais disponíveis."), 410

    try:
        players_a = _fetch_players(json.loads(proposal.players_a or "[]"))
        players_b = _fetch_players(json.loads(proposal.players_b or "[]"))
        picks_a = _fetch_picks(json.loads(proposal.picks_a or "[]"))
        picks_b = _fetch_picks(json.loads(proposal.picks_b or "[]"))
    except (ValueError, TypeError):
        return render_template("trade_proposal.html",
                               error="Proposta corrompida."), 500

    impact = _compute_cap_impact(team_a, team_b, players_a, players_b, picks_a, picks_b)
    days_left = (proposal.expires_at - datetime.utcnow()).days

    return render_template("trade_proposal.html",
                           proposal=proposal,
                           impact=impact,
                           creator_name=proposal.creator.name if proposal.creator else None,
                           days_left=max(days_left, 0))


@trades_bp.route("/api/trades")
@login_required
def list_trades():
    trades = Trade.query.order_by(Trade.created_at.desc()).limit(50).all()
    return jsonify([t.to_dict() for t in trades])


@trades_bp.route("/api/trades/<int:tid>", methods=["DELETE"])
@admin_required
def delete_trade(tid):
    trade = db.get_or_404(Trade, tid)
    db.session.delete(trade)
    db.session.commit()
    return jsonify({"success": True})


def _fetch_players(ids: list) -> list:
    return [p for pid in ids if (p := Player.query.get(pid))]


def _fetch_picks(ids: list) -> list:
    return [p for pid in ids if (p := Pick.query.get(pid))]
