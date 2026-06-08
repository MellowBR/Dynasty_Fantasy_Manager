import json
import re
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user

from models import db, Player, Pick, Trade, Team, TradeProposal, SALARY_CAP, get_current_season
from routes.auth import admin_required
from dynasty_values import (
    get_dynasty_values, pick_sleeper_id, resolve_asset_value,
    resolve_asset_redraft_value, CACHE_TTL_HOURS,
)

trades_bp = Blueprint("trades", __name__)

PROPOSAL_TTL_DAYS = 7

# T3-FIX-UX-4: parse Trade.description into structured "de/para" view
# Description format from sync_sleeper.py: "Player (TeamFrom→TeamTo); Player (TeamFrom→TeamTo); ..."
# N-way prefixed with "[N-WAY] " — esses retornam None pra cair no render raw.
_DESC_TOKEN_RE = re.compile(r"^(.+?)\s*\(\s*(.+?)\s*→\s*(.+?)\s*\)\s*$")


def _parse_trade_description(desc: str | None, team_a: str, team_b: str) -> dict | None:
    """Quebra a descrição da trade em duas listas por direção do envio.

    Returns: {a_to_b: [str], b_to_a: [str], unparsed: [str]}.
    Returns None se descrição vazia, [N-WAY], ou nenhum token parseável.
    """
    if not desc or desc.startswith("[N-WAY]"):
        return None
    parts = [p.strip() for p in desc.split(";") if p.strip()]
    a_to_b, b_to_a, unparsed = [], [], []
    for p in parts:
        m = _DESC_TOKEN_RE.match(p)
        if not m:
            unparsed.append(p)
            continue
        asset, from_t, to_t = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if from_t == team_a and to_t == team_b:
            a_to_b.append(asset)
        elif from_t == team_b and to_t == team_a:
            b_to_a.append(asset)
        else:
            unparsed.append(p)
    if not (a_to_b or b_to_a):
        return None
    return {"a_to_b": a_to_b, "b_to_a": b_to_a, "unparsed": unparsed}


@trades_bp.route("/trades")
@login_required
def trades_page():
    teams = Team.query.order_by(Team.name).all()
    recent = Trade.query.order_by(Trade.created_at.desc()).limit(30).all()
    owner_map = {t.name: t.owner_name or "" for t in teams}
    avatar_map = {t.name: t.owner_avatar or "" for t in teams}

    # T3-FIX-UX-4: enriquece cada trade com `flow` (parse estruturado da descrição)
    # pra render em 2 colunas "de/para" no template. Se None (N-way ou unparseable),
    # template cai no render raw da descrição.
    for t in recent:
        t.flow = _parse_trade_description(t.description, t.team_a, t.team_b)

    # M14: aceita ?team_a=<nome>&team_b=<nome> para pré-selecionar os selects.
    # Valida contra a lista de teams; se não bater, ignora silenciosamente.
    team_names = {t.name for t in teams}
    preset_a = request.args.get("team_a") if request.args.get("team_a") in team_names else None
    preset_b = request.args.get("team_b") if request.args.get("team_b") in team_names else None

    # M9-FIX: aceita ?pick_a=<id>&pick_b=<id> para pré-marcar checkbox de pick.
    # Valida que pick existe E pertence ao team preset correspondente
    # (pick_a → current_team_name == preset_a, idem pick_b).
    # Ignora silenciosamente se inválido.
    def _resolve_preset_pick(arg_name, team_name):
        pid_raw = request.args.get(arg_name)
        if not pid_raw or not team_name:
            return None
        try:
            pid = int(pid_raw)
        except (ValueError, TypeError):
            return None
        pick = Pick.query.get(pid)
        if pick and pick.current_team_name == team_name:
            return pid
        return None

    preset_pick_a = _resolve_preset_pick("pick_a", preset_a)
    preset_pick_b = _resolve_preset_pick("pick_b", preset_b)

    return render_template("trades.html",
                           teams=teams,
                           recent_trades=recent,
                           owner_map=owner_map,
                           avatar_map=avatar_map,
                           preset_team_a=preset_a,
                           preset_team_b=preset_b,
                           preset_pick_a=preset_pick_a,
                           preset_pick_b=preset_pick_b)


# ── API ──────────────────────────────────────────────────────────────────────

