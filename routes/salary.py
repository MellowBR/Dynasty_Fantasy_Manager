from types import SimpleNamespace

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from timeutil import utc_iso
from models import db, Player, Team, PlayerHistory, SALARY_CAP, MAX_ROSTER, sort_players_by_pos
from salary_engine import (
    full_contract_table, project_next_salary, draft_budget
)
from routes.auth import admin_required

salary_bp = Blueprint("salary", __name__)


# ── L3: composição ÚNICA "salário-base → roster sintético → draft_budget" ─────
def compose_budget(players, projected=True, extra_salaries=()):
    """Budget de um elenco sobre a BASE SALARIAL escolhida — fonte única (L3).

    Era a composição inline do POST `/budget` do cap projector: montar um roster
    sintético com o salário-base de cada jogador e entregá-lo ao `draft_budget`.
    Virou helper nomeado quando a `/league` e o `/team/<id>` passaram a exibir o cap
    PROJETADO (L3, 13/08/2026) — sem isso a mesma composição existiria em dois
    lugares, que é exatamente a réplica que o [[F10]] eliminou do JS.

    - `projected=True` (default): salário-base = `project_next_salary` — a projeção
      da próxima season (mesma fonte da coluna PROJ do roster, T4 do [[OFF26-20]],
      e do rollover real).
    - `projected=False`: salário-base = `p.salary` CORRENTE. É o modo D9 do
      [[OFF26-1]] (pós-rollover o salário armazenado já está valorizado; re-projetar
      duplicaria) e a régua do **Bid Máximo** da `/league` e da keeper sheet.
    - `extra_salaries`: salários que ocupam spot sem ser Player do roster — hoje só
      os rookies do cenário do board DP2.

    ⛔ Nenhuma aritmética de cap aqui: quem soma, conta vagas e reserva o $1 por vaga
    segue sendo `salary_engine.draft_budget` (fonte única, [[OFF26-18]]).
    """
    base = project_next_salary if projected else (lambda p: p.salary)
    roster = [SimpleNamespace(salary=base(p), is_dropped=False)
              for p in players if not getattr(p, "is_dropped", False)]
    roster += [SimpleNamespace(salary=s, is_dropped=False) for s in extra_salaries]
    return draft_budget(roster)


@salary_bp.route("/salary")
@login_required
def salary_page():
    return render_template("salary.html")


def _planning_ctx():
    """UX23 — (target_season, mode) do projector. `mode` é rótulo de exibição derivado
    do helper único: 'corrente' quando o alvo É a season atual (pós-rollover, auction
    pendente — base D9), 'projetado' caso contrário. ⛔ Nenhuma derivação `+ 1` aqui."""
    from models import planning_target_season, get_current_season
    target = planning_target_season()
    return target, ("corrente" if target == get_current_season() else "projetado")


@salary_bp.route("/cap_projector")
@login_required
def cap_projector_page():
    teams = Team.query.order_by(Team.name).all()
    # M17: pré-seleção deriva do usuário logado (não mais da flag legada is_my_team).
    # Usuário sem time vinculado → "" (nenhuma opção pré-selecionada).
    my_team = current_user.team_rel
    target_season, mode = _planning_ctx()   # UX23: títulos e JS recebem do servidor
    return render_template("cap_projector.html",
                           teams=[t.name for t in teams],
                           my_team=my_team.name if my_team else "",
                           target_season=target_season, mode=mode)


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
    from models import get_current_season, EspnValueStore
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    players = sort_players_by_pos(
        Player.query.filter_by(team_id=team.id, is_dropped=False).all()
    )

    # E4-c-1: badge PROV lê a marca provisório/definitivo do STORE canônico (por
    # sleeper_id). UX23: a season-alvo vem do helper de FASE (era `atual+1` fixo —
    # pós-rollover isso apontava para a season seguinte no meio da janela da auction).
    target_season, mode = _planning_ctx()
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

    # ESPN import status — OFF26-25: mesma LEITURA que o gate do rollover e o preview
    # usam (`latest_espn_import`); esta consulta inline era byte a byte a mesma coisa.
    from models import latest_espn_import
    last_import = latest_espn_import(target_season)
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
        # UX23: o cliente rotula colunas/título por aqui — nenhuma derivação no JS.
        "target_season": target_season,
        "mode": mode,
    })


