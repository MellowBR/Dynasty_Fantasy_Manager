from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
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
    # UX4: enrich cada player com dynasty_value + acquisition_label pré-resolvidos.
    # Mesmo padrão de UX1 em routes/league.py (team_detail).
    from dynasty_values import get_dynasty_values, resolve_asset_value
    dv_map = get_dynasty_values().get("values", {})
    for p in all_players:
        p.dynasty_value = resolve_asset_value(dv_map, p.sleeper_player_id)
        p.acquisition_label = _ACQ_LABELS.get(p.acquisition_type, p.acquisition_type or "—")
    active_players = [p for p in all_players if not p.is_on_ir]
    ir_players = [p for p in all_players if p.is_on_ir]
    players_by_pos = _build_players_by_pos(all_players)

    total_cap = sum(p.salary for p in active_players)
    ir_cap = sum(p.salary for p in ir_players)
    cap_pct = round((total_cap / SALARY_CAP) * 100, 1)

    # M1: cap overrun for the user's OWN team (independent of `?team=` viewing).
    # Banner em roster.html é gated por g_offseason_mode (context processor).
    # Threshold estritamente acima do cap; sub-cap = silêncio.
    own_cap_overrun = 0
    if current_user.is_authenticated and current_user.team_rel:
        own_active = current_user.team_rel.active_salary()
        if own_active > SALARY_CAP:
            own_cap_overrun = round(own_active - SALARY_CAP, 2)

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
        "own_cap_overrun": own_cap_overrun,
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


_DRAFT_RP_RE = __import__("re").compile(r"r(\d+)p(\d+)")


def _summarize_trade_description(description: str, max_chars: int = 100) -> str:
    """Trim a Trade.description string at ';' boundaries to fit max_chars."""
    if not description:
        return ""
    parts = [p.strip() for p in description.split(";") if p.strip()]
    out = []
    total = 0
    for part in parts:
        # total + part + ", " separator
        if out and total + 2 + len(part) > max_chars:
            out.append("…")
            break
        if out:
            total += 2
        out.append(part)
        total += len(part)
    return ", ".join(out) if out else description[:max_chars]


def _format_event_display(h, trade_by_tx: dict) -> str:
    """
    Build a human-readable PT-BR label for a PlayerHistory event.
    Falls back to h.notes for unknown event_types.
    """
    et = h.event_type
    ref = h.sleeper_event_ref or ""
    notes = h.notes or ""
    salary = int(h.salary) if h.salary else 0

    if et in ("auction_draft", "fa_auction", "rookie_draft"):
        m = _DRAFT_RP_RE.search(notes)
        rd, pk = (m.group(1), m.group(2)) if m else ("?", "?")
        prefix = {
            "auction_draft": "Startup Auction",
            "fa_auction": "FA Auction",
            "rookie_draft": "Rookie Draft",
        }[et]
        if et == "rookie_draft":
            return f"{prefix} · Rd {rd}, Pick {pk}"
        return f"{prefix} · Rd {rd}, Pick {pk} · ${salary}"

    if et == "fa_waiver":
        return "Waiver Add"
    if et == "free_agent":
        return "Free Agent Add"
    if et == "commissioner":
        return "Ajuste do comissário"
    if et == "drop":
        return f"Dropado por {h.team_name}" if h.team_name else "Dropado"
    if et == "rollover":
        yr = h.contract_year or "?"
        return f"Valorização (Ano {yr})"

    if et == "trade":
        # Look up Trade row via tx: prefix in sleeper_event_ref
        tx_id = ref[3:] if ref.startswith("tx:") else None
        trade = trade_by_tx.get(tx_id) if tx_id else None
        if not trade:
            return "Trade"
        # Determine counterparty: whichever side of Trade.team_a/team_b is not h.team_name
        if trade.team_a == h.team_name:
            counterparty = trade.team_b
        elif trade.team_b == h.team_name:
            counterparty = trade.team_a
        else:
            # h.team_name could be the destination but trade row stores the trade from
            # a different perspective — show both sides
            counterparty = f"{trade.team_a} ↔ {trade.team_b}"
        desc_short = _summarize_trade_description(trade.description or "", max_chars=110)
        if desc_short:
            return f"Trade com {counterparty} · {desc_short}"
        return f"Trade com {counterparty}"

    if et == "salary_correction":
        return notes or "Correção manual"
    if et == "keeper":
        return "Mantido como keeper"

    return notes or et