def _player_asset_dict(player, values_map):
    """Player.to_dict() + dynasty_value + redraft_value via sleeper_player_id (T3)."""
    d = player.to_dict()
    d["dynasty_value"] = resolve_asset_value(values_map, player.sleeper_player_id)
    d["redraft_value"] = resolve_asset_redraft_value(values_map, player.sleeper_player_id)
    return d


def _pick_asset_dict(pick, values_map, current_season):
    """Pick.to_dict() + dynasty_value via DP_<year_offset>_<pick_index> (T3: redraft sempre 0)."""
    d = pick.to_dict()
    fc_sid = pick_sleeper_id(pick, current_season)
    d["fc_sleeper_id"] = fc_sid
    d["dynasty_value"] = resolve_asset_value(values_map, fc_sid)
    # T3: picks têm redraft=0 por construção (puro futuro). Mantém o key explícito
    # pra simetria com player asset; UI agrega 0 e barra redraft não recebe contribuição.
    d["redraft_value"] = 0
    # Marca picks sem projected_pick como estimativa (valor do middle-of-round)
    d["dynasty_value_is_estimate"] = not getattr(pick, "projected_pick", None)
    return d


def _sum_values(assets):
    return sum((a.get("dynasty_value") or 0) for a in assets)


def _sum_redraft_values(assets):
    """T3: agregação paralela de redraft_value para a barra redraft.

    Picks contribuem 0 (já no payload). Players sem cobertura redraft contribuem 0.
    """
    return sum((a.get("redraft_value") or 0) for a in assets)


def _compute_cap_impact(team_a, team_b, players_a, players_b, picks_a, picks_b):
    """
    Pure cap + dynasty value calculation — shared between preview endpoint and
    proposal rendering. Picks don't affect cap (salary=0) but carry dynasty_value.
    Returns {team_a: {...}, team_b: {...}, dynasty: {...}} with before/after,
    over_cap, enriched assets and per-side dynasty totals.
    """
    cap_a = team_a.active_salary()
    cap_b = team_b.active_salary()

    sal_a_out = sum(p.salary for p in players_a)
    sal_a_in = sum(p.salary for p in players_b)
    sal_b_out = sum(p.salary for p in players_b)
    sal_b_in = sum(p.salary for p in players_a)

    cap_a_after = cap_a - sal_a_out + sal_a_in
    cap_b_after = cap_b - sal_b_out + sal_b_in

    # Dynasty values — single cache read, client-side-ready payload
    dv_payload = get_dynasty_values()
    values_map = dv_payload.get("values") or {}
    current_season = get_current_season()

    # Enriched asset dicts with dynasty_value fields
    ea_players_out = [_player_asset_dict(p, values_map) for p in players_a]
    ea_players_in = [_player_asset_dict(p, values_map) for p in players_b]
    ea_picks_out = [_pick_asset_dict(pk, values_map, current_season) for pk in picks_a]
    ea_picks_in = [_pick_asset_dict(pk, values_map, current_season) for pk in picks_b]

    eb_players_out = ea_players_in   # invert perspective
    eb_players_in = ea_players_out
    eb_picks_out = ea_picks_in
    eb_picks_in = ea_picks_out

    def dynasty_totals(out_players, in_players, out_picks, in_picks):
        total_out = _sum_values(out_players) + _sum_values(out_picks)
        total_in = _sum_values(in_players) + _sum_values(in_picks)
        return {
            "total_out": total_out,
            "total_in": total_in,
            "delta": total_in - total_out,
        }

    def redraft_totals(out_players, in_players, out_picks, in_picks):
        # T3: paralelo a dynasty_totals. Picks contribuem 0; players sem cobertura redraft contribuem 0.
        total_out = _sum_redraft_values(out_players) + _sum_redraft_values(out_picks)
        total_in = _sum_redraft_values(in_players) + _sum_redraft_values(in_picks)
        return {
            "total_out": total_out,
            "total_in": total_in,
            "delta": total_in - total_out,
        }

    def side(team, cap_before, cap_after, out_players, in_players, out_picks, in_picks):
        d_totals = dynasty_totals(out_players, in_players, out_picks, in_picks)
        r_totals = redraft_totals(out_players, in_players, out_picks, in_picks)
        return {
            "name": team.name,
            "owner_name": team.owner_name or "",
            "owner_avatar": team.owner_avatar or "",
            "cap_before": cap_before,
            "cap_after": round(cap_after, 2),
            "cap_remaining_after": round(SALARY_CAP - cap_after, 2),
            "over_cap": cap_after > SALARY_CAP,
            "players_out": out_players,
            "players_in":  in_players,
            "picks_out": out_picks,
            "picks_in":  in_picks,
            "dynasty_total_out": d_totals["total_out"],
            "dynasty_total_in": d_totals["total_in"],
            "dynasty_delta": d_totals["delta"],
            "redraft_total_out": r_totals["total_out"],
            "redraft_total_in": r_totals["total_in"],
            "redraft_delta": r_totals["delta"],
        }

    return {
        "team_a": side(team_a, cap_a, cap_a_after,
                       ea_players_out, ea_players_in, ea_picks_out, ea_picks_in),
        "team_b": side(team_b, cap_b, cap_b_after,
                       eb_players_out, eb_players_in, eb_picks_out, eb_picks_in),
        "dynasty_available": bool(values_map),
    }


