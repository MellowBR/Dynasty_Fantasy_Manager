from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from timeutil import utc_iso
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
    # M17: pré-seleção deriva do usuário logado (não mais da flag legada is_my_team).
    # Usuário sem time vinculado → "" (nenhuma opção pré-selecionada).
    my_team = current_user.team_rel
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
    from models import ESPNImportLog, get_current_season, EspnValueStore
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    players = sort_players_by_pos(
        Player.query.filter_by(team_id=team.id, is_dropped=False).all()
    )

    # E4-c-1: badge PROV lê a marca provisório/definitivo do STORE canônico (por
    # sleeper_id), não mais do ESPNValue (por player_id). Mesma season-alvo (atual+1).
    target_season = get_current_season() + 1
    store_vals = {r.sleeper_player_id: r for r in
                  EspnValueStore.query.filter_by(season=target_season).all()}

    player_data = []
    for p in players:
        sv = store_vals.get(p.sleeper_player_id)
        player_data.append({
            **p.to_dict(),
            "next_salary": project_next_salary(p),
            "espn_is_final": sv.is_final if sv else None,
            "espn_season": sv.season if sv else None,
        })

    budget = draft_budget(players)

    # ESPN import status
    last_import = ESPNImportLog.query.filter_by(season=target_season)\
        .order_by(ESPNImportLog.imported_at.desc()).first()
    espn_status = None
    if last_import:
        espn_status = {
            "status": last_import.status,
            "date": utc_iso(last_import.imported_at),  # M18: ISO 'Z' → formatLocalDT no cliente
            "season": last_import.season,
        }

    return jsonify({
        "team": team.to_dict(),
        "players": player_data,
        "budget": budget,
        "salary_cap": SALARY_CAP,
        "espn_status": espn_status,
    })


@salary_bp.route("/api/cap_projector/<path:team_name>/budget", methods=["POST"])
@login_required
def cap_projector_budget(team_name):
    """
    F10 — budget do cenário keep/corte do summary calculado no BACKEND (fonte única
    `draft_budget`; fim da réplica JS do `updateSummary`). Body: {"kept_ids": [id, ...]}.

    Cada jogador MANTIDO entra com o salário PROJETADO da próxima season
    (`project_next_salary` — mesma fonte da coluna de próximo salário do GET);
    cortados ficam fora do roster simulado. Projeção pura — nada é escrito.
    `cap_pct`/`shortfall` são derivados de display do próprio retorno do helper,
    expostos aqui para o cliente não fazer nenhuma aritmética de budget.
    """
    from types import SimpleNamespace
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    data = request.get_json() or {}
    kept_ids = set()
    for i in (data.get("kept_ids") or []):
        try:
            kept_ids.add(int(i))
        except (TypeError, ValueError):
            continue

    players = Player.query.filter_by(team_id=team.id, is_dropped=False).all()
    kept = [SimpleNamespace(salary=project_next_salary(p), is_dropped=False)
            for p in players if p.id in kept_ids]
    budget = draft_budget(kept)

    return jsonify({
        "team": team.name,
        "budget": budget,
        "cap_pct": min(100.0, budget["keeper_salaries"] / budget["salary_cap"] * 100.0),
        "shortfall": max(0, -budget["usable_draft_budget"]),
    })


# ── DP1: board de planejamento de cap pré-draft (rookies) ─────────────────────

@salary_bp.route("/api/cap_projector/rookies")
@login_required
def cap_projector_rookies():
    """
    DP1 — lista os rookies entrantes da season-alvo (get_current_season()+1) com o
    valor ESPN de referência (raw) e o salário projetado (floor(ESPN×1.2)).

    Fonte = RookieEspnValue (store dos NÃO-rosterados), NÃO o store canônico
    (espn_value_store): o backfill do canônico veio de `SELECT FROM players`, logo só
    contém rosterados — ler o canônico aqui devolveria board vazio de entrantes
    (F1/MAN-DP1; E4-c-2 não é pré-requisito). O salário vem da fonte única
    `salary_engine.year1_salary` (modo rookie), sem row de Player e sem réplica do
    cálculo (mesma invocação que o import de draft em draft_import.py).
    """
    from models import get_current_season, RookieEspnValue
    from salary_engine import year1_salary
    season = get_current_season() + 1
    rows = (RookieEspnValue.query
            .filter_by(season=season)
            .order_by(RookieEspnValue.espn_adjusted.desc(), RookieEspnValue.name.asc())
            .all())
    rookies = [{
        "sleeper_player_id": r.sleeper_player_id,
        "name": r.name,
        "position": r.position,
        "nfl_team": r.nfl_team or "—",
        "espn_ref_value": r.espn_raw,                 # raw (ex.: $46) — referência exibida
        "espn_adjusted": r.espn_adjusted,             # raw×1.2 (base do floor)
        "projected_salary": year1_salary("rookie_draft", 0, r.espn_adjusted),
    } for r in rows]
    return jsonify({"season": season, "rookies": rookies})


@salary_bp.route("/api/cap_projector/simulate", methods=["POST"])
@login_required
def cap_projector_simulate():
    """
    DP1 — simulação de cenário multi-pick calculada PURAMENTE no backend (não consome
    nem amplia a réplica JS de budget do `updateSummary` — débito F10).

    Projeção, não contrato: nada é escrito (nem Player, nem SalaryHistory, nem cenário).
    Budget = `draft_budget()` canônico sobre o cap ATUAL do time do `current_user` (M17)
    somado aos salários projetados (`year1_salary` modo rookie) dos rookies do cenário.
    Os rookies entram como "+salário" via objeto transitório em memória (NÃO materializa
    Player — stub-$1 segue rejeitado, E2-REFINE). Cenário vazio → budget atual do time,
    idêntico ao `/api/cap_projector` (sem alteração).
    """
    from types import SimpleNamespace
    from models import get_current_season, rookie_espn_adjusted
    from salary_engine import year1_salary
    data = request.get_json() or {}
    sids = [str(s) for s in (data.get("rookie_sids") or [])]
    season = get_current_season() + 1

    team = current_user.team_rel
    if not team:
        return jsonify({"error": "Usuário sem time vinculado — vincule um time para simular."}), 400

    # Base = roster ativo do owner com o salário ATUAL (mesma base do /api/cap_projector).
    roster = list(Player.query.filter_by(team_id=team.id, is_dropped=False).all())

    scenario = []
    seen = set()
    for sid in sids:
        if sid in seen:
            continue                       # dedup defensivo do cenário
        seen.add(sid)
        adj = rookie_espn_adjusted(sid, season)
        if adj is None:
            continue                       # sid fora do store da season → ignora
        sal = year1_salary("rookie_draft", 0, adj)
        roster.append(SimpleNamespace(salary=sal, is_dropped=False))
        scenario.append({"sleeper_player_id": sid, "projected_salary": sal})

    budget = draft_budget(roster)
    return jsonify({
        "team": team.name,
        "scenario": scenario,
        "scenario_count": len(scenario),
        "scenario_salary_total": sum(r["projected_salary"] for r in scenario),
        "budget": budget,
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
            "sleeper_player_id": p.sleeper_player_id,
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
    from models import ESPNValue, get_current_season, set_espn_value
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

        # E4-c-1: valor via fonte única (store canônico season+1 + materializa a coluna).
        set_espn_value(player, get_current_season() + 1, espn_raw * 1.2, raw=espn_raw)
        # Log legado em ESPNValue (sem leitor após o repontamento da badge; removido no E4-c-2)
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