@roster_bp.route("/api/player/<int:player_id>/history")
@login_required
def player_history(player_id):
    """
    Ordenação cronológica por (season ASC, rollover-last, Sleeper-id-numérico ASC).

    Sleeper IDs (tx_id, draft_id) são monotonic global, então extraí-los do
    sleeper_event_ref reflete a cronologia real — mais robusto que PlayerHistory.id
    (que depende de quando cada row foi inserida, não quando o evento ocorreu).

    Rollover fica no final de cada season (bordadura de fechamento).

    Cada evento recebe um campo `display_notes` formatado em PT-BR via
    _format_event_display (consulta Trade table para eventos de trade).
    """
    from models import PlayerHistory, Trade
    history = PlayerHistory.query.filter_by(player_id=player_id).all()

    # Prefetch Trade rows relevantes (tx_ids presentes no histórico do player)
    tx_ids = set()
    for h in history:
        if h.event_type == "trade" and h.sleeper_event_ref and h.sleeper_event_ref.startswith("tx:"):
            tx_ids.add(h.sleeper_event_ref[3:])
    trade_by_tx = {}
    if tx_ids:
        for t in Trade.query.filter(Trade.sleeper_transaction_id.in_(tx_ids)).all():
            trade_by_tx[t.sleeper_transaction_id] = t

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

    payload = []
    for h in history:
        d = h.to_dict()
        d["display_notes"] = _format_event_display(h, trade_by_tx)
        payload.append(d)

    return jsonify({
        "player": player.to_dict(),
        "history": payload,
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


# ── M13: Player detail page ──────────────────────────────────────────────────

# PT-BR labels for acquisition_type (reused from salary_history EVENT_LABELS convention)
_ACQ_LABELS = {
    "auction_draft": "Startup Auction",
    "rookie_draft": "Rookie Draft",
    "fa_auction": "FA Auction",
    "fa_waiver": "Waiver / Free Agent",
    "free_agent": "Free Agent",
    "waiver": "Waiver",
    "trade": "Trade",
    "keeper": "Mantido como keeper",
    "unknown": "Origem não registrada",
    "commissioner": "Ajuste do comissário",
}


@roster_bp.route("/player/<int:player_id>")
@login_required
def player_detail(player_id):
    """
    M13 — Página dedicada por jogador: header + contrato + timeline +
    botão 'Propor Trade' (só se current_user tem time vinculado e o jogador
    é de outro time). Dynasty value resolvido no backend (E3) para evitar
    flash visual.
    """
    player = db.session.get(Player, player_id)
    if not player:
        abort(404)

    team = player.team_rel  # pode ser None

    my_team_name = (current_user.team_rel.name
                    if current_user.is_authenticated and current_user.team_rel
                    else None)

    # E3: dynasty_value via backend (página única, sem necessidade de fetch JS)
    dynasty_value = None
    try:
        from dynasty_values import get_dynasty_values
        values_map = get_dynasty_values().get("values") or {}
        if player.sleeper_player_id:
            entry = values_map.get(player.sleeper_player_id)
            if entry:
                dynasty_value = entry.get("value")
    except Exception:
        dynasty_value = None  # fallback silencioso se cache/API indisponível

    can_propose_trade = (
        my_team_name is not None
        and team is not None
        and player.team_id != current_user.team_id
    )

    acquisition_label = _ACQ_LABELS.get(player.acquisition_type, player.acquisition_type or "—")

    return render_template("player_detail.html",
                           player=player,
                           team=team,
                           my_team_name=my_team_name,
                           dynasty_value=dynasty_value,
                           can_propose_trade=can_propose_trade,
                           acquisition_label=acquisition_label)