# ── T2: Dynasty values (FantasyCalc) ─────────────────────────────────────────

@trades_bp.route("/api/dynasty_values")
@login_required
def dynasty_values_endpoint():
    """
    Retorna o cache atual (ou tenta fetch se stale). Usado pelo frontend para
    carregar o mapa sid→value uma vez ao abrir /trades.
    """
    payload = get_dynasty_values()
    fetched_at = payload.get("fetched_at")
    age_hours = None
    if fetched_at:
        try:
            dt = datetime.fromisoformat(fetched_at)
            age_hours = round((datetime.utcnow() - dt).total_seconds() / 3600, 2)
        except Exception:
            age_hours = None
    # Simplifica payload: {sid: value} direto (UI não precisa do resto)
    # T3: paralelamente expõe redraft_values map. Consumidores legacy ignoram.
    entries = (payload.get("values") or {}).items()
    simple = {sid: entry.get("value", 0) for sid, entry in entries}
    redraft_simple = {sid: entry.get("redraft_value", 0) for sid, entry in (payload.get("values") or {}).items()}
    return jsonify({
        "values": simple,
        "redraft_values": redraft_simple,
        "fetched_at": fetched_at,
        "age_hours": age_hours,
        "count": payload.get("count", 0),
        "ttl_hours": CACHE_TTL_HOURS,
    })


@trades_bp.route("/api/admin/dynasty_values/refresh", methods=["POST"])
@login_required  # qualquer owner pode atualizar — operação read-only (fetch externo)
def dynasty_values_refresh():
    """Força re-fetch do FantasyCalc ignorando TTL."""
    payload = get_dynasty_values(force_refresh=True)
    return jsonify({
        "count": payload.get("count", 0),
        "fetched_at": payload.get("fetched_at"),
    })


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


@trades_bp.route("/api/trades/by_tx/<tx_id>")
@login_required
def trade_by_tx(tx_id):
    """
    Detalhe de uma Trade pelo sleeper_transaction_id — usado pelo modal clicável
    da timeline de /salary_history. Parseia Trade.description em assets por direção
    (formato: 'Player/Pick (src→dst); ...').
    """
    import re
    trade = Trade.query.filter_by(sleeper_transaction_id=tx_id).first()
    if not trade:
        return jsonify({"error": "Trade não encontrada"}), 404

    # Parse description: "Player (src→dst); Pick 2025 Rd2 (src→dst); ..."
    # Regex captura (asset, src, dst). Aceita '→' ou '->'.
    pattern = re.compile(r"^(.+?)\s*\(([^→]+?)(?:→|->)([^)]+?)\)$")
    assets_by_team = {}  # dst_team → list of assets received from their side
    if trade.description:
        from player_lookup import find_player_by_name
        parts = [p.strip() for p in trade.description.split(";") if p.strip()]
        for part in parts:
            m = pattern.match(part)
            if not m:
                continue
            asset, src, dst = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            # Best-effort: picks e nomes ambíguos retornam None (consumidor faz fallback).
            matched = find_player_by_name(asset)
            assets_by_team.setdefault(dst, []).append({
                "asset": asset,
                "from": src,
                "player_id": matched.id if matched else None,
            })

    return jsonify({
        "sleeper_transaction_id": trade.sleeper_transaction_id,
        "team_a": trade.team_a,
        "team_b": trade.team_b,
        "description": trade.description,
        "trade_date": trade.trade_date.strftime("%d/%m/%Y %H:%M") if trade.trade_date else None,
        "source": trade.source,
        "assets_by_team": assets_by_team,  # dict team_name → [{asset, from}]
    })


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
