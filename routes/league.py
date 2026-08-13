"""League Hub — visão geral da liga + detalhe por time (L1)."""
from collections import defaultdict

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from models import (
    db, Team, Player, Pick, SeasonStandings, ESPNImportLog,
    SALARY_CAP, get_config, get_current_season, sort_players_by_pos,
)
from salary_engine import roster_salary, draft_budget  # OFF26-16 + Bid Máximo (L1-BID)
from routes.salary import compose_budget               # L3: cap projetado (fonte única)
from dynasty_values import get_dynasty_values, resolve_asset_value
from routes.roster import _build_players_by_pos as build_players_by_pos, _ACQ_LABELS

league_bp = Blueprint("league", __name__)


def _projection_open() -> bool:
    """L3 — o cap PROJETADO só faz sentido ANTES do rollover.

    `project_next_salary` projeta sobre o salário ARMAZENADO: pré-rollover isso é a
    season seguinte (a pergunta útil); pós-rollover o armazenado já É o da season nova
    e projetar de novo mostraria season+2 — um número que contradiria o cap corrente
    exibido ao lado. Mesma arbitragem que o D9 do [[OFF26-1]] fez no `/budget`
    (`projected:false` pós-rollover, "re-projetar duplicaria").

    `rollover_done` é flag do ciclo de offseason corrente: some no rollover e volta
    sozinha na intertemporada seguinte, quando o reset da season a zera.
    """
    return get_config("rollover_done", "false") != "true"


def _build_team_card(team, standing, pick_count, players, dv_map, my_team_id=None,
                     show_projection=False):
    """Monta dict do card de um time. Sem queries — tudo já carregado.
    M17: `is_my_team` deriva do usuário logado (my_team_id = current_user.team_rel.id),
    não mais da flag legada Team.is_my_team."""
    # OFF26-16: folha única (IR incluído) via fonte única. `players` já vem filtrado
    # por `is_dropped=False`. NOTA: o `dynasty_total` abaixo segue excluindo IR — é
    # valor de ativo, não folha salarial, e está fora do escopo desta decisão.
    cap_used = roster_salary(players)
    dynasty_total = sum(
        resolve_asset_value(dv_map, p.sleeper_player_id) or 0
        for p in players if not p.is_on_ir
    )
    # L1-BID (07/08/2026): "Bid Máximo" = `usable_draft_budget` da FONTE ÚNICA
    # `draft_budget`, com base salarial CORRENTE (equivale ao `projected:false` da porta
    # e é a mesma régua da keeper sheet). Nenhuma aritmética de cap nova aqui.
    bid_max = int(draft_budget(players)["usable_draft_budget"])
    # L3: cap PROJETADO da season seguinte — MESMA composição do cap projector
    # (`compose_budget`, base `project_next_salary`). Zero query: opera sobre os
    # `players` que o render já carregou numa consulta só.
    # ⛔ O `bid_max` acima NÃO muda de base: é corrente de propósito (é o número que a
    # keeper sheet publica como Bid Máximo — trocá-lo por projeção quebraria a
    # coerência tela × sheet).
    proj = compose_budget(players) if show_projection else None
    return {
        "id": team.id,
        "name": team.name,
        "owner_name": team.owner_name or "",
        "owner_avatar": team.owner_avatar or "",
        "is_my_team": team.id == my_team_id,
        "cap_used": cap_used,
        "cap_space": SALARY_CAP - cap_used,
        "proj_used": proj["keeper_salaries"] if proj else None,
        "proj_space": (SALARY_CAP - proj["keeper_salaries"]) if proj else None,
        "proj_over_cap": bool(proj["over_cap"]) if proj else False,
        "bid_max": bid_max,
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
    show_projection = _projection_open()
    cards = [
        _build_team_card(
            t, standings.get(t.id), pick_counts.get(t.id, 0),
            players_by_team.get(t.id, []), dv_map, my_team_id, show_projection,
        )
        for t in teams
    ]
    cards.sort(key=lambda c: (c["rank"], c["name"]))

    # L1-BID: selo PROV no Bid Máximo enquanto a tabela ESPN DEFINITIVA não entrar
    # (mesmo padrão do Cap Projector, mas em régua de LIGA: o gate é o import marcado
    # `final` para a season-alvo, não o `is_final` de cada jogador). Sai em 18/08.
    # L3: o mesmo selo cobre o cap projetado — projeção e Bid Máximo dependem da
    # MESMA tabela ESPN, e com a provisória (valores ≈1.0) a projeção colapsa para
    # perto do salário corrente. Um único gate, nenhuma segunda definição de "PROV".
    espn_final = ESPNImportLog.query.filter_by(
        season=season + 1, status="final").first() is not None

    return render_template("league.html", cards=cards, season=season,
                           cap=SALARY_CAP, show_projection=show_projection,
                           proj_season=season + 1,
                           bid_provisional=not espn_final)


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

    # OFF26-16: `active`/`ir` seguem existindo para COMPOSIÇÃO de elenco (contagem e
    # lista de quem está no IR) — não para folha. A folha é uma só e inclui o IR.
    active = [p for p in players if not p.is_on_ir]
    ir = [p for p in players if p.is_on_ir]
    cap_used = roster_salary(players)

    # OFF26-16: a quebra por posição percorre TODOS os jogadores — antes somava só os
    # não-IR e por isso não fechava com o `cap_used` exibido na mesma tela.
    cap_by_pos = defaultdict(float)
    for p in players:
        cap_by_pos[p.position or "OTHER"] += p.salary

    # L3: cap projetado no breakdown — mesma fonte e mesmo gate da /league.
    show_projection = _projection_open()
    proj = compose_budget(players) if show_projection else None
    espn_final = ESPNImportLog.query.filter_by(
        season=season + 1, status="final").first() is not None

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
        "show_projection": show_projection,
        "proj_season": season + 1,
        "proj_cap_used": proj["keeper_salaries"] if proj else None,
        "proj_cap_remaining": (SALARY_CAP - proj["keeper_salaries"]) if proj else None,
        "proj_over_cap": bool(proj["over_cap"]) if proj else False,
        "bid_provisional": not espn_final,
        "ir_count": len(ir),
        "ir_names": [p.name for p in ir],   # OFF26-16: informativo de escalação
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