@salary_bp.route("/api/cap_projector/<path:team_name>/budget", methods=["POST"])
@login_required
def cap_projector_budget(team_name):
    """
    F10 + DP2 — budget do cenário de planejamento (keep/corte + rookies do cenário)
    calculado no BACKEND, fonte ÚNICA `draft_budget`. Body:
    `{"kept_ids": [id, ...], "rookie_sids": ["sid", ...]}`.

    Cadeia única de planejamento (DP2): cada jogador MANTIDO entra com o salário
    PROJETADO da próxima season (`project_next_salary` — mesma fonte da coluna de
    próximo salário do GET); cortados ficam fora. Cada rookie do cenário entra como
    membro de roster adicional com `year1_salary` (modo rookie) — ocupa spot e custa
    salário, exatamente como um pick real. Projeção pura — nada é escrito.

    Antes (DP1-F2) o board simulava sobre o roster integral com salário ATUAL via
    `/simulate`; o DP2 funde os dois caminhos aqui (base = cenário keep/corte do
    summary), eliminando a 2ª fonte de cálculo. `cap_pct`/`shortfall`/`scenario_*` são
    derivados de display do retorno do helper — o cliente não faz nenhuma aritmética.

    OFF26-1 (D9) — AMPLIAÇÃO DELIBERADA, não réplica: `projected` (default True)
    seleciona a BASE DE SALÁRIO do mantido. `true` = `project_next_salary` (default
    intocado p/ o cap_projector). `false` = salário CORRENTE (`p.salary`) — usado pela
    janela de cortes selada, que roda PÓS-rollover (salário já valorizado); re-projetar
    duplicaria. A FONTE DE CÁLCULO segue única (`draft_budget`); muda só qual salário
    alimenta o helper — não há aritmética nova nem 2ª rota (invariante F10 preservada).

    L3 (13/08/2026): a composição (base salarial → roster sintético → `draft_budget`)
    saiu daqui para o helper `compose_budget`, consumido também pela `/league` e pelo
    `/team/<id>`. Refactor puro — o payload deste endpoint não mudou.
    """
    from models import get_current_season, rookie_espn_adjusted
    from salary_engine import year1_salary
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    data = request.get_json() or {}
    # D9: modo de base salarial — projetado (default) vs. corrente (já rollado)
    projected = data.get("projected", True)
    kept_ids = set()
    for i in (data.get("kept_ids") or []):
        try:
            kept_ids.add(int(i))
        except (TypeError, ValueError):
            continue

    players = Player.query.filter_by(team_id=team.id, is_dropped=False).all()
    kept = [p for p in players if p.id in kept_ids]

    # DP2: rookies do cenário entram na MESMA base (ocupam spot + custam year1_salary).
    # Dedup defensivo; sid fora do store da season é ignorado. Mesma régua de cálculo
    # do board DP1 antigo (year1_salary modo rookie) — caso de referência $46→$55 / $3→$3.
    # UX23: season do helper de fase — com `atual+1` fixo, pós-rollover o sid não achava
    # o store (só tem a season corrente) e o rookie do cenário era IGNORADO EM SILÊNCIO.
    from models import planning_target_season
    season = planning_target_season()
    scenario = []
    seen = set()
    for sid in (data.get("rookie_sids") or []):
        sid = str(sid)
        if sid in seen:
            continue
        seen.add(sid)
        adj = rookie_espn_adjusted(sid, season)
        if adj is None:
            continue
        sal = year1_salary("rookie_draft", 0, adj)
        scenario.append({"sleeper_player_id": sid, "projected_salary": sal})

    budget = compose_budget(kept, projected=projected,
                            extra_salaries=[r["projected_salary"] for r in scenario])

    return jsonify({
        "team": team.name,
        "budget": budget,
        "cap_pct": min(100.0, budget["keeper_salaries"] / budget["salary_cap"] * 100.0),
        "shortfall": max(0, -budget["usable_draft_budget"]),
        "scenario_count": len(scenario),
        "scenario_salary_total": sum(r["projected_salary"] for r in scenario),
    })


# ── DP1: board de planejamento de cap pré-draft (rookies) ─────────────────────

@salary_bp.route("/api/cap_projector/rookies")
@login_required
def cap_projector_rookies():
    """
    DP1 + DP3 — lista a CLASSE ENTRANTE da season-alvo (get_current_season()+1) com o
    valor ESPN de referência (raw) e o salário projetado (floor(ESPN×1.2)).

    DP3 (snapshot materializado): a membership vem de RookieEspnValue.in_class=True,
    escrita pela captura admin (critério único is_entering_class_member — o endpoint
    NÃO reavalia classe, só lê o snapshot). Rookies JÁ ROSTERADOS (draftados →
    materializados como Player via record_acquisition) saem do board — sob a cadeia
    keep/corte do DP2 eles entram pelo roster, e listá-los aqui seria dupla contagem.
    Sem valor ESPN (fora do Top-300) → espn_adjusted=0 → year1_salary devolve $1
    (regra da liga, D2) — a MESMA fonte única do import de draft, sem réplica.
    Leitura pura: 2 queries indexadas, nada é escrito.
    """
    from models import planning_target_season, RookieEspnValue, Player
    from salary_engine import year1_salary
    # UX23: season do helper de fase — com `atual+1` fixo, pós-rollover o board pedia a
    # classe de uma season que o store não tem e vinha VAZIO no meio da janela da auction.
    season = planning_target_season()
    rostered_sids = (db.session.query(Player.sleeper_player_id)
                     .filter(Player.is_dropped == False,           # noqa: E712
                             Player.sleeper_player_id.isnot(None)))
    rows = (RookieEspnValue.query
            .filter(RookieEspnValue.season == season,
                    RookieEspnValue.in_class == True,              # noqa: E712
                    ~RookieEspnValue.sleeper_player_id.in_(rostered_sids))
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


# DP2: o antigo POST /api/cap_projector/simulate foi REMOVIDO — sua conta (rookies do
# cenário somados ao budget) foi fundida no /budget acima (base = cenário keep/corte,
# não mais roster integral com salário atual). Fonte única de cálculo, sem segunda rota.


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
